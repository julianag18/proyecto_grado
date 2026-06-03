"""
dashboard/pages/04_migracion.py
──────────────────────────────────────────────────────────────────────────────
Página de Migración ETL: muestra el historial de cargas, métricas de calidad
de datos y permite lanzar un nuevo proceso ETL mediante drag & drop de archivo.
──────────────────────────────────────────────────────────────────────────────
"""

import sys
import io
import traceback
from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboard.components.data_loader import cargar_migraciones, es_modo_demo
from dashboard.components.kpi_cards import (
    render_section_header, render_banner_demo, render_sidebar_logo,
)
from dashboard.components.charts import barras_calidad_datos

# ── Configuración ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Migración ETL — PAME Laproff",
    page_icon="📤",
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
with st.spinner("Cargando historial de migraciones..."):
    df_mig = cargar_migraciones()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <h1 style="font-size:1.7rem; font-weight:800; color:#e6edf3; margin:0;">
      📤 Migración y Calidad de Datos — ETL
    </h1>
    <p style="color:#8b949e; font-size:0.85rem; margin:0.3rem 0 0.8rem 0;">
      Historial de cargas · Métricas de calidad · Nuevo proceso de migración
    </p>
    """,
    unsafe_allow_html=True,
)

if es_modo_demo():
    render_banner_demo()

st.markdown("<hr>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — KPIs de migración
# ═════════════════════════════════════════════════════════════════════════════
render_section_header("Métricas acumuladas de migración", "Calidad total de los datos integrados al PAME")

if not df_mig.empty:
    total_leidos   = int(df_mig["registros_leidos"].sum())
    total_cargados = int(df_mig["registros_cargados"].sum())
    total_dups     = int(df_mig["duplicados_omitidos"].sum())
    total_errores  = int(df_mig["errores"].sum())
    pct_exito      = round(100 * total_cargados / total_leidos, 1) if total_leidos > 0 else 0.0
    pct_dups       = round(100 * total_dups / total_leidos, 1) if total_leidos > 0 else 0.0
    n_cargas       = len(df_mig)

    col1, col2, col3, col4, col5 = st.columns(5, gap="small")
    col1.metric("📂 Cargas realizadas",    n_cargas)
    col2.metric("📋 Registros leídos",     total_leidos)
    col3.metric("✅ Cargados exitosamente", total_cargados, delta=f"{pct_exito}%", delta_color="normal")
    col4.metric("⚠️ Duplicados omitidos",  total_dups,     delta=f"{pct_dups}% del total", delta_color="off")
    col5.metric("❌ Errores",              total_errores,  delta_color="inverse")

    # Barra de progreso de calidad
    st.markdown("<br>", unsafe_allow_html=True)
    col_prog, col_prog_label = st.columns([4, 1])
    with col_prog:
        st.markdown(
            f"<div style='font-size:0.78rem; color:#8b949e; margin-bottom:0.3rem;'>"
            f"Tasa de éxito de migración: <b style='color:#22c55e'>{pct_exito}%</b>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.progress(min(pct_exito / 100, 1.0))

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráfico de calidad
    st.plotly_chart(
        barras_calidad_datos(df_mig),
        use_container_width=True,
        config={"displayModeBar": False},
    )
else:
    st.info("No hay registros de migración en la base de datos.")

st.markdown("<hr>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — HISTORIAL DE MIGRACIONES
# ═════════════════════════════════════════════════════════════════════════════
render_section_header("Historial de cargas ETL", f"{len(df_mig)} ejecución(es) registrada(s)")

if not df_mig.empty:
    # Formatear columnas para visualización
    df_hist = df_mig.copy()

    # Estado con emoji
    estado_emoji = {"completado": "✅ Completado", "parcial": "⚠️ Parcial", "fallido": "❌ Fallido"}
    if "estado" in df_hist.columns:
        df_hist["estado"] = df_hist["estado"].map(estado_emoji).fillna(df_hist["estado"])

    # Tipo con emoji
    tipo_emoji = {"inventario": "🔧 Inventario", "servicios": "📅 Servicios"}
    if "tipo" in df_hist.columns:
        df_hist["tipo"] = df_hist["tipo"].map(tipo_emoji).fillna(df_hist["tipo"])

    col_rename = {
        "nombre_archivo":      "Archivo",
        "tipo":                "Tipo",
        "registros_leidos":    "Leídos",
        "registros_cargados":  "Cargados",
        "duplicados_omitidos": "Duplicados",
        "errores":             "Errores",
        "estado":              "Estado",
        "usuario":             "Usuario",
        "ejecutado_en":        "Fecha",
    }
    columnas_presentes = [c for c in col_rename if c in df_hist.columns]
    df_hist = df_hist[columnas_presentes].rename(columns=col_rename)

    def _estilo_estado(row):
        estado = str(row.get("Estado", ""))
        if "Fallido" in estado:
            return ["background-color: rgba(239,68,68,0.08);"] * len(row)
        elif "Parcial" in estado:
            return ["background-color: rgba(234,179,8,0.06);"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df_hist.style.apply(_estilo_estado, axis=1),
        use_container_width=True,
        hide_index=True,
        height=min(400, (len(df_hist) + 1) * 40),
    )
else:
    st.info("El historial de migraciones está vacío.")

st.markdown("<hr>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — NUEVO PROCESO ETL (UPLOADER)
# ═════════════════════════════════════════════════════════════════════════════
render_section_header(
    "Ejecutar nueva migración",
    "Carga un archivo Excel o CSV para iniciar el proceso ETL de migración al PAME"
)

col_cfg1, col_cfg2 = st.columns(2, gap="medium")

with col_cfg1:
    tipo_migracion = st.radio(
        "Tipo de datos a migrar",
        options=["inventario", "servicios"],
        format_func=lambda x: "🔧 Inventario de equipos" if x == "inventario" else "📅 Cronograma de servicios",
        horizontal=True,
        key="tipo_migracion",
    )

with col_cfg2:
    hoja_excel = st.text_input(
        "Hoja de Excel (opcional)",
        value="0",
        help="Número (0 = primera hoja) o nombre de la hoja. Ignorado para CSV.",
        key="hoja_excel",
    )

archivo = st.file_uploader(
    "Arrastra el archivo aquí o haz clic para seleccionarlo",
    type=["xlsx", "xls", "csv"],
    key="archivo_etl",
    label_visibility="visible",
)

if archivo is not None:
    st.markdown(
        f"""
        <div style="background:rgba(37,99,235,0.1); border:1px solid rgba(37,99,235,0.3);
                    border-radius:10px; padding:1rem; margin:0.5rem 0;">
          <b>📄 {archivo.name}</b>
          <span style="color:#8b949e; font-size:0.8rem; margin-left:0.5rem;">
            ({archivo.size:,} bytes)
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Vista previa
    with st.expander("👁️ Vista previa del archivo (primeras 5 filas)", expanded=False):
        try:
            if archivo.name.endswith(".csv"):
                df_preview = pd.read_csv(io.BytesIO(archivo.read()), nrows=5, dtype=str)
                archivo.seek(0)
            else:
                hoja_val = int(hoja_excel) if hoja_excel.isdigit() else hoja_excel
                df_preview = pd.read_excel(io.BytesIO(archivo.read()), sheet_name=hoja_val, nrows=5, dtype=str)
                archivo.seek(0)
            st.dataframe(df_preview, use_container_width=True, hide_index=True)
            st.caption(f"Columnas detectadas: {list(df_preview.columns)}")
        except Exception as e:
            st.error(f"Error al previsualizar: {e}")

    # Mapeo de columnas
    st.markdown("### ⚙️ Mapeo de Columnas")
    
    # Pre-leer columnas del archivo para el mapeador
    columnas_detectadas = []
    try:
        if archivo.name.endswith(".csv"):
            df_cols = pd.read_csv(io.BytesIO(archivo.read()), nrows=1)
            archivo.seek(0)
        else:
            hoja_val = int(hoja_excel) if hoja_excel.isdigit() else hoja_excel
            df_cols = pd.read_excel(io.BytesIO(archivo.read()), sheet_name=hoja_val, nrows=1)
            archivo.seek(0)
        columnas_detectadas = list(df_cols.columns)
    except Exception as e:
        st.error(f"Error al leer columnas del archivo para mapear: {e}")
        
    mapeo_manual = {}
    if columnas_detectadas:
        st.markdown(
            "<div style='font-size:0.82rem; color:#8b949e; margin-bottom:0.5rem;'>"
            "Si las columnas de tu archivo no coinciden con las del sistema, puedes relacionarlas manualmente a continuación."
            "</div>",
            unsafe_allow_html=True,
        )
        
        if tipo_migracion == "inventario":
            campos_config = {
                "codigo_equipo": ("Código del Equipo *", True),
                "nombre": ("Nombre del Equipo *", True),
                "area": ("Área *", True),
                "serie": ("Número de Serie", False),
                "modelo": ("Modelo", False),
                "fabricante": ("Fabricante", False),
                "ubicacion": ("Ubicación", False),
                "estado_equipo": ("Estado del Equipo", False),
                "criticidad": ("Criticidad", False),
            }
        else:
            campos_config = {
                "codigo_equipo": ("Código del Equipo *", True),
                "nombre_equipo": ("Nombre del Equipo", False),
                "fecha_servicio_vigente": ("Fecha Último Servicio *", True),
                "tipo_servicio": ("Tipo de Servicio *", True),
                "frecuencia": ("Frecuencia *", True),
                "numero_informe": ("Número de Informe", False),
                "estado_conformidad": ("Estado Conformidad", False),
                "proveedor": ("Proveedor", False),
                "periodo_proximo_servicio": ("Período Vencimiento", False),
            }
            
        # Mostrar mapeadores en columnas
        st.info("💡 Mapeo automático de columnas sugerido. Revisa las asignaciones antes de ejecutar.")
        cols_mapper = st.columns(3, gap="small")
        
        for idx, (campo_canon, (label, requerido)) in enumerate(campos_config.items()):
            col_ui = cols_mapper[idx % 3]
            with col_ui:
                # Intentar adivinar la columna por defecto
                col_sugerida = None
                from etl.extractor import _cargar_mappings
                try:
                    mappings_ref = _cargar_mappings(tipo_migracion).get(campo_canon, [])
                    for s in mappings_ref:
                        if s in columnas_detectadas:
                            col_sugerida = s
                            break
                except Exception:
                    pass
                
                if not col_sugerida:
                    # Usar lógica de aproximación de texto
                    for c_det in columnas_detectadas:
                        if c_det.lower().strip() == campo_canon.lower().strip():
                            col_sugerida = c_det
                            break
                        palabras_clave = {
                            "codigo_equipo": ["codigo", "código", "cod", "id"],
                            "nombre": ["nombre", "equipo", "desc", "name"],
                            "area": ["area", "área"],
                            "serie": ["serie", "serial", "sn"],
                            "fecha_servicio_vigente": ["vigente", "fecha", "ultimo", "último", "servicio"],
                            "tipo_servicio": ["tipo", "servicio"],
                            "frecuencia": ["frecuencia", "frec"],
                        }.get(campo_canon, [])
                        for pk in palabras_clave:
                            if pk in c_det.lower():
                                col_sugerida = c_det
                                break
                                
                options = ["-- No Mapear --"] + columnas_detectadas
                default_idx = options.index(col_sugerida) if col_sugerida in options else 0
                
                col_seleccionada = st.selectbox(
                    f"{label}",
                    options=options,
                    index=default_idx,
                    key=f"map_{tipo_migracion}_{campo_canon}",
                )
                
                if col_seleccionada != "-- No Mapear --":
                    mapeo_manual[col_seleccionada] = campo_canon

    # Botón de ejecución
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        ejecutar = st.button("🚀 Ejecutar ETL", type="primary", use_container_width=True, key="btn_etl")

    with col_info:
        st.markdown(
            f"<div style='font-size:0.8rem; color:#8b949e; padding-top:0.6rem;'>"
            f"Se ejecutará el pipeline: <b>Extracción → Transformación → Validación → Carga</b><br>"
            f"Tipo: <b>{tipo_migracion}</b> · Archivo: <b>{archivo.name}</b>"
            f"</div>",
            unsafe_allow_html=True,
        )

    if ejecutar:
        # Guardar archivo temporalmente
        tmp_dir = ROOT_DIR / "data" / "uploads"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / archivo.name
        tmp_path.write_bytes(archivo.read())
        archivo.seek(0)

        progress_bar = st.progress(0, text="Iniciando pipeline ETL...")
        log_container = st.empty()
        log_lines = []

        def log(msg: str):
            log_lines.append(msg)
            log_container.code("\n".join(log_lines[-20:]), language="text")

        try:
            # ── EXTRACCIÓN ────────────────────────────────────────────────
            progress_bar.progress(10, text="🔍 Extrayendo datos del archivo...")
            log(f"[E] Leyendo: {archivo.name} (tipo={tipo_migracion})")

            from etl.extractor import leer_archivo
            hoja_val = int(hoja_excel) if hoja_excel.isdigit() else hoja_excel
            df_extraido = leer_archivo(tmp_path, tipo=tipo_migracion, hoja=hoja_val, mapeo_manual=mapeo_manual)
            log(f"[E] ✓ {len(df_extraido)} filas extraídas, {len(df_extraido.columns)} columnas")
            progress_bar.progress(30, text="✅ Extracción completada")

            # ── TRANSFORMACIÓN ────────────────────────────────────────────
            progress_bar.progress(40, text="🔄 Transformando datos...")
            from etl.transformer import transformar_inventario, transformar_servicios
            if tipo_migracion == "inventario":
                resultado = transformar_inventario(df_extraido)
            else:
                resultado = transformar_servicios(df_extraido)

            log(f"[T] ✓ Válidos: {resultado.total_validos} | "
                f"Rechazados: {resultado.total_rechazados} | "
                f"Duplicados: {resultado.total_duplicados}")
            progress_bar.progress(60, text="✅ Transformación completada")

            # ── MODO DEMO: no cargar a Firestore ───────────────────────────
            if es_modo_demo():
                progress_bar.progress(90, text="🧪 Modo demo: omitiendo carga a BD...")
                log("[L] ⚠ Modo demo activo — datos no cargados a Firestore")
                log("[L] Configure FIREBASE_CREDENTIALS_PATH en .env para carga real")
            else:
                # ── CARGA ─────────────────────────────────────────────────
                progress_bar.progress(70, text="📤 Cargando datos en Firestore...")
                from etl.loader import cargar_equipos, cargar_servicios, cargar_proveedores
                from etl.migration_log import registrar_migracion

                if tipo_migracion == "inventario":
                    cargar_proveedores(resultado.df_limpio)
                    res_carga = cargar_equipos(resultado.df_limpio)
                else:
                    res_carga = cargar_servicios(resultado.df_limpio)

                log(f"[L] ✓ Cargados: {res_carga.registros_exitosos} | "
                    f"Fallidos: {res_carga.registros_fallidos}")

                # Registrar en log de migraciones
                registrar_migracion(
                    nombre_archivo=archivo.name,
                    tipo=tipo_migracion,
                    registros_leidos=resultado.total_leidos,
                    registros_cargados=res_carga.registros_exitosos,
                    duplicados_omitidos=resultado.total_duplicados,
                    errores=resultado.total_rechazados + res_carga.registros_fallidos,
                    estado="completado" if res_carga.registros_fallidos == 0 else "parcial",
                )
                st.cache_data.clear()

            progress_bar.progress(100, text="✅ Pipeline ETL completado")

            # ── RESUMEN FINAL ─────────────────────────────────────────────
            st.success("🎉 **Pipeline ETL ejecutado exitosamente**")
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            col_r1.metric("📋 Leídos",     resultado.total_leidos)
            col_r2.metric("✅ Válidos",    resultado.total_validos)
            col_r3.metric("⚠️ Duplicados", resultado.total_duplicados)
            col_r4.metric("❌ Rechazados", resultado.total_rechazados)

            if resultado.total_rechazados > 0:
                with st.expander(f"⚠️ Ver {resultado.total_rechazados} registros rechazados"):
                    st.dataframe(resultado.df_rechazos, use_container_width=True, hide_index=True)

            if resultado.total_duplicados > 0:
                with st.expander(f"🔁 Ver {resultado.total_duplicados} duplicados omitidos"):
                    st.dataframe(resultado.df_duplicados, use_container_width=True, hide_index=True)

        except Exception as exc:
            progress_bar.progress(100, text="❌ Error en el pipeline")
            st.error(f"**Error durante el ETL:** {exc}")
            with st.expander("🔍 Ver detalle del error"):
                st.code(traceback.format_exc())
            log(f"[!] ERROR: {exc}")

        # Limpiar archivo temporal
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

