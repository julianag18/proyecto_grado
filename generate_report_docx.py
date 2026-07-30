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

def create_report():
    doc = docx.Document()
    
    # Page setup
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Base Style
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(11)
    font.color.rgb = RGBColor(0x33, 0x41, 0x55)

    # Title
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run("INFORME DE AVANCE PARCIAL:\nDIGITALIZACIÓN Y OPTIMIZACIÓN DEL MÓDULO METROLÓGICO (PAME)")
    title_run.bold = True
    title_run.font.size = Pt(16)
    title_run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    
    # Metadata
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.add_run("Proyecto de Grado\n").bold = True
    meta.add_run("Autor: ").bold = True
    meta.add_run("Juliana Gómez\n")
    meta.add_run("Fecha: ").bold = True
    meta.add_run("29 de Julio de 2026\n")
    meta.add_run("Destinatario: ").bold = True
    meta.add_run("Asesor Interno del Proyecto de Grado / Profesor de Universidad\n")
    
    # Divider
    p = doc.add_paragraph()
    p.add_run("―" * 45).font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Heading 1 helper
    def add_heading_1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(6)
        r = h.add_run(text)
        r.bold = True
        r.font.size = Pt(14)
        r.font.color.rgb = RGBColor(0x0F, 0x76, 0x6E) # Teal color matching PAME theme
        return h

    # Paragraph helper
    def add_para(text, before=0, after=6):
        para = doc.add_paragraph()
        para.paragraph_format.space_before = Pt(before)
        para.paragraph_format.space_after = Pt(after)
        para.paragraph_format.line_spacing = 1.15
        r = para.add_run(text)
        return r

    # Section 1
    add_heading_1("1. Resumen Ejecutivo")
    add_para(
        "Este informe presenta el estado de avance actual del desarrollo e implementación del módulo de "
        "Aseguramiento Metrológico Digital (PAME) para Laboratorios Laproff S.A.S. Durante las últimas semanas, "
        "el proyecto ha transitado de una fase preliminar con cuellos de botella técnicos a un prototipo completamente "
        "funcional, optimizado para grandes bases de datos e integrado con sistemas de despacho automático de notificaciones. "
        "Este documento sirve como insumo de cara a la revisión parcial previa a la redacción definitiva del documento de "
        "tesis y a la validación final del sistema."
    )

    # Section 2
    add_heading_1("2. Comparativo de Estado: Objetivos Iniciales vs. Avances Logrados")
    add_para(
        "A continuación se detalla el progreso técnico y funcional comparando el punto de partida con los hitos "
        "alcanzados recientemente en la optimización del backend y la integración de alertas:"
    )

    # Table 1: Progress
    table = doc.add_table(rows=5, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    headers = ["Área del Proyecto", "Estado Inicial", "Avance Implementado y Funcional"]
    col_widths = [Inches(1.8), Inches(2.2), Inches(2.5)]
    
    # Format Headers
    hdr_cells = table.rows[0].cells
    for i, header_text in enumerate(headers):
        hdr_cells[i].text = header_text
        set_cell_background(hdr_cells[i], "0F766E") # Teal header
        set_cell_margins(hdr_cells[i])
        run = hdr_cells[i].paragraphs[0].runs[0]
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        
    data = [
        (
            "Rendimiento e Integridad",
            "El cambio entre pestañas del aplicativo tardaba hasta 3 minutos tras cargar bases de datos reales más pesadas (debido a consultas recursivas N+1 en la base de datos).",
            "Optimización del 1000% (tiempo O(N) lineal): Rediseño del motor de consultas de base de datos para agrupar servicios en memoria y almacenamiento en caché inteligente. La transición entre pestañas ahora es instantánea (milisegundos) y soporta bases de datos de gran volumen."
        ),
        (
            "Notificaciones por Correo",
            "Fallas de remitente inválido y desconexión con el servidor SMTP de Brevo. No se recibían alertas.",
            "Sincronización Exitosa: Configuración del canal de retransmisión SMTP cifrado con Brevo. Despacho probado y funcional hacia el correo objetivo (juli3213@gmail.com)."
        ),
        (
            "Automatización de Alertas",
            "Inexistente. Solo existía la opción de consulta visual o descarga del cronograma en Excel.",
            "Lógica de Alertas Automáticas: Creación de un servicio en segundo plano que evalúa el inventario a diario y envía un correo consolidado de alertas cuando se acumula un lote de >= 5 equipos próximos a vencer. Si un equipo es crítico (<15 días restantes), el sistema evade la regla del lote y envía una alerta inmediata."
        ),
        (
            "Reportes y Cuadro de Mando",
            "Visualizaciones estándar sin KPIs consolidados.",
            "Dashboard de KPIs Enriquecido: Implementación de un Índice de Salud Metrológica ejecutivo, tasas de conformidad del cronograma y un reporte diario automático de KPIs enviado por correo con barra de distribución gráfica nativa HTML/CSS."
        )
    ]

    for row_idx, row_data in enumerate(data, start=1):
        row_cells = table.rows[row_idx].cells
        for col_idx, cell_value in enumerate(row_data):
            row_cells[col_idx].text = cell_value
            set_cell_margins(row_cells[col_idx])
            # Subtle alternate shading
            if row_idx % 2 == 0:
                set_cell_background(row_cells[col_idx], "F1F5F9")
            else:
                set_cell_background(row_cells[col_idx], "FFFFFF")

    # Set column widths
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width

    # Section 3
    add_heading_1("3. Justificación de Decisiones Metrológicas")
    
    p = doc.add_paragraph()
    r = p.add_run("Regla de Anticipación de 1 Mes (30 días) para Alertas Automáticas")
    r.bold = True
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    
    add_para(
        "Una de las decisiones clave de diseño y validación del sistema fue establecer que las alertas preventivas "
        "automáticas de calibración y validación se despachen exactamente con 1 mes de anticipación. Esta decisión "
        "no es arbitraria; obedece a la realidad logística y operativa del aseguramiento metrológico en la industria "
        "farmacéutica y de laboratorios:"
    )
    
    bullet_points = [
        ("Cotización y Selección de Proveedores (Días 1 a 12): ", 
         "No todas las magnitudes son calibradas internamente. El coordinador de metrología debe buscar proveedores con acreditación ONAC (u homólogos), enviar alcances, esperar propuestas económicas, tramitar aprobaciones de compras internas y emitir la orden de servicio."),
        ("Coordinación de Tiempos y Espacios (Días 12 a 17): ", 
         "Se programan las fechas de la visita del técnico o el envío de los patrones, asegurando que no interfiera críticamente con los lotes de producción activos del laboratorio."),
        ("Ejecución del Servicio y Emisión de Informes (Días 17 a 24): ", 
         "El periodo en el que se ejecuta físicamente la calibración y el tiempo de tolerancia que requiere el laboratorio externo para generar y firmar los certificados metrológicos."),
        ("Entrega y Restablecimiento (Días 24 a 30): ", 
         "El equipo regresa a la planta, se verifica la conformidad del certificado contra las tolerancias del proceso, se etiqueta y se pone en funcionamiento nuevamente.")
    ]
    
    for title, desc in bullet_points:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(4)
        run_title = p.add_run(title)
        run_title.bold = True
        run_title.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
        p.add_run(desc)
        
    add_para(
        "Conclusión: Un tiempo de alerta inferior a 30 días pondría en riesgo la continuidad operativa de los análisis "
        "en Laboratorios Laproff, forzando al uso de equipos vencidos o a detenciones de producción no planificadas."
    )

    # Section 4
    add_heading_1("4. Estado de la Validación Técnica")
    add_para(
        "Las pruebas y el control de calidad del código han arrojado resultados muy positivos. "
        "Se cuenta con una suite de pruebas automatizadas en tests/ que validan el motor de priorización de alertas, "
        "el agrupamiento por áreas, el pipeline de ETL de datos pesados y la simulación del envío de correos. "
        "El 100% de las pruebas ejecutadas (13 passed) pasan exitosamente de manera limpia y sin errores de sintaxis o de compilación."
    )

    # Section 5
    add_heading_1("5. Trabajo Pendiente (Roadmap del Proyecto)")
    add_para(
        "De cara al cierre del proyecto de grado y tras la retroalimentación del asesor en la próxima reunión, "
        "se tienen mapeadas las siguientes actividades pendientes:"
    )
    
    roadmap_points = [
        ("Mejoras en el Frontend (Detalles Visuales): ", "Uniformar las etiquetas del eje Y (conteo de equipos) y el eje X (áreas del laboratorio/meses) en las gráficas de Plotly de la pestaña principal del Dashboard. Además, mejorar la visibilidad de los nombres largos de equipos y áreas para evitar que se superpongan en resoluciones más pequeñas."),
        ("Fase Final de Validación: ", "Ejecutar un piloto en paralelo de 1 a 2 semanas utilizando datos reales del día a día del laboratorio para asegurar que el despachador automático no genere falsos positivos o spam de alertas. Adicionalmente, confirmar que los correos automáticos diarios de KPIs cumplan las expectativas visuales del coordinador metrológico."),
        ("Redacción del Documento Escrito (Tesis): ", "Redacción formal de los capítulos de Metodología de Implementación y Resultados, documentando el análisis de eficiencia antes y después de la optimización del backend.")
    ]
    
    for title, desc in roadmap_points:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(4)
        run_title = p.add_run(title)
        run_title.bold = True
        run_title.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
        p.add_run(desc)

    # Section 6
    add_heading_1("6. Siguientes Pasos de Cara a la Reunión con el Asesor")
    add_para(
        "Este informe servirá de base para la próxima sesión de revisión con el asesor universitario. El objetivo de la reunión será: "
        "1) Validar el enfoque funcional del sistema PAME. "
        "2) Confirmar si la justificación logística para la alerta preventiva de 30 días es considerada suficiente para el marco teórico de la tesis. "
        "3) Obtener aprobación del profesor para dar inicio a la redacción definitiva del documento escrito."
    )

    # Save
    doc.save("informe_avance_proyecto.docx")
    print("Report generated successfully as 'informe_avance_proyecto.docx'.")

if __name__ == "__main__":
    create_report()
