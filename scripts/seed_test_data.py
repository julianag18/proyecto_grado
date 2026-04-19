"""
scripts/seed_test_data.py
──────────────────────────────────────────────────────────────────────────────
Generador de datos de prueba sintéticos basados en la estructura real del PAME
de Laboratorios Laproff (observada en el aplicativo).

Genera DOS archivos Excel en la carpeta data/test/:
  1. inventario_prueba.xlsx  — 40 equipos típicos de laboratorio farmacéutico
  2. cronograma_prueba.xlsx  — Servicios históricos con estados variados

Los datos son realistas pero no corresponden a equipos reales.
──────────────────────────────────────────────────────────────────────────────
"""

import sys
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ── Directorio de salida ───────────────────────────────────────────────────────
SALIDA = Path(__file__).resolve().parent.parent / "data" / "test"
SALIDA.mkdir(parents=True, exist_ok=True)

# ── Semilla para reproducibilidad ─────────────────────────────────────────────
random.seed(42)

# ── Datos de referencia ────────────────────────────────────────────────────────
EQUIPOS_TIPO = [
    ("Balón Volumétrico 10 mL",     "BV",  "LMS"),
    ("Balón Volumétrico 25 mL",     "BV",  "LMS"),
    ("Balón Volumétrico 50 mL",     "BV",  "GLASSCO"),
    ("Balón Volumétrico 100 mL",    "BV",  "PYREX"),
    ("Balón Volumétrico 250 mL",    "BV",  "LMS"),
    ("Pipeta Volumétrica 1 mL",     "PV",  "BRAND"),
    ("Pipeta Volumétrica 5 mL",     "PV",  "BRAND"),
    ("Pipeta Volumétrica 10 mL",    "PV",  "BRAND"),
    ("Pipeta Volumétrica 25 mL",    "PV",  "BRAND"),
    ("Pipeta Volumétrica 50 mL",    "PV",  "PYREX"),
    ("Probeta Graduada 100 mL",     "PG",  "VITLAB"),
    ("Probeta Graduada 500 mL",     "PG",  "VITLAB"),
    ("Probeta Volumétrica 250 mL",  "PG",  "RAJAS"),
    ("Bureta 25 mL",                "BU",  "BRAND"),
    ("Bureta 50 mL",                "BU",  "BRAND"),
    ("Termohigrómetro Digital",     "TH",  "UNI-T"),
    ("Termohigrómetro Análogo",     "TH",  "SPER"),
    ("Termómetro Digital",          "TD",  "CHECKTEMP"),
    ("Termómetro de Referencia",    "TD",  "HART"),
    ("pH-metro de Banco",           "PH",  "METTLER"),
    ("pH-metro Portátil",           "PH",  "OAKTON"),
    ("Conductímetro",               "CO",  "YSI"),
    ("Refractómetro",               "RF",  "ATAGO"),
    ("Micropipeta 100-1000 µL",     "MP",  "EPPENDORF"),
    ("Micropipeta 10-100 µL",       "MP",  "EPPENDORF"),
    ("Micropipeta 1-10 µL",         "MP",  "GILSON"),
    ("Balanza Analítica 0.1 mg",    "BA",  "METTLER"),
    ("Balanza Analítica 0.01 mg",   "BA",  "SARTORIUS"),
    ("Balanza Semianálítica 1 mg",  "BS",  "OHAUS"),
    ("Balanza de Precisión 0.1 g",  "BP",  "ADAM"),
    ("Viscosímetro",                "VS",  "BROOKFIELD"),
    ("Pycnómetro 25 mL",            "PY",  "BRAND"),
    ("Espectrofotómetro UV-Vis",    "UV",  "THERMO"),
    ("Cromatógrafo HPLC",           "HP",  "AGILENT"),
    ("Agitador Vórtex",             "AV",  "VELP"),
    ("Sonicador",                   "SO",  "ELMASONIC"),
    ("Incubadora",                  "IN",  "MEMMERT"),
    ("Estufa de Secado",            "ES",  "BINDER"),
    ("Potenciómetro",               "PT",  "METTLER"),
    ("Válvula de Seguridad",        "VS",  "NO IDENTIFICADO"),
]

