"""
Módulo de conexión a Firebase Firestore para el PAME de Laboratorios Laproff.
Credenciales SIEMPRE desde variables de entorno o archivo externo, nunca hardcodeadas.
"""
import os
import json
from google.cloud import firestore
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()

_db = None

def get_db() -> firestore.Client:
    """Singleton de conexión a Firestore. Reutiliza la misma instancia."""
    global _db
    if _db is not None:
        return _db

    # Opción 1: ruta a archivo de credenciales
    creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    # Opción 2: credenciales como JSON string (útil en servidores/CI)
    creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

    if creds_path and os.path.exists(creds_path):
        credentials = service_account.Credentials.from_service_account_file(creds_path)
    elif creds_json:
        info = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(info)
    else:
        raise EnvironmentError(
            "No se encontraron credenciales de Firebase. "
            "Configura FIREBASE_CREDENTIALS_PATH o FIREBASE_CREDENTIALS_JSON en .env"
        )

    _db = firestore.Client(credentials=credentials)
    return _db
