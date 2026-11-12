import os
from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.settings import database_url, load_env

load_env()
engine = create_engine(database_url(), pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def ensure_round_count() -> None:
    database = os.environ.get("MYSQL_DATABASE", "attack_console")
    with engine.connect() as conn:
        found = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = :database
                  AND TABLE_NAME = 'batches'
                  AND COLUMN_NAME = 'round_count'
                """
            ),
            {"database": database},
        ).scalar()
        if not found:
            conn.execute(
                text(
                    "ALTER TABLE batches ADD COLUMN round_count INT UNSIGNED NOT NULL DEFAULT 0"
                )
            )
            conn.commit()
