from sqlalchemy import create_engine, text
from app.secure_db import get_db_engine

print("🚀 Запуск создания таблиц...")

engine = get_db_engine()

with engine.begin() as conn:   # begin() лучше для создания таблиц
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

print("✅ Таблицы busse, wartung и fahrten успешно созданы!")
