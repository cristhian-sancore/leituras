from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config import get_settings
from app.database import engine, Base
from app.routers import auth, empresas, usuarios, importacao, leituras, exportacao, dashboard, superadmin, atribuicoes

settings = get_settings()


async def run_migrations(conn):
    """Adiciona colunas novas em tabelas existentes (safe migrations)."""
    migrations = [
        "ALTER TABLE empresas ADD COLUMN IF NOT EXISTS percentual_esgoto NUMERIC(5,2) NOT NULL DEFAULT 70.00",
        "ALTER TABLE empresas ADD COLUMN IF NOT EXISTS consumo_minimo_m3 INTEGER NOT NULL DEFAULT 10",
        # Atribuicao de leiturista por cliente
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS leiturista_atribuido_id BIGINT REFERENCES usuarios(id) ON DELETE SET NULL",
        "CREATE INDEX IF NOT EXISTS ix_cliente_leiturista ON clientes(leiturista_atribuido_id)",
        # Layouts de impressao customizaveis
        "ALTER TABLE empresas ADD COLUMN IF NOT EXISTS layout_impressao_id BIGINT REFERENCES layout_impressao(id) ON DELETE SET NULL",
        "ALTER TABLE empresas ADD COLUMN IF NOT EXISTS layout_notificacao_id BIGINT REFERENCES layout_impressao(id) ON DELETE SET NULL",
        "ALTER TABLE layout_impressao ADD COLUMN IF NOT EXISTS tipo_impressora TEXT NOT NULL DEFAULT 'ZQ520'",
        # Flags de servico por cliente: SO AGUA = sem esgoto; sem A12 lixo = sem lixo
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS tem_esgoto BOOLEAN NOT NULL DEFAULT true",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS tem_lixo BOOLEAN NOT NULL DEFAULT true",
        # CEP do cliente (ausente na versão inicial)
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS cep TEXT",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS cidade TEXT",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS uf TEXT",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS zona TEXT",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS quadra TEXT",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS lote TEXT",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS mes_ano_ref TEXT",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS data_vencimento TEXT",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS num_fatura TEXT",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS data_leit_anterior TEXT",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS ocorr_anterior TEXT",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS tipo_servico TEXT DEFAULT '02'",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS tem_agua BOOLEAN NOT NULL DEFAULT true",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS num_hidrometro TEXT",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS economias INTEGER DEFAULT 1",
        # Superadmin nao tem empresa: tornar empresa_id nullable
        "ALTER TABLE usuarios ALTER COLUMN empresa_id DROP NOT NULL",
        # Audit log do superadmin: empresa_id pode ser null
        "ALTER TABLE audit_log ALTER COLUMN empresa_id DROP NOT NULL",
    ]
    for sql in migrations:
        try:
            print(f"DEBUG: Executando migração: {sql}")
            await conn.execute(text(sql))
        except Exception as e:
            print(f"DEBUG: Erro ao executar {sql}: {e}")
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
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
if not origins:
    origins = [] # Se vazio, não permite cross-origin explícito

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
app.include_router(atribuicoes.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
