"""Align profile draft JSON fields and restricted-content guard.

Revision ID: 0004
Revises: 0003
"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("profile_drafts") as batch:
        for old, new in (
            ("top_notes", "top_notes_json"),
            ("heart_notes", "heart_notes_json"),
            ("base_notes", "base_notes_json"),
            ("accords", "accords_json"),
            ("season", "season_json"),
            ("occasion", "occasion_json"),
            ("mood", "mood_json"),
        ):
            batch.alter_column(old, new_column_name=new)
        batch.add_column(
            sa.Column(
                "restricted_content_detected",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch.create_check_constraint(
            "profile_drafts_approval_content_guard",
            "review_status <> 'approved_for_catalogue' OR (restricted_content_detected = FALSE AND source_confidence >= 0.700)",
        )


def downgrade() -> None:
    with op.batch_alter_table("profile_drafts") as batch:
        batch.drop_constraint("profile_drafts_approval_content_guard", type_="check")
        batch.drop_column("restricted_content_detected")
        for old, new in (
            ("top_notes_json", "top_notes"),
            ("heart_notes_json", "heart_notes"),
            ("base_notes_json", "base_notes"),
            ("accords_json", "accords"),
            ("season_json", "season"),
            ("occasion_json", "occasion"),
            ("mood_json", "mood"),
        ):
            batch.alter_column(old, new_column_name=new)
