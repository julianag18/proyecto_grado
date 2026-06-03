"""
etl/loader.py
──────────────────────────────────────────────────────────────────────────────
Módulo de carga para Firebase Firestore.
Toma los DataFrames validados y los persiste en Firestore.

Estrategia NoSQL:
  - EQUIPOS: Colección principal 'equipos', ID de documento = 'codigo_equipo'
  - SERVICIOS: Subcolección 'servicios' dentro del equipo,
               ID de documento = '{tipo_servicio_safe}_{fecha_servicio_vigente}' (idempotente)
  - PROVEEDORES: Colección 'proveedores' (opcional, para mantener compatibilidad)
──────────────────────────────────────────────────────────────────────────────
"""

import math
from datetime import datetime, timezone
import pandas as pd
from rich.console import Console
from rich.progress import track

from config.settings import settings
from db.client import get_firestore_client

console = Console()


def _normalizar_nulos(val: any) -> any:
    """
    Normaliza valores nulos y cadenas de texto específicas a None (null en Firestore).
    """
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).strip()
    if val_str.upper() in ("NO IDENTIFICADO", "NO REGISTRA", "NO APLICA", "NAN", "NONE", "NULL", ""):
        return None
    return val_str


def _parsear_fecha_proximo_servicio(periodo: str | None) -> str | None:
    """
    Convierte un período 'MM/YYYY' a una fecha estándar 'YYYY-MM-01'.
    """
    if not periodo:
        return None
    parts = str(periodo).strip().split("/")
    if len(parts) == 2:
        mm, yyyy = parts
        try:
            return f"{yyyy}-{mm.zfill(2)}-01"
        except Exception:
            return None
    return None


def _extraer_anio(fecha: str | None) -> int | None:
    """
    Extrae el año como entero a partir de una fecha ISO 'YYYY-MM-DD'.
    """
    if not fecha:
        return None
    try:
        return int(str(fecha).split("-")[0])
    except (ValueError, IndexError):
        return None


class ResultadoCarga:
    """Métricas del proceso de carga."""
    def __init__(self, tabla: str, registros_enviados: int = 0):
        self.tabla = tabla
        self.registros_enviados = registros_enviados
        self.registros_exitosos = 0
        self.registros_fallidos = 0
        self.errores = []


def cargar_proveedores(df: pd.DataFrame) -> ResultadoCarga:
    """
    Guarda proveedores únicos en la colección 'proveedores'.
    """
    resultado = ResultadoCarga(tabla="proveedores")
    if "proveedor_nombre" not in df.columns and "proveedor" not in df.columns:
        return resultado

    col = "proveedor_nombre" if "proveedor_nombre" in df.columns else "proveedor"
    nombres_unicos = df[col].dropna().unique()
    registros = [str(n).strip() for n in nombres_unicos if _normalizar_nulos(n)]

    resultado.registros_enviados = len(registros)
    db = get_firestore_client()

    if db is None:
        console.print("[yellow]  ⚠ Modo Demo activo: omitiendo carga de proveedores a Firestore[/yellow]")
        resultado.registros_exitosos = len(registros)
        return resultado

    console.print(f"\n[bold blue]📤 Cargando en 'proveedores':[/bold blue] {len(registros)} registros")
    for prov in registros:
        try:
            # Usar el nombre del proveedor sanitizado como ID
            doc_id = prov.upper().replace(" ", "_")
            db.collection("proveedores").document(doc_id).set({"nombre": prov}, merge=True)
            resultado.registros_exitosos += 1
        except Exception as e:
            resultado.registros_fallidos += 1
            resultado.errores.append(f"Proveedor {prov}: {e}")

    return resultado


def cargar_equipos(df: pd.DataFrame, migracion_id: str | None = None) -> ResultadoCarga:
    """
    Carga o actualiza el DataFrame de equipos en la colección 'equipos'.
    Usa 'codigo_equipo' como ID de documento (UPSERT).
    """
    resultado = ResultadoCarga(tabla="equipos", registros_enviados=len(df))
    db = get_firestore_client()

    # Columnas conocidas que mapean directamente al documento de equipos
    campos_estandar = {
        "codigo_equipo", "nombre", "serie", "modelo", "fabricante",
        "proveedor_nombre", "ubicacion", "area", "estado_equipo",
        "es_usable", "estado_aprobacion", "activo_fijo", "mide_ambiente",
        "criticidad", "fecha_solicitud", "fecha_entrega_area",
        "fecha_aprobacion", "creado_por", "aprobado_por", "migracion_id"
    }

    if db is None:
        console.print("[yellow]  ⚠ Modo Demo activo: omitiendo carga de equipos a Firestore[/yellow]")
        resultado.registros_exitosos = len(df)
        return resultado

    console.print(f"\n[bold blue]📤 Cargando en 'equipos':[/bold blue] {len(df)} registros")

    for _, fila in track(df.iterrows(), total=len(df), description="  Cargando equipos..."):
        try:
            row_dict = fila.to_dict()
            codigo = row_dict.get("codigo_equipo")
            if not codigo:
                continue

            # Construir el documento
            doc_data = {
                "codigo_equipo": codigo,
                "nombre_equipo": _normalizar_nulos(row_dict.get("nombre") or row_dict.get("nombre_equipo")),
                "ubicacion": _normalizar_nulos(row_dict.get("ubicacion")),
                "serie_equipo": _normalizar_nulos(row_dict.get("serie") or row_dict.get("serie_equipo")),
                "activo_fijo": _normalizar_nulos(row_dict.get("activo_fijo")),
                "activo": True,
                "metadata_carga": {
                    "migracion_id": migracion_id,
                    "usuario": settings.pame_usuario,
                    "fecha_carga": datetime.now(timezone.utc).isoformat()
                }
            }

            # Agregar otros campos estándar si existen
            for k, v in row_dict.items():
                if k in campos_estandar and k not in ("codigo_equipo", "nombre", "serie", "activo_fijo"):
                    doc_data[k] = _normalizar_nulos(v)

            # Recolectar campos extra
            campos_extra = {}
            for k, v in row_dict.items():
                if k not in campos_estandar and not k.startswith("_"):
                    campos_extra[k] = v
            if campos_extra:
                doc_data["campos_extra"] = campos_extra

            # Guardar en Firestore usando set(..., merge=True)
            db.collection("equipos").document(codigo).set(doc_data, merge=True)
            resultado.registros_exitosos += 1
        except Exception as e:
            resultado.registros_fallidos += 1
            resultado.errores.append(f"Equipo {fila.get('codigo_equipo', 'desconocido')}: {e}")

    console.print(f"[green]  ✓ Exitosos: {resultado.registros_exitosos}[/green]  [red]✗ Fallidos: {resultado.registros_fallidos}[/red]")
    return resultado


