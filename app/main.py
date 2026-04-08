from app.models import AIAnalyseRequest, AIAnalyseResponse
from ai_analysis import generate_ai_summary
from fastapi import FastAPI
from sqlalchemy import text
from app.secure_db import get_db_engine, execute_safe_query

app = FastAPI(
    title="go:on – Bus Automation System",
    description="Gesellschaft für Bus- und Schienenverkehr mbH – Flottenmanagement API",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "system": "go:on Flottenmanagement-System",
        "status": "ok",
        "endpoints": ["/kpi", "/health", "/vault-test", "/test-db"]
    }

@app.post("/ai-analyse", response_model=AIAnalyseResponse)
def ai_analyse(request: AIAnalyseRequest):
    return generate_ai_summary(
        report_type=request.report_type,
        provider=request.provider
    )

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/vault-test")
def vault_test():
    from app.secure_db import get_db_credentials
    try:
        creds = get_db_credentials()
        return {"status": "success", "has_credentials": True, "username": creds.get("username")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/test-db")
def test_db():
    engine = get_db_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 as test"))
        return {"status": "success", "database": "connected", "result": result.scalar()}

@app.get("/kpi")
def get_kpi():
    """Hauptkennzahlen der Busflotte"""
    queries = {
        "total_buses":           "SELECT COUNT(*) FROM busse",
        "active_buses":          "SELECT COUNT(*) FROM busse WHERE status = 'aktiv'",
        "in_maintenance":        "SELECT COUNT(*) FROM busse WHERE status = 'in_wartung'",
        "overdue_maintenance":   """
            SELECT COUNT(*) FROM wartung
            WHERE status = 'überfällig' OR naechste_faellig < CURRENT_DATE
        """,
        "total_km":              "SELECT COALESCE(SUM(km_gesamt), 0) FROM fahrten",
        "avg_occupancy":         "SELECT ROUND(AVG(auslastung_prozent), 2) FROM fahrten"
    }

    results = {}
    for key, sql in queries.items():
        try:
            data = execute_safe_query(sql)
            results[key] = data[0] if data else None
        except Exception as e:
            results[key] = {"error": str(e)}

    return {
        "status":  "success",
        "company": "go:on Gesellschaft für Bus- und Schienenverkehr mbH",
        "kpi":     results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)