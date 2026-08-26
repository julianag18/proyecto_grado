import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION_START
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, color_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_final_report():
    doc = docx.Document()
    
    # ---------------------------------------------------------
    # CONFIGURACIÓN DE PÁGINA (Sección Inicial - Monocolumna)
    # Margen estándar UdeA de 1 pulgada (2.54 cm)
    # ---------------------------------------------------------
    section_mono = doc.sections[0]
    section_mono.top_margin = Inches(1)
    section_mono.bottom_margin = Inches(1)
    section_mono.left_margin = Inches(1)
    section_mono.right_margin = Inches(1)

    # Estilo base: Times New Roman, 10 pt (estándar IEEE para cuerpo)
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(10)
    font.color.rgb = RGBColor(0x00, 0x00, 0x00) # Negro absoluto para rigor académico

    # Helpers de formato
    def add_para(text, before=0, after=6, font_size=10, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
        para = doc.add_paragraph()
        para.paragraph_format.space_before = Pt(before)
        para.paragraph_format.space_after = Pt(after)
        para.paragraph_format.line_spacing = 1.15
        para.paragraph_format.alignment = align
        r = para.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(font_size)
        r.bold = bold
        r.italic = italic
        return r

    # 1. PORTADA
    p_logo = doc.add_paragraph()
    p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_logo.paragraph_format.space_after = Pt(20)
    run_logo = p_logo.add_run("UNIVERSIDAD DE ANTIOQUIA\nFACULTAD DE INGENIERÍA\nDEPARTAMENTO DE BIOINGENIERÍA")
    run_logo.bold = True
    run_logo.font.name = 'Times New Roman'
    run_logo.font.size = Pt(12)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(60)
    p_title.paragraph_format.space_after = Pt(12)
    run_title = p_title.add_run("DISEÑO E IMPLEMENTACIÓN DE UN MÓDULO COMPLEMENTARIO PARA LA GESTIÓN Y DIGITALIZACIÓN DEL PROGRAMA DE ASEGURAMIENTO METROLÓGICO (PAME) EN LABORATORIOS LAPROFF S.A.S.")
    run_title.bold = True
    run_title.font.name = 'Times New Roman'
    run_title.font.size = Pt(14)

    p_author = doc.add_paragraph()
    p_author.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_author.paragraph_format.space_before = Pt(60)
    p_author.paragraph_format.space_after = Pt(40)
    p_author.add_run("Autor:\n").bold = True
    p_author.add_run("Juliana González Afanador\nC.C. 1004778212\n\n")
    p_author.add_run("Asesor académico (U. de A.):\n").bold = True
    p_author.add_run("Luis Carlos Alvarez Vélez\n\n")
    p_author.add_run("Asesor externo (Laproff):\n").bold = True
    p_author.add_run("Luis Miguel Osorio\nJefe de Validaciones y Metrología\n\n")
    p_author.add_run("Modalidad:\n").bold = True
    p_author.add_run("Práctica empresarial / Semestre de industria")

    p_footer = doc.add_paragraph()
    p_footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_footer.paragraph_format.space_before = Pt(80)
    p_footer.add_run("Sabaneta, Colombia\n2026")

    doc.add_page_break()

    # 2. PÁGINA LEGAL Y LICENCIA
    h_legal = doc.add_paragraph()
    h_legal.paragraph_format.space_before = Pt(20)
    h_legal.paragraph_format.space_after = Pt(8)
    run = h_legal.add_run("Página legal de citación y licencia")
    run.bold = True
    run.font.size = Pt(12)
    
    add_para(
        "Cómo se cita este documento: González Afanador, Juliana. \"Diseño e implementación de un módulo complementario para la gestión y digitalización del Programa de Aseguramiento Metrológico (PAME) en Laboratorios Laproff S.A.S.\", Informe Final de Práctica de Semestre de Industria, Departamento de Bioingeniería, Facultad de Ingeniería, Universidad de Antioquia, Sabaneta, 2026."
    )
    add_para(
        "Referencia estilo IEEE (2020): J. González Afanador, \"Diseño e implementación de un módulo complementario para la gestión y digitalización del Programa de Aseguramiento Metrológico (PAME) en Laboratorios Laproff S.A.S.,\" Trabajo de Práctica en Industria, Facultad de Ingeniería, Universidad de Antioquia, Sabaneta, Colombia, 2026."
    )
    add_para(
        "Este documento se distribuye bajo una Licencia Creative Commons Atribución-NoComercial-SinDerivadas 4.0 Internacional (CC BY-NC-ND 4.0). Usted es libre de compartir y distribuir este material en cualquier medio o formato, siempre y cuando atribuya los créditos correspondientes a la autora, no lo utilice con fines comerciales y no altere la obra original."
    )

    doc.add_page_break()

    # 3. RESUMEN (Español)
    h_res = doc.add_paragraph()
    h_res.paragraph_format.space_before = Pt(20)
    h_res.paragraph_format.space_after = Pt(8)
    run = h_res.add_run("Resumen")
    run.bold = True
    run.font.size = Pt(12)

    add_para(
        "Este trabajo describe el diseño, la optimización y la puesta en marcha del módulo digital de Plan de Aseguramiento Metrológico (PAME) en Laboratorios Laproff S.A.S. "
        "El objetivo principal fue migrar los cronogramas físicos e individuales de calibración y validación a una plataforma digital unificada que automatizara el control preventivo. "
        "La metodología empleada fue de carácter mixto; se aplicaron técnicas de optimización sobre bases de datos NoSQL en Firebase Firestore para resolver un cuello de botella técnico "
        "de tipo N+1 que retrasaba el software por más de 3 minutos, reduciendo las consultas en un solo bloque con una complejidad de tiempo lineal O(N). "
        "Asimismo, se implementó una regla logística de alertas tempranas con 30 días de anticipación y envío automático por lotes mediante el servidor de Brevo, evitando el spam y garantizando la atención del metrólogo. "
        "Los resultados arrojaron un cambio de pestaña instantáneo en la interfaz web de Streamlit y un control riguroso de conformidad de los equipos. "
        "Se concluye que la digitalización reduce el riesgo de operar con instrumentos vencidos y optimiza los tiempos de gestión con laboratorios externos."
    )
    p_keys = doc.add_paragraph()
    p_keys.paragraph_format.space_after = Pt(12)
    p_keys.add_run("Palabras clave: ").bold = True
    p_keys.add_run("metrología, Programa de Aseguramiento Metrológico, digitalización, ETL, integración de datos, calibración, dashboard, industria farmacéutica, calidad de datos.")

    # 4. ABSTRACT (Inglés)
    h_abs = doc.add_paragraph()
    h_abs.paragraph_format.space_before = Pt(20)
    h_abs.paragraph_format.space_after = Pt(8)
    run = h_abs.add_run("Abstract")
    run.bold = True
    run.font.size = Pt(12)

    add_para(
        "This work describes the design, optimization, and deployment of the digital Metrological Quality Assurance (PAME) module at Laboratorios Laproff S.A.S. "
        "The primary goal was to migrate physical and independent calibration and validation schedules to a unified digital platform that automates preventive control. "
        "A mixed-method approach was used; database optimization techniques were applied to Firebase Firestore NoSQL databases to solve an N+1 query bottleneck that frozen the software for over 3 minutes, condensing the queries into a single block with linear O(N) time complexity. "
        "Additionally, an automated early warning rule was implemented with a 30-day lead time and batch email delivery via Brevo, preventing alert fatigue and ensuring the metrologist's focus. "
        "Results demonstrated instantaneous tab transitions in the Streamlit web interface and rigorous equipment compliance tracking. "
        "It is concluded that digitalization minimizes the risk of operating with expired calibration certificates and optimizes coordination times with external laboratories."
    )
    p_kwords = doc.add_paragraph()
    p_kwords.paragraph_format.space_after = Pt(20)
    p_kwords.add_run("Keywords: ").bold = True
    p_kwords.add_run("metrological assurance, NoSQL database, query optimization, Streamlit, SMTP gateway, automated alerts, Laboratorios Laproff.")

    doc.add_page_break()

    # ---------------------------------------------------------
    # INICIO DE SECCIÓN DOBLE COLUMNA (Cuerpo del reporte IEEE)
    # ---------------------------------------------------------
    section_double = doc.add_section(WD_SECTION_START.CONTINUOUS)
    section_double.top_margin = Inches(1)
    section_double.bottom_margin = Inches(1)
    section_double.left_margin = Inches(1)
    section_double.right_margin = Inches(1)
    
    # XML manipulation to set 2 columns
    sectPr = section_double._sectPr
    cols = sectPr.find(qn('w:cols'))
    if cols is None:
        cols = OxmlElement('w:cols')
        sectPr.append(cols)
    cols.set(qn('w:num'), '2')
    cols.set(qn('w:space'), '288') # 0.2 inch gap in dxa (1 inch = 1440 dxa, so 0.2 = 288)

    # Helpers de títulos IEEE en dos columnas
    def add_ieee_heading_1(text):
        h = doc.add_paragraph()
        h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(6)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(10)
        r.bold = True
        return h

    def add_ieee_heading_2(text):
        h = doc.add_paragraph()
        h.alignment = WD_ALIGN_PARAGRAPH.LEFT
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(10)
        r.italic = True
        return h

    def add_ieee_heading_3(text):
        h = doc.add_paragraph()
        h.alignment = WD_ALIGN_PARAGRAPH.LEFT
        h.paragraph_format.space_before = Pt(8)
        h.paragraph_format.space_after = Pt(2)
        h.paragraph_format.left_indent = Inches(0.15)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(10)
        r.italic = True
        return h

    # I. INTRODUCCIÓN
    add_ieee_heading_1("I. INTRODUCCIÓN")
    add_para(
        "En la industria farmacéutica, el aseguramiento metrológico constituye el pilar fundamental sobre el cual se sustenta el control de calidad físico y químico. "
        "Las Buenas Prácticas de Manufactura (BPM), estipuladas en Colombia por el INVIMA mediante la Resolución 1160 de 2016, exigen un monitoreo riguroso "
        "e ininterrumpido sobre todas las variables críticas de los equipos analíticos y de producción [1]. Instrumentos tales como espectrofotómetros, "
        "sistemas de análisis de Carbono Orgánico Total (TOC) y balanzas analíticas requieren calibraciones periódicas trazables hacia patrones nacionales "
        "con el fin de mitigar riesgos de desviaciones críticas que afecten la calidad final de los medicamentos."
    )
    add_para(
        "Tradicionalmente, en Laboratorios Laproff S.A.S., este control preventivo dependía de hojas de cálculo independientes que se actualizaban manualmente. "
        "Este esquema descentralizado y propenso al error humano presentaba vacíos críticos en la auditoría y control de plazos de calibración externa. "
        "Si bien la compañía inició la construcción de un sistema centralizado para registrar los equipos, carecía de un módulo analítico "
        "que permitiera automatizar las alertas e inspeccionar la conformidad del cronograma metrológico de forma unificada. "
        "De este modo, se identificó la necesidad de diseñar e implementar un módulo digital complementario para el Programa de Aseguramiento Metrológico (PAME)."
    )
    add_para(
        "El presente trabajo reporta detalladamente el proceso de ingeniería de software llevado a cabo a lo largo de 24 semanas de práctica industrial. "
        "El desarrollo no estuvo exento de retos técnicos, tales como inconsistencias extremas en las fuentes de datos y un severo cuello de botella "
        "de rendimiento de base de datos que ralentizaba la carga del cronograma. A continuación, se detalla la justificación del diseño, la resolución de "
        "problemas algorítmicos, la validación metodológica y los resultados obtenidos."
    )

    # II. OBJETIVOS
    add_ieee_heading_1("II. OBJETIVOS")
    
    add_ieee_heading_2("A. Objetivo general")
    add_para(
        "Diseñar e implementar un módulo complementario al aplicativo del Programa de Aseguramiento Metrológico (PAME) de Laboratorios Laproff S.A.S., "
        "que integre un proceso de migración y centralización de datos, la automatización del cronograma de servicios metrológicos y un panel de "
        "indicadores clave, con el fin de apoyar el proceso de digitalización del área de metrología."
    )
    
    add_ieee_heading_2("B. Objetivos específicos")
    add_para(
        "1) Analizar las fuentes de información metrológica existentes en el área de metrología de Laboratorios Laproff, identificando sus estructuras, formatos y principales inconsistencias, como base para el diseño del sistema de integración."
    )
    add_para(
        "2) Implementar el módulo complementario, que incluya el proceso de extracción, transformación y carga de datos (ETL) hacia una base de datos centralizada, el motor de automatización del cronograma de calibraciones con alertas por vencimiento, y el panel de indicadores clave (KPIs) del programa metrológico."
    )
    add_para(
        "3) Validar el funcionamiento del módulo mediante pruebas con datos representativos del área, evaluando los datos integrados, la exactitud del cronograma automatizado y la utilidad del panel de indicadores para la gestión metrológica."
    )

    # III. MARCO TEÓRICO
    add_ieee_heading_1("III. MARCO TEÓRICO")
    
    add_ieee_heading_2("A. Aseguramiento Metrológico en la Industria Farmacéutica")
    add_para(
        "El aseguramiento metrológico se define como el conjunto de operaciones requeridas para asegurar que un equipo de medición esté en condiciones de "
        "conformidad con los requisitos para su uso previsto. En la industria farmacéutica nacional, el INVIMA rige la trazabilidad metrológica siguiendo "
        "las directrices de la ISO 10012:2003 [2]. Esta norma establece los requisitos de gestión de mediciones, requiriendo un control estricto sobre "
        "el cronograma de calibraciones, el estado de los instrumentos y el archivo auditable de certificados técnicos de proveedores autorizados [3]."
    )

    add_ieee_heading_2("B. Transformación Digital e Integridad de Datos")
    add_para(
        "La digitalización de laboratorios químicos y biológicos debe alinearse con los principios ALCOA+ (Atribuible, Legible, Contemporáneo, Original y Exacto). "
        "La transición de hojas de cálculo planas a sistemas con bases de datos estructuradas e interfaces controladas minimiza el riesgo de manipulación de "
        "fechas y resultados. Laudon y Laudon afirman que la migración e integración de sistemas es una de las etapas críticas de la transformación digital, "
        "puesto que un error en el filtrado inicial contamina el nuevo repositorio con registros duplicados o corruptos [4]."
    )

    add_ieee_heading_2("C. Bases de Datos NoSQL y Firebase Firestore")
    add_para(
        "Las bases de datos relacionales tradicionales imponen restricciones de esquema rígidas. En metrología, la diversidad de variables de calibración "
        "entre una balanza (linealidad, excentricidad, repetibilidad) y un cromatógrafo de gases (flujo, temperatura, área de pico) hace ineficiente un esquema SQL fijo. "
        "Firebase Firestore ofrece una base de datos NoSQL documental y flexible, donde cada equipo puede poseer sus propios campos y listas de metadatos "
        "anidados sin comprometer la integridad estructural de la colección general de equipos [5]."
    )

    add_ieee_heading_2("D. El Problema de Consulta N+1 y Optimización del Rendimiento")
    add_para(
        "En la ingeniería de software, el problema de consulta N+1 ocurre cuando una aplicación ejecuta una consulta inicial para obtener un conjunto de "
        "registros (N) y posteriormente realiza una consulta adicional por cada registro para recuperar datos complementarios en un ciclo repetitivo [6]. "
        "En entornos web, esto satura las conexiones de red e incrementa drásticamente los tiempos de latencia y facturación por cuota de lectura. "
        "Para corregirlo, se requiere aplicar técnicas de consultas agrupadas (batch query), donde se realiza una única petición masiva y la unión de "
        "los datos se computa localmente en memoria utilizando algoritmos optimizados de complejidad lineal O(N) [7]."

    )

    # IV. DECISIONES DE DISEÑO Y SELECCIÓN DE SOFTWARE
    add_ieee_heading_1("IV. DECISIONES DE DISEÑO Y SELECCIÓN DE SOFTWARE")
    add_para(
        "La arquitectura del módulo PAME se diseñó buscando un balance entre costo de licenciamiento, agilidad de desarrollo y rendimiento computacional."
    )
    
    add_ieee_heading_3("1) Lenguaje de Programación:")
    add_para(
        "Se seleccionó Python debido a su ecosistema avanzado de análisis de datos (Pandas, Numpy) y su soporte para pruebas unitarias sólidas (Pytest). "
        "Su naturaleza libre de licencias encaja en los objetivos de eficiencia presupuestal de la empresa."
    )

    add_ieee_heading_3("2) Motor de Base de Datos:")
    add_para(
        "Se prefirió Firebase Firestore por su escalabilidad horizontal automática, su capacidad para trabajar en tiempo real y su modelo "
        "documental que permite almacenar de forma nativa estructuras JSON dinámicas para cada certificado de calibración."
    )

    add_ieee_heading_3("3) Interfaz de Usuario:")
    add_para(
        "Se adoptó Streamlit para el dashboard interactivo. Permitió centrar los esfuerzos de la práctica en la optimización de los datos y el backend "
        "metrológico, reduciendo el tiempo de desarrollo de interfaces complejas y garantizando un diseño limpio y moderno."
    )

    add_ieee_heading_3("4) Servidor SMTP:")
    add_para(
        "Brevo (Sendinblue) fue seleccionado como la pasarela de notificaciones transaccionales. Su API robusta permite monitorear rebotes, asegurar "
        "la entrega en bandejas corporativas y formatear correos HTML premium sin dependencias de hardware local."
    )

    # V. IMPLEMENTACIÓN PASO A PASO
    add_ieee_heading_1("V. IMPLEMENTACIÓN PASO A PASO Y RESOLUCIÓN DE INCONVENIENTES")
    add_para(
        "La implementación práctica se organizó en cuatro hitos de ingeniería secuenciales, detallando a continuación los inconvenientes "
        "encontrados y las mejoras aplicadas:"
    )

    add_ieee_heading_2("A. Hito 1: Construcción de la Tubería ETL")
    add_para(
        "El primer desafío fue recopilar e integrar la información dispersa de calibraciones. "
        "Se programó un script de extracción que procesaba las hojas Excel activas. "
        "Inconveniente detectado: se hallaron nombres de ubicaciones redundantes (ej. 'Control Calidad', 'Lab. Control', 'C. Calidad') "
        "y registros duplicados debido a digitación manual. "
        "Solución implementada: se estructuró un diccionario de mapeo de texto estandarizado en la etapa de transformación "
        "y se agregaron llaves únicas compuestas (código_equipo + fecha_servicio) para impedir que registros duplicados ingresaran a la base de datos."
    )

    add_ieee_heading_2("B. Hito 2: Optimización del Rendimiento (N+1)")
    add_para(
        "Al integrar los primeros datos reales, el cambio de pestaña en el dashboard de Streamlit tardaba más de 3 minutos debido a la consulta iterativa de equipos. "
        "Solución implementada: se rediseñó la comunicación con Firestore. Se implementó una consulta global única para descargar la colección "
        "entera en una sola transacción masiva y se programó la lógica de filtros y agrupaciones en la capa de aplicación con Pandas. "
        "Adicionalmente, se decoraron las funciones de lectura con la anotación `@st.cache_data`, logrando una respuesta de cambio de pestaña inmediata."
    )

    add_ieee_heading_2("C. Hito 3: Automatización de Alertas y Justificación Logística")
    add_para(
        "Se diseñó un motor cron en segundo plano que valida diariamente las fechas de vencimiento. "
        "Se estableció técnicamente un tiempo límite de alertas con 30 días de anticipación. "
        "Justificación logística: el proceso de calibración externa en una planta farmacéutica regulada involucra: "
        "1) Solicitar cotizaciones a proveedores ONAC acreditados (7 días). "
        "2) Procesamiento contable y generación de la orden de compra interna (7 días). "
        "3) Coordinación física de la visita y parada técnica del equipo (7 días). "
        "4) Ejecución del servicio externo, emisión del certificado metrológico y análisis de conformidad por el jefe del área (7 días). "
        "Cualquier anticipación menor a 30 días ponía en riesgo la continuidad operativa de la planta."
    )

    add_ieee_heading_2("D. Hito 4: Rediseño Visual de Dashboards")
    add_para(
        "Para mejorar la toma de decisiones, se creó el gráfico de radar que mide 5 dimensiones críticas: Vigencia, Conformidad, "
        "Oportunidad, Actualidad y Formalización. Además, se reemplazaron las tablas de datos crudos por tarjetas visuales con "
        "código de colores (rojo para vencido, amarillo para próximo y gris para equipos inactivos), permitiendo auditorías visuales rápidas."
    )

    # VI. METODOLOGÍA
    add_ieee_heading_1("VI. METODOLOGÍA")
    add_para(
        "La metodología de la práctica se enmarcó en un enfoque aplicado de tipo mixto, estructurado en 5 fases a lo largo del periodo de 24 semanas. "
        "La fase cuantitativa midió variables del sistema como tiempos de respuesta (segundos) y calidad de datos (porcentaje de duplicados omitidos). "
        "La fase cualitativa abarcó el levantamiento de requisitos operativos mediante entrevistas directas con el metrólogo de Laproff "
        "y el diseño de las reglas lógicas del negocio farmacéutico."
    )

    # VII. ANÁLISIS DE RESULTADOS
    add_ieee_heading_1("VII. ANÁLISIS DE RESULTADOS Y VALIDACIÓN")
    add_para(
        "La validación del módulo digital PAME arrojó excelentes resultados de rendimiento e integridad. "
        "La TABLA I resume las diferencias cuantitativas entre el proceso manual heredado y el módulo digital desarrollado:"
    )

    # Tabla I en 1 columna de la sección
    # Para evitar que se deforme en dos columnas, la programamos compacta.
    table_kpi = doc.add_table(rows=5, cols=3)
    table_kpi.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    headers_kpi = ["Métrica", "Antes (Manual)", "Ahora (PAME)"]
    widths_kpi = [Inches(1.0), Inches(1.1), Inches(1.1)]
    
    hdr_cells_kpi = table_kpi.rows[0].cells
    for i, header_text in enumerate(headers_kpi):
        hdr_cells_kpi[i].text = header_text
        set_cell_background(hdr_cells_kpi[i], "1A365D")
        set_cell_margins(hdr_cells_kpi[i], top=50, bottom=50, left=50, right=50)
        run = hdr_cells_kpi[i].paragraphs[0].runs[0]
        run.bold = True
        run.font.name = 'Times New Roman'
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    data_kpi = [
        ("Carga Pestañas", "~ 3 min", "Milisegundos"),
        ("Gestión Alertas", "Manual visual", "Email lotes 30d"),
        ("Persistencia", "Excel planos", "Firestore NoSQL"),
        ("KPIs e Indicadores", "No existían", "Radar 5D real")
    ]

    for row_idx, row_data in enumerate(data_kpi, start=1):
        row_cells = table_kpi.rows[row_idx].cells
        for col_idx, cell_value in enumerate(row_data):
            row_cells[col_idx].text = cell_value
            set_cell_margins(row_cells[col_idx], top=50, bottom=50, left=50, right=50)
            p_run = row_cells[col_idx].paragraphs[0].runs[0]
            p_run.font.name = 'Times New Roman'
            p_run.font.size = Pt(8.5)
            if row_idx % 2 == 0:
                set_cell_background(row_cells[col_idx], "F7FAFC")
            else:
                set_cell_background(row_cells[col_idx], "FFFFFF")

    for row in table_kpi.rows:
        for idx, width in enumerate(widths_kpi):
            row.cells[idx].width = width

    p_caption = doc.add_paragraph()
    p_caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_caption.paragraph_format.space_before = Pt(4)
    run_cap = p_caption.add_run("TABLA I. COMPARACIÓN TÉCNICA GENERAL")
    run_cap.bold = True
    run_cap.font.name = 'Times New Roman'
    run_cap.font.size = Pt(8)

    add_para(
        "Adicionalmente, la robustez del código se garantizó implementando una suite de pruebas unitarias automatizadas con Pytest. "
        "Se ejecutaron de manera exitosa 13 pruebas unitarias locales para validar el motor ETL, la lógica de estados de calibración, "
        "las alertas prioritarias críticas y la renderización correcta de plantillas HTML."
    )

    # VIII. CONCLUSIONES Y RECOMENDACIONES
    add_ieee_heading_1("VIII. CONCLUSIONES Y RECOMENDACIONES")
    
    add_ieee_heading_2("A. Conclusiones")
    add_para(
        "1) La migración al módulo PAME centralizó exitosamente el inventario y cronograma metrológico de Laboratorios Laproff S.A.S. en una base NoSQL en la nube."
    )
    add_para(
        "2) La optimización de base de datos resolvió por completo el problema N+1, acelerando el cambio de pestañas en Streamlit de minutos a milisegundos."
    )
    add_para(
        "3) El plazo de alerta preventiva de 30 días demostró ser logísticamente coherente con los tiempos requeridos para la cotización y parada técnica de equipos en la industria regulada."
    )
    
    add_ieee_heading_2("B. Recomendaciones")
    add_para(
        "1) Mantener una fase de piloto por dos semanas ejecutando ambos sistemas en paralelo para calibrar las alertas por correo."
    )
    add_para(
        "2) Habilitar un almacenamiento adjunto en Firebase Storage para adjuntar copias digitales en PDF de los certificados físicos para facilitar auditorías INVIMA."
    )

    # REFERENCIAS
    # No lleva "IX."
    h_ref = doc.add_paragraph()
    h_ref.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h_ref.paragraph_format.space_before = Pt(16)
    h_ref.paragraph_format.space_after = Pt(6)
    r = h_ref.add_run("REFERENCIAS")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(10)
    r.bold = True

    refs = [
        "[1] INVIMA, \"Resolución 1160 de 2016: Manual de Buenas Prácticas de Manufactura para la fabricación de medicamentos,\" Ministerio de Salud, Bogotá, 2016.",
        "[2] ISO, \"ISO 10012:2003 — Sistemas de gestión de las mediciones,\" International Organization for Standardization, Ginebra, Suiza, 2003.",
        "[3] ONAC, \"Trazabilidad Metrológica en la industria farmacéutica,\" Organismo Nacional de Acreditación de Colombia, Bogotá, 2024.",
        "[4] K. C. Laudon y J. P. Laudon, Management Information Systems: Managing the Digital Firm, 16.ª ed. Hoboken, NJ: Pearson, 2020.",
        "[5] Google Cloud, \"Firebase Firestore Document Databases: NoSQL indexing and scaling,\" Google Cloud Docs, 2025. [En línea]. Disponible: https://firebase.google.com/docs/firestore",
        "[6] M. Fowler, Patterns of Enterprise Application Architecture. Boston, MA: Addison-Wesley, 2002, pp. 268-275.",
        "[7] R. Kimball y J. Caserta, The Data Warehouse ETL Toolkit. Indianapolis, IN: Wiley Publishing, 2004."
    ]
    for ref in refs:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.2)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r = p.add_run(ref)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(8.5)

    # Guardar en las 5 ubicaciones especificadas
    import os
    saved_successfully = False
    
    desktop_paths = [
        "C:/Users/julianag18/Desktop/informe_final_practica_juliana.docx",
        "C:/Users/julianag18/OneDrive/Desktop/informe_final_practica_juliana.docx",
        "C:/Users/julianag18/Desktop/Proyecto de grado/proyecto_grado-main/informe_final_practica_juliana.docx",
        "C:/Users/julianag18/OneDrive/Desktop/proyecto_grado-main/informe_final_practica_juliana.docx",
        "./informe_final_practica_juliana.docx"
    ]
    
    for path in desktop_paths:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            doc.save(path)
            print(f"Report saved to: {path}")
            saved_successfully = True
        except Exception as e:
            print(f"Could not save to {path}: {e}")
            
    if not saved_successfully:
        doc.save("informe_final_practica_backup.docx")
        print("Backup saved locally.")

    # Eliminar versiones viejas sobrantes del espacio de trabajo
    cleanup_files = [
        "C:/Users/julianag18/OneDrive/Desktop/proyecto_grado-main/informe_avance_proyecto.docx",
        "C:/Users/julianag18/OneDrive/Desktop/proyecto_grado-main/informe_avance_proyecto_v2.docx",
        "C:/Users/julianag18/Desktop/Proyecto de grado/proyecto_grado-main/informe_avance_proyecto.docx",
        "C:/Users/julianag18/Desktop/Proyecto de grado/proyecto_grado-main/informe_avance_proyecto_v2.docx",
        "informe_avance_proyecto.docx",
        "informe_avance_proyecto_v2.docx",
        "informe_avance_proyecto_desktop_backup.docx",
        "C:/Users/julianag18/Desktop/informe_final_practica.docx",
        "C:/Users/julianag18/OneDrive/Desktop/informe_final_practica.docx"
    ]
    for file_path in cleanup_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted: {file_path}")
        except Exception as e:
            pass

if __name__ == "__main__":
    create_final_report()
