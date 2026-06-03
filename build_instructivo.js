const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, LevelFormat, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageBreak, PageNumber, Footer, Header,
  TabStopType, TabStopPosition
} = require('docx');
const fs = require('fs');

// ── PALETA ───────────────────────────────────────────────────────
const TEAL_DARK  = "0B3533";
const TEAL       = "00A99D";
const TEAL_LIGHT = "E6F5F4";
const GRAY_LIGHT = "F5F7FA";
const GRAY_MID   = "E2E8F0";
const WHITE      = "FFFFFF";
const TEXT_DARK  = "1A2535";
const AMBER      = "FEF3C7";
const RED_LIGHT  = "FEE2E2";
const GREEN_LIGHT= "D1FAE5";

// ── HELPERS ──────────────────────────────────────────────────────
const border1 = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border1, bottom: border1, left: border1, right: border1 };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

function cell(text, opts = {}) {
  const {
    bold = false, shade = WHITE, colSpan = 1, width = 2000,
    color = TEXT_DARK, size = 20, italic = false, center = false
  } = opts;
  return new TableCell({
    columnSpan: colSpan,
    width: { size: width, type: WidthType.DXA },
    borders,
    shading: { fill: shade, type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      alignment: center ? AlignmentType.CENTER : AlignmentType.LEFT,
      children: [new TextRun({ text, bold, color, size, italics: italic, font: "Arial" })]
    })]
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 200 },
    children: [new TextRun({ text, bold: true, size: 36, color: TEAL_DARK, font: "Arial" })]
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 300, after: 160 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: TEAL, space: 4 } },
    children: [new TextRun({ text, bold: true, size: 28, color: TEAL_DARK, font: "Arial" })]
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text, bold: true, size: 24, color: TEAL, font: "Arial" })]
  });
}

function h4(text) {
  return new Paragraph({
    spacing: { before: 180, after: 80 },
    children: [new TextRun({ text, bold: true, size: 22, color: TEXT_DARK, font: "Arial" })]
  });
}

function p(text, opts = {}) {
  const { bold = false, italic = false, color = TEXT_DARK, size = 20 } = opts;
  return new Paragraph({
    spacing: { before: 60, after: 100 },
    children: [new TextRun({ text, bold, italics: italic, color, size, font: "Arial" })]
  });
}

function pMono(text) {
  return new Paragraph({
    spacing: { before: 40, after: 40 },
    shading: { fill: "F1F5F9", type: ShadingType.CLEAR },
    indent: { left: 360 },
    children: [new TextRun({ text, size: 16, font: "Courier New", color: "1E3A5F" })]
  });
}

function bullet(text, opts = {}) {
  const { bold = false, color = TEXT_DARK } = opts;
  // Split text into parts: before ← and after, bolding the ← part
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 40, after: 80 },
    children: [new TextRun({ text, bold, color, size: 20, font: "Arial" })]
  });
}

function numbered(text, opts = {}) {
  const { bold = false } = opts;
  return new Paragraph({
    numbering: { reference: "numbers", level: 0 },
    spacing: { before: 40, after: 80 },
    children: [new TextRun({ text, bold, size: 20, font: "Arial", color: TEXT_DARK })]
  });
}

function note(text) {
  return new Paragraph({
    spacing: { before: 120, after: 120 },
    indent: { left: 360 },
    border: { left: { style: BorderStyle.SINGLE, size: 12, color: TEAL, space: 8 } },
    shading: { fill: TEAL_LIGHT, type: ShadingType.CLEAR },
    children: [new TextRun({ text, size: 18, italic: true, color: TEAL_DARK, font: "Arial" })]
  });
}

function warning(text) {
  return new Paragraph({
    spacing: { before: 120, after: 120 },
    indent: { left: 360 },
    border: { left: { style: BorderStyle.SINGLE, size: 12, color: "F59E0B", space: 8 } },
    shading: { fill: AMBER, type: ShadingType.CLEAR },
    children: [new TextRun({ text, size: 18, italic: true, color: "92400E", font: "Arial" })]
  });
}

function divider() {
  return new Paragraph({
    spacing: { before: 200, after: 200 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: GRAY_MID, space: 1 } },
    children: []
  });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

function headerRow(cols, widths) {
  return new TableRow({
    tableHeader: true,
    children: cols.map((c, i) => cell(c, { bold: true, shade: TEAL_DARK, color: WHITE, width: widths[i] }))
  });
}

function dataRow(cols, widths, shade = WHITE) {
  return new TableRow({
    children: cols.map((c, i) => cell(c, { shade, width: widths[i] }))
  });
}

function bloqueBanner(num, title, objetivo) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [
      new TableRow({ children: [
        new TableCell({
          columnSpan: 1,
          width: { size: 9360, type: WidthType.DXA },
          borders: noBorders,
          shading: { fill: TEAL_DARK, type: ShadingType.CLEAR },
          margins: { top: 200, bottom: 200, left: 300, right: 300 },
          children: [
            new Paragraph({ children: [new TextRun({ text: `BLOQUE ${num}`, size: 20, color: TEAL, bold: true, font: "Arial" })] }),
            new Paragraph({ children: [new TextRun({ text: title, size: 32, color: WHITE, bold: true, font: "Arial" })] }),
            new Paragraph({ spacing: { before: 80 }, children: [new TextRun({ text: objetivo, size: 18, color: "B0D4D2", font: "Arial", italics: true })] }),
          ]
        })
      ]})
    ]
  });
}

// ── PORTADA ──────────────────────────────────────────────────────
function portada() {
  return [
    new Paragraph({ spacing: { before: 1800 }, children: [] }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "INSTRUCTIVO TÉCNICO", size: 52, bold: true, color: TEAL_DARK, font: "Arial" })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 200 },
      children: [new TextRun({ text: "MÓDULO COMPLEMENTARIO PAME", size: 40, bold: true, color: TEAL, font: "Arial" })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 160 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: TEAL, space: 8 } },
      children: [new TextRun({ text: "Laboratorios Laproff S.A.S.", size: 28, color: TEXT_DARK, font: "Arial" })]
    }),
    new Paragraph({ spacing: { before: 400 }, children: [] }),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [3000, 6360],
      rows: [
        new TableRow({ children: [
          cell("Estudiante", { bold: true, shade: TEAL_DARK, color: WHITE, width: 3000 }),
          cell("Juliana González Afanador", { shade: TEAL_LIGHT, width: 6360 })
        ]}),
        new TableRow({ children: [
          cell("Programa", { bold: true, shade: TEAL_DARK, color: WHITE, width: 3000 }),
          cell("Bioingeniería — Semestre 10 — Universidad de Antioquia", { shade: WHITE, width: 6360 })
        ]}),
        new TableRow({ children: [
          cell("Empresa", { bold: true, shade: TEAL_DARK, color: WHITE, width: 3000 }),
          cell("Laboratorios Laproff S.A.S. — Sabaneta, Colombia", { shade: TEAL_LIGHT, width: 6360 })
        ]}),
        new TableRow({ children: [
          cell("Período", { bold: true, shade: TEAL_DARK, color: WHITE, width: 3000 }),
          cell("16/03/2026 — 15/09/2026  (26 semanas)", { shade: WHITE, width: 6360 })
        ]}),
        new TableRow({ children: [
          cell("Stack", { bold: true, shade: TEAL_DARK, color: WHITE, width: 3000 }),
          cell("Python · Pandas · Firebase Firestore · Streamlit", { shade: TEAL_LIGHT, width: 6360 })
        ]}),
        new TableRow({ children: [
          cell("Destino", { bold: true, shade: TEAL_DARK, color: WHITE, width: 3000 }),
          cell("Guía de desarrollo por bloques para Antigravity", { shade: WHITE, width: 6360 })
        ]}),
      ]
    }),
    new Paragraph({ spacing: { before: 600 }, children: [] }),
    note("Este instructivo está dividido en 6 bloques de trabajo independientes para entregarlos a Antigravity de forma secuencial. Espera a que Antigravity complete cada bloque antes de enviarle el siguiente. Cada bloque incluye todo el contexto necesario, ya que Antigravity no recuerda sesiones anteriores."),
    pageBreak()
  ];
}

