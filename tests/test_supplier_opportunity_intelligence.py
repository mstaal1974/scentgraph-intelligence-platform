import csv
from pathlib import Path

from aromatwin.schemas.seller_demand import SellerDemandBriefCreate
from aromatwin.services.seller_demand_briefs import create_brief
from aromatwin.services.seller_supplier_matching import match_brief_to_candidates
from aromatwin.services.supplier_opportunity_intelligence import build_supplier_opportunities
from scripts.audit_seller_supplier_matching import audit


def test_opportunities_aggregate_demand_without_private_details() -> None:
    briefs = [create_brief(SellerDemandBriefCreate(seller_name=f"Seller {n}", seller_segment="niche",
        target_customer="adult", desired_moods=["calm"], desired_occasions=["work"],
        product_formats=["10ml tester"], private_seller_notes="secret")) for n in range(2)]
    candidate = {"supplier_name": "Private supplier", "canonical_fragrance_name": "Candidate",
        "product_formats": ["10ml tester"], "profile_completeness": .8,
        "catalogue_readiness": .8, "source_confidence": .8, "reference": "internal"}
    report = build_supplier_opportunities([match_brief_to_candidates(b, [candidate])[0] for b in briefs])
    assert report[0]["matched_demand_count"] == 2
    rendered = str(report).casefold()
    assert "seller 0" not in rendered and "secret" not in rendered
    assert "price" not in rendered and "commercial terms" not in rendered


def test_samples_and_audit_are_public_safe(tmp_path: Path) -> None:
    samples = Path("data/samples")
    for name in ("seller_demand_briefs_sample.csv", "seller_supplier_matches_sample.csv",
                 "supplier_opportunity_summary_sample.csv"):
        with (samples / name).open() as handle:
            headers = next(csv.reader(handle))
        assert not {"private_seller_notes", "supplier_price", "supplier_code", "margin"} & set(headers)
    assert audit(Path.cwd()) == []
    leak = tmp_path / "seller_demand_briefs_sample.csv"
    leak.write_text("private_seller_notes,public_safe_summary\nsecret,x\n")
    assert audit(tmp_path, [leak.name])


def test_cli_rejects_public_operational_output() -> None:
    import argparse

    import pytest

    from scripts.build_seller_demand_matches import private_path
    with pytest.raises(argparse.ArgumentTypeError):
        private_path("data/samples/output.json")
