from dataclasses import dataclass
from pathlib import Path
import re
import pandas as pd
from scentgraph.services.validation import missing_headers

SUPPLIER_HEADERS = {
    "brand_name",
    "fragrance_name",
    "concentration",
    "product_type",
    "size_ml",
    "sku",
    "price",
    "currency",
    "source_reference",
}


def normalise_name(value: str) -> str:
    """Collapse spacing and apply predictable title casing without retailer rules."""
    return re.sub(r"\s+", " ", str(value).strip()).title()


def normalise_concentration(value: str) -> str:
    aliases = {
        "edp": "eau de parfum",
        "edt": "eau de toilette",
        "parfum extract": "extrait de parfum",
    }
    cleaned = re.sub(r"\s+", " ", str(value).strip()).casefold()
    return aliases.get(cleaned, cleaned)


def duplicate_mask(frame: pd.DataFrame) -> pd.Series:
    """Flag exact canonical variants; different concentrations remain distinct."""
    keys = pd.DataFrame(
        {
            "brand": frame["brand_name"].map(normalise_name).str.casefold(),
            "fragrance": frame["fragrance_name"].map(normalise_name).str.casefold(),
            "concentration": frame["concentration"].map(normalise_concentration),
        }
    )
    return keys.duplicated(keep=False)


@dataclass(frozen=True)
class ImportResult:
    staging: pd.DataFrame
    report: dict[str, object]


def prepare_supplier_csv(path: str | Path, source_name: str) -> ImportResult:
    frame = pd.read_csv(path, dtype={"sku": "string", "source_reference": "string"})
    missing = missing_headers(frame.columns, SUPPLIER_HEADERS)
    if missing:
        raise ValueError(f"Missing required headers: {', '.join(sorted(missing))}")
    staging = frame.copy()
    staging["brand_name_normalised"] = staging["brand_name"].map(normalise_name)
    staging["fragrance_name_normalised"] = staging["fragrance_name"].map(normalise_name)
    staging["concentration_normalised"] = staging["concentration"].map(normalise_concentration)
    staging["is_duplicate"] = duplicate_mask(staging)
    staging["source_name"] = source_name
    staging["source_type"] = "supplier_csv"
    report = {
        "source_name": source_name,
        "rows": len(staging),
        "duplicate_rows": int(staging["is_duplicate"].sum()),
        "variant_groups": int(
            staging.groupby(["brand_name_normalised", "fragrance_name_normalised"])[
                "concentration_normalised"
            ]
            .nunique()
            .gt(1)
            .sum()
        ),
        "warnings": [],
    }
    return ImportResult(staging=staging, report=report)
