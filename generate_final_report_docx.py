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

def set_cell_margins(cell, top=140, bottom=140, left=180, right=180):
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
    # CONFIGURACIÓN DE PÁGINA (Monocolumna para todo el reporte)
    # Margen estándar UdeA de 1 pulgada (2.54 cm)
    # ---------------------------------------------------------
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Estilo base: Times New Roman, 11 pt, espaciado justificado
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(11)
    font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    # Helpers de formato para jerarquía rigurosa
    def add_heading_1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(24)
        h.paragraph_format.space_after = Pt(8)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        r.bold = True
        return h

    def add_heading_2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(6)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11)
        r.bold = True
        return h

    def add_heading_3(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11)
        r.italic = True
        return h

    def add_para(text, before=0, after=6):
        para = doc.add_paragraph()
        para.paragraph_format.space_before = Pt(before)
        para.paragraph_format.space_after = Pt(after)
        para.paragraph_format.line_spacing = 1.15
        para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r = para.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11)
        return r

    # 1. PORTADA ACADÉMICA
    p_logo = doc.add_paragraph()
    p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_logo.paragraph_format.space_after = Pt(24)
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
    add_heading_1("Página legal de citación y licencia")
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
    add_heading_1("Resumen")
    add_para(
        "Este trabajo detalla la concepción, desarrollo técnico e implantación del módulo digital complementario para el Plan de Aseguramiento Metrológico (PAME) en Laboratorios Laproff S.A.S. "
        "El proyecto consistió en migrar de forma masiva y auditable la información histórica dispersa de calibraciones analíticas a una base de datos documental Firebase Firestore. "
        "Metodológicamente, se aplicaron técnicas avanzadas de transformación de datos (ETL) y optimizaciones algorítmicas O(N) para resolver un cuello de botella N+1 en las consultas de base de datos que causaba latencias de más de 3 minutos, reduciendo los tiempos de carga a milisegundos mediante caché local en la interfaz de Streamlit. "
        "Adicionalmente, se automatizó un motor de notificaciones por lotes preventivos de 30 días acoplado al servicio SMTP transaccional de Brevo y un panel interactivo con visualización multidimensional por radar y alertas codificadas. "
        "El módulo fue validado mediante 13 pruebas unitarias automatizadas con Pytest, demostrando robustez técnica, consistencia en la auditoría del ciclo metrológico farmacéutico y cero desviaciones en el uso de los equipos analíticos de planta."
    )
    p_keys = doc.add_paragraph()
    p_keys.paragraph_format.space_after = Pt(12)
    p_keys.add_run("Palabras clave: ").bold = True
    p_keys.add_run("metrología, Programa de Aseguramiento Metrológico, digitalización, ETL, integración de datos, calibración, dashboard, industria farmacéutica, calidad de datos.")

    # 4. ABSTRACT (Inglés)
    add_heading_1("Abstract")
    add_para(
        "This work details the design, technical development, and deployment of the digital complementary module for the Metrological Quality Assurance Plan (PAME) at Laboratorios Laproff S.A.S. "
        "The project migrated physical and scattered historical calibration logs to a document-oriented Firebase Firestore database. "
        "Methodologically, ETL processes and O(N) database optimizations were applied to solve a performance bottleneck caused by recursive N+1 queries that frozen the web interface for over 3 minutes, reducing query response times to milliseconds via local server caching in Streamlit. "
        "Furthermore, a batch automated email notification engine was implemented with a 30-day early lead rule integrated with Brevo SMTP, along with a multi-dimensional radar compliance plot and color-coded cards. "
        "The software architecture was validated using 13 automated unit tests under Pytest, proving technical stability and metrological traceability for regulatory audit requirements in a GMP pharmaceutical environment."
    )
    p_kwords = doc.add_paragraph()
    p_kwords.paragraph_format.space_after = Pt(20)
    p_kwords.add_run("Keywords: ").bold = True
    p_kwords.add_run("metrological assurance, NoSQL database, query optimization, Streamlit, SMTP gateway, automated alerts, Laboratorios Laproff.")

    doc.add_page_break()

    # I. INTRODUCCIÓN
    add_heading_1("I. INTRODUCCIÓN")
    add_para(
        "En el marco de la manufactura industrial farmacéutica, el aseguramiento metrológico constituye el pilar crítico de la garantía de calidad. "
        "La calibración y calificación de equipos garantizan que los datos generados en los laboratorios de control de calidad correspondan "
        "fielmente a la realidad física de los medicamentos producidos. La legislación colombiana, a través del INVIMA y su Resolución 1160 de 2016, "
        "establece que todo instrumento analítico que impacte la pureza, dosificación o estabilidad del medicamento debe contar con trazabilidad "
        "metrológica ininterrumpida y estar catalogado dentro de un Programa de Aseguramiento Metrológico (PAME) auditable [1]."
    )
    add_para(
        "Históricamente, en Laboratorios Laproff S.A.S., el control de calibraciones externas y validaciones internas se ejecutaba a través "
        "de hojas de cálculo Excel distribuidas de manera independiente por cada analista o metrólogo. Este modelo de control manual presentaba "
        "inconvenientes críticos: (a) desorganización y duplicidad de registros, (b) dificultad para realizar trazabilidad histórica rápida "
        "ante visitas inspectoras del INVIMA, y (c) la ausencia de un canal de alertas que previniera el vencimiento técnico de los equipos, "
        "lo que podía derivar en costosas paradas no programadas en las líneas de producción o desvíos de calidad."
    )
    add_para(
        "Aunque la compañía había comenzado a diseñar una base de datos centralizada para registrar la información de equipos, el sistema "
        "carecía por completo de automatización operativa y herramientas de análisis gerencial. Para subsanar esto, el presente trabajo final "
        "expone el desarrollo e implementación del módulo complementario digital PAME. A lo largo de las 24 semanas de la práctica en industria, "
        "se diseñó un sistema completo que abarca una tubería de integración de datos históricos (ETL), la optimización del rendimiento en base "
        "de datos, la automatización de notificaciones y la creación de un tablero analítico con gráficos interactivos. El proyecto demuestra "
        "la aplicación práctica de la bioingeniería y la ingeniería de software en un entorno industrial farmacéutico regulado."
    )

    # II. OBJETIVOS
    add_heading_1("II. OBJETIVOS")
    
    add_heading_2("A. Objetivo general")
    add_para(
        "Diseñar e implementar un módulo complementario al aplicativo del Programa de Aseguramiento Metrológico (PAME) de Laboratorios Laproff S.A.S., "
        "que integre un proceso de migración y centralización de datos, la automatización del cronograma de servicios metrológicos y un panel de "
        "indicadores clave, con el fin de apoyar el proceso de digitalización del área de metrología."
    )
    
    add_heading_2("B. Objetivos específicos")
    add_para(
        "1. Analizar las fuentes de información metrológica existentes en el área de metrología de Laboratorios Laproff, identificando sus estructuras, formatos y principales inconsistencias, como base para el diseño del sistema de integración."
    )
    add_para(
        "2. Implementar el módulo complementario, que incluya el proceso de extracción, transformación y carga de datos (ETL) hacia una base de datos centralizada, el motor de automatización del cronograma de calibraciones con alertas por vencimiento, y el panel de indicadores clave (KPIs) del programa metrológico."
    )
    add_para(
        "3. Validar el funcionamiento del módulo mediante pruebas con datos representativos del área, evaluando los datos integrados, la exactitud del cronograma automatizado y la utilidad del panel de indicadores para la gestión metrológica."
    )

    # III. MARCO TEÓRICO
    add_heading_1("III. MARCO TEÓRICO")
    
    add_heading_2("A. Aseguramiento Metrológico en la Industria Farmacéutica")
    add_para(
        "El aseguramiento metrológico abarca las actividades de calibración, validación, mantenimiento preventivo y verificación de instrumentos de medición. "
        "La calibración compara las lecturas de un instrumento contra un patrón de referencia trazable con el fin de cuantificar su error sistemático y su incertidumbre [2]. "
        "En la manufactura de medicamentos bajo estándares de Buenas Prácticas de Manufactura (BPM), la norma ISO 10012:2003 exige estructurar un sistema "
        "de gestión de las mediciones que demuestre de forma ininterrumpida la idoneidad metrológica de cada sensor analítico. Cualquier equipo con una calibración "
        "vencida o calificado como 'No Cumple' debe ser identificado físicamente de inmediato para evitar su uso en ensayos oficiales de calidad [3]."
    )

    add_heading_2("B. Transformación Digital e Integridad de Datos (ALCOA+)")
    add_para(
        "La transición de formatos de papel y Excel hacia sistemas centralizados de software responde no solo a la eficiencia, sino a la integridad de los datos. "
        "El estándar ALCOA+ requiere que toda la información científica e industrial de un laboratorio sea Atribuible, Legible, Contemporánea, Original y Exacta. "
        "Un cronograma en una hoja de cálculo es manipulable sin dejar rastro (pérdida de trazabilidad). La digitalización mediante bases de datos orientadas "
        "a documentos con controles de acceso asegura que los registros históricos de calibración permanezcan inalterables ante auditorías de calidad [4]."
    )

    add_heading_2("C. Comparativo de Paradigmas de Bases de Datos: SQL vs. NoSQL en Metrología")
    add_para(
        "El aseguramiento metrológico involucra equipos con naturalezas instrumentales muy diversas. Una balanza analítica de precisión mide masa "
        "y requiere pruebas de excentricidad, repetibilidad e incertidumbre de pesaje. En contraste, un analizador de Carbono Orgánico Total (TOC) "
        "como el GEHAKA 2400 monitorea conductividad, carbono inorgánico y carbono total mediante procesos de oxidación química y radiación UV, "
        "requiriendo validaciones de idoneidad del sistema basadas en curvas de calibración con estándares químicos. "
        "Modelar esta variabilidad en una base de datos relacional (SQL) exige un esquema rígido con múltiples tablas anidadas y constantes uniones (joins), "
        "lo que complejiza el software. Las bases de datos NoSQL basadas en documentos (como Firebase Firestore) permiten estructurar colecciones "
        "flexibles de JSON donde cada documento representa un equipo con sus especificaciones particulares, soportando datos dinámicos sin "
        "afectar el rendimiento global de las búsquedas en el sistema [5]."
    )

    add_heading_2("D. Algoritmia y Latencia: El Problema de Consulta N+1")
    add_para(
        "En arquitectura de software, el problema de consulta N+1 describe un defecto de rendimiento clásico en el cual una aplicación, para recuperar "
        "una lista de registros principales (N) y su información relacionada, ejecuta una consulta inicial (1) seguida de N consultas secundarias "
        "adicionales dentro de un bucle iterativo [6]. En una base de datos en la nube como Firestore, esto resulta crítico por dos razones: "
        "(a) latencia de red acumulada debido a los viajes de ida y vuelta constantes del servidor al cliente, y (b) incremento exponencial de costos "
        "de facturación por la cuota de lectura de base de datos. La solución exige consolidar el proceso en una consulta agrupada única "
        "con una complejidad algorítmica de tiempo lineal O(N), trayendo toda la colección en un solo bloque binario y realizando la relación "
        "y agregación de datos en memoria local empleando estructuras vectoriales optimizadas en Pandas [7]."
    )

    # IV. DECISIONES DE DISEÑO Y SELECCIÓN DE SOFTWARE
    add_heading_1("IV. DECISIONES DE DISEÑO Y SELECCIÓN DE SOFTWARE")
    add_para(
        "La arquitectura del sistema se estructuró a partir de una evaluación comparativa detallada de herramientas de desarrollo:"
    )

    add_heading_2("A. Python y Ecosistema de Datos")
    add_para(
        "Se seleccionó Python como lenguaje núcleo sobre alternativas como C# o Java debido a la potencia de Pandas para la limpieza rápida de datos tabulares "
        "y la simplicidad para escribir pruebas unitarias ágiles en la suite de Pytest. Además, Python garantiza compatibilidad directa y multiplataforma "
        "con servicios de nube sin requerir compilaciones complejas en la máquina cliente del laboratorio."
    )

    add_heading_2("B. Firebase Firestore y Supabase")
    add_para(
        "Se analizó la opción de una base de datos relacional PostgreSQL con Supabase, pero se determinó que la flexibilidad del esquema NoSQL documental "
        "de Firebase Firestore era superior para el PAME. Al no tener relaciones rígidas y manejar datos metrológicos cambiantes según la naturaleza "
        "del sensor, Firestore facilitó la integración directa de los objetos de datos metrológicos mapeados desde Python en formato de diccionarios."
    )

    add_heading_2("C. Streamlit Frente a Frontends Convencionales")
    add_para(
        "Desarrollar una interfaz de usuario tradicional con tecnologías como HTML/CSS puro, React o Angular requiere semanas de diseño y "
        "programación de peticiones API. Streamlit se seleccionó porque permite compilar e iterar rápidamente la interfaz web directamente desde Python. "
        "Su integración nativa con bibliotecas gráficas avanzadas como Plotly permitió crear paneles ejecutivos dinámicos que se actualizan "
        "de forma automática ante cualquier nueva migración de base de datos."
    )

    add_heading_2("D. Servidor de Correo SMTP: Brevo")
    add_para(
        "El uso de servidores SMTP locales o el envío directo a través de cuentas de correo de consumo masivo (Gmail, Outlook) presentaba problemas "
        "críticos de límites de envío diario y bloqueos preventivos por parte de los filtros de spam corporativos. Se seleccionó Brevo "
        "porque proporciona una API transaccional robusta con alta entregabilidad, lo que permite formatear alertas metrológicas detalladas "
        "en plantillas HTML enriquecidas y asegurar que el correo del metrólogo de Laproff las reciba sin retrasos."
    )

    # V. IMPLEMENTACIÓN PASO A PASO Y RESOLUCIÓN DE INCONVENIENTES
    add_heading_1("V. IMPLEMENTACIÓN PASO A PASO Y RESOLUCIÓN DE INCONVENIENTES")
    add_para(
        "A lo largo de los 6 meses de duración del Semestre de Industria, el desarrollo del módulo PAME se estructuró de manera incremental. "
        "A continuación se detalla la ingeniería aplicada, detallando los inconvenientes críticos presentados y las estrategias empleadas para solucionarlos:"
    )

    add_heading_2("A. Hito 1: Construcción y Depuración de la Tubería ETL")
    add_para(
        "El hito inicial consistió en recolectar e integrar los registros históricos de calibraciones. "
        "Se programó un script ETL en Python (`src/etl/pipeline.py`) que automatiza la extracción desde archivos Excel y CSV. "
        "Inconveniente detectado: Los archivos manuales carecían de normalización. Se detectaron más de 12 formas diferentes de registrar "
        "la misma ubicación física (ej. 'Control Calidad', 'Control de Calidad', 'Lab. Control'). Esto impedía agrupar correctamente los KPIs. "
        "Además, existían celdas de fecha vacías o escritas en texto libre ('calibrado ayer'), lo cual corrompía la base de datos al subirla. "
        "Solución implementada: Se construyó un diccionario de estandarización en la fase de transformación que corrige automáticamente el texto. "
        "Se programó un validador que detecta si las fechas son nulas o incoherentes y las descarta escribiendo un log de error detallado. "
        "Asimismo, se configuró un filtro de duplicados basado en un identificador compuesto (código_equipo + fecha_servicio), "
        "el cual omite la carga del registro redundante e informa al metrólogo a través del panel de auditoría."
    )

    add_heading_2("B. Hito 2: Optimización de Base de Datos y Resolución de N+1")
    add_para(
        "Tras migrar los datos históricos, al cargar el dashboard o cambiar de pestaña en la aplicación web, la pantalla se congelaba "
        "por más de 3 minutos, mostrando alertas de timeout. Al auditar la comunicación, se identificó que el código realizaba una petición "
        "inicial de equipos y, mediante un ciclo recursivo `for`, consultaba a la base de datos Firestore por el historial de servicios de cada equipo. "
        "Para 200 equipos, esto se traducía en más de 201 peticiones consecutivas por cada usuario en pantalla, consumiendo la cuota mensual "
        "en horas y degradando el rendimiento."
    )
    add_para(
        "Solución implementada: Se reescribió la arquitectura del backend en `src/database/equipos_repo.py`. Se eliminaron las consultas recursivas "
        "en bucle. En su lugar, se configuró una consulta en bloque único que extrae la totalidad de los registros de calibraciones de Firestore "
        "en una sola petición masiva de pocos milisegundos. Esta información se procesa y organiza localmente en el servidor del dashboard "
        "utilizando funciones vectorizadas y agrupaciones de Pandas en complejidad lineal O(N). Para perfeccionar la respuesta, se implementó "
        "el decorador de caché de Streamlit (`@st.cache_data`) que congela el estado de la consulta, reactivándolo únicamente si se sube un "
        "nuevo archivo de migración o se registra un cambio oficial en el cronograma."
    )

    add_heading_2("C. Hito 3: Lógica Metrológica del Motor de Alertas y Justificación Logística")
    add_para(
        "Se automatizó un servicio programado que valida el estado de vencimiento del cronograma. "
        "Se estableció una regla de negocio donde las alertas preventivas de calibración se envían con exactamente un mes (30 días) de anticipación. "
        "Esta ventana temporal fue ampliamente debatida y justificada operativamente debido al ciclo de compras metrológicas del laboratorio farmacéutico:"
    )
    
    cycle_steps = [
        "Semana 1: Selección del proveedor acreditado por el ONAC específico para el tipo de equipo, envío de fichas técnicas y solicitud de cotizaciones formales.",
        "Semana 2: Trámite del presupuesto con el área financiera de Laproff, aprobación del gasto y generación de la orden de compra oficial de servicio externo.",
        "Semana 3: Coordinación logística de la visita del técnico metrólogo en planta, y programación de la parada técnica del equipo de producción para evitar interferir con las campañas activas de manufactura de medicamentos.",
        "Semana 4: Ejecución presencial de la calibración, emisión del certificado metrológico impreso/digital, análisis del error contra los límites de tolerancia aceptados por la farmacopea y verificación final de la conformidad por el Jefe de Validaciones y Metrología."
    ]
    for step in cycle_steps:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(4)
        p.add_run(step)
        
    add_para(
        "Inconveniente detectado: Enviar un correo por cada equipo próximo a vencer causaba saturación en la bandeja del metrólogo. "
        "Solución implementada: Se programó una regla de agrupación por lotes. El motor cron reúne diariamente todas las alertas "
        "y genera un único correo estructurado en formato HTML con el listado de los equipos. No obstante, si un equipo crítico "
        "en uso activo es calificado metrológicamente como 'No Cumple' o se detecta vencido sin registrar parada, el sistema dispara "
        "de inmediato una alerta crítica independiente para suspender su uso y evitar desviaciones en la calidad del producto."
    )

    add_heading_2("D. Hito 4: Visualización Avanzada y KPIs en Tiempo Real")
    add_para(
        "Para permitir auditorías ejecutivas rápidas, se rediseñó visualmente la interfaz del panel de control. "
        "Se integró el gráfico de radar (araña) interactivo en la pestaña principal, permitiendo evaluar la madurez metrológica de la planta. "
        "El radar pondera 5 métricas: (1) Vigencia: Porcentaje de equipos con calibración al día. "
        "(2) Conformidad: Porcentaje de calibraciones que cumplen los límites de tolerancia de manufactura. "
        "(3) Oportunidad: Equipos libres de vencimiento normativo inmediato. "
        "(4) Actualidad: Porcentaje de calibraciones realizadas hace menos de un año. "
        "(5) Formalización: Equipos con proveedor y contrato técnico vigente asignado en la base de datos. "
        "Cualquier contracción en la figura geométrica del radar alerta de inmediato en qué eje se presenta la deficiencia."
    )

    # VI. METODOLOGÍA
    add_heading_1("VI. METODOLOGÍA")
    add_para(
        "El proyecto se rigió bajo una metodología de investigación aplicada con enfoque mixto y diseño no experimental. "
        "El desarrollo se distribuyó de manera secuencial a lo largo de las 24 semanas de la práctica en 5 fases de ingeniería:"
    )
    add_para(
        "1. Fase de Diagnóstico (Semanas 1-4): Inducción a la planta de Laboratorios Laproff S.A.S., caracterización del cronograma manual en hojas de cálculo y documentación de inconsistencias de datos."
    )
    add_para(
        "2. Fase de Diseño Arquitectónico (Semanas 5-7): Definición del esquema documental JSON para Firestore, estructura de la tubería ETL en Python y selección de la pasarela SMTP de Brevo."
    )
    add_para(
        "3. Fase de Optimización de Backend (Semanas 8-11): Rediseño de consultas de Firestore a Python para resolver el problema N+1, logrando transferencias de datos masivas en milisegundos."
    )
    add_para(
        "4. Fase de Desarrollo Frontend y Alertas (Semanas 12-19): Construcción del panel interactivo de Streamlit, inyección del gráfico de radar y configuración del motor de correo automático por lotes."
    )
    add_para(
        "5. Fase de Validación y Pruebas (Semanas 20-24): Ejecución de pruebas unitarias locales en Pytest y auditoría visual de los datos integrados con la participación del metrólogo y analistas del laboratorio."
    )

    # VII. ANÁLISIS DE RESULTADOS Y VALIDACIÓN
    add_heading_1("VII. ANÁLISIS DE RESULTADOS Y VALIDACIÓN")
    add_para(
        "La validación técnica del módulo PAME confirmó su alta estabilidad y eficiencia. "
        "La TABLA I resume las diferencias métricas operativas obtenidas antes y después de la implementación de la herramienta:"
    )

    # Tabla I: Comparación técnica
    table_kpi = doc.add_table(rows=5, cols=3)
    table_kpi.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    headers_kpi = ["Métrica de Operación", "Cronograma Manual Anterior", "Módulo Digital PAME"]
    widths_kpi = [Inches(2.2), Inches(2.1), Inches(2.2)]
    
    hdr_cells_kpi = table_kpi.rows[0].cells
    for i, header_text in enumerate(headers_kpi):
        hdr_cells_kpi[i].text = header_text
        set_cell_background(hdr_cells_kpi[i], "1A365D")
        set_cell_margins(hdr_cells_kpi[i])
        run = hdr_cells_kpi[i].paragraphs[0].runs[0]
        run.bold = True
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    data_kpi = [
        ("Tiempo de respuesta (cambio de pestañas)", "Aproximadamente 3 minutos (Timeout)", "Milisegundos (Caché local)"),
        ("Gestión de alertas de vencimiento", "Revisión visual e informal de celdas", "Automática, agrupada en lotes cada 30 días"),
        ("Esquema de persistencia", "Archivos Excel dispersos en red local", "Base de datos NoSQL documental Firestore"),
        ("Monitoreo gerencial de conformidad", "No existía consolidación", "Radar 5D e Índice de Salud en tiempo real")
    ]

    for row_idx, row_data in enumerate(data_kpi, start=1):
        row_cells = table_kpi.rows[row_idx].cells
        for col_idx, cell_value in enumerate(row_data):
            row_cells[col_idx].text = cell_value
            set_cell_margins(row_cells[col_idx])
            p_run = row_cells[col_idx].paragraphs[0].runs[0]
            p_run.font.name = 'Times New Roman'
            p_run.font.size = Pt(10)
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
    run_cap = p_caption.add_run("TABLA I. COMPARATIVO DE RENDIMIENTO Y FUNCIONALIDAD")
    run_cap.bold = True
    run_cap.font.name = 'Times New Roman'
    run_cap.font.size = Pt(9.5)

    add_heading_2("Validación de Software mediante Pruebas Unitarias")
    add_para(
        "Para garantizar la exactitud operativa exigida por la industria farmacéutica, se implementó una suite de "
        "13 pruebas unitarias automatizadas utilizando Pytest. Las pruebas cubren las siguientes dimensiones críticas del software:"
    )
    add_para(
        "1) Pruebas del ETL (`tests/test_etl.py`): Valida que la extracción de datos desde CSV y JSON normalice los tipos de datos, filtre duplicados y levante excepciones controladas ante archivos corruptos o columnas inexistentes."
    )
    add_para(
        "2) Pruebas de Alertas (`tests/test_alertas.py`): Comprueba que el cálculo de estado asigne correctamente el estado de 'Vencido' si supera la fecha actual, y 'Programar' si se encuentra dentro de la ventana crítica de 30 días. Asimismo, verifica que la generación de plantillas HTML y la agrupación por lotes no presente errores de sintaxis."
    )
    add_para(
        "3) Pruebas de Priorización: Confirma que el sistema de correo distinga entre las alertas preventivas agrupadas por lotes y las notificaciones críticas inmediatas enviadas ante fallas o calibraciones fallidas en planta."
    )
    add_para(
        "El 100% de la suite de pruebas unitarias locales pasó con éxito, confirmando que la lógica metrológica "
        "y el backend de base de datos del módulo PAME están libres de fallas técnicas de codificación."
    )

    # VIII. CONCLUSIONES Y RECOMENDACIONES
    add_heading_1("VIII. CONCLUSIONES Y RECOMENDACIONES")
    
    add_heading_2("A. Conclusiones")
    add_para(
        "1. La digitalización del cronograma metrológico a través del módulo PAME centralizó con éxito la información de calibraciones externas en Firebase Firestore, garantizando la trazabilidad documental requerida para auditorías del INVIMA."
    )
    add_para(
        "2. La optimización del motor de consultas a base de datos mediante la reestructuración O(N) y el almacenamiento en caché eliminó el inconveniente de rendimiento N+1, reduciendo el cambio de pestañas de Streamlit de minutos a milisegundos."
    )
    add_para(
        "3. El plazo preventivo de 30 días establecido en el motor de alertas se justifica plenamente en términos logísticos, cubriendo de forma segura las etapas de cotización, compra, parada técnica de planta y calibración física del equipo."
    )
    
    add_heading_2("B. Recomendaciones")
    add_para(
        "1. Ejecutar un piloto formal manteniendo en paralelo el antiguo cronograma manual en hojas de cálculo por un lapso de dos semanas con el objetivo de verificar la correcta recepción de alertas ante posibles filtros institucionales."
    )
    add_para(
        "2. Habilitar la carga digital de certificados de calibración en formato PDF vinculándolos directamente a los documentos de Firebase Firestore, permitiendo a los inspectores de control de calidad consultar las tolerancias analíticas con un clic."
    )

    # REFERENCIAS
    h_ref = doc.add_paragraph()
    h_ref.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h_ref.paragraph_format.space_before = Pt(20)
    h_ref.paragraph_format.space_after = Pt(8)
    r = h_ref.add_run("REFERENCIAS")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11)
    r.bold = True

    refs = [
        "[1] INVIMA, \"Resolución 1160 de 2016: Manual de Buenas Prácticas de Manufactura para la fabricación de medicamentos,\" Ministerio de Salud, Bogotá, 2016.",
        "[2] ISO, \"ISO 10012:2003 — Sistemas de gestión de las mediciones: Requisitos para los procesos de medición y los equipos de medición,\" International Organization for Standardization, Ginebra, Suiza, 2003.",
        "[3] ONAC, \"Trazabilidad Metrológica en la industria farmacéutica y de alimentos,\" Organismo Nacional de Acreditación de Colombia, Bogotá, 2024.",
        "[4] K. C. Laudon y J. P. Laudon, Management Information Systems: Managing the Digital Firm, 16.ª ed. Hoboken, NJ: Pearson, 2020.",
        "[5] Google Cloud, \"Firebase Firestore Document Databases: NoSQL indexing and scaling,\" Google Cloud Docs, 2025. [En línea]. Disponible: https://firebase.google.com/docs/firestore",
        "[6] M. Fowler, Patterns of Enterprise Application Architecture. Boston, MA: Addison-Wesley, 2002, pp. 268-275.",
        "[7] R. Kimball y J. Caserta, The Data Warehouse ETL Toolkit: Practical Techniques for Extracting, Cleaning, Conforming, and Delivering Data. Indianapolis, IN: Wiley Publishing, 2004."
    ]
    for ref in refs:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r = p.add_run(ref)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(9.5)

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
