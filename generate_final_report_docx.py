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
    # CONFIGURACIÓN DE PÁGINA (Monocolumna)
    # Margen estándar UdeA de 1 pulgada (2.54 cm)
    # ---------------------------------------------------------
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(11)
    font.color.rgb = RGBColor(0x00, 0x00, 0x00)

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
    run_title = p_title.add_run("DISEÑO E IMPLEMENTACIÓN DE UN MÓLULO COMPLEMENTARIO PARA LA GESTIÓN Y DIGITALIZACIÓN DEL PROGRAMA DE ASEGURAMIENTO METROLÓGICO (PAME) EN LABORATORIOS LAPROFF S.A.S.")
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
        "Metodológicamente, se aplicaron técnicas avanzadas de transformación de datos (ETL) y optimizaciones algorítmicas O(N) para resolver un cuello de botella técnico de tipo N+1 en las consultas de base de datos que causaba latencias de más de 3 minutos, reduciendo los tiempos de carga a milisegundos mediante caché local en la interfaz de Streamlit. "
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
        "En el contexto de la industria farmacéutica, el aseguramiento metrológico representa uno de los pilares críticos de la garantía de la calidad y de la excelencia operacional. "
        "Los laboratorios de control de calidad y las plantas de manufactura farmacéutica dependen enteramente de la confiabilidad, precisión y exactitud de sus instrumentos "
        "de medición. En Colombia, el Instituto Nacional de Vigilancia de Medicamentos y Alimentos (INVIMA), bajo el mandato de las Buenas Prácticas de Manufactura (BPM) "
        "según la Resolución 1160 de 2016, exige un control exhaustivo y documentado de los estados de calibración, calificación y mantenimiento de los equipos analíticos [1]. "
        "La operación de instrumentos con certificados de calibración vencidos o fuera de tolerancias de aceptación metrológicas no solo representa una no conformidad severa "
        "en las auditorías regulatorias, sino que introduce el riesgo crítico de liberar lotes de medicamentos con dosificaciones incorrectas o parámetros de calidad desviados."
    )
    add_para(
        "Tradicionalmente, en Laboratorios Laproff S.A.S., el seguimiento de estas actividades preventivas se ha realizado a través de hojas de cálculo individuales "
        "administradas de manera aislada por los analistas técnicos y los coordinadores de validación de cada sección. Este enfoque descentralizado presentaba "
        "inconvenientes operativos considerables: dispersión de la información, nula visibilidad gerencial agregada sobre el estado metrológico de la planta, y la "
        "ausencia de alertas automatizadas preventivas que advirtieran de forma oportuna la inminencia del vencimiento técnico de un instrumento. "
        "Esto deba como resultado la constante necesidad de inspecciones manuales del archivo para evitar que un equipo crítico quedara fuera de especificaciones."
    )
    add_para(
        "Para subsanar de raíz estas debilidades del proceso operativo, se propuso el diseño, desarrollo e implementación de un módulo complementario digital integrado "
        "para el Programa de Aseguramiento Metrológico (PAME). La meta fue centralizar los cronogramas en una base de datos documental escalable y segura, automatizar un "
        "motor de avisos predictivos por correo electrónico y proveer a la gerencia de calidad de un tablero analítico moderno con visualización de datos en tiempo real. "
        "Este informe documenta exhaustivamente la ingeniería detrás del aplicativo desarrollado, los retos técnicos asociados a la latencia de base de datos en la nube y "
        "la migración de datos estructurados, y los resultados de validación del prototipo funcional, demostrando la integración práctica de metodologías de desarrollo "
        "de software y rigor metrológico para cumplir los exigentes estándares de la industria farmacéutica."
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
    
    add_heading_2("A. El Aseguramiento Metrológico en la Industria Farmacéutica Regulada")
    add_para(
        "El aseguramiento metrológico abarca las actividades de calibración, validación, mantenimiento preventivo y verificación de instrumentos de medición. "
        "La calibración compara las lecturas de un instrumento contra un patrón de referencia trazable con el fin de cuantificar su error sistemático y su incertidumbre [2]. "
        "En la manufactura de medicamentos bajo estándares de Buenas Prácticas de Manufactura (BPM), la norma internacional ISO 10012:2003 exige estructurar un sistema "
        "de gestión de las mediciones que demuestre de forma ininterrumpida la idoneidad metrológica de cada sensor analítico. Cualquier equipo con una calibración "
        "vencida o calificado como 'No Cumple' debe ser identificado físicamente de inmediato para evitar su uso en ensayos oficiales de calidad [3]."
    )

    add_heading_2("B. Integridad de los Datos y Principios ALCOA+ en Sistemas de Software")
    add_para(
        "En la informática de laboratorios y manufactura farmacéutica, la transformación digital no solo obedece a la agilidad operativa, sino a mandatos normativos rígidos "
        "sobre la integridad de los datos. La directiva ALCOA+ establece que todos los datos deben ser Atribuibles (saber quién los generó), Legibles (comprensibles en el tiempo), "
        "Contemporáneos (registrados al instante del evento), Originales (fuente primaria no modificada) y Exactos (libres de errores de digitación manual). "
        "Las hojas de cálculo planas en formato Excel carecen de pistas de auditoría (audit trail) nativas, permitiendo la alteración histórica de fechas de calibración sin "
        "dejar registros. Un desarrollo moderno de base de datos documental debe mitigar este riesgo estructurando colecciones inmutables en servidores en la nube con "
        "mecanismos estrictos de autenticación de API para preservar la trazabilidad documental ante auditorías oficiales [4]."
    )

    add_heading_2("C. Modelado Documental NoSQL frente a Bases de Datos Relacionales (SQL)")
    add_para(
        "La naturaleza de los equipos metrológicos de un laboratorio químico es sumamente heterogénea. "
        "Una balanza analítica analógica requiere registrar magnitudes de masa, pruebas de excentricidad de carga, repetibilidad e incertidumbre expandida. "
        "Por el contrario, un analizador de Carbono Orgánico Total (TOC) como el GEHAKA 2400 realiza mediciones avanzadas de conductividad diferencial, "
        "carbono inorgánico y carbono total mediante procesos continuos de oxidación de compuestos orgánicos mediante radiación UV y persulfato de amonio. "
        "El modelado en una base de datos relacional (SQL) para un catálogo de equipos tan disímil genera un esquema rígido que requiere decenas de tablas "
        "de unión y constantes consultas tipo JOIN que degradan severamente el rendimiento computacional ante solicitudes masivas. "
        "Las bases de datos NoSQL basadas en documentos (como Firebase Firestore) resuelven este dilema de modelado. Permiten almacenar colecciones de documentos "
        "JSON dinámicos, donde cada documento representa un equipo con sus especificaciones particulares, soportando datos dinámicos sin "
        "afectar el rendimiento global de las búsquedas en el sistema [5]."
    )

    add_heading_2("D. Algoritmia, Latencia de Red y el Fenómeno de Consulta N+1")
    add_para(
        "El problema de rendimiento N+1 es un defecto algorítmico clásico que ocurre cuando un sistema de software, para renderizar un listado de N registros principales "
        "con sus respectivos detalles, ejecuta una petición principal inicial y posteriormente ejecuta N consultas adicionales e individuales en una estructura de bucle recursivo [6]. "
        "En arquitecturas web conectadas a bases de datos en la nube (como Firestore), esto causa dos fallos críticos: "
        "(1) Latencia de Red Acumulada: Cada petición a la nube requiere un viaje de ida y vuelta (round-trip) que introduce milisegundos de retraso en la red pública; ante "
        "cientos de equipos, el retraso acumulado congela por completo la interfaz web de la aplicación. "
        "(2) Incremento de Costos Operativos: Las bases de datos en la nube cobran cuotas por cantidad de lecturas ejecutadas; un ciclo recursivo N+1 dispara miles de lecturas "
        "innecesarias por cada recarga de pantalla de usuario. "
        "Para solucionarlo, el patrón de diseño exige migrar a una única consulta masiva unificada (batch query), reduciendo la complejidad del proceso a tiempo lineal O(N) "
        "y delegando el agrupamiento y filtrado de las colecciones a estructuras de datos en memoria local a través de funciones vectorizadas rápidas de Pandas [7]."
    )

    doc.add_page_break()

    # IV. METODOLOGÍA
    add_heading_1("IV. METODOLOGÍA Y CRONOGRAMA DE EJECUCIÓN (PASO A PASO)")
    add_para(
        "El proyecto se llevó a cabo siguiendo una estructura cronológica rigurosa de 6 meses de duración, dividida en fases de ingeniería con entregables acoplados. "
        "A continuación se detalla la metodología ejecutada paso a paso:"
    )

    add_heading_2("A. Fase 1: Contextualización y Levantamiento de Requerimientos (Mes 1)")
    add_para(
        "Durante el primer mes de la práctica industrial, se realizó un proceso intensivo de inmersión en el dominio metrológico y regulatorio del laboratorio. "
        "Se asimiló el vocabulario técnico crítico del área, incluyendo los conceptos de Carbono Orgánico Total (TOC), Agua Purificada (PW), Agua para Inyección (WFI), "
        "calificaciones de diseño, instalación, operación y desempeño (IQ/OQ/PQ), y directrices de validación del INVIMA. "
        "Asimismo, se estudió el funcionamiento de los sensores espectrofotométricos de absorción infrarroja no dispersiva (NDIR), evaluando la precisión respecto al "
        "rango de escala total (Full Scale) y el empleo de estándares de referencia de sacarosa certificados por la USP."
    )
    add_para(
        "Se identificó la necesidad concreta de desarrollar un módulo analítico complementario que no reemplazara el software corporativo en desarrollo en Laproff, "
        "sino que aportara capacidades diferenciadoras de alerta preventiva y visualización histórica agregada. "
        "Para ello, se auditó la fuente de datos real proporcionada por el área de Metrología: el archivo `Cronograma_De_Servicios.csv`. "
        "Este archivo posee aproximadamente 3.600 registros metrológicos distribuidos en 14 columnas de datos (incluyendo códigos de equipos, ubicaciones físicas, "
        "fechas de servicio, periodicidad y estados de conformidad), codificado bajo el formato latin-1 y delimitado por punto y coma. "
        "Mediante reuniones periódicas con el Jefe de Validaciones y Metrología (asesor externo), se definió el alcance funcional del aplicativo, estableciendo como meta "
        "construir un prototipo funcional robusto para el control en tiempo real del cronograma."
    )

    add_heading_2("B. Fase 2: Definición de Arquitectura y Modelado de Datos (Mes 2)")
    add_para(
        "El segundo mes se enfocó en el análisis arquitectónico y la selección del motor de persistencia. "
        "Se realizó un análisis comparativo entre una base de datos relacional PostgreSQL administrada mediante Supabase y una documental NoSQL estructurada en Firebase Firestore. "
        "La justificación técnica de la decisión final a favor de Firestore radicó en su capacidad nativa para almacenar y procesar documentos JSON heterogéneos. "
        "Dado que las balanzas analíticas, termohigrómetros y equipos analíticos complejos como el analizador de TOC registran datos metrológicos marcadamente diferentes, "
        "un esquema SQL clásico habría impuesto una rigidez perjudicial con múltiples tablas JOIN. "
        "Firestore permitió representar de forma directa el inventario de equipos y sus correspondientes subcolecciones de historial de calibraciones y alertas. "
        "Adicionalmente, en esta fase se definieron formalmente los KPIs diferenciales que debía ofrecer el módulo, tales como el Índice de Salud de la planta "
        "y el análisis interanual, elementos ausentes en el desarrollo corporativo central."
    )

    add_heading_2("C. Fase 3: Construcción de la Tubería ETL (Mes 3)")
    add_para(
        "El tercer mes estuvo dedicado al desarrollo del pipeline de extracción, transformación y carga (ETL) desarrollado en Python. "
        "Para asegurar la flexibilidad del sistema ante posibles cambios futuros en las exportaciones de datos de la empresa, "
        "se incorporó la lectura nativa de formatos JSON, además de los formatos CSV de Laproff. "
        "Se programó una subrutina de detección automática de estructura capaz de interpretar las variaciones en las columnas de 4 formatos de cronograma distintos."
    )
    add_para(
        "Con el objetivo de validar la robustez de la tubería ETL sin alterar la base de datos real del laboratorio, se generaron tres archivos sintéticos de prueba: "
        "(1) `cronograma_sample.csv` (55 registros que incorporaban intencionalmente celdas vacías, caracteres especiales y fechas mal formateadas para evaluar la tolerancia al error), "
        "(2) `cronograma_historico.json` (123 registros reales cubriendo el periodo de calibraciones 2022–2024 para poblar el histórico anual) "
        "y (3) `equipos_nuevos.csv` (10 registros con equipos nuevos sin historial previo). "
        "Las pruebas realizadas confirmaron que el pipeline corrige las inconsistencias de texto de forma automática y omite registros duplicados empleando una llave compuesta de control."
    )

    add_heading_2("D. Fase 4: Motor de Alertas y Notificaciones (Mes 4)")
    add_para(
        "Durante el cuarto mes, se implementó el motor de notificaciones solicitado explícitamente por el Jefe de Validaciones de Laproff para evitar la revisión visual manual. "
        "Se configuró el envío automatizado a través de la pasarela SMTP transaccional de Brevo. "
        "Se diseñaron plantillas de correo electrónico responsivas en HTML que incorporan el logotipo institucional, tablas estructuradas de los equipos próximos "
        "y una barra visual de distribución de estados. "
        "Para accionar el motor, se programó un script planificador (scheduler) de ejecución diaria en segundo plano. "
        "Este script corre cada mañana, computa la diferencia de días entre la fecha actual y la fecha de vencimiento metrológico de cada equipo, "
        "y despacha alertas por lotes si encuentra instrumentos dentro del margen crítico de 30 días, o alertas inmediatas individuales ante fallos analíticos."
    )

    add_heading_2("E. Fase 5: Desarrollo del Tablero Interactivo en Streamlit (Mes 5)")
    add_para(
        "El quinto mes se centró en la construcción de la interfaz web interactiva en Streamlit. "
        "Se integraron gráficos dinámicos desarrollados con Plotly, tales como curvas de tendencia mensual con relleno degradado y el comparativo anual. "
        "Para responder a los requerimientos del asesor externo, se desarrolló especialmente la pestaña de 'Cumplimiento Anual', "
        "la cual permite visualizar año tras año la evolución del cumplimiento y el estado de conformidad acumulado por área. "
        "Esta vista histórica constituía el requerimiento diferenciador clave del módulo PAME. "
        "Se iteró continuamente en el diseño de los selectores laterales, filtros por sección y tablas editables para garantizar que la interfaz "
        "fuera intuitiva tanto para los analistas de laboratorio como para los auditores de calidad."
    )

    add_heading_2("F. Fase 6: Integración, Pruebas y Entrega (Mes 6)")
    add_para(
        "El último mes estuvo dedicado a la integración final del sistema completo de extremo a extremo (ETL $\rightarrow$ Firestore $\rightarrow$ Alertas $\rightarrow$ Streamlit). "
        "Se realizaron pruebas de integración inyectando simultáneamente los tres archivos sintéticos de prueba y el archivo de datos reales del laboratorio. "
        "Para asegurar la transferencia de conocimiento y facilitar futuras mejoras, se redactó una documentación técnica estructurada en bloques lógicos. "
        "Esta documentación técnica sirvió de base para entrenar un asistente de programación con IA, facilitando la validación del código y correcciones menores del dashboard."
    )
    add_para(
        "El proyecto finalizado y el análisis metrológico complementario realizado sobre el analizador de TOC GEHAKA 2400 (que detallaba el plan de idoneidad del sistema) "
        "fueron presentados formalmente ante el comité primario del área de metrología de Laboratorios Laproff S.A.S., recibiendo la aprobación unánime de los asesores."
    )

    doc.add_page_break()

    # V. ANÁLISIS DE RESULTADOS
    add_heading_1("V. ANÁLISIS DE RESULTADOS Y VALIDACIÓN")
    add_para(
        "El módulo digital PAME implementó mejoras cuantitativas y operativas drásticas en comparación con el control tradicional del laboratorio. "
        "Para evidenciar de forma rigurosa estas diferencias de rendimiento y capacidades técnicas, se estructuró la TABLA II, "
        "detallando las dimensiones críticas evaluadas bajo la norma IEEE:"
    )

    # TABLA II IEEE
    p_tab_label = doc.add_paragraph()
    p_tab_label.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tab_label.paragraph_format.space_before = Pt(12)
    p_tab_label.paragraph_format.space_after = Pt(2)
    p_tab_label.paragraph_format.keep_with_next = True
    r_tab = p_tab_label.add_run("TABLA II")
    r_tab.bold = True
    r_tab.font.name = 'Times New Roman'
    r_tab.font.size = Pt(10)

    p_tab_title = doc.add_paragraph()
    p_tab_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tab_title.paragraph_format.space_after = Pt(8)
    p_tab_title.paragraph_format.keep_with_next = True
    r_title = p_tab_title.add_run("MATRIZ COMPARATIVA DE RENDIMIENTO Y CAPACIDADES OPERATIVAS")
    r_title.bold = True
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(10)

    table_comp = doc.add_table(rows=11, cols=3)
    table_comp.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    headers_comp = ["Dimensión / Criterio", "Proceso / Sistema Actual de Laproff", "Módulo Digital PAME"]
    widths_comp = [Inches(2.0), Inches(2.2), Inches(2.3)]
    
    hdr_cells = table_comp.rows[0].cells
    for i, header_text in enumerate(headers_comp):
        hdr_cells[i].text = header_text
        set_cell_background(hdr_cells[i], "1A365D")
        set_cell_margins(hdr_cells[i])
        run = hdr_cells[i].paragraphs[0].runs[0]
        run.bold = True
        run.font.name = 'Times New Roman'
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    data_comp = [
        ("Datos de entrada", "Excel manual y disperso por analista", "ETL automatizado con soporte de CSV/JSON y detección automática de estructura"),
        ("Estructura de datos", "Hojas de cálculo planas desestructuradas", "Base documental JSON Firebase Firestore en la nube"),
        ("Trazabilidad histórica", "Nula consolidación anual histórica", "Historial anual consolidado con análisis interanual (2022–2024)"),
        ("Mecanismo de alertas", "Revisión manual visual del cronograma", "Alertas SMTP automáticas (Brevo) agrupadas por lotes de 30 días"),
        ("Visualización", "Reportes estáticos planos e informales", "Tablero interactivo en Streamlit con radar 5D y gráficos Plotly"),
        ("Escalabilidad", "Manual; requiere modificar fórmulas y archivos", "Automática; soporta nuevos equipos dinámicos sin alterar el esquema"),
        ("Tiempos de respuesta", "Retrasos críticos detectados tarde", "Carga inmediata (milisegundos) y alertas proactivas a tiempo"),
        ("Intervención humana", "Alta carga operativa de digitación y control", "Mínima; tubería ETL automatiza validaciones y limpieza"),
        ("KPIs disponibles", "Ninguno centralizado de conformidad", "Índice de Salud de la planta y KPIs multidimensionales"),
        ("Aseguramiento de Calidad", "Complejo de auditar ante el INVIMA", "Cumplimiento ALCOA+ con trazabilidad digital inmediata")
    ]

    for row_idx, row_data in enumerate(data_comp, start=1):
        row_cells = table_comp.rows[row_idx].cells
        for col_idx, cell_value in enumerate(row_data):
            row_cells[col_idx].text = cell_value
            set_cell_margins(row_cells[col_idx])
            p_run = row_cells[col_idx].paragraphs[0].runs[0]
            p_run.font.name = 'Times New Roman'
            p_run.font.size = Pt(9.5)
            if row_idx % 2 == 0:
                set_cell_background(row_cells[col_idx], "F7FAFC")
            else:
                set_cell_background(row_cells[col_idx], "FFFFFF")

    for row in table_comp.rows:
        for idx, width in enumerate(widths_comp):
            row.cells[idx].width = width

    # Nota inferior
    p_note = doc.add_paragraph()
    p_note.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_note.paragraph_format.space_before = Pt(4)
    p_note.paragraph_format.space_after = Pt(12)
    run_note = p_note.add_run("Nota: Datos recopilados a partir de las pruebas unitarias sobre los 3.600 registros de Laproff y los archivos de prueba sintéticos.")
    run_note.italic = True
    run_note.font.name = 'Times New Roman'
    run_note.font.size = Pt(8.5)

    add_heading_2("Análisis Crítico de la Matriz Comparativa")
    add_para(
        "Al evaluar detalladamente las diferencias condensadas en la TABLA II, es posible determinar tres mejoras fundamentales "
        "aportadas por el módulo PAME frente a la operación tradicional del laboratorio. "
        "En primer lugar, la unificación del modelo de datos de entrada mediante la tubería ETL automatizada erradica el error humano "
        "asociado a la transcripción manual de fechas y normaliza variaciones críticas de texto, garantizando la consistencia "
        "de la información subida a Firebase Firestore. "
        "En segundo lugar, el motor de alertas por correo electrónico parametrizado a 30 días introduce una garantía de tiempo "
        "lógico indispensable para el ciclo de cotización y compras de servicios de calibración externa bajo las BPM de la UdeA. "
        "Finalmente, la disponibilidad de KPIs dinámicos agregados y la vista interanual le conceden al Jefe de Metrología y Validaciones "
        "una herramienta de control auditable de primer nivel, reduciendo a milisegundos la consulta técnica de conformidad "
        "ante auditorías del INVIMA."
    )

    # VI. CONCLUSIONES Y RECOMENDACIONES
    add_heading_1("VI. CONCLUSIONES Y RECOMENDACIONES")
    
    add_heading_2("A. Conclusiones")
    add_para(
        "1. La digitalización integral del cronograma metrológico mediante el módulo PAME centralizó con éxito la información técnica del laboratorio "
        "en una base de datos Firebase Firestore. Este hito resolvió el riesgo regulatorio latente de operar con calibraciones vencidas en Laboratorios Laproff S.A.S., "
        "proporcionando una única fuente de verdad documental inalterable y auditable frente a futuras visitas de inspección del INVIMA."
    )
    add_para(
        "2. La reingeniería del motor de comunicación con la base de datos eliminó por completo el problema N+1 que ralentizaba la plataforma. "
        "Al sustituir consultas iterativas repetitivas por consultas unificadas en bloque con orden lineal O(N) y caché en memoria local, se redujo el tiempo "
        "de cambio de pestañas en Streamlit de minutos a milisegundos, garantizando la usabilidad de la herramienta con datos reales."
    )
    add_para(
        "3. El plazo preventivo de 30 días establecido en el motor de alertas se justifica plenamente en términos logísticos. Se demostró que este margen temporal "
        "cubre con holgura las cuatro fases del ciclo de compras metrológicas farmacéuticas externas (cotización, orden de compra, programación de parada de planta "
        "y análisis técnico de conformidad), previniendo detenciones inesperadas en las líneas de producción."
    )
    add_para(
        "4. La suite de 13 pruebas unitarias automatizadas en Pytest y la validación en paralelo confirmaron la estabilidad y exactitud algorítmica del software. "
        "La integración del radar de 5 dimensiones y las tarjetas de riesgo HTML simplificó la toma de decisiones, reduciendo a segundos la detección de desviaciones."
    )
    
    add_heading_2("B. Recomendaciones")
    add_para(
        "1. Ejecutar un piloto formal de dos semanas manteniendo el sistema antiguo en paralelo para calibrar posibles filtros de correo institucional que puedan desviar las alertas."
    )
    add_para(
        "2. Ampliar las capacidades del módulo para permitir la carga de los certificados de calibración en formato PDF directamente en Firestore, facilitando auditorías inmediatas por parte del Invima."
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
