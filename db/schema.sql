-- ══════════════════════════════════════════════════════════════════════════════
-- db/schema.sql
-- Schema completo del módulo complementario PAME
-- Ejecutar en el SQL Editor de Supabase (una sola vez)
-- ══════════════════════════════════════════════════════════════════════════════

-- Habilitar extensión para UUID automáticos
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ──────────────────────────────────────────────────────────────────────────────
-- 1. PROVEEDORES
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS proveedores (
    id            UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre        TEXT        NOT NULL UNIQUE,
    nit           TEXT,
    contacto      TEXT,
    email         TEXT,
    telefono      TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE proveedores IS 'Proveedores de servicios metrológicos registrados en el PAME';

-- ──────────────────────────────────────────────────────────────────────────────
-- 2. EQUIPOS
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS equipos (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo_equipo       TEXT        NOT NULL UNIQUE,
    nombre              TEXT        NOT NULL,
    serie               TEXT,
    modelo              TEXT,
    fabricante          TEXT,
    proveedor_id        UUID        REFERENCES proveedores(id) ON DELETE SET NULL,
    proveedor_nombre    TEXT,                          -- desnormalizado para búsqueda rápida
    ubicacion           TEXT,
    area                TEXT,
    estado_equipo       TEXT        NOT NULL DEFAULT 'En Servicio'
                            CHECK (estado_equipo IN (
                                'En Servicio', 'Fuera de Uso',
                                'En Reparación', 'Dado de Baja')),
    es_usable           TEXT        DEFAULT 'Disponible'
                            CHECK (es_usable IN (
                                'Disponible', 'No Disponible', 'En Préstamo')),
    estado_aprobacion   TEXT        DEFAULT 'Borrador'
                            CHECK (estado_aprobacion IN (
                                'Borrador', 'Pendiente', 'Aprobado', 'Rechazado')),
    activo_fijo         TEXT,
    mide_ambiente       BOOLEAN     DEFAULT FALSE,
    criticidad          TEXT        DEFAULT 'Media'
                            CHECK (criticidad IN ('Alta', 'Media', 'Baja')),
    fecha_solicitud     DATE,
    fecha_entrega_area  DATE,
    fecha_aprobacion    DATE,
    creado_por          TEXT,
    aprobado_por        TEXT,
    migracion_id        UUID,                          -- referencia al lote de migración
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE equipos IS 'Inventario de equipos de medición del PAME Laproff';
COMMENT ON COLUMN equipos.codigo_equipo IS 'Código único del equipo p.ej. LS1871';
COMMENT ON COLUMN equipos.criticidad IS 'Nivel de criticidad: Alta (impacta directamente calidad del producto), Media, Baja';

-- Índices para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_equipos_area ON equipos(area);
CREATE INDEX IF NOT EXISTS idx_equipos_estado ON equipos(estado_equipo);
CREATE INDEX IF NOT EXISTS idx_equipos_proveedor ON equipos(proveedor_id);

-- ──────────────────────────────────────────────────────────────────────────────
-- 3. SERVICIOS (cronograma)
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS servicios (
    id                          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipo_id                   UUID        REFERENCES equipos(id) ON DELETE CASCADE,
    codigo_equipo               TEXT        NOT NULL,  -- desnormalizado para joins rápidos
    nombre_equipo               TEXT,                  -- desnormalizado
    -- ── Fechas ────────────────────────────────────────────────────────────────
    fecha_servicio_vigente      DATE,
    fecha_ejecucion_programada  DATE,
    fecha_ejecucion_real        DATE,
    -- ── Tipo y frecuencia ─────────────────────────────────────────────────────
    tipo_servicio               TEXT        DEFAULT 'Calibración'
                                    CHECK (tipo_servicio IN (
                                        'Calibración', 'Verificación',
                                        'Mantenimiento', 'Calificación')),
    frecuencia                  TEXT
                                    CHECK (frecuencia IN (
                                        'Anual', 'Semestral', 'Trimestral',
                                        'Bimestral', 'Mensual')),
    frecuencia_dias             INTEGER,               -- calculado por scheduler
    -- ── Informe y estados ─────────────────────────────────────────────────────
    numero_informe              TEXT,
    estado_servicio             TEXT        DEFAULT 'Programar'
                                    CHECK (estado_servicio IN (
                                        'Programar', 'En Ejecución',
                                        'Ejecutado', 'Cancelado')),
    estado_entrega              TEXT        DEFAULT 'Pendiente'
                                    CHECK (estado_entrega IN (
                                        'Pendiente', 'Entregado')),
    estado_conformidad          TEXT        DEFAULT 'Pendiente de Calificar'
                                    CHECK (estado_conformidad IN (
                                        'Pendiente de Calificar', 'Conforme',
                                        'No Conforme', 'Fuera de Especificación')),
    proveedor                   TEXT,
    periodo_proximo_servicio    TEXT,                  -- texto original del Excel p.ej. "04/2026"
    -- ── Campos calculados por el scheduler ────────────────────────────────────
    fecha_proximo_servicio      DATE,
    estado_alerta               TEXT        DEFAULT 'SIN_DATOS'
                                    CHECK (estado_alerta IN (
                                        'AL_DIA', 'PROXIMO', 'CRITICO',
                                        'VENCIDO', 'SIN_DATOS')),
    dias_restantes              INTEGER,
    -- ── Trazabilidad ──────────────────────────────────────────────────────────
    migracion_id                UUID,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE servicios IS 'Cronograma de servicios metrológicos por equipo';
COMMENT ON COLUMN servicios.frecuencia_dias IS 'Calculado automáticamente: Anual=365, Semestral=182, Trimestral=91, Bimestral=60, Mensual=30';
COMMENT ON COLUMN servicios.estado_alerta IS 'Calculado por el Scheduling Engine: AL_DIA, PROXIMO (≤30d), CRITICO (≤15d), VENCIDO (<0d)';

CREATE INDEX IF NOT EXISTS idx_servicios_equipo ON servicios(equipo_id);
CREATE INDEX IF NOT EXISTS idx_servicios_alerta ON servicios(estado_alerta);
CREATE INDEX IF NOT EXISTS idx_servicios_proximo ON servicios(fecha_proximo_servicio);
CREATE INDEX IF NOT EXISTS idx_servicios_codigo ON servicios(codigo_equipo);

-- ──────────────────────────────────────────────────────────────────────────────
-- 4. ALERTAS
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alertas (
    id               UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipo_id        UUID        REFERENCES equipos(id) ON DELETE CASCADE,
    servicio_id      UUID        REFERENCES servicios(id) ON DELETE CASCADE,
    tipo_alerta      TEXT        NOT NULL,
    nivel_prioridad  TEXT        NOT NULL
                         CHECK (nivel_prioridad IN ('alta', 'media', 'baja')),
    mensaje          TEXT        NOT NULL,
    leida            BOOLEAN     DEFAULT FALSE,
    generada_en      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    leida_en         TIMESTAMPTZ
);

COMMENT ON TABLE alertas IS 'Alertas generadas por el motor de cronograma';

CREATE INDEX IF NOT EXISTS idx_alertas_equipo ON alertas(equipo_id);
CREATE INDEX IF NOT EXISTS idx_alertas_leida ON alertas(leida);
CREATE INDEX IF NOT EXISTS idx_alertas_prioridad ON alertas(nivel_prioridad);

-- ──────────────────────────────────────────────────────────────────────────────
-- 5. MIGRACIONES (log de cargas ETL)
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS migraciones (
    id                   UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre_archivo       TEXT        NOT NULL,
    tipo                 TEXT        NOT NULL
                             CHECK (tipo IN ('inventario', 'servicios')),
    registros_leidos     INTEGER     DEFAULT 0,
    registros_cargados   INTEGER     DEFAULT 0,
    duplicados_omitidos  INTEGER     DEFAULT 0,
    errores              INTEGER     DEFAULT 0,
    estado               TEXT        NOT NULL
                             CHECK (estado IN ('completado', 'parcial', 'fallido')),
    usuario              TEXT,
    notas                TEXT,
    ejecutado_en         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE migraciones IS 'Log de cada ejecución del proceso ETL para trazabilidad académica';

-- ──────────────────────────────────────────────────────────────────────────────
-- 6. TRIGGER: actualizar updated_at automáticamente
-- ──────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION actualizar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_equipos_updated_at
    BEFORE UPDATE ON equipos
    FOR EACH ROW EXECUTE FUNCTION actualizar_updated_at();

CREATE OR REPLACE TRIGGER trg_servicios_updated_at
    BEFORE UPDATE ON servicios
    FOR EACH ROW EXECUTE FUNCTION actualizar_updated_at();

CREATE OR REPLACE TRIGGER trg_proveedores_updated_at
    BEFORE UPDATE ON proveedores
    FOR EACH ROW EXECUTE FUNCTION actualizar_updated_at();

-- ──────────────────────────────────────────────────────────────────────────────
-- 7. VISTAS útiles para el Dashboard
-- ──────────────────────────────────────────────────────────────────────────────

-- Vista consolidada: equipo + último servicio + alerta
CREATE OR REPLACE VIEW v_estado_pame AS
SELECT
    e.id                    AS equipo_id,
    e.codigo_equipo,
    e.nombre,
    e.area,
    e.ubicacion,
    e.estado_equipo,
    e.criticidad,
    s.tipo_servicio,
    s.frecuencia,
    s.fecha_servicio_vigente,
    s.fecha_proximo_servicio,
    s.dias_restantes,
    s.estado_alerta,
    s.estado_servicio,
    s.estado_conformidad,
    s.proveedor,
    s.numero_informe
FROM equipos e
LEFT JOIN LATERAL (
    SELECT * FROM servicios
    WHERE equipo_id = e.id
    ORDER BY fecha_servicio_vigente DESC NULLS LAST
    LIMIT 1
) s ON TRUE;

COMMENT ON VIEW v_estado_pame IS 'Vista consolidada del estado actual de cada equipo en el PAME';

-- Vista de KPIs globales
CREATE OR REPLACE VIEW v_kpis_pame AS
SELECT
    COUNT(*)                                            AS total_equipos,
    COUNT(*) FILTER (WHERE estado_alerta = 'AL_DIA')   AS al_dia,
    COUNT(*) FILTER (WHERE estado_alerta = 'PROXIMO')  AS proximos,
    COUNT(*) FILTER (WHERE estado_alerta = 'CRITICO')  AS criticos,
    COUNT(*) FILTER (WHERE estado_alerta = 'VENCIDO')  AS vencidos,
    COUNT(*) FILTER (WHERE estado_alerta = 'SIN_DATOS')AS sin_datos,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE estado_alerta = 'AL_DIA') / NULLIF(COUNT(*), 0),
        2
    )                                                   AS pct_al_dia
FROM v_estado_pame;

COMMENT ON VIEW v_kpis_pame IS 'Indicadores clave (KPIs) globales del PAME';
