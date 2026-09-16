from aromatwin.services.review_queue_builder import build_review_queues, public_queue_summary


def test_queue_builds_expected_sources_and_minimises_output():
    sources = {
        "profile_drafts": [{"profile_draft_id": "p1", "supplier_price": 20}],
        "enrichment_items": [{"enrichment_item_id": "e1", "seller_private_notes": "secret"}],
        "launch_candidates": [{"launch_candidate_id": "l1", "raw_individual_feedback": "private"}],
        "pilot_blockers": [{"blocker_id": "b1", "severity": "critical"}],
    }
    queue = build_review_queues(sources)
    assert len(queue) == 4
    assert all({"gate_type", "priority_band", "risk_band", "assigned_role"} <= item.keys()
               for item in queue)
    rendered = str([public_queue_summary(item) for item in queue])
    assert "secret" not in rendered and "supplier_price" not in rendered and "private" not in rendered
