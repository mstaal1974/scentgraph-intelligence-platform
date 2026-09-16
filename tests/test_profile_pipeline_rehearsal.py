from aromatwin.schemas.profile_pipeline_rehearsal import ProfilePipelineRehearsalRequest
from aromatwin.services.profile_pipeline_rehearsal import run_profile_pipeline_rehearsal


def test_rehearsal_is_fictional_and_non_actioning(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result, _ = run_profile_pipeline_rehearsal(ProfilePipelineRehearsalRequest(max_candidates=2))
    assert result.source_label == "fictional-rehearsal-sample"
    assert result.draft_profile_count == 2
    assert result.maison_ready_count == 0
    assert not list(tmp_path.rglob("*"))
    assert "approved" not in result.model_dump_json()


def test_trace_only_has_no_production_counts():
    result, _ = run_profile_pipeline_rehearsal(
        ProfilePipelineRehearsalRequest(rehearsal_mode="trace_only")
    )
    assert result.draft_profile_count == result.review_packet_count == 0
