"""
Módulo de envío de correo electrónico para alertas del PAME.
Genera plantillas HTML con colores de Laproff y envía vía SMTP.
Si no hay credenciales, imprime en consola y registra en Firestore.
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
from typing import List
import schedule
import time

from dotenv import load_dotenv
from src.database.equipos_repo import registrar_alerta
from src.alertas.motor_alertas import Alerta, generar_alertas

load_dotenv()

# Colores del tema Laproff
COLOR_HEADER_BG = "#0B3533"  # Teal oscuro
COLOR_PRIMARY = "#00A99D"    # Teal brillante
COLOR_CRITICA = "#FEE2E2"    # Rojo claro
COLOR_ALTA = "#FEF3C7"       # Amarillo claro
COLOR_MEDIA = "#F1F5F9"      # Gris claro
COLOR_TEXT = "#1A2535"

def generar_html_alerta(alertas: List[Alerta]) -> str:
    """
    Construye el cuerpo HTML del correo con tablas separadas por prioridad.
    """
    # Separar por prioridad
    criticas = [a for a in alertas if a.prioridad == "CRITICA"]
    altas = [a for a in alertas if a.prioridad == "ALTA"]
    medias = [a for a in alertas if a.prioridad == "MEDIA"]

    html = f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; color: {COLOR_TEXT}; line-height: 1.5; }}
          .header {{ background-color: {COLOR_HEADER_BG}; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
          .header h1 {{ color: #FFFFFF; margin: 0; font-size: 24px; }}
          .header h2 {{ color: {COLOR_PRIMARY}; margin: 5px 0 0 0; font-size: 16px; font-weight: normal; }}
          .section-title {{ font-size: 18px; font-weight: bold; margin-top: 25px; margin-bottom: 10px; border-bottom: 2px solid {COLOR_PRIMARY}; padding-bottom: 5px; }}
          table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px; }}
          th {{ background-color: {COLOR_HEADER_BG}; color: #FFFFFF; text-align: left; padding: 10px; font-weight: bold; }}
          td {{ padding: 10px; border: 1px solid #E2E8F0; }}
          .row-critica {{ background-color: {COLOR_CRITICA}; }}
          .row-alta {{ background-color: {COLOR_ALTA}; }}
          .row-media {{ background-color: {COLOR_MEDIA}; }}
          .badge {{ display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; }}
          .badge-critica {{ background-color: #DC2626; color: #FFFFFF; }}
          .badge-alta {{ background-color: #D97706; color: #FFFFFF; }}
          .badge-media {{ background-color: #4B5563; color: #FFFFFF; }}
          .footer {{ text-align: center; margin-top: 30px; font-size: 11px; color: #94A3B8; border-top: 1px solid #E2E8F0; padding-top: 15px; }}
        </style>
      </head>
      <body>
        <div class="header">
          <h1>PAME — Aseguramiento Metrológico</h1>
          <h2>Reporte Diario de Alertas de Servicios</h2>
        </div>
        
        <p>Estimado equipo de Metrología y Validaciones,</p>
        <p>A continuación se presenta el resumen de los servicios metrológicos próximos a vencer o vencidos en la planta:</p>
    """

    # Tabla Críticas
    if criticas:
        html += f'<div class="section-title" style="color: #DC2626;">🚨 ALERTAS CRÍTICAS (Vencidos o Vencen en &le; 7 días)</div>'
        html += "<table><thead><tr><th>Código</th><th>Nombre</th><th>Ubicación</th><th>Servicio</th><th>Vencimiento</th><th>Días</th><th>Proveedor</th></tr></thead><tbody>"
        for a in criticas:
            dias_label = f"VENCIDO ({a.dias_restantes} d)" if a.dias_restantes < 0 else f"{a.dias_restantes} días"
            html += f"""
            <tr class="row-critica">
              <td><b>{a.codigo_equipo}</b></td>
              <td>{a.nombre_equipo}</td>
              <td>{a.ubicacion}</td>
              <td>{a.tipo_servicio}</td>
              <td>{a.fecha_proxima}</td>
              <td><span class="badge badge-critica">{dias_label}</span></td>
              <td>{a.proveedor or 'N/A'}</td>
            </tr>
            """
        html += "</tbody></table>"

    # Tabla Altas
    if altas:
        html += f'<div class="section-title" style="color: #D97706;">⚠️ ALERTAS DE PRIORIDAD ALTA (Vencen en 8 a 15 días)</div>'
        html += "<table><thead><tr><th>Código</th><th>Nombre</th><th>Ubicación</th><th>Servicio</th><th>Vencimiento</th><th>Días</th><th>Proveedor</th></tr></thead><tbody>"
        for a in altas:
            html += f"""
            <tr class="row-alta">
              <td><b>{a.codigo_equipo}</b></td>
              <td>{a.nombre_equipo}</td>
              <td>{a.ubicacion}</td>
              <td>{a.tipo_servicio}</td>
              <td>{a.fecha_proxima}</td>
              <td><span class="badge badge-alta">{a.dias_restantes} días</span></td>
              <td>{a.proveedor or 'N/A'}</td>
            </tr>
            """
        html += "</tbody></table>"

    # Tabla Medias
    if medias:
        html += f'<div class="section-title" style="color: #4B5563;">🔔 ALERTAS DE PRIORIDAD MEDIA (Vencen en 16 a 30 días)</div>'
        html += "<table><thead><tr><th>Código</th><th>Nombre</th><th>Ubicación</th><th>Servicio</th><th>Vencimiento</th><th>Días</th><th>Proveedor</th></tr></thead><tbody>"
        for a in medias:
            html += f"""
            <tr class="row-media">
              <td><b>{a.codigo_equipo}</b></td>
              <td>{a.nombre_equipo}</td>
              <td>{a.ubicacion}</td>
              <td>{a.tipo_servicio}</td>
              <td>{a.fecha_proxima}</td>
              <td><span class="badge badge-media">{a.dias_restantes} días</span></td>
              <td>{a.proveedor or 'N/A'}</td>
            </tr>
            """
        html += "</tbody></table>"

    if not criticas and not altas and not medias:
        html += f"""
        <div style="background-color: #D1FAE5; color: #065F46; padding: 15px; border-radius: 6px; text-align: center; font-weight: bold; margin: 20px 0;">
          🟢 ¡Todos los equipos están al día! No hay servicios próximos a vencer en los siguientes 30 días.
        </div>
        """

    html += f"""
        <div class="footer">
          Reporte generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}<br>
          <b>Programa de Aseguramiento Metrológico — Laboratorios Laproff S.A.S.</b><br>
          <i>Este es un correo automático, por favor no responda directamente a este mensaje.</i>
        </div>
      </body>
    </html>
    """
    return html

