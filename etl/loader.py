"""
etl/loader.py
──────────────────────────────────────────────────────────────────────────────
Módulo de carga: toma los DataFrames validados y los persiste en Supabase
mediante operaciones UPSERT (insertar o actualizar si ya existe).

Estrategia UPSERT:
  - EQUIPOS: clave única = codigo_equipo
  - PROVEEDORES: clave única = nombre
  - SERVICIOS: clave única = (codigo_equipo, tipo_servicio, fecha_servicio_vigente)
──────────────────────────────────────────────────────────────────────────────
"""

import math
from dataclasses import dataclass

import pandas as pd
from rich.console import Console
from rich.progress import track

from db.client import get_client

console = Console()

# Tamaño de lote para envíos a Supabase (evita timeouts en cargas grandes)
BATCH_SIZE = 50


@dataclass
class ResultadoCarga:
    """Métricas del proceso de carga."""
    tabla: str
    registros_enviados: int = 0
    registros_exitosos: int = 0
    registros_fallidos: int = 0
    errores: list[str] = None

    def __post_init__(self):
        if self.errores is None:
            self.errores = []


def _df_a_registros(df: pd.DataFrame) -> list[dict]:
    """
    Convierte un DataFrame a lista de diccionarios, eliminando claves con None/NaN.
    Supabase rechaza valores None en campos con DEFAULT si se envían explícitamente.
    """
    registros = []
    for _, fila in df.iterrows():
        registro = {}
        for k, v in fila.to_dict().items():
            # Omitir columnas internas del ETL y valores nulos
            if k.startswith("_"):
                continue
            if v is None or (isinstance(v, float) and math.isnan(v)):
                continue
            registro[k] = v
        registros.append(registro)
    return registros


def _upsert_en_lotes(
    tabla: str,
    registros: list[dict],
    clave_conflicto: str,
) -> ResultadoCarga:
    """
    Envía los registros a Supabase en lotes usando UPSERT.

    Parámetros
    ----------
    tabla : str
        Nombre de la tabla en Supabase.
    registros : list[dict]
        Lista de registros a cargar.
    clave_conflicto : str
        Nombre de la columna (o columnas separadas por coma) para detectar conflicto.
    """
    cliente = get_client()
    resultado = ResultadoCarga(tabla=tabla, registros_enviados=len(registros))

    if not registros:
        console.print(f"[yellow]  ⚠ No hay registros para cargar en '{tabla}'[/yellow]")
        return resultado

    # Dividir en lotes
    total_lotes = math.ceil(len(registros) / BATCH_SIZE)
    console.print(
        f"\n[bold blue]📤 Cargando en '{tabla}':[/bold blue] "
        f"{len(registros)} registros en {total_lotes} lote(s)"
    )

    for i in track(range(total_lotes), description=f"  Cargando {tabla}..."):
        lote = registros[i * BATCH_SIZE: (i + 1) * BATCH_SIZE]
        try:
            cliente.table(tabla).upsert(
                lote,
                on_conflict=clave_conflicto,
            ).execute()
            resultado.registros_exitosos += len(lote)
        except Exception as e:
            resultado.registros_fallidos += len(lote)
            resultado.errores.append(
                f"Lote {i + 1}/{total_lotes}: {str(e)}"
            )
            console.print(f"[red]  ✗ Error en lote {i + 1}: {e}[/red]")

    console.print(
        f"[green]  ✓ Exitosos: {resultado.registros_exitosos}[/green]  "
        f"[red]✗ Fallidos: {resultado.registros_fallidos}[/red]"
    )
    return resultado


# ──────────────────────────────────────────────────────────────────────────────
# Funciones públicas
# ──────────────────────────────────────────────────────────────────────────────

def cargar_proveedores(df: pd.DataFrame) -> ResultadoCarga:
    """
    Extrae proveedores únicos del DataFrame de equipos y los carga/actualiza
    en la tabla 'proveedores'.

    Parámetros
    ----------
    df : pd.DataFrame
        DataFrame de equipos que puede contener columna 'proveedor_nombre'.
    """
    if "proveedor_nombre" not in df.columns:
        console.print("[yellow]  ⚠ Columna 'proveedor_nombre' no encontrada; se omite carga de proveedores[/yellow]")
        return ResultadoCarga(tabla="proveedores")

    # Extraer nombres únicos y no nulos
    nombres_unicos = df["proveedor_nombre"].dropna().unique()
    registros = [{"nombre": n} for n in nombres_unicos if str(n).strip()]

    return _upsert_en_lotes("proveedores", registros, "nombre")


