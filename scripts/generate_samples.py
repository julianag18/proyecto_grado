import csv
import json
import os
from pathlib import Path

# Paths
base_dir = Path("C:/Users/esteb/.gemini/antigravity/scratch/proyecto_grado")
samples_dir = base_dir / "data" / "samples"
samples_dir.mkdir(parents=True, exist_ok=True)

# 1. Move cronograma_historico.json if it exists at root
hist_src = base_dir / "cronograma_historico.json"
hist_dest = samples_dir / "cronograma_historico.json"
if hist_src.exists() and not hist_dest.exists():
    hist_src.rename(hist_dest)
    print("Mapeado cronograma_historico.json a data/samples/")

# 2. Generate cronograma_sample.csv
csv_path = samples_dir / "cronograma_sample.csv"

# Fields
fields = [
    "Equipo", "Código del Equipo", "Fecha de Servicio Vigente", 
    "Fecha de Ejecución del Servicio Programado", "Tipo de Servicio", 
    "Frecuencia", "Estado del Servicio", "Estado de Entrega", 
    "Estado de Conformidad", "Proveedor", "Período Próximo Servicio", 
    "Activo Fijo", "Serie Equipo", "Ubicación"
]

rows = []

# Valid unique rows count: 50
# We need to distribute:
# Estados: Vigente (23), Vencido (15), Programar (12), En ejecución (5) -- Wait, 23+15+12+5 = 55!
# Conformidades: Cumple (23), No Cumple (15), Pendiente de Calificar (17) -- 23+15+17 = 55!
# This means the 55 total rows in the CSV (including duplicates and invalid ones) must sum to these totals!
# Let's design 50 valid unique rows, 3 duplicates, and 2 invalid rows.
# Valid unique:
# Row 1-20: Vigente / Cumple
# Row 21-32: Vencido / No Cumple
# Row 33-42: Programar / Pendiente de Calificar
# Row 43-47: En ejecución / Pendiente de Calificar
# Row 48-50: Vigente / Cumple

# Let's build the list of 50 valid rows
valid_configs = []

# 23 Vigente / Cumple (rows 1-20, 48-50)
for i in range(1, 24):
    valid_configs.append({
        "estado": "Vigente",
        "conformidad": "Cumple",
        "entrega": "Entregado",
        "tipo": "Calibración" if i % 2 == 0 else "Mantenimiento Preventivo",
        "frecuencia": "Anual" if i % 3 != 0 else "Semestral",
        "fecha": f"15/01/2026" if i % 2 == 0 else "20/03/2026",
        "periodo": "01/2027" if i % 2 == 0 else "03/2027",
    })

# 15 Vencido / No Cumple
for i in range(1, 16):
    valid_configs.append({
        "estado": "Vencido",
        "conformidad": "No Cumple",
        "entrega": "Pendiente",
        "tipo": "Calificación" if i % 2 == 0 else "Diagnóstico",
        "frecuencia": "Semestral" if i % 2 == 0 else "Anual",
        "fecha": "10/10/2025",
        "periodo": "04/2026" if i % 2 == 0 else "10/2026",
    })

# 12 Programar / Pendiente de Calificar (rows 33-42, and we need 2 more to make 12. Let's make 12 here)
for i in range(1, 13):
    valid_configs.append({
        "estado": "Programar",
        "conformidad": "Pendiente de Calificar",
        "entrega": "Pendiente",
        "tipo": "Calificación OQ" if i % 2 == 0 else "Verificación Temperatura y Humedad",
        "frecuencia": "Anual" if i % 2 == 0 else "Trimestral",
        "fecha": "05/12/2025",
        "periodo": "06/2026" if i % 2 == 0 else "03/2026",
    })

# 5 En ejecución / Pendiente de Calificar
for i in range(1, 6):
    valid_configs.append({
        "estado": "En ejecución",
        "conformidad": "Pendiente de Calificar",
        "entrega": "Pendiente",
        "tipo": "Calificación PQ",
        "frecuencia": "Anual",
        "fecha": "20/05/2026",
        "periodo": "05/2027",
    })

