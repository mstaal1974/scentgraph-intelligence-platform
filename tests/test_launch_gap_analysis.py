from aromatwin.services.launch_gap_analysis import analyse_launch_gaps


def test_gap_analysis_assigns_fixes_and_owners():
    gaps = analyse_launch_gaps({"launch_candidate_id": "x", "supplier_availability_band": "unknown",
                                "format_readiness": "low", "review_status": "needs_human_review"})
    indexed = {gap["gap_type"]: gap for gap in gaps}
    assert indexed["missing_supplier_confidence"]["owner_role"] == "supplier_reviewer"
    assert indexed["missing_product_variants"]["owner_role"] == "product_manager"
    assert all(gap["recommended_fix"] for gap in gaps)
