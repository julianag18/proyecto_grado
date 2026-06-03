"""
dashboard/components/data_loader.py
──────────────────────────────────────────────────────────────────────────────
Capa de datos del dashboard: abstrae el acceso a Firestore y provee un modo
demo con datos sintéticos en memoria cuando no hay credenciales configuradas.

Modo de operación:
  • LIVE  — Credenciales FIREBASE_CREDENTIALS_PATH en .env → datos reales en Firestore
  • DEMO  — Sin credenciales → genera datos sintéticos con la misma estructura
──────────────────────────────────────────────────────────────────────────────
"""

import sys
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

# Asegurar que el root del proyecto esté en el path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ── Intentar importar cliente Firestore ───────────────────────────────────────
_FIRESTORE_DISPONIBLE = False
try:
    from config.settings import settings
    from db.client import get_firestore_client
    if get_firestore_client() is not None:
        _FIRESTORE_DISPONIBLE = True
except Exception:
    pass


# ══════════════════════════════════════════════════════════════════════════════
# Modo DEMO — datos sintéticos en memoria
# ══════════════════════════════════════════════════════════════════════════════

_AREAS = ["Control Calidad", "Producción", "I+D", "Microbiología", "Fisicoquímica"]
_TIPOS = ["Calibración", "Verificación", "Mantenimiento", "Calificación"]
_FRECUENCIAS = ["Anual", "Semestral", "Trimestral", "Bimestral", "Mensual"]
_PROVEEDORES = ["DOXA", "METROCAL", "LABORCLIN", "SOLULAB", "INCONTEC", "METROLOGÍA NACIONAL"]
_ESTADOS_ALERTA = ["AL_DIA", "PROXIMO", "CRITICO", "VENCIDO", "SIN_DATOS"]
_CONFORMIDAD = ["Conforme", "Pendiente de Calificar", "No Conforme", "Fuera de Especificación"]

_EQUIPOS_NOMBRES = [
    "Balanza Analítica 0.1 mg", "Balanza Analítica 0.01 mg", "Balanza Semianálítica",
    "Balanza de Precisión", "pH-metro de Banco", "pH-metro Portátil",
    "Termohigrómetro Digital", "Termohigrómetro Análogo", "Termómetro Digital",
    "Termómetro de Referencia", "Micropipeta 100-1000 µL", "Micropipeta 10-100 µL",
    "Micropipeta 1-10 µL", "Espectrofotómetro UV-Vis", "Cromatógrafo HPLC",
    "Conductímetro", "Refractómetro", "Viscosímetro", "Bureta 25 mL", "Bureta 50 mL",
    "Pipeta Volumétrica 10 mL", "Pipeta Volumétrica 25 mL", "Balón Volumétrico 100 mL",
    "Balón Volumétrico 250 mL", "Incubadora", "Estufa de Secado", "Potenciómetro",
    "Agitador Vórtex", "Sonicador", "Probeta Graduada 100 mL",
]


def _generar_demo_estado_pame(n: int = 40, seed: int = 42) -> pd.DataFrame:
    """Genera un DataFrame simulando la vista v_estado_pame de Supabase."""
    random.seed(seed)
    hoy = date.today()
    frecuencia_pesos = {"Anual": 365, "Semestral": 182, "Trimestral": 91, "Bimestral": 60, "Mensual": 30}

    registros = []
    for i in range(n):
        nombre = random.choice(_EQUIPOS_NOMBRES)
        area = random.choice(_AREAS)
        frecuencia = random.choice(_FRECUENCIAS)
        freq_dias = frecuencia_pesos[frecuencia]
        tipo = random.choice(_TIPOS)
        proveedor = random.choice(_PROVEEDORES)
        criticidad = random.choices(["Alta", "Media", "Baja"], weights=[2, 5, 3])[0]

        # Distribuir escenarios realistas
        escenario = random.choices(
            ["al_dia", "proximo", "critico", "vencido", "sin_datos"],
            weights=[45, 18, 12, 15, 10],
        )[0]

        if escenario == "sin_datos":
            fecha_vigente = None
            fecha_proximo = None
            dias_restantes = None
            estado_alerta = "SIN_DATOS"
        elif escenario == "al_dia":
            dias_pasados = random.randint(10, max(11, freq_dias - 35))
            fecha_vigente = hoy - timedelta(days=max(1, dias_pasados))
            fecha_proximo = fecha_vigente + timedelta(days=freq_dias)
            dias_restantes = (fecha_proximo - hoy).days
            estado_alerta = "AL_DIA"
        elif escenario == "proximo":
            dias_restantes = random.randint(16, 30)
            fecha_proximo = hoy + timedelta(days=dias_restantes)
            fecha_vigente = fecha_proximo - timedelta(days=freq_dias)
            estado_alerta = "PROXIMO"
        elif escenario == "critico":
            dias_restantes = random.randint(0, 15)
            fecha_proximo = hoy + timedelta(days=dias_restantes)
            fecha_vigente = fecha_proximo - timedelta(days=freq_dias)
            estado_alerta = "CRITICO"
        else:  # vencido
            dias_restantes = -random.randint(1, 90)
            fecha_proximo = hoy + timedelta(days=dias_restantes)
            fecha_vigente = fecha_proximo - timedelta(days=freq_dias)
            estado_alerta = "VENCIDO"

        informe = f"DN-{random.randint(100000, 999999)}" if escenario not in ("sin_datos",) and random.random() > 0.3 else None

        registros.append({
            "equipo_id":              f"eq-{i+1:04d}",
            "codigo_equipo":          f"LS{1000 + i}",
            "nombre":                 nombre,
            "area":                   area,
            "ubicacion":              f"Lab. {area}",
            "estado_equipo":          random.choices(
                ["En Servicio", "Fuera de Uso", "En Reparación"],
                weights=[8, 1, 1]
            )[0],
            "criticidad":             criticidad,
            "tipo_servicio":          tipo,
            "frecuencia":             frecuencia,
            "fecha_servicio_vigente": fecha_vigente.isoformat() if fecha_vigente else None,
            "fecha_proximo_servicio": fecha_proximo.isoformat() if fecha_proximo else None,
            "dias_restantes":         dias_restantes,
            "estado_alerta":          estado_alerta,
            "estado_servicio":        "Ejecutado" if informe else "Programar",
            "estado_conformidad":     random.choice(_CONFORMIDAD) if informe else "Pendiente de Calificar",
            "proveedor":              proveedor,
            "numero_informe":         informe,
        })

    return pd.DataFrame(registros)


