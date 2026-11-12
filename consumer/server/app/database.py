from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.settings import admin_url, database_url, load_env

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema.sql"

load_env()


def _statements() -> list[str]:
    statements = []
    for chunk in SCHEMA_PATH.read_text(encoding="utf-8").split(";"):
        lines = [
            line
            for line in chunk.splitlines()
            if line.strip() and not line.strip().startswith("--")
        ]
        statement = "\n".join(lines).strip()
        if statement:
            statements.append(statement)
    return statements


def apply_schema() -> None:
    admin = create_engine(admin_url(), isolation_level="AUTOCOMMIT", future=True)
    with admin.connect() as conn:
        for statement in _statements():
            conn.execute(text(statement))
    admin.dispose()


engine = create_engine(database_url(), pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
