"""
Database engine / session setup.

Defaults to a local SQLite file so the whole platform runs with zero external
dependencies for a demo. Point DATABASE_URL at Postgres in production.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./phishing_sim.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Import models here so they're registered on Base before create_all runs.
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
