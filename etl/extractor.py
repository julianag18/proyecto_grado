"""
etl/extractor.py
──────────────────────────────────────────────────────────────────────────────
Módulo de extracción: lee archivos Excel (.xlsx, .xls) y CSV y los convierte
en DataFrames crudos de pandas, aplicando el mapeo de columnas configurado
en column_mappings.yaml.
──────────────────────────────────────────────────────────────────────────────
"""

import pandas as pd
import yaml
from pathlib import Path
from rich.console import Console
from config.settings import ROOT_DIR

console = Console()

# Ruta al archivo de mapeos
MAPPINGS_PATH = ROOT_DIR / "config" / "column_mappings.yaml"


def _cargar_mappings(tipo: str) -> dict[str, list[str]]:
    """Carga el mapeo de columnas para el tipo dado ('inventario' o 'servicios')."""
    with open(MAPPINGS_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get(tipo, {})


def _aplicar_mapeo(df: pd.DataFrame, mappings: dict[str, list[str]]) -> pd.DataFrame:
    """
    Renombra las columnas del DataFrame según el mapeo.
    Si un sinónimo está en el DataFrame, se renombra al nombre canónico de BD.
    Las columnas no reconocidas se conservan con su nombre original.
    """
    rename_map: dict[str, str] = {}
    for campo_bd, sinonimos in mappings.items():
        for sinonimo in sinonimos:
            if sinonimo in df.columns:
                rename_map[sinonimo] = campo_bd
                break  # Ya encontramos el sinónimo para este campo

    if rename_map:
        console.print(
            f"[cyan]  Columnas renombradas:[/cyan] {list(rename_map.items())}"
        )

    return df.rename(columns=rename_map)


def leer_archivo(ruta: str | Path, tipo: str, hoja: int | str = 0) -> pd.DataFrame:
    """
    Lee un archivo Excel o CSV y retorna un DataFrame con columnas normalizadas.

    Parámetros
    ----------
    ruta : str | Path
        Ruta al archivo Excel (.xlsx, .xls) o CSV (.csv).
    tipo : str
        Tipo de datos a leer: 'inventario' o 'servicios'.
    hoja : int | str
        Número o nombre de la hoja de Excel (ignorado para CSV).

    Retorna
    -------
    pd.DataFrame
        DataFrame con columnas renombradas según column_mappings.yaml.

    Excepciones
    -----------
    FileNotFoundError : Si el archivo no existe.
    ValueError : Si el tipo no es 'inventario' ni 'servicios'.
    """
    ruta = Path(ruta)

    if not ruta.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {ruta}")

    if tipo not in ("inventario", "servicios"):
        raise ValueError(f"Tipo inválido '{tipo}'. Use 'inventario' o 'servicios'.")

    extension = ruta.suffix.lower()

    console.print(f"\n[bold blue]📂 Leyendo archivo:[/bold blue] {ruta.name} [dim](tipo: {tipo})[/dim]")

    # ── Lectura según formato ──────────────────────────────────────────────────
    if extension in (".xlsx", ".xlsm"):
        df = pd.read_excel(ruta, sheet_name=hoja, dtype=str, engine="openpyxl")
    elif extension == ".xls":
        df = pd.read_excel(ruta, sheet_name=hoja, dtype=str, engine="xlrd")
    elif extension == ".csv":
        # Intentar separadores comunes; si falla con coma, probar punto y coma
        try:
            df = pd.read_csv(ruta, dtype=str, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(ruta, dtype=str, encoding="latin-1")
        if df.shape[1] == 1:
            # Probablemente separado por punto y coma
            try:
                df = pd.read_csv(ruta, dtype=str, sep=";", encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(ruta, dtype=str, sep=";", encoding="latin-1")
    else:
        raise ValueError(
            f"Formato no soportado: '{extension}'. Use .xlsx, .xls o .csv"
        )

    console.print(
        f"[green]  ✓ Leídas {len(df)} filas y {len(df.columns)} columnas[/green]"
    )
    console.print(f"[dim]  Columnas originales: {list(df.columns)}[/dim]")

    # ── Eliminar filas completamente vacías ────────────────────────────────────
    df = df.dropna(how="all")

    # ── Normalizar nombres de columnas (quitar espacios extra) ─────────────────
    df.columns = [str(c).strip() for c in df.columns]

    # ── Aplicar mapeo de columnas ──────────────────────────────────────────────
    mappings = _cargar_mappings(tipo)
    df = _aplicar_mapeo(df, mappings)

    console.print(
        f"[green]  ✓ Extracción completada: {len(df)} registros listos para transformación[/green]"
    )

    return df


def listar_hojas(ruta: str | Path) -> list[str]:
    """Retorna los nombres de las hojas de un archivo Excel."""
    ruta = Path(ruta)
    xl = pd.ExcelFile(ruta)
    return xl.sheet_names
