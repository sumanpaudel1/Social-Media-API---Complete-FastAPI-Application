import asyncio
from database import engine

async def test_connection():
    try:
        async with engine.begin() as conn:
            print(" Successfully connected to PostgreSQL!")
    except Exception as e:
        print(" Connection failed:", e)

asyncio.run(test_connection())
