import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

from aromatwin.services.margin_intelligence import PRODUCT_FORMATS, CostInput, calculate_margin


def test_margin_calculates_fictional_product_cost() -> None:
    result = calculate_margin(CostInput(product_format="10ml tester",
        fragrance_oil_cost=Decimal("2"), bottle_cost=Decimal("1"),
        labour_cost=Decimal("1"), target_margin_percentage=Decimal("50")))
    assert result.oil_cost_estimate == Decimal("4.00")
    assert result.total_unit_cost_estimate == Decimal("6.00")
    assert result.suggested_retail_price == Decimal("12.00")
    assert result.gross_margin_percentage == Decimal("50.00")


def test_all_required_product_formats_are_supported() -> None:
    expected = {"10ml tester", "30ml bottle", "50ml bottle", "car diffuser",
                "body wash", "moisturiser", "kit / bundle"}
    assert expected <= PRODUCT_FORMATS.keys()
    for product_format in expected:
        assert calculate_margin(CostInput(product_format=product_format,
            fragrance_oil_cost=Decimal("1"))).product_format == product_format


def test_margin_cli_writes_only_to_private_reports() -> None:
    private = Path("data/private/test-margin-input.json")
    output = Path("data/private/reports/test-margin-output.json")
    private.parent.mkdir(parents=True, exist_ok=True)
    private.write_text(json.dumps([{"product_format": "30ml bottle",
                                   "fragrance_oil_cost": "1"}]))
    try:
        result = subprocess.run([sys.executable, "scripts/build_margin_scenarios.py", str(private),
                                 "--output", str(output)], check=True, capture_output=True, text=True)
        assert "accepted=1 rejected=0" in result.stdout
        assert output.exists()
        assert Path("data/private/reports").resolve() in output.resolve().parents
    finally:
        private.unlink(missing_ok=True)
        output.unlink(missing_ok=True)
