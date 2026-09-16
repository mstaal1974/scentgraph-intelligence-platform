import pytest

from aromatwin.services.review_decisions import apply_review_decision, public_decision_summary
from aromatwin.services.review_queue_builder import build_review_queues


@pytest.mark.parametrize("decision", ["approve", "reject", "request_enrichment",
    "request_supplier_review", "request_provenance_review", "hold", "escalate"])
def test_decisions_are_internal_and_audited(decision):
    item = build_review_queues({"profile_drafts": [{"profile_draft_id": "p1"}]})[0]
    events = []
    result = apply_review_decision(item, decision, "catalogue_reviewer",
                                   decision_reason="private", audit_recorder=lambda **event: events.append(event))
    assert result["creates_audit_event"] and events
    assert "publication" in result["next_action"]
    assert "decision_reason" not in public_decision_summary(result)
    assert not ({"product_sku", "catalogue_record", "campaign"} & result.keys())


def test_profile_approval_is_next_internal_stage():
    item = build_review_queues({"profile_drafts": [{"profile_draft_id": "p1"}]})[0]
    assert apply_review_decision(item, "approve", "catalogue_reviewer")["next_status"] == \
        "approved_for_catalogue_review"
