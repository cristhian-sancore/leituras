from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config import get_settings
from app.database import engine, Base
from app.routers import auth, empresas, usuarios, importacao, leituras, exportacao, dashboard, superadmin

settings = get_settings()


async def run_migrations(conn):
    """Adiciona colunas novas em tabelas existentes (safe migrations)."""
    migrations = [
        "ALTER TABLE empresas ADD COLUMN IF NOT EXISTS percentual_esgoto NUMERIC(5,2) NOT NULL DEFAULT 70.00",
        "ALTER TABLE empresas ADD COLUMN IF NOT EXISTS consumo_minimo_m3 INTEGER NOT NULL DEFAULT 10",
    ]
    for sql in migrations:
        try:
            await conn.execute(text(sql))
        except Exception:
            pass  # Coluna ja existe ou tabela nao existe ainda


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: cria tabelas no banco se nao existem."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await run_migrations(conn)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema de Leitura de Agua como Servico (SaaS)",
    lifespan=lifespan,
    docs_url=None,        # Desativado em produção
    redoc_url=None,       # Desativado em produção
    openapi_url=None,     # Desativado em produção
)

# CORS
origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(auth.router, prefix="/api/v1")
app.include_router(empresas.router, prefix="/api/v1")
app.include_router(usuarios.router, prefix="/api/v1")
app.include_router(importacao.router, prefix="/api/v1")
app.include_router(leituras.router, prefix="/api/v1")
app.include_router(exportacao.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(superadmin.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
