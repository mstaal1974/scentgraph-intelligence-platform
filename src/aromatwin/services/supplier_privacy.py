import csv
from pathlib import Path

FORBIDDEN_PUBLIC_SAMPLE_COLUMNS = frozenset(
    {
        "AED",
        "CODE",
        "CN",
        "USD",
        "USD $",
        "QTY",
        "QUANTITY",
        "CN CODE",
        "CN_CODE",
        "COST",
        "COST PRICE",
        "MARGIN",
        "PRICE",
        "SKU",
        "STOCK",
        "SUPPLIER CODE",
        "SUPPLIER_CODE",
        "SUPPLIER PRICE",
        "SUPPLIER_PRICE",
        "COMMERCIAL TERMS",
        "COMMERCIAL_TERMS",
    }
)
REQUIRED_PUBLIC_SAMPLE_COLUMNS = frozenset({"BRAND", "NAME", "ORI"})


def normalise_column(column: str) -> str:
    return " ".join(column.lstrip("\ufeff").strip().upper().replace("_", " ").split())


def validate_public_supplier_sample(path: str | Path) -> set[str]:
    """Validate that a tracked sample contains identity hints, never commercial fields."""
    sample = Path(path)
    with sample.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        headers = {normalise_column(column) for column in next(reader, [])}
    forbidden = headers & {normalise_column(column) for column in FORBIDDEN_PUBLIC_SAMPLE_COLUMNS}
    if forbidden:
        raise ValueError(
            f"Public supplier sample contains sensitive columns: {', '.join(sorted(forbidden))}"
        )
    missing = REQUIRED_PUBLIC_SAMPLE_COLUMNS - headers
    if missing:
        raise ValueError(
            f"Public supplier sample is missing identity columns: {', '.join(sorted(missing))}"
        )
    return headers


def is_private_import_path(path: str | Path) -> bool:
    parts = Path(path).as_posix().strip("/").split("/")
    return parts[:3] == ["data", "private", "imports"] or parts[0] == "private"
