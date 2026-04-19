"""
tests/test_engine.py
──────────────────────────────────────────────────────────────────────────────
Pruebas unitarias para el motor de cronograma (scheduler/engine.py y frequency_parser.py).
No requieren conexión a Supabase.
──────────────────────────────────────────────────────────────────────────────
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scheduler.frequency_parser import frecuencia_a_dias
from scheduler.engine import calcular_fecha_proximo, _clasificar_alerta


# ──────────────────────────────────────────────────────────────────────────────
# Tests de frecuencia_a_dias
# ──────────────────────────────────────────────────────────────────────────────

class TestFrecuenciaADias:
    def test_anual(self):
        assert frecuencia_a_dias("Anual") == 365

    def test_semestral(self):
        assert frecuencia_a_dias("Semestral") == 182

    def test_trimestral(self):
        assert frecuencia_a_dias("Trimestral") == 91

    def test_bimestral(self):
        assert frecuencia_a_dias("Bimestral") == 60

    def test_mensual(self):
        assert frecuencia_a_dias("Mensual") == 30

    def test_case_insensitive(self):
        assert frecuencia_a_dias("anual") == 365
        assert frecuencia_a_dias("SEMESTRAL") == 182

    def test_alias_6_meses(self):
        assert frecuencia_a_dias("6 meses") == 182

    def test_alias_12_meses(self):
        assert frecuencia_a_dias("12 meses") == 365

    def test_alias_3_meses(self):
        assert frecuencia_a_dias("3 meses") == 91

    def test_none_retorna_none(self):
        assert frecuencia_a_dias(None) is None

    def test_desconocido_retorna_none(self):
        assert frecuencia_a_dias("Quincenal") is None


# ──────────────────────────────────────────────────────────────────────────────
# Tests de calcular_fecha_proximo
# ──────────────────────────────────────────────────────────────────────────────

class TestCalcularFechaProximo:
    def test_anual_desde_inicio_año(self):
        fecha = calcular_fecha_proximo("2024-01-15", 365)
        assert fecha == date(2025, 1, 15)

    def test_semestral(self):
        fecha = calcular_fecha_proximo("2024-06-01", 182)
        assert fecha == date(2024, 6, 1) + timedelta(days=182)

    def test_fecha_none_retorna_none(self):
        assert calcular_fecha_proximo(None, 365) is None

    def test_frecuencia_none_retorna_none(self):
        assert calcular_fecha_proximo("2024-01-01", None) is None

    def test_fecha_invalida_retorna_none(self):
        assert calcular_fecha_proximo("no-es-fecha", 365) is None


# ──────────────────────────────────────────────────────────────────────────────
# Tests de _clasificar_alerta
# ──────────────────────────────────────────────────────────────────────────────

class TestClasificarAlerta:
    def test_vencido_negativo(self):
        assert _clasificar_alerta(-1) == "VENCIDO"
        assert _clasificar_alerta(-90) == "VENCIDO"

    def test_critico_0_a_15(self):
        assert _clasificar_alerta(0) == "CRITICO"
        assert _clasificar_alerta(7) == "CRITICO"
        assert _clasificar_alerta(15) == "CRITICO"

    def test_proximo_16_a_30(self):
        assert _clasificar_alerta(16) == "PROXIMO"
        assert _clasificar_alerta(25) == "PROXIMO"
        assert _clasificar_alerta(30) == "PROXIMO"

    def test_al_dia_mayor_30(self):
        assert _clasificar_alerta(31) == "AL_DIA"
        assert _clasificar_alerta(180) == "AL_DIA"
        assert _clasificar_alerta(365) == "AL_DIA"

    def test_sin_datos_para_none(self):
        assert _clasificar_alerta(None) == "SIN_DATOS"


# ──────────────────────────────────────────────────────────────────────────────
# Test de integración local (sin BD) — flujo completo de un equipo
# ──────────────────────────────────────────────────────────────────────────────

def test_flujo_completo_clasificacion():
    """
    Simula el flujo completo del scheduler para un equipo:
    fecha_vigente + frecuencia → fecha_próxima → días → estado_alerta
    """
    from datetime import date

    hoy = date.today()

    # Caso: equipo con calibración anual hace 350 días → CRITICO (quedan 15d)
    fecha_vigente = (hoy - timedelta(days=350)).isoformat()
    freq_dias = frecuencia_a_dias("Anual")  # 365
    fecha_proximo = calcular_fecha_proximo(fecha_vigente, freq_dias)
    dias = (fecha_proximo - hoy).days
    estado = _clasificar_alerta(dias)

    assert estado == "CRITICO"
    assert 0 <= dias <= 15

    # Caso: equipo con calibración anual hace 400 días → VENCIDO
    fecha_vigente_2 = (hoy - timedelta(days=400)).isoformat()
    fecha_proximo_2 = calcular_fecha_proximo(fecha_vigente_2, freq_dias)
    dias_2 = (fecha_proximo_2 - hoy).days
    estado_2 = _clasificar_alerta(dias_2)

    assert estado_2 == "VENCIDO"
    assert dias_2 < 0
