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
VALORES_NULOS = {"NO IDENTIFICADO", "NO REGISTRA", "NO APLICA", "", "nan", "NaN", "N/A", "NONE", "NULL"}

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
        if not fecha_ejec or str(fecha_ejec).strip() in {"", "nan", "None", "null", "NULL"}:
            mapeado["fecha_ejecucion_programada"] = None
            fechas_ejecucion_vacias += 1
        else:
            mapeado["fecha_ejecucion_programada"] = _parsear_fecha(fecha_ejec)

        # 6. Convertir período próximo servicio (MM/YYYY → fecha ISO + guardar original)
        periodo = str(mapeado.get("periodo_proximo_servicio", "")).strip()
        if not periodo or periodo.upper() in VALORES_NULOS:
            mapeado["periodo_proximo_servicio"] = None
            mapeado["fecha_proximo_servicio"] = None
        else:
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
    return s if s and s.lower() not in {"nan", "none", "", "null"} else None


def _parsear_fecha(valor) -> Optional[str]:
    """Intenta parsear una fecha en múltiples formatos y retorna ISO 8601 (YYYY-MM-DD)."""
    if not valor or str(valor).strip() in {"", "nan", "None", "null", "NULL"}:
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