// ── CONTEXTO GLOBAL ──────────────────────────────────────────────
function contextoGlobal() {
  return [
    h1("CONTEXTO GLOBAL — Incluir en toda entrega"),
    p("Este texto debe ir al inicio de cada bloque que le entregues a Antigravity para que tenga el contexto completo del proyecto."),

    h3("Proyecto"),
    p("Módulo complementario al aplicativo PAME (Programa de Aseguramiento Metrológico) de Laboratorios Laproff S.A.S. El módulo NO reemplaza el aplicativo existente — lo complementa con capacidades que aún no tiene."),

    h3("Stack tecnológico"),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [2800, 6560],
      rows: [
        headerRow(["Componente", "Tecnología / Decisión"], [2800, 6560]),
        dataRow(["Backend / lógica", "Python 3.x + Pandas + Openpyxl"], [2800, 6560], GRAY_LIGHT),
        dataRow(["Base de datos", "Firebase Firestore (NoSQL documental) ← principal"], [2800, 6560]),
        dataRow(["Dashboard", "Streamlit"], [2800, 6560], GRAY_LIGHT),
        dataRow(["Archivos de entrada", "CSV, Excel (.xlsx), JSON (estructura variable)"], [2800, 6560]),
        dataRow(["Alertas", "SMTP (correo electrónico) + scheduler automático"], [2800, 6560], GRAY_LIGHT),
      ]
    }),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h3("Por qué Firestore (NoSQL)"),
    p("Los archivos JSON que llegan al sistema pueden tener estructuras distintas entre sí: distintos nombres de campos, anidamiento variable, campos extra o faltantes. Firestore almacena documentos flexibles sin esquema rígido, lo que hace el sistema robusto frente a esa variabilidad. Los campos desconocidos se preservan, no se descartan."),

    h3("Lo que ya existe en Laproff — NO tocar"),
    bullet("Aplicativo interno con módulos de registro de equipos y seguimiento del cronograma de servicios."),
    bullet("Frontend HTML/CSS/JS de referencia visual (pame.html): sidebar teal oscuro (#0B3533), cards blancas, badges de color para estados."),

    h3("Lo que este módulo construye"),
    numbered("ETL multi-formato: extracción desde CSV, Excel y JSON → transformación y limpieza → carga a Firestore."),
    numbered("Motor de alertas priorizadas (CRÍTICA / ALTA / MEDIA) con envío automático por correo electrónico SMTP."),
    numbered("Dashboard Streamlit con vista histórica anual de cumplimiento del cronograma (diferenciador principal)."),
    divider(), pageBreak()
  ];
}

