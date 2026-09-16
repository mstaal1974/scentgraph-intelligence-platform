#!/usr/bin/env python3
import argparse
import json
from dataclasses import fields
from decimal import Decimal
from pathlib import Path

from aromatwin.services.supplier_offer_importer import SupplierOffer
from aromatwin.services.supplier_offer_matching import compare_supplier_offers


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare private staged supplier offers")
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/private/reports/supplier-offer-comparison.json"))
    args = parser.parse_args()
    if Path("data/private").resolve() not in args.output.resolve().parents:
        raise SystemExit("Comparison reports containing commercial data must be under data/private/")
    names = {field.name for field in fields(SupplierOffer)}
    offers = []
    for source in args.inputs:
        for item in json.loads(source.read_text(encoding="utf-8")):
            for key in ("quantity_private", "price_aed_private", "price_usd_private"):
                if item.get(key) is not None:
                    item[key] = Decimal(str(item[key]))
            offers.append(SupplierOffer(**{key: value for key, value in item.items() if key in names}))
    summary = compare_supplier_offers(offers)
    report = {"groups": summary, "offers": [item for item in json.loads(json.dumps(
        [offer.__dict__ for offer in offers], default=str))]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"offer_count": len(offers), "group_count": len(summary)}))


if __name__ == "__main__":
    main()
