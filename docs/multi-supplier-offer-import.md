# Multi-supplier offer import

Supplier offers are private commercial availability records. They are deliberately separate from
public fragrance catalogue records: many suppliers may offer the same fragrance, while the
fragrance has one approved public identity. An offer can link to an existing match candidate or an
already-approved catalogue fragrance, but it cannot create a fragrance profile or bypass the
normal enrichment, human review, and catalogue-promotion workflow.

## Formats and mapping

The existing format maps `BRAND NAME` to the raw brand/name identity, `ORI` to the supplier
reference and candidate hint, and retains the remaining commercial columns only in private fields.
The Fatma layout maps `BRAND` and `NAME` to identity, while its code and monetary columns remain
private. Repeated headings and section rows are removed. A section such as “ALL PRICE 1 KGS” sets
the following offers' `price_basis` to `1kg`; that basis is commercial metadata and is never
published.

Automatic format detection is available, or callers can select `existing_supplier` or `fatma`.
Names are normalised without replacing the raw provenance. Exact duplicate rows are marked
`rejected_duplicate`; name variants, absent supplier identifiers, and suspicious numeric values are
reported for review rather than silently promoted.

## Privacy boundary

Raw files, staged rows, reports, supplier identifiers, tariff identifiers, availability, amounts,
currencies, price bases, and private notes stay below `data/private/`, which is gitignored. Public
samples contain fictional identity and workflow fields only. Default HTTP list, detail,
catalogue-link, comparison, and import responses are allowlisted and contain no commercial values.
All supplier-offer routes are internal and protected by the private API-key dependency.

## Matching and comparison

Matching uses normalised brand, name, and, when present, reference identity. A reference raises
confidence; Fatma-style rows without one remain lower-confidence and normally require human
review. Matches only attach provenance-bearing offers to records that already exist. They never
create a public record.

Private comparison groups availability from multiple suppliers around the same candidate or
catalogue identity. Detailed commercial comparisons are written only to private reports; API and
console output outside that boundary contains counts. These records support internal buying
decisions now and may later support Maison Obsidian sourcing, without entering Maison's public API
or becoming descriptive fragrance content.

## Commands

```bash
python scripts/import_supplier_offers.py data/private/imports/offers.csv \
  --supplier-name "Internal supplier label" --supplier-format auto
python scripts/compare_supplier_offers.py data/private/staging/supplier_offers/*.json
python scripts/audit_supplier_offers.py
```
