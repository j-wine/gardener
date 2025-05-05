import os
from typing import AsyncGenerator

import dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Load environment variables from .env file
dotenv.load_dotenv()

# Database URL constructed using environment variables
DATABASE_URL = (
    f'postgresql+asyncpg://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}:'
    f'{os.getenv("DB_PORT")}/{os.getenv("DB_DATABASE")}'
)

# Create asynchronous SQLAlchemy engine
engine = create_async_engine(url=DATABASE_URL)

# Create a configured "Session" class
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# Dependency to get the session
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
