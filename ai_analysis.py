import json
import httpx
from app.secure_db import execute_safe_query
from app.config import settings
from app.models import FleetKPI, AIAnalyseResponse
from datetime import datetime


def get_fleet_data_for_ai() -> FleetKPI:
    """Sammelt alle relevanten Flottendaten und validiert sie via Pydantic"""

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

    high_km = execute_safe_query("""
        SELECT kennzeichen, km_stand, modell, baujahr
        FROM busse WHERE km_stand > 500000
        ORDER BY km_stand DESC LIMIT 5
    """)

    return FleetKPI(
        busse_gesamt=buses_total,
        busse_aktiv=buses_active,
        busse_wartung=buses_repair,
        avg_auslastung=float(avg_occ),
        gesamt_km=int(total_km),
        ueberfaellige_wartungen=overdue,
        letzte_fahrten=fahrten,
        hoher_km_stand=high_km,
        bericht_datum=datetime.now().strftime("%d.%m.%Y"),
    )


def _build_prompt(data: FleetKPI, report_type: str) -> str:
    period = "wöchentlichen" if report_type == "weekly" else "monatlichen"
    return f"""Du bist ein erfahrener Flottenmanager bei go:on – Gesellschaft für Bus- und Schienenverkehr mbH.
Analysiere die folgenden Flottendaten und erstelle eine prägnante {period} Zusammenfassung auf Deutsch.

FLOTTENDATEN:
{json.dumps(data.model_dump(), ensure_ascii=False, indent=2, default=str)}

Erstelle eine strukturierte Analyse mit:
1. **Gesamtbewertung** (2-3 Sätze): Wie ist der aktuelle Zustand der Flotte?
2. **Kritische Punkte** (falls vorhanden): Überfällige Wartungen, Busse mit sehr hohem km-Stand
3. **Auslastungsanalyse**: Bewertung der durchschnittlichen Auslastung von {data.avg_auslastung}%
4. **Empfehlungen** (2-3 konkrete Maßnahmen)

Schreibe professionell, präzise und auf Deutsch. Maximal 200 Wörter.
Kein Markdown, nur fließender Text mit nummerierten Punkten. Kein Markdown, keine ###, keine **, nur normaler Fließtext."""



def _call_ollama(prompt: str) -> str:
    """Lokale KI-Analyse via Ollama — kostenlos"""
    response = httpx.post(
        f"{settings.ollama_url}/api/generate",
        json={
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False
        },
        timeout=120.0
    )
    response.raise_for_status()
    return response.json()["response"]


def _call_claude(prompt: str) -> str:
    """KI-Analyse via Anthropic Claude API"""
    import anthropic
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def generate_ai_summary(
    report_type: str = "weekly",
    provider: str | None = None
) -> AIAnalyseResponse:
    """
    Erstellt eine KI-Analyse der Flottendaten.
    provider: 'claude' | 'ollama' | None (verwendet Settings-Default)
    """
    active_provider = provider or settings.ai_provider
    model_used = settings.ollama_model if active_provider == "ollama" else "claude-opus-4-6"

    try:
        data = get_fleet_data_for_ai()
        prompt = _build_prompt(data, report_type)

        if active_provider == "ollama":
            summary = _call_ollama(prompt)
        else:
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY nicht konfiguriert.")
            summary = _call_claude(prompt)

        print(f"✅ KI-Analyse via {active_provider} ({model_used}): {len(summary)} Zeichen")

        return AIAnalyseResponse(
            summary=summary,
            provider_used=active_provider,
            model_used=model_used,
            zeichen=len(summary)
        )

    except Exception as e:
        print(f"❌ KI-Analyse Fehler ({active_provider}): {e}")
        return AIAnalyseResponse(
            summary=f"KI-Analyse konnte nicht erstellt werden: {str(e)}",
            provider_used=active_provider,
            model_used=model_used,
            zeichen=0
        )