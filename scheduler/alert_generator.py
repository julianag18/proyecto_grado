"""
scheduler/alert_generator.py
──────────────────────────────────────────────────────────────────────────────
Generador de alertas: lee el estado_alerta calculado por engine.py y escribe
registros detallados en la tabla 'alertas'.
Omite duplicar alertas que ya existen para el mismo servicio.
──────────────────────────────────────────────────────────────────────────────
"""

from datetime import datetime, timezone

from rich.console import Console

from db.client import get_client

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
        nombre=datos.get("nombre_equipo", ""),
        dias=datos.get("dias_restantes", 0),
        abs_dias=abs(datos.get("dias_restantes", 0) or 0),
        fecha=datos.get("fecha_proximo_servicio", "?"),
        estado=estado,
    )


def generar_alertas(limpiar_anteriores: bool = False) -> dict:
    """
    Lee todos los servicios con estado de alerta VENCIDO, CRITICO o PROXIMO
    y crea los registros correspondientes en la tabla 'alertas'.

    Parámetros
    ----------
    limpiar_anteriores : bool
        Si True, elimina todas las alertas no leídas antes de regenerar.
        Útil para ejecuciones programadas.

    Retorna
    -------
    dict con métricas: nuevas_alertas, omitidas, errores
    """
    cliente = get_client()
    console.print("\n[bold blue]🔔 Generando alertas...[/bold blue]")

    # ── Opcional: limpiar alertas no leídas anteriores ─────────────────────────
    if limpiar_anteriores:
        try:
            cliente.table("alertas").delete().eq("leida", False).execute()
            console.print("[dim]  Alertas anteriores no leídas eliminadas[/dim]")
        except Exception as e:
            console.print(f"[yellow]  ⚠ No se pudo limpiar alertas anteriores: {e}[/yellow]")

    # ── Leer servicios en estado de alerta relevante ───────────────────────────
    respuesta = (
        cliente.table("servicios")
        .select(
            "id, equipo_id, codigo_equipo, nombre_equipo, tipo_servicio, "
            "dias_restantes, estado_alerta, fecha_proximo_servicio"
        )
        .in_("estado_alerta", ["VENCIDO", "CRITICO", "PROXIMO"])
        .execute()
    )
    servicios = respuesta.data or []
    console.print(f"[cyan]  {len(servicios)} servicio(s) requieren alerta[/cyan]")

    metricas = {"nuevas_alertas": 0, "omitidas": 0, "errores": 0}

    # ── Obtener alertas ya existentes (para evitar duplicados) ─────────────────
    resp_existentes = (
        cliente.table("alertas")
        .select("servicio_id")
        .eq("leida", False)
        .execute()
    )
    ids_con_alerta = {r["servicio_id"] for r in (resp_existentes.data or [])}

    # ── Generar nuevas alertas ─────────────────────────────────────────────────
    for srv in servicios:
        sid = srv["id"]

        # Omitir si ya tiene alerta no leída (salvo que se hayan limpiado)
        if not limpiar_anteriores and sid in ids_con_alerta:
            metricas["omitidas"] += 1
            continue

        estado = srv.get("estado_alerta", "SIN_DATOS")
        mensaje = _construir_mensaje(estado, srv)

        alerta = {
            "equipo_id": srv.get("equipo_id"),
            "servicio_id": sid,
            "tipo_alerta": f"SERVICIO_{estado}",
            "nivel_prioridad": _PRIORIDAD.get(estado, "baja"),
            "mensaje": mensaje,
            "leida": False,
            "generada_en": datetime.now(timezone.utc).isoformat(),
        }

        try:
            cliente.table("alertas").insert(alerta).execute()
            metricas["nuevas_alertas"] += 1
        except Exception as e:
            metricas["errores"] += 1
            console.print(f"[red]  ✗ Error insertando alerta para {sid}: {e}[/red]")

    console.print(
        f"[green]  ✓ Nuevas alertas: {metricas['nuevas_alertas']}[/green]  "
        f"[dim]Omitidas: {metricas['omitidas']}  |  "
        f"Errores: {metricas['errores']}[/dim]"
    )
    return metricas
