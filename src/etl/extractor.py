"""
Extractor multi-formato para el PAME de Laproff.
Detecta el formato por extensión y normaliza a lista de diccionarios.
El JSON es el más complejo por su estructura variable.
"""
import pandas as pd
import json
from pathlib import Path
from typing import Union

class ExtractorError(Exception):
    """Error descriptivo de extracción con mensaje en español."""
    pass

def extract(filepath: str) -> tuple[list[dict], dict]:
    """
    Lee un archivo CSV, Excel o JSON y retorna:
    - lista de diccionarios (un dict por registro)
    - dict con metadatos: {"formato": str, "estructura_detectada": str, "total_registros": int}

    Retorna lista de dicts en lugar de DataFrame para preservar la flexibilidad
    de los campos extra que puede traer el JSON.
    """
    path = Path(filepath)
    if not path.exists():
        raise ExtractorError(f"Archivo no encontrado: {filepath}")

    ext = path.suffix.lower()

    if ext == ".csv":
        return _extract_csv(filepath)
    elif ext in (".xlsx", ".xls"):
        return _extract_excel(filepath)
    elif ext == ".json":
        return _extract_json(filepath)
    else:
        raise ExtractorError(
            f"Formato '{ext}' no soportado. Use .csv, .xlsx o .json"
        )

def _extract_csv(filepath: str) -> tuple[list[dict], dict]:
    """Lee CSV con detección automática de separador y encoding."""
    # Intentar encodings comunes en archivos latinoamericanos
    for encoding in ["latin-1", "utf-8", "cp1252"]:
        for sep in [";", ",", "\t"]:
            try:
                df = pd.read_csv(filepath, encoding=encoding, sep=sep)
                if len(df.columns) > 1:  # separador correcto si hay más de 1 columna
                    registros = df.where(pd.notna(df), None).to_dict(orient="records")
                    return registros, {
                        "formato": "csv",
                        "encoding_detectado": encoding,
                        "separador_detectado": sep,
                        "total_registros": len(registros)
                    }
            except Exception:
                continue
    # Fallback default
    try:
        df = pd.read_csv(filepath)
        registros = df.where(pd.notna(df), None).to_dict(orient="records")
        return registros, {
            "formato": "csv",
            "encoding_detectado": "unknown",
            "separador_detectado": "unknown",
            "total_registros": len(registros)
        }
    except Exception as e:
        raise ExtractorError(
            f"No se pudo leer el CSV. Verifique que el archivo no esté dañado: {e}"
        )

def _extract_excel(filepath: str) -> tuple[list[dict], dict]:
    """Lee Excel, primera hoja por defecto."""
    try:
        # Usar openpyxl para xlsx y xlrd para xls
        engine = "openpyxl" if str(filepath).endswith(".xlsx") else "xlrd"
        df = pd.read_excel(filepath, engine=engine)
        registros = df.where(pd.notna(df), None).to_dict(orient="records")
        return registros, {
            "formato": "excel",
            "total_registros": len(registros)
        }
    except Exception as e:
        raise ExtractorError(f"Error al leer Excel: {str(e)}")

def _extract_json(filepath: str) -> tuple[list[dict], dict]:
    """
    Lee JSON con detección automática de estructura.
    Soporta múltiples formatos posibles:

    Formato A — Array plano (el más común):
        [{"Código del Equipo": "LS001", ...}, ...]

    Formato B — Objeto con clave conocida:
        {"equipos": [...]} o {"servicios": [...]} o {"data": [...]}

    Formato C — Objeto con servicios anidados por equipo:
        {"LS001": {"nombre": "...", "servicios": [...]}, "LS002": {...}}

    Formato D — Un solo objeto (un registro):
        {"Código del Equipo": "LS001", ...}

    Los campos no reconocidos se preservan en 'campos_extra'.
    """
    try:
        with open(filepath, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        raise ExtractorError(f"Error al leer JSON: {str(e)}")

    # Formato A: array de objetos planos
    if isinstance(raw, list):
        return raw, {"formato": "json", "estructura_detectada": "array_plano",
                     "total_registros": len(raw)}

    # Formato B: objeto con una clave que contiene el array
    if isinstance(raw, dict):
        claves_lista = [k for k, v in raw.items() if isinstance(v, list)]
        if len(claves_lista) == 1:
            registros = raw[claves_lista[0]]
            return registros, {"formato": "json",
                               "estructura_detectada": f"objeto_clave_{claves_lista[0]}",
                               "total_registros": len(registros)}

        # Buscar clave conocida
        for clave in ["equipos", "servicios", "data", "records", "items", "cronograma"]:
            if clave in raw and isinstance(raw[clave], list):
                registros = raw[clave]
                return registros, {"formato": "json",
                                   "estructura_detectada": f"objeto_clave_{clave}",
                                   "total_registros": len(registros)}

        # Formato C: objeto de objetos (clave = codigo_equipo)
        if raw:
            primer_valor = next(iter(raw.values()))
            if isinstance(primer_valor, dict):
                registros = []
                for codigo, datos in raw.items():
                    if isinstance(datos, dict):
                        # Si tiene subarray de servicios, aplanar
                        if "servicios" in datos and isinstance(datos["servicios"], list):
                            for srv in datos["servicios"]:
                                reg = {"Código del Equipo": codigo}
                                reg.update({k: v for k, v in datos.items() if k != "servicios"})
                                reg.update(srv)
                                registros.append(reg)
                        else:
                            datos_copy = dict(datos)
                            datos_copy.setdefault("Código del Equipo", codigo)
                            registros.append(datos_copy)
                return registros, {"formato": "json",
                                    "estructura_detectada": "objeto_de_objetos",
                                    "total_registros": len(registros)}

        # Formato D: un solo objeto
        return [raw], {"formato": "json", "estructura_detectada": "objeto_unico",
                       "total_registros": 1}

    raise ExtractorError(
        "Estructura JSON no reconocida. "
        "Se esperaba un array o un objeto con lista de registros."
    )
