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
    
    # Si faltan credenciales o se fuerza consola, trabajamos en modo fallback/consola
    if force_console or not smtp_host or not smtp_user or not smtp_pass or "app_password" in smtp_pass:
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

    if force_console or not smtp_host or not smtp_user or not smtp_pass or "app_password" in smtp_pass:
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

def programar_alertas_diarias(hora: str = "08:00"):
    """
    Programa el envío automático de alertas diarias usando la librería schedule.
    Este loop bloquea la ejecución. Debe llamarse en un hilo separado o loop controlado.
    """
    def job():
        print(f"[Cronograma Alertas] Iniciando trabajo diario a las {hora}...")
        try:
            alertas = generar_alertas()
            enviar_alerta_diaria(alertas)
        except Exception as e:
            print(f"[Cronograma Alertas Error] Error al generar o enviar alertas diarias: {e}")

    schedule.every().day.at(hora).do(job)
    print(f"[Cronograma Alertas] Programado exitosamente para ejecutarse todos los días a las {hora}")
