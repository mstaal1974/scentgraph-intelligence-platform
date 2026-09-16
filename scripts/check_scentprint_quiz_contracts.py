#!/usr/bin/env python3
"""Validate the canonical Scentprint quiz contract."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aromatwin.services.scentprint_quiz_contracts import (  # noqa: E402
    get_quiz_contract,
    validate_quiz_contract,
)


def main() -> int:
    contract = get_quiz_contract()
    errors = validate_quiz_contract(contract)
    if errors:
        print("Scentprint quiz contract validation failed:\n- " + "\n- ".join(errors))
        return 1
    print(f"Scentprint quiz contract {contract['quiz_contract_version']} is public-safe "
          f"({len(contract['questions'])} questions; no open text).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
