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
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
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


@app.get("/api/v1/debug/register-test")
async def debug_register_test():
    """Debug: testa se o register funciona."""
    import traceback
    from app.database import get_db
    from app.models import Empresa, Usuario
    from app.auth.password import hash_password
    from sqlalchemy import select
    try:
        async for db in get_db():
            empresa = Empresa(nome="Test Debug", slug="test-debug-" + str(int(__import__('time').time())))
            db.add(empresa)
            await db.flush()
            usuario = Usuario(
                empresa_id=empresa.id,
                nome="Debug User",
                email=f"debug-{int(__import__('time').time())}@test.com",
                senha_hash=hash_password("123456"),
                role="admin",
            )
            db.add(usuario)
            await db.flush()
            await db.rollback()
            return {"status": "ok", "empresa_id": empresa.id, "user_id": usuario.id}
    except Exception as e:
        return {"status": "error", "error": str(e), "trace": traceback.format_exc()}



async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