def enviar_alerta_diaria(alertas: List[Alerta], force_console: bool = False) -> dict:
    """
    Envía resumen diario a los destinatarios configurados.
    Registra el log en la colección 'alertas_log'.
    """
    destinatarios_env = os.getenv("EMAIL_DESTINATARIOS", "juli3213@gmail.com")
    destinatarios = [d.strip() for d in destinatarios_env.split(",") if d.strip()]
    
    remitente = os.getenv("EMAIL_REMITENTE", "pame-alertas@laproff.com")
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    html_content = generar_html_alerta(alertas)
    
    exito = False
    error_msg = None
    
    # Si faltan credenciales o se usan placeholders, trabajamos en modo fallback/consola
    is_placeholder = False
    if smtp_user and smtp_pass:
        is_placeholder = ("tu_cuenta_de_correo" in smtp_user or 
                          "tu_contrasena_de_aplicacion" in smtp_pass or 
                          "correo@laproff.com" in smtp_user)
                          
    if force_console or not smtp_host or not smtp_user or not smtp_pass or "app_password" in smtp_pass or is_placeholder:
        print("\n=== [MODO SIMULACIÓN / CONSOLA] ENVIANDO ALERTA DIARIA ===")
        print(f"Remitente: {remitente}")
        print(f"Destinatarios: {destinatarios}")
        print(f"Asunto: Resumen Diario de Alertas PAME — {len(alertas)} alerta(s) activa(s)")
        print(f"HTML generado ({len(html_content)} bytes). Vista previa guardada localmente.")
        exito = True
    else:
        # Enviar correo real vía SMTP
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Resumen Diario de Alertas PAME — {len(alertas)} alerta(s) activa(s)"
            msg["From"] = remitente
            msg["To"] = ", ".join(destinatarios)
            
            msg.attach(MIMEText(html_content, "html"))
            
            port = int(smtp_port) if smtp_port else 587
            server = smtplib.SMTP(smtp_host, port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(remitente, destinatarios, msg.as_string())
            server.quit()
            exito = True
            print(f"[SMTP] Correo diario enviado exitosamente a: {destinatarios}")
        except Exception as e:
            error_msg = str(e)
            print(f"[SMTP ERROR] No se pudo enviar el correo: {e}")

    # Registrar en Firestore
    log_alerta = {
        "tipo": "diaria",
        "equipos_alertados": [a.codigo_equipo for a in alertas],
        "total_alertas": len(alertas),
        "destinatarios": destinatarios,
        "fecha_envio": datetime.utcnow().isoformat(),
        "exito": exito,
        "error": error_msg
    }

    try:
        registrar_alerta(log_alerta)
    except Exception as e:
        print(f"No se pudo guardar el registro de la alerta en Firestore: {e}")

    return log_alerta

def enviar_alerta_critica_inmediata(alerta: Alerta, force_console: bool = False) -> dict:
    """
    Envía correo urgente individual de inmediato para un equipo crítico.
    """
    destinatarios_env = os.getenv("EMAIL_DESTINATARIOS", "juli3213@gmail.com")
    destinatarios = [d.strip() for d in destinatarios_env.split(",") if d.strip()]
    
    remitente = os.getenv("EMAIL_REMITENTE", "pame-alertas@laproff.com")
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    html_content = f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; color: {COLOR_TEXT}; }}
          .box {{ background-color: #FEF2F2; border: 2px solid #EF4444; border-radius: 8px; padding: 20px; }}
          .title {{ font-size: 18px; font-weight: bold; color: #DC2626; margin-bottom: 15px; }}
          table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
          td, th {{ padding: 10px; border: 1px solid #FCA5A5; text-align: left; }}
          th {{ background-color: #EF4444; color: white; }}
        </style>
      </head>
      <body>
        <div class="box">
          <div class="title">⚠️ [URGENTE] EQUIPO EN ESTADO CRÍTICO EN EL PAME</div>
          <p>Se ha detectado un equipo cuya calibración o servicio metrológico requiere atención inmediata:</p>
          <table>
            <tr><th>Campo</th><th>Detalle</th></tr>
            <tr><td><b>Código del Equipo</b></td><td>{alerta.codigo_equipo}</td></tr>
            <tr><td><b>Nombre del Equipo</b></td><td>{alerta.nombre_equipo}</td></tr>
            <tr><td><b>Ubicación/Área</b></td><td>{alerta.ubicacion}</td></tr>
            <tr><td><b>Tipo de Servicio</b></td><td>{alerta.tipo_servicio}</td></tr>
            <tr><td><b>Fecha Próxima del Servicio</b></td><td>{alerta.fecha_proxima}</td></tr>
            <tr><td><b>Días Restantes</b></td><td><span style="color:red; font-weight:bold;">{alerta.dias_restantes} día(s)</span></td></tr>
            <tr><td><b>Proveedor</b></td><td>{alerta.proveedor or 'N/A'}</td></tr>
          </table>
          <p style="margin-top: 15px; font-weight: bold; color: #DC2626;">
            Mensaje: {alerta.mensaje}
          </p>
        </div>
      </body>
    </html>
    """

    exito = False
    error_msg = None

    is_placeholder = False
    if smtp_user and smtp_pass:
        is_placeholder = ("tu_cuenta_de_correo" in smtp_user or 
                          "tu_contrasena_de_aplicacion" in smtp_pass or 
                          "correo@laproff.com" in smtp_user)

    if force_console or not smtp_host or not smtp_user or not smtp_pass or "app_password" in smtp_pass or is_placeholder:
        print("\n=== [MODO SIMULACIÓN / CONSOLA] ENVIANDO ALERTA CRÍTICA INMEDIATA ===")
        print(f"Equipo: {alerta.codigo_equipo} ({alerta.nombre_equipo})")
        print(f"Destinatarios: {destinatarios}")
        print(f"Asunto: [URGENTE] PAME — Equipo {alerta.codigo_equipo} en estado crítico")
        exito = True
    else:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[URGENTE] PAME — Equipo {alerta.codigo_equipo} en estado crítico"
            msg["From"] = remitente
            msg["To"] = ", ".join(destinatarios)
            
            msg.attach(MIMEText(html_content, "html"))
            
            port = int(smtp_port) if smtp_port else 587
            server = smtplib.SMTP(smtp_host, port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(remitente, destinatarios, msg.as_string())
            server.quit()
            exito = True
            print(f"[SMTP] Correo urgente enviado exitosamente para {alerta.codigo_equipo}")
        except Exception as e:
            error_msg = str(e)
            print(f"[SMTP ERROR] No se pudo enviar el correo urgente: {e}")

    # Registrar en Firestore
    log_alerta = {
        "tipo": "critica_inmediata",
        "equipos_alertados": [alerta.codigo_equipo],
        "total_alertas": 1,
        "destinatarios": destinatarios,
        "fecha_envio": datetime.utcnow().isoformat(),
        "exito": exito,
        "error": error_msg
    }

    try:
        registrar_alerta(log_alerta)
    except Exception as e:
        print(f"No se pudo guardar el registro de la alerta en Firestore: {e}")

    return log_alerta

def enviar_reporte_kpis_diario(force_console: bool = False) -> dict:
    """
    Calcula los KPIs actuales del laboratorio y envía un correo diario con el resumen.
    """
    from src.database.equipos_repo import get_estado_actual_todos, registrar_alerta
    
    equipos = get_estado_actual_todos()
    total_equipos = len(equipos)
    
    al_dia = sum(1 for e in equipos if e.get("estado_servicio") == "Vigente")
    vencidos = sum(1 for e in equipos if e.get("estado_servicio") == "Vencido")
    programar = sum(1 for e in equipos if e.get("estado_servicio") == "Programar")
    
    pct_al_dia = round(al_dia / total_equipos * 100, 1) if total_equipos > 0 else 0.0
    pct_vencido = round(vencidos / total_equipos * 100, 1) if total_equipos > 0 else 0.0
    pct_programar = round(programar / total_equipos * 100, 1) if total_equipos > 0 else 0.0
    
    conformes = sum(1 for e in equipos if e.get("estado_conformidad") == "Cumple")
    no_conformes = sum(1 for e in equipos if e.get("estado_conformidad") == "No Cumple")
    tasa_conformidad = round(conformes / (conformes + no_conformes) * 100, 1) if (conformes + no_conformes) > 0 else 100.0
    
    # Generar HTML
    html_content = f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; color: {COLOR_TEXT}; line-height: 1.5; }}
          .header {{ background-color: {COLOR_HEADER_BG}; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
          .header h1 {{ color: #FFFFFF; margin: 0; font-size: 24px; }}
          .header h2 {{ color: {COLOR_PRIMARY}; margin: 5px 0 0 0; font-size: 16px; font-weight: normal; }}
          .kpi-container {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 20px; }}
          .kpi-card {{ flex: 1; min-width: 120px; background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 15px; text-align: center; }}
          .kpi-value {{ font-size: 20px; font-weight: bold; color: {COLOR_PRIMARY}; margin-top: 5px; }}
          .kpi-label {{ font-size: 12px; color: #64748B; }}
          .section-title {{ font-size: 16px; font-weight: bold; margin-top: 25px; border-bottom: 2px solid {COLOR_PRIMARY}; padding-bottom: 5px; }}
          table.data-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; }}
          table.data-table th {{ background-color: {COLOR_HEADER_BG}; color: #FFFFFF; padding: 8px; text-align: left; }}
          table.data-table td {{ padding: 8px; border: 1px solid #E2E8F0; }}
          .footer {{ text-align: center; margin-top: 30px; font-size: 11px; color: #94A3B8; border-top: 1px solid #E2E8F0; padding-top: 15px; }}
        </style>
      </head>
      <body>
        <div style="max-width: 600px; margin: 0 auto; border: 1px solid #E2E8F0; border-radius: 8px; padding: 15px;">
          <div class="header">
            <h1>PAME — Aseguramiento Metrológico</h1>
            <h2>Reporte Diario de KPIs del Laboratorio</h2>
          </div>
          
          <p>Estimado Coordinador, a continuación se presenta el estado de los indicadores de aseguramiento metrológico el día de hoy ({datetime.now().strftime('%d/%m/%Y')}):</p>
          
          <div class="kpi-container" style="margin-bottom: 20px;">
            <div class="kpi-card">
              <div class="kpi-label">Equipos Totales</div>
              <div class="kpi-value">{total_equipos}</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-label">% Equipos al Día</div>
              <div class="kpi-value">{pct_al_dia}%</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-label">Tasa Conformidad</div>
              <div class="kpi-value">{tasa_conformidad}%</div>
            </div>
          </div>
          
          <div class="kpi-container" style="margin-bottom: 20px;">
            <div class="kpi-card" style="background-color: #FEF2F2; border-color: #FCA5A5;">
              <div class="kpi-label" style="color: #991B1B;">Equipos Vencidos</div>
              <div class="kpi-value" style="color: #DC2626;">{vencidos}</div>
            </div>
            <div class="kpi-card" style="background-color: #FEF3C7; border-color: #FDE68A;">
              <div class="kpi-label" style="color: #92400E;">Por Programar</div>
              <div class="kpi-value" style="color: #D97706;">{programar}</div>
            </div>
          </div>

          <div style="margin-top: 15px; margin-bottom: 25px;">
            <span style="font-size: 13px; font-weight: bold; color: #4B5563;">Distribución de Estado Metrológico:</span>
            <table style="width: 100%; border-collapse: collapse; margin-top: 5px; height: 24px; border: 1px solid #E2E8F0; border-radius: 6px; overflow: hidden; text-align: center;">
              <tr>
                {f'<td style="width: {pct_al_dia}%; background-color: #10B981; color: white; font-size: 11px; font-weight: bold; padding: 4px;">{pct_al_dia}% Vigentes</td>' if pct_al_dia > 5 else f'<td style="width: {pct_al_dia}%; background-color: #10B981;"></td>' if pct_al_dia > 0 else ''}
                {f'<td style="width: {pct_programar}%; background-color: #F59E0B; color: white; font-size: 11px; font-weight: bold; padding: 4px;">{pct_programar}% Próximos</td>' if pct_programar > 5 else f'<td style="width: {pct_programar}%; background-color: #F59E0B;"></td>' if pct_programar > 0 else ''}
                {f'<td style="width: {pct_vencido}%; background-color: #DC2626; color: white; font-size: 11px; font-weight: bold; padding: 4px;">{pct_vencido}% Vencidos</td>' if pct_vencido > 5 else f'<td style="width: {pct_vencido}%; background-color: #DC2626;"></td>' if pct_vencido > 0 else ''}
              </tr>
            </table>
          </div>
    """
    
    # Listar vencidos si los hay
    vencidos_list = [e for e in equipos if e.get("estado_servicio") == "Vencido"]
    if vencidos_list:
        html_content += """
          <div class="section-title" style="color: #DC2626;">🚨 EQUIPOS VENCIDOS</div>
          <table class="data-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Nombre</th>
                <th>Ubicación</th>
                <th>Días Vencido</th>
              </tr>
            </thead>
            <tbody>
        """
        for eq in vencidos_list:
            dias_v = abs(eq.get("dias_restantes") or 0)
            html_content += f"""
              <tr>
                <td><b>{eq.get('codigo_equipo')}</b></td>
                <td>{eq.get('nombre')}</td>
                <td>{eq.get('ubicacion')}</td>
                <td style="color: #DC2626; font-weight: bold;">Hace {dias_v} días</td>
              </tr>
            """
        html_content += """
            </tbody>
          </table>
        """

    # Listar próximos a vencer (15 a 45 días) para dar visibilidad
    proximos_list = [e for e in equipos if e.get("dias_restantes") is not None and 15 < e.get("dias_restantes") <= 45]
    if proximos_list:
        html_content += """
          <div class="section-title" style="color: #D97706; border-bottom-color: #F59E0B;">📅 EQUIPOS PRÓXIMOS A VENCER (Planificación a 1 mes)</div>
          <table class="data-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Nombre</th>
                <th>Ubicación</th>
                <th>Días Restantes</th>
              </tr>
            </thead>
            <tbody>
        """
        for eq in proximos_list:
            dias_r = eq.get("dias_restantes")
            html_content += f"""
              <tr>
                <td><b>{eq.get('codigo_equipo')}</b></td>
                <td>{eq.get('nombre')}</td>
                <td>{eq.get('ubicacion')}</td>
                <td style="color: #D97706; font-weight: bold;">{dias_r} días restantes</td>
              </tr>
            """
        html_content += """
            </tbody>
          </table>
        """
        
    html_content += f"""
          <div class="footer">
            Generado automáticamente por PAME — Aseguramiento Metrológico de Laboratorios Laproff S.A.S.<br>
            © {datetime.now().year} Todos los derechos reservados.
          </div>
        </div>
      </body>
    </html>
    """

    destinatarios_env = os.getenv("EMAIL_DESTINATARIOS", "juli3213@gmail.com")
    destinatarios = [d.strip() for d in destinatarios_env.split(",") if d.strip()]
    remitente = os.getenv("EMAIL_REMITENTE", "pame-alertas@laproff.com")
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    exito = False
    error_msg = None

    is_placeholder = False
    if smtp_user and smtp_pass:
        is_placeholder = ("tu_cuenta_de_correo" in smtp_user or 
                          "tu_contrasena_de_aplicacion" in smtp_pass or 
                          "correo@laproff.com" in smtp_user)

    if force_console or not smtp_host or not smtp_user or not smtp_pass or "app_password" in smtp_pass or is_placeholder:
        print("\n=== [MODO SIMULACIÓN / CONSOLA] ENVIANDO REPORTE DIARIO DE KPIS ===")
        print(f"Destinatarios: {destinatarios}")
        print(f"Asunto: Reporte Diario de KPIs PAME — % Al Día: {pct_al_dia}%")
        exito = True
    else:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Reporte Diario de KPIs PAME — % Al Día: {pct_al_dia}%"
            msg["From"] = remitente
            msg["To"] = ", ".join(destinatarios)
            msg.attach(MIMEText(html_content, "html"))
            port = int(smtp_port) if smtp_port else 587
            server = smtplib.SMTP(smtp_host, port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(remitente, destinatarios, msg.as_string())
            server.quit()
            exito = True
            print(f"[SMTP] Reporte de KPIs diario enviado exitosamente a: {destinatarios}")
        except Exception as e:
            error_msg = str(e)
            print(f"[SMTP ERROR] No se pudo enviar el reporte de KPIs diario: {e}")

    log_alerta = {
        "tipo": "reporte_kpis_diario",
        "equipos_alertados": ["KPI_REPORT"],
        "total_alertas": 1,
        "destinatarios": destinatarios,
        "fecha_envio": datetime.utcnow().isoformat(),
        "exito": exito,
        "error": error_msg
    }
    try:
        registrar_alerta(log_alerta)
    except Exception as e:
        print(f"No se pudo guardar el registro del reporte de KPIs en DB: {e}")

    return log_alerta

def enviar_alertas_mes_siguiente(force_console: bool = False) -> dict:
    """
    Busca los equipos que vencen el próximo mes calendario y envía el informe consolidado.
    """
    from src.database.equipos_repo import get_estado_actual_todos, registrar_alerta
    from datetime import date
    
    equipos = get_estado_actual_todos()
    
    # Calcular próximo mes calendario
    hoy = date.today()
    if hoy.month == 12:
        sig_mes = 1
        sig_anio = hoy.year + 1
    else:
        sig_mes = hoy.month + 1
        sig_anio = hoy.year

    nombre_sig_mes = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ][sig_mes - 1]

    # Filtrar equipos que vencen en el próximo mes
    alertas_filtradas = []
    for eq in equipos:
        f_prox_str = eq.get("fecha_proximo_servicio")
        if not f_prox_str:
            continue
        try:
            f_prox = date.fromisoformat(f_prox_str)
            if f_prox.year == sig_anio and f_prox.month == sig_mes:
                dias = eq.get("dias_restantes") or 0
                prioridad = "MEDIA"
                if dias <= 15:
                    prioridad = "CRITICA"
                elif dias <= 30:
                    prioridad = "ALTA"
                    
                alertas_filtradas.append(Alerta(
                    codigo_equipo  = eq.get("codigo_equipo", ""),
                    nombre_equipo  = eq.get("nombre", ""),
                    ubicacion      = eq.get("ubicacion", "SIN UBICACIÓN"),
                    proveedor      = eq.get("proveedor"),
                    tipo_servicio  = eq.get("tipo_servicio"),
                    fecha_proxima  = f_prox_str,
                    dias_restantes = dias,
                    prioridad      = prioridad,
                    mensaje        = f"Vence el próximo mes ({nombre_sig_mes} de {sig_anio})",
                ))
        except Exception:
            continue

    # Enviar reporte consolidado si hay alertas
    destinatarios_env = os.getenv("EMAIL_DESTINATARIOS", "juli3213@gmail.com")
    destinatarios = [d.strip() for d in destinatarios_env.split(",") if d.strip()]
    remitente = os.getenv("EMAIL_REMITENTE", "pame-alertas@laproff.com")
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    exito = False
    error_msg = None
    
    if not alertas_filtradas:
        print(f"[Alertas Mensuales] No hay equipos con vencimiento en {nombre_sig_mes} {sig_anio}.")
        log_alerta = {
            "tipo": "alertas_mes_siguiente",
            "equipos_alertados": [],
            "total_alertas": 0,
            "destinatarios": destinatarios,
            "fecha_envio": datetime.utcnow().isoformat(),
            "exito": True,
            "error": "No hay vencimientos programados para el próximo mes"
        }
        return log_alerta

    html_content = generar_html_alerta(alertas_filtradas)
    html_content = html_content.replace(
        "<h1>PAME — Aseguramiento Metrológico</h1>",
        f"<h1>PAME — Aseguramiento Metrológico</h1><h2 style='color:#FFF;'>Alertas de Vencimientos: {nombre_sig_mes} {sig_anio}</h2>"
    )

    is_placeholder = False
    if smtp_user and smtp_pass:
        is_placeholder = ("tu_cuenta_de_correo" in smtp_user or 
                          "tu_contrasena_de_aplicacion" in smtp_pass or 
                          "correo@laproff.com" in smtp_user)

    if force_console or not smtp_host or not smtp_user or not smtp_pass or "app_password" in smtp_pass or is_placeholder:
        print(f"\n=== [MODO SIMULACIÓN / CONSOLA] ENVIANDO ALERTAS MENSUALES DE VENCIMIENTO ({nombre_sig_mes}) ===")
        print(f"Destinatarios: {destinatarios}")
        print(f"Total alertas: {len(alertas_filtradas)}")
        exito = True
    else:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Cronograma PAME — Alertas de Vencimiento para {nombre_sig_mes} {sig_anio} ({len(alertas_filtradas)} equipos)"
            msg["From"] = remitente
            msg["To"] = ", ".join(destinatarios)
            msg.attach(MIMEText(html_content, "html"))
            port = int(smtp_port) if smtp_port else 587
            server = smtplib.SMTP(smtp_host, port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(remitente, destinatarios, msg.as_string())
            server.quit()
            exito = True
            print(f"[SMTP] Alertas mensuales enviadas exitosamente a: {destinatarios}")
        except Exception as e:
            error_msg = str(e)
            print(f"[SMTP ERROR] No se pudo enviar el reporte mensual: {e}")

    log_alerta = {
        "tipo": "alertas_mes_siguiente",
        "equipos_alertados": [a.codigo_equipo for a in alertas_filtradas],
        "total_alertas": len(alertas_filtradas),
        "destinatarios": destinatarios,
        "fecha_envio": datetime.utcnow().isoformat(),
        "exito": exito,
        "error": error_msg
    }
    try:
        registrar_alerta(log_alerta)
    except Exception as e:
        print(f"No se pudo guardar el registro de alertas del próximo mes en DB: {e}")

    return log_alerta

def verificar_y_enviar_alertas_automaticas(force_console: bool = False) -> dict:
    """
    Verifica de forma automática el envío de alertas de vencimiento.
    Aplica una regla de negocio logística:
    1. Filtra los equipos a un mes de vencerse (días restantes entre 15 y 45).
    2. Solo envía el correo si hay al menos 5 equipos en este rango (para optimizar cotizaciones en lote).
    3. Excepción de seguridad: Si hay algún equipo con estado crítico (<15 días), se envía de inmediato.
    """
    from src.database.equipos_repo import get_estado_actual_todos, registrar_alerta
    
    equipos = get_estado_actual_todos()
    
    proximos = []   # Equipos a un mes de vencerse (15-45 días)
    criticos = []   # Equipos críticos (<15 días)
    
    for eq in equipos:
        dias = eq.get("dias_restantes")
        if dias is None:
            continue
        
        alerta_obj = Alerta(
            codigo_equipo  = eq.get("codigo_equipo", ""),
            nombre_equipo  = eq.get("nombre", ""),
            ubicacion      = eq.get("ubicacion", "SIN UBICACIÓN"),
            proveedor      = eq.get("proveedor"),
            tipo_servicio  = eq.get("tipo_servicio"),
            fecha_proxima  = eq.get("fecha_proximo_servicio"),
            dias_restantes = dias,
            prioridad      = "MEDIA" if dias > 30 else "ALTA" if dias > 15 else "CRITICA",
            mensaje        = f"Vence en {dias} días",
        )
        
        if 15 < dias <= 45:
            proximos.append(alerta_obj)
        elif dias <= 15:
            criticos.append(alerta_obj)
            
    # Evaluar si se cumple la regla de negocio para enviar
    debe_enviar = False
    motivo = ""
    
    if len(proximos) >= 5:
        debe_enviar = True
        motivo = f"Lote de {len(proximos)} equipos próximos a vencer (Límite >= 5 alcanzado)"
    elif len(criticos) > 0:
        debe_enviar = True
        motivo = f"Alerta de seguridad: {len(criticos)} equipos críticos con menos de 15 días"
        
    if not debe_enviar:
        print(f"[Alertas Automáticas] Evaluación omitida: {len(proximos)} próximos (requiere >= 5) y {len(criticos)} críticos.")
        return {
            "tipo": "alerta_automatica_lote",
            "equipos_alertados": [],
            "total_alertas": 0,
            "destinatarios": [],
            "fecha_envio": datetime.utcnow().isoformat(),
            "exito": True,
            "error": "Omitido por regla de negocio (acumulación < 5 y 0 críticos)"
        }

    # Unir alertas para el correo
    todas_alertas = criticos + proximos
    
    destinatarios_env = os.getenv("EMAIL_DESTINATARIOS", "juli3213@gmail.com")
    destinatarios = [d.strip() for d in destinatarios_env.split(",") if d.strip()]
    remitente = os.getenv("EMAIL_REMITENTE", "pame-alertas@laproff.com")
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    exito = False
    error_msg = None
    
    html_content = generar_html_alerta(todas_alertas)
    html_content = html_content.replace(
        "<h1>PAME — Aseguramiento Metrológico</h1>",
        f"<h1>PAME — Aseguramiento Metrológico</h1><h2 style='color:#FFF;'>Despacho Automático: {motivo}</h2>"
    )

    is_placeholder = False
    if smtp_user and smtp_pass:
        is_placeholder = ("tu_cuenta_de_correo" in smtp_user or 
                          "tu_contrasena_de_aplicacion" in smtp_pass or 
                          "correo@laproff.com" in smtp_user)

    if force_console or not smtp_host or not smtp_user or not smtp_pass or "app_password" in smtp_pass or is_placeholder:
        print(f"\n=== [MODO SIMULACIÓN] ENVIANDO ALERTAS AUTOMÁTICAS ({motivo}) ===")
        print(f"Destinatarios: {destinatarios}")
        print(f"Total alertas: {len(todas_alertas)}")
        exito = True
    else:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Alerta Automática PAME — {motivo}"
            msg["From"] = remitente
            msg["To"] = ", ".join(destinatarios)
            msg.attach(MIMEText(html_content, "html"))
            port = int(smtp_port) if smtp_port else 587
            server = smtplib.SMTP(smtp_host, port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(remitente, destinatarios, msg.as_string())
            server.quit()
            exito = True
            print(f"[SMTP] Alerta automática enviada: {motivo}")
        except Exception as e:
            error_msg = str(e)
            print(f"[SMTP ERROR] No se pudo enviar el correo automático: {e}")

    log_alerta = {
        "tipo": "alerta_automatica_lote",
        "equipos_alertados": [a.codigo_equipo for a in todas_alertas],
        "total_alertas": len(todas_alertas),
        "destinatarios": destinatarios,
        "fecha_envio": datetime.utcnow().isoformat(),
        "exito": exito,
        "error": error_msg
    }
    try:
        registrar_alerta(log_alerta)
    except Exception as e:
        print(f"No se pudo registrar la alerta automática en DB: {e}")

    return log_alerta

def programar_alertas_diarias(hora: str = "08:00"):
    """
    Programa el envío automático de alertas usando la librería schedule.
    1. Envía KPIs diarios todos los días a la hora indicada.
    2. Ejecuta la verificación de alertas por lotes todos los días a la misma hora.
    """
    def job_diario_kpi():
        print(f"[Cronograma Diario] Iniciando reporte de KPIs diario a las {hora}...")
        try:
            enviar_reporte_kpis_diario()
        except Exception as e:
            print(f"[Cronograma Diario Error] Error al generar o enviar reporte de KPIs: {e}")

    def job_diario_alertas():
        print(f"[Cronograma Diario] Verificando envío automático de alertas a las {hora}...")
        try:
            verificar_y_enviar_alertas_automaticas()
        except Exception as e:
            print(f"[Cronograma Diario Error] Error al evaluar alertas de vencimiento: {e}")

    schedule.every().day.at(hora).do(job_diario_kpi)
    schedule.every().day.at(hora).do(job_diario_alertas)
    print(f"[Cronograma PAME] Tareas programadas exitosamente a las {hora} todos los días.")


