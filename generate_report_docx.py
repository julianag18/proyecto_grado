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
    
    # Configuración de página (1 pulgada de margen)
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Estilo base del documento (Arial 11, gris oscuro para lectura cómoda)
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(11)
    font.color.rgb = RGBColor(0x2D, 0x37, 0x48)

    # Título principal del documento
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run("Informe de avance parcial: Módulo metrológico (PAME)")
    title_run.bold = True
    title_run.font.size = Pt(14)
    title_run.font.color.rgb = RGBColor(0x1A, 0x20, 0x2C)
    
    # Metadatos del proyecto
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.paragraph_format.space_after = Pt(12)
    meta.add_run("Proyecto de grado\n").bold = True
    meta.add_run("Autor: Juliana Gómez\n")
    meta.add_run("Fecha: 30 de julio de 2026\n")
    meta.add_run("Presentado a: Asesor interno del proyecto de grado\n")
    
    # Línea divisoria sencilla
    p = doc.add_paragraph()
    p.add_run("―" * 45).font.color.rgb = RGBColor(0xCB, 0xD5, 0xE0)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Funciones auxiliares para títulos con formato normal en español (solo primera letra en mayúscula)
    def add_heading_1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(6)
        r = h.add_run(text)
        r.bold = True
        r.font.size = Pt(12)
        r.font.color.rgb = RGBColor(0x2C, 0x52, 0x82) # Azul oscuro sobrio
        return h

    def add_heading_2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(10)
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

    # 1. Resumen ejecutivo
    add_heading_1("1. Resumen ejecutivo")
    add_para(
        "Este informe resume las actividades desarrolladas en el módulo de aseguramiento metrológico "
        "(PAME) para Laboratorios Laproff S.A.S. En las últimas semanas, nos enfocamos en trasladar el control "
        "del cronograma de calibración a una plataforma web centralizada y funcional. Los cambios principales "
        "abarcan la optimización del rendimiento al cargar bases de datos reales y la integración del sistema de "
        "envío de correos para las alertas de vencimiento."
    )

    # 2. Avance en comparación al planteamiento inicial
    add_heading_1("2. Comparación de avances respecto al estado inicial")
    add_para(
        "A continuación se detallan las mejoras realizadas en el aplicativo en comparación con el punto de partida:"
    )

    # Tabla de avances
    table = doc.add_table(rows=5, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    headers = ["Aspecto", "Estado inicial", "Estado actual"]
    col_widths = [Inches(1.8), Inches(2.2), Inches(2.5)]
    
    # Formato de cabecera de la tabla
    hdr_cells = table.rows[0].cells
    for i, header_text in enumerate(headers):
        hdr_cells[i].text = header_text
        set_cell_background(hdr_cells[i], "2C5282") # Fondo azul oscuro
        set_cell_margins(hdr_cells[i])
        run = hdr_cells[i].paragraphs[0].runs[0]
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        
    data = [
        (
            "Rendimiento del aplicativo",
            "La pantalla se congelaba por unos 3 minutos al cambiar de pestaña cuando se cargaba la base de datos completa de los equipos.",
            "Se modificó el código para consultar los datos en un solo bloque y agruparlos en memoria. El cambio de pestaña ahora es inmediato."
        ),
        (
            "Envío de correos",
            "Las alertas no se enviaban debido a problemas de configuración y sincronización con el servidor de Brevo.",
            "Se configuraron las credenciales correctas en el archivo de entorno y el envío de correos funciona correctamente."
        ),
        (
            "Alertas automáticas",
            "No existían avisos automáticos de vencimiento; solo se podían consultar los datos de forma manual.",
            "Se programó una tarea que revisa diariamente el inventario y envía alertas automáticas según las reglas del laboratorio."
        ),
        (
            "Indicadores de control",
            "No se contaba con KPIs consolidados en el inicio de la pantalla.",
            "Se incluyó una tarjeta resumen en el dashboard que muestra el porcentaje de equipos al día, equipos conformes y vencidos."
        )
    ]

    for row_idx, row_data in enumerate(data, start=1):
        row_cells = table.rows[row_idx].cells
        for col_idx, cell_value in enumerate(row_data):
            row_cells[col_idx].text = cell_value
            set_cell_margins(row_cells[col_idx])
            if row_idx % 2 == 0:
                set_cell_background(row_cells[col_idx], "F7FAFC")
            else:
                set_cell_background(row_cells[col_idx], "FFFFFF")

    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width

    # 3. Decisiones tomadas y su explicación
    add_heading_1("3. Explicación de las decisiones tomadas")
    
    add_heading_2("Optimización del tiempo de carga en la base de datos")
    add_para(
        "Al integrar los datos reales del laboratorio, notamos que el cambio de pestañas era demasiado lento. Al revisar "
        "el código, encontramos que el programa realizaba consultas individuales a la base de datos por cada equipo de forma consecutiva "
        "(problema conocido como N+1). Para solucionarlo, reescribimos el repositorio para que traiga toda la información necesaria "
        "en una sola consulta y haga el cruce de datos en la memoria del servidor. Además, añadimos un sistema de caché local que "
        "evita consultar la base de datos repetidamente a menos que se cargue un nuevo archivo de datos."
    )
    
    add_heading_2("Configuración del envío de correos por lotes")
    add_para(
        "Para evitar saturar al metrólogo con correos diarios individuales por cada equipo que venza, establecimos que las "
        "alertas rutinarias (equipos que vencen el próximo mes) se agrupen y se envíen en un solo correo consolidado cuando "
        "se acumulen 5 o más equipos. Sin embargo, si un equipo está a menos de 15 días de vencerse, se considera una alerta "
        "crítica y el correo se envía de inmediato, asegurando que los casos urgentes no queden en espera."
    )

    # 4. Justificación del plazo de anticipación de un mes
    add_heading_1("4. Justificación del plazo de 30 días para alertas preventivas")
    add_para(
        "Se decidió que las alertas preventivas se emitan con un mes (30 días) de anticipación. Esta ventana de tiempo responde "
        "a la logística y los procesos operativos necesarios en el laboratorio:"
    )
    
    bullet_points = [
        ("Cotización con proveedores autorizados: ", 
         "Muchas magnitudes requieren calibración por laboratorios externos acreditados. El proceso de solicitar cotizaciones, comparar ofertas y tramitar la orden de compra interna toma aproximadamente entre 1 y 12 días."),
        ("Programación del servicio: ", 
         "Es necesario coordinar con el área de producción para programar la calibración en fechas que no afecten los lotes de fabricación activos. Esta planeación toma entre 3 y 5 días adicionales."),
        ("Ejecución y traslado: ", 
         "El tiempo que tarda el proveedor en realizar el servicio técnico, emitir el informe de calibración y entregar el equipo calibrado toma aproximadamente una semana."),
        ("Verificación del certificado de conformidad: ", 
         "Una vez entregado el equipo, el metrólogo debe revisar el informe, contrastar los datos contra las tolerancias permitidas por el método y dictaminar si el equipo es apto para volver a usarse en planta.")
    ]
    
    for title, desc in bullet_points:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(4)
        run_title = p.add_run(title)
        run_title.bold = True
        run_title.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)
        p.add_run(desc)
        
    add_para(
        "Por estas razones, un plazo menor a un mes no daría margen suficiente para realizar las gestiones, obligando "
        "a detener la operación del equipo o a usarlo con la calibración ya vencida."
    )

    # 5. Estado de la validación
    add_heading_1("5. Estado de las pruebas y validación")
    add_para(
        "El funcionamiento lógico del aplicativo se validó mediante una serie de pruebas unitarias locales (pytest). "
        "Estas pruebas verifican que el cálculo de los días restantes sea correcto, que las alertas se agrupen de forma adecuada "
        "por área y prioridad, y que el formato HTML de los correos no presente fallas de visualización. Actualmente, todas las "
        "pruebas del sistema pasan correctamente."
    )

    # 6. Trabajo pendiente
    add_heading_1("6. Siguientes pasos y temas para la reunión")
    add_para(
        "Para finalizar el proyecto, se tienen programadas las siguientes tareas:"
    )
    
    roadmap_points = [
        ("Detalles de la visualización: ", "Ajustar las leyendas y títulos de los ejes de los gráficos en el dashboard para evitar que los textos largos de las áreas del laboratorio se vean cortados."),
        ("Prueba piloto: ", "Iniciar una prueba de campo de 1 a 2 semanas utilizando datos diarios reales del laboratorio para verificar el flujo de correos automáticos en el entorno de trabajo."),
        ("Escrito final: ", "Iniciar la redacción formal del documento de tesis basándonos en la estructura aprobada por el asesor.")
    ]
    
    for title, desc in roadmap_points:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(4)
        run_title = p.add_run(title)
        run_title.bold = True
        run_title.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)
        p.add_run(desc)

    # Guardar en el escritorio de la usuaria
    import os
    saved_successfully = False
    
    desktop_paths = [
        "C:/Users/julianag18/Desktop/informe_avance_proyecto.docx",
        "C:/Users/julianag18/OneDrive/Desktop/informe_avance_proyecto.docx"
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
        doc.save("informe_avance_proyecto_backup.docx")
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
    create_report()
