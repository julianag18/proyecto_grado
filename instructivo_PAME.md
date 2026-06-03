# INSTRUCTIVO TÉCNICO — MÓDULO PAME
## Laboratorios Laproff S.A.S. — Práctica Académica Juliana González Afanador
### Guía de desarrollo por tareas para Antigravity

---

> **Cómo usar este instructivo:**
> Este documento está dividido en **bloques de trabajo independientes** para entregarle a Antigravity de forma secuencial. Cada bloque corresponde a una sesión de trabajo. Espera a que Antigravity complete y te entregue cada bloque antes de enviarle el siguiente. Incluye contexto suficiente en cada entrega para que no dependa de sesiones anteriores.

---

## CONTEXTO GLOBAL (incluir en toda entrega)

**Proyecto:** Módulo complementario al aplicativo PAME (Programa de Aseguramiento Metrológico) de Laboratorios Laproff S.A.S.

**Stack tecnológico definido:**
- Backend / lógica de datos: Python 3.x
- Manipulación de datos: Pandas, Openpyxl
- Base de datos: **Firebase Firestore (NoSQL documental)** ← base de datos principal
- Dashboard: Streamlit
- Archivos de entrada: Excel (.xlsx), CSV, JSON (estructura variable)

**Por qué NoSQL / Firestore:**
Los archivos JSON que llegan al sistema pueden tener estructuras distintas entre sí (campos renombrados, anidamiento diferente, campos extra o faltantes). Una base de datos documental como Firestore permite almacenar documentos flexibles sin un esquema rígido, lo que hace el sistema más robusto frente a esa variabilidad. Cada documento puede tener campos distintos sin romper la base de datos.

