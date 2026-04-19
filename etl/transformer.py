"""
etl/transformer.py
──────────────────────────────────────────────────────────────────────────────
Módulo de transformación: limpieza, normalización, deduplicación y preparación
de los DataFrames extraídos para su carga en Supabase.

Operaciones realizadas:
  1. Normalización de texto (tildes, mayúsculas, espacios extra)
  2. Conversión de fechas a formato ISO 8601
  3. Normalización de enums (estado_equipo, tipo_servicio, etc.)
  4. Detección y separación de duplicados
  5. Retorno de DataFrame limpio + DataFrame de rechazos con motivo
──────────────────────────────────────────────────────────────────────────────
"""

import re
import unicodedata
from datetime import datetime
from dataclasses import dataclass, field

import pandas as pd
import yaml
from rich.console import Console
from rich.table import Table as RichTable

from config.settings import ROOT_DIR

console = Console()
MAPPINGS_PATH = ROOT_DIR / "config" / "column_mappings.yaml"

# ──────────────────────────────────────────────────────────────────────────────
# Estructuras de resultado
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ResultadoTransformacion:
    """Resultado devuelto por la función principal de transformación."""
    df_limpio: pd.DataFrame                # Registros válidos listos para cargar
    df_rechazos: pd.DataFrame              # Registros con errores críticos
    df_duplicados: pd.DataFrame            # Registros duplicados omitidos
    total_leidos: int = 0
    total_validos: int = 0
    total_rechazados: int = 0
    total_duplicados: int = 0
    advertencias: list[str] = field(default_factory=list)

    def imprimir_resumen(self):
        """Imprime un resumen legible en consola usando rich."""
        t = RichTable(title="📊 Resultado de Transformación", show_header=True)
        t.add_column("Métrica", style="cyan")
        t.add_column("Valor", justify="right", style="bold")
        t.add_row("Total leídos", str(self.total_leidos))
        t.add_row("Válidos (para cargar)", str(self.total_validos), style="green")
        t.add_row("Rechazados (error crítico)", str(self.total_rechazados), style="red")
        t.add_row("Duplicados omitidos", str(self.total_duplicados), style="yellow")
        console.print(t)
        if self.advertencias:
            console.print("\n[yellow]⚠ Advertencias:[/yellow]")
            for adv in self.advertencias:
                console.print(f"  • {adv}")


# ──────────────────────────────────────────────────────────────────────────────
# Funciones auxiliares de normalización
# ──────────────────────────────────────────────────────────────────────────────

def _normalizar_texto(valor: any) -> str | None:
    """
    Normaliza una cadena de texto:
      - Elimina espacios al inicio/fin y saltos de línea
      - Colapsa espacios múltiples a uno solo
      - Devuelve None si el valor es nulo o vacío
    """
    if pd.isna(valor) or str(valor).strip() in ("", "nan", "NaN", "None", "N/A", "NA"):
        return None
    texto = str(valor).strip()
    texto = re.sub(r"\s+", " ", texto)
    return texto


