"""
Repositorio de operaciones sobre las colecciones 'equipos' y subcolección 'servicios'.
Todas las funciones trabajan con diccionarios Python (documentos Firestore).
Soporta un modo Fallback local (JSON) si las credenciales de Firestore no están disponibles.
"""
from src.database.firebase_client import get_db, firestore_disponible
from datetime import date, datetime
from typing import Optional
import json
import os
import uuid
from pathlib import Path

# ── COLECCIONES ──────────────────────────────────────────────────
COL_EQUIPOS     = "equipos"
COL_ALERTAS_LOG = "alertas_log"
COL_ETL_LOG     = "etl_log"
SUBCOL_SERVICIOS = "servicios"

# Ruta para la base de datos local de respaldo / simulación
MOCK_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "local_db_mock.json"

def _cargar_mock_db() -> dict:
    """Carga la base de datos mock local desde un archivo JSON."""
    if not MOCK_DB_PATH.exists():
        MOCK_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Inicializar estructura vacía
        with open(MOCK_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump({"equipos": {}, "servicios": {}, "etl_log": [], "alertas_log": [], "alertas": {}}, f, indent=2, ensure_ascii=False)
    try:
        with open(MOCK_DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"equipos": {}, "servicios": {}, "etl_log": [], "alertas_log": [], "alertas": {}}

def _guardar_mock_db(data: dict):
    """Guarda la base de datos mock local en el archivo JSON."""
    try:
        with open(MOCK_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error guardando base de datos mock local: {e}")

# ── EQUIPOS ──────────────────────────────────────────────────────

def upsert_equipo(codigo: str, datos: dict) -> None:
    """
    Inserta o actualiza un equipo usando su codigo_equipo como ID de documento.
    Soporta fallback local.
    """
    datos["updated_at"] = datetime.utcnow().isoformat()
    
    if firestore_disponible():
        db = get_db()
        ref = db.collection(COL_EQUIPOS).document(codigo)
        ref.set(datos, merge=True)
    else:
        db_local = _cargar_mock_db()
        eq_existente = db_local["equipos"].get(codigo, {})
        # Combinar emulando merge=True
        eq_existente.update(datos)
        db_local["equipos"][codigo] = eq_existente
        _guardar_mock_db(db_local)

def get_equipo(codigo: str) -> Optional[dict]:
    """Retorna el documento del equipo o None si no existe."""
    if firestore_disponible():
        db = get_db()
        doc = db.collection(COL_EQUIPOS).document(codigo).get()
        return doc.to_dict() if doc.exists else None
    else:
        db_local = _cargar_mock_db()
        eq = db_local["equipos"].get(codigo)
        if eq:
            return {"id": codigo, **eq}
        return None

def get_all_equipos(solo_activos: bool = True) -> list[dict]:
    """Retorna lista de todos los equipos. Si solo_activos=True, filtra activo==True."""
    if firestore_disponible():
        db = get_db()
        query = db.collection(COL_EQUIPOS)
        if solo_activos:
            query = query.where("activo", "==", True)
        return [{"id": d.id, **d.to_dict()} for d in query.stream()]
    else:
        db_local = _cargar_mock_db()
        equipos = []
        for k, v in db_local["equipos"].items():
            if not solo_activos or v.get("activo", True) == True:
                equipos.append({"id": k, **v})
        return equipos

def limpiar_equipos() -> int:
    """
    Elimina todos los documentos de la colección equipos (y sus subcolecciones).
    Retorna el número de documentos eliminados.
    """
    if firestore_disponible():
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
    else:
        db_local = _cargar_mock_db()
        count = len(db_local["equipos"]) + len(db_local["servicios"])
        db_local["equipos"] = {}
        db_local["servicios"] = {}
        db_local["alertas"] = {}
        _guardar_mock_db(db_local)
        return count

# ── SERVICIOS (subcolección) ──────────────────────────────────────

def agregar_servicio(codigo_equipo: str, servicio: dict) -> str:
    """
    Agrega un documento a la subcolección servicios del equipo indicado.
    Retorna el ID autogenerado del documento.
    """
    servicio["created_at"] = datetime.utcnow().isoformat()
    
    if firestore_disponible():
        db = get_db()
        ref = db.collection(COL_EQUIPOS).document(codigo_equipo)\
                .collection(SUBCOL_SERVICIOS).document()
        ref.set(servicio)
        return ref.id
    else:
        db_local = _cargar_mock_db()
        srv_id = str(uuid.uuid4())
        servicio["codigo_equipo"] = codigo_equipo
        servicio["id"] = srv_id
        db_local["servicios"][srv_id] = servicio
        _guardar_mock_db(db_local)
        return srv_id

def get_servicios_equipo(codigo_equipo: str) -> list[dict]:
    """Retorna todos los servicios de un equipo, ordenados por fecha descendente."""
    if firestore_disponible():
        db = get_db()
        docs = db.collection(COL_EQUIPOS).document(codigo_equipo)\
                 .collection(SUBCOL_SERVICIOS)\
                 .order_by("fecha_servicio_vigente", direction=get_db().Query.DESCENDING)\
                 .stream()
        return [{"id": d.id, **d.to_dict()} for d in docs]
    else:
        db_local = _cargar_mock_db()
        servicios = [v for v in db_local["servicios"].values() if v.get("codigo_equipo") == codigo_equipo]
        # Ordenar por fecha descendente
        servicios.sort(key=lambda x: x.get("fecha_servicio_vigente") or "", reverse=True)
        return servicios

def get_ultimo_servicio(codigo_equipo: str, tipo_servicio: str = None) -> Optional[dict]:
    """
    Retorna el servicio más reciente del equipo.
    Si se especifica tipo_servicio, filtra solo ese tipo.
    """
    if firestore_disponible():
        try:
            from google.cloud import firestore
            db = get_db()
            query = db.collection(COL_EQUIPOS).document(codigo_equipo)\
                      .collection(SUBCOL_SERVICIOS)
            if tipo_servicio:
                query = query.where("tipo_servicio", "==", tipo_servicio)
            query = query.order_by("fecha_servicio_vigente",
                                   direction=firestore.Query.DESCENDING).limit(1)
            docs = list(query.stream())
            return {"id": docs[0].id, **docs[0].to_dict()} if docs else None
        except Exception:
            return None
    else:
        servicios = get_servicios_equipo(codigo_equipo)
        if tipo_servicio:
            servicios = [s for s in servicios if s.get("tipo_servicio") == tipo_servicio]
        return servicios[0] if servicios else None

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
    """
    if firestore_disponible():
        from google.api_core.exceptions import FailedPrecondition
        from src.database.exceptions import FirestoreIndexError
        import re

        db = get_db()
        if anio > 0:
            query = db.collection_group(SUBCOL_SERVICIOS).where("anio", "==", anio)
        else:
            query = db.collection_group(SUBCOL_SERVICIOS)
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

        if ubicacion:
            servicios = [s for s in servicios if s.get("ubicacion") == ubicacion]
        return servicios
    else:
        db_local = _cargar_mock_db()
        servicios = []
        for v in db_local["servicios"].values():
            if anio <= 0 or v.get("anio") == anio:
                if not ubicacion or v.get("ubicacion") == ubicacion:
                    servicios.append(v)
        return servicios

def marcar_alerta_resuelta_repo(alerta_id: str) -> bool:
    """
    Marca una alerta como leída (resuelta) y registra la transacción en el histórico alertas_log.
    """
    resueltas_en = datetime.utcnow().isoformat()
    
    if firestore_disponible():
        db = get_db()
        try:
            doc_ref = db.collection("alertas").document(alerta_id)
            doc = doc_ref.get()
            if not doc.exists:
                return False
            
            data = doc.to_dict()
            if data.get("leida") == True:
                return True
                
            # Calcular días transcurridos
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
            
            doc_ref.update({
                "leida": True,
                "resuelta_en": resueltas_en,
                "dias_respuesta": dias_respuesta
            })
            
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
    else:
        db_local = _cargar_mock_db()
        alerta = db_local.get("alertas", {}).get(alerta_id)
        if not alerta:
            return False
        if alerta.get("leida") == True:
            return True
            
        generada_en_str = alerta.get("generada_en") or alerta.get("created_at")
        dias_respuesta = None
        if generada_en_str:
            try:
                t_gen = datetime.fromisoformat(generada_en_str.replace("Z", "+00:00"))
                t_res = datetime.fromisoformat(resueltas_en)
                dias_respuesta = round((t_res - t_gen).total_seconds() / 86400.0, 2)
            except Exception:
                pass
                
        alerta["leida"] = True
        alerta["resuelta_en"] = resueltas_en
        alerta["dias_respuesta"] = dias_respuesta
        db_local["alertas"][alerta_id] = alerta
        
        log_entrada = {
            "alerta_id": alerta_id,
            "codigo_equipo": alerta.get("codigo_equipo"),
            "nombre_equipo": alerta.get("nombre_equipo"),
            "area": alerta.get("ubicacion"),
            "tipo_alerta": alerta.get("prioridad"),
            "nivel_prioridad": alerta.get("prioridad"),
            "generada_en": generada_en_str,
            "resuelta_en": resueltas_en,
            "dias_respuesta": dias_respuesta,
            "tipo_servicio": alerta.get("tipo_servicio")
        }
        db_local["alertas_log"].append({
            "id": str(uuid.uuid4()),
            "fecha_envio": resueltas_en,
            **log_entrada
        })
        _guardar_mock_db(db_local)
        return True

def get_metricas_alertas() -> dict:
    """
    Calcula métricas agregadas del histórico de alertas_log.
    """
    if firestore_disponible():
        db = get_db()
        docs = db.collection(COL_ALERTAS_LOG).stream()
        datos = [{"id": d.id, **d.to_dict()} for d in docs]
    else:
        db_local = _cargar_mock_db()
        datos = db_local["alertas_log"]
        
    resueltas = 0
    suma_dias = 0.0
    prioridades = {}
    
    for data in datos:
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
    log["fecha_carga"] = datetime.utcnow().isoformat()
    
    if firestore_disponible():
        db = get_db()
        ref = db.collection(COL_ETL_LOG).document()
        ref.set(log)
        return ref.id
    else:
        db_local = _cargar_mock_db()
        log_id = str(uuid.uuid4())
        log["id"] = log_id
        db_local["etl_log"].append(log)
        _guardar_mock_db(db_local)
        return log_id

def get_historial_etl(limite: int = 20) -> list[dict]:
    """Retorna los últimos N registros de carga ETL."""
    if firestore_disponible():
        db = get_db()
        docs = db.collection(COL_ETL_LOG)\
                 .order_by("fecha_carga", direction=firestore.Query.DESCENDING)\
                 .limit(limite).stream()
        return [{"id": d.id, **d.to_dict()} for d in docs]
    else:
        db_local = _cargar_mock_db()
        logs = db_local["etl_log"]
        logs.sort(key=lambda x: x.get("fecha_carga") or "", reverse=True)
        return logs[:limite]

def registrar_alerta(log: dict) -> str:
    """Guarda un registro de alerta enviada en la colección alertas_log."""
    log["fecha_envio"] = datetime.utcnow().isoformat()
    
    if firestore_disponible():
        db = get_db()
        ref = db.collection(COL_ALERTAS_LOG).document()
        ref.set(log)
        return ref.id
    else:
        db_local = _cargar_mock_db()
        log_id = str(uuid.uuid4())
        log["id"] = log_id
        db_local["alertas_log"].append(log)
        _guardar_mock_db(db_local)
        return log_id

def get_historial_alertas(limite: int = 30) -> list[dict]:
    """Retorna los últimos N registros de alertas enviadas."""
    if firestore_disponible():
        db = get_db()
        docs = db.collection(COL_ALERTAS_LOG)\
                 .order_by("fecha_envio", direction=firestore.Query.DESCENDING)\
                 .limit(limite).stream()
        return [{"id": d.id, **d.to_dict()} for d in docs]
    else:
        db_local = _cargar_mock_db()
        logs = db_local["alertas_log"]
        logs.sort(key=lambda x: x.get("fecha_envio") or "", reverse=True)
        return logs[:limite]
