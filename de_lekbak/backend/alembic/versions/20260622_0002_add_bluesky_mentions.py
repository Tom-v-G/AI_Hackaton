"""add bluesky mentions

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
        "bluesky_mentions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("post_uri", sa.String(length=512), nullable=False),
        sa.Column("cid", sa.String(length=256), nullable=True),
        sa.Column("author_did", sa.String(length=256), nullable=True),
        sa.Column("author_handle", sa.String(length=256), nullable=True),
        sa.Column("display_name", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("like_count", sa.Integer(), nullable=False),
        sa.Column("reply_count", sa.Integer(), nullable=False),
        sa.Column("repost_count", sa.Integer(), nullable=False),
        sa.Column("quote_count", sa.Integer(), nullable=False),
        sa.Column("engagement_score", sa.Float(), nullable=False),
        sa.Column("extracted_cves", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column(
            "inserted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_uri"),
    )
    op.create_index("ix_bluesky_mentions_created_at", "bluesky_mentions", ["created_at"])
    op.create_index("ix_bluesky_mentions_author_handle", "bluesky_mentions", ["author_handle"])
    op.create_index(
        "ix_bluesky_mentions_extracted_cves",
        "bluesky_mentions",
        ["extracted_cves"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_bluesky_mentions_engagement_score_desc",
        "bluesky_mentions",
        [sa.text("engagement_score DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_bluesky_mentions_engagement_score_desc", table_name="bluesky_mentions")
    op.drop_index("ix_bluesky_mentions_extracted_cves", table_name="bluesky_mentions")
    op.drop_index("ix_bluesky_mentions_author_handle", table_name="bluesky_mentions")
    op.drop_index("ix_bluesky_mentions_created_at", table_name="bluesky_mentions")
    op.drop_table("bluesky_mentions")
