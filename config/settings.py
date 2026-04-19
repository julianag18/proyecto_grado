"""
config/settings.py
──────────────────────────────────────────────────────────────────────────────
Carga y valida las variables de entorno del módulo PAME usando Pydantic v2.
Provee un objeto global `settings` que es importado por todos los demás módulos.
──────────────────────────────────────────────────────────────────────────────
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

# Ruta raíz del proyecto — importable sin instanciar Settings
ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Configuración centralizada del módulo PAME."""

    # ── Supabase ──────────────────────────────────────────────────────────────
    supabase_url: str = Field(default="", description="URL del proyecto Supabase")
    supabase_anon_key: str = Field(default="", description="Clave anon/public de Supabase")
    supabase_service_key: str = Field(default="", description="Clave service_role de Supabase")

    # ── Trazabilidad ──────────────────────────────────────────────────────────
    pame_usuario: str = Field(default="sistema", description="Usuario para logs de migración")

    # ── Entorno ───────────────────────────────────────────────────────────────
    env: str = Field(default="development")

    # ── Rutas internas ────────────────────────────────────────────────────────
    data_dir: Path = Field(default=ROOT_DIR / "data")
    logs_dir: Path = Field(default=ROOT_DIR / "logs")

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Crear directorios si no existen
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


# Instancia global — importar desde cualquier módulo con:
#   from config.settings import settings
settings = Settings()
