"""grocery tables

Revision ID: 0001_grocery
Revises:
Create Date: 2026-11-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0001_grocery"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "users" in tables:
        columns = {column["name"] for column in inspector.get_columns("users")}
        if "email" not in columns:
            op.add_column("users", sa.Column("email", sa.String(128), nullable=True))
        if "nickname" not in columns:
            op.add_column("users", sa.Column("nickname", sa.String(64), nullable=True))
        if "role" not in columns:
            op.add_column("users", sa.Column("role", sa.String(16), nullable=False, server_default=sa.text("'user'")))
        if "updated_at" not in columns:
            op.add_column("users", sa.Column("updated_at", sa.DateTime(), nullable=True))
    from common.models import Base

    Base.metadata.create_all(bind)


def downgrade() -> None:
    pass
