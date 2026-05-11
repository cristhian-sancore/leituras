from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import engine, Base
from app.routers import auth, empresas, usuarios, importacao, leituras, exportacao, dashboard, superadmin

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: cria tabelas no banco se não existem."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema de Leitura de Água como Serviço (SaaS)",
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


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
