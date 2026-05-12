from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente."""

    DATABASE_URL: str = "postgresql+asyncpg://saemi:saemi@db:5432/saemi"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480  # 8 horas
    JWT_REFRESH_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: str = "" # Padrão vazio: permite apenas a mesma origem se não for definido
    UPLOAD_DIR: str = "/app/uploads"
    APP_NAME: str = "SAEMI SaaS"
    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    if not settings.JWT_SECRET or len(settings.JWT_SECRET) < 32:
        raise ValueError("JWT_SECRET deve ter pelo menos 32 caracteres. Verifique o arquivo .env.")
    if settings.JWT_SECRET == "change-me":
        raise ValueError("JWT_SECRET não pode ser o valor padrão 'change-me'. Modifique no arquivo .env.")
    return settings
