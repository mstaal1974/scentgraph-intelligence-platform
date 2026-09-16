"""Align profile drafts with the public review contract.

Revision ID: 0003
Revises: 0002
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for old, new in (
        ("top_notes", "top_notes_json"),
        ("heart_notes", "heart_notes_json"),
        ("base_notes", "base_notes_json"),
        ("accords", "accords_json"),
        ("season", "season_json"),
        ("occasion", "occasion_json"),
        ("mood", "mood_json"),
    ):
        op.alter_column("profile_drafts", old, new_column_name=new)
    op.add_column(
        "profile_drafts",
        sa.Column(
            "restricted_content_detected",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.drop_constraint("profile_drafts_approved_reviewed", "profile_drafts", type_="check")
    op.create_check_constraint(
        "profile_drafts_approval_guard",
        "profile_drafts",
        "review_status <> 'approved_for_catalogue' OR "
        "(reviewer IS NOT NULL AND approved_at IS NOT NULL "
        "AND restricted_content_detected = FALSE AND source_confidence >= 0.700)",
    )


def downgrade() -> None:
    op.drop_constraint("profile_drafts_approval_guard", "profile_drafts", type_="check")
    op.create_check_constraint(
        "profile_drafts_approved_reviewed",
        "profile_drafts",
        "review_status <> 'approved_for_catalogue' OR "
        "(reviewer IS NOT NULL AND approved_at IS NOT NULL)",
    )
    op.drop_column("profile_drafts", "restricted_content_detected")
    for current, previous in (
        ("top_notes_json", "top_notes"),
        ("heart_notes_json", "heart_notes"),
        ("base_notes_json", "base_notes"),
        ("accords_json", "accords"),
        ("season_json", "season"),
        ("occasion_json", "occasion"),
        ("mood_json", "mood"),
    ):
        op.alter_column("profile_drafts", current, new_column_name=previous)
