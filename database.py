import os
from databases import Database
from sqlalchemy import create_engine, MetaData
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# databases library needs asyncpg driver whereas sqlalchemy engine needs psycopg2
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://") \
                                 .replace("postgresql+psycopg2://", "postgresql+asyncpg://")

SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://") \
                                .replace("postgresql+asyncpg://", "postgresql+psycopg2://")

database = Database(ASYNC_DATABASE_URL, min_size=1, max_size=5)
metadata = MetaData()
engine = create_engine(SYNC_DATABASE_URL, connect_args={"connect_timeout": 10})
