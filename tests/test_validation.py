from pathlib import Path

from scripts.validate_data import validate


def test_repository_csv_headers_are_valid() -> None:
    assert validate(Path("data")) == []
