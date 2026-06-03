"""
tests/test_etl_mapper.py
──────────────────────────────────────────────────────────────────────────────
Pruebas unitarias para el mapeador de columnas flexible (etl/extractor.py).
──────────────────────────────────────────────────────────────────────────────
"""

import sys
import pandas as pd
import pytest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from etl.extractor import leer_archivo


def test_leer_archivo_con_mapeo_manual(tmp_path):
    """
    Verifica que al pasar un mapeo manual, las columnas del archivo
    sean renombradas correctamente a los nombres canónicos de la base de datos.
    """
    # Crear un archivo CSV temporal con columnas no estándar
    csv_file = tmp_path / "equipos_no_estandar.csv"
    df_raw = pd.DataFrame({
        "ID_EQUIPO": ["CC-001", "CC-002"],
        "DESC_EQUIPO": ["Balanza", "pH-metro"],
        "DEPTO": ["Control Calidad", "Microbiología"],
    })
    df_raw.to_csv(csv_file, index=False, encoding="utf-8")

    # Mapeo manual a campos canónicos
    mapeo_manual = {
        "ID_EQUIPO": "codigo_equipo",
        "DESC_EQUIPO": "nombre",
        "DEPTO": "area",
    }

    # Leer el archivo aplicando el mapeo manual
    df_mapped = leer_archivo(csv_file, tipo="inventario", mapeo_manual=mapeo_manual)

    # Verificar que las columnas fueron renombradas correctamente
    assert list(df_mapped.columns) == ["codigo_equipo", "nombre", "area"]
    assert df_mapped.loc[0, "codigo_equipo"] == "CC-001"
    assert df_mapped.loc[1, "nombre"] == "pH-metro"