def cargar_equipos(df: pd.DataFrame, migracion_id: str | None = None) -> ResultadoCarga:
    """
    Carga el DataFrame de inventario en la tabla 'equipos'.

    Parámetros
    ----------
    df : pd.DataFrame
        DataFrame validado de equipos.
    migracion_id : str | None
        UUID del registro de migración para trazabilidad.
    """
    df_carga = df.copy()

    # Agregar ID de migración para trazabilidad
    if migracion_id:
        df_carga["migracion_id"] = migracion_id

    # Columnas permitidas en la tabla equipos (sin proveedor_id, se resuelve por trigger)
    columnas_equipos = [
        "codigo_equipo", "nombre", "serie", "modelo", "fabricante",
        "proveedor_nombre", "ubicacion", "area", "estado_equipo",
        "es_usable", "estado_aprobacion", "activo_fijo", "mide_ambiente",
        "criticidad", "fecha_solicitud", "fecha_entrega_area",
        "fecha_aprobacion", "creado_por", "aprobado_por", "migracion_id",
    ]
    columnas_presentes = [c for c in columnas_equipos if c in df_carga.columns]
    df_carga = df_carga[columnas_presentes]

    registros = _df_a_registros(df_carga)
    return _upsert_en_lotes("equipos", registros, "codigo_equipo")


def cargar_servicios(df: pd.DataFrame, migracion_id: str | None = None) -> ResultadoCarga:
    """
    Carga el DataFrame de servicios en la tabla 'servicios'.
    Resuelve el equipo_id buscando el codigo_equipo en Supabase.

    Parámetros
    ----------
    df : pd.DataFrame
        DataFrame validado de servicios.
    migracion_id : str | None
        UUID del registro de migración para trazabilidad.
    """
    df_carga = df.copy()
    cliente = get_client()

    # ── Resolver equipo_id para cada codigo_equipo ─────────────────────────────
    console.print("\n[cyan]  🔗 Resolviendo equipo_id desde codigo_equipo...[/cyan]")
    codigos_unicos = df_carga["codigo_equipo"].dropna().unique().tolist()

    # Obtener el mapeo codigo_equipo → id desde Supabase
    respuesta = cliente.table("equipos")\
        .select("id, codigo_equipo")\
        .in_("codigo_equipo", codigos_unicos)\
        .execute()

    mapa_id = {r["codigo_equipo"]: r["id"] for r in respuesta.data}

    df_carga["equipo_id"] = df_carga["codigo_equipo"].map(mapa_id)

    # Filas sin equipo_id (equipo no registrado en BD)
    sin_id = df_carga["equipo_id"].isna().sum()
    if sin_id > 0:
        console.print(
            f"[yellow]  ⚠ {sin_id} servicio(s) sin equipo correspondiente en BD (se omitirán)[/yellow]"
        )
        df_carga = df_carga[df_carga["equipo_id"].notna()]

    # Agregar ID de migración
    if migracion_id:
        df_carga["migracion_id"] = migracion_id

    columnas_servicios = [
        "equipo_id", "codigo_equipo", "nombre_equipo",
        "fecha_servicio_vigente", "fecha_ejecucion_programada",
        "tipo_servicio", "frecuencia", "frecuencia_dias",
        "numero_informe", "estado_servicio", "estado_entrega",
        "estado_conformidad", "proveedor", "periodo_proximo_servicio",
        "migracion_id",
    ]
    columnas_presentes = [c for c in columnas_servicios if c in df_carga.columns]
    df_carga = df_carga[columnas_presentes]

    registros = _df_a_registros(df_carga)
    return _upsert_en_lotes(
        "servicios",
        registros,
        "codigo_equipo,tipo_servicio,fecha_servicio_vigente",
    )
