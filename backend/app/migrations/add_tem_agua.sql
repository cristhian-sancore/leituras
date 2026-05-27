-- Migration: Adicionar coluna tem_agua na tabela clientes
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='clientes' AND column_name='tem_agua') THEN
        ALTER TABLE clientes ADD COLUMN tem_agua BOOLEAN NOT NULL DEFAULT TRUE;
    END IF;
END $$;
