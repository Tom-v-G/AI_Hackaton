"""add reddit cves

Revision ID: 20260622_0002
Revises: 20260622_0001
Create Date: 2026-06-22 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260622_0002"
down_revision: str | None = "20260622_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reddit_cves",
        sa.Column("cve_number", sa.String(length=32), nullable=False),
        sa.Column("mention_count", sa.Integer(), nullable=False),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cve_number"),
    )
    op.create_index(op.f("ix_reddit_cves_cve_number"), "reddit_cves", ["cve_number"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reddit_cves_cve_number"), table_name="reddit_cves")
    op.drop_table("reddit_cves")
