"""
dashboard/components/charts.py
──────────────────────────────────────────────────────────────────────────────
Funciones de gráficos Plotly para el Dashboard PAME.
Todos los gráficos usan un tema oscuro consistente con la paleta de colores
definida en style.css.
──────────────────────────────────────────────────────────────────────────────
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ── Paleta de colores del PAME (espejo de style.css) ──────────────────────────
COLORES = {
    "AL_DIA":    "#10B981", # Emerald green
    "PROXIMO":   "#F59E0B", # Amber
    "CRITICO":   "#EF4444", # Red
    "VENCIDO":   "#DC2626", # Crimson
    "SIN_DATOS": "#94A3B8", # Slate
}

BG_CHART     = "rgba(0,0,0,0)"          # Fondo transparente
GRID_COLOR   = "#E2ECF5"
TEXT_COLOR   = "#4B5D72"
FONT_FAMILY  = "Plus Jakarta Sans, sans-serif"

_LAYOUT_BASE = dict(
    paper_bgcolor=BG_CHART,
    plot_bgcolor=BG_CHART,
    font=dict(family=FONT_FAMILY, color=TEXT_COLOR, size=12),
    margin=dict(l=16, r=16, t=40, b=16),
    legend=dict(
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#E2ECF5",
        borderwidth=1,
        font=dict(size=11),
    ),
)


def _aplicar_layout(fig: go.Figure, **kwargs) -> go.Figure:
    """Aplica el layout base a una figura y acepta overrides."""
    layout = {**_LAYOUT_BASE, **kwargs}
    fig.update_layout(**layout)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 1. Gauge de cumplimiento (% AL DÍA)
# ══════════════════════════════════════════════════════════════════════════════

def gauge_cumplimiento(pct: float) -> go.Figure:
    """
    Gauge semicircular que muestra el % de equipos AL DÍA.

    Parámetros
    ----------
    pct : float
        Porcentaje de equipos al día (0–100).
    """
    # Color del indicador según umbral
    if pct >= 80:
        color_aguja = COLORES["AL_DIA"]
    elif pct >= 60:
        color_aguja = COLORES["PROXIMO"]
    elif pct >= 40:
        color_aguja = COLORES["CRITICO"]
    else:
        color_aguja = COLORES["VENCIDO"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct,
        number={"suffix": "%", "font": {"size": 36, "color": color_aguja, "family": FONT_FAMILY}},
        delta={
            "reference": 80,
            "valueformat": ".1f",
            "suffix": "% vs meta 80%",
            "font": {"size": 11},
        },
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": GRID_COLOR,
                "tickfont": {"color": TEXT_COLOR, "size": 10},
            },
            "bar": {"color": color_aguja, "thickness": 0.25},
            "bgcolor": "rgba(240,245,250,0.8)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  40], "color": "rgba(220,38,38,0.15)"},
                {"range": [40, 60], "color": "rgba(245,158,11,0.12)"},
                {"range": [60, 80], "color": "rgba(245,158,11,0.12)"},
                {"range": [80, 100],"color": "rgba(16,185,129,0.12)"},
            ],
            "threshold": {
                "line": {"color": "#1A2535", "width": 2},
                "thickness": 0.75,
                "value": 80,
            },
        },
        title={"text": "Cumplimiento del PAME", "font": {"size": 13, "color": TEXT_COLOR}},
    ))

    _aplicar_layout(fig, height=240, margin=dict(l=30, r=30, t=50, b=10))
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 2. Barras apiladas por área
# ══════════════════════════════════════════════════════════════════════════════

def barras_por_area(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras apiladas con el estado de alerta por área.

    Parámetros
    ----------
    df : pd.DataFrame
        DataFrame con columnas 'area' y 'estado_alerta'.
    """
    if df.empty or "area" not in df.columns or "estado_alerta" not in df.columns:
        return _figura_vacia("Sin datos de área disponibles")

    orden_estados = ["AL_DIA", "PROXIMO", "CRITICO", "VENCIDO", "SIN_DATOS"]
    etiquetas = {
        "AL_DIA":    "Al día",
        "PROXIMO":   "Próximos",
        "CRITICO":   "Críticos",
        "VENCIDO":   "Vencidos",
        "SIN_DATOS": "Sin datos",
    }

    pivot = (
        df.groupby(["area", "estado_alerta"])
        .size()
        .reset_index(name="count")
        .pivot(index="area", columns="estado_alerta", values="count")
        .fillna(0)
        .reindex(columns=orden_estados, fill_value=0)
    )

    fig = go.Figure()
    for estado in orden_estados:
        if estado not in pivot.columns:
            continue
        fig.add_trace(go.Bar(
            name=etiquetas.get(estado, estado),
            x=pivot.index.tolist(),
            y=pivot[estado].tolist(),
            marker_color=COLORES[estado],
            marker_line_width=0,
            hovertemplate="%{x}<br>%{fullData.name}: <b>%{y}</b><extra></extra>",
        ))

    return _aplicar_layout(
        fig,
        barmode="stack",
        xaxis=dict(
            title="Área",
            gridcolor=GRID_COLOR,
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            title="Número de equipos",
            gridcolor=GRID_COLOR,
        ),
        title=dict(text="Estado de alertas por área", font=dict(size=13, color=TEXT_COLOR)),
        height=320,
        margin=dict(l=40, r=16, t=50, b=50),
    )


