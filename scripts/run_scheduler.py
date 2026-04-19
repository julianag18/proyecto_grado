"""
scripts/run_scheduler.py
──────────────────────────────────────────────────────────────────────────────
CLI para ejecutar el motor de cronograma y el generador de alertas.

Uso:
  python scripts/run_scheduler.py            # solo calcula fechas/alertas
  python scripts/run_scheduler.py --limpiar  # regenera todas las alertas
──────────────────────────────────────────────────────────────────────────────
"""

import sys
from pathlib import Path

import typer
from rich.console import Console

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scheduler import engine, alert_generator

app = typer.Typer(help="Motor de cronograma y alertas del PAME")
console = Console()


@app.command()
def ejecutar(
    limpiar: bool = typer.Option(
        False,
        "--limpiar",
        "-l",
        help="Eliminar alertas no leídas anteriores y regenerar todas",
    ),
    solo_fechas: bool = typer.Option(
        False,
        "--solo-fechas",
        help="Calcular fechas y estados sin generar alertas",
    ),
):
    """
    Ejecuta el motor de cronograma: calcula fechas de próximo servicio,
    clasifica estados de alerta y genera registros en la tabla alertas.
    """
    console.rule("[bold]⏰ Scheduler PAME[/bold]")

    # Paso 1: Calcular fechas y estados
    metricas_engine = engine.ejecutar(verbose=True)

    if solo_fechas:
        console.print("[dim]Modo '--solo-fechas': no se generan alertas[/dim]")
        return

    # Paso 2: Generar alertas
    metricas_alertas = alert_generator.generar_alertas(limpiar_anteriores=limpiar)

    console.rule("[bold green]✅ Scheduler completado[/bold green]")


if __name__ == "__main__":
    app()
