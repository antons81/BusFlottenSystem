def generate_ki_pdf(result) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from io import BytesIO
    import datetime

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2.5*cm, rightMargin=2.5*cm,
                            topMargin=2.5*cm, bottomMargin=2.5*cm)

    styles = getSampleStyleSheet()
    accent = colors.HexColor("#667eea")

    title_style = ParagraphStyle("KITitle", parent=styles["Heading1"],
                                 textColor=accent, fontSize=18, spaceAfter=6)
    meta_style  = ParagraphStyle("KIMeta",  parent=styles["Normal"],
                                 textColor=colors.HexColor("#64748b"), fontSize=9, spaceAfter=16)
    body_style  = ParagraphStyle("KIBody",  parent=styles["Normal"],
                                 fontSize=10, leading=16, spaceAfter=8)

    label = "Wöchentlich" if "weekly" in result.model_used.lower() else "Monatlich"

    story = [
        Paragraph("KI-Flottenanalyse", title_style),
        Paragraph(
            f"{label} · {result.provider_used.upper()} / {result.model_used} · "
            f"Erstellt am {datetime.date.today().strftime('%d.%m.%Y')}",
            meta_style
        ),
        Spacer(1, 0.3*cm),
    ]

    for line in result.summary.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.2*cm))
        else:
            story.append(Paragraph(line, body_style))

    doc.build(story)
    return buf.getvalue()