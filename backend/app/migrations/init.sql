-- SAEMI SaaS - Schema Inicial
-- Este arquivo é executado automaticamente pelo PostgreSQL no primeiro start

-- As tabelas são criadas pelo SQLAlchemy no startup da aplicação.
-- Este arquivo serve como referência e para extensões.

-- Migration v1.1: Adicionar colunas novas na tabela empresas
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='empresas' AND column_name='percentual_esgoto') THEN
        ALTER TABLE empresas ADD COLUMN percentual_esgoto NUMERIC(5,2) NOT NULL DEFAULT 70.00;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='empresas' AND column_name='consumo_minimo_m3') THEN
        ALTER TABLE empresas ADD COLUMN consumo_minimo_m3 INTEGER NOT NULL DEFAULT 10;
    END IF;
END $$;
