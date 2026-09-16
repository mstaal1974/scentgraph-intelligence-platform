"""Internal-only product format costing and margin scenario calculations."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

PRODUCT_FORMATS = {
    "10ml tester": Decimal("10"), "30ml bottle": Decimal("30"),
    "50ml bottle": Decimal("50"), "car diffuser": Decimal("8"),
    "body wash": Decimal("250"), "moisturiser": Decimal("200"),
    "kit / bundle": None, "kit": None,
}


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class CostInput:
    product_format: str
    fragrance_oil_cost: Decimal
    bottle_cost: Decimal = Decimal("0")
    cap_sprayer_cost: Decimal = Decimal("0")
    label_cost: Decimal = Decimal("0")
    box_packaging_cost: Decimal = Decimal("0")
    labour_cost: Decimal = Decimal("0")
    wastage_percentage: Decimal = Decimal("0")
    fulfilment_cost: Decimal = Decimal("0")
    marketplace_fee: Decimal = Decimal("0")
    payment_processing_fee: Decimal = Decimal("0")
    referral_fee: Decimal = Decimal("0")
    gst_tax_placeholder: Decimal = Decimal("0")
    target_margin_percentage: Decimal = Decimal("60")
    fill_volume_ml: Decimal | None = None
    oil_concentration_percentage: Decimal = Decimal("20")


@dataclass(frozen=True)
class MarginResult:
    product_format: str
    fill_volume_ml: Decimal | None
    oil_cost_estimate: Decimal
    packaging_cost_estimate: Decimal
    labour_cost_estimate: Decimal
    total_unit_cost_estimate: Decimal
    suggested_retail_price: Decimal
    gross_margin_amount: Decimal
    gross_margin_percentage: Decimal
    scenario_name: str
    confidence_score: float
    private_notes: str | None
    review_status: str


def calculate_margin(inputs: CostInput, scenario_name: str = "target") -> MarginResult:
    if inputs.product_format not in PRODUCT_FORMATS:
        raise ValueError(f"Unsupported product format: {inputs.product_format}")
    if not Decimal("0") <= inputs.target_margin_percentage < Decimal("100"):
        raise ValueError("target margin percentage must be at least 0 and below 100")
    fill = inputs.fill_volume_ml if inputs.fill_volume_ml is not None else PRODUCT_FORMATS[inputs.product_format]
    # fragrance_oil_cost is a per-ml input; bundles may provide an aggregate through fill_volume_ml=1.
    oil = inputs.fragrance_oil_cost * (fill or Decimal("1")) * inputs.oil_concentration_percentage / Decimal("100")
    oil *= Decimal("1") + inputs.wastage_percentage / Decimal("100")
    packaging = inputs.bottle_cost + inputs.cap_sprayer_cost + inputs.label_cost + inputs.box_packaging_cost
    subtotal = oil + packaging + inputs.labour_cost + inputs.fulfilment_cost
    rate = (inputs.marketplace_fee + inputs.payment_processing_fee + inputs.referral_fee + inputs.gst_tax_placeholder) / Decimal("100")
    divisor = Decimal("1") - inputs.target_margin_percentage / Decimal("100") - rate
    if divisor <= 0:
        raise ValueError("target margin and retail-price fees must total less than 100 percent")
    retail = subtotal / divisor
    total = subtotal + retail * rate
    margin = retail - total
    return MarginResult(inputs.product_format, fill, _money(oil), _money(packaging),
                        _money(inputs.labour_cost), _money(total), _money(retail), _money(margin),
                        (margin / retail * 100).quantize(Decimal("0.01")), scenario_name, 0.8,
                        "Internal estimate; validate assumptions before pricing.", "pending_review")


def public_safe_margin(result: MarginResult) -> dict[str, object]:
    return {"product_format": result.product_format, "scenario_name": result.scenario_name,
            "review_status": result.review_status, "confidence_score": result.confidence_score,
            "public_safe_summary": "An internal margin scenario was calculated for review."}
