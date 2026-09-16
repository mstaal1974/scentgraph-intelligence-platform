from aromatwin.services.profile_pipeline_trace import STAGES, build_profile_pipeline_trace


def test_trace_required_stages_and_safe_references():
    rows = build_profile_pipeline_trace("fictional-rehearsal-001")
    assert [r.stage_name for r in rows] == STAGES
    assert all(
        r.privacy_status == "public_safe" and r.input_reference.startswith("ref-") for r in rows
    )
    forbidden = {"price", "cost", "stock", "quantity", "email", "review_text"}
    assert not any(word in r.model_dump_json().lower() for r in rows for word in forbidden)
