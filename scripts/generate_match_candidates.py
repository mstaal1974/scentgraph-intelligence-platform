#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict
from pathlib import Path
from aromatwin.services.matching import candidate_from_supplier
from aromatwin.services.supplier_importer import prepare_supplier_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--supplier-name", required=True)
    parser.add_argument("--output", type=Path, default=Path("match-candidates.json"))
    args = parser.parse_args()
    result = prepare_supplier_file(args.input, args.supplier_name)
    candidates = [asdict(candidate_from_supplier(row)) for row in result.rows]
    args.output.write_text(json.dumps(candidates, indent=2) + "\n")
