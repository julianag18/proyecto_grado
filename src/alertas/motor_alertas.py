"""
Motor de alertas para el PAME de Laproff.
Calcula prioridades de alertas y las agrupa por área.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional
from src.database.equipos_repo import get_estado_actual_todos

@dataclass
class Alerta:
    codigo_equipo:  str
    nombre_equipo:  str
    ubicacion:      str
    proveedor:      Optional[str]
    tipo_servicio:  Optional[str]
    fecha_proxima:  Optional[str]   # ISO 8601
    dias_restantes: Optional[int]   # negativo = ya venció
    prioridad:      str             # "CRITICA", "ALTA", "MEDIA"
    mensaje:        str

def obtener_umbrales_alerta(frecuencia: str) -> tuple[int, int, int]:
    """
    Retorna los umbrales de días (CRITICA, ALTA, MEDIA) según la frecuencia del servicio.
    Optimizado para dar suficiente tiempo logístico para agendar y ejecutar calibraciones.
    """
    frec = str(frecuencia).strip().lower()
    if frec in ["bienal", "trienal", "anual"]:
        return 15, 30, 45  # Metrología anual requiere más margen (compras, contratos)
    elif frec == "semestral":
        return 10, 20, 30
    elif frec in ["trimestral", "mensual"]:
        return 5, 10, 15
    else:
        return 7, 15, 30   # Umbrales por defecto

def generar_alertas() -> List[Alerta]:
    """
    Consulta Firestore, obtiene el estado actual de todos los equipos
    y genera una lista de alertas priorizadas.
    """
    equipos = get_estado_actual_todos()
    alertas = []

    for eq in equipos:
        dias = eq.get("dias_restantes")
        if dias is None:
            continue

        frecuencia = eq.get("frecuencia") or "Anual"
        u_critica, u_alta, u_media = obtener_umbrales_alerta(frecuencia)

        if dias < 0:
            prioridad = "CRITICA"
            mensaje = (f"VENCIDO hace {abs(dias)} días — "
                       f"Tipo: {eq.get('tipo_servicio', 'N/A')} — "
                       f"Proveedor: {eq.get('proveedor', 'N/A')}")
        elif dias <= u_critica:
            prioridad = "CRITICA"
            mensaje = (f"Vence en {dias} días — "
                       f"Tipo: {eq.get('tipo_servicio', 'N/A')} — "
                       f"Acción inmediata requerida")
        elif dias <= u_alta:
            prioridad = "ALTA"
            mensaje = f"Vence en {dias} días — Programar servicio pronto"
        elif dias <= u_media:
            prioridad = "MEDIA"
            mensaje = f"Vence en {dias} días — Pendiente de programar"
        else:
            continue  # sin alerta si queda más de lo parametrizado

        alertas.append(Alerta(
            codigo_equipo  = eq.get("id", ""),
            nombre_equipo  = eq.get("nombre_equipo", ""),
            ubicacion      = eq.get("ubicacion", "SIN UBICACIÓN"),
            proveedor      = eq.get("proveedor"),
            tipo_servicio  = eq.get("tipo_servicio"),
            fecha_proxima  = eq.get("fecha_proximo_servicio"),
            dias_restantes = dias,
            prioridad      = prioridad,
            mensaje        = mensaje,
        ))

    # Ordenar: primero las críticas, luego por días restantes ascendente
    alertas.sort(key=lambda a: (
        0 if a.prioridad == "CRITICA" else 1 if a.prioridad == "ALTA" else 2,
        a.dias_restantes if a.dias_restantes is not None else 999
    ))
    return alertas

def agrupar_por_area(alertas: List[Alerta]) -> dict[str, List[Alerta]]:
    """Agrupa alertas por área/ubicación para envío segmentado."""
    grupos = {}
    for alerta in alertas:
        area = alerta.ubicacion or "SIN ÁREA"
        grupos.setdefault(area, []).append(alerta)
    return grupos
