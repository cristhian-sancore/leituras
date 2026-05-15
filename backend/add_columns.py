import asyncio
from sqlalchemy import text
from app.database import engine

async def main():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE importacoes ADD COLUMN desc_agua TEXT DEFAULT 'FORNECIMENTO DE AGUA'"))
            print("Added desc_agua")
        except Exception as e:
            print(e)
            
        try:
            await conn.execute(text("ALTER TABLE importacoes ADD COLUMN desc_esgoto TEXT DEFAULT 'ESGOTO'"))
            print("Added desc_esgoto")
        except Exception as e:
            print(e)
            
        try:
            await conn.execute(text("ALTER TABLE importacoes ADD COLUMN desc_lixo TEXT DEFAULT 'TAXA DE LIXO'"))
            print("Added desc_lixo")
        except Exception as e:
            print(e)

if __name__ == "__main__":
    asyncio.run(main())
