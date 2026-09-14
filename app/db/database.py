import truststore
truststore.inject_into_ssl()

"""
SQLAlchemy engine/session setup.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

db_url = settings.DATABASE_URL

# Normalize Postgres URLs to use the psycopg2 driver explicitly
if db_url.startswith("postgresql://") and "+psycopg2" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
elif db_url.startswith("postgres://"):
    # Some providers (Neon, Render, Heroku-style) give "postgres://" - SQLAlchemy needs "postgresql://"
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)

connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.db import models  # noqa: F401  (ensure models are registered)
    Base.metadata.create_all(bind=engine)