# Total rows generated so far: 23 + 15 + 12 + 5 = 55 valid config structures!
# Wait! If we have 55 valid structures, let's select 50 unique ones.
# Let's map them to 50 unique equipments: LS2001 to LS2050.
# For the 3 duplicates, we will repeat 3 of these records exactly (same equipment, same service, same date).
# For the 2 invalid rows, we will make them invalid by leaving Code/Name empty or similar.
# Wait! Let's adjust the counts so that after adding duplicates and invalid, the TOTAL is 55.
# Let's see: if we have 50 unique valid rows, 3 exact duplicates of 3 valid rows, and 2 invalid rows,
# the total rows will be 50 + 3 + 2 = 55 rows!
# Let's check the counts of states in these 55 rows:
# If the 3 duplicates are:
# - 1 Vigente / Cumple
# - 1 Vencido / No Cumple
# - 1 Programar / Pendiente de Calificar
# Then the counts will be:
# Vigente: 23 unique + 1 dup = 24?
# Wait! The instruction says:
# "cronograma_sample.csv — 55 filas ficticias... Estados: Vigente (23), Vencido (15), Programar (12), En ejecución (5)."
# This sums to: 23 + 15 + 12 + 5 = 55 rows!
# So the 55 rows in the CSV (including duplicates and invalid ones) must sum to exactly these counts!
# What about the 2 invalid rows? They will still have a State field filled (e.g. Vigente or Vencido) but will be invalid because of missing Code or Name.
# So:
# Total Vigente = 23 rows (22 valid unique + 1 duplicate = 23)
# Total Vencido = 15 rows (13 valid unique + 1 duplicate + 1 invalid = 15)
# Total Programar = 12 rows (10 valid unique + 1 duplicate + 1 invalid = 12)
# Total En ejecución = 5 rows (5 valid unique = 5)
# Let's count valid unique rows: 22 (Vigente) + 13 (Vencido) + 10 (Programar) + 5 (En ejecución) = 50 valid unique rows!
# Duplicates: 3 rows (1 Vigente, 1 Vencido, 1 Programar).
# Invalid: 2 rows (1 Vencido, 1 Programar).
# Total rows: 50 unique + 3 duplicates + 2 invalid = 55 rows!
# Let's double check counts:
# Vigente: 22 unique + 1 duplicate = 23 rows.
# Vencido: 13 unique + 1 duplicate + 1 invalid = 15 rows.
# Programar: 10 unique + 1 duplicate + 1 invalid = 12 rows.
# En ejecución: 5 unique = 5 rows.
# Total rows = 23 + 15 + 12 + 5 = 55 rows!
# Let's check Conformidades:
# Cumple: Vigente rows (23) = 23 rows.
# No Cumple: Vencido rows (15) = 15 rows.
# Pendiente de Calificar: Programar (12) + En ejecución (5) = 17 rows.
# Total conformidades: 23 + 15 + 17 = 55 rows!
# This matches the instructions perfectly!

proveedores = [
    "LAPROFF", "ZOSER", "CONTROL SUPERIOR", "DOXA", "ALMAPAL", "Centricol", "KAIKA",
    "AGUATEC", "CONAMET", "METROGLOBAL", "KILIAN", "CELSIUS", "BLAMIS"
]

ubicaciones = [
    "CONTROL CALIDAD", "METROLOGÍA", "MICROBIOLOGÍA", "INVESTIGACIÓN Y DESARROLLO",
    "PLANTA DE PRODUCCIÓN", "VALIDACIONES", "ALMACÉN DE MATERIALES"
]

csv_rows = []

# Generate 50 unique valid configurations mapped to LS2001 to LS2050
# 22 Vigente
for idx in range(1, 23):
    cod = f"LS{2000 + idx}"
    csv_rows.append({
        "Equipo": f"Balanza {cod}",
        "Código del Equipo": cod,
        "Fecha de Servicio Vigente": "15/01/2026",
        "Fecha de Ejecución del Servicio Programado": "",
        "Tipo de Servicio": "Calibración" if idx % 2 == 0 else "Mantenimiento Preventivo",
        "Frecuencia": "Anual" if idx % 3 != 0 else "Semestral",
        "Estado del Servicio": "Vigente",
        "Estado de Entrega": "Entregado",
        "Estado de Conformidad": "Cumple",
        "Proveedor": proveedores[idx % len(proveedores)],
        "Período Próximo Servicio": "01/2027",
        "Activo Fijo": "AF10-03600" if idx % 2 == 0 else "NO IDENTIFICADO",
        "Serie Equipo": f"SN-{10000 + idx}" if idx % 3 != 0 else "NO REGISTRA",
        "Ubicación": ubicaciones[idx % len(ubicaciones)]
    })

# 13 Vencido
for idx in range(23, 36):
    cod = f"LS{2000 + idx}"
    csv_rows.append({
        "Equipo": f"Termómetro {cod}",
        "Código del Equipo": cod,
        "Fecha de Servicio Vigente": "10/10/2025",
        "Fecha de Ejecución del Servicio Programado": "",
        "Tipo de Servicio": "Calificación" if idx % 2 == 0 else "Diagnóstico",
        "Frecuencia": "Semestral" if idx % 2 == 0 else "Anual",
        "Estado del Servicio": "Vencido",
        "Estado de Entrega": "Pendiente",
        "Estado de Conformidad": "No Cumple",
        "Proveedor": proveedores[idx % len(proveedores)],
        "Período Próximo Servicio": "04/2026",
        "Activo Fijo": "AF10-00882" if idx % 2 == 0 else "NO APLICA",
        "Serie Equipo": f"SN-{10000 + idx}" if idx % 3 != 0 else "NO IDENTIFICADO",
        "Ubicación": ubicaciones[idx % len(ubicaciones)]
    })