// ── BLOQUE 0 ─────────────────────────────────────────────────────
function bloque0() {
  return [
    bloqueBanner("0", "LECTURA Y PREPARACIÓN", "Que Antigravity comprenda el dominio metrológico, la arquitectura NoSQL y el diseño visual antes de escribir código."),
    new Paragraph({ spacing: { before: 200 }, children: [] }),

    h2("Tarea 0.1 — Dominio metrológico"),
    p("El proyecto gestiona el ciclo de vida de equipos de medición en una farmacéutica regulada por el INVIMA (Colombia). Cada equipo pasa por calibraciones, calificaciones, mantenimientos y verificaciones periódicas."),

    h4("Estados del servicio"),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [2200, 4200, 2960],
      rows: [
        headerRow(["Estado", "Significado", "Color del badge"], [2200, 4200, 2960]),
        dataRow(["Vigente", "Servicio ejecutado, dentro del plazo", "#10B981 — Verde"], [2200, 4200, 2960], GREEN_LIGHT),
        dataRow(["En ejecución", "Servicio actualmente en curso", "#00A99D — Teal"], [2200, 4200, 2960], TEAL_LIGHT),
        dataRow(["Programar", "Próximo a vencer, debe agendarse", "#F59E0B — Amarillo"], [2200, 4200, 2960], AMBER),
        dataRow(["Vencido", "Fecha de vencimiento superada", "#DC2626 — Rojo oscuro"], [2200, 4200, 2960], RED_LIGHT),
        dataRow(["Sin datos", "Sin historial de servicio", "#94A3B8 — Gris"], [2200, 4200, 2960], GRAY_LIGHT),
      ]
    }),
    new Paragraph({ spacing: { before: 200 }, children: [] }),

    h2("Tarea 0.2 — Estructura de datos real del CSV de Laproff"),
    warning("Este es el esquema real del Cronograma_De_Servicios.csv (3.606 registros, sep: ;, encoding: latin-1). Todo el sistema debe respetar exactamente estos campos y valores."),
    new Paragraph({ spacing: { before: 120 }, children: [] }),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [3200, 2600, 3560],
      rows: [
        headerRow(["Campo original (CSV)", "Campo interno en BD", "Notas"], [3200, 2600, 3560]),
        dataRow(["Equipo", "nombre_equipo", "Nombre del instrumento"], [3200, 2600, 3560], GRAY_LIGHT),
        dataRow(["Código del Equipo", "codigo_equipo", "ID único (ej: LS1191, CC397-25)"], [3200, 2600, 3560]),
        dataRow(["Fecha de Servicio Vigente", "fecha_servicio_vigente", "Formato DD/MM/YYYY"], [3200, 2600, 3560], GRAY_LIGHT),
        dataRow(["Fecha de Ejecución del Servicio Programado", "fecha_ejecucion_programada", "SIEMPRE vacía en datos reales"], [3200, 2600, 3560]),
        dataRow(["Tipo de Servicio", "tipo_servicio", "Ver valores válidos"], [3200, 2600, 3560], GRAY_LIGHT),
        dataRow(["Frecuencia", "frecuencia", "Ver valores válidos"], [3200, 2600, 3560]),
        dataRow(["Estado del Servicio", "estado_servicio", "Ver valores válidos"], [3200, 2600, 3560], GRAY_LIGHT),
        dataRow(["Estado de Entrega", "estado_entrega", "Entregado / Pendiente"], [3200, 2600, 3560]),
        dataRow(["Estado de Conformidad", "estado_conformidad", "Ver valores válidos"], [3200, 2600, 3560], GRAY_LIGHT),
        dataRow(["Proveedor", "proveedor", "Empresa que ejecuta el servicio"], [3200, 2600, 3560]),
        dataRow(["Período Próximo Servicio", "periodo_proximo_servicio", "Formato MM/YYYY (ej: 01/2027)"], [3200, 2600, 3560], GRAY_LIGHT),
        dataRow(["Activo Fijo", "activo_fijo", "Puede ser NO IDENTIFICADO/REGISTRA/APLICA → null"], [3200, 2600, 3560]),
        dataRow(["Serie Equipo", "serie_equipo", "Puede ser NO IDENTIFICADO → null"], [3200, 2600, 3560], GRAY_LIGHT),
        dataRow(["Ubicación", "ubicacion", "Área física dentro de la planta"], [3200, 2600, 3560]),
      ]
    }),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h4("Valores válidos por campo categórico"),
    p("Tipo de Servicio:", { bold: true }),
    p("Calibración, Calificación, Calificación PQ, Calificación OQ, Mantenimiento Preventivo, Mantenimiento Correctivo, Verificación Temperatura y Humedad, Mapeo, Diagnóstico"),
    p("Frecuencia:", { bold: true }),
    p("Anual, Semestral, Trimestral, Bienal, Trienal, NoAplica"),
    p("Estado del Servicio:", { bold: true }),
    p("Vigente, Programar, En ejecución, Vencido"),
    p("Estado de Conformidad:", { bold: true }),
    p("Cumple, No Cumple, Pendiente de Calificar"),
    new Paragraph({ spacing: { before: 120 }, children: [] }),

    h4("Particularidades importantes del CSV real"),
    bullet("Un mismo equipo puede tener MÚLTIPLES filas, una por tipo de servicio o período. Es normal."),
    bullet("La columna 'Fecha de Ejecución del Servicio Programado' está completamente vacía. Nunca lanzar error por esto."),
    bullet("'Período Próximo Servicio' viene como MM/YYYY, no como fecha estándar. Convertir al primer día del mes."),
    bullet("Activo Fijo y Serie Equipo pueden contener NO IDENTIFICADO, NO REGISTRA o NO APLICA. Normalizar a null en Firestore."),
    bullet("El CSV real tiene 3.606 registros con 3.386 códigos de equipo únicos."),
    new Paragraph({ spacing: { before: 120 }, children: [] }),

    h2("Tarea 0.3 — Arquitectura NoSQL con Firebase Firestore"),
    p("Se usa Firestore porque los JSON pueden llegar con estructuras distintas (campos renombrados, anidamiento variable, campos extra). Firestore almacena documentos flexibles sin esquema rígido."),

    h4("Estructura de colecciones en Firestore"),
    pMono("Firestore"),
    pMono("├── equipos/                        ← Colección principal"),
    pMono("│   ├── LS1191/                     ← ID = codigo_equipo"),
    pMono("│   │   ├── nombre_equipo: 'LS1191'"),
    pMono("│   │   ├── ubicacion: 'CONTROL CALIDAD'"),
    pMono("│   │   ├── serie_equipo: null"),
    pMono("│   │   ├── activo_fijo: null"),
    pMono("│   │   ├── activo: true"),
    pMono("│   │   └── servicios/              ← Subcolección"),
    pMono("│   │       └── {auto_id}/"),
    pMono("│   │           ├── tipo_servicio: 'Calibración'"),
    pMono("│   │           ├── frecuencia: 'Anual'"),
    pMono("│   │           ├── fecha_servicio_vigente: '2026-01-13'"),
    pMono("│   │           ├── fecha_proximo_servicio: '2027-01-01'"),
    pMono("│   │           ├── estado_servicio: 'Vigente'"),
    pMono("│   │           ├── estado_conformidad: 'Cumple'"),
    pMono("│   │           ├── proveedor: 'LAPROFF'"),
    pMono("│   │           ├── anio: 2026"),
    pMono("│   │           └── campos_extra: {...}  ← campos desconocidos del JSON"),
    pMono("├── alertas_log/                    ← Historial de alertas enviadas"),
    pMono("└── etl_log/                        ← Historial de cargas ETL"),
    new Paragraph({ spacing: { before: 120 }, children: [] }),
    note("Los campos desconocidos del JSON NO se descartan. Se guardan en campos_extra: {} del documento de servicio. Esto preserva información futura y respeta la filosofía NoSQL."),

    h2("Tarea 0.4 — Diseño visual de referencia"),
    p("El dashboard Streamlit debe respetar la paleta del archivo pame.html:"),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [3000, 3000, 3360],
      rows: [
        headerRow(["Variable", "Hex", "Uso"], [3000, 3000, 3360]),
        dataRow(["primary / teal", "#00A99D", "Color primario, botones principales"], [3000, 3000, 3360], TEAL_LIGHT),
        dataRow(["sidebar", "#0B3533", "Fondo del sidebar"], [3000, 3000, 3360]),
        dataRow(["Vigente / Cumple", "#10B981", "Estado positivo"], [3000, 3000, 3360], GREEN_LIGHT),
        dataRow(["Programar", "#F59E0B", "Advertencia"], [3000, 3000, 3360], AMBER),
        dataRow(["En ejecución urgente", "#EF4444", "Alerta"], [3000, 3000, 3360], RED_LIGHT),
        dataRow(["Vencido", "#DC2626", "Crítico"], [3000, 3000, 3360], RED_LIGHT),
        dataRow(["Sin datos", "#94A3B8", "Neutro"], [3000, 3000, 3360], GRAY_LIGHT),
      ]
    }),
    new Paragraph({ spacing: { before: 160 }, children: [] }),
    h4("Entregable esperado del Bloque 0"),
    bullet("Confirmación de comprensión del dominio y arquitectura NoSQL."),
    bullet("Lista de preguntas técnicas antes de empezar."),
    bullet("Propuesta de estructura de carpetas del proyecto."),
    divider(), pageBreak()
  ];
}

