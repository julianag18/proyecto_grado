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
        "Esto último obligaba al personal a realizar constantes inspecciones visuales manuales del cronograma general para evitar que un equipo quedara fuera de servicio "
        "o, peor aún, fuera utilizado en un análisis oficial de liberación de producto con su certificación técnica caducada."
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
        "El aseguramiento metrológico se define como el conjunto de operaciones requeridas para garantizar que los equipos de medición cumplan con las especificaciones "
        "necesarias para su uso previsto. En entornos regulados por agencias sanitarias (como el INVIMA o la FDA), cada instrumento analítico se somete a ciclos continuos "
        "de calibración y calificación (instalación IQ, operación OQ y desempeño PQ) para certificar su trazabilidad metrológica hacia patrones internacionales reconocidos [2]. "
        "De acuerdo con la norma internacional ISO 10012:2003, un sistema de control metrológico eficaz exige que el laboratorio farmacéutico defina y respete intervalos de "
        "calibración específicos para cada variable crítica y que documente formalmente las desviaciones de tolerancia permitidas. Si una medición excede las tolerancias "
        "definidas, el instrumento debe marcarse inmediatamente como fuera de especificación para evitar desviaciones en la manufactura de fármacos [3]."
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
        "JSON dinámicos, donde cada equipo contiene sus propios metadatos anidados específicos sin forzar a los demás instrumentos a compartir el mismo esquema rígido, "
        "optimizando la escalabilidad del sistema [5]."
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

    # IV. DECISIONES DE DISEÑO Y SELECCIÓN DE SOFTWARE
    add_heading_1("IV. DECISIONES DE DISEÑO Y SELECCIÓN DE SOFTWARE")
    add_para(
        "La arquitectura de software implementada se estructuró a partir de un riguroso análisis comparativo de tecnologías de desarrollo. "
        "En esta sección se detallan las justificaciones técnicas y los compromisos de ingeniería que sustentaron la elección de cada componente del ecosistema:"
    )

    add_heading_2("A. Lenguaje de Programación: Python y su ecosistema analítico")
    add_para(
        "Se seleccionó Python como lenguaje de programación principal del proyecto, superando la alternativa de lenguajes compilados como Java o C#. "
        "El factor determinante fue la disponibilidad y rendimiento de Pandas, la biblioteca estándar para el análisis y manipulación de datos tabulares, "
        "y de Pytest para estructurar pruebas unitarias avanzadas. "
        "En un proyecto metrológico centrado en la migración de archivos Excel dispersos y la automatización de notificaciones, "
        "Python nos permitió escribir código legible, fácil de mantener por el equipo de Laproff y con un tiempo de desarrollo sustancialmente menor."
    )

    add_heading_2("B. Firebase Firestore frente a Supabase y PostgreSQL")
    add_para(
        "Se evaluó implementar una base de datos relacional PostgreSQL con Supabase. "
        "Sin embargo, tras analizar el inventario metrológico real de la planta, se identificó que la variabilidad de campos por tipo de equipo "
        "(ej. balanzas con pruebas de linealidad, cromatógrafos con tiempos de retención y medidores de conductividad con constantes de celda) "
        "habría requerido una base relacional altamente normalizada con múltiples tablas de unión. "
        "Firebase Firestore fue seleccionado gracias a su flexibilidad NoSQL documental. Esto permitió a cada registro de equipo poseer un objeto JSON "
        "metrológico dinámico propio. "
        "Además, Firestore ofrece sincronización nativa en tiempo real y una latencia de escritura baja, idónea para sistemas que registran "
        "datos de calibración sobre la marcha desde diferentes áreas de la planta farmacéutica."
    )

    add_heading_2("C. Interfaz de Usuario: Streamlit frente a frameworks tradicionales")
    add_para(
        "La construcción de una aplicación web interactiva de manera tradicional (utilizando React, Angular o Vue en el frontend y Node.js o Flask en el backend) "
        "requiere semanas de desarrollo dedicadas a la creación de APIs REST, layouts web y la sincronización de estados. "
        "Se eligió Streamlit porque permite compilar e iterar rápidamente la interfaz web directamente en lenguaje Python, reduciendo a cero la latencia de "
        "desarrollo del frontend. "
        "Su integración transparente con Plotly facilitó la inyección de gráficos metrológicos sofisticados (radar, líneas, barras) "
        "y su capacidad de recarga de estados en caché local ayudó a resolver los problemas de rendimiento directamente en el backend de Python."
    )

    add_heading_2("D. Servicio de Correo SMTP y Plantillas Transaccionales: Brevo")
    add_para(
        "El motor de alertas requería una pasarela con altos estándares de entregabilidad. "
        "El uso de cuentas SMTP estándar de consumo masivo (Gmail corporativo) presentaba severos límites de envío y bloqueos por sospecha de spam "
        "cuando se enviaban múltiples correos consecutivos a los analistas. "
        "Se implementó Brevo (antiguo Sendinblue) como pasarela transaccional. "
        "Brevo nos permitió diseñar plantillas HTML interactivas con estilos responsivos y barras de distribución visual, ofreciendo logs "
        "detallados de entrega y asegurando que las alertas de vencimiento de 30 días arriben a la bandeja de entrada del metrólogo sin demoras."
    )

    doc.add_page_break()

    # V. IMPLEMENTACIÓN PASO A PASO Y RESOLUCIÓN DE INCONVENIENTES
    add_heading_1("V. IMPLEMENTACIÓN PASO A PASO Y RESOLUCIÓN DE INCONVENIENTES")
    add_para(
        "El desarrollo del módulo digital PAME se ejecutó de forma incremental a lo largo de las 24 semanas de la práctica. "
        "A continuación se presenta el flujo detallado de la implementación, documentando los principales inconvenientes técnicos "
        "y las respectivas estrategias de ingeniería aplicadas para solucionarlos:"
    )

    add_heading_2("A. Hito 1: Construcción y Depuración de la Tubería ETL")
    add_para(
        "La fase inicial del proyecto estuvo enfocada en consolidar y normalizar el historial disperso de calibraciones. "
        "Se programó un script de automatización ETL en Python (`src/etl/pipeline.py`) utilizando la biblioteca Pandas. "
        "El script extrae las tablas desde archivos Excel y CSV, ejecuta rutinas de transformación de tipos y las carga a Firestore."
    )
    add_para(
        "1. Inconveniente Detectado: Se halló una extrema inconsistencia en los nombres de las ubicaciones y equipos digitados manualmente por los operarios. "
        "Ubicaciones como 'Control de Calidad' aparecían registradas de más de 12 formas diferentes, lo que imposibilitaba agrupar correctamente los datos analíticos "
        "o calcular estadísticas por área. Asimismo, múltiples celdas de fechas críticas estaban vacías o contenían valores inválidos de texto."
    )
    add_para(
        "2. Solución y Mejoras Aplicadas: Se integró en la fase de transformación un diccionario estandarizado de mapeo de texto que unifica de forma automática "
        "la nomenclatura. Se diseñó una función de validación de fechas que evalúa las cadenas de texto, descartando los registros corruptos y escribiendo logs "
        "de auditoría detallados. Para evitar la duplicidad de registros, se configuró un validador que genera una llave única compuesta (código_equipo + fecha_servicio), "
        "bloqueando la subida a base de datos de registros repetidos."
    )

    add_heading_2("B. Hito 2: Optimización de Base de Datos y Resolución del Problema N+1")
    add_para(
        "Tras migrar los datos iniciales del laboratorio, al renderizar el dashboard interactivo de Streamlit, la interfaz del usuario se congelaba "
        "por más de 3 minutos, arrojando errores de timeout. Al auditar la comunicación del backend, se descubrió la presencia del fenómeno de consulta N+1. "
        "La aplicación leía una lista inicial de N equipos y, dentro de un bucle iterativo recursivo, realizaba una nueva petición a Firestore "
        "para extraer el historial de calibraciones individuales de cada instrumento."
    )
    add_para(
        "1. Inconveniente Detectado: Con un volumen real de 200 equipos analíticos, el aplicativo ejecutaba 201 peticiones consecutivas a Firestore "
        "por cada usuario en pantalla, saturando el ancho de banda y consumiendo el límite de cuotas de lectura gratuitas del servicio en la nube."
    )
    add_para(
        "2. Solución y Mejoras Aplicadas: Se reescribió el backend en `src/database/equipos_repo.py`. Se eliminó el bucle recursivo. "
        "Se programó una única consulta en bloque masivo que descarga la colección completa de calibraciones en una sola petición. "
        "Posteriormente, la unión de datos se realiza en memoria local empleando agrupamientos vectorizados de Pandas, logrando una respuesta lineal O(N) "
        "en milisegundos. Para optimizar aún más el rendimiento, se decoraron las funciones de carga con `@st.cache_data`, inmovilizando la consulta "
        "a menos de que el usuario suba un nuevo archivo de migración o edite el cronograma."
    )

    add_heading_2("C. Hito 3: Lógica Metrológica del Motor de Alertas y Justificación Logística")
    add_para(
        "Se implementó un motor cron en segundo plano que valida diariamente el cronograma metrológico de Laproff. "
        "Se parametrizó una regla de negocio donde las notificaciones preventivas por correo electrónico se disparan con un mes (30 días) de anticipación. "
        "Esta ventana temporal se justificó operacionalmente debido al ciclo de abastecimiento de compras metrológicas externas en la industria farmacéutica:"
    )
    
    cycle_steps = [
        "Semana 1: Selección del proveedor acreditado por el ONAC específico para el instrumento, envío de fichas y solicitud de cotizaciones formales de calibración.",
        "Semana 2: Trámite del presupuesto con el área financiera de Laproff, aprobación del gasto y generación de la orden de compra oficial de servicio externo.",
        "Semana 3: Coordinación de la visita física del técnico metrólogo en planta y programación de la parada técnica del equipo de manufactura para evitar interferir con las campañas activas de producción de medicamentos.",
        "Semana 4: Ejecución de la calibración, emisión del certificado metrológico impreso/digital, análisis de desviación contra tolerancias de la farmacopea y verificación final de la conformidad por el Jefe de Validaciones y Metrología."
    ]
    for step in cycle_steps:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(4)
        p.add_run(step)
        
    add_para(
        "1. Inconveniente Detectado: Enviar un correo electrónico independiente por cada equipo vencido saturaba la bandeja del metrólogo jefe. "
        "Por el contrario, si un equipo de alta criticidad para la producción farmacéutica fallaba metrológicamente y se registraba como 'No Cumple', "
        "esperar al reporte del final del día para notificarlo ponía en grave riesgo la conformidad de los lotes de medicamentos en proceso de envasado."
    )
    add_para(
        "2. Solución y Mejoras Aplicadas: Se programó una regla de agrupación por lotes. El motor cron recopila las alertas preventivas del día "
        "y genera un reporte diario único estructurado en HTML con la lista consolidada de los instrumentos. "
        "Sin embargo, si se registra un estado metrológico crítico ('No Cumple' o 'Vencido en Uso'), el motor de notificaciones dispara "
        "una alerta inmediata e independiente al supervisor técnico del área para suspender la operación del equipo de inmediato."
    )

    add_heading_2("D. Hito 4: Visualización Ejecutiva y KPIs en Tiempo Real")
    add_para(
        "Para permitir auditorías ejecutivas rápidas, se rediseñó visualmente la interfaz del panel de control de Streamlit. "
        "Se integró un gráfico de radar (araña) interactivo en la pestaña principal, permitiendo evaluar la madurez metrológica de cada sección. "
        "El radar pondera 5 métricas críticas de 0 a 100%: (1) Vigencia: Porcentaje de equipos con calibración al día. "
        "(2) Conformidad: Porcentaje de calibraciones que cumplen los límites de tolerancia de manufactura. "
        "(3) Oportunidad: Equipos libres de vencimiento normativo inmediato. "
        "(4) Actualidad: Porcentaje de calibraciones realizadas hace menos de un año. "
        "(5) Formalización: Equipos con proveedor y contrato técnico vigente asignado en la base de datos."
    )

    # VI. METODOLOGÍA
    add_heading_1("VI. METODOLOGÍA")
    add_para(
        "La metodología de la práctica se enmarcó en un enfoque aplicado de tipo mixto, estructurado en 5 fases a lo largo del periodo de 24 semanas. "
        "La fase cuantitativa midió variables del sistema como tiempos de respuesta (segundos) y calidad de datos (porcentaje de duplicados omitidos). "
        "La fase cualitativa abarcó el levantamiento de requisitos operativos mediante entrevistas directas con el metrólogo de Laproff "
        "y el diseño de las reglas lógicas del negocio farmacéutico."
    )

    # VII. ANÁLISIS DE RESULTADOS Y VALIDACIÓN
    add_heading_1("VII. ANÁLISIS DE RESULTADOS Y VALIDACIÓN")
    add_para(
        "La validación técnica del módulo PAME arrojó excelentes resultados de rendimiento e integridad. "
        "La TABLA I resume las diferencias cuantitativas entre el proceso manual heredado y el módulo digital desarrollado:"
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
        "3. La ventana preventiva de alertas automáticas establecida en 30 días demostró ser operacionalmente óptima. Se validó que este margen temporal cubre "
        "con holgura las cuatro fases del ciclo de compras metrológicas farmacéuticas externas (cotización, orden de compra, programación de parada de planta "
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
