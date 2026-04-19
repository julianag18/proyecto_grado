"""
scripts/run_etl.py
──────────────────────────────────────────────────────────────────────────────
CLI para ejecutar el pipeline ETL completo desde la línea de comandos.

Uso:
  python scripts/run_etl.py inventario data/inventario.xlsx
  python scripts/run_etl.py servicios data/cronograma.xlsx --hoja "Cronograma"
  python scripts/run_etl.py inventario data/equipos.csv
──────────────────────────────────────────────────────────────────────────────
"""

import sys
from pathlib import Path

import typer
from rich.console import Console

# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from etl.extractor import leer_archivo
from etl.transformer import transformar_inventario, transformar_servicios
from etl.validator import validar_inventario, validar_servicios
from etl.loader import cargar_proveedores, cargar_equipos, cargar_servicios
from etl.migration_log import registrar_migracion

app = typer.Typer(help="ETL pipeline del módulo complementario PAME")
console = Console()


@app.command()
def ejecutar(
    tipo: str = typer.Argument(..., help="Tipo de datos: 'inventario' o 'servicios'"),
    archivo: Path = typer.Argument(..., help="Ruta al archivo Excel o CSV"),
    hoja: str = typer.Option("0", "--hoja", "-h", help="Nombre o índice de la hoja Excel"),
):
    """
    Ejecuta el pipeline ETL completo para el archivo especificado.
    Extrae → Transforma → Valida → Carga → Registra migración.
    """
    console.rule(f"[bold]🚀 ETL PAME — {tipo.upper()}[/bold]")

    # ── Parsear hoja ──────────────────────────────────────────────────────────
    hoja_parsed: int | str = int(hoja) if hoja.isdigit() else hoja

    # ── 1. Extracción ─────────────────────────────────────────────────────────
    try:
        df_crudo = leer_archivo(archivo, tipo, hoja=hoja_parsed)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]✗ Error de extracción: {e}[/red]")
        raise typer.Exit(code=1)

    # ── 2. Transformación ─────────────────────────────────────────────────────
    if tipo == "inventario":
        resultado_transform = transformar_inventario(df_crudo)
    elif tipo == "servicios":
        resultado_transform = transformar_servicios(df_crudo)
    else:
        console.print(f"[red]✗ Tipo inválido: '{tipo}'. Use 'inventario' o 'servicios'[/red]")
        raise typer.Exit(code=1)

    # ── 3. Validación ─────────────────────────────────────────────────────────
    if tipo == "inventario":
        df_valido, df_invalido = validar_inventario(resultado_transform.df_limpio)
    else:
        df_valido, df_invalido = validar_servicios(resultado_transform.df_limpio)

    errores_totales = resultado_transform.total_rechazados + len(df_invalido)

    # ── 4. Guardar rechazos en archivo para revisión ───────────────────────────
    if not resultado_transform.df_rechazos.empty:
        ruta_rechazos = archivo.parent / f"rechazos_{archivo.stem}.xlsx"
        resultado_transform.df_rechazos.to_excel(ruta_rechazos, index=False)
        console.print(f"[yellow]  ⚠ Rechazos guardados en: {ruta_rechazos}[/yellow]")

    if not df_invalido.empty:
        ruta_invalidos = archivo.parent / f"invalidos_{archivo.stem}.xlsx"
        df_invalido.to_excel(ruta_invalidos, index=False)
        console.print(f"[yellow]  ⚠ Inválidos de validación guardados en: {ruta_invalidos}[/yellow]")

    # ── 5. Carga ──────────────────────────────────────────────────────────────
    resultado_carga_eq = None
    resultado_carga_srv = None
    migracion_id = None

    # Registrar migración ANTES de cargar para obtener el ID
    estado_migration = "completado" if errores_totales == 0 else (
        "parcial" if len(df_valido) > 0 else "fallido"
    )
    migracion_id = registrar_migracion(
        nombre_archivo=archivo.name,
        tipo=tipo,
        registros_leidos=resultado_transform.total_leidos,
        registros_cargados=len(df_valido),
        duplicados_omitidos=resultado_transform.total_duplicados,
        errores=errores_totales,
        estado=estado_migration,
    )

    if len(df_valido) > 0:
        if tipo == "inventario":
            cargar_proveedores(df_valido)
            resultado_carga_eq = cargar_equipos(df_valido, migracion_id=migracion_id)
        else:
            resultado_carga_srv = cargar_servicios(df_valido, migracion_id=migracion_id)

    # ── Resumen final ─────────────────────────────────────────────────────────
    console.rule("[bold green]✅ ETL Finalizado[/bold green]")
    console.print(f"  Archivo procesado : {archivo.name}")
    console.print(f"  Registros leídos  : {resultado_transform.total_leidos}")
    console.print(f"  Cargados          : {len(df_valido)}")
    console.print(f"  Duplicados        : {resultado_transform.total_duplicados}")
    console.print(f"  Errores           : {errores_totales}")
    console.print(f"  Estado migración  : {estado_migration.upper()}")
    if migracion_id:
        console.print(f"  ID migración      : {migracion_id}")


if __name__ == "__main__":
    app()