def _generar_demo_alertas(df_estado: pd.DataFrame) -> pd.DataFrame:
    """Genera alertas a partir del DataFrame de estado."""
    alertas = []
    for _, row in df_estado.iterrows():
        estado = row["estado_alerta"]
        if estado not in ("VENCIDO", "CRITICO", "PROXIMO"):
            continue

        if estado == "VENCIDO":
            msg = (f"⚠ VENCIDO: El servicio de {row['tipo_servicio']} para [{row['codigo_equipo']}] "
                   f"{row['nombre']} venció hace {abs(row['dias_restantes'])} día(s). Acción inmediata.")
            prioridad = "alta"
        elif estado == "CRITICO":
            msg = (f"🔴 CRÍTICO: El servicio de {row['tipo_servicio']} para [{row['codigo_equipo']}] "
                   f"{row['nombre']} vence en {row['dias_restantes']} día(s).")
            prioridad = "alta"
        else:
            msg = (f"🟡 PRÓXIMO: El servicio de {row['tipo_servicio']} para [{row['codigo_equipo']}] "
                   f"{row['nombre']} vence en {row['dias_restantes']} día(s).")
            prioridad = "media"

        alertas.append({
            "equipo_id":       row["equipo_id"],
            "codigo_equipo":   row["codigo_equipo"],
            "nombre":          row["nombre"],
            "area":            row["area"],
            "tipo_alerta":     f"SERVICIO_{estado}",
            "nivel_prioridad": prioridad,
            "mensaje":         msg,
            "leida":           False,
            "estado_alerta":   estado,
            "dias_restantes":  row["dias_restantes"],
            "tipo_servicio":   row["tipo_servicio"],
        })

    return pd.DataFrame(alertas) if alertas else pd.DataFrame()


def _generar_demo_migraciones() -> pd.DataFrame:
    """Simula el historial de migraciones ETL."""
    hoy = date.today()
    return pd.DataFrame([
        {
            "nombre_archivo":      "inventario_inicial_2024.xlsx",
            "tipo":                "inventario",
            "registros_leidos":    45,
            "registros_cargados":  40,
            "duplicados_omitidos": 3,
            "errores":             2,
            "estado":              "parcial",
            "usuario":             "admin",
            "ejecutado_en":        (hoy - timedelta(days=45)).isoformat(),
        },
        {
            "nombre_archivo":      "cronograma_2024.xlsx",
            "tipo":                "servicios",
            "registros_leidos":    40,
            "registros_cargados":  38,
            "duplicados_omitidos": 1,
            "errores":             1,
            "estado":              "parcial",
            "usuario":             "admin",
            "ejecutado_en":        (hoy - timedelta(days=44)).isoformat(),
        },
        {
            "nombre_archivo":      "inventario_actualizacion_2025.xlsx",
            "tipo":                "inventario",
            "registros_leidos":    12,
            "registros_cargados":  12,
            "duplicados_omitidos": 0,
            "errores":             0,
            "estado":              "completado",
            "usuario":             "admin",
            "ejecutado_en":        (hoy - timedelta(days=10)).isoformat(),
        },
    ])


