import pytest
from pydantic import ValidationError
from scentgraph.schemas.fragrance import FragranceRead
from scentgraph.schemas.scentprint import ScentprintRequest


def test_fragrance_schema_accepts_valid_record() -> None:
    item = FragranceRead(id=1, brand_id=1, name="Example", slug="example", source_confidence=0.8)
    assert item.source_confidence == 0.8


def test_schema_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        FragranceRead(id=1, brand_id=1, name="Example", slug="example", source_confidence=2)


def test_scentprint_rejects_unknown_dimensions() -> None:
    with pytest.raises(ValidationError):
        ScentprintRequest(preferences={"unknown": 0.5})
