# Supplier source drop — 2026-04-26

This directory is the canonical input location for the dated supplier-first staging batch. Source CSV/XLS/XLSX files are read in place, hashed, validated, and converted to `supplier_imported` staging rows.

The source files were not present in the repository workspace when this workflow was implemented. No supplier rows have therefore been fabricated or copied from templates. Add the original supplied files here without editing them, then run:

```bash
python scripts/import_supplier.py data/imports/supplier-2026-04-26 \
  --supplier-name "<supplier name>" \
  --output staging/supplier-2026-04-26.json \
  --report staging/supplier-2026-04-26-report.json
```

Generated rows are staging evidence only. They are never approved catalogue records and must proceed through candidate matching and independent enrichment review.
