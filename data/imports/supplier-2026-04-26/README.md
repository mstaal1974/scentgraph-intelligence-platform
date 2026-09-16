# Supplier import audit — 2026-04-26

This tracked directory was reviewed during supplier-import hardening. It contained no supplier CSV or spreadsheet: only this documentation file was committed. A separate public template elsewhere in the repository did contain example cost and supplier-code columns; that template has been removed and replaced with the identity-only sample at `data/samples/supplier_identity_sample.csv`.

Do **not** add raw supplier files here. Confidential source files—including prices, quantities, stock positions, supplier codes, and commercial terms—belong under the gitignored local path:

```text
data/private/imports/supplier-2026-04-26/
```

The importer stages those private files locally. Generated staging output and validation reports must also remain under ignored local paths. Staged rows retain `supplier_imported` status and are never approved catalogue records.
