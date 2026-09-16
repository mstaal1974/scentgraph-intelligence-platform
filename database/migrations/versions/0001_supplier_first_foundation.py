"""Supplier-first foundation baseline.

Revision ID: 0001
"""

from pathlib import Path
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema = Path(__file__).resolve().parents[2] / "schema.sql"
    sql = schema.read_text(encoding="utf-8").removeprefix("BEGIN;").removesuffix("COMMIT;\n")
    for statement in sql.split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade() -> None:
    for table in (
        "source_provenance",
        "aliases",
        "clone_relationships",
        "products",
        "scent_vectors",
        "fragrance_accords",
        "accords",
        "fragrance_notes",
        "notes",
        "fragrances",
        "brands",
        "enrichment_reviews",
        "match_candidates",
        "supplier_items",
        "import_batches",
        "reference_sources",
        "review_statuses",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
