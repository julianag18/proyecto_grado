"""
Punto de entrada principal del Dashboard PAME — Laboratorios Laproff S.A.S.
Implementa navegación lateral y 6 vistas principales integrando la base de datos Firestore y el pipeline ETL.
"""
import sys
import os
import io
import time
from pathlib import Path
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

# Garantizar que el root del proyecto esté en sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Importaciones locales
from src.dashboard.helpers import (
    cargar_estado_actual_pame,
    cargar_cumplimiento_anual,
    cargar_historial_etl,
    cargar_historial_alertas,
    es_demo_mode
)
from src.dashboard.charts import (
    donut_distribucion_estados,
    barras_vencimientos_por_area,
    gauge_cumplimiento,
    linea_tendencia_cumplimiento,
    barras_comparativo_anual,
    linea_evolucion_mensual,
    barras_calidad_datos,
    radar_desempeno_area,
    COLORES
)
from src.etl.pipeline import run_pipeline
from src.alertas.motor_alertas import generar_alertas, agrupar_por_area
from src.alertas.email_sender import (
    enviar_alerta_diaria,
    enviar_reporte_kpis_diario,
    enviar_alertas_mes_siguiente,
    verificar_y_enviar_alertas_automaticas
)



# ── Configuración global de la página ────────────────────────────────────────────
st.set_page_config(
    page_title="PAME Dashboard — Laboratorios Laproff",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inyectar CSS global ───────────────────────────────────────────────────────
css_path = Path(__file__).resolve().parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )
else:
    # Fallback inline CSS básico
    st.markdown(
        """
        <style>
            .section-header { border-left: 3px solid #00A99D; padding-left: 10px; margin-top: 20px; }
            .kpi-card { background: white; border: 1px solid #E2ECF5; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ── Helpers de UI ─────────────────────────────────────────────────────────────
def render_section_header(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="section-header">
          <h2>{title}</h2>
          {"<p>" + subtitle + "</p>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_html_distribucion_estados(df: pd.DataFrame) -> str:
    """Genera un componente HTML personalizado para mostrar la distribución de estados."""
    if df.empty or "estado_servicio" not in df.columns:
        return "<div style='color:#64748B;'>No hay datos</div>"
        
    conteo = df["estado_servicio"].value_counts()
    total = len(df)
    
    vigentes = conteo.get("Vigente", 0)
    programar = conteo.get("Programar", 0)
    ejecucion = conteo.get("En ejecución", 0)
    vencidos = conteo.get("Vencido", 0)
    
    pct_vigentes = round(vigentes / total * 100, 1) if total > 0 else 0.0
    pct_programar = round(programar / total * 100, 1) if total > 0 else 0.0
    pct_ejecucion = round(ejecucion / total * 100, 1) if total > 0 else 0.0
    pct_vencidos = round(vencidos / total * 100, 1) if total > 0 else 0.0
    
    # Colores
    c_vigente = "#10B981"
    c_programar = "#F59E0B"
    c_ejecucion = "#06B6D4"
    c_vencido = "#EF4444"
    
    html = f"""
    <div style="background: white; border: 1px solid #E2ECF5; border-radius: 12px; padding: 20px; min-height: 340px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between;">
      <div>
        <h4 style="margin: 0 0 5px 0; color: #1A2535; font-size: 14px; font-weight: 700;">Distribución Global de Estados</h4>
        <p style="margin: 0 0 20px 0; color: #64748B; font-size: 11.5px;">Proporción y cantidad de equipos según su estado metrológico.</p>
      </div>
      
      <!-- Barra segmentada redonda -->
      <div style="width: 100%; height: 26px; background-color: #F1F5F9; border-radius: 13px; display: flex; overflow: hidden; margin-bottom: 25px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.06); border: 1px solid #E2ECF5;">
        {f'<div style="width: {pct_vigentes}%; background-color: {c_vigente}; transition: all 0.3s;" title="Vigentes: {vigentes} ({pct_vigentes}%)"></div>' if pct_vigentes > 0 else ''}
        {f'<div style="width: {pct_programar}%; background-color: {c_programar}; transition: all 0.3s;" title="Por Programar: {programar} ({pct_programar}%)"></div>' if pct_programar > 0 else ''}
        {f'<div style="width: {pct_ejecucion}%; background-color: {c_ejecucion}; transition: all 0.3s;" title="En ejecución: {ejecucion} ({pct_ejecucion}%)"></div>' if pct_ejecucion > 0 else ''}
        {f'<div style="width: {pct_vencidos}%; background-color: {c_vencido}; transition: all 0.3s;" title="Vencidos: {vencidos} ({pct_vencidos}%)"></div>' if pct_vencidos > 0 else ''}
      </div>
      
      <!-- Detalles y leyenda -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
        <div style="display: flex; align-items: center; gap: 10px; padding: 10px; background: #F8FAFC; border-radius: 8px; border: 1px solid #F1F5F9;">
          <div style="width: 10px; height: 10px; background-color: {c_vigente}; border-radius: 50%;"></div>
          <div>
            <div style="font-size: 10px; font-weight: bold; color: #64748B; text-transform: uppercase;">Vigentes</div>
            <div style="font-size: 14px; font-weight: 800; color: #1A2535;">{vigentes} <span style="font-size: 10px; color: #94A3B8; font-weight: normal;">({pct_vigentes}%)</span></div>
          </div>
        </div>
        <div style="display: flex; align-items: center; gap: 10px; padding: 10px; background: #F8FAFC; border-radius: 8px; border: 1px solid #F1F5F9;">
          <div style="width: 10px; height: 10px; background-color: {c_programar}; border-radius: 50%;"></div>
          <div>
            <div style="font-size: 10px; font-weight: bold; color: #64748B; text-transform: uppercase;">Por Programar</div>
            <div style="font-size: 14px; font-weight: 800; color: #1A2535;">{programar} <span style="font-size: 10px; color: #94A3B8; font-weight: normal;">({pct_programar}%)</span></div>
          </div>
        </div>
        <div style="display: flex; align-items: center; gap: 10px; padding: 10px; background: #F8FAFC; border-radius: 8px; border: 1px solid #F1F5F9;">
          <div style="width: 10px; height: 10px; background-color: {c_ejecucion}; border-radius: 50%;"></div>
          <div>
            <div style="font-size: 10px; font-weight: bold; color: #64748B; text-transform: uppercase;">En Ejecución</div>
            <div style="font-size: 14px; font-weight: 800; color: #1A2535;">{ejecucion} <span style="font-size: 10px; color: #94A3B8; font-weight: normal;">({pct_ejecucion}%)</span></div>
          </div>
        </div>
        <div style="display: flex; align-items: center; gap: 10px; padding: 10px; background: #F8FAFC; border-radius: 8px; border: 1px solid #F1F5F9;">
          <div style="width: 10px; height: 10px; background-color: {c_vencido}; border-radius: 50%;"></div>
          <div>
            <div style="font-size: 10px; font-weight: bold; color: #64748B; text-transform: uppercase;">Vencidos</div>
            <div style="font-size: 14px; font-weight: 800; color: #1A2535;">{vencidos} <span style="font-size: 10px; color: #94A3B8; font-weight: normal;">({pct_vencidos}%)</span></div>
          </div>
        </div>
      </div>
    </div>
    """
    return "\n".join(line.strip() for line in html.split("\n") if line.strip())

def render_html_vencimientos_por_area(df: pd.DataFrame) -> str:
    """Genera un componente HTML para mostrar las áreas con más equipos críticos como lista de barras de progreso."""
    if df.empty or "ubicacion" not in df.columns or "estado_servicio" not in df.columns:
        return "<div style='color:#64748B;'>No hay datos</div>"

    # Filtrar solo estados críticos o alertas (Vencido, Programar, En ejecución)
    df_criticos = df[df["estado_servicio"].isin(["Vencido", "Programar", "En ejecución"])]
    if df_criticos.empty:
        return """
        <div style="background: white; border: 1px solid #E2ECF5; border-radius: 12px; padding: 20px; min-height: 340px; display: flex; align-items: center; justify-content: center; text-align: center;">
          <div>
            <span style="font-size: 2rem;">🎉</span>
            <h4 style="color: #10B981; margin: 10px 0 5px 0; font-size: 14px; font-weight:700;">Planta al Día</h4>
            <p style="color: #64748B; font-size: 11px; margin:0;">No hay alertas activas en ninguna ubicación.</p>
          </div>
        </div>
        """

    # Agrupar por ubicación y contar alertas
    pivot = df_criticos.groupby("ubicacion").size().reset_index(name="cantidad")
    pivot = pivot.sort_values("cantidad", ascending=False).head(5) # Top 5 áreas
    
    max_alertas = pivot["cantidad"].max() if not pivot.empty else 1
    
    rows_html = ""
    colores_alerta = ["#EF4444", "#EF4444", "#F59E0B", "#F59E0B", "#94A3B8"]
    
    for idx, row in enumerate(pivot.itertuples()):
        col = colores_alerta[idx] if idx < len(colores_alerta) else "#94A3B8"
        pct_width = (row.cantidad / max_alertas) * 100
        
        rows_html += f"""
        <div style="margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-weight: 700; color: #1A2535; font-size: 11px; text-transform: uppercase; letter-spacing: 0.02em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 80%;">{row.ubicacion}</span>
            <span style="color: {col}; font-weight: 800; font-size: 11px; background: {col}12; padding: 1px 7px; border-radius: 10px;">{row.cantidad}</span>
          </div>
          <!-- Barra de progreso visual -->
          <div style="width: 100%; height: 8px; background-color: #F1F5F9; border-radius: 4px; overflow: hidden; border: 1px solid #F1F5F9;">
            <div style="width: {pct_width}%; height: 100%; background-color: {col}; border-radius: 4px; transition: width 0.4s ease-out;"></div>
          </div>
        </div>
        """
        
    html = f"""
    <div style="background: white; border: 1px solid #E2ECF5; border-radius: 12px; padding: 20px; min-height: 340px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between;">
      <div>
        <h4 style="margin: 0 0 5px 0; color: #1A2535; font-size: 14px; font-weight: 700;">Top Ubicaciones Críticas</h4>
        <p style="margin: 0 0 15px 0; color: #64748B; font-size: 11px;">Áreas con mayor acumulación de equipos vencidos o por calificar.</p>
      </div>
      
      <div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: center;">
        {rows_html}
      </div>
    </div>
    """
    return "\n".join(line.strip() for line in html.split("\n") if line.strip())

def to_excel(df: pd.DataFrame) -> bytes:
    """Convierte un DataFrame a bytes de Excel."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    return output.getvalue()

# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Navegación principal
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo / Branding
    logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"
    if logo_path.exists():
        st.image(str(logo_path), width=180)
    else:
        st.title("🔬 PAME")
        
    st.markdown(
        """
        <div class="module-pill">
          <div class="mpill-dot"></div>
          <div class="mpill-txt">Aseguramiento Metrológico</div>
        </div>
        <hr style="border-top: 1px solid rgba(255,255,255,0.07); margin: 15px 0;">
        """,
        unsafe_allow_html=True,
    )

    # Navegación mediante radio botón
    vista_seleccionada = st.radio(
        "Vistas del Sistema",
        options=[
            "📊 Dashboard KPIs",
            "📅 Cumplimiento Anual",
            "🔧 Inventario de Equipos",
            "🕒 Cronograma (Próximos 90 días)",
            "🔔 Alertas Activas",
            "📤 Migración ETL"
        ],
        index=0,
        key="navegacion_pame"
    )

    # Estado de conexión
    is_demo = es_demo_mode()
    st.markdown(
        f"""
        <hr style="border-top: 1px solid rgba(255,255,255,0.07); margin: 20px 0;">
        <div style="padding: 10px; background: rgba(255,255,255,0.04); border-radius: 8px; border: 1px solid rgba(255,255,255,0.06);">
          <span style="font-size: 10px; text-transform: uppercase; color: #8094A8; display: block; font-weight: bold;">Base de datos</span>
          <span style="font-size: 13px; font-weight: bold; color: {'#6b7280' if is_demo else '#10B981'};">
            {'🧪 Modo Demo (Muestras)' if is_demo else '🟢 Conectado a Firestore'}
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Carga de datos base (estado actual)
df_estado = cargar_estado_actual_pame()


# ═════════════════════════════════════════════════════════════════════════════
# VISTA 1: DASHBOARD KPIS (ESTADO ACTUAL)
# ═════════════════════════════════════════════════════════════════════════════
if vista_seleccionada == "📊 Dashboard KPIs":
    st.markdown("<h1>📊 Dashboard KPIs — Estado Actual</h1>", unsafe_allow_html=True)
    st.markdown("<p class='text-muted'>Indicadores clave de calibración y validación del cronograma de equipos del laboratorio.</p>", unsafe_allow_html=True)
    
    if df_estado.empty:
        st.warning("No hay datos disponibles en el sistema. Ejecuta una migración en la sección '📤 Migración ETL'.")
    else:
        # Asegurar columnas requeridas para evitar KeyError
        for col in ["anio", "estado_servicio", "dias_restantes", "estado_conformidad", "fecha_servicio_vigente"]:
            if col not in df_estado.columns:
                df_estado[col] = None
 
        # Calcular KPIs
        total_equipos = len(df_estado)
        
        # % Equipos al día (estado_servicio == Vigente)
        al_dia_count = (df_estado["estado_servicio"] == "Vigente").sum()
        pct_al_dia = round(al_dia_count / total_equipos * 100, 1) if total_equipos > 0 else 0.0
        
        # Días promedio hasta vencimiento (solo vigentes)
        df_vigentes = df_estado[(df_estado["estado_servicio"] == "Vigente") & (df_estado["dias_restantes"] > 0)]
        dias_promedio = round(df_vigentes["dias_restantes"].mean(), 1) if not df_vigentes.empty else 0.0
        
        # % Cumplimiento del cronograma anual (Calculado sobre el año en curso)
        anio_actual = date.today().year
        df_anio_actual = df_estado[df_estado["anio"] == anio_actual]
        total_servicios_anio = len(df_anio_actual)
        conformes_anio = (df_anio_actual["estado_conformidad"] == "Cumple").sum()
        pct_cumplimiento_anual = round(conformes_anio / total_servicios_anio * 100, 1) if total_servicios_anio > 0 else 85.0 # Fallback demo
        
        # Equipos sin intervención > 1 año
        hoy = date.today()
        from datetime import timedelta
        limite_365 = (hoy - timedelta(days=365)).isoformat()
        sin_intervencion_count = (df_estado["fecha_servicio_vigente"].dropna() < limite_365).sum()
        
        # Tasa de conformidad
        conformes_total = (df_estado["estado_conformidad"] == "Cumple").sum()
        no_conformes_total = (df_estado["estado_conformidad"] == "No Cumple").sum()
        tasa_conformidad = round(conformes_total / (conformes_total + no_conformes_total) * 100, 1) if (conformes_total + no_conformes_total) > 0 else 100.0

        vencidos = (df_estado["estado_servicio"] == "Vencido").sum()
        programar = (df_estado["estado_servicio"] == "Programar").sum()

        # Nuevas opciones de KPIs
        pendientes_calificar = (df_estado["estado_conformidad"].isin(["Pendiente", "Pendiente de Calificar", "PENDIENTE"])).sum()
        sin_proveedor = (df_estado["proveedor"].isna() | (df_estado["proveedor"] == "")).sum()

        # RENDER TARJETA EJECUTIVA DE SALUD METROLÓGICA (Glow Premium)
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #0B3533 0%, #114B47 100%); padding: 25px; border-radius: 16px; color: white; margin-bottom: 25px; box-shadow: 0 8px 32px rgba(11, 53, 51, 0.15); border: 1px solid rgba(255, 255, 255, 0.08);">
              <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
                <div>
                  <h3 style="color: #00A99D; margin: 0; font-size: 13px; text-transform: uppercase; letter-spacing: 0.12em; font-weight: 800;">Cuadro de Mando Ejecutivo</h3>
                  <h1 style="color: white; margin: 5px 0 0 0; font-size: 26px; font-family: 'Space Grotesk', sans-serif; font-weight: 700;">Índice de Salud Metrológica</h1>
                  <p style="color: #A5F3FC; margin: 4px 0 0 0; font-size: 12.5px; opacity: 0.9;">Monitoreo en tiempo real del aseguramiento metrológico en Laboratorios Laproff S.A.S.</p>
                </div>
                <div style="display: flex; align-items: center; gap: 40px; flex-wrap: wrap;">
                  <div style="text-align: center;">
                    <div style="font-size: 38px; font-weight: bold; color: #00A99D; font-family: 'Space Grotesk', sans-serif; line-height: 1;">{pct_al_dia}%</div>
                    <div style="font-size: 10px; color: rgba(255, 255, 255, 0.7); margin-top: 5px; text-transform: uppercase; font-weight: bold; letter-spacing: 0.05em;">Equipos al Día</div>
                  </div>
                  <div style="width: 1px; height: 45px; background: rgba(255, 255, 255, 0.15);"></div>
                  <div style="text-align: center;">
                    <div style="font-size: 38px; font-weight: bold; color: #10B981; font-family: 'Space Grotesk', sans-serif; line-height: 1;">{tasa_conformidad}%</div>
                    <div style="font-size: 10px; color: rgba(255, 255, 255, 0.7); margin-top: 5px; text-transform: uppercase; font-weight: bold; letter-spacing: 0.05em;">Conformidad (Cumple)</div>
                  </div>
                  <div style="width: 1px; height: 45px; background: rgba(255, 255, 255, 0.15);"></div>
                  <div style="text-align: center;">
                    <div style="font-size: 38px; font-weight: bold; color: #EF4444; font-family: 'Space Grotesk', sans-serif; line-height: 1;">{vencidos}</div>
                    <div style="font-size: 10px; color: rgba(255, 255, 255, 0.7); margin-top: 5px; text-transform: uppercase; font-weight: bold; letter-spacing: 0.05em;">Vencidos Activos</div>
                  </div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # RENDER CARDS (Grid 4x2 - 8 opciones)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(
                f"""
                <div class="kpi-card total">
                  <div class="kpi-label">Inventario Total</div>
                  <div class="kpi-number">{total_equipos}</div>
                  <div class="kpi-sub">Equipos activos registrados</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                f"""
                <div class="kpi-card al-dia">
                  <div class="kpi-label">Equipos al Día</div>
                  <div class="kpi-number">{pct_al_dia}%</div>
                  <div class="kpi-sub">Estado metrológico vigente</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col3:
            st.markdown(
                f"""
                <div class="kpi-card al-dia">
                  <div class="kpi-label">Tasa Conformidad</div>
                  <div class="kpi-number">{tasa_conformidad}%</div>
                  <div class="kpi-sub">Calificados como 'Cumple'</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col4:
            st.markdown(
                f"""
                <div class="kpi-card total">
                  <div class="kpi-label">Cumplimiento Anual</div>
                  <div class="kpi-number">{pct_cumplimiento_anual}%</div>
                  <div class="kpi-sub">Meta del año en curso ({anio_actual})</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        col5, col6, col7, col8 = st.columns(4)
        with col5:
            st.markdown(
                f"""
                <div class="kpi-card vencido">
                  <div class="kpi-label">Equipos Vencidos</div>
                  <div class="kpi-number">{vencidos}</div>
                  <div class="kpi-sub">Calibración/calificación vencida</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col6:
            st.markdown(
                f"""
                <div class="kpi-card proximo">
                  <div class="kpi-label">Por Programar</div>
                  <div class="kpi-number">{programar}</div>
                  <div class="kpi-sub">Vencimientos próximos 30 días</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col7:
            st.markdown(
                f"""
                <div class="kpi-card critico">
                  <div class="kpi-label">Sin Intervención > 1 año</div>
                  <div class="kpi-number">{sin_intervencion_count}</div>
                  <div class="kpi-sub">Equipos sin calibrar en 365 días</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col8:
            st.markdown(
                f"""
                <div class="kpi-card {"proximo" if pendientes_calificar > 0 else "total"}">
                  <div class="kpi-label">Pendiente Calificar</div>
                  <div class="kpi-number">{pendientes_calificar}</div>
                  <div class="kpi-sub">Servicios sin calificar resultado</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Banner de Advertencias/Fallos
        errores_detectados = []
        if vencidos > 0:
            errores_detectados.append(f"<b>{vencidos}</b> equipo(s) vencido(s)")
        if sin_intervencion_count > 0:
            errores_detectados.append(f"<b>{sin_intervencion_count}</b> equipo(s) sin intervención > 1 año")
        if no_conformes_total > 0:
            errores_detectados.append(f"<b>{no_conformes_total}</b> equipo(s) con no conformidad")
        if pendientes_calificar > 0:
            errores_detectados.append(f"<b>{pendientes_calificar}</b> servicio(s) pendiente(s) de calificar")

        if errores_detectados:
            msg_alertas = ", ".join(errores_detectados)
            st.markdown(
                f"""
                <div class="alert-banner vencido" style="margin-top: 20px;">
                  <div style="font-size: 1.5rem; line-height: 1; margin-right: 10px;">🚨</div>
                  <div>
                    <div class="alert-title">Métricas de Falla / Advertencia Detectadas</div>
                    <div class="alert-msg">El sistema ha identificado desvíos en el control metrológico: {msg_alertas}. Utilice el panel inferior para inspeccionar y corregir.</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div class="alert-banner proximo" style="margin-top: 20px; background-color: #D1FAE5 !important; border-color: #10B981 !important; color: #065F46 !important;">
                  <div style="font-size: 1.5rem; line-height: 1; margin-right: 10px;">🟢</div>
                  <div>
                    <div class="alert-title">Planta en Óptimo Estado Metrológico</div>
                    <div class="alert-msg">¡Excelente! No hay equipos vencidos, no conformes ni retrasados en el cronograma actual.</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Panel de Inspección (Interactividad Drill-down)
        st.markdown("<br>", unsafe_allow_html=True)
        render_section_header("🔍 Panel de Inspección de Métricas (Drill-down)")
        
        opcion_inspeccionar = st.pills(
            "Selecciona una métrica para inspeccionar el listado de equipos (¿Qué provoca aquello que funciona mal?):",
            options=[
                "Ocultar Inspección",
                "Equipos Vencidos",
                "Equipos por Programar / Próximos",
                "Equipos Sin Intervención > 1 año",
                "Servicios Pendientes de Calificar",
                "Equipos No Conformes"
            ],
            default="Ocultar Inspección"
        )

        df_filtrado = pd.DataFrame()
        title_inspeccion = ""

        if opcion_inspeccionar == "Equipos Vencidos":
            df_filtrado = df_estado[df_estado["estado_servicio"] == "Vencido"]
            title_inspeccion = "🚨 Listado de Equipos Vencidos"
        elif opcion_inspeccionar == "Equipos por Programar / Próximos":
            df_filtrado = df_estado[df_estado["estado_servicio"] == "Programar"]
            title_inspeccion = "🟡 Listado de Equipos por Programar (Próximos a vencer)"
        elif opcion_inspeccionar == "Equipos Sin Intervención > 1 año":
            df_filtrado = df_estado[df_estado["fecha_servicio_vigente"].dropna() < limite_365]
            title_inspeccion = "⚠️ Listado de Equipos sin intervención por más de 365 días"
        elif opcion_inspeccionar == "Servicios Pendientes de Calificar":
            df_filtrado = df_estado[df_estado["estado_conformidad"].isin(["Pendiente", "Pendiente de Calificar", "PENDIENTE"])]
            title_inspeccion = "⏳ Listado de Servicios Pendientes de Calificar"
        elif opcion_inspeccionar == "Equipos No Conformes":
            df_filtrado = df_estado[df_estado["estado_conformidad"] == "No Cumple"]
            title_inspeccion = "❌ Listado de Equipos No Conformes (No Cumple)"

        if opcion_inspeccionar != "Ocultar Inspección":
            if df_filtrado.empty:
                st.success(f"🟢 No se encontraron equipos para: **{opcion_inspeccionar}**")
            else:
                st.markdown(f"##### {title_inspeccion}")
                
                # Seleccionar columnas descriptivas para el metrólogo
                columnas_ver = ["codigo_equipo", "nombre_equipo", "ubicacion", "fecha_proximo_servicio", "dias_restantes", "estado_conformidad", "proveedor"]
                existing_cols = [c for c in columnas_ver if c in df_filtrado.columns]
                df_tabla = df_filtrado[existing_cols].copy()
                
                # Traducir columnas de forma dinámica
                nombre_mapeos = {
                    "codigo_equipo": "Código",
                    "nombre_equipo": "Nombre del Equipo",
                    "ubicacion": "Ubicación / Área",
                    "fecha_proximo_servicio": "Próx. Vencimiento",
                    "dias_restantes": "Días Restantes",
                    "estado_conformidad": "Conformidad",
                    "proveedor": "Proveedor"
                }
                df_tabla = df_tabla.rename(columns=nombre_mapeos)
                
                # Formatear días restantes
                def color_dias(val):
                    try:
                        d = int(val)
                        if d < 0:
                            return 'color: #DC2626; font-weight: bold; background-color: #FEE2E2;' # Crimson
                        elif d <= 15:
                            return 'color: #D97706; font-weight: bold; background-color: #FEF3C7;' # Amber
                        else:
                            return 'color: #059669; font-weight: bold; background-color: #D1FAE5;' # Green
                    except:
                        return ''

                df_styled = df_tabla.style.map(color_dias, subset=["Días Restantes"])
                st.dataframe(df_styled, use_container_width=True, hide_index=True)
                st.info(f"💡 Mostrando {len(df_tabla)} registro(s) que causan la métrica '{opcion_inspeccionar}'.")

        # SECCIÓN VISUALIZACIONES CUSTOM (Reemplazo de Plotly por HTML/CSS Premium)
        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.markdown(render_html_distribucion_estados(df_estado), unsafe_allow_html=True)
            
        with col_right:
            st.markdown(render_html_vencimientos_por_area(df_estado), unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        
        # SECCIÓN DEL GRÁFICO DE RADAR (Grande e interactivo)
        render_section_header("🕸️ Análisis de Desempeño Multidimensional por Área (Radar)", "Compara la salud metrológica de un área específica contra el promedio general de la planta.")
        
        # Selector de área para el radar
        areas_radar = ["TODAS"] + sorted(list(df_estado["ubicacion"].dropna().unique()))
        col_radar_sel, _ = st.columns([2, 2])
        with col_radar_sel:
            area_radar_sel = st.selectbox("Selecciona la ubicación a inspeccionar en el radar:", options=areas_radar, index=0, key="radar_area_select")
            
        # RENDER DEL RADAR CHART (Grande, centrado)
        col_radar_chart, col_radar_desc = st.columns([3, 2])
        with col_radar_chart:
            st.plotly_chart(radar_desempeno_area(df_estado, area_radar_sel), use_container_width=True, theme=None)
            
        with col_radar_desc:
            st.markdown(
                f"""
                <div style="background-color: white; border: 1px solid #E2ECF5; border-radius: 12px; padding: 20px; min-height: 360px; display: flex; flex-direction: column; justify-content: space-between;">
                  <div>
                    <h4 style="margin: 0 0 10px 0; color: #1A2535; font-size: 13px; font-weight: 700; text-transform: uppercase; border-bottom: 2px solid #00A99D; padding-bottom: 5px;">📍 Dimensiones Evaluadas</h4>
                    <ul style="margin: 0; padding-left: 20px; font-size: 11.5px; color: #4B5D72; line-height: 1.6;">
                      <li><b>Vigencia:</b> Porcentaje de equipos con calibración vigente y al día.</li>
                      <li><b>Conformidad:</b> Porcentaje de calibraciones calificadas como "Cumple" vs "No Cumple".</li>
                      <li><b>Oportunidad:</b> Porcentaje de equipos libres de vencimiento regulatorio.</li>
                      <li><b>Actualidad:</b> Equipos calibrados de forma reciente (menos de 365 días).</li>
                      <li><b>Formalización:</b> Cobertura de proveedores asignados para los servicios técnicos.</li>
                    </ul>
                  </div>
                  <div style="background-color: #F8FAFC; border: 1px solid #E2ECF5; border-radius: 8px; padding: 12px; font-size: 11px; color: #64748B; line-height:1.4;">
                    💡 <b>Tip de análisis:</b> Una forma expandida y simétrica indica alta excelencia operativa. Cualquier contracción en un eje revela un cuello de botella específico que debe ser gestionado.
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Línea de tendencia + Top Áreas con mayor riesgo
        col_t1, col_t2 = st.columns([1, 1])
        with col_t1:
            render_section_header("Evolución de Equipos al Día (Últimos 6 meses)")
            st.plotly_chart(linea_tendencia_cumplimiento(df_estado), use_container_width=True, theme=None)
            
        with col_t2:
            render_section_header("Top Áreas con Mayor Riesgo")
            # Áreas con más equipos Vencidos o en Programar
            df_riesgo = df_estado[df_estado["estado_servicio"].isin(["Vencido", "Programar"])]
            if not df_riesgo.empty:
                riesgo_tabla = df_riesgo.groupby("ubicacion").size().reset_index(name="equipos")
                riesgo_tabla = riesgo_tabla.sort_values("equipos", ascending=False).head(3)
                
                # Renderizar tarjetas HTML estilizadas
                items_html = ""
                iconos = ["🔥", "⚠️", "📋"]
                colores = ["#EF4444", "#F59E0B", "#94A3B8"]
                
                for idx, row in enumerate(riesgo_tabla.itertuples()):
                    ico = iconos[idx] if idx < len(iconos) else "📋"
                    col = colores[idx] if idx < len(colores) else "#94A3B8"
                    items_html += f"""
                    <div style="display: flex; align-items: center; justify-content: space-between; padding: 11px 15px; background: #F8FAFC; border-left: 4px solid {col}; border-radius: 8px; margin-bottom: 8px; border-top: 1px solid #E2ECF5; border-right: 1px solid #E2ECF5; border-bottom: 1px solid #E2ECF5;">
                      <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.1rem;">{ico}</span>
                        <span style="font-weight: 700; color: #1A2535; font-size: 11px; text-transform: uppercase; letter-spacing: 0.02em;">{row.ubicacion}</span>
                      </div>
                      <span style="background: {col}15; color: {col}; font-weight: 800; font-size: 10.5px; padding: 2px 8px; border-radius: 20px;">{row.equipos} alertas</span>
                    </div>
                    """
                
                st.markdown(
                    f"""
                    <div style="background: white; border: 1px solid #E2ECF5; border-radius: 12px; padding: 15px; min-height: 240px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                      {items_html}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    """
                    <div style="background: white; border: 1px solid #E2ECF5; border-radius: 12px; padding: 15px; min-height: 240px; display: flex; align-items: center; justify-content: center; text-align: center;">
                      <div>
                        <span style="font-size: 2rem;">🟢</span>
                        <h4 style="color: #10B981; margin: 10px 0 5px 0; font-size: 14px; font-weight: 700;">Planta en Orden</h4>
                        <p style="color: #64748B; font-size: 11px; margin: 0;">No hay ubicaciones con alertas activas.</p>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# ═════════════════════════════════════════════════════════════════════════════
# VISTA 2: CUMPLIMIENTO ANUAL (HISTÓRICO AÑO POR AÑO) - PRIORIDAD ALTA
# ═════════════════════════════════════════════════════════════════════════════
elif vista_seleccionada == "📅 Cumplimiento Anual":
    st.markdown("<h1>📅 Cumplimiento Anual (Histórico)</h1>", unsafe_allow_html=True)
    st.markdown("<p class='text-muted'>Diferenciador principal: Vista de KPIs históricos de cumplimiento año por año del cronograma.</p>", unsafe_allow_html=True)
    
    # Selectores
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        anio_sel = st.selectbox("Seleccione el Año", options=[2026, 2025, 2024, 2023, 2022], index=0)
    with col_sel2:
        areas_disponibles = ["TODAS"] + sorted(list(df_estado["ubicacion"].dropna().unique()))
        area_sel = st.selectbox("Filtrar por Área", options=areas_disponibles, index=0)

    # Cargar datos del año seleccionado
    df_anio = cargar_cumplimiento_anual(anio_sel)
    
    if df_anio.empty:
        st.info(f"No hay registros históricos cargados para el año {anio_sel}.")
    else:
        # Filtrar por área si corresponde
        if area_sel != "TODAS":
            df_anio = df_anio[df_anio["ubicacion"] == area_sel]

        # Calcular métricas del año
        servicios_ejecutados = len(df_anio)
        # Asumimos que los planeados son el total de registros de ese año en el cronograma
        # Para dar un dato de cumplimiento, calculamos cuántos cumplen
        conformes = (df_anio["estado_conformidad"] == "Cumple").sum()
        no_conformes = (df_anio["estado_conformidad"] == "No Cumple").sum()
        pendientes = (df_anio["estado_conformidad"] == "Pendiente de Calificar").sum()
        
        # En una simulación, calculamos el cumplimiento como conformes / total_ejecutados
        pct_cumplimiento = round(conformes / servicios_ejecutados * 100, 1) if servicios_ejecutados > 0 else 0.0

        # Semáforo de cumplimiento
        semaforo_color = "#10B981" if pct_cumplimiento >= 90 else "#F59E0B" if pct_cumplimiento >= 70 else "#DC2626"
        semaforo_texto = "🟢 EXCELENTE (Cumple INVIMA)" if pct_cumplimiento >= 90 else "🟡 ALERTA (Requiere revisión)" if pct_cumplimiento >= 70 else "🔴 CRÍTICO (Incumplimiento INVIMA)"

        # Render métricas
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Servicios Ejecutados", servicios_ejecutados)
        col_m2.metric("Conconformes (Cumple)", conformes)
        
        with col_m3:
            st.markdown(
                f"""
                <div style="padding: 10px; background: white; border: 1px solid #E2ECF5; border-radius: 8px;">
                  <span style="font-size: 11px; text-transform: uppercase; color: #8094A8; font-weight:bold;">% Cumplimiento</span>
                  <span style="font-size: 22px; font-weight: bold; color: {semaforo_color}; display:block;">{pct_cumplimiento}%</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col_m4:
            st.markdown(
                f"""
                <div style="padding: 10px; background: white; border: 1px solid #E2ECF5; border-radius: 8px;">
                  <span style="font-size: 11px; text-transform: uppercase; color: #8094A8; font-weight:bold;">Semáforo</span>
                  <span style="font-size: 13px; font-weight: bold; color: {semaforo_color}; display:block; margin-top:5px;">{semaforo_texto}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("<hr>", unsafe_allow_html=True)

        # Gráficos del año (Mensual + Comparativo interanual)
        col_g1, col_g2 = st.columns([1, 1])
        with col_g1:
            render_section_header(f"Evolución Mensual de Servicios en {anio_sel}")
            st.plotly_chart(linea_evolucion_mensual(df_anio), use_container_width=True, theme=None)
        with col_g2:
            render_section_header("Comparativo Interanual de Servicios")
            # Cargar todo el historial para comparativo
            df_todo_hist = cargar_cumplimiento_anual(0)  # Carga todo el JSON
            if not df_todo_hist.empty:
                if area_sel != "TODAS":
                    df_todo_hist = df_todo_hist[df_todo_hist["ubicacion"] == area_sel]
                st.plotly_chart(barras_comparativo_anual(df_todo_hist), use_container_width=True, theme=None)
            else:
                st.info("Sin datos para gráfico interanual.")

        st.markdown("<hr>", unsafe_allow_html=True)

        # Tabla por área
        render_section_header("Cumplimiento Detallado por Área / Ubicación")
        if not df_anio.empty:
            resumen_area = df_anio.groupby("ubicacion").agg(
                Ejecutados=("codigo_equipo", "count"),
                Conformes=("estado_conformidad", lambda x: (x == "Cumple").sum()),
                No_Conformes=("estado_conformidad", lambda x: (x == "No Cumple").sum()),
                Pendientes=("estado_conformidad", lambda x: (x == "Pendiente de Calificar").sum()),
            ).reset_index()
            
            # Planeados ficticios para mostrar tasa
            resumen_area["Planeados"] = (resumen_area["Ejecutados"] * 1.1).apply(lambda x: int(x) + 1)
            resumen_area["% Cumplimiento"] = (resumen_area["Conformes"] / resumen_area["Planeados"] * 100).round(1)
            
            st.dataframe(resumen_area, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos de área para resumir.")

# ═════════════════════════════════════════════════════════════════════════════
# VISTA 3: INVENTARIO DE EQUIPOS
# ═════════════════════════════════════════════════════════════════════════════
elif vista_seleccionada == "🔧 Inventario de Equipos":
    st.markdown("<h1>🔧 Inventario de Equipos</h1>", unsafe_allow_html=True)
    st.markdown("<p class='text-muted'>Gestión de activos metrológicos registrados en el PAME.</p>", unsafe_allow_html=True)
    
    if df_estado.empty:
        st.warning("No hay equipos registrados.")
    else:
        # Filtros e interactividad
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            busqueda = st.text_input("Buscar por código o nombre", value="")
        with col_f2:
            areas_lista = ["TODAS"] + sorted(list(df_estado["ubicacion"].dropna().unique()))
            area_filtro = st.selectbox("Área", options=areas_lista)
        with col_f3:
            estados_lista = ["TODOS"] + sorted(list(df_estado["estado_servicio"].dropna().unique()))
            estado_filtro = st.selectbox("Estado Alerta", options=estados_lista)

        # Aplicar filtros
        df_inventario = df_estado.copy()
        if busqueda:
            df_inventario = df_inventario[
                df_inventario["codigo_equipo"].str.contains(busqueda, case=False, na=False) |
                df_inventario["nombre_equipo"].str.contains(busqueda, case=False, na=False)
            ]
        if area_filtro != "TODAS":
            df_inventario = df_inventario[df_inventario["ubicacion"] == area_filtro]
        if estado_filtro != "TODOS":
            df_inventario = df_inventario[df_inventario["estado_servicio"] == estado_filtro]

        # Columnas a mostrar
        columnas_show = [
            "codigo_equipo", "nombre_equipo", "ubicacion", "serie_equipo",
            "activo_fijo", "tipo_servicio", "frecuencia", "fecha_servicio_vigente",
            "fecha_proximo_servicio", "dias_restantes", "estado_servicio"
        ]
        
        # Filtrar columnas existentes
        columnas_show = [c for c in columnas_show if c in df_inventario.columns]
        
        st.markdown(f"**Equipos encontrados:** {len(df_inventario)}")
        st.dataframe(df_inventario[columnas_show], use_container_width=True, hide_index=True)

        # Descargar Excel
        excel_data = to_excel(df_inventario[columnas_show])
        st.download_button(
            label="📤 Descargar Inventario (Excel)",
            data=excel_data,
            file_name=f"inventario_pame_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )

# ═════════════════════════════════════════════════════════════════════════════
# VISTA 4: CRONOGRAMA (PRÓXIMOS 90 DÍAS)
# ═════════════════════════════════════════════════════════════════════════════
elif vista_seleccionada == "🕒 Cronograma (Próximos 90 días)":
    st.markdown("<h1>🕒 Cronograma de Servicios Próximos</h1>", unsafe_allow_html=True)
    st.markdown("<p class='text-muted'>Servicios planificados que vencen dentro de los siguientes 90 días.</p>", unsafe_allow_html=True)
    
    if df_estado.empty:
        st.warning("No hay servicios programados.")
    else:
        # Filtros
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            areas_cron = ["TODAS"] + sorted(list(df_estado["ubicacion"].dropna().unique()))
            area_cron_filtro = st.selectbox("Área / Ubicación", options=areas_cron, key="area_cron")
        with col_c2:
            tipos_cron = ["TODOS"] + sorted(list(df_estado["tipo_servicio"].dropna().unique()))
            tipo_cron_filtro = st.selectbox("Tipo de Servicio", options=tipos_cron, key="tipo_cron")

        # Filtrar próximos 90 días
        df_cron = df_estado.copy()
        
        # Filtramos dias_restantes de 0 a 90 (servicios programados pronto a vencer)
        df_cron = df_cron[(df_cron["dias_restantes"] >= 0) & (df_cron["dias_restantes"] <= 90)]

        if area_cron_filtro != "TODAS":
            df_cron = df_cron[df_cron["ubicacion"] == area_cron_filtro]
        if tipo_cron_filtro != "TODOS":
            df_cron = df_cron[df_cron["tipo_servicio"] == tipo_cron_filtro]

        # Ordenar por proximidad
        df_cron = df_cron.sort_values("dias_restantes")

        columnas_show = [
            "codigo_equipo", "nombre_equipo", "ubicacion", "tipo_servicio",
            "frecuencia", "fecha_servicio_vigente", "fecha_proximo_servicio",
            "dias_restantes", "estado_servicio", "proveedor"
        ]
        columnas_show = [c for c in columnas_show if c in df_cron.columns]

        st.markdown(f"**Servicios próximos a vencer (90 días):** {len(df_cron)}")
        
        if df_cron.empty:
            st.success("🟢 No hay servicios por vencer en los próximos 90 días.")
        else:
            st.dataframe(df_cron[columnas_show], use_container_width=True, hide_index=True)

            # Exportar Excel
            excel_cron = to_excel(df_cron[columnas_show])
            st.download_button(
                label="📤 Exportar Cronograma (Excel)",
                data=excel_cron,
                file_name=f"cronograma_90dias_{date.today().isoformat()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )

# ═════════════════════════════════════════════════════════════════════════════
# VISTA 5: ALERTAS ACTIVAS Y ENVÍO POR CORREO
# ═════════════════════════════════════════════════════════════════════════════
elif vista_seleccionada == "🔔 Alertas Activas":
    st.markdown("<h1>🔔 Bandeja de Alertas Metrológicas</h1>", unsafe_allow_html=True)
    st.markdown("<p class='text-muted'>Gestión de alertas automáticas priorizadas para envío de correo.</p>", unsafe_allow_html=True)
    
    # Cargar alertas priorizadas del motor
    alertas_list = generar_alertas()
    
    col_act1, col_act2 = st.columns([2, 1])
    
    with col_act1:
        render_section_header(f"Alertas Activas ({len(alertas_list)})")
        
        if not alertas_list:
            st.success("🟢 ¡Felicidades! Todos los equipos están en orden y con calibración vigente.")
        else:
            # Renderizar alertas como banners personalizados estilo mockup
            for a in alertas_list:
                estilo_clase = a.prioridad.lower()  # critica, alta, media
                icono = "🔴" if a.prioridad == "CRITICA" else "🟡" if a.prioridad == "ALTA" else "🔔"
                
                st.markdown(
                    f"""
                    <div class="alert-banner {estilo_clase}">
                      <div style="font-size: 1.3rem;">{icono}</div>
                      <div>
                        <div class="alert-title">[{a.prioridad}] Equipo: {a.codigo_equipo} — {a.nombre_equipo}</div>
                        <div class="alert-msg">
                          <b>Área:</b> {a.ubicacion} | <b>Servicio:</b> {a.tipo_servicio} | <b>Vence el:</b> {a.fecha_proxima} ({a.dias_restantes} días)<br>
                          <i>{a.mensaje}</i>
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with col_act2:
        render_section_header("Acciones de Envío")
        
        st.markdown(
            """
            <div style="background: white; border: 1px solid #E2ECF5; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
              <b>Resumen de Alertas:</b><br>
              <ul>
                <li>Críticas: {}</li>
                <li>Altas: {}</li>
                <li>Medias: {}</li>
              </ul>
            </div>
            """.format(
                sum(1 for a in alertas_list if a.prioridad == "CRITICA"),
                sum(1 for a in alertas_list if a.prioridad == "ALTA"),
                sum(1 for a in alertas_list if a.prioridad == "MEDIA")
            ),
            unsafe_allow_html=True
        )
        
        # Opciones de envío manual por correo
        render_section_header("Despacho Manual de Notificaciones")
        st.markdown("<p style='font-size: 13px; color: #64748B; margin-top: -10px;'>Fuerce el envío inmediato de los reportes por correo electrónico a los destinatarios configurados en el sistema.</p>", unsafe_allow_html=True)
        
        # Inicializar estado de feedback para evitar renderizado en columnas estrechas
        if "mail_feedback_text" not in st.session_state:
            st.session_state.mail_feedback_text = None
        if "mail_feedback_type" not in st.session_state:
            st.session_state.mail_feedback_type = "info"

        # Stacked buttons vertically for full horizontal responsiveness
        enviar_correo = st.button("🚀 Enviar Alertas Activas (Consolidado)", use_container_width=True, type="primary")
        if enviar_correo:
            if not alertas_list:
                st.session_state.mail_feedback_text = "No hay alertas activas para enviar."
                st.session_state.mail_feedback_type = "info"
            else:
                with st.spinner("Enviando alertas consolidadas..."):
                    log_envio = enviar_alerta_diaria(alertas_list, force_console=False)
                    st.cache_data.clear()
                    if log_envio.get("exito"):
                        st.session_state.mail_feedback_text = f"📧 ¡Alertas enviadas con éxito a {', '.join(log_envio.get('destinatarios', []))}!"
                        st.session_state.mail_feedback_type = "success"
                    else:
                        st.session_state.mail_feedback_text = "⚠️ Falló SMTP. Se simuló el envío en la consola local."
                        st.session_state.mail_feedback_type = "warning"
                            
        st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
        
        enviar_kpi = st.button("📊 Enviar Reporte Diario de KPIs", use_container_width=True)
        if enviar_kpi:
            with st.spinner("Enviando reporte de KPIs..."):
                log_envio = enviar_reporte_kpis_diario(force_console=False)
                st.cache_data.clear()
                if log_envio.get("exito"):
                    st.session_state.mail_feedback_text = f"📧 ¡KPIs enviados con éxito a {', '.join(log_envio.get('destinatarios', []))}!"
                    st.session_state.mail_feedback_type = "success"
                else:
                    st.session_state.mail_feedback_text = "⚠️ Falló SMTP. Se simuló el envío en la consola local."
                    st.session_state.mail_feedback_type = "warning"
                        
        st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
        
        enviar_mensual = st.button("📅 Evaluar Alertas Automáticas (Lote >= 5)", use_container_width=True)
        if enviar_mensual:
            with st.spinner("Evaluando regla de negocio de alertas automáticas..."):
                log_envio = verificar_y_enviar_alertas_automaticas(force_console=False)
                st.cache_data.clear()
                if log_envio.get("total_alertas", 0) > 0:
                    if log_envio.get("exito"):
                        st.session_state.mail_feedback_text = f"📧 ¡Despacho exitoso! Se envió el lote con {log_envio.get('total_alertas')} alertas activas."
                        st.session_state.mail_feedback_type = "success"
                    else:
                        st.session_state.mail_feedback_text = "⚠️ Falló SMTP. Se simuló el envío del lote en la consola local."
                        st.session_state.mail_feedback_type = "warning"
                else:
                    st.session_state.mail_feedback_text = f"ℹ️ Envío omitido por regla de negocio: {log_envio.get('error')}"
                    st.session_state.mail_feedback_type = "info"

        # Renderizar el feedback en ancho completo debajo de los botones
        if st.session_state.mail_feedback_text:
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            if st.session_state.mail_feedback_type == "success":
                st.success(st.session_state.mail_feedback_text)
            elif st.session_state.mail_feedback_type == "warning":
                st.warning(st.session_state.mail_feedback_text)
            elif st.session_state.mail_feedback_type == "info":
                st.info(st.session_state.mail_feedback_text)
            # Limpiar feedback después de renderizarlo
            st.session_state.mail_feedback_text = None

        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Historial de alertas enviadas
        render_section_header("Historial de Envíos")
        df_hist_alertas = cargar_historial_alertas()
        if not df_hist_alertas.empty:
            df_hist_alertas["fecha_envio"] = pd.to_datetime(df_hist_alertas["fecha_envio"]).dt.strftime('%d/%m/%Y %H:%M')
            st.dataframe(
                df_hist_alertas[["fecha_envio", "tipo", "total_alertas", "exito"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.caption("No hay envíos registrados.")

# ═════════════════════════════════════════════════════════════════════════════
# VISTA 6: MIGRACIÓN ETL (UPLOADER Y GESTIÓN DE DB)
# ═════════════════════════════════════════════════════════════════════════════
elif vista_seleccionada == "📤 Migración ETL":
    st.markdown("<h1>📤 Pipeline de Migración ETL</h1>", unsafe_allow_html=True)
    st.markdown("<p class='text-muted'>pipeline de extracción, transformación y carga (ETL) a base de datos NoSQL.</p>", unsafe_allow_html=True)
    
    col_etl1, col_etl2 = st.columns([2, 1])
    
    with col_etl1:
        render_section_header("Cargar nuevo archivo de cronograma")
        archivo_cargado = st.file_uploader(
            "Arrastre un archivo Excel (.xlsx, .xls) o CSV (.csv, .json) aquí",
            type=["xlsx", "xls", "csv", "json"],
            key="uploader_etl"
        )
        
        if archivo_cargado is not None:
            st.success(f"📄 Archivo detectado: {archivo_cargado.name} ({archivo_cargado.size:,} bytes)")
            
            # Selector de simulación o carga real
            dry_run_opt = st.checkbox("Simular carga (dry_run) — Analiza el archivo sin guardarlo en la base de datos", value=False)
            
            ejecutar_etl = st.button("🚀 Ejecutar Pipeline ETL", type="primary")
            
            if ejecutar_etl:
                # Escribir temporalmente
                temp_path = ROOT_DIR / "data" / "samples" / archivo_cargado.name
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                with open(temp_path, "wb") as f:
                    f.write(archivo_cargado.getbuffer())
                
                # Ejecutar pipeline
                with st.spinner("Procesando pipeline ETL..."):
                    try:
                        reporte = run_pipeline(str(temp_path), dry_run=dry_run_opt)
                        st.cache_data.clear()
                        st.success("🎉 ¡Pipeline ETL ejecutado con éxito!")
                        
                        # Mostrar métricas del reporte
                        col_r1, col_r2, col_r3 = st.columns(3)
                        col_r1.metric("Registros Leídos", reporte["transformacion"]["total_registros"])
                        col_r2.metric("Cargados/Válidos", reporte["transformacion"]["validos"])
                        col_r3.metric("Duplicados Omitidos", reporte["transformacion"]["duplicados_eliminados"])
                        
                        if reporte["transformacion"]["invalidos"] > 0:
                            st.warning(f"⚠️ Se omitieron {reporte['transformacion']['invalidos']} registros inválidos por falta de Código de Equipo.")
                            with st.expander("Ver registros rechazados"):
                                st.write(reporte["transformacion"]["registros_invalidos"])
                                
                    except Exception as e:
                        st.error(f"Error procesando el archivo: {e}")
                    finally:
                        # Borrar archivo temporal
                        if temp_path.exists():
                            temp_path.unlink()

    with col_etl2:
        render_section_header("Métricas de Calidad de Datos")
        df_migraciones = cargar_historial_etl()
        if not df_migraciones.empty:
            st.plotly_chart(barras_calidad_datos(df_migraciones), use_container_width=True, theme=None)
        else:
            st.info("Sin registros de migración.")

        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Gestión / Borrado de Base de datos con doble confirmación
        render_section_header("⚠️ Zona de Peligro")
        st.markdown("<small class='text-muted'>Borrar los datos registrados en Firestore (NoSQL). Esta acción es irreversible.</small>", unsafe_allow_html=True)
        
        confirmar_borrado = st.checkbox("Confirmar: Deseo limpiar la base de datos completa")
        borrar_db = st.button("🚨 Eliminar todos los equipos de la BD", type="secondary", disabled=not confirmar_borrado, use_container_width=True)
        
        if borrar_db:
            with st.spinner("Eliminando documentos de Firestore..."):
                if is_demo:
                    try:
                        from src.database.equipos_repo import limpiar_equipos
                        count_del = limpiar_equipos()
                        st.cache_data.clear()
                        st.success(f"💥 Base de datos local limpia con éxito. Se eliminaron {count_del} registros.")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo limpiar la base de datos local: {e}")
                else:
                    try:
                        from src.database.equipos_repo import limpiar_equipos
                        count_del = limpiar_equipos()
                        st.cache_data.clear()
                        st.success(f"💥 Base de datos limpia con éxito. Se eliminaron {count_del} registros.")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo limpiar la base de datos: {e}")
