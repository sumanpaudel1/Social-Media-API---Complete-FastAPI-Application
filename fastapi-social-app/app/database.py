import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Dependency function to get database session
async def get_db():
    """
    Dependency function to provide database session to FastAPI routes.
    This ensures proper connection management and cleanup.
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
