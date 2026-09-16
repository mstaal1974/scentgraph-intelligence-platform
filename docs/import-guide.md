# Private Supplier Import Guide

Supplier files may contain confidential prices, quantities, supplier codes, stock positions, and commercial terms. They must never be committed to the public repository or copied into public samples.

## Safe local setup

1. Create the ignored directory `data/private/imports/supplier-2026-04-26/`.
2. Copy the original CSV/XLS/XLSX files into that directory without editing them.
3. Confirm Git ignores each file with `git check-ignore -v <path>`.
4. Restrict local permissions where appropriate, for example `chmod -R go-rwx data/private`.
5. Run the importer without overriding its private output defaults:

```bash
python scripts/import_supplier.py \
  --supplier-name "Supplier"
```

Set `AROMATWIN_PRIVATE_IMPORT_ROOT` when private input is mounted elsewhere. If explicit `--output` or `--report` paths are used, keep them outside tracked directories. Do not use `git add -f` on private supplier files.

The raw importer expects `BRAND`, `NAME`, `ORI`, `CN CODE`, `QTY`, `AED`, and `USD`. Those commercial fields stay local. The tracked `data/samples/supplier_identity_sample.csv` contains only fictional `BRAND`, `NAME`, and `ORI` identity hints and is not an importer-ready price list.

Every imported row remains `supplier_imported` with catalogue promotion disabled. Candidate matching and independently sourced human review are required before catalogue approval.
