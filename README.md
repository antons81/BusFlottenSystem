# 🚌 go:on – Flottenmanagement-System

> **Automatisierte Flottenüberwachung, KI-gestützte Berichterstattung und Datenaggregation**  
> *Prototyp entwickelt von Anton Stremovskyi · April 2026*

---

## 📋 Übersicht

Dieses System automatisiert die gesamte Berichterstattung für die Busflotte der **go:on Gesellschaft für Bus- und Schienenverkehr mbH**. Es aggregiert Daten aus mehreren Datenbanken, generiert professionelle PDF-Berichte mit KI-Analyse und versendet diese automatisch per E-Mail.

---

## ✨ Funktionen

| Feature | Beschreibung |
|---|---|
| 📊 **Dashboard** | Interaktives Streamlit-Dashboard mit Login, KPI-Übersicht und Echtzeit-Diagrammen |
| 📄 **PDF-Berichte** | Professionelle wöchentliche & monatliche Berichte im go:on-Corporate-Design |
| 🤖 **KI-Analyse** | Automatische Flottenauswertung & Handlungsempfehlungen via Claude AI |
| 📧 **E-Mail-Versand** | Automatischer Versand per SMTP mit APScheduler |
| 🔐 **Vault-Sicherheit** | Zugangsdaten werden sicher in HashiCorp Vault gespeichert |
| 🐳 **Docker** | Vollständig containerisiert mit Docker Compose |

---

## 🏗️ Architektur

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   DB Dortmund   │     │   DB Hamburg    │     │   DB Berlin     │
│   PostgreSQL    │     │   PostgreSQL    │     │   PostgreSQL    │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                        │
         └───────────────────────┼────────────────────────┘
                                 │ Daten
                    ┌────────────▼────────────┐
                    │                         │◄──── HashiCorp Vault
                    │        FastAPI           │      (Zugangsdaten)
                    │   Aggregation &          │
                    │   Zugriffssteuerung      │
                    └────────────┬────────────┘
                                 │ nur aggregierte Daten
                    ┌────────────▼────────────┐
                    │       Streamlit          │
                    │  Dashboard & Berichte    │
                    └─────────────────────────┘
```

> **Sicherheitsprinzip:** Streamlit hat keinen direkten Zugriff auf Vault oder die Quelldatenbanken. Nur FastAPI kommuniziert mit den Datenquellen.

---

## 🛠️ Technischer Stack

```
Backend       │ Python 3.12 + FastAPI
Datenbank     │ PostgreSQL 16 + SQLAlchemy
Sicherheit    │ HashiCorp Vault (KV v2)
Berichte      │ ReportLab (PDF)
KI-Analyse    │ Anthropic Claude API
Dashboard     │ Streamlit
Scheduler     │ APScheduler
Container     │ Docker + Docker Compose
E-Mail        │ SMTP (Gmail / Corporate)
```

---

## 🚀 Installation & Start

### Voraussetzungen

- Docker & Docker Compose
- Python 3.12+
- Anthropic API Key
- Gmail App Password (für E-Mail-Versand)

### 1. Repository klonen

```bash
git clone https://github.com/dein-username/goon-flottenmanagement.git
cd goon-flottenmanagement
```

### 2. Umgebungsvariablen konfigurieren

```bash
cp .env.example .env
```

`.env` ausfüllen:

```env
# Datenbank
POSTGRES_USER=busadmin
POSTGRES_PASSWORD=dein_passwort
POSTGRES_DB=busdb

# Vault
VAULT_TOKEN=myroot

# Dashboard
DASHBOARD_USER=admin
DASHBOARD_PASSWORD=dein_passwort

# E-Mail
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=deine@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
REPORT_EMAIL_TO=empfaenger@email.de

# KI
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. System starten

```bash
docker compose up -d
```

### 4. Datenbank initialisieren

```bash
docker exec -it bus-app python /app/init_db.py
docker exec -it bus-app python /app/seed_with_proper_id.py
```

### 5. Dashboard öffnen

```
http://localhost:8501
```

---

## 📁 Projektstruktur

```
goon-flottenmanagement/
│
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI Backend
│   └── secure_db.py         # Vault + Datenbankverbindung
│
├── streamlit_dashboard.py   # Dashboard UI
├── generate_pdf_report.py   # PDF-Generator
├── auto_reports.py          # Scheduler & E-Mail-Versand
├── ai_analysis.py           # Claude AI Integration
├── init_db.py               # Datenbankschema
├── seed_with_proper_id.py   # Testdaten
│
├── docker-compose.yml
├── Dockerfile
├── vault-init.sh            # Vault Auto-Setup
├── requirements.txt
└── .env.example
```

---

## 📊 Dashboard

Das Dashboard bietet:

- **6 KPI-Karten** — Gesamtbusse, Aktive, In Wartung, Überfällige, Auslastung, Gesamt-km
- **Interaktive Diagramme** — Kilometerleistung & Auslastung nach Kennzeichen
- **Wartungsübersicht** — Alle überfälligen Serviceintervalle auf einen Blick
- **Berichtsgenerator** — PDF per Knopfdruck oder automatisch per E-Mail
- **KI-Analyse** — Claude AI wertet Flottendaten aus und gibt Empfehlungen

**Login:** Zugangsdaten werden über Umgebungsvariablen konfiguriert.

---

## 🤖 KI-Analyse

Die KI-Analyse basiert auf **Anthropic Claude** und wertet automatisch aus:

1. **Gesamtbewertung** — Aktueller Zustand der Flotte
2. **Kritische Punkte** — Überfällige Wartungen, Hochkilometer-Fahrzeuge
3. **Auslastungsanalyse** — Effizienz der Fahrzeugdisposition
4. **Empfehlungen** — Konkrete Maßnahmen für das Management

Die Analyse wird automatisch in jeden PDF-Bericht integriert.

---

## ⏰ Automatischer Berichtsversand

| Bericht | Zeitplan | Format |
|---|---|---|
| Wochenbericht | Jeden Montag, 07:00 Uhr | PDF per E-Mail |
| Monatsbericht | 1. des Monats, 07:00 Uhr | PDF per E-Mail |

---

## 🔐 Sicherheitskonzept

- Alle Datenbankpasswörter werden in **HashiCorp Vault** gespeichert
- Das Dashboard hat **keinen direkten Datenbankzugriff**
- Nur FastAPI kommuniziert mit Vault und den Datenquellen
- `.env` Datei niemals in Git committen

---

## 🗺️ Weiterentwicklung

- [ ] Anbindung an echte Unternehmensdatenbanken
- [ ] Prädiktive Wartungsanalyse (Machine Learning)
- [ ] React Native App für Fahrerkommunikation
- [ ] Kubernetes für Produktionsbetrieb
- [ ] Erweiterte Benachrichtigungen (SMS, Push)

---

## 👤 Autor

**Anton Stremovskyi**  
Entwickler des Prototyps  
April 2026

---

<div align="center">
  <sub>Entwickelt für go:on Gesellschaft für Bus- und Schienenverkehr mbH</sub>
</div>
