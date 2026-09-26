"""add users, sessions and ownership columns

Revision ID: 20260911_0004
Revises: 20260731_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260911_0004"
down_revision: str | None = "20260731_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    for name in ("email", "role", "is_active", "created_at"):
        op.create_index(f"ix_users_{name}", "users", [name])

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("token_hash", name="uq_auth_sessions_token_hash"),
    )
    for name in ("user_id", "token_hash", "expires_at", "created_at"):
        op.create_index(f"ix_auth_sessions_{name}", "auth_sessions", [name])

    for table in ("trips", "trip_versions", "files", "jobs", "skill_calls"):
        op.add_column(table, sa.Column("user_id", sa.String(64), nullable=True))
        op.create_index(f"ix_{table}_user_id", table, ["user_id"])


def downgrade() -> None:
    for table in ("trips", "trip_versions", "files", "jobs", "skill_calls"):
        op.drop_index(f"ix_{table}_user_id", table_name=table)
        op.drop_column(table, "user_id")
    for name in ("user_id", "token_hash", "expires_at", "created_at"):
        op.drop_index(f"ix_auth_sessions_{name}", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    for name in ("email", "role", "is_active", "created_at"):
        op.drop_index(f"ix_users_{name}", table_name="users")
    op.drop_table("users")
