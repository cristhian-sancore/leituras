import asyncio
from sqlalchemy import text
from app.database import engine

async def run_migrations():
    migrations = [
        "ALTER TABLE empresas ADD COLUMN IF NOT EXISTS percentual_esgoto NUMERIC(5,2) NOT NULL DEFAULT 70.00",
        "ALTER TABLE empresas ADD COLUMN IF NOT EXISTS consumo_minimo_m3 INTEGER NOT NULL DEFAULT 10",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS leiturista_atribuido_id BIGINT REFERENCES usuarios(id) ON DELETE SET NULL",
        "CREATE INDEX IF NOT EXISTS ix_cliente_leiturista ON clientes(leiturista_atribuido_id)",
        "ALTER TABLE empresas ADD COLUMN IF NOT EXISTS layout_impressao_id BIGINT REFERENCES layout_impressao(id) ON DELETE SET NULL",
        "ALTER TABLE empresas ADD COLUMN IF NOT EXISTS layout_notificacao_id BIGINT REFERENCES layout_impressao(id) ON DELETE SET NULL",
        "ALTER TABLE layout_impressao ADD COLUMN IF NOT EXISTS tipo_impressora TEXT NOT NULL DEFAULT 'ZQ520'",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS tem_esgoto BOOLEAN NOT NULL DEFAULT true",
        "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS tem_lixo BOOLEAN NOT NULL DEFAULT true",
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
        "ALTER TABLE usuarios ALTER COLUMN empresa_id DROP NOT NULL",
        "ALTER TABLE audit_log ALTER COLUMN empresa_id DROP NOT NULL",
    ]
    
    async with engine.begin() as conn:
        for sql in migrations:
            try:
                print(f"Executando: {sql}")
                await conn.execute(text(sql))
                print("OK")
            except Exception as e:
                print(f"ERRO: {e}")

if __name__ == "__main__":
    asyncio.run(run_migrations())