AREAS = ["Control Calidad", "Producción", "I+D", "Microbiología", "Fisicoquímica"]
UBICACIONES = [
    "Laboratorio Control Calidad",
    "Cuarto de Inflamables (Almacén de Materiales)",
    "Laboratorio Fisicoquímica",
    "Área de Producción Sólidos",
    "Laboratorio Microbiología",
    "Oficina Técnica",
    "Cuarto Frío",
]
ESTADOS_EQUIPO = ["En Servicio"] * 7 + ["Fuera de Uso"] + ["En Reparación"]
CRITICIDADES = ["Alta"] * 3 + ["Media"] * 5 + ["Baja"] * 2
PROVEEDORES = ["DOXA", "METROCAL", "LABORCLIN", "SOLULAB", "INCONTEC", "METROLOGÍA NACIONAL"]
FRECUENCIAS = ["Anual", "Anual", "Anual", "Semestral", "Trimestral"]
TIPOS_SERVICIO = ["Calibración"] * 6 + ["Verificación"] * 2 + ["Mantenimiento"]
ESTADOS_CONFORMIDAD = (
    ["Conforme"] * 5 + ["Pendiente de Calificar"] * 3 +
    ["No Conforme"] + ["Fuera de Especificación"]
)


def _codigo(prefijo: str, numero: int) -> str:
    """Genera un código tipo 'CC-180-20' o 'LS1871'."""
    if prefijo in ("BV", "PV", "PG", "BU", "PY"):
        return f"CC-{numero:03d}-{random.randint(18,24)}"
    else:
        return f"LS{1000 + numero}"


def generar_inventario(n: int = 40) -> pd.DataFrame:
    """Genera n registros de inventario de equipos."""
    registros = []

    for i, (nombre, prefijo, fabricante) in enumerate(EQUIPOS_TIPO[:n], start=100):
        codigo = _codigo(prefijo, i)
        serie = f"C{random.randint(100000, 999999)}" if fabricante != "NO IDENTIFICADO" else ""
        modelo = f"{prefijo}-{random.randint(10,99)}" if fabricante != "NO IDENTIFICADO" else ""
        area = random.choice(AREAS)
        estado = random.choice(ESTADOS_EQUIPO)
        criticidad = "Alta" if prefijo in ("BA", "BS", "HP", "UV", "PH") else random.choice(["Media", "Baja"])
        fecha_sol = date(2023, random.randint(1, 12), random.randint(1, 28))

        registros.append({
            "Código del Equipo": codigo,
            "Nombre":            nombre,
            "Serie":             serie,
            "Modelo":            modelo,
            "Fabricante":        fabricante,
            "Proveedor del Equipo": random.choice(PROVEEDORES),
            "Ubicación":         random.choice(UBICACIONES),
            "Área":              area,
            "Estado del Equipo": estado,
            "¿Es usable el equipo?": "Disponible" if estado == "En Servicio" else "No Disponible",
            "Estado de Aprobación": "Aprobado",
            "Activo Fijo":       f"AF-{random.randint(1000,9999)}",
            "Mide ambiente":     "Sí" if prefijo == "TH" else "",
            "Criticidad":        criticidad,
            "Fecha Solicitud":   fecha_sol.strftime("%d/%m/%Y"),
            "Creado Por":        random.choice(["JUAN JOSE SALAZAR RAMIREZ", "DIANA MARCELA OSPINA", "CARLOS ANDRÉS PÉREZ"]),
        })

    # Introducir intencionalmente 3 duplicados para probar el ETL
    for _ in range(3):
        dup = registros[random.randint(0, len(registros) - 1)].copy()
        registros.append(dup)

    # Introducir 2 registros sin código para probar rechazos
    for _ in range(2):
        sin_cod = registros[0].copy()
        sin_cod["Código del Equipo"] = ""
        registros.append(sin_cod)

    df = pd.DataFrame(registros)
    return df


