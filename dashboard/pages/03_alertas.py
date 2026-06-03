"""
dashboard/pages/03_alertas.py
──────────────────────────────────────────────────────────────────────────────
Página de Alertas: bandeja priorizada de alertas activas con contadores por
nivel y posibilidad de marcar como leída.
──────────────────────────────────────────────────────────────────────────────
"""

import sys
from pathlib import Path
from datetime import date

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboard.components.data_loader import (
    cargar_alertas, cargar_estado_pame, calcular_kpis,
    marcar_alerta_leida, es_modo_demo, cargar_metricas_alertas,
)
from dashboard.components.kpi_cards import (
    render_section_header, render_banner_demo, render_sidebar_logo,
)

# ── Configuración ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Alertas PAME — Laproff",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_path = Path(__file__).resolve().parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    render_sidebar_logo()
    st.page_link("app.py",                  label="🏠 Inicio")
    st.page_link("pages/01_estado_pame.py", label="📊 Estado General")
    st.page_link("pages/02_cronograma.py",  label="📅 Cronograma")
    st.page_link("pages/03_alertas.py",     label="🔔 Alertas")
    st.page_link("pages/04_migracion.py",   label="📤 Migración ETL")
    st.markdown("<hr style='border-color:rgba(255,255,255,0.07);'>", unsafe_allow_html=True)
    if st.button("🔄 Actualizar", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# CARGA DE DATOS
# ═════════════════════════════════════════════════════════════════════════════
with st.spinner("Cargando alertas..."):
    df_alertas = cargar_alertas(solo_no_leidas=True)
    df_estado, is_live = cargar_estado_pame()
    kpis = calcular_kpis(df_estado)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <h1 style="font-size:1.7rem; font-weight:800; color:#e6edf3; margin:0;">
      🔔 Bandeja de Alertas
    </h1>
    <p style="color:#8b949e; font-size:0.85rem; margin:0.3rem 0 0.8rem 0;">
      Alertas activas ordenadas por prioridad · {'🟢 Live' if is_live else '🧪 Demo'} · {date.today().strftime('%d/%m/%Y')}
    </p>
    """,
    unsafe_allow_html=True,
)

if es_modo_demo():
    render_banner_demo()

st.markdown("<hr>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# CONTADORES DE ALERTAS
# ═════════════════════════════════════════════════════════════════════════════
render_section_header("Resumen de alertas activas")

col_v, col_c, col_p, col_total = st.columns(4, gap="small")

if df_alertas.empty:
    n_vencidos = kpis["vencidos"]
    n_criticos = kpis["criticos"]
    n_proximos = kpis["proximos"]
else:
    estado_col = "estado_alerta" if "estado_alerta" in df_alertas.columns else "tipo_alerta"
    if "estado_alerta" in df_alertas.columns:
        n_vencidos = (df_alertas["estado_alerta"] == "VENCIDO").sum()
        n_criticos = (df_alertas["estado_alerta"] == "CRITICO").sum()
        n_proximos = (df_alertas["estado_alerta"] == "PROXIMO").sum()
    else:
        n_vencidos = df_alertas["tipo_alerta"].str.contains("VENCIDO", na=False).sum()
        n_criticos = df_alertas["tipo_alerta"].str.contains("CRITICO", na=False).sum()
        n_proximos = df_alertas["tipo_alerta"].str.contains("PROXIMO", na=False).sum()

col_v.metric("🔴 Vencidos",  n_vencidos, delta="Acción inmediata", delta_color="inverse")
col_c.metric("🟠 Críticos",  n_criticos, delta="≤ 15 días",         delta_color="inverse")
col_p.metric("🟡 Próximos",  n_proximos, delta="≤ 30 días",         delta_color="off")
col_total.metric("Total alertas", n_vencidos + n_criticos + n_proximos)

st.markdown("<br>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# MÉTRICAS DE RESPUESTA METROLÓGICA (Trazabilidad)
# ═════════════════════════════════════════════════════════════════════════════
render_section_header("Métricas de Respuesta e Historial de Calibración", "Trazabilidad del tiempo promedio de cierre metrológico")
metricas_al = cargar_metricas_alertas()

col_t1, col_t2, col_t3 = st.columns(3, gap="medium")
with col_t1:
    st.metric(
        label="⏱️ Tiempo Promedio de Cierre", 
        value=f"{metricas_al.get('tiempo_promedio_resolucion', 0.0)} días",
        help="Tiempo transcurrido desde que se genera la alerta hasta que se marca como calibrado/resuelto en Firestore."
    )
with col_t2:
    st.metric(
        label="✅ Total Alertas Gestionadas", 
        value=metricas_al.get("total_alertas_resueltas", 0)
    )
with col_t3:
    total_resueltas = metricas_al.get("total_alertas_resueltas", 0)
    tasa = "100%" if total_resueltas > 0 else "0%"
    st.metric(label="📈 Tasa de Cierre Metrológico", value=tasa)

st.markdown("<br>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# FILTRO DE PRIORIDAD
# ═════════════════════════════════════════════════════════════════════════════
col_filt1, col_filt2, _ = st.columns([1, 1, 3])
with col_filt1:
    filtro_nivel = st.selectbox(
        "Filtrar por nivel",
        options=["Todos", "🔴 Vencidos", "🟠 Críticos", "🟡 Próximos"],
        key="filtro_nivel_alerta",
    )
with col_filt2:
    area_col = "area" if "area" in df_alertas.columns else None
    if area_col:
        areas_alertas = ["Todas"] + sorted(df_alertas[area_col].dropna().unique().tolist())
        filtro_area = st.selectbox("Filtrar por área", options=areas_alertas, key="filtro_area_alerta")
    else:
        filtro_area = "Todas"

st.markdown("<hr>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# RENDERIZAR ALERTAS
# ═════════════════════════════════════════════════════════════════════════════
render_section_header("Alertas activas", "Ordenadas por criticidad: Vencido → Crítico → Próximo")

if df_alertas.empty:
    # Generar alertas desde el estado PAME si no hay tabla de alertas
    alertas_sinteticas = []
    for _, row in df_estado.iterrows():
        estado = row.get("estado_alerta", "")
        if estado not in ("VENCIDO", "CRITICO", "PROXIMO"):
            continue
        dias = row.get("dias_restantes", 0)
        if estado == "VENCIDO":
            msg = (f"Servicio de **{row.get('tipo_servicio','N/A')}** para "
                   f"**[{row['codigo_equipo']}] {row['nombre']}** — "
                   f"venció hace **{abs(dias)} día(s)**.")
            nivel = "vencido"
        elif estado == "CRITICO":
            msg = (f"Servicio de **{row.get('tipo_servicio','N/A')}** para "
                   f"**[{row['codigo_equipo']}] {row['nombre']}** — "
                   f"vence en **{dias} día(s)**.")
            nivel = "critico"
        else:
            msg = (f"Servicio de **{row.get('tipo_servicio','N/A')}** para "
                   f"**[{row['codigo_equipo']}] {row['nombre']}** — "
                   f"vence en **{dias} día(s)**.")
            nivel = "proximo"
        alertas_sinteticas.append({
            "nivel": nivel,
            "estado": estado,
            "area": row.get("area", "N/A"),
            "codigo": row["codigo_equipo"],
            "nombre": row["nombre"],
            "tipo": row.get("tipo_servicio", "N/A"),
            "dias": dias,
            "msg": msg,
            "id": None,
        })

    # Ordenar: vencido → critico → proximo
    orden_nivel = {"vencido": 0, "critico": 1, "proximo": 2}
    alertas_sinteticas.sort(key=lambda x: (orden_nivel.get(x["nivel"], 9), x["dias"]))

    # Aplicar filtros
    if filtro_nivel != "Todos":
        mapa_filtro = {"🔴 Vencidos": "VENCIDO", "🟠 Críticos": "CRITICO", "🟡 Próximos": "PROXIMO"}
        estado_filtro = mapa_filtro.get(filtro_nivel)
        alertas_sinteticas = [a for a in alertas_sinteticas if a["estado"] == estado_filtro]
    if filtro_area != "Todas":
        alertas_sinteticas = [a for a in alertas_sinteticas if a["area"] == filtro_area]

    if not alertas_sinteticas:
        st.success("✅ No hay alertas activas con los filtros seleccionados.")
    else:
        iconos = {"vencido": "🔴", "critico": "🟠", "proximo": "🟡"}
        for alerta in alertas_sinteticas:
            nivel = alerta["nivel"]
            icono = iconos.get(nivel, "⚪")
            area_badge = f'<span style="font-size:0.7rem; color:#8b949e;">📍 {alerta["area"]}</span>'
            dias_badge = (
                f'<span style="color:#ef4444; font-weight:600;">Vencido hace {abs(alerta["dias"])} día(s)</span>'
                if nivel == "vencido" else
                f'<span style="color:{("#f97316" if nivel=="critico" else "#eab308")}; font-weight:600;">'
                f'Vence en {alerta["dias"]} día(s)</span>'
            )
            st.markdown(
                f"""
                <div class="alert-banner {nivel}">
                  <div style="font-size:1.4rem; line-height:1;">{icono}</div>
                  <div style="flex:1;">
                    <div class="alert-title">[{alerta['codigo']}] {alerta['nombre']}</div>
                    <div class="alert-msg">
                      {area_badge} &nbsp;·&nbsp; {dias_badge} &nbsp;·&nbsp;
                      {alerta.get('tipo','N/A')}
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

else:
    # Usar tabla de alertas real de Supabase
    orden_prioridad = {"alta": 0, "media": 1, "baja": 2}

    if "nivel_prioridad" in df_alertas.columns:
        df_alertas = df_alertas.assign(
            _ord=df_alertas["nivel_prioridad"].map(orden_prioridad).fillna(9)
        ).sort_values("_ord").drop(columns=["_ord"])

    for _, alerta in df_alertas.iterrows():
        nivel_raw = alerta.get("nivel_prioridad", "baja")
        tipo_alerta = str(alerta.get("tipo_alerta", ""))
        nivel_css = "vencido" if "VENCIDO" in tipo_alerta else (
            "critico" if "CRITICO" in tipo_alerta else "proximo"
        )
        icono = "🔴" if "VENCIDO" in tipo_alerta else ("🟠" if "CRITICO" in tipo_alerta else "🟡")
        mensaje = alerta.get("mensaje", "Sin mensaje")

        col_msg, col_btn = st.columns([5, 1])
        with col_msg:
            st.markdown(
                f"""
                <div class="alert-banner {nivel_css}">
                  <div style="font-size:1.4rem; line-height:1;">{icono}</div>
                  <div><div class="alert-msg">{mensaje}</div></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_btn:
            alerta_id = alerta.get("id")
            if alerta_id and st.button("✓ Leída", key=f"leida_{alerta_id}", use_container_width=True):
                if marcar_alerta_leida(str(alerta_id)):
                    st.success("Marcada como leída")
                    st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# FOOTER: equipos sin historial
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("<hr>", unsafe_allow_html=True)
render_section_header("⚪ Equipos sin historial de calibración",
                       "Equipos registrados pero sin servicios asociados")

df_sin_datos = df_estado[df_estado["estado_alerta"] == "SIN_DATOS"] if not df_estado.empty else None
if df_sin_datos is not None and not df_sin_datos.empty:
    cols_mostrar = ["codigo_equipo", "nombre", "area", "estado_equipo"]
    cols_presentes = [c for c in cols_mostrar if c in df_sin_datos.columns]
    st.dataframe(
        df_sin_datos[cols_presentes].rename(columns={
            "codigo_equipo": "Código",
            "nombre": "Equipo",
            "area": "Área",
            "estado_equipo": "Estado",
        }),
        use_container_width=True,
        hide_index=True,
        height=min(300, (len(df_sin_datos) + 1) * 38),
    )
else:
    st.success("✅ Todos los equipos tienen al menos un servicio registrado.")
