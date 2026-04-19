"""
scheduler/engine.py
──────────────────────────────────────────────────────────────────────────────
Motor de cronograma: lee todos los servicios de Supabase, calcula la fecha
del próximo servicio, los días restantes y el estado de alerta de cada equipo.
Escribe los resultados en la columna fecha_proximo_servicio, dias_restantes
y estado_alerta de la tabla 'servicios'.

Reglas de clasificación de alertas:
  VENCIDO  → dias_restantes < 0
  CRITICO  → 0 ≤ dias_restantes ≤ 15
  PROXIMO  → 16 ≤ dias_restantes ≤ 30
  AL_DIA   → dias_restantes > 30
  SIN_DATOS → sin fecha_servicio_vigente o sin frecuencia_dias
──────────────────────────────────────────────────────────────────────────────
"""

import math
from datetime import date, timedelta

from rich.console import Console
from rich.table import Table as RichTable

from db.client import get_client
from scheduler.frequency_parser import frecuencia_a_dias

console = Console()

# Umbrales de alerta en días
UMBRAL_CRITICO = 15
UMBRAL_PROXIMO = 30


def _clasificar_alerta(dias: int | None) -> str:
    """Clasifica el estado de alerta según los días restantes."""
    if dias is None:
        return "SIN_DATOS"
    if dias < 0:
        return "VENCIDO"
    if dias <= UMBRAL_CRITICO:
        return "CRITICO"
    if dias <= UMBRAL_PROXIMO:
        return "PROXIMO"
    return "AL_DIA"


def calcular_fecha_proximo(fecha_vigente: str | None, frecuencia_dias: int | None) -> date | None:
    """
    Calcula la fecha del próximo servicio.

    Parámetros
    ----------
    fecha_vigente : str | None
        Fecha del último servicio en formato ISO "YYYY-MM-DD".
    frecuencia_dias : int | None
        Número de días de la frecuencia de servicio.

    Retorna
    -------
    date | None
    """
    if not fecha_vigente or not frecuencia_dias:
        return None
    try:
        d = date.fromisoformat(str(fecha_vigente))
        return d + timedelta(days=frecuencia_dias)
    except (ValueError, TypeError):
        return None


def ejecutar(verbose: bool = True) -> dict:
    """
    Ejecuta el motor de cronograma completo:
      1. Lee todos los servicios de Supabase
      2. Calcula fecha_proximo_servicio y dias_restantes
      3. Clasifica estado_alerta
      4. Actualiza cada registro en Supabase
      5. Retorna un resumen de métricas

    Parámetros
    ----------
    verbose : bool
        Si True, imprime tabla de resumen en consola.

    Retorna
    -------
    dict con métricas: total, al_dia, proximos, criticos, vencidos, sin_datos
    """
    cliente = get_client()
    hoy = date.today()

    console.print(f"\n[bold blue]⏰ Motor de Cronograma PAME[/bold blue] — {hoy.isoformat()}")

    # ── 1. Leer todos los servicios ────────────────────────────────────────────
    respuesta = cliente.table("servicios")\
        .select("id, codigo_equipo, nombre_equipo, fecha_servicio_vigente, frecuencia, frecuencia_dias")\
        .execute()

    servicios = respuesta.data or []
    console.print(f"[cyan]  📋 {len(servicios)} servicios encontrados[/cyan]")

    if not servicios:
        console.print("[yellow]  No hay servicios para procesar.[/yellow]")
        return {}

    # ── 2. Calcular y actualizar ───────────────────────────────────────────────
    metricas = {
        "total": len(servicios),
        "al_dia": 0,
        "proximos": 0,
        "criticos": 0,
        "vencidos": 0,
        "sin_datos": 0,
        "actualizados": 0,
        "errores": 0,
    }

    for srv in servicios:
        sid = srv["id"]

        # Resolver frecuencia_dias si no está guardada
        freq_dias = srv.get("frecuencia_dias")
        if not freq_dias and srv.get("frecuencia"):
            freq_dias = frecuencia_a_dias(srv["frecuencia"])

        # Calcular fecha próxima
        fecha_proximo = calcular_fecha_proximo(
            srv.get("fecha_servicio_vigente"),
            freq_dias,
        )

        # Calcular días restantes
        if fecha_proximo:
            dias_restantes = (fecha_proximo - hoy).days
        else:
            dias_restantes = None

        # Clasificar alerta
        estado_alerta = _clasificar_alerta(dias_restantes)

        # Actualizar contadores de métricas
        metricas[estado_alerta.lower()] += 1

        # ── Persistir en Supabase ──────────────────────────────────────────────
        actualizacion = {
            "frecuencia_dias": freq_dias,
            "fecha_proximo_servicio": fecha_proximo.isoformat() if fecha_proximo else None,
            "dias_restantes": dias_restantes,
            "estado_alerta": estado_alerta,
        }
        # Quitar None para no sobreescribir con null
        actualizacion = {k: v for k, v in actualizacion.items() if v is not None}

        try:
            cliente.table("servicios").update(actualizacion).eq("id", sid).execute()
            metricas["actualizados"] += 1
        except Exception as e:
            metricas["errores"] += 1
            console.print(f"[red]  ✗ Error actualizando servicio {sid}: {e}[/red]")

    # ── 3. Mostrar resumen ─────────────────────────────────────────────────────
    if verbose:
        t = RichTable(title="📅 Resumen de Cronograma PAME", show_header=True)
        t.add_column("Estado", style="bold")
        t.add_column("Cantidad", justify="right")
        t.add_column("% del total", justify="right")
        total = metricas["total"] or 1

        filas = [
            ("🟢 AL DÍA",     "al_dia",    "green"),
            ("🟡 PRÓXIMOS",   "proximos",  "yellow"),
            ("🟠 CRÍTICOS",   "criticos",  "dark_orange"),
            ("🔴 VENCIDOS",   "vencidos",  "red"),
            ("⚪ SIN DATOS",  "sin_datos", "dim"),
        ]
        for label, clave, color in filas:
            cant = metricas[clave]
            pct = f"{cant / total * 100:.1f}%"
            t.add_row(label, str(cant), pct, style=color)

        console.print(t)
        console.print(
            f"[dim]  Actualizados: {metricas['actualizados']}  |  "
            f"Errores: {metricas['errores']}[/dim]"
        )

    return metricas
