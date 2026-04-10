import streamlit as st
import pandas as pd
from app.secure_db import execute_safe_query
import plotly.express as px
from datetime import datetime
import os
import glob
import time
import pytz

from generate_pdf_report import generate_pdf_report, generate_ki_pdf
from auto_reports import create_weekly_report
from ai_analysis import generate_ai_summary
from app.models import AIAnalyseResponse

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
    .stApp { background: linear-gradient(135deg, #f0f4f8 0%, #e8eef4 50%, #f4f0f8 100%); }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f36 0%, #2d3561 60%, #1e3a5f 100%);
        border-right: none;
    }
            
    [data-testid="stSidebar"] * { color: rgba(255,255,255,0.88) !important; }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: white !important; font-weight: 600 !important; }
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15) !important; }
    [data-testid="stSidebar"] .stButton button {
        background: rgba(255,255,255,1) !important;
        border: 1px solid rgba(255,255,255,1) !important;
        color: white !important; border-radius: 8px !important;
    }
    
    [data-testid="stSidebar"] .stButton button:hover { background: rgba(255,255,255,0.12) !important; }
    .report-name {
        display: -webkit-box;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 5;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: normal !important;
        line-height: 1.2rem;
        max-height: 5.6rem;
        word-break: break-word;
    }
    .report-name .report-icon {
        margin-right: 0.35rem;
        color: #ffffff;
    }
    .report-name .report-text {
        color: #f8fafc;
        font-size: 1rem;
        font-weight: 500;
    }
    [data-testid="stSidebar"] [data-testid="stDownloadButton"] button {
        background: rgba(255,255,255,0.12) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        color: white !important; border-radius: 8px !important;
    }
            
    [data-testid="stMetric"] {
        background: white; border-radius: 14px;
        padding: 1.1rem 1.3rem !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.07);
        position: relative; overflow: hidden;
    }
    
    [data-testid="stMetric"]::before {
        content: ''; position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2, #f64f59);
    }
    [data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.78rem !important; text-transform: uppercase; }
    [data-testid="stMetricValue"] { color: #1e293b !important; font-weight: 700 !important; font-size: 1.7rem !important; }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important; border-radius: 10px !important;
        color: white !important; font-weight: 500 !important;
        box-shadow: 0 4px 12px rgba(102,126,234,0.35) !important;
    }
    .stButton > button[kind="secondary"] {
        background: rgba(255,255,255,0.12) !important; border: 1.5px solid rgba(255,255,255,0.12) !important;
        border-radius: 10px !important; color: #475569 !important;
    }
    .section-title {
        font-size: 0.88rem; font-weight: 600; color: #475569;
        text-transform: uppercase; letter-spacing: 0.07em;
        margin-bottom: 0.8rem; padding-bottom: 0.5rem;
        border-bottom: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: white; border-radius: 12px;
        padding: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important; font-weight: 500 !important;
        color: #64748b !important; padding-left: 16px !important; padding-right: 16px !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ====================== AUTHENTIFIZIERUNG ======================
def check_auth():
    if "authenticated" not in st.session_state:
        params = st.query_params
        secret = os.getenv("DASHBOARD_PASSWORD", "goon2026")
        st.session_state.authenticated = params.get("session") == secret

    if st.session_state.authenticated:
        st.query_params["session"] = os.getenv("DASHBOARD_PASSWORD", "goon2026")
        return True

    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; padding: 2.5rem 0 1.5rem;">
            <div style="font-size:3.5rem">🚌</div>
            <h2 style="color:#1e293b; margin:0.3rem 0 0; font-weight:700">go:on</h2>
            <p style="color:#64748b; margin:0.3rem 0 0; font-size:0.9rem">Flottenmanagement-System</p>
        </div>
        """, unsafe_allow_html=True)
        username = st.text_input("Benutzername", placeholder="admin")
        password = st.text_input("Passwort", type="password", placeholder="••••••••")
        if st.button("🔐 Anmelden", type="primary", use_container_width=True):
            if username == os.getenv("DASHBOARD_USER", "admin") and password == os.getenv("DASHBOARD_PASSWORD", "goon2026"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Ungültige Zugangsdaten")
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
            name = os.path.basename(rp)
            c1, c2, c3 = st.columns([5, 2, 2])
            with c1:
                st.markdown(
                    f"<small class=\"report-name\"><span class=\"report-icon\">📄</span>"
                    f"<span class=\"report-text\">{name}</span></small>",
                    unsafe_allow_html=True
                )
            with c2:
                with open(rp, "rb") as f:
                    st.download_button("💾", data=f.read(), file_name=name, mime="application/pdf", key=f"dl_{rp}")
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

# ====================== PALETTE & LAYOUT ======================
PALETTE = ["#667eea","#f093fb","#4facfe","#43e97b","#fa709a","#764ba2","#fee140","#30cfd0","#a18cd1","#fbc2eb"]
LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="arial", color="#475569", size=12),
    title_font=dict(size=13, color="#1e293b"),
    legend=dict(bgcolor="rgba(255,255,255,0.85)", bordercolor="rgba(0,0,0,0.06)", borderwidth=1, font=dict(size=10)),
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis=dict(showgrid=False, linecolor="#e2e8f0", tickfont=dict(size=10)),
    yaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0", tickfont=dict(size=10), title=None),
)

# ====================== HEADER ======================
st.markdown(f"""
<div style="background: linear-gradient(135deg, #1a1f36 0%, #2d3561 50%, #1e3a5f 100%);
            border-radius: 16px; padding: 1.4rem 2rem; margin-bottom: 1.5rem;
            box-shadow: 0 8px 32px rgba(26,31,54,0.25);
            display: flex; align-items: center; justify-content: space-between;">
    <div>
        <div style="font-size:0.7rem; color:rgba(255,255,255,0.45); text-transform:uppercase; letter-spacing:0.12em; margin-bottom:0.3rem">
            Flottenmanagement-System
        </div>
        <div style="font-size:1.45rem; font-weight:700; color:white">go:on &nbsp;–&nbsp; Busflotten Dashboard</div>
        <div style="font-size:0.78rem; color:rgba(255,255,255,0.5); margin-top:0.2rem">
            Gesellschaft für Bus- und Schienenverkehr mbH
        </div>
    </div>
    <div style="text-align:right">
        <div style="font-size:0.7rem; color:rgba(255,255,255,0.4); margin-bottom:0.2rem">Stand</div>
        <div style="font-size:1rem; font-weight:600; color:rgba(255,255,255,0.85)">{datetime.now().strftime('%d.%m.%Y')}</div>
        <div style="font-size:0.82rem; color:rgba(255,255,255,0.5)">{datetime.now(tz=pytz.timezone('Europe/Berlin')).strftime('%H:%M')} Uhr</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ====================== KPI ======================
ivu_top = execute_safe_query("""
    SELECT
        COUNT(*) as fahrten,
        ROUND(AVG(auslastung_prozent)::numeric, 1) as avg_auslastung,
        ROUND(AVG(verspaetung_min)::numeric, 1) as avg_verspaetung,
        SUM(passagiere_einsteig) as passagiere,
        ROUND(SUM(COALESCE(energie_verbrauch_kwh,0))::numeric, 0) as energie,
        ROUND(100.0 * SUM(CASE WHEN COALESCE(verspaetung_min, 0) <= 5 THEN 1 ELSE 0 END)::numeric
              / NULLIF(COUNT(*), 0), 1) as puenktlichkeit
    FROM ivu_fahrten
""")[0]

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("🚍 Fahrten gesamt", f"{ivu_top['fahrten']:,}")
c2.metric("👥 Ø Auslastung", f"{ivu_top['avg_auslastung']}%")
c3.metric("⏱ Ø Verspätung", f"{ivu_top['avg_verspaetung']} min")
c4.metric("🎫 Passagiere", f"{ivu_top['passagiere']:,}")
c5.metric("⚡ Energie", f"{ivu_top['energie']:,} kWh")
c6.metric("✅ Pünktlichkeit", f"{ivu_top['puenktlichkeit']}%",
          delta="gut" if ivu_top['puenktlichkeit'] and ivu_top['puenktlichkeit'] >= 80 else "kritisch",
          delta_color="normal" if ivu_top['puenktlichkeit'] and ivu_top['puenktlichkeit'] >= 80 else "inverse")

st.markdown("<br>", unsafe_allow_html=True)

# ====================== TABS ======================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 PDF-Berichte",
    "📡 IVU – Fahrten",
    "🎫 IVU – Ticketing",
    "📈 KPI-Trends",
    "🤖 KI-Analyse"
])

