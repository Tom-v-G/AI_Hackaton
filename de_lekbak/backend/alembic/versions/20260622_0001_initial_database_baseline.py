"""initial database baseline

Revision ID: 20260622_0001
Revises:
Create Date: 2026-06-22 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260622_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cves",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cve_id", sa.String(length=32), nullable=False),
        sa.Column("source_identifier", sa.String(length=255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_modified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("vuln_status", sa.String(length=64), nullable=True),
        sa.Column("description_en", sa.Text(), nullable=True),
        sa.Column("cwe_ids", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("affected_vendors", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("affected_products", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("raw_nvd", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
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
        sa.UniqueConstraint("cve_id"),
    )
    op.create_index("ix_cves_cve_id", "cves", ["cve_id"], unique=False)
    op.create_index("ix_cves_last_modified", "cves", ["last_modified"], unique=False)

    op.create_table(
        "cve_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cve_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=128), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["cve_id"], ["cves.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cve_id", "url", name="uq_cve_reference_url"),
    )
    op.create_index("ix_cve_references_cve_id", "cve_references", ["cve_id"], unique=False)

    op.create_table(
        "cve_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cve_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.String(length=8), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("base_score", sa.Numeric(precision=3, scale=1), nullable=True),
        sa.Column("base_severity", sa.String(length=16), nullable=True),
        sa.Column("vector_string", sa.Text(), nullable=True),
        sa.Column("metric_type", sa.String(length=16), nullable=False),
        sa.Column("raw_metric", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["cve_id"], ["cves.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "cve_id",
            "version",
            "source",
            "metric_type",
            name="uq_cve_metric_version_source_type",
        ),
    )
    op.create_index("ix_cve_metrics_cve_id", "cve_metrics", ["cve_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_cve_metrics_cve_id", table_name="cve_metrics")
    op.drop_table("cve_metrics")
    op.drop_index("ix_cve_references_cve_id", table_name="cve_references")
    op.drop_table("cve_references")
    op.drop_index("ix_cves_last_modified", table_name="cves")
    op.drop_index("ix_cves_cve_id", table_name="cves")
    op.drop_table("cves")
