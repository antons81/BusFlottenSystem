from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class Bus(BaseModel):
    bus_id: int
    kennzeichen: str
    modell: str
    baujahr: int
    km_stand: int
    status: str  # aktiv, in_wartung, außer_betrieb


class Fahrt(BaseModel):
    fahrt_id: int
    bus_id: int
    kennzeichen: Optional[str] = None
    datum: date
    start_ort: str
    ziel_ort: str
    km_gesamt: float
    auslastung_prozent: float


class Wartung(BaseModel):
    wartung_id: int
    bus_id: int
    kennzeichen: Optional[str] = None
    typ: str
    naechste_faellig: date
    status: str  # geplant, überfällig, erledigt


class FleetKPI(BaseModel):
    busse_gesamt: int
    busse_aktiv: int
    busse_wartung: int
    avg_auslastung: float = Field(ge=0, le=100)
    gesamt_km: int
    ueberfaellige_wartungen: list[dict]
    letzte_fahrten: list[dict]
    hoher_km_stand: list[dict]
    bericht_datum: str


class AIAnalyseRequest(BaseModel):
    report_type: str = Field(default="weekly", pattern="^(weekly|monthly)$")
    provider: Optional[str] = Field(
        default=None,
        description="claude oder ollama — überschreibt Settings"
    )


class AIAnalyseResponse(BaseModel):
    summary: str
    provider_used: str
    model_used: str
    zeichen: int