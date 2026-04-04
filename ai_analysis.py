import os
import json
from app.secure_db import execute_safe_query
from datetime import datetime

def get_fleet_data_for_ai() -> dict:
    """Sammelt alle relevanten Flottendaten für die KI-Analyse"""

    buses_total  = execute_safe_query("SELECT COUNT(*) as c FROM busse")[0]['c']
    buses_active = execute_safe_query("SELECT COUNT(*) as c FROM busse WHERE status = 'aktiv'")[0]['c']
    buses_repair = execute_safe_query("SELECT COUNT(*) as c FROM busse WHERE status = 'in_wartung'")[0]['c']

    overdue = execute_safe_query("""
        SELECT COALESCE(b.kennzeichen, 'Bus'||w.bus_id::text) as kfz,
               w.typ, w.naechste_faellig, w.status
        FROM wartung w
        LEFT JOIN busse b ON w.bus_id = b.bus_id
        WHERE w.status = 'überfällig' OR w.naechste_faellig < CURRENT_DATE
    """)

    fahrten = execute_safe_query("""
        SELECT COALESCE(b.kennzeichen,'Bus'||f.bus_id::text) as kfz,
               f.km_gesamt, f.auslastung_prozent,
               f.start_ort, f.ziel_ort, f.datum
        FROM fahrten f
        LEFT JOIN busse b ON f.bus_id = b.bus_id
        ORDER BY f.datum DESC
        LIMIT 20
    """)

    avg_occ  = execute_safe_query(
        "SELECT ROUND(COALESCE(AVG(auslastung_prozent),0),1) as a FROM fahrten"
    )[0]['a']
    total_km = execute_safe_query(
        "SELECT COALESCE(SUM(km_gesamt),0) as s FROM fahrten"
    )[0]['s']

    # Busse mit hohem km-Stand
    high_km = execute_safe_query("""
        SELECT kennzeichen, km_stand, modell, baujahr
        FROM busse WHERE km_stand > 500000
        ORDER BY km_stand DESC LIMIT 5
    """)

    return {
        "busse_gesamt":   buses_total,
        "busse_aktiv":    buses_active,
        "busse_wartung":  buses_repair,
        "avg_auslastung": float(avg_occ),
        "gesamt_km":      int(total_km),
        "ueberfaellige_wartungen": overdue,
        "letzte_fahrten":          fahrten,
        "hoher_km_stand":          high_km,
        "bericht_datum":           datetime.now().strftime("%d.%m.%Y"),
    }


def generate_ai_summary(report_type: str = "weekly") -> str:
    """Erstellt eine KI-Analyse der Flottendaten via Anthropic API"""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "⚠️ Kein ANTHROPIC_API_KEY konfiguriert."

    try:
        import anthropic
    except ImportError:
        return "⚠️ Anthropic-Paket nicht installiert. Bitte: pip install anthropic"

    try:
        data = get_fleet_data_for_ai()
        period = "wöchentlichen" if report_type == "weekly" else "monatlichen"

        prompt = f"""Du bist ein erfahrener Flottenmanager bei go:on – Gesellschaft für Bus- und Schienenverkehr mbH.
Analysiere die folgenden Flottendaten und erstelle eine prägnante {period} Zusammenfassung auf Deutsch.

FLOTTENDATEN:
{json.dumps(data, ensure_ascii=False, indent=2, default=str)}

Erstelle eine strukturierte Analyse mit:
1. **Gesamtbewertung** (2-3 Sätze): Wie ist der aktuelle Zustand der Flotte?
2. **Kritische Punkte** (falls vorhanden): Überfällige Wartungen, Busse mit sehr hohem km-Stand
3. **Auslastungsanalyse**: Bewertung der durchschnittlichen Auslastung von {data['avg_auslastung']}%
4. **Empfehlungen** (2-3 konkrete Maßnahmen)

Schreibe professionell, präzise und auf Deutsch. Maximal 200 Wörter.
Kein Markdown, nur fließender Text mit nummerierten Punkten."""

        client  = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )

        summary = message.content[0].text
        print(f"✅ KI-Analyse erfolgreich generiert ({len(summary)} Zeichen)")
        return summary

    except Exception as e:
        print(f"❌ KI-Analyse Fehler: {e}")
        return f"KI-Analyse konnte nicht erstellt werden: {str(e)}"