# ══════════════════════════════════════════════════════════════════════════════
# API pública del data_loader
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60, show_spinner=False)
def cargar_estado_pame() -> tuple[pd.DataFrame, bool]:
    """
    Carga el estado PAME desde Firestore (modo live) o genera datos demo.
    Combina la información del equipo y de sus servicios en un DataFrame plano.
    """
    db = get_firestore_client() if _FIRESTORE_DISPONIBLE else None
    
    if db is not None:
        try:
            from src.database.equipos_repo import get_estado_actual_todos
            registros = get_estado_actual_todos()
            if registros:
                df = pd.DataFrame(registros)
                return df, True
        except Exception as e:
            from src.database.exceptions import FirestoreIndexError
            if isinstance(e, FirestoreIndexError) or "FirestoreIndexError" in type(e).__name__:
                from dashboard.components.kpi_cards import render_index_error_banner
                render_index_error_banner(e)
            else:
                st.warning(f"No se pudo conectar a Firestore: {e}. Usando datos demo.")

    return _generar_demo_estado_pame(), False


@st.cache_data(ttl=60, show_spinner=False)
def cargar_alertas(solo_no_leidas: bool = True) -> pd.DataFrame:
    """Carga alertas activas desde Firestore o genera demo."""
    db = get_firestore_client() if _FIRESTORE_DISPONIBLE else None
    
    if db is not None:
        try:
            # Consulta a la colección 'alertas'
            alertas_ref = db.collection("alertas")
            if solo_no_leidas:
                alertas_ref = alertas_ref.where("leida", "==", False)
            
            docs = alertas_ref.stream()
            registros = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                registros.append(data)
                
            df = pd.DataFrame(registros)
            
            # Ordenar localmente por fecha de generación descendente (evita problemas de índices)
            if not df.empty and "generada_en" in df.columns:
                df = df.sort_values("generada_en", ascending=False)
                
            return df
        except Exception:
            pass

    # Demo: generar alertas desde el estado
    df_estado, _ = cargar_estado_pame()
    return _generar_demo_alertas(df_estado)


@st.cache_data(ttl=60, show_spinner=False)
def cargar_migraciones() -> pd.DataFrame:
    """Carga el historial de migraciones ETL de la colección 'etl_log'."""
    db = get_firestore_client() if _FIRESTORE_DISPONIBLE else None
    
    if db is not None:
        try:
            from src.database.equipos_repo import get_historial_etl
            registros = get_historial_etl(limite=50)
            if registros:
                for r in registros:
                    if "ejecutado_en" not in r and "fecha_carga" in r:
                        r["ejecutado_en"] = r["fecha_carga"]
                df = pd.DataFrame(registros)
                return df
        except Exception:
            pass

    return _generar_demo_migraciones()


@st.cache_data(ttl=120, show_spinner=False)
def calcular_kpis(df: pd.DataFrame) -> dict:
    """
    Calcula los 6 KPIs del PAME a partir del DataFrame de estado.
    """
    if df.empty:
        return {"total": 0, "al_dia": 0, "proximos": 0, "criticos": 0, "vencidos": 0, "sin_datos": 0, "pct_al_dia": 0.0}

    total = len(df)
    al_dia    = (df["estado_alerta"] == "AL_DIA").sum()
    proximos  = (df["estado_alerta"] == "PROXIMO").sum()
    criticos  = (df["estado_alerta"] == "CRITICO").sum()
    vencidos  = (df["estado_alerta"] == "VENCIDO").sum()
    sin_datos = (df["estado_alerta"] == "SIN_DATOS").sum()
    pct_al_dia = round(100 * al_dia / total, 1) if total > 0 else 0.0

    return {
        "total":      int(total),
        "al_dia":     int(al_dia),
        "proximos":   int(proximos),
        "criticos":   int(criticos),
        "vencidos":   int(vencidos),
        "sin_datos":  int(sin_datos),
        "pct_al_dia": float(pct_al_dia),
    }


def marcar_alerta_leida(alerta_id: str) -> bool:
    """Marca una alerta como leída en Firestore."""
    db = get_firestore_client() if _FIRESTORE_DISPONIBLE else None
    
    if db is None:
        return True  # En demo, simular éxito
        
    try:
        from src.database.equipos_repo import marcar_alerta_resuelta_repo
        res = marcar_alerta_resuelta_repo(alerta_id)
        st.cache_data.clear()
        return res
    except Exception:
        try:
            db.collection("alertas").document(alerta_id).update({"leida": True})
            st.cache_data.clear()
            return True
        except Exception:
            return False


@st.cache_data(ttl=60, show_spinner=False)
def cargar_metricas_alertas() -> dict:
    """Retorna las métricas históricas de alertas desde el repositorio."""
    if _FIRESTORE_DISPONIBLE:
        try:
            from src.database.equipos_repo import get_metricas_alertas
            return get_metricas_alertas()
        except Exception:
            pass
    # Métricas demo
    return {
        "tiempo_promedio_resolucion": 4.2,
        "total_alertas_resueltas": 18,
        "alertas_por_prioridad": {"alta": 8, "media": 10}
    }


def es_modo_demo() -> bool:
    """Retorna True si el dashboard está corriendo en modo demo."""
    return not _FIRESTORE_DISPONIBLE
