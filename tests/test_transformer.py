"""
tests/test_transformer.py
──────────────────────────────────────────────────────────────────────────────
Pruebas unitarias para el módulo etl/transformer.py.
No requieren conexión a Supabase ni archivos reales.
──────────────────────────────────────────────────────────────────────────────
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from etl.transformer import (
    _normalizar_texto,
    _normalizar_fecha,
    _normalizar_enum,
    transformar_inventario,
    transformar_servicios,
)


# ──────────────────────────────────────────────────────────────────────────────
# Tests de funciones auxiliares
# ──────────────────────────────────────────────────────────────────────────────

class TestNormalizarTexto:
    def test_elimina_espacios_extremos(self):
        assert _normalizar_texto("  Balón  ") == "Balón"

    def test_colapsa_espacios_internos(self):
        assert _normalizar_texto("Balón  Volumétrico   50  mL") == "Balón Volumétrico 50 mL"

    def test_retorna_none_para_vacio(self):
        assert _normalizar_texto("") is None
        assert _normalizar_texto("  ") is None
        assert _normalizar_texto(None) is None
        assert _normalizar_texto("nan") is None
        assert _normalizar_texto("N/A") is None

    def test_conserva_tildes(self):
        assert _normalizar_texto("Calibración") == "Calibración"


class TestNormalizarFecha:
    def test_formato_dd_mm_yyyy(self):
        assert _normalizar_fecha("15/06/2024") == "2024-06-15"

    def test_formato_yyyy_mm_dd(self):
        assert _normalizar_fecha("2024-06-15") == "2024-06-15"

    def test_formato_dd_mm_yy(self):
        assert _normalizar_fecha("15/06/24") == "2024-06-15"

    def test_retorna_none_para_vacio(self):
        assert _normalizar_fecha("") is None
        assert _normalizar_fecha(None) is None

    def test_retorna_none_para_texto_invalido(self):
        assert _normalizar_fecha("no es fecha") is None


class TestNormalizarEnum:
    OPCIONES = ["En Servicio", "Fuera de Uso", "En Reparación", "Dado de Baja"]

    def test_coincidencia_exacta(self):
        assert _normalizar_enum("En Servicio", self.OPCIONES) == "En Servicio"

    def test_coincidencia_case_insensitive(self):
        assert _normalizar_enum("en servicio", self.OPCIONES) == "En Servicio"
        assert _normalizar_enum("EN SERVICIO", self.OPCIONES) == "En Servicio"

    def test_coincidencia_parcial(self):
        assert _normalizar_enum("Servicio", self.OPCIONES) == "En Servicio"

    def test_retorna_none_para_vacio(self):
        assert _normalizar_enum("", self.OPCIONES) is None
        assert _normalizar_enum(None, self.OPCIONES) is None

    def test_valor_sin_coincidencia_se_conserva(self):
        resultado = _normalizar_enum("Desconocido", self.OPCIONES)
        assert resultado == "Desconocido"


# ──────────────────────────────────────────────────────────────────────────────
# Tests de transformar_inventario
# ──────────────────────────────────────────────────────────────────────────────

def _df_inventario_base(n: int = 5) -> pd.DataFrame:
    """Crea un DataFrame de inventario mínimo para tests."""
    return pd.DataFrame({
        "codigo_equipo": [f"CC-{100+i:03d}-20" for i in range(n)],
        "nombre":        [f"Equipo de prueba {i}" for i in range(n)],
        "serie":         [f"SN{i:04d}" for i in range(n)],
        "frecuencia":    ["Anual"] * n,
        "estado_equipo": ["En Servicio"] * n,
        "criticidad":    ["Media"] * n,
    })


class TestTransformarInventario:
    def test_retorna_resultado_con_campos_correctos(self):
        df = _df_inventario_base(5)
        resultado = transformar_inventario(df)
        assert hasattr(resultado, "df_limpio")
        assert hasattr(resultado, "df_rechazos")
        assert hasattr(resultado, "df_duplicados")
        assert hasattr(resultado, "total_leidos")

    def test_rechaza_filas_sin_codigo(self):
        df = _df_inventario_base(5)
        df.loc[2, "codigo_equipo"] = None
        resultado = transformar_inventario(df)
        assert resultado.total_rechazados == 1
        assert resultado.total_validos == 4

    def test_detecta_duplicados(self):
        df = _df_inventario_base(5)
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)  # duplicar fila 0
        resultado = transformar_inventario(df)
        assert resultado.total_duplicados == 1
        assert resultado.total_validos == 5

    def test_normaliza_estado_equipo(self):
        df = _df_inventario_base(3)
        df["estado_equipo"] = ["en servicio", "FUERA DE USO", "En Reparación"]
        resultado = transformar_inventario(df)
        estados = resultado.df_limpio["estado_equipo"].tolist()
        assert estados[0] == "En Servicio"
        assert estados[1] == "Fuera de Uso"

    def test_total_leidos_es_correcto(self):
        df = _df_inventario_base(10)
        resultado = transformar_inventario(df)
        assert resultado.total_leidos == 10

    def test_asigna_criticidad_por_defecto(self):
        """Si no hay columna criticidad, debe asignarse 'Media' a todos."""
        df = _df_inventario_base(3)
        df = df.drop(columns=["criticidad"])
        resultado = transformar_inventario(df)
        assert (resultado.df_limpio["criticidad"] == "Media").all()
