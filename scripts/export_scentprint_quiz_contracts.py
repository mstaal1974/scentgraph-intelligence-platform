#!/usr/bin/env python3
"""Export public-safe Scentprint contracts and examples without private records."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from build_scentprint_quiz_samples import SAMPLE_RESPONSES, build  # noqa: E402

from aromatwin.services.scentprint_quiz_contracts import get_quiz_contract  # noqa: E402
from aromatwin.services.scentprint_quiz_results import build_quiz_result  # noqa: E402
from aromatwin.services.scentprint_quiz_scoring import score_quiz_responses  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/samples"))
    parser.add_argument("--format", choices=("json", "csv", "both"), default="both")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    scored = score_quiz_responses("quiz_demo001", SAMPLE_RESPONSES)
    result = build_quiz_result(scored, demo_mode=True)
    if args.format in {"csv", "both"}:
        build(args.output)
    if args.format in {"json", "both"}:
        bundle = {"contract": get_quiz_contract(), "response_example": {
            "scentprint_public_alias": "quiz_demo001", "responses": SAMPLE_RESPONSES},
            "result_example": result}
        (args.output / "scentprint_quiz_contract_export.json").write_text(
            json.dumps(bundle, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Exported public-safe Scentprint contracts to {args.output}")


if __name__ == "__main__":
    main()
