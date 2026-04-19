"""
etl/validator.py
──────────────────────────────────────────────────────────────────────────────
Validación de esquema y tipos usando modelos Pydantic v2.
Se ejecuta DESPUÉS de transformer.py y ANTES de loader.py.
Genera un reporte detallado de filas inválidas con su motivo.
──────────────────────────────────────────────────────────────────────────────
"""

from datetime import date
from typing import Optional, Literal

import pandas as pd
from pydantic import BaseModel, field_validator, ValidationError
from rich.console import Console

console = Console()


# ──────────────────────────────────────────────────────────────────────────────
# Modelos Pydantic (esquema esperado en la BD)
# ──────────────────────────────────────────────────────────────────────────────

class EquipoSchema(BaseModel):
    """Esquema de validación para un registro de equipo."""

    codigo_equipo: str
    nombre: str
    serie: Optional[str] = None
    modelo: Optional[str] = None
    fabricante: Optional[str] = None
    proveedor_nombre: Optional[str] = None
    ubicacion: Optional[str] = None
    area: Optional[str] = None
    estado_equipo: Literal[
        "En Servicio", "Fuera de Uso", "En Reparación", "Dado de Baja"
    ] = "En Servicio"
    es_usable: Optional[Literal["Disponible", "No Disponible", "En Préstamo"]] = None
    estado_aprobacion: Optional[Literal[
        "Borrador", "Pendiente", "Aprobado", "Rechazado"
    ]] = "Borrador"
    activo_fijo: Optional[str] = None
    mide_ambiente: Optional[bool] = False
    criticidad: Literal["Alta", "Media", "Baja"] = "Media"
    fecha_solicitud: Optional[str] = None       # ISO string "YYYY-MM-DD"
    fecha_entrega_area: Optional[str] = None
    fecha_aprobacion: Optional[str] = None
    creado_por: Optional[str] = None
    aprobado_por: Optional[str] = None

    @field_validator("codigo_equipo", "nombre")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("No puede estar vacío")
        return v.strip()


class ServicioSchema(BaseModel):
    """Esquema de validación para un registro de servicio."""

    codigo_equipo: str
    nombre_equipo: Optional[str] = None
    fecha_servicio_vigente: Optional[str] = None
    fecha_ejecucion_programada: Optional[str] = None
    tipo_servicio: Optional[Literal[
        "Calibración", "Verificación", "Mantenimiento", "Calificación"
    ]] = "Calibración"
    frecuencia: Optional[Literal[
        "Anual", "Semestral", "Trimestral", "Bimestral", "Mensual"
    ]] = None
    frecuencia_dias: Optional[int] = None
    numero_informe: Optional[str] = None
    estado_servicio: Optional[Literal[
        "Programar", "En Ejecución", "Ejecutado", "Cancelado"
    ]] = "Programar"
    estado_entrega: Optional[Literal["Pendiente", "Entregado"]] = "Pendiente"
    estado_conformidad: Optional[Literal[
        "Pendiente de Calificar", "Conforme",
        "No Conforme", "Fuera de Especificación"
    ]] = "Pendiente de Calificar"
    proveedor: Optional[str] = None
    periodo_proximo_servicio: Optional[str] = None

    @field_validator("codigo_equipo")
    @classmethod
    def codigo_no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("codigo_equipo no puede estar vacío")
        return v.strip()


# ──────────────────────────────────────────────────────────────────────────────
# Función principal de validación
# ──────────────────────────────────────────────────────────────────────────────

def validar_dataframe(
    df: pd.DataFrame,
    schema: type[BaseModel],
    nombre_tipo: str = "registros",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Valida cada fila del DataFrame contra el schema Pydantic dado.

    Parámetros
    ----------
    df : pd.DataFrame
        DataFrame transformado (salida de transformer.py).
    schema : type[BaseModel]
        Clase Pydantic a usar (EquipoSchema o ServicioSchema).
    nombre_tipo : str
        Nombre descriptivo para los mensajes de consola.

    Retorna
    -------
    (df_valido, df_invalido) : tuple[pd.DataFrame, pd.DataFrame]
        df_valido  → registros que pasaron la validación
        df_invalido → registros rechazados con columna '_errores_validacion'
    """
    console.print(f"\n[bold blue]✅ Validando {len(df)} {nombre_tipo}...[/bold blue]")

    filas_validas: list[int] = []
    filas_invalidas: list[tuple[int, str]] = []

    # Columnas del schema (para no pasar columnas extra que Pydantic rechace)
    campos_schema = set(schema.model_fields.keys())

    for idx, fila in df.iterrows():
        # Filtrar solo los campos del schema; reemplazar NaN por None
        datos = {
            k: (None if pd.isna(v) else v)
            for k, v in fila.to_dict().items()
            if k in campos_schema
        }
        try:
            schema(**datos)
            filas_validas.append(idx)
        except ValidationError as e:
            # Consolidar errores en un string legible
            mensajes = "; ".join(
                f"{err['loc'][0] if err['loc'] else '?'}: {err['msg']}"
                for err in e.errors()
            )
            filas_invalidas.append((idx, mensajes))

    df_valido = df.loc[filas_validas].copy().reset_index(drop=True)

    if filas_invalidas:
        indices_inv = [i for i, _ in filas_invalidas]
        mensajes_inv = {i: m for i, m in filas_invalidas}
        df_invalido = df.loc[indices_inv].copy()
        df_invalido["_errores_validacion"] = df_invalido.index.map(mensajes_inv)
        df_invalido = df_invalido.reset_index(drop=True)
    else:
        df_invalido = pd.DataFrame()

    console.print(
        f"[green]  ✓ {len(df_valido)} válidos[/green]  "
        f"[red]✗ {len(df_invalido)} inválidos[/red]"
    )

    return df_valido, df_invalido


def validar_inventario(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Atajo para validar un DataFrame de inventario."""
    return validar_dataframe(df, EquipoSchema, "equipos")


def validar_servicios(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Atajo para validar un DataFrame de servicios."""
    return validar_dataframe(df, ServicioSchema, "servicios")
