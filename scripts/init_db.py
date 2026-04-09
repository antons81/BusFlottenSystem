from sqlalchemy import create_engine, text
from app.secure_db import get_db_engine

print("🚀 Запуск создания таблиц...")

engine = get_db_engine()

with engine.begin() as conn:

    # ─── Существующие таблицы ───────────────────────────────────────────

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS busse (
            bus_id SERIAL PRIMARY KEY,
            kennzeichen VARCHAR(20) UNIQUE NOT NULL,
            modell VARCHAR(50),
            baujahr INTEGER,
            km_stand INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'aktiv'
        );
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS wartung (
            wartung_id SERIAL PRIMARY KEY,
            bus_id INTEGER REFERENCES busse(bus_id),
            datum DATE NOT NULL,
            typ VARCHAR(50),
            status VARCHAR(20) DEFAULT 'geplant',
            naechste_faellig DATE
        );
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fahrten (
            fahrt_id SERIAL PRIMARY KEY,
            bus_id INTEGER REFERENCES busse(bus_id),
            datum DATE NOT NULL,
            start_ort VARCHAR(100),
            ziel_ort VARCHAR(100),
            km_gesamt INTEGER,
            dauer_min INTEGER,
            auslastung_prozent DECIMAL(5,2),
            kraftstoff_liter DECIMAL(8,2)
        );
    """))

    # ─── IVU Tabellen ───────────────────────────────────────────────────

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ivu_fahrten (
            fahrt_id SERIAL PRIMARY KEY,
            datum DATE,
            linie VARCHAR(20),
            richtung VARCHAR(10),
            fahrzeug_nr VARCHAR(20),
            fahrer_id VARCHAR(20),
            start_zeit TIME,
            ende_zeit TIME,
            soll_start TIME,
            soll_ende TIME,
            verspaetung_min INTEGER,
            km_gesamt NUMERIC(8,2),
            passagiere_einsteig INTEGER,
            auslastung_prozent NUMERIC(5,2),
            energie_verbrauch_kwh NUMERIC(8,2),
            status VARCHAR(20)
        );
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ivu_ticketing (
            validierung_id SERIAL PRIMARY KEY,
            fahrt_id INTEGER REFERENCES ivu_fahrten(fahrt_id),
            zeit TIMESTAMP,
            tarif_typ VARCHAR(50),
            betrag_eur NUMERIC(6,2),
            zahlungsart VARCHAR(20),
            haltestelle VARCHAR(100)
        );
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ivu_kpi_daily (
            datum DATE PRIMARY KEY,
            gesamt_km NUMERIC(10,2),
            gesamt_passagiere INTEGER,
            gesamt_umsatz_eur NUMERIC(12,2),
            durchschnitt_auslastung NUMERIC(5,2),
            durchschnitt_verspaetung_min NUMERIC(5,2),
            puenktlichkeitsrate_prozent NUMERIC(5,2)
        );
    """))

print("✅ Таблицы busse, wartung, fahrten erfolgreich erstellt!")
print("✅ IVU Tabellen ivu_fahrten, ivu_ticketing, ivu_kpi_daily erfolgreich erstellt!")