**Lo que ya existe (no tocar):**
- Un aplicativo interno en Laproff con módulos de registro de equipos y seguimiento de cronograma de servicios, que usa su propia base de datos.
- Un frontend HTML/CSS/JS de referencia visual (`pame.html`) con diseño aprobado: sidebar teal oscuro (#0B3533), cards blancas, badges de color para estados, charts con Chart.js.

**Lo que este módulo construye:**
1. Proceso ETL (extracción, transformación y carga) desde Excel, CSV y JSON → Firestore.
2. Motor de automatización del cronograma con alertas priorizadas y **envío por correo electrónico**.
3. Dashboard de KPIs en Streamlit con **vista histórica anual** (no solo tiempo real).

---

## BLOQUE 0 — LECTURA Y PREPARACIÓN (Entregar primero)

### Objetivo
Que Antigravity entienda el dominio del negocio, la arquitectura NoSQL elegida y el diseño visual antes de escribir código.

### Tarea 0.1 — Comprensión del dominio metrológico

**Explica a Antigravity:**
El proyecto gestiona el ciclo de vida de equipos de medición en una farmacéutica regulada por el INVIMA (Colombia). Cada equipo pasa por calibraciones, calificaciones, mantenimientos y verificaciones periódicas. El estado de cada servicio puede ser:

| Estado | Significado | Color del badge |
|--------|-------------|-----------------|
| Vigente | Servicio ejecutado, dentro del plazo | Verde |
| En ejecución | Servicio actualmente en curso | Azul teal |
| Programar | Próximo a vencer, necesita ser agendado | Amarillo |
| Vencido | Fecha de vencimiento superada | Rojo oscuro |
| Sin datos | Sin historial de servicio | Gris |

---

### ⚠️ ESTRUCTURA REAL DE DATOS DEL CRONOGRAMA DE LAPROFF

> **Este es el esquema de datos real del PAME. Todo el sistema debe respetar estos campos y valores.**

El archivo fuente principal es un CSV separado por punto y coma (`;`), codificación `latin-1`. Los campos son:

| Campo original (CSV) | Campo interno en BD | Descripción |
|----------------------|---------------------|-------------|
| `Equipo` | `nombre_equipo` | Nombre del equipo (puede coincidir con el código) |
| `Código del Equipo` | `codigo_equipo` | Identificador único (ej: `LS1191`, `CC397-25`) |
| `Fecha de Servicio Vigente` | `fecha_servicio_vigente` | Fecha del último servicio ejecutado (`DD/MM/YYYY`) |
| `Fecha de Ejecución del Servicio Programado` | `fecha_ejecucion_programada` | Fecha programada — **actualmente siempre vacía** |
| `Tipo de Servicio` | `tipo_servicio` | Ver valores válidos abajo |
| `Frecuencia` | `frecuencia` | Ver valores válidos abajo |
| `Estado del Servicio` | `estado_servicio` | Ver valores válidos abajo |
| `Estado de Entrega` | `estado_entrega` | `Entregado` / `Pendiente` |
| `Estado de Conformidad` | `estado_conformidad` | Ver valores válidos abajo |
| `Proveedor` | `proveedor` | Empresa que realiza el servicio |
| `Período Próximo Servicio` | `periodo_proximo_servicio` | Formato `MM/YYYY` (ej: `01/2027`) |
| `Activo Fijo` | `activo_fijo` | Código activo fijo (puede ser `NO IDENTIFICADO`, `NO REGISTRA`, `NO APLICA`) |
| `Serie Equipo` | `serie_equipo` | Número de serie del equipo |
| `Ubicación` | `ubicacion` | Área física dentro de la planta |

**Valores válidos por campo categórico:**
```
Tipo de Servicio:
  Calibración, Calificación, Calificación PQ, Calificación OQ,
  Mantenimiento Preventivo, Mantenimiento Correctivo,
  Verificación Temperatura y Humedad, Mapeo, Diagnóstico

Frecuencia:
  Anual, Semestral, Trimestral, Bienal, Trienal, NoAplica

Estado del Servicio:
  Vigente, Programar, En ejecución, Vencido

Estado de Entrega:
  Entregado, Pendiente

Estado de Conformidad:
  Cumple, No Cumple, Pendiente de Calificar
```

**Proveedores reales** (usar en datos ficticios):
```
LAPROFF, ZOSER, CONTROL SUPERIOR, DOXA, ALMAPAL, Centricol, KAIKA,
AGUATEC, CONAMET, METROGLOBAL, KILIAN, CELSIUS, BLAMIS,
INSTRUELECTRONIC, MB METROLOGÍA, LABORATORIO METROLOGICO DE ANTIOQUIA,
ANTON PAAR, PREMAC, ENDRESS+HAUSER, INNOVATEK, LABZUL,
RED METROLÓGICA DE ANTIOQUIA, SERVIMETERS, KASALAB, METRILAB
```

**Ubicaciones/áreas reales** (usar en datos ficticios):
```
CONTROL CALIDAD, METROLOGÍA, MICROBIOLOGÍA, INVESTIGACIÓN Y DESARROLLO,
PLANTA DE PRODUCCIÓN, VALIDACIONES, ALMACÉN DE MATERIALES,
TABLETEADO A, TABLETEADO B, TABLETEADO C, TABLETEADO D,
DISPENSACIÓN (CABINA DE PESAJE N°1), DISPENSACIÓN (CABINA DE PESAJE N°2),
ENVASADO DE LÍQUIDOS Y SUSPENSIONES, ENVASADO DE CREMAS,
ENCAPSULADO A, CONTROL PROCESOS 1, CONTROL PROCESOS 2, CONTROL PROCESOS 3
```

**Particularidades del CSV real que el ETL debe manejar:**
- Un mismo equipo puede tener **múltiples filas**, una por cada tipo de servicio o periodo.
- La columna `Fecha de Ejecución del Servicio Programado` está **completamente vacía** — nunca lanzar error por esto.
- `Período Próximo Servicio` viene como `MM/YYYY`, no como fecha estándar.
- `Activo Fijo` y `Serie Equipo` pueden contener literalmente `"NO IDENTIFICADO"`, `"NO REGISTRA"` o `"NO APLICA"` — normalizar estos a `null` en Firestore.
- El CSV real tiene 3.606 registros con 3.386 códigos de equipo únicos.

### Tarea 0.2 — Comprensión de la arquitectura NoSQL

**Explica a Antigravity:**

Se usará **Firebase Firestore** como base de datos. La razón principal es que los archivos JSON que llegan al sistema pueden tener estructuras distintas: distintos nombres de campos, anidamiento variable, campos extra. Firestore almacena documentos flexibles (como objetos JSON) sin exigir que todos tengan los mismos campos.

**Conceptos clave de Firestore para este proyecto:**
- **Colección:** equivalente a una tabla. Contiene documentos.
- **Documento:** equivalente a un registro/fila. Es un objeto JSON con campos propios.
- **Subcolección:** colección dentro de un documento (se usa para el historial de servicios de cada equipo).
- **ID de documento:** puede ser el propio `codigo_equipo` en lugar de un UUID autogenerado, lo que simplifica las consultas.

**Estructura de colecciones del proyecto:**
```
Firestore
│
├── equipos/                        ← Colección principal
│   ├── LS1191/                     ← Documento con ID = codigo_equipo
│   │   ├── nombre_equipo: "LS1191"
│   │   ├── ubicacion: "CONTROL CALIDAD"
│   │   ├── serie_equipo: null
│   │   ├── activo_fijo: null
│   │   ├── activo: true
│   │   ├── metadata_carga: {...}   ← trazabilidad de qué archivo lo cargó
│   │   └── servicios/              ← Subcolección de servicios de este equipo
│   │       ├── {auto_id}/
│   │       │   ├── tipo_servicio: "Calibración"
│   │       │   ├── frecuencia: "Anual"
│   │       │   ├── fecha_servicio_vigente: "2026-01-13"
│   │       │   ├── fecha_ejecucion_programada: null
│   │       │   ├── periodo_proximo_servicio: "01/2027"
│   │       │   ├── fecha_proximo_servicio: "2027-01-01"
│   │       │   ├── estado_servicio: "Vigente"
│   │       │   ├── estado_entrega: "Entregado"
│   │       │   ├── estado_conformidad: "Cumple"
│   │       │   ├── proveedor: "LAPROFF"
│   │       │   ├── anio: 2026
│   │       │   └── campos_extra: {...}  ← campos desconocidos del JSON original
│   │       └── ...
│   └── ...
│
├── alertas_log/                    ← Historial de alertas enviadas
│   └── {auto_id}/
│       ├── fecha_envio: timestamp
│       ├── tipo: "diaria" | "critica_inmediata"
│       ├── equipos_alertados: [...]
│       └── destinatarios: [...]
│
└── etl_log/                        ← Historial de cargas ETL
    └── {auto_id}/
        ├── fecha_carga: timestamp
        ├── archivo: "cronograma_2026.csv"
        ├── formato: "csv"
        ├── registros_totales: 55
        ├── insertados: 50
        ├── actualizados: 3
        └── errores: [...]
```

**Por qué el historial de servicios es una subcolección y no una colección separada:**
Porque en Firestore las consultas son más eficientes cuando los datos relacionados están colocados juntos. Para obtener todos los servicios de `LS1191` basta leer `equipos/LS1191/servicios/` sin hacer joins.

**Campos extra de JSON desconocido:**
Si el archivo JSON trae campos que no están en el esquema conocido, NO descartarlos. Guardarlos dentro del campo `campos_extra: {}` del documento. Esto respeta la flexibilidad del NoSQL y preserva información que puede ser útil en el futuro.

### Tarea 0.3 — Revisión del diseño visual de referencia

Se adjunta `pame.html` con el diseño visual aprobado. El dashboard Streamlit debe respetar esta paleta:

```css
--teal: #00A99D          /* Color primario */
--sidebar: #0B3533       /* Fondo sidebar */
--green: #10B981         /* Vigente / Cumple */
--amber: #F59E0B         /* Programar */
--red: #EF4444           /* En ejecución urgente */
--crimson: #DC2626       /* Vencido */
--neutral: #94A3B8       /* Sin datos */
```

**Entregable esperado de este bloque:**
- Confirmación de comprensión del dominio y la arquitectura NoSQL.
- Preguntas técnicas antes de empezar.
- Propuesta de estructura de carpetas del proyecto.

---

## BLOQUE 1 — MODELO DE DATOS Y CONEXIÓN A FIRESTORE

### Objetivo
Configurar Firebase Firestore y construir el módulo Python de conexión y operaciones sobre las colecciones.

### Tarea 1.1 — Configuración de Firebase

**Pasos para configurar Firestore:**
1. Crear proyecto en Firebase Console.
2. Activar Firestore en modo nativo.
3. Ir a Configuración del proyecto → Cuentas de servicio → Generar nueva clave privada.
4. Guardar el archivo JSON descargado como `firebase_credentials.json` en la raíz del proyecto.
5. Agregar `firebase_credentials.json` al `.gitignore` **inmediatamente** — nunca subir al repositorio.

**Variables de entorno en `.env`:**
```
FIREBASE_CREDENTIALS_PATH=firebase_credentials.json
# Alternativa: pasar el JSON completo como string para despliegues en la nube
FIREBASE_CREDENTIALS_JSON={"type": "service_account", ...}
```

### Tarea 1.2 — Módulo de conexión

Crear `src/database/firebase_client.py`:

```python
"""
Módulo de conexión a Firebase Firestore para el PAME de Laboratorios Laproff.
Credenciales SIEMPRE desde variables de entorno o archivo externo, nunca hardcodeadas.
"""
import os
import json
from google.cloud import firestore
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()

_db = None

def get_db() -> firestore.Client:
    """Singleton de conexión a Firestore. Reutiliza la misma instancia."""
    global _db
    if _db is not None:
        return _db

    # Opción 1: ruta a archivo de credenciales
    creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    # Opción 2: credenciales como JSON string (útil en servidores/CI)
    creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

    if creds_path and os.path.exists(creds_path):
        credentials = service_account.Credentials.from_service_account_file(creds_path)
    elif creds_json:
        info = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(info)
    else:
        raise EnvironmentError(
            "No se encontraron credenciales de Firebase. "
            "Configura FIREBASE_CREDENTIALS_PATH o FIREBASE_CREDENTIALS_JSON en .env"
        )

    _db = firestore.Client(credentials=credentials)
    return _db
```

### Tarea 1.3 — Repositorio de equipos y servicios

Crear `src/database/equipos_repo.py` con las siguientes funciones. **Importante:** en Firestore no hay SQL ni JOINs — la lógica de agregación y filtrado se hace en Python después de traer los documentos.

```python
"""
Repositorio de operaciones sobre las colecciones 'equipos' y subcolección 'servicios'.
Todas las funciones trabajan con diccionarios Python (documentos Firestore).
"""
from src.database.firebase_client import get_db
from datetime import date, datetime
from typing import Optional

# ── COLECCIONES ──────────────────────────────────────────────────
COL_EQUIPOS     = "equipos"
COL_ALERTAS_LOG = "alertas_log"
COL_ETL_LOG     = "etl_log"
SUBCOL_SERVICIOS = "servicios"

# ── EQUIPOS ──────────────────────────────────────────────────────

def upsert_equipo(codigo: str, datos: dict) -> None:
    """
    Inserta o actualiza un equipo usando su codigo_equipo como ID de documento.
    Usa merge=True para no sobrescribir campos no incluidos en datos.
    """
    db = get_db()
    ref = db.collection(COL_EQUIPOS).document(codigo)
    datos["updated_at"] = datetime.utcnow().isoformat()
    ref.set(datos, merge=True)

def get_equipo(codigo: str) -> Optional[dict]:
    """Retorna el documento del equipo o None si no existe."""
    db = get_db()
    doc = db.collection(COL_EQUIPOS).document(codigo).get()
    return doc.to_dict() if doc.exists else None

def get_all_equipos(solo_activos: bool = True) -> list[dict]:
    """Retorna lista de todos los equipos. Si solo_activos=True, filtra activo==True."""
    db = get_db()
    query = db.collection(COL_EQUIPOS)
    if solo_activos:
        query = query.where("activo", "==", True)
    return [{"id": d.id, **d.to_dict()} for d in query.stream()]

def limpiar_equipos() -> int:
    """
    Elimina todos los documentos de la colección equipos (y sus subcolecciones).
    Retorna el número de documentos eliminados.
    PRECAUCIÓN: operación irreversible. Pedir confirmación antes de llamar.
    """
    db = get_db()
    equipos = list(db.collection(COL_EQUIPOS).stream())
    count = 0
    for eq in equipos:
        # Borrar subcolección servicios primero
        for srv in eq.reference.collection(SUBCOL_SERVICIOS).stream():
            srv.reference.delete()
            count += 1
        eq.reference.delete()
        count += 1
    return count

# ── SERVICIOS (subcolección) ──────────────────────────────────────

def agregar_servicio(codigo_equipo: str, servicio: dict) -> str:
    """
    Agrega un documento a la subcolección servicios del equipo indicado.
    Retorna el ID autogenerado del documento.
    """
    db = get_db()
    ref = db.collection(COL_EQUIPOS).document(codigo_equipo)\
            .collection(SUBCOL_SERVICIOS).document()
    servicio["created_at"] = datetime.utcnow().isoformat()
    ref.set(servicio)
    return ref.id

def get_servicios_equipo(codigo_equipo: str) -> list[dict]:
    """Retorna todos los servicios de un equipo, ordenados por fecha descendente."""
    db = get_db()
    docs = db.collection(COL_EQUIPOS).document(codigo_equipo)\
             .collection(SUBCOL_SERVICIOS)\
             .order_by("fecha_servicio_vigente", direction=firestore.Query.DESCENDING)\
             .stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

def get_ultimo_servicio(codigo_equipo: str, tipo_servicio: str = None) -> Optional[dict]:
    """
    Retorna el servicio más reciente del equipo.
    Si se especifica tipo_servicio, filtra solo ese tipo.
    """
    db = get_db()
    query = db.collection(COL_EQUIPOS).document(codigo_equipo)\
              .collection(SUBCOL_SERVICIOS)
    if tipo_servicio:
        query = query.where("tipo_servicio", "==", tipo_servicio)
    query = query.order_by("fecha_servicio_vigente",
                           direction=firestore.Query.DESCENDING).limit(1)
    docs = list(query.stream())
    return {"id": docs[0].id, **docs[0].to_dict()} if docs else None

# ── CONSULTAS PARA DASHBOARD ──────────────────────────────────────

def get_estado_actual_todos() -> list[dict]:
    """
    Retorna el estado actual de todos los equipos activos.
    Para cada equipo obtiene su servicio más reciente.
    Retorna lista de dicts con campos combinados equipo + último servicio.
    """
    equipos = get_all_equipos(solo_activos=True)
    resultado = []
    for eq in equipos:
        ultimo = get_ultimo_servicio(eq["id"])
        if ultimo:
            eq.update({
                "tipo_servicio":           ultimo.get("tipo_servicio"),
                "estado_servicio":         ultimo.get("estado_servicio"),
                "estado_conformidad":      ultimo.get("estado_conformidad"),
                "fecha_servicio_vigente":  ultimo.get("fecha_servicio_vigente"),
                "fecha_proximo_servicio":  ultimo.get("fecha_proximo_servicio"),
                "proveedor":               ultimo.get("proveedor"),
                "frecuencia":              ultimo.get("frecuencia"),
                "dias_restantes":          calcular_dias_restantes(
                                               ultimo.get("fecha_proximo_servicio")
                                           ),
            })
        else:
            eq["estado_servicio"] = "Sin datos"
        resultado.append(eq)
    return resultado

def get_servicios_por_anio(anio: int, ubicacion: str = None) -> list[dict]:
    """
    Retorna todos los servicios del año indicado.
    Opcionalmente filtra por ubicación del equipo.
    Se usa para la vista de cumplimiento anual del dashboard.
    NOTA: Firestore no soporta consultas entre colecciones directamente.
    Se resuelve con Collection Group queries sobre la subcolección 'servicios'.
    """
    db = get_db()
    query = db.collection_group(SUBCOL_SERVICIOS).where("anio", "==", anio)
    docs = list(query.stream())
    servicios = [{"srv_id": d.id, **d.to_dict()} for d in docs]

    # Si se pide filtro por ubicación, cruzar con datos del equipo padre
    if ubicacion:
        servicios = [s for s in servicios if s.get("ubicacion") == ubicacion]
    return servicios

def calcular_dias_restantes(fecha_proximo_str: Optional[str]) -> Optional[int]:
    """Calcula días entre hoy y la fecha próxima. Negativo = ya venció."""
    if not fecha_proximo_str:
        return None
    try:
        fecha = date.fromisoformat(fecha_proximo_str)
        return (fecha - date.today()).days
    except ValueError:
        return None

# ── LOGS ──────────────────────────────────────────────────────────

def registrar_carga_etl(log: dict) -> str:
    """Guarda un registro de la carga ETL en la colección etl_log."""
    db = get_db()
    ref = db.collection(COL_ETL_LOG).document()
    log["fecha_carga"] = datetime.utcnow().isoformat()
    ref.set(log)
    return ref.id

def get_historial_etl(limite: int = 20) -> list[dict]:
    """Retorna los últimos N registros de carga ETL."""
    db = get_db()
    docs = db.collection(COL_ETL_LOG)\
             .order_by("fecha_carga", direction=firestore.Query.DESCENDING)\
             .limit(limite).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

def registrar_alerta(log: dict) -> str:
    """Guarda un registro de alerta enviada en la colección alertas_log."""
    db = get_db()
    ref = db.collection(COL_ALERTAS_LOG).document()
    log["fecha_envio"] = datetime.utcnow().isoformat()
    ref.set(log)
    return ref.id

def get_historial_alertas(limite: int = 30) -> list[dict]:
    """Retorna los últimos N registros de alertas enviadas."""
    db = get_db()
    docs = db.collection(COL_ALERTAS_LOG)\
             .order_by("fecha_envio", direction=firestore.Query.DESCENDING)\
             .limit(limite).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]
```

**Estructura de carpetas del proyecto:**
```
pame_module/
├── .env                        ← NUNCA subir a git
├── .env.example
├── .gitignore                  ← incluir firebase_credentials.json y .env
├── firebase_credentials.json   ← NUNCA subir a git
├── requirements.txt
├── run.py
├── src/
│   ├── database/
│   │   ├── firebase_client.py
│   │   └── equipos_repo.py
│   ├── etl/
│   │   ├── extractor.py
│   │   ├── transformer.py
│   │   ├── loader.py
│   │   └── pipeline.py
│   ├── alertas/
│   │   ├── motor_alertas.py
│   │   └── email_sender.py
│   └── dashboard/
│       ├── app.py
│       ├── charts.py
│       └── helpers.py
├── tests/
│   ├── test_etl.py
│   ├── test_alertas.py
│   └── test_metricas_etl.py
└── data/
    └── samples/
        ├── cronograma_sample.csv
        ├── cronograma_historico.json
        └── equipos_nuevos.csv
```

**`requirements.txt` esperado:**
```
firebase-admin>=6.0.0
google-cloud-firestore>=2.0.0
pandas>=2.0.0
openpyxl>=3.1.0
streamlit>=1.35.0
python-dotenv>=1.0.0
schedule>=1.2.0
```

**Entregable esperado:**
- `firebase_client.py` y `equipos_repo.py` completos.
- `requirements.txt` con todas las dependencias.
- `.env.example` con todas las variables necesarias.
- `.gitignore` correctamente configurado.

---

## BLOQUE 2 — MÓDULO ETL (Extracción, Transformación y Carga)

### Objetivo
Construir el pipeline ETL que acepta CSV, Excel y JSON de **estructura variable**, los normaliza y los carga a Firestore.

### Tarea 2.1 — Extractor multi-formato con detección de estructura JSON

Crear `src/etl/extractor.py`:

El extractor debe manejar los tres formatos. El reto principal está en el JSON, porque puede llegar con estructuras distintas. Implementar detección automática:

```python
"""
Extractor multi-formato para el PAME de Laproff.
Detecta el formato por extensión y normaliza a lista de diccionarios.
El JSON es el más complejo por su estructura variable.
"""
import pandas as pd
import json
from pathlib import Path
from typing import Union

class ExtractorError(Exception):
    """Error descriptivo de extracción con mensaje en español."""
    pass

def extract(filepath: str) -> tuple[list[dict], dict]:
    """
    Lee un archivo CSV, Excel o JSON y retorna:
    - lista de diccionarios (un dict por registro)
    - dict con metadatos: {"formato": str, "estructura_detectada": str, "total_registros": int}

    Retorna lista de dicts en lugar de DataFrame para preservar la flexibilidad
    de los campos extra que puede traer el JSON.
    """
    path = Path(filepath)
    if not path.exists():
        raise ExtractorError(f"Archivo no encontrado: {filepath}")

    ext = path.suffix.lower()

    if ext == ".csv":
        return _extract_csv(filepath)
    elif ext in (".xlsx", ".xls"):
        return _extract_excel(filepath)
    elif ext == ".json":
        return _extract_json(filepath)
    else:
        raise ExtractorError(
            f"Formato '{ext}' no soportado. Use .csv, .xlsx o .json"
        )

def _extract_csv(filepath: str) -> tuple[list[dict], dict]:
    """Lee CSV con detección automática de separador y encoding."""
    # Intentar encodings comunes en archivos latinoamericanos
    for encoding in ["latin-1", "utf-8", "cp1252"]:
        for sep in [";", ",", "\t"]:
            try:
                df = pd.read_csv(filepath, encoding=encoding, sep=sep)
                if len(df.columns) > 1:  # separador correcto si hay más de 1 columna
                    registros = df.where(pd.notna(df), None).to_dict(orient="records")
                    return registros, {
                        "formato": "csv",
                        "encoding_detectado": encoding,
                        "separador_detectado": sep,
                        "total_registros": len(registros)
                    }
            except Exception:
                continue
    raise ExtractorError(
        f"No se pudo leer el CSV. Verifique que el archivo no esté dañado."
    )

def _extract_excel(filepath: str) -> tuple[list[dict], dict]:
    """Lee Excel, primera hoja por defecto."""
    try:
        df = pd.read_excel(filepath, engine="openpyxl")
        registros = df.where(pd.notna(df), None).to_dict(orient="records")
        return registros, {
            "formato": "excel",
            "total_registros": len(registros)
        }
    except Exception as e:
        raise ExtractorError(f"Error al leer Excel: {str(e)}")

def _extract_json(filepath: str) -> tuple[list[dict], dict]:
    """
    Lee JSON con detección automática de estructura.
    Soporta múltiples formatos posibles:

    Formato A — Array plano (el más común):
        [{"Código del Equipo": "LS001", ...}, ...]

    Formato B — Objeto con clave conocida:
        {"equipos": [...]} o {"servicios": [...]} o {"data": [...]}

    Formato C — Objeto con servicios anidados por equipo:
        {"LS001": {"nombre": "...", "servicios": [...]}, "LS002": {...}}

    Formato D — Un solo objeto (un registro):
        {"Código del Equipo": "LS001", ...}

    Los campos no reconocidos se preservan en 'campos_extra'.
    """
    try:
        with open(filepath, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        raise ExtractorError(f"Error al leer JSON: {str(e)}")

    # Formato A: array de objetos planos
    if isinstance(raw, list):
        return raw, {"formato": "json", "estructura_detectada": "array_plano",
                     "total_registros": len(raw)}

    # Formato B: objeto con una clave que contiene el array
    if isinstance(raw, dict):
        claves_lista = [k for k, v in raw.items() if isinstance(v, list)]
        if len(claves_lista) == 1:
            registros = raw[claves_lista[0]]
            return registros, {"formato": "json",
                               "estructura_detectada": f"objeto_clave_{claves_lista[0]}",
                               "total_registros": len(registros)}

        # Buscar clave conocida
        for clave in ["equipos", "servicios", "data", "records", "items", "cronograma"]:
            if clave in raw and isinstance(raw[clave], list):
                registros = raw[clave]
                return registros, {"formato": "json",
                                   "estructura_detectada": f"objeto_clave_{clave}",
                                   "total_registros": len(registros)}

        # Formato C: objeto de objetos (clave = codigo_equipo)
        primer_valor = next(iter(raw.values()))
        if isinstance(primer_valor, dict):
            registros = []
            for codigo, datos in raw.items():
                if isinstance(datos, dict):
                    # Si tiene subarray de servicios, aplanar
                    if "servicios" in datos and isinstance(datos["servicios"], list):
                        for srv in datos["servicios"]:
                            reg = {"Código del Equipo": codigo}
                            reg.update({k: v for k, v in datos.items() if k != "servicios"})
                            reg.update(srv)
                            registros.append(reg)
                    else:
                        datos.setdefault("Código del Equipo", codigo)
                        registros.append(datos)
            return registros, {"formato": "json",
                                "estructura_detectada": "objeto_de_objetos",
                                "total_registros": len(registros)}

        # Formato D: un solo objeto
        return [raw], {"formato": "json", "estructura_detectada": "objeto_unico",
                       "total_registros": 1}

    raise ExtractorError(
        "Estructura JSON no reconocida. "
        "Se esperaba un array o un objeto con lista de registros."
    )
```

### Tarea 2.2 — Transformador y validador

Crear `src/etl/transformer.py`:

```python
"""
Transformador del ETL PAME.
Normaliza registros de cualquier formato al esquema interno de Firestore.
Los campos no reconocidos NO se descartan — se guardan en 'campos_extra'.
"""
from datetime import date, datetime
from typing import Optional

# Mapeo de nombres de columna → nombre interno en Firestore
# Incluye variantes conocidas (con/sin tilde, mayúsculas, etc.)
COLUMN_MAPPING = {
    # Nombres exactos del CSV de Laproff
    "Equipo"                                       : "nombre_equipo",
    "Código del Equipo"                            : "codigo_equipo",
    "Fecha de Servicio Vigente"                    : "fecha_servicio_vigente",
    "Fecha de Ejecución del Servicio Programado"   : "fecha_ejecucion_programada",
    "Tipo de Servicio"                             : "tipo_servicio",
    "Frecuencia"                                   : "frecuencia",
    "Estado del Servicio"                          : "estado_servicio",
    "Estado de Entrega"                            : "estado_entrega",
    "Estado de Conformidad"                        : "estado_conformidad",
    "Proveedor"                                    : "proveedor",
    "Período Próximo Servicio"                     : "periodo_proximo_servicio",
    "Activo Fijo"                                  : "activo_fijo",
    "Serie Equipo"                                 : "serie_equipo",
    "Ubicación"                                    : "ubicacion",
    # Variantes alternativas que pueden venir en JSON
    "codigo"          : "codigo_equipo",
    "code"            : "codigo_equipo",
    "equipo_codigo"   : "codigo_equipo",
    "nombre"          : "nombre_equipo",
    "name"            : "nombre_equipo",
    "ubicacion"       : "ubicacion",
    "location"        : "ubicacion",
    "area"            : "ubicacion",
    "tipo"            : "tipo_servicio",
    "service_type"    : "tipo_servicio",
    "proveedor"       : "proveedor",
    "provider"        : "proveedor",
    "frecuencia"      : "frecuencia",
    "frequency"       : "frecuencia",
}

# Campos internos conocidos del esquema
CAMPOS_CONOCIDOS = set(COLUMN_MAPPING.values())

# Valores de texto que representan nulo en los datos de Laproff
VALORES_NULOS = {"NO IDENTIFICADO", "NO REGISTRA", "NO APLICA", "", "nan", "NaN", "N/A"}

# Valores válidos para campos categóricos
TIPOS_SERVICIO_VALIDOS = {
    "Calibración", "Calificación", "Calificación PQ", "Calificación OQ",
    "Mantenimiento Preventivo", "Mantenimiento Correctivo",
    "Verificación Temperatura y Humedad", "Mapeo", "Diagnóstico"
}
FRECUENCIAS_VALIDAS = {"Anual", "Semestral", "Trimestral", "Bienal", "Trienal", "NoAplica"}
ESTADOS_SERVICIO_VALIDOS = {"Vigente", "Programar", "En ejecución", "Vencido"}


def transform(registros: list[dict]) -> tuple[list[dict], list[dict], dict]:
    """
    Transforma una lista de registros crudos al esquema interno.
    Retorna:
    - lista de registros válidos listos para Firestore
    - lista de registros inválidos con razón
    - dict con reporte de calidad
    """
    validos = []
    invalidos = []
    duplicados_eliminados = 0
    nulos_normalizados = 0
    fechas_ejecucion_vacias = 0
    campos_extra_encontrados = 0
    vistos = set()  # para deduplicación

    for raw in registros:
        # 1. Mapear columnas al nombre interno
        mapeado = {}
        campos_extra = {}
        for k, v in raw.items():
            k_limpio = str(k).strip()
            nombre_interno = COLUMN_MAPPING.get(k_limpio)
            if nombre_interno:
                mapeado[nombre_interno] = v
            else:
                # Campo desconocido: preservar en campos_extra
                campos_extra[k_limpio] = v

        if campos_extra:
            mapeado["campos_extra"] = campos_extra
            campos_extra_encontrados += len(campos_extra)

        # 2. Validar campos obligatorios
        codigo = _limpiar_str(mapeado.get("codigo_equipo"))
        nombre = _limpiar_str(mapeado.get("nombre_equipo"))

        if not codigo:
            invalidos.append({"registro": raw, "razon": "Falta código de equipo (campo obligatorio)"})
            continue
        if not nombre:
            # Si no hay nombre, usar el código como nombre antes de rechazar
            nombre = codigo
            mapeado["nombre_equipo"] = nombre

        # 3. Deduplicar por (codigo + tipo_servicio + fecha_servicio_vigente)
        clave_dup = (
            codigo,
            str(mapeado.get("tipo_servicio", "")),
            str(mapeado.get("fecha_servicio_vigente", ""))
        )
        if clave_dup in vistos:
            duplicados_eliminados += 1
            continue
        vistos.add(clave_dup)

        # 4. Normalizar valores nulos textuales → None
        for campo in ["activo_fijo", "serie_equipo"]:
            val = str(mapeado.get(campo, "")).strip().upper()
            if val in {v.upper() for v in VALORES_NULOS}:
                mapeado[campo] = None
                nulos_normalizados += 1

        # 5. Convertir fechas
        mapeado["fecha_servicio_vigente"] = _parsear_fecha(
            mapeado.get("fecha_servicio_vigente")
        )

        fecha_ejec = mapeado.get("fecha_ejecucion_programada")
        if not fecha_ejec or str(fecha_ejec).strip() in {"", "nan", "None"}:
            mapeado["fecha_ejecucion_programada"] = None
            fechas_ejecucion_vacias += 1
        else:
            mapeado["fecha_ejecucion_programada"] = _parsear_fecha(fecha_ejec)

        # 6. Convertir período próximo servicio (MM/YYYY → fecha ISO + guardar original)
        periodo = str(mapeado.get("periodo_proximo_servicio", "")).strip()
        mapeado["periodo_proximo_servicio"] = periodo  # guardar original
        mapeado["fecha_proximo_servicio"] = _parsear_periodo(periodo)

        # 7. Normalizar ubicación (unificar mayúsculas/minúsculas)
        if mapeado.get("ubicacion"):
            mapeado["ubicacion"] = str(mapeado["ubicacion"]).strip().upper()

        # 8. Calcular estado_servicio si está vacío o inválido
        estado_actual = mapeado.get("estado_servicio")
        if not estado_actual or estado_actual not in ESTADOS_SERVICIO_VALIDOS:
            mapeado["estado_servicio"] = calcular_estado_servicio(
                mapeado.get("fecha_proximo_servicio")
            )

        # 9. Agregar campo anio para facilitar consultas históricas
        if mapeado.get("fecha_servicio_vigente"):
            try:
                mapeado["anio"] = int(mapeado["fecha_servicio_vigente"][:4])
            except (ValueError, TypeError):
                mapeado["anio"] = None

        # 10. Agregar metadatos
        mapeado["codigo_equipo"] = codigo
        mapeado["nombre_equipo"] = nombre
        validos.append(mapeado)

    reporte = {
        "total_registros":          len(registros),
        "validos":                  len(validos),
        "invalidos":                len(invalidos),
        "duplicados_eliminados":    duplicados_eliminados,
        "nulos_normalizados":       nulos_normalizados,
        "fechas_ejecucion_vacias":  fechas_ejecucion_vacias,
        "campos_extra_encontrados": campos_extra_encontrados,
        "registros_invalidos":      invalidos,
    }
    return validos, invalidos, reporte


def calcular_estado_servicio(fecha_proximo_iso: Optional[str]) -> str:
    if not fecha_proximo_iso:
        return "Vencido"
    try:
        fecha = date.fromisoformat(fecha_proximo_iso)
        dias = (fecha - date.today()).days
        if dias < 0:
            return "Vencido"
        elif dias <= 30:
            return "Programar"
        else:
            return "Vigente"
    except ValueError:
        return "Vencido"


def _limpiar_str(valor) -> Optional[str]:
    if valor is None:
        return None
    s = str(valor).strip()
    return s if s and s.lower() not in {"nan", "none", ""} else None


def _parsear_fecha(valor) -> Optional[str]:
    """Intenta parsear una fecha en múltiples formatos y retorna ISO 8601 (YYYY-MM-DD)."""
    if not valor or str(valor).strip() in {"", "nan", "None"}:
        return None
    s = str(valor).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None  # no se pudo parsear


def _parsear_periodo(periodo: str) -> Optional[str]:
    """Convierte MM/YYYY al primer día del mes en ISO 8601."""
    if not periodo or "/" not in periodo:
        return None
    try:
        partes = periodo.strip().split("/")
        mes, anio = int(partes[0]), int(partes[1])
        return date(anio, mes, 1).isoformat()
    except (ValueError, IndexError):
        return None
```

### Tarea 2.3 — Cargador a Firestore

Crear `src/etl/loader.py`:

```python
"""
Cargador ETL: toma registros transformados y los escribe en Firestore.
Separa cada registro en su parte de equipo (colección equipos)
y su parte de servicio (subcolección servicios).
"""
import time
from src.database.equipos_repo import upsert_equipo, agregar_servicio, registrar_carga_etl

# Campos que pertenecen al documento del equipo (datos maestros)
CAMPOS_EQUIPO = {
    "codigo_equipo", "nombre_equipo", "serie_equipo",
    "activo_fijo", "ubicacion", "activo"
}

# Campos que pertenecen al documento de servicio
CAMPOS_SERVICIO = {
    "tipo_servicio", "frecuencia", "fecha_servicio_vigente",
    "fecha_ejecucion_programada", "periodo_proximo_servicio",
    "fecha_proximo_servicio", "estado_servicio", "estado_entrega",
    "estado_conformidad", "proveedor", "anio", "campos_extra"
}

def load(registros_validos: list[dict], nombre_archivo: str,
         reporte_transform: dict, dry_run: bool = False) -> dict:
    """
    Carga los registros válidos a Firestore.
    Si dry_run=True, simula la carga sin escribir nada.
    Retorna reporte de carga.
    """
    inicio = time.time()
    insertados = 0
    actualizados = 0
    errores = []

    for reg in registros_validos:
        codigo = reg.get("codigo_equipo")
        if not codigo:
            continue

        # Separar datos de equipo vs datos de servicio
        datos_equipo = {k: v for k, v in reg.items() if k in CAMPOS_EQUIPO}
        datos_equipo.setdefault("activo", True)

        datos_servicio = {k: v for k, v in reg.items() if k in CAMPOS_SERVICIO}
        # Agregar referencia de ubicación al servicio para facilitar Collection Group queries
        datos_servicio["ubicacion"] = reg.get("ubicacion")

        if dry_run:
            insertados += 1
            continue

        try:
            upsert_equipo(codigo, datos_equipo)
            agregar_servicio(codigo, datos_servicio)
            insertados += 1
        except Exception as e:
            errores.append({"codigo": codigo, "error": str(e)})

    duracion = round(time.time() - inicio, 2)

    reporte_carga = {
        "archivo":              nombre_archivo,
        "dry_run":              dry_run,
        "insertados":           insertados,
        "actualizados":         actualizados,
        "errores":              errores,
        "duracion_segundos":    duracion,
        "reporte_transformacion": reporte_transform,
    }

    if not dry_run:
        registrar_carga_etl(reporte_carga)

    return reporte_carga
```

### Tarea 2.4 — Pipeline completo

Crear `src/etl/pipeline.py`:

```python
"""
Pipeline ETL completo: extrae → transforma → carga.
Punto de entrada para procesar cualquier archivo al sistema PAME.
"""
from src.etl.extractor import extract
from src.etl.transformer import transform
from src.etl.loader import load
from pathlib import Path

def run_pipeline(filepath: str, dry_run: bool = False) -> dict:
    """
    Ejecuta el pipeline ETL completo sobre un archivo.

    Args:
        filepath: ruta al archivo (.csv, .xlsx, .json)
        dry_run: si True, analiza y reporta sin cargar a Firestore

    Returns:
        dict con reporte completo de extracción, transformación y carga
    """
    nombre_archivo = Path(filepath).name

    # Paso 1: Extracción
    print(f"[ETL] Extrayendo: {nombre_archivo}")
    registros_crudos, meta_extraccion = extract(filepath)
    print(f"[ETL] Registros extraídos: {meta_extraccion['total_registros']}")

    # Paso 2: Transformación
    print("[ETL] Transformando y validando...")
    validos, invalidos, reporte_transform = transform(registros_crudos)
    print(f"[ETL] Válidos: {reporte_transform['validos']} | "
          f"Inválidos: {reporte_transform['invalidos']} | "
          f"Duplicados eliminados: {reporte_transform['duplicados_eliminados']}")

    # Paso 3: Carga
    modo = "SIMULACIÓN (dry_run)" if dry_run else "CARGA REAL"
    print(f"[ETL] Cargando a Firestore ({modo})...")
    reporte_carga = load(validos, nombre_archivo, reporte_transform, dry_run=dry_run)
    print(f"[ETL] Completado en {reporte_carga['duracion_segundos']}s")

    return {
        "extraccion":    meta_extraccion,
        "transformacion": reporte_transform,
        "carga":         reporte_carga,
    }
```

**Entregable esperado:**
- Los 4 módulos ETL completos con manejo de errores en español.
- `tests/test_etl.py` con casos de prueba para los 3 formatos.
- Los archivos de muestra adjuntos ya listos en `data/samples/` (ver Bloque 5).

---

## BLOQUE 3 — MOTOR DE ALERTAS CON ENVÍO POR CORREO

### Objetivo
Construir el motor que calcula alertas desde Firestore y las envía por correo electrónico con priorización.

### Tarea 3.1 — Motor de alertas

Crear `src/alertas/motor_alertas.py`:

```python
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional
from src.database.equipos_repo import get_estado_actual_todos

@dataclass
class Alerta:
    codigo_equipo:  str
    nombre_equipo:  str
    ubicacion:      str
    proveedor:      Optional[str]
    tipo_servicio:  Optional[str]
    fecha_proxima:  Optional[str]   # ISO 8601
    dias_restantes: Optional[int]   # negativo = ya venció
    prioridad:      str             # "CRITICA", "ALTA", "MEDIA"
    mensaje:        str

def generar_alertas() -> List[Alerta]:
    """
    Consulta Firestore, obtiene el estado actual de todos los equipos
    y genera lista de alertas priorizadas.

    Prioridades:
    - CRITICA: vencido (dias_restantes < 0) o vence en ≤ 7 días
    - ALTA:    vence entre 8 y 15 días
    - MEDIA:   vence entre 16 y 30 días
    """
    equipos = get_estado_actual_todos()
    alertas = []

    for eq in equipos:
        dias = eq.get("dias_restantes")
        if dias is None:
            continue

        if dias < 0:
            prioridad = "CRITICA"
            mensaje = (f"VENCIDO hace {abs(dias)} días — "
                       f"Tipo: {eq.get('tipo_servicio', 'N/A')} — "
                       f"Proveedor: {eq.get('proveedor', 'N/A')}")
        elif dias <= 7:
            prioridad = "CRITICA"
            mensaje = (f"Vence en {dias} días — "
                       f"Tipo: {eq.get('tipo_servicio', 'N/A')} — "
                       f"Acción inmediata requerida")
        elif dias <= 15:
            prioridad = "ALTA"
            mensaje = f"Vence en {dias} días — Programar servicio pronto"
        elif dias <= 30:
            prioridad = "MEDIA"
            mensaje = f"Vence en {dias} días — Pendiente de programar"
        else:
            continue  # sin alerta si queda más de 30 días

        alertas.append(Alerta(
            codigo_equipo  = eq.get("id", ""),
            nombre_equipo  = eq.get("nombre_equipo", ""),
            ubicacion      = eq.get("ubicacion", ""),
            proveedor      = eq.get("proveedor"),
            tipo_servicio  = eq.get("tipo_servicio"),
            fecha_proxima  = eq.get("fecha_proximo_servicio"),
            dias_restantes = dias,
            prioridad      = prioridad,
            mensaje        = mensaje,
        ))

    # Ordenar: primero las críticas, luego por días restantes ascendente
    alertas.sort(key=lambda a: (
        0 if a.prioridad == "CRITICA" else 1 if a.prioridad == "ALTA" else 2,
        a.dias_restantes if a.dias_restantes is not None else 999
    ))
    return alertas

def agrupar_por_area(alertas: List[Alerta]) -> dict[str, List[Alerta]]:
    """Agrupa alertas por área/ubicación para envío segmentado."""
    grupos = {}
    for alerta in alertas:
        area = alerta.ubicacion or "SIN ÁREA"
        grupos.setdefault(area, []).append(alerta)
    return grupos
```

### Tarea 3.2 — Envío de correo electrónico

Crear `src/alertas/email_sender.py`:

Variables de entorno requeridas:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=correo@laproff.com
SMTP_PASSWORD=app_password_aqui
EMAIL_REMITENTE=pame-alertas@laproff.com
EMAIL_DESTINATARIOS=jefe.validacionesymetrologia@laproff.com,supervisor@laproff.com
```

El módulo debe implementar:

1. `generar_html_alerta(alertas)` → construye el cuerpo HTML del correo con tablas separadas por prioridad (CRÍTICA en rojo, ALTA en amarillo, MEDIA en gris), usando la paleta de colores del proyecto.
2. `enviar_alerta_diaria(alertas)` → envía resumen diario a todos los destinatarios configurados. Registra el envío en la colección `alertas_log` de Firestore.
3. `enviar_alerta_critica_inmediata(alerta)` → envía correo urgente individual cuando un equipo entra en estado CRÍTICO. Asunto marcado con `[URGENTE]`.
4. `programar_alertas_diarias(hora="08:00")` → usa la librería `schedule` para ejecutar `enviar_alerta_diaria` automáticamente cada día a la hora configurada.

**Entregable esperado:**
- `motor_alertas.py` y `email_sender.py` completos.
- `tests/test_alertas.py` con prueba en modo dry-run (sin enviar correo real).
- Sección en el README explicando cómo configurar el correo SMTP.

---

## BLOQUE 4 — DASHBOARD STREAMLIT (KPIs + Vista Histórica Anual)

### Objetivo
Construir el dashboard consultando directamente Firestore, con dos grandes secciones: estado actual y cumplimiento histórico anual.

> **Diferenciador clave:** el aplicativo existente de Laproff muestra estado en tiempo real. Este dashboard agrega la vista histórica por año para evaluar el cumplimiento de metas anuales del cronograma.

### Tarea 4.1 — Estructura general

El dashboard tiene las siguientes secciones en el sidebar:
1. Dashboard KPIs (estado actual)
2. Cumplimiento Anual ← *prioridad alta, diferenciador*
3. Inventario de Equipos
4. Cronograma (próximos 90 días)
5. Alertas Activas
6. Migración ETL

### Tarea 4.2 — Sección "Dashboard KPIs"

KPIs diferenciales (no duplicar los que ya tiene el aplicativo de Laproff):

| KPI | Descripción | Cálculo desde Firestore |
|-----|-------------|------------------------|
| % Equipos al día | Proporción con estado Vigente | `count(Vigente) / total * 100` |
| Días promedio hasta vencimiento | Promedio de días restantes (solo vigentes) | `media(dias_restantes > 0)` |
| % Cumplimiento del cronograma anual | Servicios ejecutados vs planeados en año en curso | `count(anio=actual) / planeados * 100` |
| Equipos sin intervención > 1 año | Equipos con última fecha de servicio hace más de 365 días | `count` |
| Tasa de conformidad del periodo | Servicios con Cumple / total con resultado | `count(Cumple) / count(Cumple+NoCumple) * 100` |
| Top 3 áreas con mayor riesgo | Áreas con más equipos Vencidos o en Programar | `groupby(ubicacion).count()` |

Visualizaciones: dona de distribución de estados, barras por área, línea de tendencia 6 meses.

### Tarea 4.3 — Sección "Cumplimiento Anual" ← PRIORIDAD ALTA

Usa `get_servicios_por_anio(anio)` del repositorio (Collection Group query sobre `servicios`).

Componentes:
1. Selector de año + selector de área (opcional).
2. Métricas del año: total ejecutados, planeados, % cumplimiento, conformes vs no conformes.
3. Tabla por área: Área | Planeados | Ejecutados | % Cumplimiento | Conformes | No conformes.
4. Comparativo interanual: barras agrupadas por año, filtrable por área.
5. Semáforo: verde ≥ 90%, amarillo 70–90%, rojo < 70%.
6. Evolución mensual: línea de servicios ejecutados vs planeados por mes dentro del año.

### Tarea 4.4 — Sección "Inventario de Equipos"

Tabla interactiva con filtros por área, estado, proveedor, año. Búsqueda por código/nombre. Exportar a Excel. Datos desde `get_all_equipos()` + estado calculado.

### Tarea 4.5 — Sección "Cronograma"

Lista de servicios de los próximos 90 días. Filtros por área y tipo de servicio. Indicador visual de urgencia. Botón "Generar reporte" (exportar a Excel).

### Tarea 4.6 — Sección "Alertas Activas"

Lista de alertas priorizadas (desde `generar_alertas()`). Botón "Enviar alertas ahora". Historial de alertas enviadas desde `get_historial_alertas()`.

### Tarea 4.7 — Sección "Migración ETL"

Uploader de archivos (CSV, Excel, JSON). Botón "Analizar" (dry_run=True). Botón "Cargar a Firestore". Log en tiempo real. Historial de cargas desde `get_historial_etl()`. Botón "Limpiar base de datos" con confirmación explícita (usa `limpiar_equipos()`).

**Paleta de colores Streamlit:**
```python
COLORS = {
    "Vigente":       "#10B981",
    "Programar":     "#F59E0B",
    "En ejecución":  "#EF4444",
    "Vencido":       "#DC2626",
    "Sin datos":     "#94A3B8",
    "primary":       "#00A99D",
    "sidebar":       "#0B3533",
}
```

**Entregable esperado:**
- `app.py`, `charts.py`, `helpers.py` completos.
- Dashboard funcional con `streamlit run src/dashboard/app.py`.

---

## BLOQUE 5 — INTEGRACIÓN, PRUEBAS Y DOCUMENTACIÓN

### Tarea 5.1 — Script de ejecución completo

Crear `run.py` en la raíz:

```python
"""
Punto de entrada principal del módulo PAME.
Uso:
    python run.py --mode etl --file data/samples/cronograma_sample.csv
    python run.py --mode etl --file data/samples/cronograma_historico.json --dry-run
    python run.py --mode alertas
    python run.py --mode dashboard
    python run.py --mode scheduler
    python run.py --mode limpiar    ← pide confirmación antes de borrar
"""
```

### Tarea 5.2 — Pruebas con datos representativos

> ✅ **Los tres archivos de muestra ya están generados y se entregan junto con este instructivo.** Copiarlos en `data/samples/`. No es necesario crearlos.

**`cronograma_sample.csv`** — 55 filas ficticias, estructura exacta del CSV real de Laproff:
- Separador `;`, encoding `latin-1`.
- Estados: `Vigente` (23), `Vencido` (15), `Programar` (12), `En ejecución` (5).
- Conformidades: `Cumple` (23), `No Cumple` (15), `Pendiente de Calificar` (17).
- 3 filas duplicadas exactas intencionales → para probar deduplicación del transformador.
- 2 filas inválidas intencionales (sin código/nombre) → para probar validación.
- Columna `Fecha de Ejecución del Servicio Programado` completamente vacía en todas las filas.
- Mezcla de `NO IDENTIFICADO`, `NO REGISTRA`, `NO APLICA` y códigos `AF10-XXXXX`.

**`cronograma_historico.json`** — 123 registros de 3 años (2022, 2023, 2024):
- Formato array plano con claves exactas del CSV real.
- Distribución de conformidad distinta por año para que la vista histórica sea informativa.
- `Fecha de Ejecución del Servicio Programado` como `null` en todos los registros.

**`equipos_nuevos.csv`** — 10 filas con códigos `CC900-26` a `CC909-26`:
- Equipos inexistentes en el sample → para probar carga incremental (upsert en Firestore).

### Tarea 5.3 — Validación de métricas ETL

Crear `tests/test_metricas_etl.py` que verifique al procesar `cronograma_sample.csv`:
- Se detectan exactamente 3 duplicados.
- Se detectan exactamente 2 registros inválidos.
- Los campos `NO REGISTRA` / `NO IDENTIFICADO` se convierten a `None`.
- Las fechas `DD/MM/YYYY` se convierten correctamente a ISO 8601.
- El campo `anio` se calcula correctamente para cada registro.
- Los campos extra de JSON se guardan en `campos_extra` sin perderse.

### Tarea 5.4 — README técnico

Crear `README.md` con:
1. Descripción del proyecto, stack y arquitectura NoSQL.
2. Instalación: `pip install -r requirements.txt`.
3. Configuración de Firebase (pasos para obtener `firebase_credentials.json`).
4. Configuración de `.env`.
5. Ejecutar el ETL con los tres formatos de archivo.
6. Iniciar el dashboard.
7. Configurar alertas por correo SMTP.
8. Limpiar y recargar la base de datos.
9. Estructura de carpetas.
10. Glosario metrológico.

**Entregable esperado:**
- `run.py` funcional.
- ~~Archivos de muestra~~ → **ya entregados**. Solo copiar en `data/samples/`.
- `tests/test_metricas_etl.py` ejecutable con `pytest`.
- `README.md` completo.

---

## RESUMEN DE ENTREGAS POR BLOQUE

| Bloque | Entrega a Antigravity | Entregable esperado |
|--------|-----------------------|---------------------|
| **Bloque 0** | Contexto + NoSQL + dominio + diseño | Confirmación + preguntas + estructura de carpetas |
| **Bloque 1** | Modelo Firestore + módulo conexión | `firebase_client.py` + `equipos_repo.py` + `requirements.txt` |
| **Bloque 2** | ETL completo multi-formato | `extractor.py` + `transformer.py` + `loader.py` + `pipeline.py` |
| **Bloque 3** | Alertas + correo | `motor_alertas.py` + `email_sender.py` + tests |
| **Bloque 4** | Dashboard Streamlit | `app.py` + `charts.py` + `helpers.py` |
| **Bloque 5** | Integración y cierre | `run.py` + `README.md` + `test_metricas_etl.py` |

> 📎 **Archivos adjuntos** (entregar junto con el Bloque 2):
> - `cronograma_sample.csv` — 55 filas ficticias, estructura real Laproff
> - `cronograma_historico.json` — 123 registros, 3 años de historial
> - `equipos_nuevos.csv` — 10 equipos para prueba de carga incremental

---

## NOTAS IMPORTANTES PARA CADA ENTREGA A ANTIGRAVITY

1. **Siempre incluir el contexto global** en cada entrega — Antigravity no recuerda sesiones anteriores.
2. **Base de datos NoSQL (Firestore)**, no SQL. Sin tablas, sin JOINs. Los datos se consultan en Python.
3. **Nunca hardcodear credenciales.** Todo en `.env` o archivo externo excluido del repositorio.
4. **Los campos extra del JSON se preservan** en `campos_extra: {}` — nunca descartar información desconocida.
5. **Los archivos de muestra son ficticios** — no usar datos reales de Laproff en ningún test.
6. **El módulo es independiente del aplicativo existente** de Laproff — no conectarse a él.
7. **Comentar el código en español** — el usuario final es hispanohablante.
8. **Mensajes de error en español y descriptivos** — el usuario final no es desarrollador.

---

*Documento generado para el proyecto de práctica académica de Juliana González Afanador — Universidad de Antioquia — Bioingeniería — Semestre 10 — 2026*
