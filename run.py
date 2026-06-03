"""
Punto de entrada principal del módulo PAME.
Permite ejecutar el pipeline ETL, generar alertas, lanzar el dashboard,
iniciar el programador de alertas diarias o limpiar la base de datos Firestore.

Uso:
    python run.py --mode etl --file data/samples/cronograma_sample.csv
    python run.py --mode etl --file data/samples/cronograma_historico.json --dry-run
    python run.py --mode alertas
    python run.py --mode dashboard
    python run.py --mode scheduler
    python run.py --mode limpiar
"""
import argparse
import sys
import subprocess
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Asegurar que el root del proyecto esté en sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

def ejecutar_etl(file_path: str, dry_run: bool):
    """Ejecuta el pipeline ETL sobre el archivo especificado."""
    if not file_path:
        print("Error: Debe especificar un archivo con --file para el modo etl.")
        sys.exit(1)
        
    path = Path(file_path)
    if not path.exists():
        print(f"Error: El archivo especificado no existe: {file_path}")
        sys.exit(1)
        
    try:
        from src.etl.pipeline import run_pipeline
        print(f"Iniciando ETL para el archivo: {file_path}")
        reporte = run_pipeline(str(path), dry_run=dry_run)
        print("\n=== REPORTE DE EJECUCIÓN ETL ===")
        print(f"Archivo: {reporte['carga']['archivo']}")
        print(f"Simulación (dry-run): {reporte['carga']['dry_run']}")
        print(f"Registros leídos: {reporte['transformacion']['total_registros']}")
        print(f"Registros cargados exitosamente: {reporte['carga']['insertados']}")
        print(f"Duplicados omitidos: {reporte['transformacion']['duplicados_eliminados']}")
        print(f"Registros inválidos (omitidos): {reporte['transformacion']['invalidos']}")
        print(f"Errores en carga: {len(reporte['carga']['errores'])}")
        print(f"Duración: {reporte['carga']['duracion_segundos']} segundos")
        print("================================")
    except Exception as e:
        print(f"Error crítico durante la ejecución de la ETL: {e}")
        sys.exit(1)

def ejecutar_alertas():
    """Genera alertas y simula o envía por correo electrónico."""
    try:
        from src.alertas.motor_alertas import generar_alertas
        from src.alertas.email_sender import enviar_alerta_diaria
        
        print("Consultando equipos y servicios para generar alertas...")
        alertas = generar_alertas()
        print(f"Se generaron {len(alertas)} alerta(s) activa(s).")
        
        # Enviar/simular alerta
        log_envio = enviar_alerta_diaria(alertas)
        print("\n=== REPORTE DE ENVÍO DE ALERTAS ===")
        print(f"Tipo: {log_envio.get('tipo')}")
        print(f"Destinatarios: {log_envio.get('destinatarios')}")
        print(f"Total alertas reportadas: {log_envio.get('total_alertas')}")
        print(f"Resultado de envío: {'ÉXITO' if log_envio.get('exito') else 'SIMULACIÓN/FALLIDO'}")
        if log_envio.get('error'):
            print(f"Detalle de error: {log_envio.get('error')}")
        print("====================================")
    except Exception as e:
        print(f"Error crítico generando alertas: {e}")
        sys.exit(1)

def ejecutar_dashboard():
    """Ejecuta el servidor de Streamlit para el dashboard."""
    dashboard_path = ROOT_DIR / "src" / "dashboard" / "app.py"
    if not dashboard_path.exists():
        print(f"Error: No se encontró el archivo del dashboard en {dashboard_path}")
        sys.exit(1)
        
    print(f"Iniciando Dashboard Streamlit ({dashboard_path})...")
    try:
        subprocess.run(["streamlit", "run", str(dashboard_path)], check=True)
    except KeyboardInterrupt:
        print("\nDashboard detenido por el usuario.")
    except Exception as e:
        print(f"Error iniciando Streamlit: {e}")
        sys.exit(1)

def ejecutar_scheduler():
    """Inicia el programador en bucle infinito para alertas diarias."""
    try:
        import time
        import schedule
        from src.alertas.email_sender import programar_alertas_diarias
        
        # Programar alertas para las 08:00
        programar_alertas_diarias("08:00")
        
        print("Programador iniciado. Presione Ctrl+C para detener.")
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nProgramador detenido por el usuario.")
    except Exception as e:
        print(f"Error en el programador: {e}")
        sys.exit(1)

def ejecutar_limpiar():
    """Limpia la base de datos Firestore pidiendo confirmación previa."""
    print("⚠️ ADVERTENCIA: Esta acción eliminará permanentemente todos los equipos y servicios de Firestore.")
    confirmacion = input("¿Está seguro de que desea continuar? (escriba 'si' para confirmar): ").strip().lower()
    
    if confirmacion == 'si':
        try:
            from src.database.equipos_repo import limpiar_equipos
            print("Limpiando base de datos Firestore...")
            eliminados = limpiar_equipos()
            print(f"Base de datos limpia con éxito. Se eliminaron {eliminados} documentos (equipos/servicios).")
        except Exception as e:
            print(f"Error limpiando la base de datos: {e}")
            sys.exit(1)
    else:
        print("Limpieza cancelada. No se modificó ningún dato.")

def main():
    parser = argparse.ArgumentParser(description="Módulo PAME - Laboratorios Laproff")
    parser.add_argument(
        "--mode",
        choices=["etl", "alertas", "dashboard", "scheduler", "limpiar"],
        required=True,
        help="Modo de ejecución del programa."
    )
    parser.add_argument(
        "--file",
        help="Ruta al archivo de datos (.csv, .xlsx, .json) para el modo etl."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Si se activa, el modo etl analizará el archivo sin escribir en Firestore."
    )
    
    args = parser.parse_args()
    
    if args.mode == "etl":
        ejecutar_etl(args.file, args.dry_run)
    elif args.mode == "alertas":
        ejecutar_alertas()
    elif args.mode == "dashboard":
        ejecutar_dashboard()
    elif args.mode == "scheduler":
        ejecutar_scheduler()
    elif args.mode == "limpiar":
        ejecutar_limpiar()

if __name__ == "__main__":
    main()
