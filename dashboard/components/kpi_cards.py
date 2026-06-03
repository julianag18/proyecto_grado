"""
dashboard/components/kpi_cards.py
──────────────────────────────────────────────────────────────────────────────
Componentes reutilizables de tarjetas KPI para el Dashboard PAME.
Usa HTML/CSS inyectado via st.markdown para lograr el diseño glassmorphism.
──────────────────────────────────────────────────────────────────────────────
"""

import streamlit as st


# ── Mapa de configuración visual por tipo de KPI ──────────────────────────────

_CONFIG_KPI = {
    "total": {
        "clase":  "total",
        "icono":  "🔬",
        "label":  "TOTAL EQUIPOS",
        "sub":    "En inventario PAME",
    },
    "al_dia": {
        "clase":  "al-dia",
        "icono":  "✅",
        "label":  "AL DÍA",
        "sub":    "Calibración vigente",
    },
    "proximos": {
        "clase":  "proximo",
        "icono":  "🟡",
        "label":  "PRÓXIMOS A VENCER",
        "sub":    "Vencen en ≤ 30 días",
    },
    "criticos": {
        "clase":  "critico",
        "icono":  "🟠",
        "label":  "CRÍTICOS",
        "sub":    "Vencen en ≤ 15 días",
    },
    "vencidos": {
        "clase":  "vencido",
        "icono":  "🔴",
        "label":  "VENCIDOS",
        "sub":    "Requieren acción inmediata",
    },
    "sin_datos": {
        "clase":  "sin-datos",
        "icono":  "⚪",
        "label":  "SIN HISTORIAL",
        "sub":    "Sin datos de calibración",
    },
}


