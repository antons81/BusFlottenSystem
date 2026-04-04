import streamlit as st
import pandas as pd
from app.secure_db import execute_safe_query
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import glob
import time
import pytz
from generate_pdf_report import generate_pdf_report
from auto_reports import create_weekly_report, create_monthly_report, send_report_email
from ai_analysis import generate_ai_summary, get_fleet_data_for_ai

# ====================== KONFIGURATION ======================
st.set_page_config(
    page_title="go:on – Flottenmanagement",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== CSS ======================
st.markdown("""
<style>
    /* ── Hintergrund ── */
    .stApp {
        background: linear-gradient(135deg, #f0f4f8 0%, #e8eef4 50%, #f4f0f8 100%);
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f36 0%, #2d3561 60%, #1e3a5f 100%);
        border-right: none;
    }
    [data-testid="stSidebar"] * { color: rgba(255,255,255,0.88) !important; }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: white !important; font-weight: 600 !important;
    }
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15) !important; }
    [data-testid="stSidebar"] .stButton button {
        background: rgba(255,255,255,0.12) !important;
        border: 1px solid rgba(255,255,255,0.25) !important;
        color: white !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(255,255,255,0.22) !important;
        border-color: rgba(255,255,255,0.45) !important;
        color: white !important;
    }
    /* Download button in sidebar */
    [data-testid="stSidebar"] [data-testid="stDownloadButton"] button {
        background: rgba(255,255,255,0.12) !important;
        border: 1px solid rgba(255,255,255,0.25) !important;
        color: white !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stDownloadButton"] button:hover {
        background: rgba(255,255,255,0.22) !important;
        color: white !important;
    }

    /* Logout button speziell */
    [data-testid="stSidebar"] .stButton button[kind="secondary"] {
        background: rgba(239,68,68,0.15) !important;
        border: 1px solid rgba(239,68,68,0.45) !important;
        color: #fca5a5 !important;
    }
    [data-testid="stSidebar"] .stButton button[kind="secondary"]:hover {
        background: rgba(239,68,68,0.28) !important;
        color: white !important;
    }

    /* ── Metric Karten ── */
    [data-testid="stMetric"] {
        background: white;
        border-radius: 14px;
        padding: 1.1rem 1.3rem !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.07);
        border: 1px solid rgba(255,255,255,0.9);
        position: relative;
        overflow: hidden;
    }
    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2, #f64f59);
    }
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    [data-testid="stMetricValue"] {
        color: #1e293b !important;
        font-weight: 700 !important;
        font-size: 1.7rem !important;
    }

    /* ── Buttons ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        border-radius: 10px !important;
        color: white !important;
        font-weight: 500 !important;
        box-shadow: 0 4px 12px rgba(102,126,234,0.35) !important;
        transition: all 0.2s !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 16px rgba(102,126,234,0.5) !important;
        transform: translateY(-1px);
    }
    .stButton > button[kind="secondary"] {
        background: white !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 10px !important;
        color: #475569 !important;
        font-weight: 500 !important;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: #667eea !important;
        color: #667eea !important;
    }

    /* ── Section title ── */
    .section-title {
        font-size: 0.88rem;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-bottom: 0.8rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #e2e8f0;
    }

    /* ── Dataframes ── */
    [data-testid="stDataFrame"] {
        border-radius: 12px !important;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    /* ── Login card ── */
    .login-card {
        background: white;
        border-radius: 20px;
        padding: 2.5rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.10);
    }
</style>
""", unsafe_allow_html=True)


# ====================== AUTHENTIFIZIERUNG ======================
def check_auth():
    # Sitzung bei Seitenaktualisierung wiederherstellen
    if "authenticated" not in st.session_state:
        params = st.query_params
        secret = os.getenv("DASHBOARD_PASSWORD", "goon2026")
        if params.get("session") == secret:
            st.session_state.authenticated = True
        else:
            st.session_state.authenticated = False

    if st.session_state.authenticated:
        # Sitzung in URL-Parametern speichern
        st.query_params["session"] = os.getenv("DASHBOARD_PASSWORD", "goon2026")
        return True

    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; padding: 2.5rem 0 1.5rem;">
            <div style="font-size:3.5rem">🚌</div>
            <h2 style="color:#1e293b; margin:0.3rem 0 0; font-weight:700">go:on</h2>
            <p style="color:#64748b; margin:0.3rem 0 0; font-size:0.9rem">
                Flottenmanagement-System
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.container():
            username = st.text_input("Benutzername", placeholder="admin")
            password = st.text_input("Passwort", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔐 Anmelden", type="primary", use_container_width=True):
                valid_user = os.getenv("DASHBOARD_USER", "admin")
                valid_pass = os.getenv("DASHBOARD_PASSWORD", "goon2026")
                if username == valid_user and password == valid_pass:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Ungültige Zugangsdaten")

        st.markdown("""
        <p style="text-align:center; color:#94a3b8; font-size:0.72rem; margin-top:1.5rem">
        © go:on Gesellschaft für Bus- und Schienenverkehr mbH
        </p>
        """, unsafe_allow_html=True)
    return False


if not check_auth():
    st.stop()


# ====================== SIDEBAR ======================
with st.sidebar:
    st.markdown("""
    <div style="padding:0.5rem 0 1rem; text-align:center">
        <div style="font-size:2rem">🚌</div>
        <div style="font-size:1.1rem; font-weight:700; margin-top:0.3rem">go:on</div>
        <div style="font-size:0.72rem; opacity:0.55">Flottenmanagement</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📚 Berichte")

    reports = sorted(glob.glob("reports/*.pdf"), reverse=True)
    if reports:
        for rp in reports:
            name  = os.path.basename(rp)
            short = name[:26] + "…" if len(name) > 26 else name
            c1, c2, c3 = st.columns([5, 2, 2])
            with c1:
                st.markdown(f"<small>📄 {short}</small>", unsafe_allow_html=True)
            with c2:
                with open(rp, "rb") as f:
                    st.download_button("↓", data=f.read(), file_name=name,
                                       mime="application/pdf", key=f"dl_{rp}")
            with c3:
                if st.button("🗑", key=f"del_{rp}"):
                    os.remove(rp); st.rerun()
    else:
        st.info("Noch keine Berichte.")

    st.divider()
    if st.button("🚪 Abmelden", use_container_width=True, type="secondary"):
        st.session_state.authenticated = False
        st.query_params.clear()
        st.rerun()


# ====================== DATEN ======================
total    = execute_safe_query("SELECT COUNT(*) as c FROM busse")[0]['c']
active   = execute_safe_query("SELECT COUNT(*) as c FROM busse WHERE status = 'aktiv'")[0]['c']
in_rep   = execute_safe_query("SELECT COUNT(*) as c FROM busse WHERE status = 'in_wartung'")[0]['c']
overdue  = execute_safe_query("""
    SELECT COUNT(*) as c FROM wartung
    WHERE status = 'überfällig' OR naechste_faellig < CURRENT_DATE
""")[0]['c']
avg_occ  = execute_safe_query(
    "SELECT ROUND(COALESCE(AVG(auslastung_prozent),0),1) as a FROM fahrten"
)[0]['a']
total_km = execute_safe_query(
    "SELECT COALESCE(SUM(km_gesamt),0) as s FROM fahrten"
)[0]['s']


# ====================== HEADER ======================
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, #1a1f36 0%, #2d3561 50%, #1e3a5f 100%);
    border-radius: 16px;
    padding: 1.4rem 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(26,31,54,0.25);
    display: flex;
    align-items: center;
    justify-content: space-between;
">
    <div>
        <div style="font-size:0.7rem; color:rgba(255,255,255,0.45);
                    text-transform:uppercase; letter-spacing:0.12em; margin-bottom:0.3rem">
            Flottenmanagement-System
        </div>
        <div style="font-size:1.45rem; font-weight:700; color:white">
            go:on &nbsp;–&nbsp; Busflotten Dashboard
        </div>
        <div style="font-size:0.78rem; color:rgba(255,255,255,0.5); margin-top:0.2rem">
            Gesellschaft für Bus- und Schienenverkehr mbH
        </div>
    </div>
    <div style="text-align:right">
        <div style="font-size:0.7rem; color:rgba(255,255,255,0.4); margin-bottom:0.2rem">Stand</div>
        <div style="font-size:1rem; font-weight:600; color:rgba(255,255,255,0.85)">
            {datetime.now().strftime('%d.%m.%Y')}
        </div>
        <div style="font-size:0.82rem; color:rgba(255,255,255,0.5)">
            {datetime.now(tz=pytz.timezone('Europe/Berlin')).strftime('%H:%M')} Uhr
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ====================== KPI ======================
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("🚌 Gesamte Busse",  total)
c2.metric("✅ Aktiv",           active)
c3.metric("🔧 In Wartung",      in_rep)
c4.metric("⚠️ Überfällig",      overdue,
          delta="kritisch" if overdue > 0 else None, delta_color="inverse")
c5.metric("📊 Ø Auslastung",    f"{avg_occ}%")
c6.metric("🛣️ Gesamt-km",       f"{total_km:,}")

st.markdown("<br>", unsafe_allow_html=True)


# ====================== AKTIONEN ======================
st.markdown('<div class="section-title">📄 Berichte & Aktionen</div>',
            unsafe_allow_html=True)

ca, cb, cc, cd = st.columns(4)
with ca:
    if st.button("📄 Wochenbericht erstellen", type="primary", use_container_width=True):
        with st.spinner("Wird erstellt…"):
            p = generate_pdf_report("weekly")
            st.success(f"✅ {os.path.basename(p)}")
            time.sleep(1); st.rerun()
with cb:
    if st.button("📅 Monatsbericht erstellen", type="primary", use_container_width=True):
        with st.spinner("Wird erstellt…"):
            p = generate_pdf_report("monthly")
            st.success(f"✅ {os.path.basename(p)}")
            time.sleep(1); st.rerun()
with cc:
    if st.button("📨 Per E-Mail versenden", type="secondary", use_container_width=True):
        with st.spinner("Erstelle & sende…"):
            p = create_weekly_report(send_email=True)
            st.success("✅ E-Mail versendet!" if p else "❌ Fehler")
            time.sleep(1.5); st.rerun()
with cd:
    if st.button("🚀 Force Test", type="secondary", use_container_width=True):
        with st.spinner("…"):
            create_weekly_report(send_email=False)
            st.success("✅ Test-Bericht erstellt!")
            time.sleep(1); st.rerun()

st.markdown("<br>", unsafe_allow_html=True)


# ====================== DIAGRAMME ======================
st.markdown('<div class="section-title">📊 Kilometerleistung & Auslastung</div>',
            unsafe_allow_html=True)

df = pd.DataFrame(execute_safe_query("""
    SELECT
        f.datum,
        COALESCE(b.kennzeichen, 'Bus' || f.bus_id::text) as kennzeichen,
        f.km_gesamt,
        f.auslastung_prozent as "Auslastung %"
    FROM fahrten f
    LEFT JOIN busse b ON f.bus_id = b.bus_id
    ORDER BY f.datum
"""))

PALETTE = [
    "#667eea","#f093fb","#4facfe","#43e97b","#fa709a",
    "#764ba2","#fee140","#30cfd0","#a18cd1","#fbc2eb"
]

LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="sans-serif", color="#475569", size=11),
    title_font=dict(size=13, color="#1e293b"),
    legend=dict(
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="rgba(0,0,0,0.06)",
        borderwidth=1,
        font=dict(size=10)
    ),
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis=dict(showgrid=False, linecolor="#e2e8f0", tickfont=dict(size=10)),
    yaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0", tickfont=dict(size=10), title=None),
)

if not df.empty:
    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.bar(df, x='datum', y='km_gesamt', color='kennzeichen',
                      title="Gefahrene Kilometer pro Tag",
                      color_discrete_sequence=PALETTE, template="none")
        fig1.update_layout(**LAYOUT)
        fig1.update_traces(marker_line_width=0, opacity=0.88)
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        fig2 = px.line(df, x='datum', y='Auslastung %', color='kennzeichen',
                       title="Auslastung der Busse (%)",
                       color_discrete_sequence=PALETTE, template="none")
        fig2.update_layout(**LAYOUT)
        fig2.update_traces(line_width=2.5)
        fig2.add_hline(y=80, line_dash="dot", line_color="#f64f59", line_width=1.5,
                       annotation_text="Ziel 80%",
                       annotation_font=dict(color="#f64f59", size=10),
                       annotation_position="top left")
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("Keine Fahrtendaten vorhanden.")

st.markdown("<br>", unsafe_allow_html=True)


# ====================== WARTUNGEN ======================
st.markdown('<div class="section-title">⚠️ Überfällige Wartungen</div>',
            unsafe_allow_html=True)

overdue_df = pd.DataFrame(execute_safe_query("""
    SELECT
        COALESCE(b.kennzeichen, 'Bus' || w.bus_id::text) as "Kennzeichen",
        w.datum              as "Wartungsdatum",
        w.typ                as "Typ",
        w.naechste_faellig   as "Fällig am",
        w.status             as "Status"
    FROM wartung w
    LEFT JOIN busse b ON w.bus_id = b.bus_id
    WHERE w.status = 'überfällig' OR w.naechste_faellig < CURRENT_DATE
"""))

if not overdue_df.empty:
    st.dataframe(overdue_df, use_container_width=True, hide_index=True)
else:
    st.success("✅ Keine überfälligen Wartungen.")

st.markdown("<br>", unsafe_allow_html=True)


# ====================== FLOTTE ======================
st.markdown('<div class="section-title">🚌 Busflotten Übersicht</div>',
            unsafe_allow_html=True)

fleet_df = pd.DataFrame(execute_safe_query("""
    SELECT kennzeichen as "Kennzeichen", modell as "Modell",
           baujahr as "Baujahr", km_stand as "km-Stand", status as "Status"
    FROM busse ORDER BY kennzeichen
"""))
if not fleet_df.empty:
    st.dataframe(fleet_df, use_container_width=True, hide_index=True)


# ====================== FOOTER ======================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; padding:0.8rem 0">
    <span style="color:#94a3b8; font-size:0.72rem">
    © go:on Gesellschaft für Bus- und Schienenverkehr mbH &nbsp;·&nbsp;
    Flottenmanagement-System &nbsp;·&nbsp; Prototyp v1.0
    </span>
</div>
""", unsafe_allow_html=True)