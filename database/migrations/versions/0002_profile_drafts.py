"""Add review-only profile drafts.

Revision ID: 0002_profile_drafts
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_profile_drafts"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if "profile_drafts" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "profile_drafts",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("supplier_item_id", sa.BigInteger(), nullable=False),
        sa.Column("match_candidate_id", sa.BigInteger(), nullable=False),
        sa.Column("brand", sa.Text(), nullable=False),
        sa.Column("fragrance_name", sa.Text(), nullable=False),
        sa.Column("concentration", sa.Text()),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("provenance_notes", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("review_status", sa.Text(), nullable=False),
        sa.Column("rejection_reason", sa.Text()),
        sa.ForeignKeyConstraint(["supplier_item_id"], ["supplier_items.id"]),
        sa.ForeignKeyConstraint(["match_candidate_id"], ["match_candidates.id"]),
        sa.ForeignKeyConstraint(["review_status"], ["review_statuses.code"]),
        sa.UniqueConstraint("supplier_item_id", "match_candidate_id"),
        sa.CheckConstraint("source_confidence BETWEEN 0 AND 1"),
    )


def downgrade() -> None:
    if "profile_drafts" in sa.inspect(op.get_bind()).get_table_names():
        op.drop_table("profile_drafts")
