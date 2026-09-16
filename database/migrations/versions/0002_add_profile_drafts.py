"""Add review-only fragrance profile drafts.

Revision ID: 0002
Revises: 0001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None
STATUSES = (
    "needs_human_review",
    "approved_for_catalogue",
    "rejected_low_confidence",
    "rejected_licensing_risk",
    "rejected_duplicate",
    "requires_more_sources",
)


def upgrade() -> None:
    op.create_table(
        "profile_drafts",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "supplier_item_id",
            sa.BigInteger(),
            sa.ForeignKey("supplier_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "match_candidate_id",
            sa.BigInteger(),
            sa.ForeignKey("match_candidates.id", ondelete="SET NULL"),
        ),
        sa.Column("candidate_brand", sa.Text(), nullable=False),
        sa.Column("candidate_fragrance_name", sa.Text(), nullable=False),
        sa.Column("likely_original_brand", sa.Text()),
        sa.Column("likely_original_name", sa.Text()),
        sa.Column("profile_title", sa.Text(), nullable=False),
        sa.Column("description_original", sa.Text(), nullable=False),
        sa.Column("description_generation_method", sa.Text(), nullable=False),
        sa.Column("top_notes", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("heart_notes", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("base_notes", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("accords", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("fragrance_family", sa.Text()),
        sa.Column("gender", sa.Text()),
        sa.Column("season", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("occasion", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("mood", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("scent_vector_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("confidence_score", sa.Numeric(4, 3), nullable=False),
        sa.Column("source_confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("provenance_notes", sa.Text(), nullable=False),
        sa.Column("review_status", sa.Text(), nullable=False),
        sa.Column("reviewer", sa.Text()),
        sa.Column("rejection_reason", sa.Text()),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("rejected_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "confidence_score BETWEEN 0 AND 1", name="profile_drafts_confidence_range"
        ),
        sa.CheckConstraint(
            "source_confidence BETWEEN 0 AND 1", name="profile_drafts_source_confidence_range"
        ),
        sa.CheckConstraint(f"review_status IN {STATUSES}", name="profile_drafts_review_status"),
        sa.CheckConstraint(
            "review_status <> 'approved_for_catalogue' OR (reviewer IS NOT NULL AND approved_at IS NOT NULL)",
            name="profile_drafts_approved_reviewed",
        ),
        sa.CheckConstraint(
            "review_status NOT LIKE 'rejected_%' OR (reviewer IS NOT NULL AND rejected_at IS NOT NULL AND rejection_reason IS NOT NULL)",
            name="profile_drafts_rejected_reviewed",
        ),
    )
    op.create_index(
        "profile_drafts_review_queue_idx", "profile_drafts", ["review_status", "created_at"]
    )
    op.execute(
        "CREATE UNIQUE INDEX profile_drafts_active_candidate_idx ON profile_drafts(supplier_item_id, match_candidate_id) WHERE review_status IN ('needs_human_review','requires_more_sources','approved_for_catalogue')"
    )


def downgrade() -> None:
    op.drop_table("profile_drafts")
