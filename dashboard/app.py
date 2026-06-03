"""
dashboard/app.py
──────────────────────────────────────────────────────────────────────────────
Punto de entrada principal del Dashboard PAME — Laboratorios Laproff S.A.S.

Ejecución:
    streamlit run dashboard/app.py

Desde la raíz del proyecto también funciona:
    streamlit run dashboard/app.py --server.port 8501
──────────────────────────────────────────────────────────────────────────────
"""

import sys
from pathlib import Path
from datetime import date

import streamlit as st

# ── Garantizar que el root del proyecto esté en sys.path ──────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ── Configuración global de página ────────────────────────────────────────────
st.set_page_config(
    page_title="PAME Dashboard — Laboratorios Laproff",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": (
            "**PAME — Módulo Complementario**\n\n"
            "Programa de Aseguramiento Metrológico · Laboratorios Laproff S.A.S.\n\n"
            "Proyecto de Práctica Académica · Bioingeniería · 2026"
        ),
    },
)

# ── Inyectar CSS global ───────────────────────────────────────────────────────
css_path = Path(__file__).resolve().parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )

# ── Importar data_loader para verificar conexión ──────────────────────────────
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

# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Navegación principal
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo / Branding
    render_sidebar_logo()

    # Navegación de páginas
    st.markdown(
        "<div style='font-size:0.7rem; color:#484f58; letter-spacing:0.08em; "
        "text-transform:uppercase; margin-bottom:0.4rem; padding-left:0.2rem;'>Navegación</div>",
        unsafe_allow_html=True,
    )

    st.page_link("app.py",                    label="🏠 Inicio",         icon=None)
    st.page_link("pages/01_estado_pame.py",   label="📊 Estado General", icon=None)
    st.page_link("pages/02_cronograma.py",    label="📅 Cronograma",     icon=None)
    st.page_link("pages/03_alertas.py",       label="🔔 Alertas",        icon=None)
    st.page_link("pages/04_migracion.py",     label="📤 Migración ETL",  icon=None)

    st.markdown(
        "<hr style='border:none; border-top:1px solid rgba(255,255,255,0.07); margin:0.8rem 0;'>",
        unsafe_allow_html=True,
    )

    # Botón de actualización
    if st.button("🔄 Actualizar datos", use_container_width=True, type="primary", key="btn_refresh_home"):
        st.cache_data.clear()
        st.rerun()

    # Estado de conexión
    is_demo = es_modo_demo()
    st.markdown(
        f"""
        <div style="margin-top:1rem; padding:0.6rem 0.8rem;
                    background:rgba(255,255,255,0.04); border-radius:8px;
                    border:1px solid rgba(255,255,255,0.06);">
          <div style="font-size:0.68rem; color:#484f58; text-transform:uppercase; letter-spacing:0.05em;">
            Conexión
          </div>
          <div style="font-size:0.8rem; margin-top:0.2rem; font-weight:600;
                      color:{'#6b7280' if is_demo else '#22c55e'};">
            {'🧪 Modo demo' if is_demo else '🟢 Supabase'}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="font-size:0.68rem; color:#484f58; text-align:center; margin-top:1.5rem;">
          Práctica Académica · Bioingeniería<br>
          {date.today().strftime('%d/%m/%Y')}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ═════════════════════════════════════════════════════════════════════════════
# PÁGINA DE INICIO — Hero + KPIs resumidos
# ═════════════════════════════════════════════════════════════════════════════

# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="padding: 2rem 0 1rem 0;">
      <div style="font-size:0.75rem; color:#2563eb; font-weight:600;
                  letter-spacing:0.1em; text-transform:uppercase; margin-bottom:0.5rem;">
        Laboratorios Laproff S.A.S.
      </div>
      <h1 style="font-size:2.2rem; font-weight:800; color:#e6edf3; margin:0; line-height:1.2;">
        Programa de Aseguramiento<br>Metrológico
      </h1>
      <p style="color:#8b949e; font-size:0.95rem; margin: 0.8rem 0 0 0; max-width:600px;">
        Panel de indicadores clave, cronograma automatizado de calibraciones
        y gestión integral de la digitalización del PAME.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if is_demo:
    render_banner_demo()

st.markdown("<hr>", unsafe_allow_html=True)

# ── Carga de datos ─────────────────────────────────────────────────────────────
with st.spinner("Cargando datos del PAME..."):
    df_estado, is_live = cargar_estado_pame()
    kpis = calcular_kpis(df_estado)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
render_section_header("Indicadores clave — Estado actual del PAME")
render_fila_kpis(kpis)

st.markdown("<br>", unsafe_allow_html=True)

# ── Gauge + Donut ──────────────────────────────────────────────────────────────
render_section_header("Cumplimiento y distribución")

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

# ── Barras por área + Timeline ─────────────────────────────────────────────────
render_section_header("Análisis por área y próximos vencimientos")

col_area, col_time = st.columns([1.5, 1], gap="medium")
with col_area:
    st.plotly_chart(
        barras_por_area(df_estado),
        use_container_width=True,
        config={"displayModeBar": False},
    )
with col_time:
    st.plotly_chart(
        timeline_vencimientos(df_estado, top_n=8),
        use_container_width=True,
        config={"displayModeBar": False},
    )

st.markdown("<hr>", unsafe_allow_html=True)

# ── Accesos rápidos ─────────────────────────────────────────────────────────────
render_section_header("Accesos rápidos")

col_a, col_b, col_c, col_d = st.columns(4, gap="medium")

with col_a:
    vencidos = kpis.get("vencidos", 0)
    criticos = kpis.get("criticos", 0)
    urgentes = vencidos + criticos
    clase_card = "vencido" if urgentes > 0 else "al-dia"
    icono_card = "🔴" if urgentes > 0 else "✅"
    st.markdown(
        f"""
        <div class="kpi-card {clase_card}" style="cursor:pointer;">
          <span class="kpi-icon">{icono_card}</span>
          <div class="kpi-label">Alertas urgentes</div>
          <div class="kpi-number">{urgentes}</div>
          <div class="kpi-sub">Vencidos + Críticos</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/03_alertas.py", label="→ Ver alertas", icon="🔔")

with col_b:
    st.markdown(
        """
        <div class="kpi-card total">
          <span class="kpi-icon">📅</span>
          <div class="kpi-label">Cronograma</div>
          <div class="kpi-sub">Tabla completa de equipos con filtros por área y estado</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/02_cronograma.py", label="→ Ver cronograma", icon="📅")

with col_c:
    st.markdown(
        """
        <div class="kpi-card proximo">
          <span class="kpi-icon">📤</span>
          <div class="kpi-label">Migración ETL</div>
          <div class="kpi-sub">Cargar nuevos archivos Excel o CSV al sistema</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/04_migracion.py", label="→ Migrar datos", icon="📤")

with col_d:
    st.markdown(
        """
        <div class="kpi-card al-dia">
          <span class="kpi-icon">📊</span>
          <div class="kpi-label">Estado detallado</div>
          <div class="kpi-sub">Vista completa de KPIs, áreas y gráficos del PAME</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/01_estado_pame.py", label="→ Ver estado PAME", icon="📊")

st.markdown("<br><br>", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center; padding:1rem 0; border-top:1px solid rgba(255,255,255,0.06);">
      <span style="font-size:0.72rem; color:#484f58;">
        PAME Módulo Complementario · Laboratorios Laproff S.A.S. ·
        Proyecto de Práctica Académica · Bioingeniería · 2026
      </span>
    </div>
    """,
    unsafe_allow_html=True,
)