// ── BLOQUE 1 ─────────────────────────────────────────────────────
function bloque1() {
  return [
    bloqueBanner("1", "MODELO DE DATOS Y CONEXIÓN A FIRESTORE", "Configurar Firebase Firestore y construir el módulo Python de conexión y operaciones CRUD."),
    new Paragraph({ spacing: { before: 200 }, children: [] }),

    h2("Tarea 1.1 — Configuración de Firebase"),
    numbered("Crear proyecto en Firebase Console (console.firebase.google.com)."),
    numbered("Activar Cloud Firestore en modo nativo."),
    numbered("Ir a Configuración del proyecto → Cuentas de servicio → Generar nueva clave privada."),
    numbered("Guardar el JSON descargado como firebase_credentials.json en la raíz del proyecto."),
    numbered("Agregar firebase_credentials.json al .gitignore INMEDIATAMENTE — nunca subir al repositorio."),
    new Paragraph({ spacing: { before: 120 }, children: [] }),
    h4("Variables de entorno (.env)"),
    pMono("FIREBASE_CREDENTIALS_PATH=firebase_credentials.json"),
    pMono("# Alternativa para despliegues en la nube (sin archivo físico):"),
    pMono('FIREBASE_CREDENTIALS_JSON={"type": "service_account", ...}'),
    pMono(""),
    pMono("# Correo SMTP para alertas"),
    pMono("SMTP_HOST=smtp.gmail.com"),
    pMono("SMTP_PORT=587"),
    pMono("SMTP_USER=correo@laproff.com"),
    pMono("SMTP_PASSWORD=app_password_aqui"),
    pMono("EMAIL_REMITENTE=pame-alertas@laproff.com"),
    pMono("EMAIL_DESTINATARIOS=jefe.validacionesymetrologia@laproff.com,supervisor@laproff.com"),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h2("Tarea 1.2 — Módulo de conexión: firebase_client.py"),
    p("Crear src/database/firebase_client.py. Singleton de conexión: soporta FIREBASE_CREDENTIALS_PATH (ruta a archivo JSON) y FIREBASE_CREDENTIALS_JSON (string para servidores/CI). Nunca hardcodear credenciales."),

    h2("Tarea 1.3 — Repositorio: equipos_repo.py"),
    p("Crear src/database/equipos_repo.py con todas las operaciones sobre Firestore. En Firestore NO hay SQL ni JOINs — toda la lógica de agregación y filtrado se hace en Python después de traer los documentos."),

    h4("Funciones requeridas — Equipos"),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [3800, 5560],
      rows: [
        headerRow(["Función", "Descripción"], [3800, 5560]),
        dataRow(["upsert_equipo(codigo, datos)", "Inserta o actualiza con merge=True. Usa codigo_equipo como ID de documento."], [3800, 5560], GRAY_LIGHT),
        dataRow(["get_equipo(codigo)", "Retorna el documento del equipo o None."], [3800, 5560]),
        dataRow(["get_all_equipos(solo_activos=True)", "Lista todos los equipos. Filtra activo==True si se indica."], [3800, 5560], GRAY_LIGHT),
        dataRow(["limpiar_equipos()", "Elimina TODOS los documentos y subcolecciones. Pedir confirmación antes de llamar."], [3800, 5560]),
      ]
    }),
    new Paragraph({ spacing: { before: 120 }, children: [] }),

    h4("Funciones requeridas — Servicios (subcolección)"),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [3800, 5560],
      rows: [
        headerRow(["Función", "Descripción"], [3800, 5560]),
        dataRow(["agregar_servicio(codigo_equipo, servicio)", "Agrega documento a la subcolección servicios del equipo."], [3800, 5560], GRAY_LIGHT),
        dataRow(["get_servicios_equipo(codigo_equipo)", "Todos los servicios de un equipo, ordenados por fecha descendente."], [3800, 5560]),
        dataRow(["get_ultimo_servicio(codigo, tipo=None)", "Servicio más reciente. Filtra por tipo si se especifica."], [3800, 5560], GRAY_LIGHT),
        dataRow(["get_estado_actual_todos()", "Estado actual de todos los equipos activos (equipo + último servicio combinados)."], [3800, 5560]),
        dataRow(["get_servicios_por_anio(anio, ubicacion=None)", "Todos los servicios del año. Usa Collection Group query sobre la subcolección servicios."], [3800, 5560], GRAY_LIGHT),
      ]
    }),
    new Paragraph({ spacing: { before: 120 }, children: [] }),

    h4("Funciones requeridas — Logs"),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [3800, 5560],
      rows: [
        headerRow(["Función", "Descripción"], [3800, 5560]),
        dataRow(["registrar_carga_etl(log)", "Guarda registro de carga ETL en colección etl_log."], [3800, 5560], GRAY_LIGHT),
        dataRow(["get_historial_etl(limite=20)", "Últimos N registros de carga ETL."], [3800, 5560]),
        dataRow(["registrar_alerta(log)", "Guarda registro de alerta enviada en alertas_log."], [3800, 5560], GRAY_LIGHT),
        dataRow(["get_historial_alertas(limite=30)", "Últimos N registros de alertas enviadas."], [3800, 5560]),
      ]
    }),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h2("Estructura de carpetas del proyecto"),
    pMono("pame_module/"),
    pMono("├── .env                        ← NUNCA subir a git"),
    pMono("├── .env.example"),
    pMono("├── .gitignore                  ← incluir .env y firebase_credentials.json"),
    pMono("├── firebase_credentials.json   ← NUNCA subir a git"),
    pMono("├── requirements.txt"),
    pMono("├── run.py"),
    pMono("├── src/"),
    pMono("│   ├── database/"),
    pMono("│   │   ├── firebase_client.py"),
    pMono("│   │   └── equipos_repo.py"),
    pMono("│   ├── etl/"),
    pMono("│   │   ├── extractor.py"),
    pMono("│   │   ├── transformer.py"),
    pMono("│   │   ├── loader.py"),
    pMono("│   │   └── pipeline.py"),
    pMono("│   ├── alertas/"),
    pMono("│   │   ├── motor_alertas.py"),
    pMono("│   │   └── email_sender.py"),
    pMono("│   └── dashboard/"),
    pMono("│       ├── app.py"),
    pMono("│       ├── charts.py"),
    pMono("│       └── helpers.py"),
    pMono("├── tests/"),
    pMono("│   ├── test_etl.py"),
    pMono("│   ├── test_alertas.py"),
    pMono("│   └── test_metricas_etl.py"),
    pMono("└── data/"),
    pMono("    └── samples/"),
    pMono("        ├── cronograma_sample.csv"),
    pMono("        ├── cronograma_historico.json"),
    pMono("        └── equipos_nuevos.csv"),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h4("requirements.txt"),
    pMono("firebase-admin>=6.0.0"),
    pMono("google-cloud-firestore>=2.0.0"),
    pMono("pandas>=2.0.0"),
    pMono("openpyxl>=3.1.0"),
    pMono("streamlit>=1.35.0"),
    pMono("python-dotenv>=1.0.0"),
    pMono("schedule>=1.2.0"),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h4("Entregable esperado del Bloque 1"),
    bullet("firebase_client.py y equipos_repo.py completos con manejo de errores en español."),
    bullet("requirements.txt con todas las dependencias."),
    bullet(".env.example con todas las variables necesarias."),
    bullet(".gitignore correctamente configurado."),
    divider(), pageBreak()
  ];
}

