"""
Pruebas de calidad y métricas del ETL procesando el archivo de muestra cronograma_sample.csv.
Valida la deduplicación, validación de registros inválidos, normalización de nulos y
conversión de fechas según las especificaciones del Bloque 5.
"""
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.etl.extractor import extract
from src.etl.transformer import transform

def test_calidad_cronograma_sample():
    """
    Verifica que al procesar cronograma_sample.csv:
    - Se detecten exactamente 3 duplicados.
    - Se detecten exactamente 2 registros inválidos.
    - Los campos 'NO REGISTRA' / 'NO IDENTIFICADO' se conviertan a None.
    - Las fechas se conviertan a ISO 8601.
    - El campo 'anio' se calcule correctamente.
    """
    csv_path = ROOT_DIR / "data" / "samples" / "cronograma_sample.csv"
    assert csv_path.exists(), f"No se encontró el archivo {csv_path}"

    # 1. Extraer registros
    registros_crudos, meta = extract(str(csv_path))
    assert len(registros_crudos) == 55, f"Se esperaban 55 registros crudos, se obtuvieron {len(registros_crudos)}"

    # 2. Transformar
    validos, invalidos, reporte = transform(registros_crudos)

    # 3. Verificar métricas del reporte de calidad
    assert reporte["duplicados_eliminados"] == 3, f"Se esperaban 3 duplicados eliminados, se obtuvieron {reporte['duplicados_eliminados']}"
    assert reporte["invalidos"] == 2, f"Se esperaban 2 registros inválidos, se obtuvieron {reporte['invalidos']}"
    assert len(validos) == 50, f"Se esperaban 50 registros válidos, se obtuvieron {len(validos)}"

    # 4. Verificar normalizaciones específicas en los válidos
    for v in validos:
        # Los campos 'NO REGISTRA', 'NO IDENTIFICADO', 'NO APLICA' se convierten a None
        assert v.get("activo_fijo") is None or not str(v.get("activo_fijo")).upper() in {"NO REGISTRA", "NO IDENTIFICADO", "NO APLICA"}, \
            f"El activo_fijo '{v.get('activo_fijo')}' no fue normalizado a None"
        assert v.get("serie_equipo") is None or not str(v.get("serie_equipo")).upper() in {"NO REGISTRA", "NO IDENTIFICADO", "NO APLICA"}, \
            f"La serie_equipo '{v.get('serie_equipo')}' no fue normalizado a None"

        # Las fechas deben ser formato ISO (YYYY-MM-DD) o None
        fecha_vig = v.get("fecha_servicio_vigente")
        if fecha_vig:
            assert len(fecha_vig) == 10 and fecha_vig[4] == '-' and fecha_vig[7] == '-', \
                f"La fecha vigente '{fecha_vig}' no está en formato ISO YYYY-MM-DD"
            
        fecha_prox = v.get("fecha_proximo_servicio")
        if fecha_prox:
            assert len(fecha_prox) == 10 and fecha_prox[4] == '-' and fecha_prox[7] == '-', \
                f"La fecha próxima '{fecha_prox}' no está en formato ISO YYYY-MM-DD"

        # El campo anio debe coincidir con el año de la fecha de servicio vigente
        if fecha_vig:
            assert v.get("anio") == int(fecha_vig[:4]), \
                f"El campo anio '{v.get('anio')}' no coincide con el año de la fecha vigente '{fecha_vig}'"

def test_campos_extra_json():
    """
    Verifica que los campos extra de un JSON se preserven en 'campos_extra' sin perderse.
    """
    json_path = ROOT_DIR / "data" / "samples" / "cronograma_historico.json"
    assert json_path.exists(), f"No se encontró el archivo {json_path}"

    registros_crudos, meta = extract(str(json_path))
    
    # Agregar un campo ficticio a un registro de prueba y pasarlo por transform
    registro_prueba = {
        "Código del Equipo": "EQ-EXTRA-99",
        "Equipo": "Balanza de Precisión",
        "Ubicación": "CONTROL CALIDAD",
        "Tipo de Servicio": "Calibración",
        "Frecuencia": "Anual",
        "Período Próximo Servicio": "12/2026",
        "CampoInventado1": "ValorEspecial1",
        "TemperaturaAmbiente": 23.5
    }

    validos, invalidos, reporte = transform([registro_prueba])
    assert len(validos) == 1
    v = validos[0]
    
    # Verificar que los campos no reconocidos se guarden en campos_extra
    assert "campos_extra" in v, "No se generó el diccionario 'campos_extra'"
    assert v["campos_extra"].get("CampoInventado1") == "ValorEspecial1", "Se perdió el campo CampoInventado1"
    assert v["campos_extra"].get("TemperaturaAmbiente") == 23.5, "Se perdió el campo TemperaturaAmbiente"