# ══════════════════════════════════════════════════════════════════════════════
# 3. Donut por estado de alerta global
# ══════════════════════════════════════════════════════════════════════════════

def donut_estado_global(kpis: dict) -> go.Figure:
    """
    Donut chart con la distribución global de estados de alerta.

    Parámetros
    ----------
    kpis : dict
        Resultado de data_loader.calcular_kpis()
    """
    labels = ["Al día", "Próximos", "Críticos", "Vencidos", "Sin datos"]
    valores = [
        kpis.get("al_dia", 0),
        kpis.get("proximos", 0),
        kpis.get("criticos", 0),
        kpis.get("vencidos", 0),
        kpis.get("sin_datos", 0),
    ]
    colores = [
        COLORES["AL_DIA"], COLORES["PROXIMO"],
        COLORES["CRITICO"], COLORES["VENCIDO"], COLORES["SIN_DATOS"],
    ]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=valores,
        hole=0.62,
        marker=dict(colors=colores, line=dict(color="rgba(0,0,0,0)", width=0)),
        textinfo="percent",
        textfont=dict(size=11, color="#ffffff"),
        hovertemplate="%{label}: <b>%{value}</b> (%{percent})<extra></extra>",
        pull=[0.03 if v == max(valores) and v > 0 else 0 for v in valores],
    ))

    # Anotación central
    total = sum(valores)
    fig.add_annotation(
        text=f"<b>{total}</b><br><span style='font-size:10px'>equipos</span>",
        x=0.5, y=0.5,
        font=dict(size=18, color="#1A2535", family=FONT_FAMILY),
        showarrow=False,
    )

    _aplicar_layout(
        fig,
        title=dict(text="Distribución global", font=dict(size=13, color=TEXT_COLOR)),
        showlegend=True,
        legend=dict(orientation="v", x=1.0, y=0.5, **_LAYOUT_BASE["legend"]),
        height=280,
        margin=dict(l=0, r=120, t=50, b=10),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 4. Barras por tipo de servicio
# ══════════════════════════════════════════════════════════════════════════════

def barras_tipo_servicio(df: pd.DataFrame) -> go.Figure:
    """Distribución de equipos por tipo de servicio (horizontal)."""
    if df.empty or "tipo_servicio" not in df.columns:
        return _figura_vacia("Sin datos de tipo de servicio")

    conteo = df["tipo_servicio"].dropna().value_counts().reset_index()
    conteo.columns = ["tipo", "total"]

    colores_tipo = ["#00A99D", "#008F84", "#006B63", "#6EDDD7"]

    fig = go.Figure(go.Bar(
        x=conteo["total"].tolist(),
        y=conteo["tipo"].tolist(),
        orientation="h",
        marker=dict(
            color=colores_tipo[:len(conteo)],
            line=dict(width=0),
        ),
        text=conteo["total"].tolist(),
        textposition="outside",
        textfont=dict(size=11, color="#1A2535"),
        hovertemplate="%{y}: <b>%{x}</b> equipos<extra></extra>",
    ))

    return _aplicar_layout(
        fig,
        title=dict(text="Por tipo de servicio", font=dict(size=13, color=TEXT_COLOR)),
        xaxis=dict(gridcolor=GRID_COLOR, title="Cantidad"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        height=220,
        margin=dict(l=16, r=50, t=50, b=16),
    )


# ══════════════════════════════════════════════════════════════════════════════
# 5. Timeline de próximos vencimientos
# ══════════════════════════════════════════════════════════════════════════════

def timeline_vencimientos(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """
    Gráfico de barras horizontales con los próximos vencimientos ordenados.

    Parámetros
    ----------
    df : pd.DataFrame
        DataFrame completo de estado PAME.
    top_n : int
        Número de equipos a mostrar.
    """
    if df.empty:
        return _figura_vacia("Sin datos de vencimientos")

    # Filtrar equipos con fecha próxima y ordenar por días restantes
    df_filtrado = (
        df[df["estado_alerta"].isin(["PROXIMO", "CRITICO", "VENCIDO"])]
        .dropna(subset=["dias_restantes"])
        .sort_values("dias_restantes")
        .head(top_n)
    )

    if df_filtrado.empty:
        return _figura_vacia("No hay vencimientos próximos")

    etiquetas = [
        f"{row['codigo_equipo']} — {str(row['nombre'])[:30]}"
        for _, row in df_filtrado.iterrows()
    ]
    dias = df_filtrado["dias_restantes"].tolist()
    estados = df_filtrado["estado_alerta"].tolist()
    colores_barras = [COLORES.get(e, "#6b7280") for e in estados]

    fig = go.Figure(go.Bar(
        x=dias,
        y=etiquetas,
        orientation="h",
        marker=dict(color=colores_barras, line=dict(width=0)),
        text=[f"{d}d" for d in dias],
        textposition="outside",
        textfont=dict(size=10, color="#1A2535"),
        hovertemplate="%{y}<br>Días restantes: <b>%{x}</b><extra></extra>",
    ))

    # Línea vertical en 0 (hoy)
    fig.add_vline(x=0, line=dict(color="rgba(26,37,53,0.3)", width=1, dash="dash"))

    return _aplicar_layout(
        fig,
        title=dict(text="Próximos vencimientos", font=dict(size=13, color=TEXT_COLOR)),
        xaxis=dict(gridcolor=GRID_COLOR, title="Días restantes"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", autorange="reversed"),
        height=max(280, top_n * 28),
        margin=dict(l=16, r=60, t=50, b=30),
    )


# ══════════════════════════════════════════════════════════════════════════════
# 6. Métricas de calidad de datos ETL
# ══════════════════════════════════════════════════════════════════════════════

def barras_calidad_datos(df_migraciones: pd.DataFrame) -> go.Figure:
    """
    Muestra la calidad acumulada de todas las migraciones ETL.

    Parámetros
    ----------
    df_migraciones : pd.DataFrame
        DataFrame de la tabla migraciones.
    """
    if df_migraciones.empty:
        return _figura_vacia("Sin historial de migraciones")

    total_leidos    = int(df_migraciones["registros_leidos"].sum())
    total_cargados  = int(df_migraciones["registros_cargados"].sum())
    total_dups      = int(df_migraciones["duplicados_omitidos"].sum())
    total_errores   = int(df_migraciones["errores"].sum())

    categorias = ["Leídos", "Cargados exitosamente", "Duplicados omitidos", "Errores"]
    valores = [total_leidos, total_cargados, total_dups, total_errores]
    colores_barras = ["#00A99D", COLORES["AL_DIA"], COLORES["PROXIMO"], COLORES["VENCIDO"]]

    fig = go.Figure(go.Bar(
        x=categorias,
        y=valores,
        marker=dict(color=colores_barras, line=dict(width=0)),
        text=valores,
        textposition="outside",
        textfont=dict(size=13, color="#1A2535"),
        hovertemplate="%{x}: <b>%{y}</b> registros<extra></extra>",
    ))

    return _aplicar_layout(
        fig,
        title=dict(text="Métricas acumuladas de migración ETL", font=dict(size=13, color=TEXT_COLOR)),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(gridcolor=GRID_COLOR, title="Registros"),
        height=280,
        margin=dict(l=40, r=16, t=50, b=16),
    )


# ══════════════════════════════════════════════════════════════════════════════
# Figura vacía (fallback)
# ══════════════════════════════════════════════════════════════════════════════

def _figura_vacia(mensaje: str = "Sin datos disponibles") -> go.Figure:
    """Retorna una figura con un mensaje centrado cuando no hay datos."""
    fig = go.Figure()
    fig.add_annotation(
        text=mensaje,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color=TEXT_COLOR, family=FONT_FAMILY),
    )
    _aplicar_layout(fig, height=240)
    return fig
