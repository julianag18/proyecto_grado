"""
scheduler/engine.py
──────────────────────────────────────────────────────────────────────────────
Motor de cronograma para Firebase Firestore.
Lee todos los servicios de Firestore, calcula la fecha del próximo servicio,
los días restantes y el estado de alerta de cada equipo.
Actualiza los documentos correspondientes en la subcolección 'servicios'.

Reglas de clasificación de alertas:
  VENCIDO   → dias_restantes < 0
  CRITICO   → 0 ≤ dias_restantes ≤ 15
  PROXIMO   → 16 ≤ dias_restantes ≤ 30
  AL_DIA    → dias_restantes > 30
  SIN_DATOS → sin fecha_servicio_vigente o sin frecuencia_dias
──────────────────────────────────────────────────────────────────────────────
"""

from datetime import date, timedelta
from rich.console import Console
from rich.table import Table as RichTable

from db.client import get_firestore_client
from scheduler.frequency_parser import frecuencia_a_dias

console = Console()

# Umbrales de alerta en días
UMBRAL_CRITICO = 15
UMBRAL_PROXIMO = 30


def _clasificar_alerta(dias: int | None) -> str:
    """Clasifica el estado de alerta según los días restantes."""
    if dias is None:
        return "SIN_DATOS"
    if dias < 0:
        return "VENCIDO"
    if dias <= UMBRAL_CRITICO:
        return "CRITICO"
    if dias <= UMBRAL_PROXIMO:
        return "PROXIMO"
    return "AL_DIA"


def calcular_fecha_proximo(fecha_vigente: str | None, frecuencia_dias: int | None) -> date | None:
    """
    Calcula la fecha del próximo servicio.
    """
    if not fecha_vigente or not frecuencia_dias:
        return None
    try:
        d = date.fromisoformat(str(fecha_vigente))
        return d + timedelta(days=frecuencia_dias)
    except (ValueError, TypeError):
        return None


def ejecutar(verbose: bool = True) -> dict:
    """
    Ejecuta el motor de cronograma:
      1. Lee todos los equipos y sus subcolecciones de servicios de Firestore.
      2. Calcula fecha_proximo_servicio y dias_restantes.
      3. Clasifica estado_alerta.
      4. Actualiza los documentos en Firestore (solo si hubo cambios).
      5. Retorna un resumen de métricas.
    """
    db = get_firestore_client()
    hoy = date.today()

    console.print(f"\n[bold blue]⏰ Motor de Cronograma PAME[/bold blue] — {hoy.isoformat()}")

    metricas = {
        "total": 0,
        "al_dia": 0,
        "proximos": 0,
        "criticos": 0,
        "vencidos": 0,
        "sin_datos": 0,
        "actualizados": 0,
        "errores": 0,
    }

    if db is None:
        console.print("[yellow]  ⚠ Modo Demo activo: omitiendo ejecución del cronograma en Firestore[/yellow]")
        return metricas

    try:
        # Obtener todos los equipos
        equipos_ref = db.collection("equipos").stream()
        
        for eq_doc in equipos_ref:
            codigo_equipo = eq_doc.id
            
            # Obtener servicios del equipo
            servicios_ref = db.collection("equipos").document(codigo_equipo).collection("servicios").stream()
            
            for srv_doc in servicios_ref:
                metricas["total"] += 1
                srv_data = srv_doc.to_dict()
                srv_id = srv_doc.id
                
                # Resolver frecuencia_dias si no está guardada
                freq_dias = srv_data.get("frecuencia_dias")
                frecuencia = srv_data.get("frecuencia")
                if not freq_dias and frecuencia:
                    freq_dias = frecuencia_a_dias(frecuencia)
                
                # Calcular fecha próxima
                fecha_vigente = srv_data.get("fecha_servicio_vigente")
                fecha_proximo = calcular_fecha_proximo(fecha_vigente, freq_dias)
                
                # Calcular días restantes
                if fecha_proximo:
                    dias_restantes = (fecha_proximo - hoy).days
                else:
                    dias_restantes = None
                
                # Clasificar alerta
                estado_alerta = _clasificar_alerta(dias_restantes)
                metricas[estado_alerta.lower()] += 1
                
                # Preparar campos a actualizar
                actualizacion = {
                    "frecuencia_dias": freq_dias,
                    "fecha_proximo_servicio": fecha_proximo.isoformat() if fecha_proximo else None,
                    "dias_restantes": dias_restantes,
                    "estado_alerta": estado_alerta,
                }
                
                # Detectar si hay cambios reales para evitar escrituras redundantes
                necesita_actualizacion = False
                for k, v in actualizacion.items():
                    if srv_data.get(k) != v:
                        necesita_actualizacion = True
                        break
                
                if necesita_actualizacion:
                    try:
                        db.collection("equipos").document(codigo_equipo)\
                          .collection("servicios").document(srv_id)\
                          .update(actualizacion)
                        metricas["actualizados"] += 1
                    except Exception as e:
                        metricas["errores"] += 1
                        console.print(f"[red]  ✗ Error actualizando servicio {srv_id} del equipo {codigo_equipo}: {e}[/red]")
        
        # Mostrar resumen
        if verbose and metricas["total"] > 0:
            t = RichTable(title="📅 Resumen de Cronograma PAME (Firestore)", show_header=True)
            t.add_column("Estado", style="bold")
            t.add_column("Cantidad", justify="right")
            t.add_column("% del total", justify="right")
            total = metricas["total"] or 1

            filas = [
                ("🟢 AL DÍA",     "al_dia",    "green"),
                ("🟡 PRÓXIMOS",   "proximos",  "yellow"),
                ("🟠 CRÍTICOS",   "criticos",  "dark_orange"),
                ("🔴 VENCIDOS",   "vencidos",  "red"),
                ("⚪ SIN DATOS",  "sin_datos", "dim"),
            ]
            for label, clave, color in filas:
                cant = metricas[clave]
                pct = f"{cant / total * 100:.1f}%"
                t.add_row(label, str(cant), pct, style=color)

            console.print(t)
            console.print(
                f"[dim]  Actualizados: {metricas['actualizados']}  |  "
                f"Errores: {metricas['errores']}[/dim]"
            )

    except Exception as e:
        console.print(f"[red]✗ Error general en motor de cronograma: {e}[/red]")
        
    return metricas
