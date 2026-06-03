# Aseguramiento Metrológico PAME — Módulo Complementario
## Laboratorios Laproff S.A.S.

Módulo complementario para el **Programa de Aseguramiento Metrológico (PAME)** de Laboratorios Laproff S.A.S., desarrollado como proyecto de práctica académica para **Juliana González Afanador** (Bioingeniería, Universidad de Antioquia).

El sistema automatiza el procesamiento y la normalización de cronogramas y hojas de servicios metrológicos multiformato (CSV, Excel y JSON) a una base de datos documental **Firebase Firestore (NoSQL)**, calcula alertas automatizadas por proximidad de vencimiento y genera reportes interactivos y de cumplimiento histórico para auditorías del INVIMA.

---

## 🔬 Glosario y Dominio Metrológico

En la industria farmacéutica bajo la regulación del INVIMA (Colombia), los equipos deben pasar por controles periódicos para asegurar que sus mediciones sean exactas y válidas:
* **Calibración:** Conjunto de operaciones que establecen la relación entre los valores indicados por un instrumento de medición y los valores correspondientes de un patrón.
* **Calificación (OQ/PQ):** Proceso que demuestra que un equipo funciona correctamente y produce los resultados esperados bajo condiciones operativas (OQ) y de desempeño real (PQ).
* **Mantenimiento Preventivo:** Tareas periódicas de inspección, limpieza y calibración de componentes para evitar fallos mecánicos o de medición.
* **Verificación:** Confirmación mediante aportación de evidencia objetiva de que el equipo cumple con los requisitos especificados.
* **Estado de Conformidad (Cumple / No Cumple):** Indica si tras la calibración/verificación el equipo cumple con las tolerancias y especificaciones metrológicas definidas para su uso.

---

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.11+
* **Procesamiento de datos:** Pandas, Openpyxl
* **Base de Datos:** Firebase Firestore (NoSQL Documental)
* **Visualizaciones y Dashboard:** Streamlit, Plotly
* **Pruebas Unitarias:** Pytest

---

## 📁 Estructura del Proyecto

```
proyecto_grado/
├── .env                        ← Variables de entorno (SMTP, Destinatarios)
├── .env.example                ← Plantilla de variables de entorno
├── .gitignore                  ← Excluye archivos locales (.env, credenciales, venv)
├── firebase_credentials.json   ← Clave privada de Firebase (excluida de git)
├── requirements.txt            ← Dependencias del sistema
├── run.py                      ← CLI de ejecución principal
├── src/                        ← Código fuente del módulo
│   ├── database/
│   │   ├── firebase_client.py  ← Cliente Singleton para Firestore NoSQL
│   │   └── equipos_repo.py     ← Repositorio de operaciones y logs en BD
│   ├── etl/
│   │   ├── extractor.py        ← Extractor de CSV, Excel y JSON multiformato
│   │   ├── transformer.py      ← Normalizador, deduplicador y validador de datos
│   │   ├── loader.py           ← Cargador upsert en lotes para Firestore
│   │   └── pipeline.py         ← Coordinador del flujo ETL
│   ├── alertas/
│   │   ├── motor_alertas.py    ← Motor de priorización y días restantes
│   │   └── email_sender.py     ← Envío de correos SMTP HTML con logs
│   └── dashboard/
│       ├── app.py              ← Frontend e interfaz Streamlit (6 pestañas)
│       ├── charts.py           ← Gráficos Plotly adaptados a paleta de colores
│       └── helpers.py          ← Orquestador de origen de datos (Firestore/Demo)
├── tests/                      ← Suite de pruebas con Pytest
│   ├── test_alertas.py         ← Pruebas unitarias de alertas y correos ficticios
│   ├── test_etl.py             ← Pruebas de extracción y carga simulada
│   └── test_metricas_etl.py    ← Pruebas de calidad y deduplicación con el sample
└── data/
    └── samples/                ← Datos de prueba representativos
        ├── cronograma_sample.csv
        ├── cronograma_historico.json
        └── equipos_nuevos.csv
```

---

## 🚀 Instalación y Configuración

### 1. Clonar el repositorio y configurar el entorno
```bash
# 1. Crear entorno virtual
python -m venv .venv

# 2. Activar el entorno virtual
# En Windows (PowerShell):
.venv\Scripts\Activate.ps1
# En Windows (CMD):
.venv\Scripts\activate.bat
# En macOS/Linux:
source .venv/bin/activate

# 3. Instalar dependencias requeridas
pip install -r requirements.txt
```

