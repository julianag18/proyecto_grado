"""
Pipeline ETL completo: extrae → transforma → carga.
Punto de entrada para procesar cualquier archivo al sistema PAME.
"""
from src.etl.extractor import extract
from src.etl.transformer import transform
from src.etl.loader import load
from pathlib import Path

def run_pipeline(filepath: str, dry_run: bool = False) -> dict:
    """
    Ejecuta el pipeline ETL completo sobre un archivo.

    Args:
        filepath: ruta al archivo (.csv, .xlsx, .json)
        dry_run: si True, analiza y reporta sin cargar a Firestore

    Returns:
        dict con reporte completo de extracción, transformación y carga
    """
    nombre_archivo = Path(filepath).name

    # Paso 1: Extracción
    print(f"[ETL] Extrayendo: {nombre_archivo}")
    registros_crudos, meta_extraccion = extract(filepath)
    print(f"[ETL] Registros extraídos: {meta_extraccion['total_registros']}")

    # Paso 2: Transformación
    print("[ETL] Transformando y validando...")
    validos, invalidos, reporte_transform = transform(registros_crudos)
    print(f"[ETL] Válidos: {reporte_transform['validos']} | "
          f"Inválidos: {reporte_transform['invalidos']} | "
          f"Duplicados eliminados: {reporte_transform['duplicados_eliminados']}")

    # Paso 3: Carga
    modo = "SIMULACIÓN (dry_run)" if dry_run else "CARGA REAL"
    print(f"[ETL] Cargando a Firestore ({modo})...")
    reporte_carga = load(validos, nombre_archivo, reporte_transform, dry_run=dry_run)
    print(f"[ETL] Completado en {reporte_carga['duracion_segundos']}s")

    return {
        "extraccion":    meta_extraccion,
        "transformacion": reporte_transform,
        "carga":         reporte_carga,
    }
