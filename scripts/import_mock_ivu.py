# import_mock_ivu.py
import pandas as pd
from sqlalchemy import text
import os
import sys

print("🚀 Запуск импорта mock-данных VDV 452...\n")

from app.secure_db import get_db_engine
engine = get_db_engine()

fahrten_file = "mock_ivu_fahrten.csv"
ticketing_file = "mock_ivu_ticketing.csv"

if not os.path.exists(fahrten_file):
    print(f"❌ Файл не найден: {fahrten_file}")
    sys.exit(1)

print(f"✅ Найден файл рейсов: {fahrten_file}")

with engine.begin() as conn:
    print("🔧 Обновляем структуру таблицы ivu_fahrten...")
    conn.execute(text("""
        ALTER TABLE ivu_fahrten 
        ADD COLUMN IF NOT EXISTS basis_version INTEGER,
        ADD COLUMN IF NOT EXISTS frt_fid INTEGER,
        ADD COLUMN IF NOT EXISTS fahrtart_nr SMALLINT,
        ADD COLUMN IF NOT EXISTS produktiv BOOLEAN DEFAULT true,
        ADD COLUMN IF NOT EXISTS fahrt_bezeichner VARCHAR(128),
        ADD COLUMN IF NOT EXISTS start_ort_nr INTEGER,
        ADD COLUMN IF NOT EXISTS ende_ort_nr INTEGER;
    """))

    print("🗑️  Очищаем старые данные...")
    conn.execute(text("TRUNCATE TABLE ivu_ticketing CASCADE;"))
    conn.execute(text("TRUNCATE TABLE ivu_fahrten CASCADE;"))
    conn.execute(text("TRUNCATE TABLE ivu_kpi_daily CASCADE;"))

# Импорт Fahrten
print("📥 Импорт рейсов...")
df_fahrten = pd.read_csv(fahrten_file)
df_fahrten['datum'] = pd.to_datetime(df_fahrten['datum']).dt.date

for col in ['start_zeit', 'ende_zeit', 'soll_start', 'soll_ende']:
    if col in df_fahrten.columns:
        df_fahrten[col] = pd.to_datetime(df_fahrten[col], format='%H:%M:%S', errors='coerce').dt.time

if 'produktiv' not in df_fahrten.columns:
    df_fahrten['produktiv'] = True
if 'fahrtart_nr' not in df_fahrten.columns:
    df_fahrten['fahrtart_nr'] = 1

with engine.begin() as conn:
    df_fahrten.to_sql('ivu_fahrten', conn, if_exists='append', index=False, method='multi')

print(f"✅ Загружено {len(df_fahrten)} рейсов")

# Импорт Ticketing
if os.path.exists(ticketing_file):
    print("📥 Импорт валидаций билетов...")
    df_ticketing = pd.read_csv(ticketing_file)
    df_ticketing['fahrt_id'] = pd.to_numeric(df_ticketing['fahrt_id'], errors='coerce').astype('Int64')
    df_ticketing['betrag_eur'] = pd.to_numeric(df_ticketing['betrag_eur'], errors='coerce')

    existing_ids = set(df_fahrten['fahrt_id'].dropna())
    df_ticketing = df_ticketing[df_ticketing['fahrt_id'].isin(existing_ids)]

    if not df_ticketing.empty:
        with engine.begin() as conn:
            df_ticketing.to_sql('ivu_ticketing', conn, if_exists='append', index=False, method='multi')
        print(f"✅ Загружено {len(df_ticketing)} валидаций")
    else:
        print("⚠️  Нет совпадающих fahrt_id")
else:
    print("⚠️  mock_ivu_ticketing.csv не найден — пропускаем")

# Расчёт KPI (исправленная версия)
print("📊 Расчёт KPI...")
with engine.begin() as conn:
    conn.execute(text("""
        INSERT INTO ivu_kpi_daily 
        (datum, gesamt_km, gesamt_passagiere, gesamt_umsatz_eur, 
         durchschnitt_auslastung, durchschnitt_verspaetung_min, puenktlichkeitsrate_prozent)
        SELECT 
            datum,
            ROUND(SUM(km_gesamt)::numeric, 2),
            SUM(passagiere_einsteig),
            ROUND(SUM(COALESCE((SELECT SUM(betrag_eur) FROM ivu_ticketing t WHERE t.fahrt_id = f.fahrt_id), 0))::numeric, 2),
            ROUND(AVG(auslastung_prozent)::numeric, 2),
            ROUND(AVG(COALESCE(verspaetung_min, 0)::numeric), 2),
            ROUND(100.0 * SUM(CASE WHEN COALESCE(verspaetung_min, 0) <= 5 THEN 1 ELSE 0 END)::numeric 
                  / NULLIF(COUNT(*), 0), 2)
        FROM ivu_fahrten f
        GROUP BY datum;
    """))

print("\n✅ KPI рассчитаны")
print("🎉 Импорт успешно завершён!")
print("Теперь можешь запускать дашборд.")