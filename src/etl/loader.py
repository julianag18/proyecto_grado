"""
Cargador ETL: toma registros transformados y los escribe en Firestore.
Separa cada registro en su parte de equipo (colección equipos)
y su parte de servicio (subcolección servicios).
"""
import time
from src.database.equipos_repo import upsert_equipo, agregar_servicio, registrar_carga_etl

# Campos que pertenecen al documento del equipo (datos maestros)
CAMPOS_EQUIPO = {
    "codigo_equipo", "nombre_equipo", "serie_equipo",
    "activo_fijo", "ubicacion", "activo"
}

# Campos que pertenecen al documento de servicio
CAMPOS_SERVICIO = {
    "tipo_servicio", "frecuencia", "fecha_servicio_vigente",
    "fecha_ejecucion_programada", "periodo_proximo_servicio",
    "fecha_proximo_servicio", "estado_servicio", "estado_entrega",
    "estado_conformidad", "proveedor", "anio", "campos_extra"
}

def load(registros_validos: list[dict], nombre_archivo: str,
         reporte_transform: dict, dry_run: bool = False) -> dict:
    """
    Carga los registros válidos a Firestore.
    Si dry_run=True, simula la carga sin escribir nada.
    Retorna reporte de carga.
    """
    inicio = time.time()
    insertados = 0
    actualizados = 0
    errores = []

    for reg in registros_validos:
        codigo = reg.get("codigo_equipo")
        if not codigo:
            continue

        # Separar datos de equipo vs datos de servicio
        datos_equipo = {k: v for k, v in reg.items() if k in CAMPOS_EQUIPO}
        datos_equipo.setdefault("activo", True)

        datos_servicio = {k: v for k, v in reg.items() if k in CAMPOS_SERVICIO}
        # Agregar referencia de ubicación al servicio para facilitar Collection Group queries
        datos_servicio["ubicacion"] = reg.get("ubicacion")

        if dry_run:
            insertados += 1
            continue

        try:
            upsert_equipo(codigo, datos_equipo)
            agregar_servicio(codigo, datos_servicio)
            insertados += 1
        except Exception as e:
            errores.append({"codigo": codigo, "error": str(e)})

    duracion = round(time.time() - inicio, 2)

    reporte_carga = {
        "archivo":              nombre_archivo,
        "dry_run":              dry_run,
        "insertados":           insertados,
        "actualizados":         actualizados,
        "errores":              errores,
        "duracion_segundos":    duracion,
        "reporte_transformacion": reporte_transform,
    }

    if not dry_run:
        try:
            registrar_carga_etl(reporte_carga)
        except Exception as e:
            print(f"Error registrando carga ETL en la base de datos: {e}")

    return reporte_carga