// ── BLOQUE 2 ─────────────────────────────────────────────────────
function bloque2() {
  return [
    bloqueBanner("2", "MÓDULO ETL — EXTRACCIÓN, TRANSFORMACIÓN Y CARGA", "Pipeline que acepta CSV, Excel y JSON de estructura variable, los normaliza y los carga a Firestore."),
    new Paragraph({ spacing: { before: 200 }, children: [] }),

    h2("Tarea 2.1 — Extractor multi-formato (extractor.py)"),
    p("El extractor detecta el formato por extensión y normaliza a lista de diccionarios Python. El reto principal está en el JSON, que puede llegar con distintas estructuras."),
    h4("CSV"),
    bullet("Detección automática de encoding: probar latin-1, utf-8, cp1252."),
    bullet("Detección automática de separador: probar ; , \\t."),
    bullet("El CSV de Laproff usa latin-1 y separador ;."),
    h4("Excel"),
    bullet("Leer primera hoja con openpyxl."),
    bullet("Convertir valores NaN a None."),
    h4("JSON — Detección automática de estructura (4 formatos)"),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [1800, 3400, 4160],
      rows: [
        headerRow(["Formato", "Estructura", "Ejemplo"], [1800, 3400, 4160]),
        dataRow(["A — Array plano", "Array de objetos directamente", '[{"Código del Equipo": "LS001", ...}]'], [1800, 3400, 4160], GRAY_LIGHT),
        dataRow(["B — Objeto con clave", "Objeto con una clave que contiene el array", '{"equipos": [...]} o {"data": [...]}'], [1800, 3400, 4160]),
        dataRow(["C — Objeto de objetos", "Clave = codigo_equipo, valor = datos", '{"LS001": {"nombre": ..., "servicios": [...]}}'], [1800, 3400, 4160], GRAY_LIGHT),
        dataRow(["D — Objeto único", "Un solo registro", '{"Código del Equipo": "LS001", ...}'], [1800, 3400, 4160]),
      ]
    }),
    new Paragraph({ spacing: { before: 120 }, children: [] }),
    note("Los campos no reconocidos del JSON NO se descartan. Se preservan en campos_extra: {} para no perder información."),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h2("Tarea 2.2 — Transformador y validador (transformer.py)"),
    p("Normaliza registros de cualquier formato al esquema interno de Firestore."),

    h4("Diccionario de mapeo de columnas (COLUMN_MAPPING) — obligatorio"),
    p("Mapea los nombres exactos del CSV de Laproff (con tildes, espacios) a los nombres internos, además de variantes alternativas que pueden venir en JSON:"),
    pMono("'Equipo'                                     → nombre_equipo"),
    pMono("'Código del Equipo'                          → codigo_equipo"),
    pMono("'Fecha de Servicio Vigente'                  → fecha_servicio_vigente"),
    pMono("'Fecha de Ejecución del Servicio Programado' → fecha_ejecucion_programada"),
    pMono("'Tipo de Servicio'                           → tipo_servicio"),
    pMono("'Frecuencia'                                 → frecuencia"),
    pMono("'Estado del Servicio'                        → estado_servicio"),
    pMono("'Estado de Entrega'                          → estado_entrega"),
    pMono("'Estado de Conformidad'                      → estado_conformidad"),
    pMono("'Proveedor'                                  → proveedor"),
    pMono("'Período Próximo Servicio'                   → periodo_proximo_servicio"),
    pMono("'Activo Fijo'                                → activo_fijo"),
    pMono("'Serie Equipo'                               → serie_equipo"),
    pMono("'Ubicación'                                  → ubicacion"),
    pMono("# Variantes JSON alternativas:"),
    pMono("'codigo', 'code', 'equipo_codigo'            → codigo_equipo"),
    pMono("'nombre', 'name'                             → nombre_equipo"),
    pMono("'area', 'location'                           → ubicacion"),
    new Paragraph({ spacing: { before: 120 }, children: [] }),

    h4("Pasos de transformación (en orden)"),
    numbered("Mapear columnas al nombre interno usando COLUMN_MAPPING."),
    numbered("Guardar campos desconocidos en campos_extra: {} sin descartarlos."),
    numbered("Validar campos obligatorios: codigo_equipo es obligatorio. Si falta → registro inválido con razón."),
    numbered("Deduplicar por clave (codigo_equipo + tipo_servicio + fecha_servicio_vigente)."),
    numbered("Normalizar nulos textuales: NO IDENTIFICADO, NO REGISTRA, NO APLICA, nan → None."),
    numbered("Convertir fecha_servicio_vigente de DD/MM/YYYY a ISO 8601 (YYYY-MM-DD)."),
    numbered("Manejar fecha_ejecucion_programada vacía sin error → None."),
    numbered("Convertir periodo_proximo_servicio (MM/YYYY) al primer día del mes en ISO 8601 → fecha_proximo_servicio."),
    numbered("Normalizar ubicacion a MAYÚSCULAS para unificar variantes."),
    numbered("Calcular estado_servicio si está vacío: Vencido si dias<0, Programar si dias≤30, Vigente si dias>30."),
    numbered("Agregar campo anio (int) extraído de fecha_servicio_vigente para las consultas históricas."),
    new Paragraph({ spacing: { before: 120 }, children: [] }),

    h4("Reporte de calidad que debe devolver transform()"),
    pMono("{ 'total_registros': int,"),
    pMono("  'validos': int,"),
    pMono("  'invalidos': int,"),
    pMono("  'duplicados_eliminados': int,"),
    pMono("  'nulos_normalizados': int,"),
    pMono("  'fechas_ejecucion_vacias': int,"),
    pMono("  'campos_extra_encontrados': int,"),
    pMono("  'registros_invalidos': list }   ← con codigo y razón"),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h2("Tarea 2.3 — Cargador a Firestore (loader.py)"),
    p("Separa cada registro transformado en sus dos partes: datos del equipo (van al documento equipos/{codigo}) y datos del servicio (van a la subcolección servicios/)."),
    h4("Campos que van al documento del equipo"),
    p("codigo_equipo, nombre_equipo, serie_equipo, activo_fijo, ubicacion, activo."),
    h4("Campos que van al documento de servicio"),
    p("tipo_servicio, frecuencia, fechas, estados, proveedor, anio, campos_extra."),
    h4("Comportamiento"),
    bullet("Usa upsert_equipo (merge=True) para no sobrescribir campos existentes."),
    bullet("Agrega siempre un nuevo documento de servicio (no hace upsert en servicios)."),
    bullet("Si dry_run=True → simula sin escribir nada en Firestore."),
    bullet("Registra el resultado en la colección etl_log al finalizar."),
    h4("Reporte de carga que debe devolver load()"),
    pMono("{ 'archivo': str, 'dry_run': bool,"),
    pMono("  'insertados': int, 'actualizados': int,"),
    pMono("  'errores': list, 'duracion_segundos': float }"),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h2("Tarea 2.4 — Pipeline completo (pipeline.py)"),
    p("Orquesta los tres pasos: extraer → transformar → cargar. Interfaz:"),
    pMono("def run_pipeline(filepath: str, dry_run: bool = False) -> dict:"),
    pMono("    # Paso 1: extract(filepath)"),
    pMono("    # Paso 2: transform(registros_crudos)"),
    pMono("    # Paso 3: load(validos, nombre_archivo, reporte, dry_run)"),
    pMono("    # Retorna: {'extraccion': ..., 'transformacion': ..., 'carga': ...}"),
    new Paragraph({ spacing: { before: 120 }, children: [] }),

    h4("Archivos de muestra ya generados — copiar en data/samples/"),
    note("Los tres archivos ya están disponibles para descarga junto con este instructivo. NO es necesario que Antigravity los cree."),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [3200, 6160],
      rows: [
        headerRow(["Archivo", "Contenido"], [3200, 6160]),
        dataRow(["cronograma_sample.csv", "55 filas: 50 válidas + 3 duplicados + 2 inválidas. Todos los estados y conformidades. Encoding latin-1, sep ;."], [3200, 6160], GRAY_LIGHT),
        dataRow(["cronograma_historico.json", "123 registros de 3 años (2022–2024), 20 equipos. Distribución de conformidad distinta por año para la vista histórica."], [3200, 6160]),
        dataRow(["equipos_nuevos.csv", "10 equipos (CC900-26 a CC909-26) no existentes en el sample. Para probar carga incremental."], [3200, 6160], GRAY_LIGHT),
      ]
    }),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h4("Entregable esperado del Bloque 2"),
    bullet("extractor.py, transformer.py, loader.py, pipeline.py completos con manejo de errores en español."),
    bullet("tests/test_etl.py con pruebas para CSV, Excel y JSON."),
    divider(), pageBreak()
  ];
}

