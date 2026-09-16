from aromatwin.services.pilot_readiness_report import build_readiness_report


def stage(name, status="completed", blockers=None):
    return {"stage": name, "status": status, "blockers": blockers or []}


def test_small_pilot_still_requires_human_review():
    report = build_readiness_report("run", [stage("launch_intelligence")])
    assert report["readiness_status"] == "ready_for_small_launch_pilot"
    assert "human review" in report["pilot_recommendation"]
    assert "public launch approval" in report["pilot_recommendation"]


def test_reports_enrichment_supplier_product_and_privacy_gates():
    assert build_readiness_report("a", [stage("enrichment_research_queue", "skipped")])[
        "readiness_status"] == "ready_after_enrichment"
    assert build_readiness_report("b", [stage("supplier_matching", "skipped")])[
        "readiness_status"] == "ready_after_supplier_review"
    assert build_readiness_report("c", [stage("product_catalogue_readiness", "skipped")])[
        "readiness_status"] == "ready_after_product_setup"
    assert build_readiness_report("d", [], "failed")["readiness_status"] == "blocked_privacy_risk"
