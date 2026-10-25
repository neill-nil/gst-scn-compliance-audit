# Data

Source: AWS Open Data `s3://indian-high-court-judgments` (official eCourts PDFs, CC-BY-4.0).

## Get the data (teammates start here)
Needs Python 3 and `pdftotext` (`sudo apt install poppler-utils`). No other packages.
```
python scripts/fetch_data.py --reasoned-only   # ~430 reasoned judgments, about 1 minute
python scripts/fetch_data.py                   # all ~4,900 in-scope cases, about 10–15 minutes
```
Every PDF is checked against the sha256 in the manifest.

## Layout
| Path | Contents | In git |
|---|---|---|
| `manifests/screened.csv` | every screened case (20,087): CNR, court, S3 key, sha256, bucket, flags, exclusion reasons, rule version | yes |
| `splits/schema_pilot.csv` | 19 reasoned cases for the schema/taxonomy session (excluded from the test set) | yes |
| `text/<court_code>/<cnr>.txt.gz` | extracted text, in-scope non-duplicate cases | no |
| `raw/<court_code>/<cnr>.pdf` | PDFs of reasoned cases | no |
| `gold/` | human-verified records (coming) | yes |

Buckets: `out_of_scope`, `not_final`, `no_procedural_defect_argued`, `remand_or_short`, `reasoned`.
`reasoned` is a keyword-rule tag (~75% precision); it is confirmed by LLM triage and human annotation before anything becomes gold.

## Rebuild from scratch (only needed if screening rules change)
Needs `pip install -r scripts/requirements.txt`.
```
python scripts/find_candidates.py cands.parquet 2024 2026
python scripts/screen_fulltext.py cands.parquet work <court_code> ...
python scripts/build_store.py data work/text work/screen.jsonl
```
