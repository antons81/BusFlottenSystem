# reset_to_ivu_tables.py
from sqlalchemy import create_engine, text
from app.secure_db import get_db_engine

print("🚀 Начинаем очистку и обновление схемы для IVU...")

engine = get_db_engine()

with engine.begin() as conn:
    print("🗑️  Удаляем старые таблицы...")

    # Удаляем старые таблицы (в правильном порядке из-за FK)
    conn.execute(text("DROP TABLE IF EXISTS fahrten CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS wartung CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS busse CASCADE;"))

    print("✅ Старые таблицы удалены.")

    # Создаём чистые IVU-таблицы с улучшениями под VDV 452
    print("🛠️  Создаём актуальные IVU-таблицы...")

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ivu_fahrten (
            fahrt_id SERIAL PRIMARY KEY,
            basis_version INTEGER,
            frt_fid INTEGER,                    -- VDV 452: FRT_FID
            datum DATE NOT NULL,
            linie VARCHAR(20) NOT NULL,
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
            fahrtart_nr SMALLINT,               -- VDV 452: FAHRTART_NR
            produktiv BOOLEAN DEFAULT true,     -- продуктивный рейс с пассажирами
            fahrt_bezeichner VARCHAR(128),      -- внешний идентификатор
            start_ort_nr INTEGER,
            ende_ort_nr INTEGER,
            status VARCHAR(20) DEFAULT 'planmäßig'
        );
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ivu_ticketing (
            validierung_id SERIAL PRIMARY KEY,
            fahrt_id INTEGER REFERENCES ivu_fahrten(fahrt_id) ON DELETE CASCADE,
            zeit TIMESTAMP NOT NULL,
            tarif_typ VARCHAR(50),
            betrag_eur NUMERIC(6,2),
            zahlungsart VARCHAR(30),
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

    # Полезные индексы
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ivu_fahrten_datum_linie ON ivu_fahrten(datum, linie);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ivu_fahrten_fahrzeug ON ivu_fahrten(fahrzeug_nr);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ivu_ticketing_fahrt ON ivu_ticketing(fahrt_id);"))

print("✅ Все таблицы успешно обновлены под VDV 452!")
print("   - Старые таблицы (busse, wartung, fahrten) удалены")
print("   - ivu_fahrten расширена под стандарт VDV 452")