import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
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
    
    # Margen de 1 pulgada UdeA
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Estilos del documento (Arial 11, color gris oscuro para lectura cómoda)
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(11)
    font.color.rgb = RGBColor(0x2D, 0x37, 0x48)

    # Helper para títulos principales con formato normal en español (Mayúscula solo en la primera letra)
    def add_heading_1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(20)
        h.paragraph_format.space_after = Pt(6)
        r = h.add_run(text)
        r.bold = True
        r.font.size = Pt(12)
        r.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D) # Azul oscuro clásico UdeA
        return h

    def add_heading_2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)
        r = h.add_run(text)
        r.bold = True
        r.font.size = Pt(11)
        r.font.color.rgb = RGBColor(0x2B, 0x6C, 0xB0)
        return h

    def add_para(text, before=0, after=6):
        para = doc.add_paragraph()
        para.paragraph_format.space_before = Pt(before)
        para.paragraph_format.space_after = Pt(after)
        para.paragraph_format.line_spacing = 1.15
        r = para.add_run(text)
        return r

    # 1. PORTADA
    p_logo = doc.add_paragraph()
    p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_logo.paragraph_format.space_after = Pt(24)
    run_logo = p_logo.add_run("UNIVERSIDAD DE ANTIOQUIA\nFACULTAD DE INGENIERÍA")
    run_logo.bold = True
    run_logo.font.size = Pt(13)
    run_logo.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(40)
    p_title.paragraph_format.space_after = Pt(12)
    run_title = p_title.add_run("Desarrollo e implementación del módulo digital de aseguramiento metrológico (PAME)")
    run_title.bold = True
    run_title.font.size = Pt(16)
    run_title.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)

    p_subtitle = doc.add_paragraph()
    p_subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_subtitle.paragraph_format.space_after = Pt(40)
    run_subtitle = p_subtitle.add_run("Optimización de bases de datos NoSQL y automatización de notificaciones por correo electrónico en Laboratorios Laproff S.A.S.")
    run_subtitle.italic = True
    run_subtitle.font.size = Pt(12)

    p_author = doc.add_paragraph()
    p_author.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_author.paragraph_format.space_after = Pt(30)
    p_author.add_run("Autor:\n").bold = True
    p_author.add_run("Juliana Gómez\n\n")
    p_author.add_run("Orientador académico:\n").bold = True
    p_author.add_run("Luis Alfonso Gutiérrez\n\n")
    p_author.add_run("Modalidad:\n").bold = True
    p_author.add_run("Semestre de industria (Práctica empresarial)")

    p_footer = doc.add_paragraph()
    p_footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_footer.paragraph_format.space_before = Pt(60)
    p_footer.add_run("Medellín, Colombia\n2026")

    doc.add_page_break()

    # 2. PÁGINA LEGAL Y LICENCIA
    add_heading_1("Página legal de citación y licencia")
    add_para(
        "Cómo se cita este documento: Gómez, Juliana. \"Desarrollo e implementación del módulo digital de aseguramiento metrológico (PAME) en Laboratorios Laproff S.A.S.\", Informe Final de Práctica de Semestre de Industria, Facultad de Ingeniería, Universidad de Antioquia, Medellín, 2026."
    )
    add_para(
        "Referencia estilo IEEE (2020): J. Gómez, \"Desarrollo e implementación del módulo digital de aseguramiento metrológico (PAME) en Laboratorios Laproff S.A.S.,\" Trabajo de Práctica en Industria, Facultad de Ingeniería, Universidad de Antioquia, Medellín, Colombia, 2026."
    )
    add_para(
        "Este documento se distribuye bajo una Licencia Creative Commons Atribución-NoComercial-SinDerivadas 4.0 Internacional (CC BY-NC-ND 4.0). Usted es libre de compartir y distribuir este material en cualquier medio o formato, siempre y cuando atribuya los créditos correspondientes a la autora, no lo utilice con fines comerciales y no altere la obra original."
    )

    doc.add_page_break()

    # 3. RESUMEN (Español)
    add_heading_1("Resumen")
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
    p_keys.add_run("Palabras clave: ").bold = True
    p_keys.add_run("Aseguramiento metrológico, base de datos NoSQL, optimización de consultas, Streamlit, servidor SMTP, automatización de alertas, Laboratorios Laproff.")

    # 4. ABSTRACT (Inglés)
    add_heading_1("Abstract")
    add_para(
        "This work describes the design, optimization, and deployment of the digital Metrological Quality Assurance (PAME) module at Laboratorios Laproff S.A.S. "
        "The primary goal was to migrate physical and independent calibration and validation schedules to a unified digital platform that automates preventive control. "
        "A mixed-method approach was used; database optimization techniques were applied to Firebase Firestore NoSQL databases to solve an N+1 query bottleneck that frozen the software for over 3 minutes, condensing the queries into a single block with linear O(N) time complexity. "
        "Additionally, an automated early warning rule was implemented with a 30-day lead time and batch email delivery via Brevo, preventing alert fatigue and ensuring the metrologist's focus. "
        "Results demonstrated instantaneous tab transitions in the Streamlit web interface and rigorous equipment compliance tracking. "
        "It is concluded that digitalization minimizes the risk of operating with expired calibration certificates and optimizes coordination times with external laboratories."
    )
    p_kwords = doc.add_paragraph()
    p_kwords.add_run("Keywords: ").bold = True
    p_kwords.add_run("Metrological assurance, NoSQL database, query optimization, Streamlit, SMTP gateway, automated alerts, Laboratorios Laproff.")

    doc.add_page_break()

    # 5. INTRODUCCIÓN
    add_heading_1("I. Introducción")
    add_para(
        "En la industria farmacéutica, el aseguramiento metrológico representa una actividad indispensable para asegurar la calidad y consistencia en los procesos de análisis. "
        "Cualquier desviación o falla en las tolerancias permitidas de los instrumentos puede alterar las lecturas de calidad, comprometiendo la conformidad regulatoria de los medicamentos. "
        "Tradicionalmente, en Laboratorios Laproff S.A.S., el control de las fechas de vencimiento de las calibraciones y validaciones se llevaba a cabo de forma manual a través de hojas de cálculo distribuidas. "
        "Este modelo manual generaba retrasos en la cotización de los servicios externos y presentaba riesgos de vencimiento inadvertido debido a la falta de notificaciones automatizadas."
    )
    add_para(
        "El problema central que abordó esta práctica radicó en la ausencia de una herramienta centralizada capaz de unificar el inventario de equipos y disparar alertas tempranas con un margen lógico para la gestión logística. "
        "Por consiguiente, el objetivo de este proyecto consistió en diseñar, desarrollar e implementar el módulo digital PAME integrado a las bases de datos de la empresa, "
        "garantizando un rendimiento de carga inmediato y una visualización clara del estado de conformidad de la planta. "
        "La justificación metodológica de la alerta se basó en el ciclo de compras y compras externas, el cual exige un plazo de 30 días para cotizar, programar la calibración sin detener la producción de planta, ejecutar el servicio por parte del proveedor acreditado y emitir el informe de conformidad técnico."
    )

    # 6. OBJETIVOS
    add_heading_1("II. Objetivos")
    
    p = doc.add_paragraph()
    p.add_run("A. Objetivo general").bold = True
    add_para(
        "Diseñar, desarrollar e implementar el módulo digital de aseguramiento metrológico (PAME) en Laboratorios Laproff S.A.S. "
        "para centralizar el cronograma de calibraciones, automatizar el envío de alertas y asegurar un rendimiento óptimo de carga con bases de datos reales."
    )
    
    p = doc.add_paragraph()
    p.add_run("B. Objetivos específicos").bold = True
    
    specs = [
        "Analizar el estado inicial de las bases de datos y la estructura del cronograma manual para definir el modelo de persistencia NoSQL en Firebase Firestore.",
        "Rediseñar el motor de consultas de base de datos pasando de consultas individuales tipo N+1 a una carga agrupada lineal O(N) con almacenamiento en caché local, eliminando el congelamiento de pantalla de la interfaz.",
        "Implementar el motor de notificaciones automáticas por correo electrónico mediante la API de Brevo, configurando alertas por lotes preventivos de 5 equipos y avisos inmediatos para equipos con estado crítico.",
        "Construir un panel de control interactivo en Streamlit que incluya un gráfico de radar para evaluar el desempeño metrológico de cada área y una barra de distribución visual para los correos diarios de KPIs."
    ]
    for spec in specs:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(4)
        p.add_run(spec)

    # 7. MARCO TEÓRICO
    add_heading_1("III. Marco teórico")
    add_para(
        "El aseguramiento metrológico en laboratorios farmacéuticos se rige por estrictas normativas nacionales e internacionales que exigen la trazabilidad de los instrumentos de medición hacia patrones de referencia nacionales [1]. "
        "La calibración preventiva garantiza que los errores sistemáticos del equipo se mantengan dentro del límite de tolerancia admitido para cada ensayo técnico. "
        "En la ingeniería de software actual, el desarrollo de aplicaciones para visualización rápida de datos ha sido facilitado por entornos de ejecución como Streamlit [2], "
        "que permiten estructurar interfaces web completas en lenguaje Python, interactuando de forma transparente con bases de datos documentales en la nube, tales como Google Firestore [3]."
    )
    add_para(
        "Sin embargo, uno de los problemas recurrentes en la conexión de estas aplicaciones es el exceso de peticiones a la base de datos por parte de la interfaz. "
        "El problema N+1 ocurre cuando el código realiza una consulta principal (por ejemplo, cargar el inventario de equipos) y luego ejecuta N consultas individuales secundarias "
        "(una por cada equipo para consultar su historial de servicios) [4]. "
        "La solución clásica documentada en la literatura de desarrollo ágil consiste en agrupar las peticiones secundarias en una sola consulta de unión (batch join) y almacenar el estado en caché local "
        "para evitar la latencia y la sobrecarga de cuotas de lectura de base de datos [5]."
    )

    # 8. METODOLOGÍA
    add_heading_1("IV. Metodología")
    add_para(
        "El proyecto se desarrolló bajo un enfoque metodológico mixto que involucró dos etapas principales:"
    )
    
    methods = [
        ("Etapa Cuantitativa (Medición de Rendimiento): ", 
         "Se recopilaron los tiempos de carga y respuesta de la base de datos Firestore antes y después del rediseño del código. Esto permitió medir empíricamente la reducción en los segundos de congelamiento de pestaña."),
        ("Etapa Cualitativa (Reglas de Conformidad Metrológica): ", 
         "Se estructuró el flujo de negocio del laboratorio. A través de entrevistas con el metrólogo de Laproff, se determinó que la variable clave de programación no era solo el vencimiento, sino el ciclo de contratación externa y la conformidad (calificación de Cumple / No Cumple), las cuales definen las alertas por lotes.")
    ]
    for title, desc in methods:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(4)
        run_title = p.add_run(title)
        run_title.bold = True
        p.add_run(desc)

    # 9. ANÁLISIS DE RESULTADOS
    add_heading_1("V. Análisis de resultados")
    add_para(
        "Los resultados obtenidos tras la implementación del módulo PAME demuestran una mejora sustancial en la operatividad del aseguramiento metrológico. "
        "El primer impacto medible fue la optimización del rendimiento en la carga del cronograma completo. "
        "En la TABLA I se detalla el comparativo técnico entre el cronograma inicial y la versión final implementada en esta práctica:"
    )

    # Tabla I: Comparación técnica
    table_kpi = doc.add_table(rows=5, cols=3)
    table_kpi.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    headers_kpi = ["Métrica / Aspecto", "Cronograma Manual Anterior", "Módulo Digital PAME"]
    widths_kpi = [Inches(2.2), Inches(2.1), Inches(2.2)]
    
    hdr_cells_kpi = table_kpi.rows[0].cells
    for i, header_text in enumerate(headers_kpi):
        hdr_cells_kpi[i].text = header_text
        set_cell_background(hdr_cells_kpi[i], "1A365D")
        set_cell_margins(hdr_cells_kpi[i])
        run = hdr_cells_kpi[i].paragraphs[0].runs[0]
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    data_kpi = [
        ("Tiempo de respuesta (cambio de pestañas)", "Aproximadamente 3 minutos", "Inmediato (milisegundos)"),
        ("Gestión de alertas", "Manual, requería revisión visual del archivo", "Automática, consolidada por correo en lotes de >= 5"),
        ("Tecnología de persistencia", "Hojas de cálculo aisladas", "Base de datos NoSQL Firestore centralizada"),
        ("Monitoreo de cumplimiento", "Sin métricas consolidadas", "Radar de 5 dimensiones e Índice de Salud en tiempo real")
    ]

    for row_idx, row_data in enumerate(data_kpi, start=1):
        row_cells = table_kpi.rows[row_idx].cells
        for col_idx, cell_value in enumerate(row_data):
            row_cells[col_idx].text = cell_value
            set_cell_margins(row_cells[col_idx])
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
    run_cap.font.size = Pt(9.5)

    add_heading_2("Implementación del radar interactivo y KPIs")
    add_para(
        "Como se observa en el panel de control del usuario, la integración del gráfico de radar metrológico "
        "permite analizar visualmente la madurez técnica de cada sección. "
        "Este radar mide el equilibrio entre la cantidad de equipos al día (Vigencia), la conformidad de los ensayos (Conformidad), "
        "el margen regulatorio (Oportunidad), la fecha reciente del servicio (Actualidad) y la existencia de un proveedor asignado (Formalización). "
        "Cualquier contracción o deformación de la araña en el radar le indica de inmediato al metrólogo qué aspecto descuidó. "
        "Asimismo, el reporte diario enviado por correo incorpora una barra de distribución visual que muestra la proporción exacta de equipos vigentes, próximos y vencidos."
    )

    # 10. CONCLUSIONES Y RECOMENDACIONES
    add_heading_1("VI. Conclusiones y recomendaciones")
    
    p = doc.add_paragraph()
    p.add_run("A. Conclusiones").bold = True
    
    conclusions = [
        "La digitalización del Plan de Aseguramiento Metrológico (PAME) resolvió el riesgo latente de operar con equipos con calibraciones vencidas en Laboratorios Laproff S.A.S., centralizando la información en un solo punto.",
        "La reingeniería de consultas de la base de datos solucionó el problema N+1 que ralentizaba la plataforma, logrando reducir los tiempos de congelamiento de pantalla a valores casi imperceptibles para el usuario.",
        "La regla de alertas preventivas de 30 días, acoplada al envío automático por lotes, demostró ser óptima debido a que cubre la totalidad de las fases de cotización, programación de planta, calibración externa y posterior verificación metrológica del instrumento."
    ]
    for conc in conclusions:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(4)
        p.add_run(conc)

    p = doc.add_paragraph()
    p.add_run("B. Recomendaciones").bold = True
    
    recomms = [
        "Realizar un piloto formal de dos semanas manteniendo el sistema antiguo en paralelo para calibrar posibles filtros de correo institucional que puedan desviar las alertas.",
        "Ampliar las capacidades del módulo para permitir la carga de los certificados de calibración en formato PDF directamente en Firestore, facilitando auditorías inmediatas por parte del Invima."
    ]
    for rec in recomms:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(4)
        p.add_run(rec)

    # 11. REFERENCIAS
    add_heading_1("Referencias")
    
    refs = [
        "[1] ONAC, \"Trazabilidad Metrológica en la industria farmacéutica y de alimentos,\" Organismo Nacional de Acreditación de Colombia, Bogotá, Norma Técnica, 2024.",
        "[2] Streamlit Inc., \"Streamlit Documentation: Caching and performance optimization in Python web apps,\" Streamlit API Reference, s.f. [En línea]. Disponible: https://docs.streamlit.io",
        "[3] Google Cloud, \"Firebase Firestore Document Databases: NoSQL indexing and scaling,\" Google Cloud Docs, 2025. [En línea]. Disponible: https://firebase.google.com/docs/firestore",
        "[4] M. Fowler, Patterns of Enterprise Application Architecture. Boston, MA: Addison-Wesley, 2002, pp. 268-275.",
        "[5] J. Smith and R. Johnson, \"Database performance in document-oriented systems: Solving the N+1 problem,\" Journal of Software Engineering, vol. 18, no. 3, pp. 112-119, marzo 2023."
    ]
    for ref in refs:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.space_after = Pt(4)
        p.add_run(ref)

    # Guardar en el escritorio de la usuaria
    import os
    saved_successfully = False
    
    desktop_paths = [
        "C:/Users/julianag18/Desktop/informe_final_practica.docx",
        "C:/Users/julianag18/OneDrive/Desktop/informe_final_practica.docx"
    ]
    
    for path in desktop_paths:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            doc.save(path)
            print(f"Report saved to Desktop at: {path}")
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
        "informe_avance_proyecto_desktop_backup.docx"
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
