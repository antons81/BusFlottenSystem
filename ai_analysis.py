import httpx
from datetime import datetime
from app.config import settings
from app.models import AIAnalyseResponse
from app.secure_db import execute_safe_query

def get_extended_db_data():
    """Holt KPI-Trends, Problem-Linien und Finanzdaten aus der DB"""
    try:
        trends = execute_safe_query("""
            SELECT datum, puenktlichkeitsrate_prozent, gesamt_passagiere, 
                   durchschnitt_auslastung, gesamt_umsatz_eur
            FROM ivu_kpi_daily 
            ORDER BY datum DESC LIMIT 2
        """)
        
        problem_lines = execute_safe_query("""
            SELECT linie, ROUND(AVG(verspaetung_min)::numeric, 1) as avg_v, COUNT(*) as fahrt_count
            FROM ivu_fahrten
            WHERE datum >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY linie
            ORDER BY avg_v DESC LIMIT 3
        """)

        return {
            "trends": trends if trends else [],
            "problem_lines": problem_lines if problem_lines else []
        }
    except Exception as e:
        print(f"Extended DB Error: {e}")
        return {"trends": [], "problem_lines": []}

def generate_ai_summary(report_type: str = "weekly", provider: str = None) -> AIAnalyseResponse:
    """KI-Analyse (Claude/Ollama) mit Finanzprognose и защитой от обрывов текста."""
    
    active_provider = provider or settings.ai_provider
    data = get_extended_db_data()
    
    if not data["trends"]:
        return AIAnalyseResponse(summary="Fehler: Keine Daten.", provider_used=active_provider, 
                                 model_used="N/A", zeichen=0, report_type=report_type)

    curr = data["trends"][0]
    prev = data["trends"][1] if len(data["trends"]) > 1 else curr
    
    p_diff = curr['puenktlichkeitsrate_prozent'] - prev['puenktlichkeitsrate_prozent']
    u_diff = curr['gesamt_umsatz_eur'] - prev['gesamt_umsatz_eur']
    
    lines_detail = "\n".join([f"- Linie {l['linie']}: {l['avg_v']} Min Ø Verspätung ({l['fahrt_count']} Fahrten)" for l in data['problem_lines']])
    report_name_de = "Wochenbericht" if report_type == "weekly" else "Monatsbericht"

    # Единый промпт для обоих провайдеров
    prompt = f"""
Du bist ein Senior-Consultant für Mobilitätsstrategie. Erstelle einen umfassenden {report_name_de} für go:on.
Berichtszeitraum: {datetime.now().strftime('%d.%m.%Y')}

### STRENG VERTRAULICHE FORMATIERUNGSRICHTLINIE:
Erstelle eine saubere Markdown-Tabelle. 
Spalten: | Metrik | Wert | Trend | Status |

WICHTIG: Schreibe NUR den Endwert in die Tabelle. Keine Erklärungen der Regeln (z.B. NICHT ">=95% -> 🟢").
Setze das Icon basierend auf diesen internen Kriterien:
- Pünktlichkeit: 100-95% = 🟢, 94-85% = 🟡, <85% = 🔴
- Auslastung: 60-80% = 🟢, sonst 🟡
- Umsatz/Passagiere: Trend > 0 = 📈, Trend < 0 = 📉, Trend 0 = ➡️

### DATEN FÜR DIE TABELLE:
- Pünktlichkeit: {curr['puenktlichkeitsrate_prozent']}%
- Passagiere: {curr['gesamt_passagiere']}
- Auslastung: {curr['durchschnitt_auslastung']}%
- Gesamtumsatz: {curr['gesamt_umsatz_eur']} €


### DETAILLIERTE PROBLEMLINIEN:
{lines_detail if lines_detail else "Alle Linien im grünen Bereich."}

### BERICHTSSTRUKTUR:
1. **DASHBOARD**: Die Tabelle mit den oben genannten Icons.
2. **OPERATIVE ANALYSE**: Systemische Analyse der Pünktlichkeit (100% Paradoxon) und Auslastung.
3. **FINANZ-PROGNOSE**: Analyse des Umsatztrends und Berechnung der hypothetischen Kosten bei Pünktlichkeitsverlust.
4. **MASSNAHMEN**: 3 strategische Empfehlungen zur Optimierung.


### EXPERTEN-MODUS AKTIVIERT:
- Schreibe JEDEN Abschnitt (Operative Analyse, Finanz-Prognose, Maßnahmen) in Form von MINDESTENS zwei langen, fließenden Absätzen.
- VERBOTE: Keine kurzen Aufzählungszeichen (Stichpunkte) in den Analyse-Sektionen. Nutze nur ausformulierte Sätze.
- ANALYSE-FOKUS: Erkläre tiefgreifend, warum die Auslastung von 66,55% im Widerspruch zur perfekten Pünktlichkeit steht. Ziehe Vergleiche zu Branchendurchschnitten.
- FINANZ-LOGIK: Diskutiere explizit das Verhältnis von 20,80 € Umsatz zu 479 Passagieren. Ist das ein defizitäres Modell? Fordere strategische Änderungen.


ANTWORTE NUR AUF DEUTSCH. NUTZE FETTDRUCK FÜR WICHTIGE STELLEN. keine emglischen Begriffe, außer Fachtermini.
"""

    try:
        if active_provider == "ollama":
            model_used = settings.ollama_model
            with httpx.Client(timeout=300.0) as client: # Увеличили таймаут для Mac Mini
                response = client.post(
                    f"{settings.ollama_url}/api/generate",
                    json={
                        "model": model_used,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.6,
                            "num_predict": 4096,  # no text cutting, but also not too long to avoid timeouts
                            "num_ctx": 8192,      # model memory context, should be enough for our prompt + response
                            "repeat_penalty": 1.15
                        }
                    }
                )
                response.raise_for_status()
                summary_text = response.json().get("response", "")
        else:
            model_used = "claude-sonnet-4-6"
            with httpx.Client(timeout=90.0) as client:
                response = client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": settings.anthropic_api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                    json={
                        "model": model_used,
                        "max_tokens": 4000,
                        "temperature": 0.7,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                )
                response.raise_for_status()
                summary_text = response.json()["content"][0]["text"]

        return AIAnalyseResponse(
            summary=summary_text.strip(),
            provider_used=active_provider.capitalize(),
            model_used=model_used,
            zeichen=len(summary_text),
            report_type=report_type
        )

    except Exception as e:
        return AIAnalyseResponse(summary=f"Fehler: {str(e)}", provider_used=active_provider, model_used="Error", zeichen=0, report_type=report_type)