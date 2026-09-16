import importlib.util
from pathlib import Path

from sqlalchemy import inspect

from aromatwin.persistence.database import create_persistence_engine, initialise_persistence
from aromatwin.persistence.models import PersistentRun


def test_initialise_temporary_sqlite(tmp_path):
    engine = create_persistence_engine(f"sqlite:///{tmp_path / 'persistence.db'}")
    initialise_persistence(engine)
    tables = set(inspect(engine).get_table_names())
    assert "persistent_runs" in tables
    assert "persistent_audit_events" in tables
    assert PersistentRun.__tablename__ in tables


def test_migration_is_importable_and_reversible():
    path = Path("database/migrations/versions/0002_production_persistence_audit.py")
    spec = importlib.util.spec_from_file_location("persistence_migration", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    assert callable(module.upgrade)
    assert callable(module.downgrade)
    assert module.down_revision == "0003_supplier_offers"
