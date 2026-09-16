from aromatwin.services.review_gates import ALLOWED_DECISIONS, list_review_gates


def test_all_review_gates_are_explicit_and_audited():
    gates = list_review_gates()
    assert len(gates) == 14
    assert all(set(ALLOWED_DECISIONS) <= set(gate["allowed_decisions"]) for gate in gates)
    assert all(gate["audit_required"] for gate in gates)
    assert all("auto" not in gate["next_allowed_statuses"] for gate in gates)
