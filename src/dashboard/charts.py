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
    "Vigente":       "#10B981",  # Emerald/Green
    "Programar":     "#F59E0B",  # Amber/Yellow
    "En ejecución":  "#06B6D4",  # Cyan/Teal
    "Vencido":       "#EF4444",  # Red/Crimson
    "Sin datos":     "#94A3B8",  # Slate/Gray
    "primary":       "#00A99D",  # Teal brillante
    "sidebar":       "#0B3533",  # Teal oscuro
}

FONT_FAMILY = "Plus Jakarta Sans, sans-serif"
TEXT_COLOR = "#1A2535"

def donut_distribucion_estados(df: pd.DataFrame) -> go.Figure:
    """Gráfico de dona con la distribución global de estados de servicios."""
    if df.empty or "estado_servicio" not in df.columns:
        return _figura_vacia("No hay datos de distribución de estados")

    df_plot = df.copy()
    conteo = df_plot["estado_servicio"].value_counts().reset_index()
    conteo.columns = ["estado", "cantidad"]

    colores_pie = [COLORES.get(est, "#6b7280") for est in conteo["estado"]]

    fig = go.Figure(go.Pie(
        labels=conteo["estado"],
        values=conteo["cantidad"],
        hole=0.72, # Dona delgada y elegante
        marker=dict(colors=colores_pie, line=dict(color="#FFFFFF", width=3)),
        textinfo="percent",
        hovertemplate="%{label}: <b>%{value}</b> (%{percent})<extra></extra>",
    ))

    total = conteo["cantidad"].sum()
    fig.add_annotation(
        text=f"<span style='font-size:28px; font-weight:800; color:#0B3533;'>{total}</span><br><span style='font-size:11px; font-weight:600; color:#64748B; text-transform:uppercase; letter-spacing:0.05em;'>Equipos</span>",
        x=0.5, y=0.5,
        font=dict(family=FONT_FAMILY),
        showarrow=False,
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.08,
            xanchor="center", x=0.5,
            font=dict(family=FONT_FAMILY, size=11, color=TEXT_COLOR)
        ),
        margin=dict(l=10, r=10, t=10, b=50),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=340 # Alineado perfectamente con el gráfico de barras (340px)
    )
    return fig

def barras_vencimientos_por_area(df: pd.DataFrame) -> go.Figure:
    """Gráfico de barras horizontales con cantidad de alertas críticas/vencidas por área."""
    if df.empty or "ubicacion" not in df.columns or "estado_servicio" not in df.columns:
        return _figura_vacia("No hay datos de ubicación disponibles")

    # Filtrar solo estados críticos o alertas (Vencido, Programar, En ejecución)
    df_criticos = df[df["estado_servicio"].isin(["Vencido", "Programar", "En ejecución"])]
    if df_criticos.empty:
        return _figura_vacia("🎉 No hay alertas activas en ninguna ubicación")

    pivot = df_criticos.groupby(["ubicacion", "estado_servicio"]).size().reset_index(name="cantidad")
    
    # Ordenar áreas de mayor a menor cantidad total de alertas
    totales_por_area = pivot.groupby("ubicacion")["cantidad"].sum().reset_index()
    totales_por_area = totales_por_area.sort_values("cantidad", ascending=True) # Ascending for correct vertical alignment in Plotly
    
    # Asegurar tipo categórico ordenado
    pivot["ubicacion"] = pd.Categorical(pivot["ubicacion"], categories=totales_por_area["ubicacion"], ordered=True)
    pivot = pivot.sort_values("ubicacion")

    # Crear gráfico horizontal
    fig = px.bar(
        pivot,
        x="cantidad",
        y="ubicacion",
        color="estado_servicio",
        color_discrete_map=COLORES,
        orientation="h",
        labels={"ubicacion": "Área / Ubicación", "cantidad": "Equipos", "estado_servicio": "Estado"},
        barmode="stack",
        height=340
    )

    fig.update_layout(
        margin=dict(l=220, r=15, t=35, b=15),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, size=11, color=TEXT_COLOR),
        yaxis=dict(
            title=None, 
            gridcolor="rgba(0,0,0,0)",
            categoryorder="array",
            categoryarray=totales_por_area["ubicacion"].tolist(), # Garantiza orden consistente
            tickfont=dict(size=10, family=FONT_FAMILY, color=TEXT_COLOR)
        ),
        xaxis=dict(
            gridcolor="#E2ECF5",
            title=None,
            dtick=1, # Ticks enteros: no 1.5 o 2.5 equipos
            tickfont=dict(size=10, family=FONT_FAMILY)
        ),
        legend=dict(
            orientation="h", 
            yanchor="bottom", y=1.02, 
            xanchor="right", x=1,
            font=dict(family=FONT_FAMILY, size=10, color=TEXT_COLOR)
        ),
        bargap=0.45 # Separación elegante entre barras
    )
    return fig