// ── BLOQUE 3 ─────────────────────────────────────────────────────
function bloque3() {
  return [
    bloqueBanner("3", "MOTOR DE ALERTAS CON ENVÍO POR CORREO", "Motor de priorización de alertas desde Firestore y envío automático por SMTP con template HTML."),
    new Paragraph({ spacing: { before: 200 }, children: [] }),

    h2("Tarea 3.1 — Motor de alertas (motor_alertas.py)"),
    p("Consulta Firestore vía get_estado_actual_todos() y genera una lista priorizada de alertas según los días restantes para cada equipo."),
    h4("Lógica de priorización"),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [2000, 4000, 3360],
      rows: [
        headerRow(["Prioridad", "Condición", "Color correo"], [2000, 4000, 3360]),
        dataRow(["CRÍTICA", "Vencido (dias < 0) o vence en ≤ 7 días", "Fondo rojo claro #FEE2E2"], [2000, 4000, 3360], RED_LIGHT),
        dataRow(["ALTA", "Vence entre 8 y 15 días", "Fondo amarillo #FEF3C7"], [2000, 4000, 3360], AMBER),
        dataRow(["MEDIA", "Vence entre 16 y 30 días", "Fondo gris #F1F5F9"], [2000, 4000, 3360], GRAY_LIGHT),
      ]
    }),
    new Paragraph({ spacing: { before: 120 }, children: [] }),
    h4("Funciones requeridas"),
    bullet("generar_alertas() → List[Alerta]: consulta Firestore, calcula prioridades, ordena CRITICA→ALTA→MEDIA."),
    bullet("agrupar_por_area(alertas) → dict: agrupa por ubicacion para envíos segmentados."),
    new Paragraph({ spacing: { before: 120 }, children: [] }),
    h4("Dataclass Alerta"),
    pMono("@dataclass"),
    pMono("class Alerta:"),
    pMono("    codigo_equipo:  str"),
    pMono("    nombre_equipo:  str"),
    pMono("    ubicacion:      str"),
    pMono("    proveedor:      Optional[str]"),
    pMono("    tipo_servicio:  Optional[str]"),
    pMono("    fecha_proxima:  Optional[str]   # ISO 8601"),
    pMono("    dias_restantes: Optional[int]   # negativo = ya venció"),
    pMono("    prioridad:      str             # CRITICA / ALTA / MEDIA"),
    pMono("    mensaje:        str"),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h2("Tarea 3.2 — Envío de correo (email_sender.py)"),
    h4("Funciones requeridas"),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [3800, 5560],
      rows: [
        headerRow(["Función", "Descripción"], [3800, 5560]),
        dataRow(["generar_html_alerta(alertas)", "Construye el HTML del correo con tablas por prioridad, usando la paleta de colores del proyecto."], [3800, 5560], GRAY_LIGHT),
        dataRow(["enviar_alerta_diaria(alertas)", "Envía resumen diario a todos los destinatarios. Registra en alertas_log de Firestore."], [3800, 5560]),
        dataRow(["enviar_alerta_critica_inmediata(alerta)", "Correo urgente individual. Asunto: [URGENTE] PAME — Equipo en estado crítico."], [3800, 5560], GRAY_LIGHT),
        dataRow(["programar_alertas_diarias(hora='08:00')", "Usa librería schedule para ejecutar envío diario automático a la hora configurada."], [3800, 5560]),
      ]
    }),
    new Paragraph({ spacing: { before: 120 }, children: [] }),
    h4("Estructura del template HTML del correo"),
    bullet("Encabezado con fondo #0B3533, título 'PAME — Alertas de Calibración' en color #00A99D."),
    bullet("Tabla de alertas CRÍTICAS con fondo rojo claro, tabla ALTAS con amarillo, tabla MEDIAS con gris."),
    bullet("Columnas de la tabla: Código | Nombre | Área | Tipo de Servicio | Fecha próxima | Días restantes | Proveedor."),
    bullet("Footer con fecha de generación y texto 'Generado automáticamente por el módulo PAME'."),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h4("Entregable esperado del Bloque 3"),
    bullet("motor_alertas.py y email_sender.py completos."),
    bullet("tests/test_alertas.py con prueba en modo dry-run (sin enviar correo real)."),
    bullet("Instrucciones en README sobre cómo configurar las variables SMTP."),
    divider(), pageBreak()
  ];
}