def render_kpi_card(tipo: str, valor: int, pct: float | None = None) -> None:
    """
    Renderiza una tarjeta KPI con HTML/CSS personalizado.

    Parámetros
    ----------
    tipo : str
        Clave del KPI: 'total', 'al_dia', 'proximos', 'criticos', 'vencidos', 'sin_datos'
    valor : int
        Valor numérico a mostrar.
    pct : float | None
        Porcentaje opcional a mostrar como subtítulo adicional (ej: 75.3 → "75.3%").
    """
    cfg = _CONFIG_KPI.get(tipo, {
        "clase": "total", "icono": "📊", "label": tipo.upper(), "sub": "",
    })

    pct_html = f'<div class="kpi-sub">{pct:.1f}% del total</div>' if pct is not None else ""

    html = f"""
    <div class="kpi-card {cfg['clase']}">
      <span class="kpi-icon">{cfg['icono']}</span>
      <div class="kpi-label">{cfg['label']}</div>
      <div class="kpi-number">{valor}</div>
      <div class="kpi-sub">{cfg['sub']}</div>
      {pct_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_fila_kpis(kpis: dict) -> None:
    """
    Renderiza la fila completa de 6 tarjetas KPI usando columnas de Streamlit.

    Parámetros
    ----------
    kpis : dict
        Resultado de data_loader.calcular_kpis()
    """
    total = kpis.get("total", 0)

    def pct(valor: int) -> float | None:
        return round(100 * valor / total, 1) if total > 0 else None

    cols = st.columns(6, gap="small")

    with cols[0]:
        render_kpi_card("total", kpis["total"])

    with cols[1]:
        render_kpi_card("al_dia", kpis["al_dia"], pct(kpis["al_dia"]))

    with cols[2]:
        render_kpi_card("proximos", kpis["proximos"], pct(kpis["proximos"]))

    with cols[3]:
        render_kpi_card("criticos", kpis["criticos"], pct(kpis["criticos"]))

    with cols[4]:
        render_kpi_card("vencidos", kpis["vencidos"], pct(kpis["vencidos"]))

    with cols[5]:
        render_kpi_card("sin_datos", kpis["sin_datos"], pct(kpis["sin_datos"]))


def render_badge_alerta(estado: str) -> str:
    """
    Retorna HTML de un badge de estado de alerta.

    Parámetros
    ----------
    estado : str
        'AL_DIA', 'PROXIMO', 'CRITICO', 'VENCIDO', 'SIN_DATOS'

    Returns
    -------
    str HTML del badge
    """
    mapa = {
        "AL_DIA":    ("badge-al-dia",    "✅ AL DÍA"),
        "PROXIMO":   ("badge-proximo",   "🟡 PRÓXIMO"),
        "CRITICO":   ("badge-critico",   "🟠 CRÍTICO"),
        "VENCIDO":   ("badge-vencido",   "🔴 VENCIDO"),
        "SIN_DATOS": ("badge-sin-datos", "⚪ SIN DATOS"),
    }
    clase, texto = mapa.get(estado, ("badge-sin-datos", estado))
    return f'<span class="badge {clase}">{texto}</span>'


def render_section_header(titulo: str, descripcion: str = "") -> None:
    """Renderiza un encabezado de sección con borde izquierdo azul."""
    desc_html = f'<p>{descripcion}</p>' if descripcion else ""
    st.markdown(
        f"""
        <div class="section-header">
          <h2>{titulo}</h2>
          {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_banner_demo() -> None:
    """Muestra un banner informativo cuando el dashboard está en modo demo."""
    st.info(
        "**Modo demostración** — Los datos mostrados son sintéticos y representativos. "
        "Configure `FIREBASE_CREDENTIALS_PATH` en el archivo `.env` para "
        "conectar con la base de datos real del PAME.",
        icon="🧪",
    )


def render_metric_mini(label: str, valor, delta=None, delta_color: str = "normal") -> None:
    """
    Wrapper ligero sobre st.metric para uso en sidebars o resúmenes compactos.
    """
    st.metric(label=label, value=valor, delta=delta, delta_color=delta_color)


def get_logo_base64() -> str:
    """Retorna la imagen del logo en base64 para inyección HTML."""
    import base64
    from pathlib import Path
    logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
    if logo_path.exists():
        try:
            return base64.b64encode(logo_path.read_bytes()).decode("utf-8")
        except Exception:
            pass
    return ""


def render_sidebar_logo() -> None:
    """Renderiza el logo y branding de Laboratorios Laproff en el sidebar."""
    logo_b64 = get_logo_base64()
    if logo_b64:
        logo_html = f'<img class="logo-img" src="data:image/png;base64,{logo_b64}" alt="Laboratorios Laproff" />'
    else:
        logo_html = '<div style="font-size:2.5rem; margin-bottom:0.4rem;">🔬</div>'

    st.markdown(
        f"""
        <div class="s-logo">
          <div class="logo-row">
            {logo_html}
          </div>
          <div style="font-weight:800; font-size:1.15rem; color:#ffffff; letter-spacing:0.05em; margin-top:0.2rem;">
            PAME
          </div>
          <div style="font-size:0.78rem; color:rgba(255,255,255,0.6); margin-top:0.1rem; text-align:center;">
            Laboratorios Laproff S.A.S.
          </div>
          <div class="module-pill">
            <div class="mpill-dot"></div>
            <div class="mpill-txt">Módulo Metrológico</div>
          </div>
        </div>
        <hr style="border:none; border-top:1px solid rgba(255,255,255,0.07); margin:0 0 1rem 0;">
        """,
        unsafe_allow_html=True,
    )


def render_index_error_banner(error) -> None:
    """Muestra un banner amigable cuando Firestore requiere la creación manual de un índice."""
    url = getattr(error, "index_url", None)
    url_html = ""
    if url:
        url_html = f"""
        <p style="margin-top: 0.75rem;">
          <a href="{url}" target="_blank" class="btn-pri" style="text-decoration: none; display: inline-block; padding: 8px 16px; width: auto; font-size: 0.82rem; color: white !important;">
            🛠️ Crear índice en Firebase Console
          </a>
        </p>
        """
    st.markdown(
        f"""
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 12px; padding: 1.25rem; margin: 1rem 0; color: #991B1B;">
          <h4 style="margin: 0 0 0.5rem 0; color: #7F1D1D; display: flex; align-items: center; gap: 0.5rem;">
            ⚠️ Falta Configurar un Índice en Firestore
          </h4>
          <p style="margin: 0; font-size: 0.85rem; line-height: 1.5; color: #4B5D72;">
            La base de datos Firestore requiere un índice de grupo de colecciones para realizar esta consulta. 
            Como administrador del sistema, puedes crearlo haciendo clic en el siguiente enlace de forma automática.
          </p>
          {url_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


