"""
SIH 2026 — PS26103 | Database Session & Engine
==============================================
Provides SQLAlchemy engine, session factory, and FastAPI get_db dependency.
Defaults to PostgreSQL with automatic fallback to local SQLite.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from loguru import logger
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Database URL from environment, or fallback to SQLite for local development
DEFAULT_DB_PATH = PROJECT_ROOT / "paimana.db"
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Try connecting to PostgreSQL default
    pg_user = os.getenv("POSTGRES_USER", "paimana_admin")
    pg_pass = os.getenv("POSTGRES_PASSWORD", "changeme_in_production")
    pg_db = os.getenv("POSTGRES_DB", "sih2026_paimana")
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    DATABASE_URL = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"

# Test connection or fallback to SQLite
engine = None
try:
    if DATABASE_URL.startswith("postgresql"):
        # Test connecting to Postgres quickly
        test_engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 2})
        with test_engine.connect() as conn:
            pass
        engine = test_engine
        logger.info(f"Connected to PostgreSQL database: {DATABASE_URL.split('@')[-1]}")
    else:
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        logger.info(f"Using database: {DATABASE_URL}")
except Exception as e:
    # Fallback to local SQLite so development and tests never block
    sqlite_url = f"sqlite:///{DEFAULT_DB_PATH}"
    logger.warning(f"PostgreSQL connection unavailable ({e}). Falling back to local SQLite: {sqlite_url}")
    DATABASE_URL = sqlite_url
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that provides a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

