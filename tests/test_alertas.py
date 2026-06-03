"""
Pruebas unitarias para el motor de alertas y el generador de correos.
Valida la clasificación, agrupación y generación del HTML.
"""
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.alertas.motor_alertas import Alerta, agrupar_por_area, generar_alertas
from src.alertas.email_sender import generar_html_alerta, enviar_alerta_diaria, enviar_alerta_critica_inmediata


def test_priorizacion_alertas():
    """Valida la clasificación de prioridades en base a los días restantes."""
    # Simular una lista de alertas manuales
    a1 = Alerta("EQ1", "Equipo 1", "Planta", "PROV", "Calibración", "2026-01-01", -5, "CRITICA", "vencido")
    a2 = Alerta("EQ2", "Equipo 2", "Planta", "PROV", "Calibración", "2026-01-01", 3, "CRITICA", "vence pronto")
    a3 = Alerta("EQ3", "Equipo 3", "Planta", "PROV", "Calibración", "2026-01-01", 10, "ALTA", "vence pronto")
    a4 = Alerta("EQ4", "Equipo 4", "Planta", "PROV", "Calibración", "2026-01-01", 20, "MEDIA", "vence pronto")
    
    assert a1.prioridad == "CRITICA"
    assert a2.prioridad == "CRITICA"
    assert a3.prioridad == "ALTA"
    assert a4.prioridad == "MEDIA"


def test_agrupar_por_area():
    """Valida la agrupación por áreas físicas de la planta."""
    a1 = Alerta("EQ1", "Equipo 1", "CONTROL CALIDAD", "PROV", "Calibración", "2026-01-01", -5, "CRITICA", "")
    a2 = Alerta("EQ2", "Equipo 2", "METROLOGÍA", "PROV", "Calibración", "2026-01-01", 3, "CRITICA", "")
    a3 = Alerta("EQ3", "Equipo 3", "CONTROL CALIDAD", "PROV", "Calibración", "2026-01-01", 10, "ALTA", "")
    
    alertas = [a1, a2, a3]
    grupos = agrupar_por_area(alertas)
    
    assert "CONTROL CALIDAD" in grupos
    assert "METROLOGÍA" in grupos
    assert len(grupos["CONTROL CALIDAD"]) == 2
    assert len(grupos["METROLOGÍA"]) == 1


def test_generar_html_alerta():
    """Valida la estructura del HTML del correo de alertas."""
    a1 = Alerta("EQ1", "Balanza 1", "CONTROL CALIDAD", "LAPROFF", "Calibración", "2026-01-15", -5, "CRITICA", "Vencido hace 5 días")
    a2 = Alerta("EQ2", "Balanza 2", "CONTROL CALIDAD", "LAPROFF", "Calibración", "2026-02-15", 10, "ALTA", "Vence en 10 días")
    
    alertas = [a1, a2]
    html = generar_html_alerta(alertas)
    
    # Validaciones en el HTML
    assert "<html>" in html
    assert "PAME — Aseguramiento Metrológico" in html
    assert "EQ1" in html
    assert "EQ2" in html
    assert "row-critica" in html
    assert "row-alta" in html
    assert "badge badge-critica" in html
    assert "badge badge-alta" in html


def test_enviar_alerta_diaria_simulada(monkeypatch):
    """Valida la ejecución del envío diario en consola (fallback/dry-run)."""
    # Deshabilitar variables de entorno de correo real para asegurar modo consola
    monkeypatch.setenv("SMTP_HOST", "")
    monkeypatch.setenv("SMTP_USER", "")
    monkeypatch.setenv("SMTP_PASSWORD", "")
    
    a1 = Alerta("EQ1", "Balanza 1", "CONTROL CALIDAD", "LAPROFF", "Calibración", "2026-01-15", -5, "CRITICA", "Vencido")
    alertas = [a1]
    
    # Ejecutar en consola
    log = enviar_alerta_diaria(alertas, force_console=True)
    
    assert log["tipo"] == "diaria"
    assert log["total_alertas"] == 1
    assert log["exito"] is True
    assert "EQ1" in log["equipos_alertados"]


def test_enviar_alerta_critica_inmediata_simulada(monkeypatch):
    """Valida la ejecución de alertas críticas en consola (fallback/dry-run)."""
    monkeypatch.setenv("SMTP_HOST", "")
    monkeypatch.setenv("SMTP_USER", "")
    monkeypatch.setenv("SMTP_PASSWORD", "")
    
    a1 = Alerta("EQ1", "Balanza 1", "CONTROL CALIDAD", "LAPROFF", "Calibración", "2026-01-15", -5, "CRITICA", "Vencido")
    
    log = enviar_alerta_critica_inmediata(a1, force_console=True)
    
    assert log["tipo"] == "critica_inmediata"
    assert log["total_alertas"] == 1
    assert log["exito"] is True
    assert "EQ1" in log["equipos_alertados"]
