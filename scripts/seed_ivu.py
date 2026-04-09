"""
Seed-скрипт для IVU mock-данных.
Генерирует 30 дней реалистичных данных для ivu_fahrten, ivu_ticketing, ivu_kpi_daily.
"""
import random
from datetime import date, datetime, timedelta, time
from decimal import Decimal
from sqlalchemy import text
from app.secure_db import get_db_engine

random.seed(42)

engine = get_db_engine()

# ─── Конфигурация ───────────────────────────────────────────────────────────

LINIEN = {
    "101": {"km": 18.5, "takt_min": 20, "kapazitaet": 62},
    "105": {"km": 24.7, "takt_min": 30, "kapazitaet": 90},
    "210": {"km": 21.3, "takt_min": 20, "kapazitaet": 82},
    "320": {"km": 15.8, "takt_min": 60, "kapazitaet": 60},
    "415": {"km": 31.2, "takt_min": 60, "kapazitaet": 90},
}

FAHRZEUGE = ["B-1234", "B-1235", "B-5678", "B-5679", "B-9012", "B-9013", "B-3456", "B-3457", "B-4100"]
FAHRER    = ["F123", "F234", "F456", "F567", "F789", "F890", "F101", "F112", "F334"]

TARIFE = [
    ("Einzelfahrschein", 2.90, 0.35),
    ("Tagesticket",      7.50, 0.15),
    ("Monatsabo",        0.00, 0.25),
    ("Sozialticket",     1.50, 0.10),
    ("Schülerticket",    1.20, 0.10),
    ("Gruppenticket",   12.00, 0.05),
]

ZAHLUNGSARTEN = ["Bar", "eTicket", "Handy", "Karte"]

HALTESTELLEN = [
    "Hauptbahnhof", "ZOB", "Universität", "Rathaus", "Marktplatz",
    "Stadtpark", "Klinikum", "Messegelände", "Flughafen", "Ostbahnhof",
    "Westend", "Nordmarkt", "Südring", "Technologiepark", "Schulzentrum"
]

START_DATUM = date.today() - timedelta(days=30)


def random_time(hour_start: int, hour_end: int) -> time:
    h = random.randint(hour_start, hour_end - 1)
    m = random.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
    return time(h, m)


def add_minutes(t: time, minutes: int) -> time:
    dt = datetime.combine(date.today(), t) + timedelta(minutes=minutes)
    return dt.time()


def is_weekend(d: date) -> bool:
    return d.weekday() >= 5


def generate_fahrten(datum: date) -> list[dict]:
    fahrten = []
    weekend = is_weekend(datum)

    for linie, cfg in LINIEN.items():
        takt = cfg["takt_min"]
        km   = cfg["km"]
        kap  = cfg["kapazitaet"]

        # В будни больше рейсов
        start_hour = 6
        end_hour   = 22 if not weekend else 20
        current    = random_time(start_hour, start_hour + 1)

        fahrzeug_pool = random.sample(FAHRZEUGE, min(3, len(FAHRZEUGE)))
        fahrer_pool   = random.sample(FAHRER,    min(3, len(FAHRER)))

        richtung_toggle = True
        i = 0

        while current.hour < end_hour:
            soll_start = current
            dauer_soll = int(km * 2.8)  # ~2.8 мин/км
            soll_ende  = add_minutes(soll_start, dauer_soll)

            # Опоздание: обычно 0-8 мин, иногда -1 (досрочно)
            if weekend:
                verspaetung = random.choices(
                    [-1, 0, 1, 2, 3, 5, 8, 15],
                    weights=[5, 40, 20, 15, 10, 5, 3, 2]
                )[0]
            else:
                verspaetung = random.choices(
                    [-1, 0, 1, 2, 3, 5, 8, 15],
                    weights=[3, 30, 20, 20, 12, 8, 5, 2]
                )[0]

            start_zeit = add_minutes(soll_start, max(0, verspaetung))
            ende_zeit  = add_minutes(soll_ende,  verspaetung)

            # Загрузка зависит от времени суток
            if 7 <= current.hour <= 9 or 16 <= current.hour <= 18:
                auslastung = random.uniform(65, 98)   # час пик
            elif 22 <= current.hour or current.hour <= 5:
                auslastung = random.uniform(10, 35)   # ночь
            else:
                auslastung = random.uniform(30, 75)   # обычное время

            passagiere = int(kap * auslastung / 100)

            # Электробус потребление
            energie = round(km * random.uniform(1.8, 2.4), 2)

            status = "ausgefallen" if random.random() < 0.01 else (
                "verspätet" if verspaetung >= 5 else "planmäßig"
            )

            fahrten.append({
                "datum":               datum,
                "linie":               linie,
                "richtung":            "Hin" if richtung_toggle else "Rück",
                "fahrzeug_nr":         fahrzeug_pool[i % len(fahrzeug_pool)],
                "fahrer_id":           fahrer_pool[i % len(fahrer_pool)],
                "start_zeit":          start_zeit,
                "ende_zeit":           ende_zeit,
                "soll_start":          soll_start,
                "soll_ende":           soll_ende,
                "verspaetung_min":     verspaetung,
                "km_gesamt":           km,
                "passagiere_einsteig": passagiere,
                "auslastung_prozent":  round(auslastung, 2),
                "energie_verbrauch_kwh": energie,
                "status":              status,
            })

            current = add_minutes(current, takt)
            richtung_toggle = not richtung_toggle
            i += 1

    return fahrten


