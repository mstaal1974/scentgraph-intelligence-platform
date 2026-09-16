"""Add independent enrichment review workflow.

Revision ID: 0003
Revises: 0002
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "INSERT INTO review_statuses(code,description,terminal) VALUES "
        "('enrichment_started','Enrichment started',false),"
        "('needs_source_review','Source permissions require review',false),"
        "('needs_human_review','Human review required',false),"
        "('ready_for_approval','Enrichment is ready for a human decision',false),"
        "('rejected_duplicate','Rejected as a duplicate',true),"
        "('requires_more_sources','Additional permitted sources required',false) "
        "ON CONFLICT DO NOTHING"
    )
    op.create_table(
        "enrichment_sources",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("source_name", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text()),
        sa.Column("source_title", sa.Text()),
        sa.Column("source_domain", sa.Text()),
        sa.Column(
            "commercial_use_allowed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("can_copy_text", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_copy_images", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "can_use_for_factual_reference", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("can_use_for_matching", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source_confidence", sa.Numeric(4, 3), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("source_confidence BETWEEN 0 AND 1"),
        sa.CheckConstraint(
            "commercial_use_allowed OR (can_copy_text = FALSE AND can_copy_images = FALSE)"
        ),
    )
    op.execute("ALTER TABLE enrichment_reviews DROP CONSTRAINT IF EXISTS enrichment_reviews_check")
    with op.batch_alter_table("enrichment_reviews") as batch:
        batch.alter_column("match_candidate_id", nullable=True)
        batch.add_column(sa.Column("profile_draft_id", sa.BigInteger(), nullable=True))
        batch.create_foreign_key(
            "enrichment_reviews_profile_draft_fk",
            "profile_drafts",
            ["profile_draft_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch.create_unique_constraint("enrichment_reviews_profile_draft_key", ["profile_draft_id"])
        batch.add_column(sa.Column("source_summary", sa.Text()))
        batch.add_column(
            sa.Column("note_pyramid_json", postgresql.JSONB(), nullable=False, server_default="{}")
        )
        batch.add_column(
            sa.Column("scent_vector_json", postgresql.JSONB(), nullable=False, server_default="{}")
        )
        batch.add_column(
            sa.Column("enrichment_confidence", sa.Numeric(4, 3), nullable=False, server_default="0")
        )
        batch.add_column(
            sa.Column("licensing_risk", sa.Text(), nullable=False, server_default="high")
        )
        batch.add_column(
            sa.Column(
                "copied_text_detected", sa.Boolean(), nullable=False, server_default=sa.false()
            )
        )
        batch.add_column(sa.Column("review_notes", sa.Text()))
        batch.add_column(sa.Column("rejected_at", sa.DateTime(timezone=True)))
        batch.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            )
        )
        batch.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            )
        )
        batch.create_check_constraint(
            "enrichment_reviews_profile_or_match",
            "profile_draft_id IS NOT NULL OR match_candidate_id IS NOT NULL",
        )
        batch.create_check_constraint(
            "enrichment_reviews_confidence_range", "enrichment_confidence BETWEEN 0 AND 1"
        )
        batch.create_check_constraint(
            "enrichment_reviews_licensing_risk", "licensing_risk IN ('low','medium','high')"
        )
        batch.create_check_constraint(
            "enrichment_reviews_approval_guard",
            "review_status <> 'approved_for_catalogue' OR (description_reviewed AND reviewer IS NOT NULL AND approved_at IS NOT NULL AND enrichment_confidence >= 0.700 AND licensing_risk = 'low' AND copied_text_detected = FALSE)",
        )
    op.create_table(
        "profile_source_links",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "profile_draft_id",
            sa.BigInteger(),
            sa.ForeignKey("profile_drafts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "enrichment_source_id",
            sa.BigInteger(),
            sa.ForeignKey("enrichment_sources.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("usage_type", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("profile_draft_id", "enrichment_source_id", "usage_type"),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1"),
    )
    op.create_table(
        "profile_enrichment_events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "profile_draft_id",
            sa.BigInteger(),
            sa.ForeignKey("profile_drafts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("event_summary", sa.Text(), nullable=False),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "enrichment_reviews_status_idx", "enrichment_reviews", ["review_status", "created_at"]
    )
    op.create_index(
        "profile_enrichment_events_profile_idx",
        "profile_enrichment_events",
        ["profile_draft_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("profile_enrichment_events")
    op.drop_table("profile_source_links")
    op.drop_table("enrichment_sources")
    with op.batch_alter_table("enrichment_reviews") as batch:
        for column in (
            "profile_draft_id",
            "source_summary",
            "note_pyramid_json",
            "scent_vector_json",
            "enrichment_confidence",
            "licensing_risk",
            "copied_text_detected",
            "review_notes",
            "rejected_at",
            "created_at",
            "updated_at",
        ):
            batch.drop_column(column)
        batch.alter_column("match_candidate_id", nullable=False)
