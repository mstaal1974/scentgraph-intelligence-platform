# Supplier Import Workflow

The supplier price list is the primary source of commercial availability. The canonical dated input is `data/imports/supplier-2026-04-26/`. The importer discovers CSV/XLS/XLSX files in that directory, hashes the original bytes, and derives a stable batch ID from the supplier, directory, file names, and hashes.

For every row it preserves raw `BRAND`, `NAME`, `ORI`, `CN CODE`, `QTY`, `AED`, and `USD`, source file, original spreadsheet/CSV row number, and batch identity. Headers are whitespace/case normalised before validation. Blank rows are ignored; missing brand/name values and invalid numeric fields are reported with their source location.

Names are normalised for matching, TOP/SUPER/LZ markers are separated, and duplicates are detected both within each file and across the dated batch. File-level and aggregate counts, hashes, variants, duplicates, and errors belong in the validation report.

Every output row is assigned `supplier_imported`, with `catalogue_promotion_allowed=false`. Importing never creates or updates brands or fragrances. The only next step is candidate matching, followed by independent verification and enrichment review.

If any source file fails validation, the batch is rejected as a unit: no partial staging output is written, `status=validation_failed`, and the report identifies each invalid file while keeping catalogue promotion disabled.
