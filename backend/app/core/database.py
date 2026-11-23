from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool, NullPool
from contextlib import contextmanager
from pathlib import Path
from app.core.config import get_settings
from app.models.database import Base

settings = get_settings()

# Ensure data directory exists for SQLite
if "sqlite" in settings.DATABASE_URL:
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

# Configure engine based on database type
is_sqlite = "sqlite" in settings.DATABASE_URL
is_postgresql = "postgresql" in settings.DATABASE_URL

if is_sqlite:
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG,
    )
elif is_postgresql:
    # Use NullPool for serverless PostgreSQL (Neon) to avoid connection limits
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,
        connect_args={
            "sslmode": "require",
            "connect_timeout": 10,
        },
        echo=settings.DEBUG,
    )
else:
    # Default configuration
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False} if is_sqlite else {},
        echo=settings.DEBUG,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    return SessionLocal()