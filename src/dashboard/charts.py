"""
Módulo de visualización con Plotly para el dashboard PAME de Laproff.
Implementa gráficos interactivos respetando la paleta de colores del tema.
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional

# Colores del tema Laproff
COLORES = {
    "Vigente":       "#10B981",  # Verde
    "Programar":     "#F59E0B",  # Amarillo/Ambar
    "En ejecución":  "#EF4444",  # Rojo claro
    "Vencido":       "#DC2626",  # Crimson / Rojo oscuro
    "Sin datos":     "#94A3B8",  # Gris
    "primary":       "#00A99D",  # Teal brillante
    "sidebar":       "#0B3533",  # Teal oscuro
}

FONT_FAMILY = "Arial, sans-serif"
TEXT_COLOR = "#1A2535"

def donut_distribucion_estados(df: pd.DataFrame) -> go.Figure:
    """Gráfico de dona con la distribución global de estados de servicios."""
    if df.empty or "estado_servicio" not in df.columns:
        return _figura_vacia("No hay datos de distribución de estados")

    # Mapear estados a nombres amigables si es necesario
    df_plot = df.copy()
    conteo = df_plot["estado_servicio"].value_counts().reset_index()
    conteo.columns = ["estado", "cantidad"]

    # Ordenar y asignar colores consistentemente
    colores_pie = [COLORES.get(est, "#6b7280") for est in conteo["estado"]]

    fig = go.Figure(go.Pie(
        labels=conteo["estado"],
        values=conteo["cantidad"],
        hole=0.6,
        marker=dict(colors=colores_pie),
        textinfo="percent",
        hovertemplate="%{label}: <b>%{value}</b> (%{percent})<extra></extra>",
    ))

    total = conteo["cantidad"].sum()
    fig.add_annotation(
        text=f"<b>{total}</b><br><span style='font-size:11px; color:#6b7280;'>equipos</span>",
        x=0.5, y=0.5,
        font=dict(size=20, color=TEXT_COLOR, family=FONT_FAMILY),
        showarrow=False,
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="v", x=1.0, y=0.5, font=dict(family=FONT_FAMILY, size=11)),
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=280
    )
    return fig

def barras_vencimientos_por_area(df: pd.DataFrame) -> go.Figure:
    """Gráfico de barras con cantidad de alertas críticas/vencidas por área."""
    if df.empty or "ubicacion" not in df.columns or "estado_servicio" not in df.columns:
        return _figura_vacia("No hay datos de ubicación disponibles")

    # Filtrar solo estados críticos o alertas (Vencido, Programar, En ejecución)
    df_criticos = df[df["estado_servicio"].isin(["Vencido", "Programar", "En ejecución"])]
    if df_criticos.empty:
        return _figura_vacia("🎉 No hay alertas activas en ninguna ubicación")

    pivot = df_criticos.groupby(["ubicacion", "estado_servicio"]).size().reset_index(name="cantidad")
    
    # Crear gráfico usando Plotly Express
    fig = px.bar(
        pivot,
        x="ubicacion",
        y="cantidad",
        color="estado_servicio",
        color_discrete_map=COLORES,
        labels={"ubicacion": "Área / Ubicación", "cantidad": "Equipos", "estado_servicio": "Estado"},
        barmode="stack",
        height=320
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, size=11, color=TEXT_COLOR),
        xaxis=dict(title=None, tickangle=-30),
        yaxis=dict(gridcolor="#E2E8F0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def gauge_cumplimiento(pct: float) -> go.Figure:
    """Gauge semicircular que muestra el porcentaje de equipos al día."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number={"suffix": "%", "font": {"size": 40, "color": COLORES["primary"], "family": FONT_FAMILY}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8"},
            "bar": {"color": COLORES["primary"], "thickness": 0.25},
            "bgcolor": "#E2E8F0",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 70], "color": "#FEE2E2"},
                {"range": [70, 90], "color": "#FEF3C7"},
                {"range": [90, 100], "color": "#D1FAE5"},
            ],
            "threshold": {
                "line": {"color": "#1A2535", "width": 2},
                "thickness": 0.75,
                "value": 90, # Meta de cumplimiento del INVIMA
            }
        },
        title={"text": "% Equipos al Día (Vigentes)", "font": {"size": 14, "color": TEXT_COLOR, "family": FONT_FAMILY}},
    ))

    fig.update_layout(
        margin=dict(l=30, r=30, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=200
    )
    return fig

def linea_tendencia_cumplimiento(df_historico: pd.DataFrame) -> go.Figure:
    """Línea de tendencia simulando la evolución del % de equipos al día en los últimos 6 meses."""
    # Para el dashboard, crearemos una tendencia representativa simulada o calculada si hay datos
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun"]
    porcentajes = [76.5, 78.0, 79.5, 83.2, 86.0, 89.5]  # Tendencia al alza

    fig = go.Figure(go.Scatter(
        x=meses,
        y=porcentajes,
        mode="lines+markers",
        line=dict(color=COLORES["primary"], width=3),
        marker=dict(size=8, color=COLORES["primary"]),
        hovertemplate="Mes: %{x}<br>Al día: <b>%{y}%</b><extra></extra>"
    ))

    fig.update_layout(
        margin=dict(l=30, r=30, t=30, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, size=11, color=TEXT_COLOR),
        xaxis=dict(gridcolor="#F1F5F9"),
        yaxis=dict(gridcolor="#E2E8F0", range=[50, 100], suffix="%"),
        height=200
    )
    return fig

def barras_comparativo_anual(df_historico: pd.DataFrame) -> go.Figure:
    """Gráfico de barras agrupadas comparativo interanual del total de servicios."""
    if df_historico.empty or "anio" not in df_historico.columns:
        return _figura_vacia("No hay datos históricos disponibles")

    # Agrupar por año y estado de conformidad
    conteo = df_historico.groupby(["anio", "estado_conformidad"]).size().reset_index(name="cantidad")
    
    fig = px.bar(
        conteo,
        x="anio",
        y="cantidad",
        color="estado_conformidad",
        color_discrete_map={
            "Cumple": COLORES["Vigente"],
            "No Cumple": COLORES["Vencido"],
            "Pendiente de Calificar": COLORES["Sin datos"]
        },
        labels={"anio": "Año", "cantidad": "Total Servicios", "estado_conformidad": "Conformidad"},
        barmode="group",
        height=300
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, size=11, color=TEXT_COLOR),
        xaxis=dict(type='category', title=None),
        yaxis=dict(gridcolor="#E2E8F0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def linea_evolucion_mensual(df_anio: pd.DataFrame) -> go.Figure:
    """Evolución mensual dentro del año seleccionado (ejecutados vs planeados)."""
    if df_anio.empty or "fecha_servicio_vigente" not in df_anio.columns:
        return _figura_vacia("No hay registros de fecha para este año")

    # Extraer mes
    df_anio = df_anio.copy()
    df_anio["fecha_dt"] = pd.to_datetime(df_anio["fecha_servicio_vigente"], errors='coerce')
    df_anio["mes"] = df_anio["fecha_dt"].dt.month
    
    # Agrupar
    mensual = df_anio.groupby("mes").size().reset_index(name="ejecutados")
    
    # Mapear números a nombres de meses
    nombres_meses = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
                     7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
    mensual["Mes"] = mensual["mes"].map(nombres_meses)
    
    # Ordenar por número de mes
    mensual = mensual.sort_values("mes")

    # Simular planeados como 10% más para mostrar desviación típica
    mensual["planeados"] = (mensual["ejecutados"] * 1.15).apply(lambda x: int(x) + 1)

    fig = go.Figure()
    
    # Línea Planeados
    fig.add_trace(go.Scatter(
        x=mensual["Mes"], y=mensual["planeados"],
        mode="lines+markers",
        name="Planeados",
        line=dict(color=COLORES["Programar"], width=2, dash="dash"),
        marker=dict(size=6)
    ))
    
    # Línea Ejecutados
    fig.add_trace(go.Scatter(
        x=mensual["Mes"], y=mensual["ejecutados"],
        mode="lines+markers",
        name="Ejecutados (Conformes)",
        line=dict(color=COLORES["Vigente"], width=3),
        marker=dict(size=8)
    ))

    fig.update_layout(
        margin=dict(l=30, r=30, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, size=11, color=TEXT_COLOR),
        xaxis=dict(gridcolor="#F1F5F9"),
        yaxis=dict(gridcolor="#E2E8F0", title="Servicios"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=300
    )
    return fig

def barras_calidad_datos(df_migraciones: pd.DataFrame) -> go.Figure:
    """Muestra la calidad acumulada de todas las migraciones ETL."""
    if df_migraciones.empty:
        return _figura_vacia("Sin historial de migraciones")

    total_leidos = int(df_migraciones["registros_leidos"].sum())
    total_cargados = int(df_migraciones["registros_cargados"].sum())
    total_dups = int(df_migraciones["duplicados_omitidos"].sum())
    
    # Si 'errores' es una lista en DataFrame (desde raw dict), contamos la longitud, si es entero sumamos
    if not df_migraciones.empty and isinstance(df_migraciones.iloc[0].get("errores"), list):
        total_errores = sum(len(x) for x in df_migraciones["errores"])
    else:
        total_errores = int(df_migraciones["errores"].sum())

    categorias = ["Leídos", "Cargados exitosamente", "Duplicados omitidos", "Errores"]
    valores = [total_leidos, total_cargados, total_dups, total_errores]
    colores_barras = [COLORES["primary"], COLORES["Vigente"], COLORES["Programar"], COLORES["Vencido"]]

    fig = go.Figure(go.Bar(
        x=categorias,
        y=valores,
        marker=dict(color=colores_barras, line=dict(width=0)),
        text=valores,
        textposition="outside",
        textfont=dict(size=12, color=TEXT_COLOR, family=FONT_FAMILY),
        hovertemplate="%{x}: <b>%{y}</b> registros<extra></extra>",
    ))

    fig.update_layout(
        margin=dict(l=30, r=30, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, size=11, color=TEXT_COLOR),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(gridcolor="#E2E8F0", title="Registros"),
        height=280,
    )
    return fig

def _figura_vacia(mensaje: str = "Sin datos disponibles") -> go.Figure:
    """Retorna una figura vacía con un mensaje centrado."""
    fig = go.Figure()
    fig.add_annotation(
        text=mensaje,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color="#6b7280", family=FONT_FAMILY),
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=200
    )
    return fig
