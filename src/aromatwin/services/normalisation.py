import re

VARIANT_PATTERN = re.compile(r"(?:\s|[-_/])(TOP|SUPER|LZ)(?:\s|[-_/]|$)", re.IGNORECASE)


def normalise_name(value: object) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    return text.title()


def split_variant(value: object) -> tuple[str, str | None]:
    text = normalise_name(value)
    match = VARIANT_PATTERN.search(text)
    if not match:
        return text, None
    cleaned = VARIANT_PATTERN.sub(" ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -_/")
    return cleaned, match.group(1).upper()


def parse_original_hint(value: object) -> tuple[str | None, str | None]:
    text = normalise_name(value)
    if not text:
        return None, None
    for delimiter in (" / ", " - ", " | ", ": "):
        if delimiter in text:
            brand, name = text.split(delimiter, 1)
            return brand.strip() or None, name.strip() or None
    return None, text
