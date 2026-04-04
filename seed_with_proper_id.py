from sqlalchemy import text
from app.secure_db import get_db_engine
from datetime import datetime

engine = get_db_engine()

print("🔄 Пересоздаём данные с правильным id...")

with engine.begin() as conn:
    # Включаем режим, чтобы можно было удалять с FK
    conn.execute(text("SET session_replication_role = replica;"))

    '''conn.execute(text("DELETE FROM fahrten"))
    conn.execute(text("DELETE FROM wartung"))
    conn.execute(text("DELETE FROM busse"))'''

    conn.execute(text("TRUNCATE TABLE fahrten, wartung, busse RESTART IDENTITY CASCADE;"))

    # Создаём автобусы с явным SERIAL id
    print("Добавляем 20 автобусов с правильным id...")
    conn.execute(text("""
        INSERT INTO busse (kennzeichen, modell, baujahr, km_stand, status) VALUES
        ('DO-B 1234', 'Setra S 516 HD', 2022, 245000, 'aktiv'),
        ('DO-B 5678', 'Setra S 515 HD', 2021, 312000, 'aktiv'),
        ('DO-B 9012', 'Mercedes Tourismo', 2023, 89000, 'aktiv'),
        ('DO-B 3456', 'Setra S 516 HD', 2020, 478000, 'in_wartung'),
        ('DO-B 7890', 'Setra S 515 HD', 2019, 556000, 'aktiv'),
        ('DO-B 1122', 'Setra S 517 HD', 2022, 198000, 'aktiv'),
        ('DO-B 3344', 'Mercedes Tourismo', 2021, 267000, 'aktiv'),
        ('DO-B 5566', 'Setra S 516 HD', 2023, 67000, 'aktiv'),
        ('DO-B 7788', 'Setra S 515 HD', 2018, 689000, 'aktiv'),
        ('DO-B 9900', 'Mercedes Tourismo', 2020, 345000, 'in_wartung'),
        ('DO-B 2468', 'Setra S 517 HD', 2022, 156000, 'aktiv'),
        ('DO-B 1357', 'Setra S 516 HD', 2021, 289000, 'aktiv'),
        ('DO-B 9876', 'Mercedes Tourismo', 2023, 45000, 'aktiv'),
        ('DO-B 5432', 'Setra S 515 HD', 2019, 512000, 'aktiv'),
        ('DO-B 1111', 'Setra S 516 HD', 2020, 398000, 'aktiv'),
        ('DO-B 2222', 'Mercedes Tourismo', 2022, 134000, 'aktiv'),
        ('DO-B 3333', 'Setra S 517 HD', 2021, 276000, 'in_wartung'),
        ('DO-B 4444', 'Setra S 515 HD', 2018, 634000, 'aktiv'),
        ('DO-B 5555', 'Mercedes Tourismo', 2023, 89000, 'aktiv'),
        ('DO-B 6666', 'Setra S 516 HD', 2020, 467000, 'aktiv')
        ON CONFLICT (kennzeichen) DO NOTHING;
    """))

    # Добавляем ТО и рейсы
    print("Добавляем техобслуживание и рейсы...")
    conn.execute(text("""
        INSERT INTO wartung (bus_id, datum, typ, status, naechste_faellig) VALUES
        (1, '2026-03-10', 'Inspektion + Ölwechsel', 'erledigt', '2026-09-10'),
        (4, '2026-01-15', 'Große Wartung', 'überfällig', '2026-01-15'),
        (10, '2026-02-28', 'HU + Bremsen', 'überfällig', '2026-02-28'),
        (3, '2026-04-05', 'Inspektion', 'geplant', '2026-10-05'),
        (7, '2026-03-20', 'Reifenwechsel', 'erledigt', '2026-09-20'),
        (15, '2026-02-10', 'Große Wartung', 'überfällig', '2026-02-10')
        ON CONFLICT DO NOTHING;
    """))

    conn.execute(text("""
        INSERT INTO fahrten (bus_id, datum, start_ort, ziel_ort, km_gesamt, dauer_min, auslastung_prozent, kraftstoff_liter) VALUES
        (1, '2026-03-20', 'Dortmund', 'München', 620, 480, 92.5, 380.2),
        (2, '2026-03-21', 'Dortmund', 'Berlin', 550, 420, 78.0, 310.5),
        (3, '2026-03-22', 'Dortmund', 'Hamburg', 480, 360, 95.0, 265.8),
        (4, '2026-03-23', 'Dortmund', 'Frankfurt', 240, 190, 88.0, 135.7),
        (5, '2026-03-24', 'Dortmund', 'Köln', 95, 80, 65.0, 45.3),
        (6, '2026-03-25', 'Dortmund', 'Stuttgart', 410, 320, 91.0, 245.6),
        (7, '2026-03-26', 'Dortmund', 'Leipzig', 380, 290, 82.0, 210.4),
        (8, '2026-03-27', 'Dortmund', 'Hannover', 280, 220, 87.0, 165.2),
        (9, '2026-03-28', 'Dortmund', 'Essen', 120, 100, 76.0, 68.5),
        (10, '2026-03-29', 'Dortmund', 'Bochum', 85, 70, 92.0, 52.1)
        ON CONFLICT DO NOTHING;
    """))

    conn.execute(text("SET session_replication_role = DEFAULT;"))

print("✅ Все данные успешно пересозданы с правильными id!")
print(f"Время: {datetime.now().strftime('%H:%M:%S')}")