# ─── TAB 1: PDF-Berichte ────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-title">📄 Berichte & Aktionen</div>', unsafe_allow_html=True)
    ca, cb, cc = st.columns(3)
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
            with st.spinner("Sende E-Mail…"):
                create_weekly_report(send_email=True)
                st.success("✅ E-Mail versendet!")
                time.sleep(1.5); st.rerun()

# ─── TAB 2: IVU Fahrten ─────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-title">📡 IVU – Fahrtenanalyse</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        pünkt_df = pd.DataFrame(execute_safe_query("""
            SELECT linie,
                   ROUND(100.0 * SUM(CASE WHEN verspaetung_min <= 5 THEN 1 ELSE 0 END)
                         / COUNT(*), 1) as puenktlichkeit,
                   ROUND(AVG(verspaetung_min)::numeric, 1) as avg_verspaetung
            FROM ivu_fahrten GROUP BY linie ORDER BY linie
        """))
        if not pünkt_df.empty:
            fig = px.bar(pünkt_df, x='linie', y='puenktlichkeit',
                         title="Pünktlichkeitsrate pro Linie (%)",
                         color='puenktlichkeit',
                         color_continuous_scale=["#f64f59","#fee140","#43e97b"],
                         template="none", text='puenktlichkeit')
            fig.update_layout(**LAYOUT)
            fig.update_traces(texttemplate='%{text}%', textposition='outside')
            fig.add_hline(y=80, line_dash="dot", line_color="#f64f59", annotation_text="Ziel 80%")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        status_df = pd.DataFrame(execute_safe_query("""
            SELECT status, COUNT(*) as anzahl FROM ivu_fahrten GROUP BY status
        """))
        if not status_df.empty:
            fig = px.pie(status_df, names='status', values='anzahl',
                         title="Fahrtstatus Verteilung",
                         color_discrete_sequence=["#43e97b","#fee140","#f64f59"],
                         template="none")
            fig.update_layout(**LAYOUT)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

    verspaetung_df = pd.DataFrame(execute_safe_query("""
        SELECT datum,
               ROUND(AVG(verspaetung_min)::numeric, 2) as avg_verspaetung,
               ROUND(AVG(auslastung_prozent)::numeric, 2) as avg_auslastung
        FROM ivu_fahrten GROUP BY datum ORDER BY datum
    """))
    col1, col2 = st.columns(2)
    with col1:
        if not verspaetung_df.empty:
            fig = px.line(verspaetung_df, x='datum', y='avg_verspaetung',
                          title="Ø Verspätung pro Tag (min)",
                          color_discrete_sequence=["#f64f59"], template="none")
            fig.update_layout(**LAYOUT)
            fig.update_traces(line_width=2.5, fill='tozeroy', fillcolor='rgba(246,79,89,0.08)')
            fig.add_hline(y=5, line_dash="dot", line_color="#fee140", annotation_text="Grenze 5 min")
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        if not verspaetung_df.empty:
            fig = px.line(verspaetung_df, x='datum', y='avg_auslastung',
                          title="Ø Auslastung pro Tag (%)",
                          color_discrete_sequence=["#667eea"], template="none")
            fig.update_layout(**LAYOUT)
            fig.update_traces(line_width=2.5, fill='tozeroy', fillcolor='rgba(102,126,234,0.08)')
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">🗓 Letzte Fahrten</div>', unsafe_allow_html=True)
    fahrten_df = pd.DataFrame(execute_safe_query("""
        SELECT datum as "Datum", linie as "Linie", richtung as "Richtung",
               fahrzeug_nr as "Fahrzeug", fahrer_id as "Fahrer",
               verspaetung_min as "Verspätung (min)",
               auslastung_prozent as "Auslastung %",
               passagiere_einsteig as "Passagiere",
               status as "Status"
        FROM ivu_fahrten
        ORDER BY datum DESC, start_zeit DESC LIMIT 50
    """))
    if not fahrten_df.empty:
        st.dataframe(fahrten_df, use_container_width=True, hide_index=True)

# ─── TAB 3: IVU Ticketing ───────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-title">🎫 IVU – Ticketing & Einnahmen</div>', unsafe_allow_html=True)

    tick_kpi = execute_safe_query("""
        SELECT COUNT(*) as validierungen,
               ROUND(SUM(betrag_eur)::numeric, 2) as umsatz,
               ROUND(AVG(betrag_eur)::numeric, 2) as avg_ticket
        FROM ivu_ticketing
    """)[0]

    k1, k2, k3 = st.columns(3)
    k1.metric("🎫 Validierungen gesamt", f"{tick_kpi['validierungen']:,}")
    k2.metric("💶 Gesamtumsatz", f"{tick_kpi['umsatz']:,} €")
    k3.metric("💳 Ø Ticketpreis", f"{tick_kpi['avg_ticket']} €")

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        tarif_df = pd.DataFrame(execute_safe_query("""
            SELECT tarif_typ, COUNT(*) as anzahl,
                   ROUND(SUM(betrag_eur)::numeric, 2) as umsatz
            FROM ivu_ticketing GROUP BY tarif_typ ORDER BY anzahl DESC
        """))
        if not tarif_df.empty:
            fig = px.bar(tarif_df, x='tarif_typ', y='anzahl',
                         title="Tickets nach Typ (Anzahl)",
                         color='umsatz', color_continuous_scale=["#667eea","#764ba2"],
                         template="none", text='anzahl')
            fig.update_layout(**LAYOUT)
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        zahlung_df = pd.DataFrame(execute_safe_query("""
            SELECT zahlungsart, COUNT(*) as anzahl FROM ivu_ticketing GROUP BY zahlungsart
        """))
        if not zahlung_df.empty:
            fig = px.pie(zahlung_df, names='zahlungsart', values='anzahl',
                         title="Zahlungsarten Verteilung",
                         color_discrete_sequence=PALETTE, template="none")
            fig.update_layout(**LAYOUT)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        halt_df = pd.DataFrame(execute_safe_query("""
            SELECT haltestelle, COUNT(*) as einsteiger
            FROM ivu_ticketing GROUP BY haltestelle ORDER BY einsteiger DESC LIMIT 10
        """))
        if not halt_df.empty:
            fig = px.bar(halt_df, x='einsteiger', y='haltestelle',
                         title="Top 10 Haltestellen (Einsteiger)",
                         orientation='h', color_discrete_sequence=["#4facfe"], template="none")
            fig.update_layout(**LAYOUT)
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        umsatz_df = pd.DataFrame(execute_safe_query("""
            SELECT DATE(zeit) as datum,
                   ROUND(SUM(betrag_eur)::numeric, 2) as tagesumsatz
            FROM ivu_ticketing GROUP BY DATE(zeit) ORDER BY datum
        """))
        if not umsatz_df.empty:
            fig = px.bar(umsatz_df, x='datum', y='tagesumsatz',
                         title="Tagesumsatz (€)",
                         color_discrete_sequence=["#43e97b"], template="none")
            fig.update_layout(**LAYOUT)
            fig.update_traces(marker_line_width=0, opacity=0.88)
            st.plotly_chart(fig, use_container_width=True)

# ─── TAB 4: KPI-Trends ──────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-title">📈 KPI-Trends (30 Tage)</div>', unsafe_allow_html=True)

    kpi_df = pd.DataFrame(execute_safe_query("""
        SELECT datum, gesamt_km, gesamt_passagiere, gesamt_umsatz_eur,
               durchschnitt_auslastung, durchschnitt_verspaetung_min,
               puenktlichkeitsrate_prozent
        FROM ivu_kpi_daily ORDER BY datum
    """))

    if not kpi_df.empty:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.line(kpi_df, x='datum', y='gesamt_passagiere',
                          title="Passagiere pro Tag",
                          color_discrete_sequence=["#667eea"], template="none")
            fig.update_layout(**LAYOUT)
            fig.update_traces(line_width=2.5, fill='tozeroy', fillcolor='rgba(102,126,234,0.08)')
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.line(kpi_df, x='datum', y='gesamt_umsatz_eur',
                          title="Tagesumsatz (€)",
                          color_discrete_sequence=["#43e97b"], template="none")
            fig.update_layout(**LAYOUT)
            fig.update_traces(line_width=2.5, fill='tozeroy', fillcolor='rgba(67,233,123,0.08)')
            st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            fig = px.line(kpi_df, x='datum', y='puenktlichkeitsrate_prozent',
                          title="Pünktlichkeitsrate (%)",
                          color_discrete_sequence=["#4facfe"], template="none")
            fig.update_layout(**LAYOUT)
            fig.update_traces(line_width=2.5)
            fig.add_hline(y=80, line_dash="dot", line_color="#f64f59", annotation_text="Ziel 80%")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(kpi_df, x='datum', y='gesamt_km',
                         title="Gesamtkilometer pro Tag",
                         color_discrete_sequence=["#f093fb"], template="none")
            fig.update_layout(**LAYOUT)
            fig.update_traces(marker_line_width=0, opacity=0.88)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">📋 KPI Übersichtstabelle</div>', unsafe_allow_html=True)
        display_df = kpi_df.copy()
        display_df.columns = ["Datum","Gesamt-km","Passagiere","Umsatz (€)","Ø Auslastung %","Ø Verspätung min","Pünktlichkeit %"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# ─── TAB 5: KI-Analyse ──────────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-title">🤖 KI-Flottenanalyse</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 4])
    with col1:
        report_type = st.selectbox("Berichtstyp", ["weekly", "monthly"],
                                   format_func=lambda x: "Wöchentlich" if x == "weekly" else "Monatlich")
    with col2:
        provider = st.selectbox("KI-Anbieter", ["ollama", "claude"],
                                format_func=lambda x: "🏠 Qwen2.5 3B (lokal, kostenlos)" if x == "ollama" else "☁️ Claude (Anthropic)")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        run_ai = st.button("🤖 Analyse starten", type="primary", use_container_width=True)

    if run_ai:
        with st.spinner(f"KI-Analyse läuft via {provider}…"):
            try:
                result: AIAnalyseResponse = generate_ai_summary(report_type=report_type, provider=provider)
                st.session_state["ki_result"] = result
            except Exception as e:
                st.error(f"Fehler: {str(e)}")
                st.session_state.pop("ki_result", None)

    if "ki_result" in st.session_state:
        result = st.session_state["ki_result"]
        st.caption(f"🤖 {result.provider_used} · {result.model_used}")
        st.markdown(result.summary)

        try:
            pdf_bytes = generate_ki_pdf(result, report_type=report_type)
            st.download_button(
                label="📄 Als PDF speichern",
                data=pdf_bytes,
                file_name=f"ki_analyse_{report_type}_{datetime.now(tz=pytz.timezone('Europe/Berlin')).strftime('%d-%m-%Y')}.pdf",
                mime="application/pdf",
            )
    
        except Exception as e:
            st.warning(f"PDF-Export nicht verfügbar: {e}")

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