# Supplier Import Guide

Supplier data enters staging and never overwrites canonical records directly. Operators must retain permitted provenance and review duplicate and variant warnings.

## Expected CSV

Required headers:

```csv
brand_name,fragrance_name,concentration,product_type,size_ml,sku,price,currency,source_reference
Example Brand,Example Scent,eau de parfum,spray,50,EX-50,79.00,GBP,catalogue-row-1
```

Run `python scripts/import_supplier.py input.csv --source-name "Supplier" --output staging.csv --report report.json`. The pipeline loads CSV, validates headers, normalises names, identifies duplicate keys, preserves concentration variants, emits staging records, and writes a validation report with provenance metadata. Human review and database loading are later phases.
