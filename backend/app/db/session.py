from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

engine = create_engine(
    settings.DATABASE_URL,
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()