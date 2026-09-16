"""Add production persistence and operational audit tables.

Revision ID: 0004_production_persistence_audit
Revises: 0003_supplier_offers
"""

from alembic import op

from aromatwin.database import Base
from aromatwin.persistence import models  # noqa: F401

revision = "0004_production_persistence_audit"
down_revision = "0003_supplier_offers"
branch_labels = None
depends_on = None

TABLES = (
    "persistent_runs",
    "persistent_run_stages",
    "persistent_artifacts",
    "persistent_profile_drafts",
    "persistent_review_items",
    "persistent_launch_candidates",
    "persistent_seller_demand_briefs",
    "persistent_consumer_scentprints",
    "persistent_provenance_records",
    "persistent_audit_events",
)


def upgrade() -> None:
    bind = op.get_bind()
    for name in TABLES:
        Base.metadata.tables[name].create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for name in reversed(TABLES):
        Base.metadata.tables[name].drop(bind=bind, checkfirst=True)
