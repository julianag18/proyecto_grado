"""
db/client.py
──────────────────────────────────────────────────────────────────────────────
Singleton del cliente Supabase.
Todos los módulos importan `get_client()` para obtener la conexión.
──────────────────────────────────────────────────────────────────────────────
"""

from supabase import create_client, Client
from config.settings import settings

_client: Client | None = None


def get_client() -> Client:
    """
    Retorna el cliente Supabase como singleton.
    Se crea una única instancia al primer llamado y se reutiliza.
    Usa la clave service_role para operaciones del servidor (ETL, scheduler).
    """
    global _client
    if _client is None:
        _client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_key,
        )
    return _client


def get_anon_client() -> Client:
    """
    Retorna un cliente con clave anon (solo lectura / permisos de usuario).
    Usar en el Dashboard cuando no se necesitan privilegios elevados.
    """
    return create_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_anon_key,
    )