// ── BLOQUE 4 ─────────────────────────────────────────────────────
function bloque4() {
  return [
    bloqueBanner("4", "DASHBOARD STREAMLIT — KPIs + VISTA HISTÓRICA ANUAL", "Dashboard con dos modos: estado actual (KPIs diferenciales) y cumplimiento histórico anual (diferenciador principal)."),
    new Paragraph({ spacing: { before: 200 }, children: [] }),

    note("DIFERENCIADOR CLAVE: El aplicativo existente de Laproff muestra el estado en tiempo real conforme se actualiza. Este dashboard agrega la capacidad de ver el cumplimiento del cronograma año por año, permitiendo comparar el desempeño histórico y evaluar el avance de metas anuales."),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h2("Tarea 4.1 — Estructura general del dashboard"),
    p("El dashboard tiene 6 secciones en el sidebar (app.py con Streamlit):"),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [600, 3000, 5760],
      rows: [
        headerRow(["#", "Sección", "Propósito"], [600, 3000, 5760]),
        dataRow(["1", "Dashboard KPIs", "Estado actual con KPIs diferenciales"], [600, 3000, 5760], GRAY_LIGHT),
        dataRow(["2", "Cumplimiento Anual ★", "Vista histórica año por año — PRIORIDAD ALTA"], [600, 3000, 5760], TEAL_LIGHT),
        dataRow(["3", "Inventario de Equipos", "Tabla con filtros y búsqueda"], [600, 3000, 5760], GRAY_LIGHT),
        dataRow(["4", "Cronograma", "Próximos 90 días de servicios"], [600, 3000, 5760]),
        dataRow(["5", "Alertas Activas", "Alertas priorizadas + envío por correo"], [600, 3000, 5760], GRAY_LIGHT),
        dataRow(["6", "Migración ETL", "Carga de archivos a Firestore"], [600, 3000, 5760]),
      ]
    }),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h2("Tarea 4.2 — Sección 'Dashboard KPIs'"),
    p("KPIs diferenciales — no duplicar los que ya tiene el aplicativo de Laproff (total equipos, conteo por estado):"),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [3000, 3800, 2560],
      rows: [
        headerRow(["KPI", "Descripción", "Cálculo"], [3000, 3800, 2560]),
        dataRow(["% Equipos al día", "Proporción con estado Vigente", "count(Vigente) / total × 100"], [3000, 3800, 2560], GRAY_LIGHT),
        dataRow(["Días promedio hasta vencimiento", "Promedio de días restantes en equipos vigentes", "media(dias_restantes > 0)"], [3000, 3800, 2560]),
        dataRow(["% Cumplimiento cronograma anual", "Servicios ejecutados vs planeados en el año actual", "ejecutados / planeados × 100"], [3000, 3800, 2560], GRAY_LIGHT),
        dataRow(["Equipos sin intervención > 1 año", "Última calibración hace más de 365 días", "count(dias_desde_ultimo > 365)"], [3000, 3800, 2560]),
        dataRow(["Tasa de conformidad del período", "Servicios 'Cumple' / total con resultado", "count(Cumple) / count(Cumple+NoCumple) × 100"], [3000, 3800, 2560], GRAY_LIGHT),
        dataRow(["Top 3 áreas con mayor riesgo", "Áreas con más equipos Vencidos o en Programar", "groupby(ubicacion).count()"], [3000, 3800, 2560]),
      ]
    }),
    new Paragraph({ spacing: { before: 120 }, children: [] }),
    h4("Visualizaciones de la sección KPIs"),
    bullet("Gráfico de dona: distribución de estados (Vigente / Programar / En ejecución / Vencido / Sin datos)."),
    bullet("Barras por área: equipos en estado crítico/vencido por ubicación."),
    bullet("Línea de tendencia: evolución del % de equipos al día en los últimos 6 meses."),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h2("Tarea 4.3 — Sección 'Cumplimiento Anual' ← PRIORIDAD ALTA"),
    p("Usa get_servicios_por_anio(anio) del repositorio (Collection Group query). Esta es la funcionalidad más valorada por Laproff."),
    h4("Componentes requeridos"),
    numbered("Selector de año (2020 al año actual) + selector de área (opcional, todos por defecto)."),
    numbered("Métricas del año: total ejecutados, total planeados, % cumplimiento, conformes vs no conformes."),
    numbered("Tabla de cumplimiento por área: Área | Planeados | Ejecutados | % Cumplimiento | Conformes | No conformes."),
    numbered("Comparativo interanual: barras agrupadas por año, filtrable por área."),
    numbered("Semáforo de cumplimiento: verde ≥ 90%, amarillo 70–90%, rojo < 70%."),
    numbered("Evolución mensual del año seleccionado: línea de servicios ejecutados vs planeados por mes."),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h2("Tarea 4.4 — Sección 'Inventario de Equipos'"),
    bullet("Tabla interactiva con filtros por área, estado, proveedor y año de última calibración."),
    bullet("Búsqueda por código o nombre de equipo."),
    bullet("Columnas: Código | Nombre | Área | Estado (badge de color) | Última calibración | Próxima calibración | Días restantes | Proveedor."),
    bullet("Botón 'Exportar a Excel'."),

    h2("Tarea 4.5 — Sección 'Cronograma'"),
    bullet("Lista de servicios programados en los próximos 90 días, ordenados por fecha."),
    bullet("Filtros por área y tipo de servicio."),
    bullet("Indicador visual de urgencia (colores por días restantes)."),
    bullet("Botón 'Generar reporte de cronograma' (exportar a Excel)."),

    h2("Tarea 4.6 — Sección 'Alertas Activas'"),
    bullet("Listado de alertas priorizadas (desde generar_alertas())."),
    bullet("Botón 'Enviar alertas ahora' → dispara email_sender.enviar_alerta_diaria()."),
    bullet("Historial de las últimas 30 alertas enviadas (desde get_historial_alertas())."),

    h2("Tarea 4.7 — Sección 'Migración ETL'"),
    bullet("Uploader de archivos CSV, Excel o JSON (cualquier estructura)."),
    bullet("Botón 'Analizar' → ejecuta pipeline con dry_run=True y muestra reporte de calidad."),
    bullet("Botón 'Cargar a Firestore' → ejecuta pipeline completo."),
    bullet("Log en tiempo real del proceso de carga."),
    bullet("Historial de cargas anteriores (desde get_historial_etl())."),
    bullet("Botón 'Limpiar base de datos' con confirmación explícita antes de ejecutar limpiar_equipos()."),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h4("Entregable esperado del Bloque 4"),
    bullet("app.py con todas las secciones implementadas."),
    bullet("charts.py con funciones de gráficos reutilizables (usando plotly o altair)."),
    bullet("helpers.py con funciones de formato: badges de color, semáforos, formateo de fechas."),
    bullet("Dashboard funcional ejecutable con: streamlit run src/dashboard/app.py"),
    divider(), pageBreak()
  ];
}

// ── BLOQUE 5 ─────────────────────────────────────────────────────
function bloque5() {
  return [
    bloqueBanner("5", "INTEGRACIÓN, PRUEBAS Y DOCUMENTACIÓN", "Unir todos los componentes, validar con datos reales y generar la documentación final del sistema."),
    new Paragraph({ spacing: { before: 200 }, children: [] }),

    h2("Tarea 5.1 — Script de ejecución unificado (run.py)"),
    p("Punto de entrada único en la raíz del proyecto. Acepta argumentos por línea de comandos:"),
    pMono("python run.py --mode etl --file data/samples/cronograma_sample.csv"),
    pMono("python run.py --mode etl --file data/samples/cronograma_historico.json --dry-run"),
    pMono("python run.py --mode alertas"),
    pMono("python run.py --mode dashboard"),
    pMono("python run.py --mode scheduler      # inicia el programador automático de alertas"),
    pMono("python run.py --mode limpiar        # pide confirmación antes de borrar Firestore"),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h2("Tarea 5.2 — Archivos de muestra (ya provistos)"),
    note("Los tres archivos están generados y disponibles para descarga. Copiarlos en data/samples/. No es necesario que Antigravity los cree."),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [3000, 6360],
      rows: [
        headerRow(["Archivo", "Descripción"], [3000, 6360]),
        dataRow(["cronograma_sample.csv", "55 filas: 50 válidas + 3 duplicados + 2 inválidas. Todos los estados/conformidades. Sep=; encoding=latin-1."], [3000, 6360], GRAY_LIGHT),
        dataRow(["cronograma_historico.json", "123 registros de 3 años (2022-2024). Distribución diferente por año para que la vista histórica sea informativa."], [3000, 6360]),
        dataRow(["equipos_nuevos.csv", "10 equipos nuevos (CC900-26 a CC909-26) para probar carga incremental con upsert."], [3000, 6360], GRAY_LIGHT),
      ]
    }),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h2("Tarea 5.3 — Pruebas con datos reales de Laproff"),
    warning("Esta tarea se ejecuta DESPUÉS de validar el sistema con los archivos de muestra ficticios. Usa el modo dry_run=True primero para verificar el reporte de calidad antes de cargar datos reales."),
    h4("Secuencia recomendada"),
    numbered("Ejecutar: python run.py --mode etl --file Cronograma_De_Servicios.csv --dry-run"),
    numbered("Revisar el reporte de calidad: verificar mapeo de columnas, duplicados detectados, nulos normalizados."),
    numbered("Ajustar COLUMN_MAPPING en transformer.py si alguna columna no se mapea correctamente."),
    numbered("Cuando el reporte sea satisfactorio: python run.py --mode etl --file Cronograma_De_Servicios.csv"),
    numbered("Verificar en Firebase Console que los documentos se crearon correctamente."),
    numbered("Ejecutar el dashboard y verificar que la vista histórica anual muestra datos."),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h2("Tarea 5.4 — Tests de validación ETL (test_metricas_etl.py)"),
    p("Crear tests/test_metricas_etl.py que verifique al procesar cronograma_sample.csv:"),
    bullet("Se detectan exactamente 3 duplicados."),
    bullet("Se detectan exactamente 2 registros inválidos."),
    bullet("Los campos NO REGISTRA / NO IDENTIFICADO / NO APLICA se convierten a None."),
    bullet("Las fechas DD/MM/YYYY se convierten correctamente a formato ISO 8601."),
    bullet("El campo anio se calcula correctamente para cada registro."),
    bullet("Los campos extra del JSON se guardan en campos_extra sin perderse."),
    bullet("El pipeline en dry_run=True NO escribe nada en Firestore."),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h2("Tarea 5.5 — README técnico del módulo"),
    p("Crear README.md con las siguientes secciones:"),
    numbered("Descripción del proyecto, stack y arquitectura NoSQL."),
    numbered("Instalación: pip install -r requirements.txt."),
    numbered("Configuración de Firebase (pasos para obtener firebase_credentials.json)."),
    numbered("Configuración del archivo .env (todas las variables)."),
    numbered("Ejecutar el ETL con los tres formatos de archivo."),
    numbered("Iniciar el dashboard."),
    numbered("Configurar y probar el envío de alertas por correo SMTP."),
    numbered("Cómo limpiar la base de datos y recargar con datos reales."),
    numbered("Estructura completa de carpetas del proyecto."),
    numbered("Glosario de términos metrológicos usados en el código."),
    new Paragraph({ spacing: { before: 160 }, children: [] }),

    h4("Entregable esperado del Bloque 5"),
    bullet("run.py funcional con todos los modos."),
    bullet("tests/test_metricas_etl.py ejecutable con pytest."),
    bullet("README.md completo en español."),
    bullet("Sistema completo funcionando de extremo a extremo."),
    divider(), pageBreak()
  ];
}

