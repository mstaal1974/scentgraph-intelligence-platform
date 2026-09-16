# Public Data and Templates

Everything tracked under `data/` must be safe for a public repository. `samples/supplier_identity_sample.csv` is deliberately identity-only and contains no supplier prices, quantities, stock, SKUs, confidential codes, or commercial terms.

Raw supplier catalogues are not public fixtures. Store them only beneath the gitignored `data/private/imports/` path. Store generated staging rows and validation reports beneath `data/private/staging/`. Never force-add either path.

The remaining CSVs document canonical catalogue and review shapes. They are not authoritative fragrance claims. Validate public files with:

```bash
python scripts/validate_data.py data
python scripts/audit_supplier_data.py
```
