from pathlib import Path

from aromatwin.services.deployment_readiness import check_deployment_readiness


def test_deployment_readiness_separates_warnings_and_blockers(tmp_path: Path) -> None:
    report = check_deployment_readiness({"AROMATWIN_ENV": "development", "ENABLE_PUBLIC_API": "true"}, root=tmp_path)
    assert report.blocking_issues
    assert report.warnings
    assert set(report.blocking_issues).isdisjoint(report.warnings)
