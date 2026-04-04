from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT   # ← Исправлено: добавили импорт
from app.secure_db import execute_safe_query
from datetime import datetime
import os
import pandas as pd
import pytz
from ai_analysis import generate_ai_summary   # ← AI анализ

# ====================== FARBEN ======================
GREEN_DARK   = colors.HexColor("#2D6A2D")
GREEN_MAIN   = colors.HexColor("#5CB85C")
GREEN_LIGHT  = colors.HexColor("#EAF5EA")
GRAY_DARK    = colors.HexColor("#2C2C2C")
GRAY_MID     = colors.HexColor("#6C757D")
GRAY_LIGHT   = colors.HexColor("#F5F5F5")
WHITE        = colors.white
RED_WARN     = colors.HexColor("#DC3545")

berlin = pytz.timezone('Europe/Berlin')

# ====================== STYLES ======================
def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'CompanyName',
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=GREEN_DARK,
        spaceAfter=2,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        'CompanySubtitle',
        fontName='Helvetica',
        fontSize=9,
        textColor=GRAY_MID,
        spaceAfter=0,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        'ReportTitle',
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=GRAY_DARK,
        spaceBefore=18,
        spaceAfter=4,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        'ReportMeta',
        fontName='Helvetica',
        fontSize=9,
        textColor=GRAY_MID,
        spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        'SectionHeading',
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=GREEN_DARK,
        spaceBefore=18,
        spaceAfter=8,
        borderPadding=(0, 0, 4, 0),
    ))
    styles.add(ParagraphStyle(
        'KPIValue',
        fontName='Helvetica-Bold',
        fontSize=28,
        textColor=GREEN_DARK,
        alignment=TA_CENTER,
        spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        'KPILabel',
        fontName='Helvetica',
        fontSize=9,
        textColor=GRAY_MID,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        'KPIValueRed',
        fontName='Helvetica-Bold',
        fontSize=28,
        textColor=RED_WARN,
        alignment=TA_CENTER,
        spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        'AIText',
        fontName='Helvetica',
        fontSize=10,
        textColor=GRAY_DARK,
        spaceAfter=6,
        leading=15,
    ))
    styles.add(ParagraphStyle(
        'FooterText',
        fontName='Helvetica',
        fontSize=8,
        textColor=GRAY_MID,
        alignment=TA_CENTER,
    ))
    return styles


def header_footer(canvas, doc):

    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")

    canvas.saveState()
    w, h = A4

    # Kopfzeile
    canvas.setFillColor(GREEN_LIGHT)
    canvas.rect(0, h - 1.8*cm, w, 1.8*cm, fill=1, stroke=0)

    # ЛОГО — исправлено
    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    if os.path.exists(logo_path):
        canvas.drawImage(logo_path, 1*cm, h - 1.6*cm, 
                         width=4*cm, height=1.3*cm, 
                         preserveAspectRatio=True, mask='auto')
    else:
        print(f"⚠️ Лого не найдено по пути: {logo_path}")

    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(GREEN_DARK)
    canvas.drawRightString(w - 1.5*cm, h - 0.9*cm, "go:on Gesellschaft für Bus- und Schienenverkehr mbH")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(w - 1.5*cm, h - 1.4*cm, "Automatisierter Flottenbericht")

    # Fußzeile
    canvas.setFillColor(GRAY_LIGHT)
    canvas.rect(0, 0, w, 1*cm, fill=1, stroke=0)
    canvas.setFillColor(GREEN_MAIN)
    canvas.rect(0, 1*cm, w, 0.05*cm, fill=1, stroke=0)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRAY_MID)
    canvas.drawString(1.5*cm, 0.35*cm,
                      f"Erstellt am {datetime.now(tz=berlin).strftime('%d.%m.%Y um %H:%M')} Uhr  |  Vertraulich")
    canvas.drawRightString(w - 1.5*cm, 0.35*cm, f"Seite {doc.page}")

    canvas.restoreState()


def kpi_card(value, label, styles, warn=False):
    val_style = 'KPIValueRed' if warn else 'KPIValue'
    data = [[Paragraph(str(value), styles[val_style])],
            [Paragraph(label, styles['KPILabel'])]]
    t = Table(data, colWidths=[4.2*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), GREEN_LIGHT if not warn else colors.HexColor("#FFF5F5")),
        ('BOX', (0,0), (-1,-1), 1, GREEN_MAIN if not warn else RED_WARN),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING',(0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    return t


