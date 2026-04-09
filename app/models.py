# app/models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date


class FleetKPI(BaseModel):
    """Модель для PDF-отчётов и других модулей"""
    busse_gesamt: int = 0
    busse_aktiv: int = 0
    busse_wartung: int = 0
    avg_auslastung: float = 0.0
    gesamt_km: int = 0
    ueberfaellige_wartungen: List[Dict] = Field(default_factory=list)
    letzte_fahrten: List[Dict] = Field(default_factory=list)
    hoher_km_stand: List[Dict] = Field(default_factory=list)
    bericht_datum: str = ""


class AIAnalyseRequest(BaseModel):
    report_type: str = Field(default="weekly", pattern="^(daily|weekly|monthly)$")
    provider: Optional[str] = Field(default=None)


class AIAnalyseResponse(BaseModel):
    summary: str
    provider_used: str
    model_used: str
    zeichen: int
    report_type: str = "weekly"