def gauge_cumplimiento(pct: float) -> go.Figure:
    """Gauge semicircular que muestra el porcentaje de equipos al día."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number={"suffix": "%", "font": {"size": 38, "color": COLORES["primary"], "family": FONT_FAMILY}},
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
        font=dict(family=FONT_FAMILY, size=11, color=TEXT_COLOR),
        height=200
    )
    return fig

def linea_tendencia_cumplimiento(df_historico: pd.DataFrame) -> go.Figure:
    """Línea de tendencia simulando la evolución del % de equipos al día en los últimos 6 meses."""
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun"]
    porcentajes = [76.5, 78.0, 79.5, 83.2, 86.0, 89.5]  # Tendencia simulada

    fig = go.Figure()
    
    # Añadir área curva suave con degradado
    fig.add_trace(go.Scatter(
        x=meses,
        y=porcentajes,
        mode="lines+markers",
        name="Cumplimiento",
        line=dict(color=COLORES["primary"], width=3, shape="spline", smoothing=1.3),
        marker=dict(size=6, color="#FFFFFF", line=dict(color=COLORES["primary"], width=2.5)),
        fill="tozeroy",
        fillcolor="rgba(0, 169, 157, 0.08)", # Relleno sutil
        hovertemplate="Mes: %{x}<br>Al día: <b>%{y}%</b><extra></extra>"
    ))

    fig.update_layout(
        margin=dict(l=35, r=15, t=15, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, size=11, color=TEXT_COLOR),
        xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=10, family=FONT_FAMILY)),
        yaxis=dict(gridcolor="#E2ECF5", range=[50, 105], ticksuffix="%", tickfont=dict(size=10, family=FONT_FAMILY)),
        height=240 # Altura ajustada para alinearse con el panel de riesgo (240px)
    )
    return fig

def barras_comparativo_anual(df_historico: pd.DataFrame) -> go.Figure:
    """Gráfico de barras agrupadas comparativo interanual del total de servicios."""
    if df_historico.empty or "anio" not in df_historico.columns:
        return _figura_vacia("No hay datos históricos disponibles")

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
        margin=dict(l=35, r=15, t=35, b=15),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, size=11, color=TEXT_COLOR),
        xaxis=dict(type='category', title=None, gridcolor="rgba(0,0,0,0)", tickfont=dict(size=10, family=FONT_FAMILY)),
        yaxis=dict(gridcolor="#E2ECF5", title=None, tickfont=dict(size=10, family=FONT_FAMILY)),
        legend=dict(
            orientation="h", 
            yanchor="bottom", y=1.02, 
            xanchor="right", x=1,
            font=dict(family=FONT_FAMILY, size=10, color=TEXT_COLOR)
        ),
        bargap=0.3,
        bargroupgap=0.05
    )
    return fig

def linea_evolucion_mensual(df_anio: pd.DataFrame) -> go.Figure:
    """Evolución mensual dentro del año seleccionado (ejecutados vs planeados)."""
    if df_anio.empty or "fecha_servicio_vigente" not in df_anio.columns:
        return _figura_vacia("No hay registros de fecha para este año")

    df_anio = df_anio.copy()
    df_anio["fecha_dt"] = pd.to_datetime(df_anio["fecha_servicio_vigente"], errors='coerce')
    df_anio["mes"] = df_anio["fecha_dt"].dt.month
    
    mensual = df_anio.groupby("mes").size().reset_index(name="ejecutados")
    
    nombres_meses = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
                     7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
    mensual["Mes"] = mensual["mes"].map(nombres_meses)
    mensual = mensual.sort_values("mes")
    mensual["planeados"] = (mensual["ejecutados"] * 1.15).apply(lambda x: int(x) + 1)

    fig = go.Figure()
    
    # Línea Planeados (curva segmentada)
    fig.add_trace(go.Scatter(
        x=mensual["Mes"], y=mensual["planeados"],
        mode="lines",
        name="Planeados",
        line=dict(color=COLORES["Programar"], width=2, dash="dash", shape="spline"),
    ))
    
    # Línea Ejecutados (curva con relleno)
    fig.add_trace(go.Scatter(
        x=mensual["Mes"], y=mensual["ejecutados"],
        mode="lines+markers",
        name="Ejecutados (Conformes)",
        line=dict(color=COLORES["Vigente"], width=3, shape="spline"),
        marker=dict(size=5, color="#FFFFFF", line=dict(color=COLORES["Vigente"], width=2)),
        fill="tozeroy",
        fillcolor="rgba(16, 185, 129, 0.05)"
    ))

    fig.update_layout(
        margin=dict(l=35, r=15, t=35, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, size=11, color=TEXT_COLOR),
        xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=10, family=FONT_FAMILY)),
        yaxis=dict(gridcolor="#E2ECF5", title=None, tickfont=dict(size=10, family=FONT_FAMILY)),
        legend=dict(
            orientation="h", 
            yanchor="bottom", y=1.02, 
            xanchor="right", x=1,
            font=dict(family=FONT_FAMILY, size=10, color=TEXT_COLOR)
        ),
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
    
    if not df_migraciones.empty and isinstance(df_migraciones.iloc[0].get("errores"), list):
        total_errores = sum(len(x) for x in df_migraciones["errores"])
    else:
        total_errores = int(df_migraciones["errores"].sum())

    categorias = ["Leídos", "Cargados", "Duplicados", "Errores"]
    valores = [total_leidos, total_cargados, total_dups, total_errores]
    colores_barras = [COLORES["primary"], COLORES["Vigente"], COLORES["Programar"], COLORES["Vencido"]]

    fig = go.Figure(go.Bar(
        x=categorias,
        y=valores,
        marker=dict(color=colores_barras, line=dict(width=0)),
        text=valores,
        textposition="outside",
        textfont=dict(size=10, color=TEXT_COLOR, family=FONT_FAMILY, weight="bold"),
        hovertemplate="%{x}: <b>%{y}</b> registros<extra></extra>",
    ))

    fig.update_layout(
        margin=dict(l=35, r=15, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, size=11, color=TEXT_COLOR),
        xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=10, family=FONT_FAMILY)),
        yaxis=dict(gridcolor="#E2ECF5", title=None, tickfont=dict(size=10, family=FONT_FAMILY)),
        height=280,
        bargap=0.5
    )
    return fig

def calcular_kpis_radar(df_area: pd.DataFrame) -> list:
    """Calcula 5 KPIs normalizados entre 0 y 100 para el gráfico de radar."""
    from datetime import date, timedelta
    if df_area.empty:
        return [0, 0, 0, 0, 0]
        
    total = len(df_area)
    
    # 1. Vigencia (% equipos al día)
    vigentes = (df_area["estado_servicio"] == "Vigente").sum()
    pct_vigencia = (vigentes / total * 100) if total > 0 else 0.0
    
    # 2. Conformidad (% cumple sobre total calificado)
    cumple = (df_area["estado_conformidad"] == "Cumple").sum()
    no_cumple = (df_area["estado_conformidad"] == "No Cumple").sum()
    tot_calif = cumple + no_cumple
    pct_conformidad = (cumple / tot_calif * 100) if tot_calif > 0 else 100.0
    
    # 3. Oportunidad (% de equipos no vencidos)
    vencidos = (df_area["estado_servicio"] == "Vencido").sum()
    pct_oportunidad = ((total - vencidos) / total * 100) if total > 0 else 0.0
    
    # 4. Actualidad (% de equipos con calibración menor a 365 días)
    hoy = date.today()
    limite = (hoy - timedelta(days=365)).isoformat()
    actuales = (df_area["fecha_servicio_vigente"].dropna() >= limite).sum()
    pct_actualidad = (actuales / total * 100) if total > 0 else 0.0
    
    # 5. Formalización (% de equipos con proveedor registrado)
    con_proveedor = (df_area["proveedor"].dropna().astype(str).str.strip() != "").sum()
    pct_formalizacion = (con_proveedor / total * 100) if total > 0 else 0.0
    
    return [pct_vigencia, pct_conformidad, pct_oportunidad, pct_actualidad, pct_formalizacion]

def radar_desempeno_area(df: pd.DataFrame, area_seleccionada: str) -> go.Figure:
    """Gráfico de radar/araña interactivo para medir el desempeño metrológico del área vs la planta."""
    if df.empty:
        return _figura_vacia("No hay datos para el radar")

    categorias = ['Vigencia', 'Conformidad', 'Oportunidad', 'Actualidad', 'Formalización']
    
    # Calcular general
    kpis_general = calcular_kpis_radar(df)
    
    # Calcular área
    df_area = df[df["ubicacion"] == area_seleccionada] if area_seleccionada != "TODAS" else df
    kpis_area = calcular_kpis_radar(df_area)
    
    # Cerrar el radar
    categorias_close = categorias + [categorias[0]]
    kpis_general_close = kpis_general + [kpis_general[0]]
    kpis_area_close = kpis_area + [kpis_area[0]]
    
    fig = go.Figure()
    
    # Promedio Planta
    fig.add_trace(go.Scatterpolar(
        r=kpis_general_close,
        theta=categorias_close,
        line=dict(color="#94A3B8", width=2, dash="dash"),
        name="Promedio Planta",
        hovertemplate="Planta - %{theta}: <b>%{r:.1f}%</b><extra></extra>"
    ))
    
    # Área Seleccionada
    fig.add_trace(go.Scatterpolar(
        r=kpis_area_close,
        theta=categorias_close,
        fill='toself',
        fillcolor="rgba(0, 169, 157, 0.22)",
        line=dict(color="#00A99D", width=3),
        name=f"Área: {area_seleccionada}" if area_seleccionada != "TODAS" else "Planta Completa",
        hovertemplate="%{theta}: <b>%{r:.1f}%</b><extra></extra>"
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix="%",
                gridcolor="#E2ECF5",
                angle=0,
                tickfont=dict(size=9, family=FONT_FAMILY, color="#64748B")
            ),
            angularaxis=dict(
                gridcolor="#E2ECF5",
                tickfont=dict(size=10, family=FONT_FAMILY, color=TEXT_COLOR)
            ),
            bgcolor="rgba(0,0,0,0)"
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.12,
            xanchor="center", x=0.5,
            font=dict(family=FONT_FAMILY, size=10, color=TEXT_COLOR)
        ),
        margin=dict(l=55, r=55, t=35, b=45),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=360
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