def generar_cronograma(df_inventario: pd.DataFrame) -> pd.DataFrame:
    """Genera el cronograma de servicios basado en el inventario."""
    registros = []
    hoy = date.today()

    for _, fila in df_inventario.iterrows():
        codigo = fila.get("Código del Equipo", "")
        if not codigo:
            continue

        tipo_srv = random.choice(TIPOS_SERVICIO)
        frecuencia = random.choice(FRECUENCIAS)

        # Simular distintos escenarios de estado de alerta
        escenario = random.choices(
            ["al_dia", "proximo", "critico", "vencido"],
            weights=[40, 20, 20, 20],
        )[0]

        if escenario == "al_dia":
            dias_pasados = random.randint(10, 60)
        elif escenario == "proximo":
            # El servicio vigente fue hace ~335 días (próximo a vencer en ~30d)
            dias_pasados = 365 - random.randint(16, 30)
        elif escenario == "critico":
            dias_pasados = 365 - random.randint(0, 15)
        else:  # vencido
            dias_pasados = 365 + random.randint(1, 90)

        fecha_vigente = hoy - timedelta(days=dias_pasados)

        # Número de informe
        informe = f"DN-{random.randint(100000, 999999)}" if random.random() > 0.3 else ""

        estado_srv = "Ejecutado" if informe else "Programar"
        estado_ent = "Entregado" if informe else "Pendiente"
        estado_conf = random.choice(ESTADOS_CONFORMIDAD) if informe else "Pendiente de Calificar"

        registros.append({
            "Nombre Equipo":                              fila.get("Nombre", ""),
            "Código del Equipo":                          codigo,
            "Fecha de Servicio Vigente":                  fecha_vigente.strftime("%d/%m/%Y"),
            "Fecha de Ejecución del Servicio Programado": fecha_vigente.strftime("%d/%m/%Y"),
            "Tipo de Servicio":                           tipo_srv,
            "Frecuencia":                                 frecuencia,
            "Número de Informe":                          informe,
            "Estado del Servicio":                        estado_srv,
            "Estado de Entrega":                          estado_ent,
            "Estado de Conformidad":                      estado_conf,
            "Proveedor":                                  random.choice(PROVEEDORES),
            "Periodo Próximo Servicio":                   "",  # lo calcula el scheduler
        })

    return pd.DataFrame(registros)


if __name__ == "__main__":
    import sys
    import io
    # Forzar UTF-8 en la salida estándar para Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("[*] Generando datos de prueba sinteticos...")

    # -- Inventario ------------------------------------------------------------
    df_inv = generar_inventario(40)
    ruta_inv = SALIDA / "inventario_prueba.xlsx"
    df_inv.to_excel(ruta_inv, index=False)
    print(f"  [OK] Inventario: {len(df_inv)} registros -> {ruta_inv}")

    # -- Cronograma (solo registros con codigo valido) -------------------------
    df_inv_valido = df_inv[df_inv["Codigo del Equipo"].str.strip() != ""] \
        if "Codigo del Equipo" in df_inv.columns \
        else df_inv[df_inv["Código del Equipo"].fillna("").str.strip() != ""]
    df_cron = generar_cronograma(df_inv_valido)
    ruta_cron = SALIDA / "cronograma_prueba.xlsx"
    df_cron.to_excel(ruta_cron, index=False)
    print(f"  [OK] Cronograma: {len(df_cron)} registros -> {ruta_cron}")

    print("\n[OK] Datos de prueba generados correctamente.")
    print(f"     Ubicacion: {SALIDA}")
    print("\n     Nota: Se incluyeron intencionalmente:")
    print("       - 3 registros duplicados (para probar deduplicacion ETL)")
    print("       - 2 registros sin codigo (para probar rechazos ETL)")
    print("       - Equipos con distintos estados de alerta (AL_DIA, PROXIMO, CRITICO, VENCIDO)")