def generate_pdf_report(report_type="weekly"):
    timestamp = datetime.now(tz=berlin).strftime("%Y-%m-%d_%H-%M")
    filename = f"reports/goon_{report_type}_Bericht_{timestamp}.pdf"
    os.makedirs("reports", exist_ok=True)

    doc = SimpleDocTemplate(
        filename, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=2.5*cm, bottomMargin=1.8*cm
    )

    styles = build_styles()
    story = []

    # Titel
    period_label = "Wöchentlicher" if report_type == "weekly" else "Monatlicher"
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"{period_label} Flottenbericht", styles['ReportTitle']))
    story.append(Paragraph(
        f"Berichtszeitraum: {datetime.now(tz=berlin).strftime('%B %Y')}  |  "
        f"Erstellt: {datetime.now(tz=berlin).strftime('%d.%m.%Y %H:%M')}",
        styles['ReportMeta']
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=GREEN_MAIN, spaceAfter=12))

    # KPI
    story.append(Paragraph("Wichtige Kennzahlen", styles['SectionHeading']))

    buses   = execute_safe_query("SELECT COUNT(*) as c FROM busse")[0]['c']
    active  = execute_safe_query("SELECT COUNT(*) as c FROM busse WHERE status = 'aktiv'")[0]['c']
    in_rep  = execute_safe_query("SELECT COUNT(*) as c FROM busse WHERE status = 'in_wartung'")[0]['c']
    overdue = execute_safe_query("SELECT COUNT(*) as c FROM wartung WHERE status = 'überfällig' OR naechste_faellig < CURRENT_DATE")[0]['c']
    avg_occ = execute_safe_query("SELECT ROUND(COALESCE(AVG(auslastung_prozent),0),1) as a FROM fahrten")[0]['a']
    total_km = execute_safe_query("SELECT COALESCE(SUM(km_gesamt),0) as s FROM fahrten")[0]['s']

    kpi_row = Table([[
        kpi_card(buses, "Gesamte Busse", styles),
        kpi_card(active, "Aktive Busse", styles),
        kpi_card(in_rep, "In Wartung", styles),
        kpi_card(overdue, "Überfällige Wartungen", styles, warn=overdue > 0),
    ]], colWidths=[4.2*cm]*4)

    story.append(kpi_row)
    story.append(Spacer(1, 0.3*cm))

    kpi_row2 = Table([[
        kpi_card(f"{avg_occ}%", "Ø Auslastung", styles),
        kpi_card(f"{total_km:,}", "Gesamt-km", styles),
    ]], colWidths=[4.2*cm]*2)
    story.append(kpi_row2)

    # KI-Analyse
    story.append(Spacer(1, 15))
    story.append(Paragraph("🤖 KI-Analyse & Empfehlungen", styles['SectionHeading']))

    ai_text = generate_ai_summary(report_type)

    for paragraph in ai_text.split('\n\n'):
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(), styles['AIText']))
            story.append(Spacer(1, 8))

    # Letzte Fahrten
    story.append(Spacer(1, 15))
    story.append(Paragraph("Letzte Fahrten", styles['SectionHeading']))

    df = pd.DataFrame(execute_safe_query("""
        SELECT
            TO_CHAR(f.datum, 'DD.MM.YYYY') as "Datum",
            COALESCE(b.kennzeichen, 'Bus ' || f.bus_id) as "Kennzeichen",
            f.start_ort as "Von",
            f.ziel_ort as "Nach",
            f.km_gesamt as "km",
            CONCAT(f.auslastung_prozent, ' %') as "Auslastung"
        FROM fahrten f
        LEFT JOIN busse b ON f.bus_id = b.bus_id
        ORDER BY f.datum DESC
        LIMIT 15
    """))

    if not df.empty:
        header = df.columns.tolist()
        rows = df.values.tolist()
        table_data = [header] + rows
        col_w = [2.8*cm, 3*cm, 3*cm, 3*cm, 1.8*cm, 2.5*cm]
        t = Table(table_data, colWidths=col_w, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), GREEN_DARK),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,0), (-1,0), 8),
            *[('BACKGROUND', (0,i), (-1,i), GRAY_LIGHT if i % 2 == 0 else WHITE)
              for i in range(1, len(table_data))],
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('TEXTCOLOR', (0,1), (-1,-1), GRAY_DARK),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor("#DDDDDD")),
        ]))
        story.append(t)

    # Überfällige Wartungen
    story.append(Spacer(1, 15))
    story.append(Paragraph("Überfällige Wartungen", styles['SectionHeading']))

    w_df = pd.DataFrame(execute_safe_query("""
        SELECT
            COALESCE(b.kennzeichen, 'Bus ' || w.bus_id) as "Kennzeichen",
            TO_CHAR(w.datum, 'DD.MM.YYYY') as "Wartungsdatum",
            w.typ as "Typ",
            TO_CHAR(w.naechste_faellig,'DD.MM.YYYY') as "Fällig am",
            w.status as "Status"
        FROM wartung w
        LEFT JOIN busse b ON w.bus_id = b.bus_id
        WHERE w.status = 'überfällig' OR w.naechste_faellig < CURRENT_DATE
        ORDER BY w.naechste_faellig
    """))

    if not w_df.empty:
        wh = w_df.columns.tolist()
        wr = w_df.values.tolist()
        wt = Table([wh] + wr, colWidths=[3*cm, 3.2*cm, 4*cm, 3.2*cm, 3*cm], repeatRows=1)
        wt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), RED_WARN),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            *[('BACKGROUND', (0,i), (-1,i), colors.HexColor("#FFF0F0") if i % 2 == 0 else WHITE)
              for i in range(1, len(wr)+1)],
            ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor("#FFCCCC")),
        ]))
        story.append(wt)
    else:
        story.append(Paragraph("✅ Keine überfälligen Wartungen.", styles['AIText']))

    # Footer
    story.append(Spacer(1, 0.8*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_MID))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Dieser Bericht wurde automatisch generiert. Alle Angaben ohne Gewähr. "
        "© go:on Gesellschaft für Bus- und Schienenverkehr mbH",
        styles['FooterText']
    ))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"✅ Schöner PDF-Bericht mit KI-Analyse erstellt: {filename}")
    return filename


if __name__ == "__main__":
    print("1. Wöchentlicher Bericht")
    print("2. Monatlicher Bericht")
    choice = input("Wählen Sie (1/2): ")
    generate_pdf_report("weekly" if choice == "1" else "monthly")