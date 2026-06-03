"""
Pruebas unitarias y de integración para el módulo ETL (extractor, transformer, loader y pipeline).
Usa los archivos de muestra en data/samples/ para las validaciones.
"""
import sys
from pathlib import Path
import pytest

# Asegurar que el root del proyecto esté en el path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.etl.extractor import extract, ExtractorError
from src.etl.transformer import transform, calcular_estado_servicio
from src.etl.loader import load
from src.etl.pipeline import run_pipeline

SAMPLE_CSV = ROOT_DIR / "data" / "samples" / "cronograma_sample.csv"
SAMPLE_JSON = ROOT_DIR / "data" / "samples" / "cronograma_historico.json"
SAMPLE_NUEVOS = ROOT_DIR / "data" / "samples" / "equipos_nuevos.csv"


# ── TEST EXTRACTOR ────────────────────────────────────────────────────────────

def test_extract_csv():
    """Valida la extracción del CSV de muestra."""
    registros, meta = extract(str(SAMPLE_CSV))
    assert meta["formato"] == "csv"
    assert meta["encoding_detectado"] in ("latin-1", "cp1252")
    assert meta["separador_detectado"] == ";"
    assert meta["total_registros"] == 55
    assert len(registros) == 55

def test_extract_json():
    """Valida la extracción del JSON de muestra."""
    registros, meta = extract(str(SAMPLE_JSON))
    assert meta["formato"] == "json"
    assert meta["estructura_detectada"] == "array_plano"
    assert meta["total_registros"] == 123
    assert len(registros) == 123

def test_extract_archivo_inexistente():
    """Valida el comportamiento con archivos que no existen."""
    with pytest.raises(ExtractorError):
        extract("data/samples/no_existe.csv")


# ── TEST TRANSFORMER ──────────────────────────────────────────────────────────

def test_transform_csv_data():
    """Valida el mapeo, limpieza, duplicidad y cálculo de estados de transformación."""
    registros_crudos, _ = extract(str(SAMPLE_CSV))
    validos, invalidos, reporte = transform(registros_crudos)

    # El CSV tiene:
    # 55 total filas: 50 únicas válidas, 3 duplicadas, 2 inválidas
    assert reporte["total_registros"] == 55
    assert len(validos) == 50
    assert len(invalidos) == 2
    assert reporte["duplicados_eliminados"] == 3

    # Validar campos normalizados de nulos
    # El primer equipo tiene "NO IDENTIFICADO" en Serie Equipo, debe quedar como None
    # y "NO IDENTIFICADO" en Activo Fijo
    assert validos[0]["activo_fijo"] is None
    
    # El segundo equipo tiene idx = 2, por lo que tiene "AF10-03600" en Activo Fijo
    assert validos[1]["activo_fijo"] == "AF10-03600"
    
    # Validar que los campos de fecha se transformen a ISO 8601 YYYY-MM-DD
    # "15/01/2026" -> "2026-01-15"
    assert validos[0]["fecha_servicio_vigente"] == "2026-01-15"
    
    # "01/2027" -> "2027-01-01"
    assert validos[0]["fecha_proximo_servicio"] == "2027-01-01"

    # Validar que se extraiga el año
    assert validos[0]["anio"] == 2026


def test_calcular_estado_servicio():
    """Prueba la lógica del cálculo de estado de servicio según días restantes."""
    from datetime import date, timedelta
    
    # Vencido
    vencido_date = (date.today() - timedelta(days=1)).isoformat()
    assert calcular_estado_servicio(vencido_date) == "Vencido"
    
    # Programar (vence en <= 30 días)
    programar_date = (date.today() + timedelta(days=15)).isoformat()
    assert calcular_estado_servicio(programar_date) == "Programar"
    
    # Vigente (vence en > 30 días)
    vigente_date = (date.today() + timedelta(days=45)).isoformat()
    assert calcular_estado_servicio(vigente_date) == "Vigente"
    
    # Nulo -> Vencido por defecto
    assert calcular_estado_servicio(None) == "Vencido"


# ── TEST LOADER Y PIPELINE (DRY-RUN) ──────────────────────────────────────────

def test_pipeline_dry_run():
    """Ejecuta el pipeline en modo simulación (dry-run) y valida que reporte exito sin fallas."""
    reporte = run_pipeline(str(SAMPLE_CSV), dry_run=True)
    
    assert "extraccion" in reporte
    assert "transformacion" in reporte
    assert "carga" in reporte
    
    assert reporte["carga"]["dry_run"] is True
    assert reporte["carga"]["insertados"] == 50
    assert len(reporte["carga"]["errores"]) == 0