def cargar_servicios(df: pd.DataFrame, migracion_id: str | None = None) -> ResultadoCarga:
    """
    Carga o actualiza servicios en la subcolección 'servicios' de cada equipo.
    El ID de documento es determinista para evitar duplicación.
    """
    resultado = ResultadoCarga(tabla="servicios", registros_enviados=len(df))
    db = get_firestore_client()

    campos_estandar = {
        "tipo_servicio", "frecuencia", "frecuencia_dias",
        "fecha_servicio_vigente", "fecha_ejecucion_programada",
        "periodo_proximo_servicio", "fecha_proximo_servicio",
        "estado_servicio", "estado_entrega", "estado_conformidad",
        "proveedor", "numero_informe", "migracion_id", "anio"
    }

    if db is None:
        console.print("[yellow]  ⚠ Modo Demo activo: omitiendo carga de servicios a Firestore[/yellow]")
        resultado.registros_exitosos = len(df)
        return resultado

    console.print(f"\n[bold blue]📤 Cargando en 'servicios':[/bold blue] {len(df)} registros")

    for _, fila in track(df.iterrows(), total=len(df), description="  Cargando servicios..."):
        try:
            row_dict = fila.to_dict()
            codigo = row_dict.get("codigo_equipo")
            tipo_srv = row_dict.get("tipo_servicio")
            fecha_vigente = row_dict.get("fecha_servicio_vigente")

            if not codigo or not tipo_srv or not fecha_vigente:
                resultado.registros_fallidos += 1
                resultado.errores.append(f"Registro sin clave única (codigo={codigo}, tipo={tipo_srv}, fecha={fecha_vigente})")
                continue

            # Limpiar fecha_vigente
            fecha_vigente_norm = _normalizar_nulos(fecha_vigente)
            if not fecha_vigente_norm:
                resultado.registros_fallidos += 1
                resultado.errores.append(f"Fecha de servicio vigente nula para equipo {codigo}")
                continue

            # Crear ID de documento determinista
            tipo_srv_safe = str(tipo_srv).lower().replace(" ", "_").replace("ñ", "n").replace("ó", "o")
            doc_id = f"{tipo_srv_safe}_{fecha_vigente_norm}"

            # Construir datos del servicio
            periodo = row_dict.get("periodo_proximo_servicio")
            fecha_proximo = row_dict.get("fecha_proximo_servicio") or _parsear_fecha_proximo_servicio(periodo)

            doc_data = {
                "tipo_servicio": tipo_srv,
                "frecuencia": _normalizar_nulos(row_dict.get("frecuencia")),
                "frecuencia_dias": row_dict.get("frecuencia_dias"),
                "fecha_servicio_vigente": fecha_vigente_norm,
                "fecha_ejecucion_programada": _normalizar_nulos(row_dict.get("fecha_ejecucion_programada")),
                "periodo_proximo_servicio": _normalizar_nulos(periodo),
                "fecha_proximo_servicio": _normalizar_nulos(fecha_proximo),
                "estado_servicio": _normalizar_nulos(row_dict.get("estado_servicio")),
                "estado_entrega": _normalizar_nulos(row_dict.get("estado_entrega")),
                "estado_conformidad": _normalizar_nulos(row_dict.get("estado_conformidad")),
                "proveedor": _normalizar_nulos(row_dict.get("proveedor")),
                "numero_informe": _normalizar_nulos(row_dict.get("numero_informe")),
                "anio": _extraer_anio(fecha_vigente_norm),
                "migracion_id": migracion_id,
            }

            # Recolectar campos extra
            campos_extra = {}
            for k, v in row_dict.items():
                if k not in campos_estandar and k not in ("codigo_equipo", "nombre_equipo") and not k.startswith("_"):
                    campos_extra[k] = v
            if campos_extra:
                doc_data["campos_extra"] = campos_extra

            # Guardar en la subcolección 'servicios' del documento del equipo
            db.collection("equipos").document(codigo).collection("servicios").document(doc_id).set(doc_data, merge=True)
            resultado.registros_exitosos += 1

        except Exception as e:
            resultado.registros_fallidos += 1
            resultado.errores.append(f"Servicio para {fila.get('codigo_equipo', 'desconocido')}: {e}")

    console.print(f"[green]  ✓ Exitosos: {resultado.registros_exitosos}[/green]  [red]✗ Fallidos: {resultado.registros_fallidos}[/red]")
    return resultado
