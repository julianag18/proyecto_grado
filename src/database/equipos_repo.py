"""
Repositorio de operaciones sobre las colecciones 'equipos' y subcolección 'servicios'.
Todas las funciones trabajan con diccionarios Python (documentos Firestore).
"""
from src.database.firebase_client import get_db
from datetime import date, datetime
from typing import Optional
from google.cloud import firestore

# ── COLECCIONES ──────────────────────────────────────────────────
COL_EQUIPOS     = "equipos"
COL_ALERTAS_LOG = "alertas_log"
COL_ETL_LOG     = "etl_log"
SUBCOL_SERVICIOS = "servicios"

# ── EQUIPOS ──────────────────────────────────────────────────────

def upsert_equipo(codigo: str, datos: dict) -> None:
    """
    Inserta o actualiza un equipo usando su codigo_equipo como ID de documento.
    Usa merge=True para no sobrescribir campos no incluidos en datos.
    """
    db = get_db()
    ref = db.collection(COL_EQUIPOS).document(codigo)
    datos["updated_at"] = datetime.utcnow().isoformat()
    ref.set(datos, merge=True)

def get_equipo(codigo: str) -> Optional[dict]:
    """Retorna el documento del equipo o None si no existe."""
    db = get_db()
    doc = db.collection(COL_EQUIPOS).document(codigo).get()
    return doc.to_dict() if doc.exists else None

def get_all_equipos(solo_activos: bool = True) -> list[dict]:
    """Retorna lista de todos los equipos. Si solo_activos=True, filtra activo==True."""
    db = get_db()
    query = db.collection(COL_EQUIPOS)
    if solo_activos:
        query = query.where("activo", "==", True)
    return [{"id": d.id, **d.to_dict()} for d in query.stream()]

def limpiar_equipos() -> int:
    """
    Elimina todos los documentos de la colección equipos (y sus subcolecciones).
    Retorna el número de documentos eliminados.
    PRECAUCIÓN: operación irreversible. Pedir confirmación antes de llamar.
    """
    db = get_db()
    equipos = list(db.collection(COL_EQUIPOS).stream())
    count = 0
    for eq in equipos:
        # Borrar subcolección servicios primero
        for srv in eq.reference.collection(SUBCOL_SERVICIOS).stream():
            srv.reference.delete()
            count += 1
        eq.reference.delete()
        count += 1
    return count

# ── SERVICIOS (subcolección) ──────────────────────────────────────

def agregar_servicio(codigo_equipo: str, servicio: dict) -> str:
    """
    Agrega un documento a la subcolección servicios del equipo indicado.
    Retorna el ID autogenerado del documento.
    """
    db = get_db()
    ref = db.collection(COL_EQUIPOS).document(codigo_equipo)\
            .collection(SUBCOL_SERVICIOS).document()
    servicio["created_at"] = datetime.utcnow().isoformat()
    ref.set(servicio)
    return ref.id

def get_servicios_equipo(codigo_equipo: str) -> list[dict]:
    """Retorna todos los servicios de un equipo, ordenados por fecha descendente."""
    db = get_db()
    docs = db.collection(COL_EQUIPOS).document(codigo_equipo)\
             .collection(SUBCOL_SERVICIOS)\
             .order_by("fecha_servicio_vigente", direction=firestore.Query.DESCENDING)\
             .stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

def get_ultimo_servicio(codigo_equipo: str, tipo_servicio: str = None) -> Optional[dict]:
    """
    Retorna el servicio más reciente del equipo.
    Si se especifica tipo_servicio, filtra solo ese tipo.
    """
    db = get_db()
    query = db.collection(COL_EQUIPOS).document(codigo_equipo)\
              .collection(SUBCOL_SERVICIOS)
    if tipo_servicio:
        query = query.where("tipo_servicio", "==", tipo_servicio)
    query = query.order_by("fecha_servicio_vigente",
                           direction=firestore.Query.DESCENDING).limit(1)
    docs = list(query.stream())
    return {"id": docs[0].id, **docs[0].to_dict()} if docs else None