else:
    st.markdown(
        """
        <div style="text-align:center; padding:2rem; color:#484f58; font-size:0.9rem;">
          ⬆️ Sube un archivo Excel (.xlsx, .xls) o CSV (.csv) para iniciar la migración
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<hr>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — INFO TÉCNICA
# ═════════════════════════════════════════════════════════════════════════════
with st.expander("ℹ️ Información técnica del pipeline ETL"):
    st.markdown("""
    ### Proceso de Extracción, Transformación y Carga (ETL)

    El pipeline ETL del módulo PAME sigue estas etapas:

    | Etapa | Módulo | Descripción |
    |---|---|---|
    | **Extracción** | `etl/extractor.py` | Lee el archivo Excel o CSV y aplica el mapeo de columnas definido en `column_mappings.yaml` |
    | **Transformación** | `etl/transformer.py` | Normaliza texto, fechas y enums; detecta y separa duplicados; valida campos obligatorios |
    | **Validación** | `etl/validator.py` | Valida el esquema completo con Pydantic antes de la carga |
    | **Carga** | `etl/loader.py` | Realiza UPSERT en lotes de 50 registros a Supabase; registra el log de migración |

    **Estrategia UPSERT:**
    - **Equipos**: clave única = `codigo_equipo`
    - **Proveedores**: clave única = `nombre`
    - **Servicios**: clave única = `(codigo_equipo, tipo_servicio, fecha_servicio_vigente)`

    **Métricas de evaluación de calidad:**
    - Completitud de campos obligatorios
    - Tasa de duplicados detectados
    - Tasa de registros rechazados por error crítico
    - Tasa de éxito de la carga
    """)
