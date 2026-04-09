# ai_analysis.py
import httpx
from app.config import settings
from app.models import AIAnalyseResponse, FleetKPI


def generate_ai_summary(report_type: str = "weekly", provider: str = None) -> AIAnalyseResponse:
    """AI-Анализ — Ollama + Claude (актуальные модели 2026)"""
    
    if provider is None:
        provider = settings.ai_provider

    # ====================== OLLAMA ======================
    if provider == "ollama":
        model = settings.ollama_model
        
        prompt = f"""
Du bist ein erfahrener Busflotten-Analyst bei go:on.

Erstelle einen klaren, professionellen deutschen Bericht zum Thema "{report_type}".

Berücksichtige besonders:
- Pünktlichkeit und Verspätungen
- Auslastung der Busse
- Anzahl der Fahrgäste
- Auffällige Probleme oder positive Entwicklungen
- Kurze praktische Empfehlungen

Schreibe sachlich, strukturiert und übersichtlich.
"""

        try:
            with httpx.Client(timeout=90.0) as client:
                response = client.post(
                    f"{settings.ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": 0.7
                    }
                )
                response.raise_for_status()
                data = response.json()

                summary_text = data.get("response", "Keine Antwort erhalten.")

                return AIAnalyseResponse(
                    summary=summary_text.strip(),
                    provider_used="ollama",
                    model_used=model,
                    zeichen=len(summary_text),
                    report_type=report_type
                )
        except Exception as e:
            return AIAnalyseResponse(
                summary=f"Fehler bei Ollama (qwen2.5:3b): {str(e)}",
                provider_used="ollama",
                model_used=model,
                zeichen=0,
                report_type=report_type
            )

    # ====================== CLAUDE (Anthropic) ======================
    else:
        if not settings.anthropic_api_key:
            return AIAnalyseResponse(
                summary="Claude API Key ist nicht konfiguriert.\nBitte überprüfe die .env Datei.",
                provider_used="claude",
                model_used="claude",
                zeichen=0,
                report_type=report_type
            )

        try:
            prompt = f"""
Du bist ein erfahrener Busflotten-Analyst bei go:on.

Erstelle einen klaren, professionellen deutschen Bericht zum Thema "{report_type}".

Berücksichtige besonders:
- Pünktlichkeit und Verspätungen
- Auslastung der Busse
- Anzahl der Fahrgäste
- Auffällige Probleme oder positive Entwicklungen
- Kurze praktische Empfehlungen

Schreibe sachlich, strukturiert und übersichtlich.
"""

            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": settings.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-sonnet-4-6",           # ← актуальная стабильная модель
                        "max_tokens": 1200,
                        "temperature": 0.7,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                )
                response.raise_for_status()
                data = response.json()

                summary_text = data["content"][0]["text"]

                return AIAnalyseResponse(
                    summary=summary_text.strip(),
                    provider_used="claude",
                    model_used="claude-sonnet-4-6",
                    zeichen=len(summary_text),
                    report_type=report_type
                )

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            return AIAnalyseResponse(
                summary=f"Claude API Fehler ({e.response.status_code}):\n{error_detail[:600]}",
                provider_used="claude",
                model_used="claude-sonnet-4-6",
                zeichen=0,
                report_type=report_type
            )
        except Exception as e:
            return AIAnalyseResponse(
                summary=f"Fehler bei Claude API: {str(e)}",
                provider_used="claude",
                model_used="claude-sonnet-4-6",
                zeichen=0,
                report_type=report_type
            )