def _normalizar_fecha(valor: any) -> str | None:
    """
    Convierte múltiples formatos de fecha al formato ISO 8601 (YYYY-MM-DD).
    Soporta: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, D/M/YY y variantes con guiones.
    Retorna None si no puede parsear.
    """
    if pd.isna(valor) or str(valor).strip() in ("", "nan", "None", "N/A"):
        return None

    valor_str = str(valor).strip()

    formatos = [
        "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y",
        "%d/%m/%y", "%m/%d/%y", "%Y/%m/%d",
        "%d %b %Y", "%B %d, %Y",
    ]

    for fmt in formatos:
        try:
            return datetime.strptime(valor_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Intento de pandas como último recurso
    try:
        return pd.to_datetime(valor_str, dayfirst=True).strftime("%Y-%m-%d")
    except Exception:
        return None


def _normalizar_enum(valor: any, opciones_validas: list[str]) -> str | None:
    """
    Normaliza un valor de tipo enum:
      1. Elimina espacios y normaliza unicode
      2. Busca coincidencia exacta (case-insensitive)
      3. Si no hay, busca coincidencia parcial
      4. Si no hay, retorna el valor tal cual (con advertencia)
    """
    if pd.isna(valor) or str(valor).strip() == "":
        return None

    valor_str = str(valor).strip()

    # Coincidencia exacta (insensible a mayúsculas)
    for opcion in opciones_validas:
        if valor_str.lower() == opcion.lower():
            return opcion

    # Coincidencia parcial
    for opcion in opciones_validas:
        if valor_str.lower() in opcion.lower() or opcion.lower() in valor_str.lower():
            return opcion

    # Sin coincidencia: devolver tal cual para que el validador lo marque
    return valor_str


def _cargar_enums() -> dict[str, list[str]]:
    """Carga los valores válidos de enums desde column_mappings.yaml."""
    with open(MAPPINGS_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("enums", {})


# ──────────────────────────────────────────────────────────────────────────────
# Transformación de INVENTARIO
# ──────────────────────────────────────────────────────────────────────────────

def transformar_inventario(df: pd.DataFrame) -> ResultadoTransformacion:
    """
    Transforma el DataFrame crudo de inventario de equipos.

    Parámetros
    ----------
    df : pd.DataFrame
        DataFrame extraído por extractor.leer_archivo() con tipo='inventario'.

    Retorna
    -------
    ResultadoTransformacion
        Objeto con df_limpio listo para el loader, df_rechazos, df_duplicados
        y métricas del proceso.
    """
    console.print("\n[bold blue]🔄 Transformando inventario...[/bold blue]")
    enums = _cargar_enums()
    advertencias: list[str] = []
    errores_filas: list[dict] = []      # filas con error crítico
    duplicados_filas: list[dict] = []   # filas duplicadas

    df = df.copy()
    total_leidos = len(df)

    # ── 1. Normalizar texto en todas las columnas ──────────────────────────────
    columnas_texto = [
        "codigo_equipo", "nombre", "serie", "modelo", "fabricante",
        "proveedor_nombre", "ubicacion", "area", "creado_por",
        "aprobado_por", "activo_fijo",
    ]
    for col in columnas_texto:
        if col in df.columns:
            df[col] = df[col].apply(_normalizar_texto)

    # ── 2. Normalizar enums ────────────────────────────────────────────────────
    mapeo_enums = {
        "estado_equipo":   enums.get("estado_equipo", []),
        "es_usable":       enums.get("es_usable", []),
        "estado_aprobacion": enums.get("estado_aprobacion", []),
        "criticidad":      enums.get("criticidad", []),
    }
    for col, opciones in mapeo_enums.items():
        if col in df.columns:
            df[col] = df[col].apply(lambda v: _normalizar_enum(v, opciones))

    # ── 3. Normalizar fechas ───────────────────────────────────────────────────
    for col in ["fecha_solicitud", "fecha_entrega_area", "fecha_aprobacion"]:
        if col in df.columns:
            df[col] = df[col].apply(_normalizar_fecha)

    # ── 4. Normalizar mide_ambiente como booleano ──────────────────────────────
    if "mide_ambiente" in df.columns:
        df["mide_ambiente"] = df["mide_ambiente"].apply(
            lambda v: True if str(v).strip().lower() in ("sí", "si", "yes", "true", "1", "x")
            else False if pd.notna(v) and str(v).strip() != ""
            else False
        )

    # ── 5. Asignar criticidad por defecto si no existe ─────────────────────────
    if "criticidad" not in df.columns:
        df["criticidad"] = "Media"
        advertencias.append("Columna 'criticidad' no encontrada. Se asignó 'Media' a todos los equipos.")

    # ── 6. Validar campo obligatorio: codigo_equipo ────────────────────────────
    mascara_sin_codigo = df["codigo_equipo"].isna() if "codigo_equipo" in df.columns \
        else pd.Series([True] * len(df))

    if mascara_sin_codigo.any():
        rechazados = df[mascara_sin_codigo].copy()
        rechazados["_motivo_rechazo"] = "codigo_equipo vacío o nulo (campo obligatorio)"
        errores_filas.append(rechazados)
        df = df[~mascara_sin_codigo]
        console.print(
            f"[red]  ✗ {mascara_sin_codigo.sum()} fila(s) rechazadas: código de equipo vacío[/red]"
        )

    # ── 7. Validar campo obligatorio: nombre ──────────────────────────────────
    if "nombre" in df.columns:
        mascara_sin_nombre = df["nombre"].isna()
        if mascara_sin_nombre.any():
            rechazados = df[mascara_sin_nombre].copy()
            rechazados["_motivo_rechazo"] = "nombre de equipo vacío (campo obligatorio)"
            errores_filas.append(rechazados)
            df = df[~mascara_sin_nombre]
            console.print(
                f"[red]  ✗ {mascara_sin_nombre.sum()} fila(s) rechazadas: nombre vacío[/red]"
            )

    # ── 8. Detectar duplicados por codigo_equipo ───────────────────────────────
    if "codigo_equipo" in df.columns:
        duplicados_mask = df.duplicated(subset=["codigo_equipo"], keep="first")
        if duplicados_mask.any():
            dups = df[duplicados_mask].copy()
            dups["_motivo_rechazo"] = "Duplicado: codigo_equipo repetido en el mismo archivo"
            duplicados_filas.append(dups)
            df = df[~duplicados_mask]
            console.print(
                f"[yellow]  ⚠ {duplicados_mask.sum()} duplicado(s) detectado(s) y omitido(s)[/yellow]"
            )

    # ── Consolidar rechazos y duplicados ──────────────────────────────────────
    df_rechazos = pd.concat(errores_filas, ignore_index=True) if errores_filas \
        else pd.DataFrame()
    df_duplicados = pd.concat(duplicados_filas, ignore_index=True) if duplicados_filas \
        else pd.DataFrame()

    resultado = ResultadoTransformacion(
        df_limpio=df.reset_index(drop=True),
        df_rechazos=df_rechazos,
        df_duplicados=df_duplicados,
        total_leidos=total_leidos,
        total_validos=len(df),
        total_rechazados=len(df_rechazos),
        total_duplicados=len(df_duplicados),
        advertencias=advertencias,
    )

    resultado.imprimir_resumen()
    return resultado


# ──────────────────────────────────────────────────────────────────────────────
# Transformación de SERVICIOS (cronograma)
# ──────────────────────────────────────────────────────────────────────────────

def transformar_servicios(df: pd.DataFrame) -> ResultadoTransformacion:
    """
    Transforma el DataFrame crudo de servicios/cronograma.

    Parámetros
    ----------
    df : pd.DataFrame
        DataFrame extraído por extractor.leer_archivo() con tipo='servicios'.

    Retorna
    -------
    ResultadoTransformacion
    """
    console.print("\n[bold blue]🔄 Transformando servicios...[/bold blue]")
    enums = _cargar_enums()
    advertencias: list[str] = []
    errores_filas: list[dict] = []
    duplicados_filas: list[dict] = []

    df = df.copy()
    total_leidos = len(df)

    # ── 1. Normalizar texto ────────────────────────────────────────────────────
    columnas_texto = [
        "codigo_equipo", "nombre_equipo", "tipo_servicio",
        "frecuencia", "numero_informe", "proveedor",
        "periodo_proximo_servicio",
    ]
    for col in columnas_texto:
        if col in df.columns:
            df[col] = df[col].apply(_normalizar_texto)

    # ── 2. Normalizar enums ────────────────────────────────────────────────────
    mapeo_enums = {
        "tipo_servicio":     enums.get("tipo_servicio", []),
        "frecuencia":        enums.get("frecuencia", []),
        "estado_servicio":   enums.get("estado_servicio", []),
        "estado_entrega":    enums.get("estado_entrega", []),
        "estado_conformidad": enums.get("estado_conformidad", []),
    }
    for col, opciones in mapeo_enums.items():
        if col in df.columns:
            df[col] = df[col].apply(lambda v: _normalizar_enum(v, opciones))

    # ── 3. Normalizar fechas ───────────────────────────────────────────────────
    for col in ["fecha_servicio_vigente", "fecha_ejecucion_programada", "fecha_ejecucion_real"]:
        if col in df.columns:
            df[col] = df[col].apply(_normalizar_fecha)

    # ── 4. Calcular frecuencia_dias a partir de frecuencia ────────────────────
    from scheduler.frequency_parser import frecuencia_a_dias
    if "frecuencia" in df.columns:
        df["frecuencia_dias"] = df["frecuencia"].apply(
            lambda v: frecuencia_a_dias(v) if pd.notna(v) else None
        )

    # ── 5. Validar campo obligatorio: codigo_equipo ────────────────────────────
    if "codigo_equipo" in df.columns:
        mascara = df["codigo_equipo"].isna()
        if mascara.any():
            rechazados = df[mascara].copy()
            rechazados["_motivo_rechazo"] = "codigo_equipo vacío (campo obligatorio en servicios)"
            errores_filas.append(rechazados)
            df = df[~mascara]

    # ── 6. Detectar duplicados por codigo_equipo + tipo_servicio + fecha_servicio_vigente
    clave_dup = [c for c in ["codigo_equipo", "tipo_servicio", "fecha_servicio_vigente"]
                 if c in df.columns]
    if clave_dup:
        dup_mask = df.duplicated(subset=clave_dup, keep="first")
        if dup_mask.any():
            dups = df[dup_mask].copy()
            dups["_motivo_rechazo"] = f"Duplicado por: {', '.join(clave_dup)}"
            duplicados_filas.append(dups)
            df = df[~dup_mask]

    df_rechazos = pd.concat(errores_filas, ignore_index=True) if errores_filas \
        else pd.DataFrame()
    df_duplicados = pd.concat(duplicados_filas, ignore_index=True) if duplicados_filas \
        else pd.DataFrame()

    resultado = ResultadoTransformacion(
        df_limpio=df.reset_index(drop=True),
        df_rechazos=df_rechazos,
        df_duplicados=df_duplicados,
        total_leidos=total_leidos,
        total_validos=len(df),
        total_rechazados=len(df_rechazos),
        total_duplicados=len(df_duplicados),
        advertencias=advertencias,
    )

    resultado.imprimir_resumen()
    return resultado
