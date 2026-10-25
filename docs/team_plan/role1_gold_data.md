# Role 1 — Gold data pipeline (owner: Neill)

**Goal:** turn the ~4,900 screened in-scope judgments into a verified gold set: 60–80 cases by 30 Oct, 150 by the final. Every value in it is backed by a verbatim quote that a program has checked, and every case is confirmed by a human.

**Give your AI:** this file, [`contracts.md`](contracts.md), [`../../data/README.md`](../../data/README.md), and the scripts in `scripts/` (especially `clean_segment.py` and `screen_fulltext.py`).

## Inputs you already have
- `data/manifests/screened.csv` (20,087 cases, buckets and flags)
- `data/text/` (in-scope texts) and `data/raw/` (429 reasoned PDFs), via `python scripts/fetch_data.py`
- `scripts/clean_segment.py` (removes boilerplate, splits numbered paragraphs)
- `data/splits/hand_labels_reasoned.csv`: 22 cases labelled by hand as reasoned / not reasoned, with the reason (used to check triage)

## Outputs you deliver
| Output | Path | Who needs it | Due |
|---|---|---|---|
| Shared model client | `src/common/llm.py` | R2, R4 | 26 Oct night |
| Triage results | `data/interim/triage.jsonl` | you (candidate list) | 27 Oct |
| Splits | `data/splits/{dev,test,heldout,precedent}.txt` | R3 (case-law index), R4 | 27 Oct |
| Pre-filled records | `data/interim/prefill/<cnr>.json` | everyone (review) | 28 Oct |
| Review app | `review_app/` | everyone | 28 Oct |
| Gold records | `data/gold/records.jsonl` | R2, R4 | 30 Oct |
| Datasheet (data funnel and error rates) | `docs/datasheet.md` | write-up | 31 Oct |

## Steps

### Sun 26 Oct
1. **Shared model client `src/common/llm.py`** (push tonight; others depend on it).
   - One function: `complete(model: str, messages: list, json_schema: dict | None = None, temperature: float = 0, seed: int = 0) -> dict` returning `{"text", "json", "tokens_in", "tokens_out", "seconds", "model"}`.
   - Backends: (a) any OpenAI-compatible server (vLLM or Ollama serving Qwen3-8B or Gemma 3 on Kaggle or locally), set by `LLM_BASE_URL`; (b) the chosen frontier API, key in `.env`.
   - Retries with backoff on rate limits; a disk cache keyed by a hash of (model, messages, schema, seed) so re-runs cost nothing; append every call to `runs/llm_calls.jsonl` for cost reporting.
   - For Qwen3, disable thinking mode for JSON calls. Validate JSON against the schema; on failure retry once with the error message, then return `json: null`.
2. **Triage script `src/triage/triage.py`** (pipeline stage 3b).
   - Input: every case in `reasoned` or `remand_or_short` (about 4,000), non-duplicate.
   - For each: run `clean_segment.py` logic; send the model the cause title, the first 3 paragraphs, the last 5 paragraphs, and any paragraph containing "violation", "sustain", "75(4)", "169", "limitation", "time-barred", "signed".
   - Ask: is this a s.73/74 demand proceeding; does the court itself rule on any procedural defect; for each, the defect type (enum in `contracts.md`), the finding, and the court's sentence as a verbatim quote.
   - Check each quote appears exactly (after whitespace normalisation) in the text; set `quote_verified`.
   - Model: Qwen3-8B on Kaggle (free, no limits).
3. Read your 5 pilot cases (rows 1–5 of `data/splits/schema_pilot.csv`) and note facts, defects and findings for the meeting.

### Mon 27 Oct
4. **Check the triage** on the 19 pilot cases plus the 22 cases in `data/splits/hand_labels_reasoned.csv`: precision and recall of "reasoned", and agreement on defect types. If precision is below ~0.8, adjust the prompt once and re-run.
5. **Run triage on all ~4,000** (Kaggle, a few hours; run in batches, the cache makes it resumable).
6. **Near-duplicate removal:** MinHash on word 5-grams of the body text (e.g. the `datasketch` package), threshold ~0.8; keep one case per cluster. This catches batch judgments filed under many case numbers (Telangana, Madras pairs). Also cap the Delhi "six categories" template orders at 5 in test.
7. **Splits:**
   - `dev`: the 19 pilot cases plus the 22 hand-labelled cases (both are used for tuning, so they can never be test cases).
   - `heldout`: all reasoned cases from courts other than Madras and Delhi (Allahabad, Karnataka, Bombay, Calcutta, Orissa, Patna and others, roughly 80), unless the team decides otherwise in the meeting.
   - `test`: confirmed-reasoned Madras and Delhi cases, stratified by defect type.
   - `precedent`: every other in-scope case (remands included). Never overlaps with dev, test or heldout.
   - Push today; role 3 builds the case-law index from `precedent.txt`.