# ── CONSULTAS PARA DASHBOARD ──────────────────────────────────────

def get_estado_actual_todos() -> list[dict]:
    """
    Retorna el estado actual de todos los equipos activos.
    Para cada equipo obtiene su servicio más reciente.
    Retorna lista de dicts con campos combinados equipo + último servicio.
    """
    equipos = get_all_equipos(solo_activos=True)
    resultado = []
    for eq in equipos:
        eq_id = eq.get("id")
        eq["equipo_id"] = eq_id
        eq["codigo_equipo"] = eq_id
        eq["nombre"] = eq.get("nombre_equipo") or eq.get("nombre") or eq_id
        
        ultimo = get_ultimo_servicio(eq_id)
        if ultimo:
            eq.update({
                "tipo_servicio":           ultimo.get("tipo_servicio"),
                "estado_servicio":         ultimo.get("estado_servicio") or "Programar",
                "estado_conformidad":      ultimo.get("estado_conformidad") or "Pendiente de Calificar",
                "fecha_servicio_vigente":  ultimo.get("fecha_servicio_vigente"),
                "fecha_proximo_servicio":  ultimo.get("fecha_proximo_servicio"),
                "proveedor":               ultimo.get("proveedor"),
                "frecuencia":              ultimo.get("frecuencia"),
                "dias_restantes":          calcular_dias_restantes(
                                               ultimo.get("fecha_proximo_servicio")
                                           ),
                "estado_alerta":           ultimo.get("estado_alerta") or "SIN_DATOS",
                "numero_informe":          ultimo.get("numero_informe"),
                "servicio_id":             ultimo.get("id"),
            })
        else:
            eq.update({
                "estado_servicio":         "Programar",
                "estado_conformidad":      "Pendiente de Calificar",
                "estado_alerta":           "SIN_DATOS",
                "tipo_servicio":           None,
                "frecuencia":              None,
                "fecha_servicio_vigente":  None,
                "fecha_proximo_servicio":  None,
                "dias_restantes":          None,
                "proveedor":               None,
                "numero_informe":          None,
                "servicio_id":             None,
            })
        resultado.append(eq)
    return resultado

def get_servicios_por_anio(anio: int, ubicacion: str = None) -> list[dict]:
    """
    Retorna todos los servicios del año indicado.
    Opcionalmente filtra por ubicación del equipo.
    Se usa para la vista de cumplimiento anual del dashboard.
    NOTA: Firestore no soporta consultas entre colecciones directamente.
    Se resuelve con Collection Group queries sobre la subcolección 'servicios'.
    """
    from google.api_core.exceptions import FailedPrecondition
    from src.database.exceptions import FirestoreIndexError
    import re

    db = get_db()
    query = db.collection_group(SUBCOL_SERVICIOS).where("anio", "==", anio)
    try:
        docs = list(query.stream())
    except FailedPrecondition as e:
        err_msg = str(e)
        url_match = re.search(r'(https://console\.firebase\.google\.com/[^\s\)\"\']+)', err_msg)
        index_url = url_match.group(1) if url_match else None
        raise FirestoreIndexError(
            "Falta el índice de grupo de colecciones requerido en Firestore para la subcolección 'servicios'.",
            index_url=index_url
        ) from e

    servicios = [{"srv_id": d.id, **d.to_dict()} for d in docs]

    # Si se pide filtro por ubicación, cruzar con datos del equipo padre
    if ubicacion:
        servicios = [s for s in servicios if s.get("ubicacion") == ubicacion]
    return servicios

