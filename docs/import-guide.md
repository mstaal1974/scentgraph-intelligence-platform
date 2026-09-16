# Supplier Import Guide

Supplier files establish availability and are processed from
`data/private/imports/supplier-2026-04-26/`. This ignored directory is the default local input;
an access-controlled path outside the repository may also be used. Keep source files unchanged so
their SHA-256 fingerprints remain auditable.

Required columns are `BRAND`, `NAME`, `ORI`, `CN CODE`, `QTY`, `AED`, and `USD`. CSV, XLS, and XLSX inputs are accepted; unrelated files are ignored.

```bash
python scripts/import_supplier.py data/private/imports/supplier-2026-04-26 \
  --supplier-name "Supplier" \
  --output staging/supplier-2026-04-26.json \
  --report staging/supplier-2026-04-26-report.json
```

The staging output preserves raw values and adds normalised matching fields, variant markers, duplicate flags, provenance coordinates, and `supplier_imported` status. `ORI` is only a supplier-provided identity hint. Neither it nor any other supplier row verifies a clone relationship or authorises a catalogue record.

The report always states `catalogue_promotion_allowed=false`. Candidate matching and independently sourced human-reviewed enrichment are mandatory before approval.
# Multi-supplier offers

Private commercial lists from multiple suppliers are imported with
`scripts/import_supplier_offers.py`; see [the offer import guide](multi-supplier-offer-import.md).
Do not place source lists or generated staging/report artifacts outside `data/private/`.
