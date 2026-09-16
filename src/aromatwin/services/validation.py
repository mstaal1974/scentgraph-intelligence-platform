from collections.abc import Iterable

SUPPLIER_COLUMNS = {"BRAND", "NAME", "ORI", "CN CODE", "QTY", "AED", "USD"}


def missing_headers(actual: Iterable[str], required: Iterable[str]) -> set[str]:
    return set(required) - set(actual)


def validate_supplier_headers(headers: Iterable[str]) -> None:
    missing = missing_headers(headers, SUPPLIER_COLUMNS)
    if missing:
        raise ValueError(f"Missing required supplier headers: {', '.join(sorted(missing))}")
