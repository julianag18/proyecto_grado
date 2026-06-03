"""
etl/migration_log.py
──────────────────────────────────────────────────────────────────────────────
Gestiona el registro de cada ejecución ETL en la colección 'etl_log' de Firestore.
Provee contexto para los KPIs de avance de migración en el Dashboard.
──────────────────────────────────────────────────────────────────────────────
"""

from datetime import datetime, timezone
from rich.console import Console
from config.settings import settings
from db.client import get_firestore_client

console = Console()


def registrar_migracion(
    nombre_archivo: str,
    tipo: str,
    registros_leidos: int,
    registros_cargados: int,
    duplicados_omitidos: int,
    errores: int,
    estado: str,
    notas: str | None = None,
) -> str | None:
    """
    Inserta un registro en la colección 'etl_log' al finalizar un proceso ETL.

    Parámetros
    ----------
    nombre_archivo : str
        Nombre del archivo procesado (p.ej. "inventario_2024.xlsx").
    tipo : str
        'inventario' o 'servicios'.
    registros_leidos : int
        Total de filas leídas del archivo fuente.
    registros_cargados : int
        Filas efectivamente cargadas en la base de datos.
    duplicados_omitidos : int
        Filas omitidas por duplicación.
    errores : int
        Filas rechazadas por error.
    estado : str
        'completado', 'parcial' o 'fallido'.
    notas : str | None
        Información adicional libre.

    Retorna
    -------
    str | None
        ID del documento creado, o None si hubo un error o si está en modo Demo.
    """
    db = get_firestore_client()

    registro = {
        "nombre_archivo": nombre_archivo,
        "tipo": tipo,
        "registros_leidos": registros_leidos,
        "registros_cargados": registros_cargados,
        "duplicados_omitidos": duplicados_omitidos,
        "errores": errores,
        "estado": estado,
        "usuario": settings.pame_usuario,
        "notas": notas,
        "ejecutado_en": datetime.now(timezone.utc).isoformat(),
        # Campos del nuevo esquema NoSQL
        "fecha_carga": datetime.now(timezone.utc).isoformat(),
        "archivo": nombre_archivo,
        "formato": nombre_archivo.split(".")[-1].lower() if "." in nombre_archivo else "desconocido",
        "registros_totales": registros_leidos,
        "insertados": registros_cargados,
        "actualizados": 0,  # Se podría calcular si fuera necesario
    }

    if db is None:
        console.print("[yellow]  ⚠ Modo Demo activo: registro de migración no guardado en Firestore[/yellow]")
        return "demo-migracion-id"

    try:
        # Agregar un nuevo documento con auto-ID en la colección 'etl_log'
        ref_doc = db.collection("etl_log").document()
        ref_doc.set(registro)
        id_creado = ref_doc.id
        console.print(
            f"[green]  ✓ Migración registrada en Firestore (ID: {id_creado})[/green]"
        )
        return id_creado
    except Exception as e:
        console.print(f"[red]  ✗ No se pudo registrar la migración en Firestore: {e}[/red]")
        return None


def obtener_historial(limite: int = 20) -> list[dict]:
    """
    Retorna los últimos registros de migración ordenados por fecha descendente.
    Útil para el panel de migración en el Dashboard.
    """
    db = get_firestore_client()
    if db is None:
        return []

    try:
        # Obtener documentos de la colección 'etl_log' ordenados por 'ejecutado_en' desc
        docs = (
            db.collection("etl_log")
            .order_by("ejecutado_en", direction="DESCENDING")
            .limit(limite)
            .stream()
        )
        historial = []
        for d in docs:
            data = d.to_dict()
            data["id"] = d.id
            historial.append(data)
        return historial
    except Exception as e:
        console.print(f"[red]  ✗ Error al obtener historial de migraciones de Firestore: {e}[/red]")
        return []
