"""
Módulo de ayuda para el dashboard Streamlit.
Orquesta la carga de datos desde Firebase Firestore o desde archivos muestra locales (Modo Demo).
"""
import os
import json
import sys
import pandas as pd
from pathlib import Path
from datetime import date

# Asegurar que el root del proyecto esté en el path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Intentar verificar disponibilidad de Firestore
_FIRESTORE_DISPONIBLE = False
try:
    from src.database.firebase_client import get_db
    # Si get_db no lanza excepción, Firestore está disponible
    get_db()
    _FIRESTORE_DISPONIBLE = True
except Exception:
    pass

def es_demo_mode() -> bool:
    """Retorna True si el sistema opera en modo demo (sin Firestore)."""
    return not _FIRESTORE_DISPONIBLE

def cargar_estado_actual_pame() -> pd.DataFrame:
    """
    Carga el estado de todos los equipos y sus últimos servicios.
    Retorna un DataFrame de Pandas.
    """
    if _FIRESTORE_DISPONIBLE:
        try:
            from src.database.equipos_repo import get_estado_actual_todos
            datos = get_estado_actual_todos()
            if datos:
                # Firestore retorna lista de diccionarios, convertimos a DataFrame
                df = pd.DataFrame(datos)
                return df
        except Exception as e:
            print(f"Error cargando desde Firestore, usando fallback: {e}")

    # Fallback / Modo Demo: Leer del cronograma_sample.csv generado
    csv_path = ROOT_DIR / "data" / "samples" / "cronograma_sample.csv"
    if not csv_path.exists():
        # Si no existe en samples, buscar en data/test
        csv_path = ROOT_DIR / "data" / "test" / "cronograma_prueba.xlsx"
        if csv_path.exists():
            df = pd.read_excel(csv_path)
            # Normalizar columnas para el dashboard
            return df
        return pd.DataFrame()

    # Cargar CSV sample
    try:
        df = pd.read_csv(csv_path, encoding="latin-1", sep=";")
        
        # Mapear nombres a los internos
        from src.etl.transformer import transform
        validos, _, _ = transform(df.to_dict(orient="records"))
        
        # Aplanar para el DataFrame
        df_validos = pd.DataFrame(validos)
        
        # Calcular dias_restantes
        from src.database.equipos_repo import calcular_dias_restantes
        if not df_validos.empty and "fecha_proximo_servicio" in df_validos.columns:
            df_validos["dias_restantes"] = df_validos["fecha_proximo_servicio"].apply(calcular_dias_restantes)
            
        return df_validos
    except Exception as e:
        print(f"Error leyendo cronograma_sample.csv en modo demo: {e}")
        return pd.DataFrame()

def cargar_cumplimiento_anual(anio: int) -> pd.DataFrame:
    """
    Carga el historial de servicios de un año determinado.
    """
    if _FIRESTORE_DISPONIBLE:
        try:
            from src.database.equipos_repo import get_servicios_por_anio
            datos = get_servicios_por_anio(anio)
            if datos:
                return pd.DataFrame(datos)
        except Exception as e:
            print(f"Error cargando cumplimiento anual desde Firestore: {e}")

    # Fallback / Modo Demo: Leer de cronograma_historico.json
    json_path = ROOT_DIR / "data" / "samples" / "cronograma_historico.json"
    if not json_path.exists():
        return pd.DataFrame()

    try:
        with open(json_path, encoding="utf-8") as f:
            raw = json.load(f)
        
        # Transformar registros
        from src.etl.transformer import transform
        validos, _, _ = transform(raw)
        
        df = pd.DataFrame(validos)
        if not df.empty and "anio" in df.columns:
            df = df[df["anio"] == anio]
        return df
    except Exception as e:
        print(f"Error leyendo cronograma_historico.json: {e}")
        return pd.DataFrame()

def cargar_historial_etl() -> pd.DataFrame:
    """Carga los logs de cargas ETL."""
    datos_crudos = []
    if _FIRESTORE_DISPONIBLE:
        try:
            from src.database.equipos_repo import get_historial_etl
            datos_crudos = get_historial_etl(limite=50)
        except Exception:
            pass

    if not datos_crudos:
        # Fallback / Modo Demo
        datos_crudos = [
            {
                "fecha_carga": "2026-06-01T08:00:00.000000",
                "archivo": "cronograma_historico.json",
                "dry_run": False,
                "insertados": 123,
                "actualizados": 0,
                "errores": [],
                "duracion_segundos": 1.45,
                "reporte_transformacion": {"total_registros": 123, "validos": 123, "invalidos": 0, "duplicados_eliminados": 0}
            },
            {
                "fecha_carga": "2026-06-03T10:36:00.000000",
                "archivo": "cronograma_sample.csv",
                "dry_run": False,
                "insertados": 50,
                "actualizados": 0,
                "errores": [],
                "duracion_segundos": 0.85,
                "reporte_transformacion": {"total_registros": 55, "validos": 50, "invalidos": 2, "duplicados_eliminados": 3}
            }
        ]

    # Aplanar y normalizar
    datos_procesados = []
    for d in datos_crudos:
        rep_trans = d.get("reporte_transformacion", {})
        if not rep_trans and "reporte_transformacion" in d:
            rep_trans = d["reporte_transformacion"]
        
        datos_procesados.append({
            "fecha_carga": d.get("fecha_carga"),
            "archivo": d.get("archivo"),
            "dry_run": d.get("dry_run"),
            "registros_leidos": rep_trans.get("total_registros", d.get("insertados", 0)),
            "registros_cargados": d.get("insertados", 0),
            "duplicados_omitidos": rep_trans.get("duplicados_eliminados", 0),
            "errores": d.get("errores", []),
            "duracion_segundos": d.get("duracion_segundos", 0.0)
        })

    return pd.DataFrame(datos_procesados)


def cargar_historial_alertas() -> pd.DataFrame:
    """Carga los logs de alertas enviadas."""
    if _FIRESTORE_DISPONIBLE:
        try:
            from src.database.equipos_repo import get_historial_alertas
            datos = get_historial_alertas(limite=50)
            if datos:
                return pd.DataFrame(datos)
        except Exception:
            pass

    # Modo Demo
    return pd.DataFrame([
        {
            "fecha_envio": "2026-06-03T08:00:00.000000",
            "tipo": "diaria",
            "equipos_alertados": ["LS2023", "LS2024", "LS2025"],
            "total_alertas": 3,
            "destinatarios": ["juli3213@gmail.com"],
            "exito": True,
            "error": None
        }
    ])
