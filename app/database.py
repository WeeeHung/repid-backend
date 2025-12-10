from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database connection settings"""
    supabase_db_url: str
    
    class Config:
        env_file = ".env"
        extra = "ignore"


# Load database URL from environment
settings = DatabaseSettings()
DATABASE_URL = settings.supabase_db_url

# Create database engine
# Set search_path via connection options (works with psycopg2)
# This ensures the search_path is set before SQLAlchemy validates foreign keys
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={
        "connect_timeout": 10,
        "options": "-csearch_path=public,auth"
    },
)


# Also set search_path via event listener as a backup
@event.listens_for(engine, "connect")
def set_search_path(dbapi_conn, connection_record):
    """Set PostgreSQL search_path to include auth schema (backup)"""
    # For psycopg2/psycopg3
    cursor = dbapi_conn.cursor()
    try:
        cursor.execute("SET search_path TO public, auth")
    finally:
        cursor.close()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

