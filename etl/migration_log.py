"""
etl/migration_log.py
──────────────────────────────────────────────────────────────────────────────
Gestiona el registro de cada ejecución ETL en la tabla 'migraciones'.
Provee contexto para los KPIs de avance de migración en el Dashboard.
──────────────────────────────────────────────────────────────────────────────
"""

from datetime import datetime, timezone

from rich.console import Console

from config.settings import settings
from db.client import get_client

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
    Inserta un registro en la tabla 'migraciones' al finalizar un proceso ETL.

    Parámetros
    ----------
    nombre_archivo : str
        Nombre del archivo procesado (p.ej. "inventario_2024.xlsx").
    tipo : str
        'inventario' o 'servicios'.
    registros_leidos : int
        Total de filas leídas del archivo fuente.
    registros_cargados : int
        Filas efectivamente cargadas en Supabase.
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
        UUID del registro creado, o None si hubo un error al insertar.
    """
    cliente = get_client()

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
    }

    try:
        respuesta = cliente.table("migraciones").insert(registro).execute()
        id_creado = respuesta.data[0]["id"] if respuesta.data else None
        console.print(
            f"[green]  ✓ Migración registrada en BD (ID: {id_creado})[/green]"
        )
        return id_creado
    except Exception as e:
        console.print(f"[red]  ✗ No se pudo registrar la migración: {e}[/red]")
        return None


def obtener_historial(limite: int = 20) -> list[dict]:
    """
    Retorna los últimos registros de migración ordenados por fecha descendente.
    Útil para el panel de migración en el Dashboard.
    """
    cliente = get_client()
    respuesta = (
        cliente.table("migraciones")
        .select("*")
        .order("ejecutado_en", desc=True)
        .limit(limite)
        .execute()
    )
    return respuesta.data or []