### 2. Configurar Firebase Firestore (Base de datos)
Si no tienes credenciales de Firebase configuradas, el sistema iniciará automáticamente en **Modo Demo (muestras locales)** para permitirte probar todas las funcionalidades y visualizaciones del dashboard.

Para conectar a una base de datos real:
1. Ve a [Firebase Console](https://console.firebase.google.com/).
2. Crea un proyecto nuevo e inicializa **Firestore Database** en modo nativo.
3. Ve a `Configuración del proyecto > Cuentas de servicio` y haz clic en **Generar nueva clave privada**.
4. Guarda el archivo JSON descargado en la raíz de este proyecto con el nombre `firebase_credentials.json`.
5. Asegúrate de que `firebase_credentials.json` esté en tu archivo `.gitignore` para evitar subirlo a Git.

### 3. Configurar variables de entorno (.env)
Copia la plantilla `.env.example` como un archivo `.env`:
```bash
copy .env.example .env
```
Abre el archivo `.env` y rellena los campos:
* `FIREBASE_CREDENTIALS_PATH`: Nombre de tu archivo de credenciales de Firebase (ej. `firebase_credentials.json`).
* `SMTP_USER` y `SMTP_PASSWORD`: Correo emisor y contraseña de aplicación (para envío real de alertas).
* `EMAIL_DESTINATARIOS`: Correo del destinatario de las alertas diario (ej. `juli3213@gmail.com`).

---

## 💻 CLI de Ejecución (`run.py`)

El archivo `run.py` en la raíz sirve como punto de acceso unificado a las tareas del sistema:

### Ejecución de ETL (Extracción, Transformación y Carga)
Puedes procesar archivos CSV, Excel o JSON:
```bash
# Procesar en Modo Simulación (sin escribir en Firestore)
python run.py --mode etl --file data/samples/cronograma_sample.csv --dry-run

# Carga real de cronograma inicial a Firestore
python run.py --mode etl --file data/samples/cronograma_sample.csv

# Carga real de histórico anual (2023, 2024, 2025)
python run.py --mode etl --file data/samples/cronograma_historico.json

# Carga incremental de nuevos equipos
python run.py --mode etl --file data/samples/equipos_nuevos.csv
```

### Generación y envío manual de Alertas
Consulta Firestore, prioriza las fechas de vencimiento y envía el reporte diario por correo electrónico:
```bash
python run.py --mode alertas
```
*Si no has configurado tus credenciales SMTP en `.env`, el sistema simulará el envío de manera segura imprimiendo el reporte en la consola de comandos.*

### Iniciar el programador automático (Scheduler)
Inicia un proceso continuo que envía de forma automática el reporte diario de alertas a las 08:00 AM:
```bash
python run.py --mode scheduler
```

### Iniciar el Dashboard en Streamlit
```bash
python run.py --mode dashboard
```
*También puedes iniciarlo directamente usando `streamlit run src/dashboard/app.py`.*

### Limpiar la Base de Datos
Borra permanentemente todos los registros en Firestore de forma segura pidiendo doble confirmación por consola:
```bash
python run.py --mode limpiar
```

---

## 🧪 Pruebas Unitarias
El proyecto cuenta con una suite completa de pruebas unitarias que evalúan el motor de alertas, la transformación de datos y la extracción. Para ejecutarlas:
```bash
pytest tests/ -v
```

---

## 🎨 Guía de Colores y Estados
El sistema respeta rigurosamente el manual de colores corporativo y de criticidad de Laboratorios Laproff:

| Estado | Significado | Hexadecimal | Color visual |
|---|---|---|---|
| **Vigente** | Servicio realizado y dentro del plazo | `#10B981` | Verde |
| **En ejecución** | Servicio metrológico en curso | `#00A99D` | Azul Teal |
| **Programar** | Vence pronto (menos de 30 días) | `#F59E0B` | Amarillo / Ámbar |
| **Vencido** | Fecha de servicio superada | `#DC2626` | Rojo oscuro / Carmesí |
| **Sin datos** | Equipo sin registro de intervenciones | `#94A3B8` | Gris neutral |
