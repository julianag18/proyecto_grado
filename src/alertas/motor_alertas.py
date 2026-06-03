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

def generar_alertas() -> List[Alerta]:
    """
    Consulta Firestore, obtiene el estado actual de todos los equipos
    y genera una lista de alertas priorizadas.

    Prioridades:
    - CRITICA: vencido (dias_restantes < 0) o vence en ≤ 7 días
    - ALTA:    vence entre 8 y 15 días
    - MEDIA:   vence entre 16 y 30 días
    """
    equipos = get_estado_actual_todos()
    alertas = []

    for eq in equipos:
        dias = eq.get("dias_restantes")
        if dias is None:
            continue

        if dias < 0:
            prioridad = "CRITICA"
            mensaje = (f"VENCIDO hace {abs(dias)} días — "
                       f"Tipo: {eq.get('tipo_servicio', 'N/A')} — "
                       f"Proveedor: {eq.get('proveedor', 'N/A')}")
        elif dias <= 7:
            prioridad = "CRITICA"
            mensaje = (f"Vence en {dias} días — "
                       f"Tipo: {eq.get('tipo_servicio', 'N/A')} — "
                       f"Acción inmediata requerida")
        elif dias <= 15:
            prioridad = "ALTA"
            mensaje = f"Vence en {dias} días — Programar servicio pronto"
        elif dias <= 30:
            prioridad = "MEDIA"
            mensaje = f"Vence en {dias} días — Pendiente de programar"
        else:
            continue  # sin alerta si queda más de 30 días

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
