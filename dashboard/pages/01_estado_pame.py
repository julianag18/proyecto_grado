"""
dashboard/pages/01_estado_pame.py
──────────────────────────────────────────────────────────────────────────────
Página principal del dashboard: Estado General del PAME.
Muestra los 6 KPIs, el gauge de cumplimiento y los gráficos de distribución.
──────────────────────────────────────────────────────────────────────────────
"""

import sys
from pathlib import Path

import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboard.components.data_loader import (
    cargar_estado_pame, calcular_kpis, es_modo_demo,
)
from dashboard.components.kpi_cards import (
    render_fila_kpis, render_section_header, render_banner_demo, render_sidebar_logo,
)
from dashboard.components.charts import (
    gauge_cumplimiento, barras_por_area, donut_estado_global,
    barras_tipo_servicio, timeline_vencimientos,
)

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Estado PAME — Laproff",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inyectar CSS global ───────────────────────────────────────────────────────
css_path = Path(__file__).resolve().parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    render_sidebar_logo()

    st.page_link("app.py",                  label="🏠 Inicio")
    st.page_link("pages/01_estado_pame.py", label="📊 Estado General")
    st.page_link("pages/02_cronograma.py",  label="📅 Cronograma")
    st.page_link("pages/03_alertas.py",     label="🔔 Alertas")
    st.page_link("pages/04_migracion.py",   label="📤 Migración ETL")

    st.markdown("<hr style='border-color:rgba(255,255,255,0.07);'>", unsafe_allow_html=True)

    if st.button("🔄 Actualizar datos", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

    st.markdown(
        "<div style='font-size:0.7rem; color:#484f58; text-align:center; margin-top:1rem;'>"
        "Práctica Académica · Bioingeniería<br>Laproff S.A.S. · 2026</div>",
        unsafe_allow_html=True,
    )

# ═════════════════════════════════════════════════════════════════════════════
# CARGA DE DATOS
# ═════════════════════════════════════════════════════════════════════════════
with st.spinner("Cargando datos del PAME..."):
    df_estado, is_live = cargar_estado_pame()
    kpis = calcular_kpis(df_estado)

# ═════════════════════════════════════════════════════════════════════════════
# HEADER
# ═════════════════════════════════════════════════════════════════════════════
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown(
        """
        <h1 style="font-size:1.7rem; font-weight:800; color:#e6edf3; margin:0;">
          📊 Estado General del PAME
        </h1>
        <p style="color:#8b949e; font-size:0.85rem; margin:0.3rem 0 0 0;">
          Programa de Aseguramiento Metrológico — Laboratorios Laproff S.A.S.
        </p>
        """,
        unsafe_allow_html=True,
    )

with col_status:
    from datetime import date
    st.markdown(
        f"""
        <div style="text-align:right; padding-top:0.5rem;">
          <div style="font-size:0.7rem; color:#484f58; text-transform:uppercase; letter-spacing:0.05em;">
            {'🟢 Conectado' if is_live else '🧪 Modo demo'}
          </div>
          <div style="font-size:0.75rem; color:#8b949e;">{date.today().strftime('%d/%m/%Y')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Banner demo
if es_modo_demo():
    render_banner_demo()

st.markdown("<hr>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — TARJETAS KPI
# ═════════════════════════════════════════════════════════════════════════════
render_section_header("Indicadores Clave (KPIs)", "Estado actual del inventario metrológico")
render_fila_kpis(kpis)

st.markdown("<br>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — GAUGE + DONUT
# ═════════════════════════════════════════════════════════════════════════════
render_section_header("Cumplimiento del programa", "Porcentaje de equipos con calibración vigente")

col_gauge, col_donut, col_tipo = st.columns([2, 2, 1.5], gap="medium")

with col_gauge:
    st.plotly_chart(
        gauge_cumplimiento(kpis["pct_al_dia"]),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with col_donut:
    st.plotly_chart(
        donut_estado_global(kpis),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with col_tipo:
    st.plotly_chart(
        barras_tipo_servicio(df_estado),
        use_container_width=True,
        config={"displayModeBar": False},
    )

st.markdown("<hr>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — BARRAS POR ÁREA + TIMELINE VENCIMIENTOS
# ═════════════════════════════════════════════════════════════════════════════
render_section_header("Análisis por área y vencimientos próximos")

col_area, col_timeline = st.columns([1.5, 1], gap="medium")

with col_area:
    st.plotly_chart(
        barras_por_area(df_estado),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with col_timeline:
    st.plotly_chart(
        timeline_vencimientos(df_estado, top_n=10),
        use_container_width=True,
        config={"displayModeBar": False},
    )

st.markdown("<hr>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — RESUMEN RÁPIDO EN NÚMEROS
# ═════════════════════════════════════════════════════════════════════════════
render_section_header("Resumen por área")

if not df_estado.empty and "area" in df_estado.columns:
    resumen_area = (
        df_estado.groupby("area")["estado_alerta"]
        .value_counts()
        .unstack(fill_value=0)
        .reindex(columns=["AL_DIA", "PROXIMO", "CRITICO", "VENCIDO", "SIN_DATOS"], fill_value=0)
        .rename(columns={
            "AL_DIA": "✅ Al día",
            "PROXIMO": "🟡 Próximos",
            "CRITICO": "🟠 Críticos",
            "VENCIDO": "🔴 Vencidos",
            "SIN_DATOS": "⚪ Sin datos",
        })
        .reset_index()
        .rename(columns={"area": "Área"})
    )
    resumen_area["Total"] = resumen_area.iloc[:, 1:].sum(axis=1)
    st.dataframe(
        resumen_area,
        use_container_width=True,
        hide_index=True,
        height=min(400, (len(resumen_area) + 1) * 38),
    )
else:
    st.info("No hay datos de área disponibles.")