def marcar_alerta_resuelta_repo(alerta_id: str) -> bool:
    """
    Marca una alerta como leída (resuelta) y registra la transacción en el histórico alertas_log,
    calculando el tiempo de respuesta en días.
    """
    db = get_db()
    try:
        doc_ref = db.collection("alertas").document(alerta_id)
        doc = doc_ref.get()
        if not doc.exists:
            return False
        
        data = doc.to_dict()
        if data.get("leida") == True:
            return True
            
        resueltas_en = datetime.utcnow().isoformat()
        
        # Calcular días transcurridos desde que se generó hasta que se resolvió
        generada_en_str = data.get("generada_en") or data.get("created_at")
        dias_respuesta = None
        if generada_en_str:
            try:
                clean_gen = generada_en_str.replace("Z", "+00:00")
                t_gen = datetime.fromisoformat(clean_gen)
                t_res = datetime.fromisoformat(resueltas_en)
                dias_respuesta = round((t_res - t_gen).total_seconds() / 86400.0, 2)
            except Exception:
                pass
        
        # Actualizar alerta original
        doc_ref.update({
            "leida": True,
            "resuelta_en": resueltas_en,
            "dias_respuesta": dias_respuesta
        })
        
        # Registrar en alertas_log
        log_entrada = {
            "alerta_id": alerta_id,
            "codigo_equipo": data.get("codigo_equipo"),
            "nombre_equipo": data.get("nombre") or data.get("nombre_equipo"),
            "area": data.get("area"),
            "tipo_alerta": data.get("tipo_alerta"),
            "nivel_prioridad": data.get("nivel_prioridad"),
            "generada_en": generada_en_str,
            "resuelta_en": resueltas_en,
            "dias_respuesta": dias_respuesta,
            "tipo_servicio": data.get("tipo_servicio")
        }
        registrar_alerta(log_entrada)
        return True
    except Exception:
        return False

def get_metricas_alertas() -> dict:
    """
    Calcula métricas agregadas del histórico de alertas_log:
    - Tiempo promedio de resolución (días)
    - Total de alertas resueltas
    - Alertas por nivel de prioridad
    """
    db = get_db()
    docs = db.collection(COL_ALERTAS_LOG).stream()
    resueltas = 0
    suma_dias = 0.0
    prioridades = {}
    
    for d in docs:
        data = d.to_dict()
        dias = data.get("dias_respuesta")
        if dias is not None:
            resueltas += 1
            suma_dias += float(dias)
        
        prioridad = data.get("nivel_prioridad", "desconocida")
        prioridades[prioridad] = prioridades.get(prioridad, 0) + 1
        
    promedio = round(suma_dias / resueltas, 1) if resueltas > 0 else 0.0
    return {
        "tiempo_promedio_resolucion": promedio,
        "total_alertas_resueltas": resueltas,
        "alertas_por_prioridad": prioridades
    }

def calcular_dias_restantes(fecha_proximo_str: Optional[str]) -> Optional[int]:
    """Calcula días entre hoy y la fecha próxima. Negativo = ya venció."""
    if not fecha_proximo_str:
        return None
    try:
        fecha = date.fromisoformat(fecha_proximo_str)
        return (fecha - date.today()).days
    except ValueError:
        return None

# ── LOGS ──────────────────────────────────────────────────────────

def registrar_carga_etl(log: dict) -> str:
    """Guarda un registro de la carga ETL en la colección etl_log."""
    db = get_db()
    ref = db.collection(COL_ETL_LOG).document()
    log["fecha_carga"] = datetime.utcnow().isoformat()
    ref.set(log)
    return ref.id

def get_historial_etl(limite: int = 20) -> list[dict]:
    """Retorna los últimos N registros de carga ETL."""
    db = get_db()
    docs = db.collection(COL_ETL_LOG)\
             .order_by("fecha_carga", direction=firestore.Query.DESCENDING)\
             .limit(limite).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

def registrar_alerta(log: dict) -> str:
    """Guarda un registro de alerta enviada en la colección alertas_log."""
    db = get_db()
    ref = db.collection(COL_ALERTAS_LOG).document()
    log["fecha_envio"] = datetime.utcnow().isoformat()
    ref.set(log)
    return ref.id

def get_historial_alertas(limite: int = 30) -> list[dict]:
    """Retorna los últimos N registros de alertas enviadas."""
    db = get_db()
    docs = db.collection(COL_ALERTAS_LOG)\
             .order_by("fecha_envio", direction=firestore.Query.DESCENDING)\
             .limit(limite).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]