# 10 Programar
for idx in range(36, 46):
    cod = f"LS{2000 + idx}"
    csv_rows.append({
        "Equipo": f"pH-metro {cod}",
        "Código del Equipo": cod,
        "Fecha de Servicio Vigente": "05/12/2025",
        "Fecha de Ejecución del Servicio Programado": "",
        "Tipo de Servicio": "Calificación OQ" if idx % 2 == 0 else "Mapeo",
        "Frecuencia": "Anual" if idx % 2 == 0 else "Trimestral",
        "Estado del Servicio": "Programar",
        "Estado de Entrega": "Pendiente",
        "Estado de Conformidad": "Pendiente de Calificar",
        "Proveedor": proveedores[idx % len(proveedores)],
        "Período Próximo Servicio": "12/2026",
        "Activo Fijo": "AF10-00354" if idx % 2 == 0 else "NO IDENTIFICADO",
        "Serie Equipo": f"SN-{10000 + idx}" if idx % 3 != 0 else "NO REGISTRA",
        "Ubicación": ubicaciones[idx % len(ubicaciones)]
    })

# 5 En ejecución
for idx in range(46, 51):
    cod = f"LS{2000 + idx}"
    csv_rows.append({
        "Equipo": f"Espectrofotómetro {cod}",
        "Código del Equipo": cod,
        "Fecha de Servicio Vigente": "20/05/2026",
        "Fecha de Ejecución del Servicio Programado": "",
        "Tipo de Servicio": "Calificación PQ",
        "Frecuencia": "Anual",
        "Estado del Servicio": "En ejecución",
        "Estado de Entrega": "Pendiente",
        "Estado de Conformidad": "Pendiente de Calificar",
        "Proveedor": proveedores[idx % len(proveedores)],
        "Período Próximo Servicio": "05/2027",
        "Activo Fijo": "AF10-02540",
        "Serie Equipo": f"SN-{10000 + idx}",
        "Ubicación": ubicaciones[idx % len(ubicaciones)]
    })

# We now have 50 unique rows in csv_rows.
# Let's add 3 duplicates of specific rows (index 5, 25, 38)
csv_rows.append(dict(csv_rows[5]))      # Vigente / Cumple
csv_rows.append(dict(csv_rows[25]))     # Vencido / No Cumple
csv_rows.append(dict(csv_rows[38]))     # Programar / Pendiente de Calificar

# Let's add 2 invalid rows (without Código del Equipo / Equipo)
# 1 Vencido
csv_rows.append({
    "Equipo": "",  # invalid
    "Código del Equipo": "",  # invalid
    "Fecha de Servicio Vigente": "10/10/2025",
    "Fecha de Ejecución del Servicio Programado": "",
    "Tipo de Servicio": "Calibración",
    "Frecuencia": "Anual",
    "Estado del Servicio": "Vencido",
    "Estado de Entrega": "Pendiente",
    "Estado de Conformidad": "No Cumple",
    "Proveedor": "LAPROFF",
    "Período Próximo Servicio": "04/2026",
    "Activo Fijo": "NO IDENTIFICADO",
    "Serie Equipo": "NO IDENTIFICADO",
    "Ubicación": "CONTROL CALIDAD"
})

# 1 Programar
csv_rows.append({
    "Equipo": "Balanza Inválida",
    "Código del Equipo": "",  # invalid
    "Fecha de Servicio Vigente": "05/12/2025",
    "Fecha de Ejecución del Servicio Programado": "",
    "Tipo de Servicio": "Calibración",
    "Frecuencia": "Anual",
    "Estado del Servicio": "Programar",
    "Estado de Entrega": "Pendiente",
    "Estado de Conformidad": "Pendiente de Calificar",
    "Proveedor": "LAPROFF",
    "Período Próximo Servicio": "12/2026",
    "Activo Fijo": "NO IDENTIFICADO",
    "Serie Equipo": "NO IDENTIFICADO",
    "Ubicación": "CONTROL CALIDAD"
})

# Save to CSV
with open(csv_path, mode="w", newline="", encoding="latin-1") as f:
    writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
    writer.writeheader()
    for row in csv_rows:
        writer.writerow(row)

print(f"Generated cronograma_sample.csv with {len(csv_rows)} rows.")

# 3. Generate equipos_nuevos.csv
eq_path = samples_dir / "equipos_nuevos.csv"
eq_rows = []

for idx in range(0, 10):
    cod = f"CC90{idx}-26"
    eq_rows.append({
        "Equipo": f"Centrífuga {cod}",
        "Código del Equipo": cod,
        "Fecha de Servicio Vigente": "01/06/2026",
        "Fecha de Ejecución del Servicio Programado": "",
        "Tipo de Servicio": "Calibración",
        "Frecuencia": "Anual",
        "Estado del Servicio": "Vigente",
        "Estado de Entrega": "Entregado",
        "Estado de Conformidad": "Cumple",
        "Proveedor": "Centricol",
        "Período Próximo Servicio": "06/2027",
        "Activo Fijo": f"AF10-0990{idx}",
        "Serie Equipo": f"SN-990{idx}",
        "Ubicación": "MICROBIOLOGÍA"
    })

with open(eq_path, mode="w", newline="", encoding="latin-1") as f:
    writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
    writer.writeheader()
    for row in eq_rows:
        writer.writerow(row)

print(f"Generated equipos_nuevos.csv with {len(eq_rows)} rows.")
