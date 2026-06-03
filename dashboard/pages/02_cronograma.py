"""
dashboard/pages/02_cronograma.py
──────────────────────────────────────────────────────────────────────────────
Página de Cronograma: tabla filtrable de todos los equipos con su estado de
alerta, fechas de calibración y días restantes. Incluye exportación a CSV.
──────────────────────────────────────────────────────────────────────────────
"""

import sys
from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboard.components.data_loader import cargar_estado_pame, es_modo_demo
from dashboard.components.kpi_cards import (
    render_section_header, render_banner_demo, render_badge_alerta, render_sidebar_logo,
)

# ── Configuración ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cronograma PAME — Laproff",
    page_icon="📅",
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
with st.spinner("Cargando cronograma..."):
    df, is_live = cargar_estado_pame()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <h1 style="font-size:1.7rem; font-weight:800; color:#e6edf3; margin:0;">
      📅 Cronograma de Calibraciones
    </h1>
    <p style="color:#8b949e; font-size:0.85rem; margin:0.3rem 0 0.8rem 0;">
      Estado de calibración de cada equipo · {'🟢 Live' if is_live else '🧪 Demo'} · {date.today().strftime('%d/%m/%Y')}
    </p>
    """,
    unsafe_allow_html=True,
)

if es_modo_demo():
    render_banner_demo()

st.markdown("<hr>", unsafe_allow_html=True)

if df.empty:
    st.warning("No hay equipos registrados en la base de datos.")
    st.stop()

# ═════════════════════════════════════════════════════════════════════════════
# FILTROS
# ═════════════════════════════════════════════════════════════════════════════
render_section_header("Filtros", "Afina la búsqueda por área, estado de alerta y tipo de servicio")

col_f1, col_f2, col_f3, col_f4 = st.columns(4, gap="small")

with col_f1:
    areas_disponibles = sorted(df["area"].dropna().unique().tolist())
    areas_sel = st.multiselect(
        "Área",
        options=areas_disponibles,
        default=[],
        placeholder="Todas las áreas",
        key="filtro_area",
    )

with col_f2:
    estados_disp = ["AL_DIA", "PROXIMO", "CRITICO", "VENCIDO", "SIN_DATOS"]
    etiquetas_estados = {
        "AL_DIA": "✅ Al día", "PROXIMO": "🟡 Próximos",
        "CRITICO": "🟠 Críticos", "VENCIDO": "🔴 Vencidos", "SIN_DATOS": "⚪ Sin datos",
    }
    estados_sel = st.multiselect(
        "Estado de alerta",
        options=estados_disp,
        format_func=lambda x: etiquetas_estados.get(x, x),
        default=[],
        placeholder="Todos los estados",
        key="filtro_estado",
    )

with col_f3:
    tipos_disp = sorted(df["tipo_servicio"].dropna().unique().tolist())
    tipos_sel = st.multiselect(
        "Tipo de servicio",
        options=tipos_disp,
        default=[],
        placeholder="Todos los tipos",
        key="filtro_tipo",
    )

with col_f4:
    proveedores_disp = sorted(df["proveedor"].dropna().unique().tolist()) if "proveedor" in df.columns else []
    prov_sel = st.multiselect(
        "Proveedor",
        options=proveedores_disp,
        default=[],
        placeholder="Todos",
        key="filtro_proveedor",
    )

# ── Búsqueda por texto ─────────────────────────────────────────────────────────
texto_busq = st.text_input(
    "🔍 Buscar equipo",
    placeholder="Código, nombre o número de informe...",
    key="busqueda_texto",
)

# ═════════════════════════════════════════════════════════════════════════════
# APLICAR FILTROS
# ═════════════════════════════════════════════════════════════════════════════
df_filtrado = df.copy()

if areas_sel:
    df_filtrado = df_filtrado[df_filtrado["area"].isin(areas_sel)]
if estados_sel:
    df_filtrado = df_filtrado[df_filtrado["estado_alerta"].isin(estados_sel)]
if tipos_sel:
    df_filtrado = df_filtrado[df_filtrado["tipo_servicio"].isin(tipos_sel)]
if prov_sel and "proveedor" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["proveedor"].isin(prov_sel)]
if texto_busq.strip():
    mask = (
        df_filtrado["codigo_equipo"].fillna("").str.contains(texto_busq, case=False, na=False)
        | df_filtrado["nombre"].fillna("").str.contains(texto_busq, case=False, na=False)
        | df_filtrado.get("numero_informe", pd.Series(dtype=str)).fillna("").str.contains(texto_busq, case=False, na=False)
    )
    df_filtrado = df_filtrado[mask]

st.markdown("<br>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# MÉTRICAS DE FILTRADO
# ═════════════════════════════════════════════════════════════════════════════
col_m1, col_m2, col_m3, col_m4 = st.columns(4, gap="small")
col_m1.metric("Equipos mostrados",  len(df_filtrado),  delta=f"de {len(df)} totales")
col_m2.metric("🔴 Vencidos",  (df_filtrado["estado_alerta"] == "VENCIDO").sum())
col_m3.metric("🟠 Críticos",  (df_filtrado["estado_alerta"] == "CRITICO").sum())
col_m4.metric("🟡 Próximos",  (df_filtrado["estado_alerta"] == "PROXIMO").sum())

st.markdown("<hr>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# TABLA PRINCIPAL
# ═════════════════════════════════════════════════════════════════════════════
render_section_header("Detalle de equipos", f"{len(df_filtrado)} registros")

# Seleccionar y renombrar columnas para mostrar
COLUMNAS_MOSTRAR = {
    "codigo_equipo":          "Código",
    "nombre":                 "Equipo",
    "area":                   "Área",
    "criticidad":             "Criticidad",
    "tipo_servicio":          "Tipo servicio",
    "frecuencia":             "Frecuencia",
    "fecha_servicio_vigente": "Último servicio",
    "fecha_proximo_servicio": "Próximo vencimiento",
    "dias_restantes":         "Días restantes",
    "estado_alerta":          "Estado alerta",
    "estado_conformidad":     "Conformidad",
    "proveedor":              "Proveedor",
    "numero_informe":         "N° Informe",
}

columnas_presentes = [c for c in COLUMNAS_MOSTRAR.keys() if c in df_filtrado.columns]
df_tabla = df_filtrado[columnas_presentes].rename(columns=COLUMNAS_MOSTRAR)

# Ordenar: primero vencidos, luego críticos, próximos, sin datos, al día
orden_alerta = {"VENCIDO": 0, "CRITICO": 1, "PROXIMO": 2, "SIN_DATOS": 3, "AL_DIA": 4}
if "Estado alerta" in df_tabla.columns:
    df_tabla = df_tabla.assign(
        _orden=df_tabla["Estado alerta"].map(orden_alerta).fillna(5)
    ).sort_values("_orden").drop(columns=["_orden"])

# Colorear columna de estado con emojis
if "Estado alerta" in df_tabla.columns:
    emoji_mapa = {
        "AL_DIA": "✅ AL DÍA",
        "PROXIMO": "🟡 PRÓXIMO",
        "CRITICO": "🟠 CRÍTICO",
        "VENCIDO": "🔴 VENCIDO",
        "SIN_DATOS": "⚪ SIN DATOS",
    }
    df_tabla["Estado alerta"] = df_tabla["Estado alerta"].map(emoji_mapa).fillna(df_tabla["Estado alerta"])

# Criticidad con emojis
if "Criticidad" in df_tabla.columns:
    crit_mapa = {"Alta": "🔺 Alta", "Media": "🔸 Media", "Baja": "🔹 Baja"}
    df_tabla["Criticidad"] = df_tabla["Criticidad"].map(crit_mapa).fillna(df_tabla["Criticidad"])

# Función de estilo de filas
def _estilo_fila(row):
    estado = str(row.get("Estado alerta", ""))
    if "VENCIDO" in estado:
        return ["background-color: rgba(239,68,68,0.08);"] * len(row)
    elif "CRÍTICO" in estado:
        return ["background-color: rgba(249,115,22,0.08);"] * len(row)
    elif "PRÓXIMO" in estado:
        return ["background-color: rgba(234,179,8,0.06);"] * len(row)
    return [""] * len(row)

st.dataframe(
    df_tabla.style.apply(_estilo_fila, axis=1),
    use_container_width=True,
    hide_index=True,
    height=min(600, max(300, (len(df_tabla) + 1) * 38)),
    column_config={
        "Días restantes": st.column_config.NumberColumn(
            "Días restantes",
            format="%d días",
        ),
        "Último servicio": st.column_config.DateColumn("Último servicio", format="DD/MM/YYYY"),
        "Próximo vencimiento": st.column_config.DateColumn("Próximo vencimiento", format="DD/MM/YYYY"),
    },
)

st.markdown("<br>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# EXPORTACIÓN
# ═════════════════════════════════════════════════════════════════════════════
col_exp1, col_exp2, _ = st.columns([1, 1, 4])

with col_exp1:
    csv_data = df_tabla.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label="⬇️ Exportar CSV",
        data=csv_data,
        file_name=f"cronograma_pame_{date.today().isoformat()}.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col_exp2:
    try:
        import io
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_tabla.to_excel(writer, index=False, sheet_name="Cronograma PAME")
        buffer.seek(0)
        st.download_button(
            label="⬇️ Exportar Excel",
            data=buffer,
            file_name=f"cronograma_pame_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    except Exception:
        pass