8. **Schema meeting** (all). Afterwards, check that the frozen `contracts.md` covers everything the parser must produce.

### Tue 28 Oct
9. **Parser pre-fill `src/prefill/prefill.py`** (pipeline stage 6), in the style of the IntrAgent paper.
   - Clean and segment each judgment; tag each paragraph's role (cause title, notice details, history, submissions, analysis, order) with one cheap model call.
   - For each field group (`proceeding`, `notice`, `events`, `order`, `defects_argued`, `outcome`): rank paragraphs by likely relevance, read them in order, extract the fields with verbatim quotes and paragraph numbers, then run a sufficiency check ("is every field supported by the quotes? if not, set it to null"). The model may answer "not stated"; it must never guess.
   - Mark quoted text from other judgments (long passages in quotation marks citing another case) so their facts and outcomes are never taken as this case's.
   - Run two different models: model A = frontier API, model B = Gemma 3 12B on Kaggle.
   - Input: about 120 test candidates (to end with 60–80 after review).
10. **Validators `src/prefill/validate.py`** (pipeline stage 7). For every field:
    - quote appears verbatim in the judgment text;
    - the value can be re-derived from the quote (dates parsed by regex from the quote must equal the value; section numbers must appear in the quote);
    - dates in a sensible order (notice ≤ reply due ≤ hearing ≤ order) and enums valid;
    - models A and B agree.
    Assign each field a tier: **auto-accept** (all checks pass), **quick check** (any check fails), **always human** (`defects_argued` and `outcome`, always).
11. **Review app `review_app/`** (Streamlit). Left pane: the judgment's paragraphs. Right pane: each field with its value, its quote highlighted in the left pane, and its tier. Buttons: accept, edit, set to null; a first question per case: "in scope and reasoned? yes/no". Saves to `data/gold/annotations/<reviewer>/<cnr>.json`.

### Wed 29 – Thu 30 Oct
12. Assign cases to reviewers (everyone reviews ~2 h/day). **30 cases are reviewed by two people** for the agreement score.
13. Merge reviews into `data/gold/records.jsonl` (`status: gold`). Disagreements on the 30 shared cases: discuss, record the final answer, keep both originals for the kappa calculation.
14. **Audit the auto-accepted fields:** randomly sample 60 auto-accepted fields and check them by hand. Report the error rate with its 95% upper bound (0 errors in 60 gives about 5%).

### Fri 31 Oct
15. **Datasheet `docs/datasheet.md`**: the funnel (20,087 screened → in scope → reasoned by rules → confirmed by triage → gold), per-court counts, rule precision/recall from hand checks, triage precision/recall, auto-accept audit error rate, reviewer agreement, known issues (consent remands, OCR courts, templates, contested law).
16. Data section of the submission.

## Depends on / blocks
- **Needs:** the frozen schema (27 Oct, all); the frontier API choice (team, 26 Oct).
- **Blocks:** R2 and R4 (llm.py, 26 Oct), R3 (precedent split, 27 Oct), everyone (review, 29 Oct), all evaluation (gold, 30 Oct).

## After the mid (1–15 Nov)
- Scale gold to 150 test + the held-out court set.
- Extraction gold for RQ2: ~100 remand cases with only `proceeding`/`notice`/`events`/`order` (no findings needed).
- Training data for the LoRA extractor: combine role 3's synthetic notices with non-test real records.
- Optional: re-check rule misses by sampling 50 `out_of_scope` cases (miss-rate estimate promised in the proposal).

## Done when (31 Oct)
- `data/gold/records.jsonl` has ≥ 60 cases with every quote verified.
- Agreement (Cohen's kappa) reported on 30 double-reviewed cases.
- Datasheet written with all the numbers above.
