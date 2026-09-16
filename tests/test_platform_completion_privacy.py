import csv
from pathlib import Path

from aromatwin.services.completion_task_registry import (
    build_completion_task_registry,
    public_task,
)
from scripts.audit_platform_completion_privacy import audit_paths


def test_completion_samples_are_public_safe():
    paths = list(Path("data/samples").glob("*platform*completion*.csv"))
    paths += list(Path("data/samples").glob("final_platform_readiness*.csv"))
    assert not audit_paths(paths)


def test_audit_rejects_private_field(tmp_path):
    unsafe = tmp_path / "completion.csv"
    with unsafe.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["task_id", "supplier_price"])
        writer.writerow(["fictional", "redacted"])
    assert audit_paths([unsafe])


def test_public_task_summaries_have_only_allowlisted_fields():
    allowed = {"task_id", "task_name", "category", "status", "blocker_type",
               "safe_auto_action", "next_action", "public_safe_summary"}
    assert all(set(public_task(task)) == allowed for task in build_completion_task_registry())
