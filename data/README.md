# Data

Source: AWS Open Data `s3://indian-high-court-judgments` (official eCourts PDFs, CC-BY-4.0).

| Path | Contents | In git |
|---|---|---|
| `manifests/screened.csv` | every screened case: CNR, court, S3 key, sha256, bucket, flags, exclusion reasons, rule version | yes |
| `text/<court_code>/<cnr>.txt.gz` | extracted text, in-scope non-duplicate cases only | no |
| `raw/<court_code>/<cnr>.pdf` | frozen PDF copies of reasoned cases, sha256-verified | no |
| `gold/`, `splits/` | human-verified records and split lists (coming) | yes |

Buckets: `out_of_scope`, `not_final`, `no_procedural_defect_argued`, `remand_or_short`, `reasoned`.
Court codes -> names are in the `court_name` column of the manifest.

Rebuild locally (needs `pip install -r scripts/requirements.txt` and poppler-utils):
```
python scripts/find_candidates.py cands.parquet 2024 2026
python scripts/screen_fulltext.py cands.parquet work <court_code> ...
python scripts/build_store.py data work/text work/screen.jsonl
```
