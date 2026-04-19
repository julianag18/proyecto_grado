# PAME — Módulo Complementario

**Módulo complementario al Programa de Aseguramiento Metrológico de Laboratorios Laproff**

> Proyecto de grado — Bioingeniería | 2025

---

## Estructura del proyecto

```
pame-modulo-complementario/
├── config/          # Configuración y mapeo de columnas
├── db/              # Cliente Supabase y schema SQL
├── etl/             # Pipeline de migración de datos
├── scheduler/       # Motor de cronograma y alertas
├── dashboard/       # Dashboard Streamlit (próxima fase)
├── scripts/         # CLI para ejecución manual
├── tests/           # Tests unitarios con pytest
└── data/test/       # Datos de prueba sintéticos (generados)
```

## Instalación

```bash
# 1. Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate   # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
copy .env.example .env
# Editar .env con las credenciales de Supabase
```

## Base de datos

Ejecutar el contenido de `db/schema.sql` en el **SQL Editor de Supabase** para crear las tablas.

## Uso rápido

```bash
# Generar datos de prueba
python scripts/seed_test_data.py

# Ejecutar ETL de inventario
python scripts/run_etl.py inventario data/test/inventario_prueba.xlsx

# Ejecutar ETL de cronograma
python scripts/run_etl.py servicios data/test/cronograma_prueba.xlsx

# Calcular fechas y generar alertas
python scripts/run_scheduler.py

# Ejecutar tests
pytest tests/ -v
```

## Stack tecnológico

| Herramienta | Rol |
|---|---|
| Python 3.11+ | Lenguaje principal |
| pandas 2.x | ETL y análisis |
| supabase-py 2.x | Base de datos |
| Pydantic v2 | Validación de esquemas |
| Streamlit | Dashboard (próxima fase) |
| pytest | Testing |
# proyecto_grado