// ── RESUMEN FINAL ─────────────────────────────────────────────────
function resumen() {
  return [
    h1("RESUMEN DE ENTREGAS POR BLOQUE"),
    p("Orden de entrega a Antigravity. Completar cada bloque antes de enviar el siguiente."),
    new Paragraph({ spacing: { before: 120 }, children: [] }),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [1200, 2800, 2360, 3000],
      rows: [
        headerRow(["Bloque", "Nombre", "Entrega a Antigravity", "Entregable esperado"], [1200, 2800, 2360, 3000]),
        dataRow(["0", "Lectura y preparación", "Contexto + NoSQL + dominio + diseño", "Confirmación + preguntas + estructura carpetas"], [1200, 2800, 2360, 3000], GRAY_LIGHT),
        dataRow(["1", "Modelo de datos Firestore", "Esquema + módulo conexión", "firebase_client.py + equipos_repo.py + requirements.txt"], [1200, 2800, 2360, 3000]),
        dataRow(["2", "Módulo ETL", "ETL multi-formato completo", "extractor.py + transformer.py + loader.py + pipeline.py"], [1200, 2800, 2360, 3000], GRAY_LIGHT),
        dataRow(["3", "Motor de alertas", "Alertas + correo SMTP", "motor_alertas.py + email_sender.py + tests"], [1200, 2800, 2360, 3000]),
        dataRow(["4", "Dashboard Streamlit", "KPIs + vista anual + secciones", "app.py + charts.py + helpers.py"], [1200, 2800, 2360, 3000], GRAY_LIGHT),
        dataRow(["5", "Integración y cierre", "Sistema completo + README", "run.py + README.md + test_metricas_etl.py"], [1200, 2800, 2360, 3000]),
      ]
    }),
    new Paragraph({ spacing: { before: 240 }, children: [] }),

    h1("NOTAS CRÍTICAS — Leer antes de cada entrega"),
    new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [600, 8760],
      rows: [
        new TableRow({ children: [
          cell("1", { bold: true, shade: TEAL_DARK, color: WHITE, width: 600, center: true }),
          cell("Incluir SIEMPRE el Contexto Global al inicio del bloque — Antigravity no recuerda sesiones anteriores.", { width: 8760, shade: TEAL_LIGHT })
        ]}),
        new TableRow({ children: [
          cell("2", { bold: true, shade: TEAL_DARK, color: WHITE, width: 600, center: true }),
          cell("Base de datos NoSQL (Firestore), NO SQL. Sin tablas, sin JOINs. Toda la lógica de agregación va en Python.", { width: 8760 })
        ]}),
        new TableRow({ children: [
          cell("3", { bold: true, shade: TEAL_DARK, color: WHITE, width: 600, center: true }),
          cell("Nunca hardcodear credenciales. Todo en .env. firebase_credentials.json siempre en .gitignore.", { width: 8760, shade: TEAL_LIGHT })
        ]}),
        new TableRow({ children: [
          cell("4", { bold: true, shade: TEAL_DARK, color: WHITE, width: 600, center: true }),
          cell("Los campos desconocidos del JSON se preservan en campos_extra: {} — nunca descartar información.", { width: 8760 })
        ]}),
        new TableRow({ children: [
          cell("5", { bold: true, shade: TEAL_DARK, color: WHITE, width: 600, center: true }),
          cell("Archivos de muestra son ficticios — no usar datos reales de Laproff en tests ni en el repositorio.", { width: 8760, shade: TEAL_LIGHT })
        ]}),
        new TableRow({ children: [
          cell("6", { bold: true, shade: TEAL_DARK, color: WHITE, width: 600, center: true }),
          cell("El módulo es independiente del aplicativo existente de Laproff — no conectarse a él.", { width: 8760 })
        ]}),
        new TableRow({ children: [
          cell("7", { bold: true, shade: TEAL_DARK, color: WHITE, width: 600, center: true }),
          cell("Comentar el código en español. Mensajes de error descriptivos en español — el usuario final no es desarrollador.", { width: 8760, shade: TEAL_LIGHT })
        ]}),
        new TableRow({ children: [
          cell("8", { bold: true, shade: TEAL_DARK, color: WHITE, width: 600, center: true }),
          cell("Para cargar datos reales de Laproff: usar dry_run=True primero para revisar el reporte de calidad antes de cargar.", { width: 8760 })
        ]}),
      ]
    }),
    new Paragraph({ spacing: { before: 400 }, children: [] }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({
        text: "Práctica académica — Juliana González Afanador — Bioingeniería UdeA — Semestre 10 — 2026",
        size: 16, color: "94A3B8", italics: true, font: "Arial"
      })]
    }),
  ];
}

// ── DOCUMENTO ────────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 540, hanging: 360 } } } }]
      },
      {
        reference: "numbers",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 540, hanging: 360 } } } }]
      },
    ]
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 20, color: TEXT_DARK } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "Arial", color: TEAL_DARK },
        paragraph: { spacing: { before: 400, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: TEAL_DARK },
        paragraph: { spacing: { before: 300, after: 160 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: TEAL },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 2 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }
      }
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [
            new TextRun({ text: "PAME — Laproff  |  Página ", size: 16, color: "94A3B8", font: "Arial" }),
            new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "94A3B8", font: "Arial" }),
          ]
        })]
      })
    },
    children: [
      ...portada(),
      ...contextoGlobal(),
      ...bloque0(),
      ...bloque1(),
      ...bloque2(),
      ...bloque3(),
      ...bloque4(),
      ...bloque5(),
      ...resumen(),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/mnt/user-data/outputs/Instructivo_PAME_Laproff.docx", buffer);
  console.log("✓ Documento generado: Instructivo_PAME_Laproff.docx");
});
