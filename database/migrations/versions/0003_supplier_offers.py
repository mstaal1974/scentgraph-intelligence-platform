"""Add private multi-supplier commercial offers.

Revision ID: 0003_supplier_offers
Revises: 0002_profile_drafts
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_supplier_offers"
down_revision: str | None = "0002_profile_drafts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if "supplier_offers" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "supplier_offers",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("supplier_name", sa.Text(), nullable=False),
        sa.Column("supplier_file_reference", sa.Text(), nullable=False),
        sa.Column("supplier_file_hash", sa.Text(), nullable=False),
        sa.Column("supplier_row_number", sa.Integer(), nullable=False),
        sa.Column("supplier_brand_raw", sa.Text(), nullable=False),
        sa.Column("supplier_name_raw", sa.Text(), nullable=False),
        sa.Column("supplier_reference_raw", sa.Text()),
        sa.Column("supplier_code_private", sa.Text()), sa.Column("supplier_cn_code_private", sa.Text()),
        sa.Column("supplier_unit", sa.Text()), sa.Column("quantity_private", sa.Numeric(12, 3)),
        sa.Column("price_aed_private", sa.Numeric(12, 2)), sa.Column("price_usd_private", sa.Numeric(12, 2)),
        sa.Column("currency", sa.Text()), sa.Column("price_basis", sa.Text()),
        sa.Column("normalised_brand", sa.Text(), nullable=False),
        sa.Column("normalised_name", sa.Text(), nullable=False), sa.Column("normalised_reference", sa.Text()),
        sa.Column("candidate_brand", sa.Text()), sa.Column("candidate_fragrance_name", sa.Text()),
        sa.Column("linked_match_candidate_id", sa.BigInteger(), sa.ForeignKey("match_candidates.id")),
        sa.Column("linked_catalogue_fragrance_id", sa.BigInteger(), sa.ForeignKey("fragrances.id")),
        sa.Column("offer_status", sa.Text(), nullable=False), sa.Column("confidence_score", sa.Numeric(4, 3)),
        sa.Column("review_status", sa.Text(), nullable=False), sa.Column("private_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1"),
        sa.CheckConstraint("review_status IN ('supplier_offer_imported','needs_matching','matched_to_candidate','matched_to_catalogue','rejected_duplicate','rejected_low_confidence','rejected_private_data_risk','needs_human_review')"),
    )


def downgrade() -> None:
    if "supplier_offers" in sa.inspect(op.get_bind()).get_table_names():
        op.drop_table("supplier_offers")
