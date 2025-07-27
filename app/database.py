from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from typing import Generator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Removed the print statement

# Create engine
engine = create_engine(DATABASE_URL, echo=False, future=True)  # Changed echo=True to echo=False

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Naming convention for Alembic
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

Base.metadata = MetaData(naming_convention=convention)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """
    Create all tables. Only use this for development/testing.
    In production, use Alembic migrations.
    """
    Base.metadata.create_all(bind=engine)
    print("Database initialized and tables created.")

def close_db():
    """
    Close database connections.
    """
    engine.dispose()
    print("Database connection closed.")