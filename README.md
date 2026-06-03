# PAME — Módulo Complementario

**Módulo complementario al Programa de Aseguramiento Metrológico de Laboratorios Laproff**

> Proyecto de grado — Bioingeniería | 2026

---

## Estructura del proyecto

```
pame-modulo-complementario/
├── config/          # Configuración y mapeo de columnas
├── db/              # Cliente Supabase y schema SQL
├── etl/             # Pipeline de migración de datos (ETL)
├── scheduler/       # Motor de cronograma y alertas
├── dashboard/       # Dashboard Streamlit (4 páginas)
│   ├── app.py           # Punto de entrada principal
│   ├── assets/          # CSS global (dark mode)
│   ├── components/      # data_loader, kpi_cards, charts
│   └── pages/           # 01_estado_pame, 02_cronograma, 03_alertas, 04_migracion
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
# Editar .env con las credenciales de Supabase (opcional — ver Modo Demo)
```

## Base de datos

Ejecutar el contenido de `db/schema.sql` en el **SQL Editor de Supabase** para crear las tablas.

## Uso rápido

```bash
# Generar datos de prueba sintéticos
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

## Dashboard

```bash
# Lanzar el dashboard (desde la raíz del proyecto)
streamlit run dashboard/app.py
```

El dashboard se abre en `http://localhost:8501` y tiene **4 páginas**:

| Página | Descripción |
|---|---|
| 📊 Estado General | KPIs, gauge de cumplimiento, gráficos por área |
| 📅 Cronograma | Tabla filtrable con semáforo de alertas + export CSV/Excel |
| 🔔 Alertas | Bandeja priorizada: Vencidos → Críticos → Próximos |
| 📤 Migración ETL | Historial de cargas + uploader drag & drop |

### Modo Demo

Si no hay credenciales de Supabase configuradas en `.env`, el dashboard
arranca en **modo demo** con 40 equipos sintéticos representativos.
Los datos demo tienen la misma estructura que los datos reales.

## Stack tecnológico

| Herramienta | Rol |
|---|---|
| Python 3.11+ | Lenguaje principal |
| pandas 2.x | ETL y análisis |
| supabase-py 2.x | Base de datos |
| Pydantic v2 | Validación de esquemas |
| Streamlit 1.36 | Dashboard interactivo |
| Plotly 5.x | Gráficos (gauge, barras, donut, timeline) |
| pytest | Testing |
# proyecto_grado
# proyecto_grado
# proyecto_grado
