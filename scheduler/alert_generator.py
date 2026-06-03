"""
scheduler/alert_generator.py
──────────────────────────────────────────────────────────────────────────────
Generador de alertas para Firebase Firestore.
Lee el estado_alerta calculado de los servicios y crea registros
en la colección 'alertas'.
Omite duplicar alertas que ya existen y no han sido leídas.
──────────────────────────────────────────────────────────────────────────────
"""

from datetime import datetime, timezone
from rich.console import Console
from db.client import get_firestore_client

console = Console()

# Plantillas de mensajes por tipo de alerta
_MENSAJES = {
    "VENCIDO": (
        "⚠ VENCIDO: El servicio de {tipo} para el equipo [{codigo}] {nombre} "
        "venció hace {abs_dias} día(s). Requiere acción inmediata."
    ),
    "CRITICO": (
        "🔴 CRÍTICO: El servicio de {tipo} para [{codigo}] {nombre} vence "
        "en {dias} día(s) ({fecha}). Prioridad alta."
    ),
    "PROXIMO": (
        "🟡 PRÓXIMO: El servicio de {tipo} para [{codigo}] {nombre} vence "
        "en {dias} día(s) ({fecha}). Planifique con anticipación."
    ),
}

_PRIORIDAD = {
    "VENCIDO": "alta",
    "CRITICO": "alta",
    "PROXIMO": "media",
    "AL_DIA":  "baja",
}


def _construir_mensaje(estado: str, datos: dict) -> str:
    """Genera el mensaje de alerta según la plantilla correspondiente."""
    plantilla = _MENSAJES.get(estado, "Estado: {estado} para equipo [{codigo}]")
    return plantilla.format(
        tipo=datos.get("tipo_servicio", "N/A"),
        codigo=datos.get("codigo_equipo", "?"),
        nombre=datos.get("nombre_equipo") or datos.get("nombre") or "",
        dias=datos.get("dias_restantes", 0),
        abs_dias=abs(datos.get("dias_restantes", 0) or 0),
        fecha=datos.get("fecha_proximo_servicio", "?"),
        estado=estado,
    )


def generar_alertas(limpiar_anteriores: bool = False) -> dict:
    """
    Busca todos los servicios en Firestore con estado de alerta VENCIDO, CRITICO o PROXIMO
    y crea los registros correspondientes en la colección 'alertas'.
    """
    db = get_firestore_client()
    console.print("\n[bold blue]🔔 Generando alertas...[/bold blue]")

    metricas = {"nuevas_alertas": 0, "omitidas": 0, "errores": 0}

    if db is None:
        console.print("[yellow]  ⚠ Modo Demo activo: omitiendo generación de alertas en Firestore[/yellow]")
        return metricas

    # ── 1. Limpiar alertas anteriores no leídas si se solicita ─────────────────
    if limpiar_anteriores:
        try:
            unread_ref = db.collection("alertas").where("leida", "==", False).stream()
            deleted_count = 0
            for doc in unread_ref:
                doc.reference.delete()
                deleted_count += 1
            if deleted_count > 0:
                console.print(f"[dim]  Se eliminaron {deleted_count} alerta(s) anterior(es) no leída(s)[/dim]")
        except Exception as e:
            console.print(f"[yellow]  ⚠ No se pudo limpiar alertas anteriores: {e}[/yellow]")

    # ── 2. Obtener servicios que requieren alerta (Index-Safe) ─────────────────
    servicios = []
    try:
        # Intento 1: Collection Group query (más rápido, requiere índice compuesto)
        srv_docs = db.collection_group("servicios").where("estado_alerta", "in", ["VENCIDO", "CRITICO", "PROXIMO"]).stream()
        for doc in srv_docs:
            data = doc.to_dict()
            data["id"] = doc.id
            # Obtener el código de equipo del documento padre
            parent_ref = doc.reference.parent.parent
            data["codigo_equipo"] = parent_ref.id
            servicios.append(data)
    except Exception as e:
        # Intento 2: Fallback manual (seguro de indexación, recorre todos los equipos)
        console.print("[yellow]  ⚠ Collection Group falló (posible falta de índice). Ejecutando escaneo manual seguro...[/yellow]")
        try:
            equipos_ref = db.collection("equipos").stream()
            for eq_doc in equipos_ref:
                eq_id = eq_doc.id
                eq_data = eq_doc.to_dict()
                
                # Consultar la subcolección de servicios filtrando por estado_alerta
                srvs_ref = db.collection("equipos").document(eq_id).collection("servicios")\
                             .where("estado_alerta", "in", ["VENCIDO", "CRITICO", "PROXIMO"]).stream()
                for doc in srvs_ref:
                    data = doc.to_dict()
                    data["id"] = doc.id
                    data["codigo_equipo"] = eq_id
                    data["nombre_equipo"] = eq_data.get("nombre_equipo") or eq_data.get("nombre")
                    servicios.append(data)
        except Exception as exc_inner:
            console.print(f"[red]✗ Error en el escaneo manual de servicios: {exc_inner}[/red]")
            metricas["errores"] += 1
            return metricas

    console.print(f"[cyan]  {len(servicios)} servicio(s) requieren alerta[/cyan]")

    if not servicios:
        return metricas

    # ── 3. Obtener alertas ya existentes no leídas para evitar duplicar ────────
    ids_con_alerta = set()
    try:
        resp_existentes = db.collection("alertas").where("leida", "==", False).stream()
        for doc in resp_existentes:
            data = doc.to_dict()
            if data.get("servicio_id"):
                ids_con_alerta.add(data["servicio_id"])
    except Exception as e:
        console.print(f"[yellow]  ⚠ Error al buscar alertas existentes: {e}[/yellow]")

    # ── 4. Insertar nuevas alertas ─────────────────────────────────────────────
    for srv in servicios:
        sid = srv["id"]
        codigo_eq = srv.get("codigo_equipo")

        # Omitir si ya tiene una alerta no leída activa
        if not limpiar_anteriores and sid in ids_con_alerta:
            metricas["omitidas"] += 1
            continue

        estado = srv.get("estado_alerta", "SIN_DATOS")
        mensaje = _construir_mensaje(estado, srv)

        alerta = {
            "equipo_id": codigo_eq,
            "servicio_id": sid,
            "tipo_alerta": f"SERVICIO_{estado}",
            "nivel_prioridad": _PRIORIDAD.get(estado, "baja"),
            "mensaje": mensaje,
            "leida": False,
            "generada_en": datetime.now(timezone.utc).isoformat(),
        }

        try:
            db.collection("alertas").document().set(alerta)
            metricas["nuevas_alertas"] += 1
        except Exception as e:
            metricas["errores"] += 1
            console.print(f"[red]  ✗ Error insertando alerta para {sid} de {codigo_eq}: {e}[/red]")

    console.print(
        f"[green]  ✓ Nuevas alertas creadas: {metricas['nuevas_alertas']}[/green]  "
        f"[dim]Omitidas: {metricas['omitidas']}  |  "
        f"Errores: {metricas['errores']}[/dim]"
    )
    return metricas