def generate_ticketing(fahrt_id: int, passagiere: int, datum: date, soll_start: time) -> list[dict]:
    tickets = []
    basis_zeit = datetime.combine(datum, soll_start)

    for _ in range(passagiere):
        tarif, betrag, _ = random.choices(TARIFE, weights=[w for _, _, w in TARIFE])[0]
        offset_sec = random.randint(0, 45 * 60)
        zeit = basis_zeit + timedelta(seconds=offset_sec)

        tickets.append({
            "fahrt_id":    fahrt_id,
            "zeit":        zeit,
            "tarif_typ":   tarif,
            "betrag_eur":  betrag,
            "zahlungsart": random.choice(ZAHLUNGSARTEN),
            "haltestelle": random.choice(HALTESTELLEN),
        })

    return tickets


def compute_kpi(datum: date, fahrten: list[dict]) -> dict:
    aktive = [f for f in fahrten if f["status"] != "ausgefallen"]
    gesamt_km          = sum(f["km_gesamt"] for f in aktive)
    gesamt_passagiere  = sum(f["passagiere_einsteig"] for f in aktive)
    gesamt_umsatz      = round(gesamt_passagiere * random.uniform(1.8, 2.5), 2)
    avg_auslastung     = round(sum(f["auslastung_prozent"] for f in aktive) / max(len(aktive), 1), 2)
    avg_verspaetung    = round(sum(max(f["verspaetung_min"], 0) for f in aktive) / max(len(aktive), 1), 2)
    puenktlich         = sum(1 for f in aktive if f["verspaetung_min"] < 5)
    puenktlichkeitsrate = round(puenktlich / max(len(aktive), 1) * 100, 2)

    return {
        "datum":                        datum,
        "gesamt_km":                    round(gesamt_km, 2),
        "gesamt_passagiere":            gesamt_passagiere,
        "gesamt_umsatz_eur":            gesamt_umsatz,
        "durchschnitt_auslastung":      avg_auslastung,
        "durchschnitt_verspaetung_min": avg_verspaetung,
        "puenktlichkeitsrate_prozent":  puenktlichkeitsrate,
    }


# ─── Основной скрипт ────────────────────────────────────────────────────────

print("🚀 Starte IVU Seed-Daten-Generierung (30 Tage)...")

with engine.begin() as conn:

    # Очищаем старые данные
    conn.execute(text("TRUNCATE ivu_ticketing, ivu_fahrten, ivu_kpi_daily RESTART IDENTITY CASCADE"))

    total_fahrten  = 0
    total_tickets  = 0

    for day_offset in range(30):
        datum   = START_DATUM + timedelta(days=day_offset)
        fahrten = generate_fahrten(datum)

        inserted_ids = []
        for f in fahrten:
            result = conn.execute(text("""
                INSERT INTO ivu_fahrten
                    (datum, linie, richtung, fahrzeug_nr, fahrer_id,
                     start_zeit, ende_zeit, soll_start, soll_ende,
                     verspaetung_min, km_gesamt, passagiere_einsteig,
                     auslastung_prozent, energie_verbrauch_kwh, status)
                VALUES
                    (:datum, :linie, :richtung, :fahrzeug_nr, :fahrer_id,
                     :start_zeit, :ende_zeit, :soll_start, :soll_ende,
                     :verspaetung_min, :km_gesamt, :passagiere_einsteig,
                     :auslastung_prozent, :energie_verbrauch_kwh, :status)
                RETURNING fahrt_id
            """), f)
            fahrt_id = result.scalar()
            inserted_ids.append((fahrt_id, f["passagiere_einsteig"], f["soll_start"]))

        total_fahrten += len(fahrten)

        # Ticketing — не для каждого пассажира чтобы не раздувать БД
        for fahrt_id, passagiere, soll_start in inserted_ids:
            sample = min(passagiere, random.randint(5, 15))
            tickets = generate_ticketing(fahrt_id, sample, datum, soll_start)
            for t in tickets:
                conn.execute(text("""
                    INSERT INTO ivu_ticketing
                        (fahrt_id, zeit, tarif_typ, betrag_eur, zahlungsart, haltestelle)
                    VALUES
                        (:fahrt_id, :zeit, :tarif_typ, :betrag_eur, :zahlungsart, :haltestelle)
                """), t)
            total_tickets += len(tickets)

        # KPI за день
        kpi = compute_kpi(datum, fahrten)
        conn.execute(text("""
            INSERT INTO ivu_kpi_daily
                (datum, gesamt_km, gesamt_passagiere, gesamt_umsatz_eur,
                 durchschnitt_auslastung, durchschnitt_verspaetung_min, puenktlichkeitsrate_prozent)
            VALUES
                (:datum, :gesamt_km, :gesamt_passagiere, :gesamt_umsatz_eur,
                 :durchschnitt_auslastung, :durchschnitt_verspaetung_min, :puenktlichkeitsrate_prozent)
            ON CONFLICT (datum) DO UPDATE SET
                gesamt_km                    = EXCLUDED.gesamt_km,
                gesamt_passagiere            = EXCLUDED.gesamt_passagiere,
                gesamt_umsatz_eur            = EXCLUDED.gesamt_umsatz_eur,
                durchschnitt_auslastung      = EXCLUDED.durchschnitt_auslastung,
                durchschnitt_verspaetung_min = EXCLUDED.durchschnitt_verspaetung_min,
                puenktlichkeitsrate_prozent  = EXCLUDED.puenktlichkeitsrate_prozent
        """), kpi)

        print(f"  ✅ {datum}: {len(fahrten)} Fahrten, {total_tickets} Tickets gesamt")

print(f"\n✅ Fertig! {total_fahrten} Fahrten, {total_tickets} Ticketing-Einträge, 30 KPI-Tage generiert.")