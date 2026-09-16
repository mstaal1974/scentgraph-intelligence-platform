# Supplier Import Workflow

The supplier price list is the primary source of commercial availability, but the original file is confidential operational input. The canonical local input is `data/private/imports/supplier-2026-04-26/`, which is excluded by `.gitignore`. `AROMATWIN_PRIVATE_IMPORT_ROOT` may point to an access-controlled mount outside the repository.

The importer discovers CSV/XLS/XLSX files, hashes the original bytes, and derives a stable batch ID from the supplier, directory, file names, and hashes. It preserves raw fields and source row coordinates locally, normalises matching fields, detects TOP/SUPER/LZ variants, and finds duplicates within and across files.

Validation and staging artifacts default to `data/private/staging/`, which is also ignored. If any file fails validation, the entire batch is rejected and only a local error report is produced. Successful rows receive `supplier_imported` and `catalogue_promotion_allowed=false`; importing never creates or updates an approved brand or fragrance.

Public examples are identity-only fictional data under `data/samples/`. They must not include price, cost, currency, quantity, stock, SKU, supplier-code, or commercial-term columns. Run `python scripts/audit_supplier_data.py` before committing to detect tracked raw imports, tracked private paths, and unsafe public-sample headers.
