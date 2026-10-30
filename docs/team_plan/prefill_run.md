# Pre-fill run: everyone runs Gemini on their own share

**Goal:** a first draft record (schema 0.1) for all 426 reasoned cases by running Gemini Flash Lite in parallel, one share per person, each on their own free API key. One share is about one day's free quota and takes about an hour. These drafts are **not gold**: they are what we review next.

## Who runs what
The shares are listed in [`data/splits/prefill_shares.csv`](../../data/splits/prefill_shares.csv) (column `share`). Each share has the same number of cases and about the same number of pages, with a mix of courts. Telangana is left out because of its bad OCR. The split was made by [`scripts/make_prefill_shares.py`](../../scripts/make_prefill_shares.py): do not re-run it, because the shares must not change.

| Share | Person | Cases | Pages | Branch |
|---|---|---|---|---|
| `r1` | Role 1 (Neill) | 106 | 968 | `prefill-r1` |
| `r2` | Role 2 | 106 | 964 | `prefill-r2` |
| `r3` | Role 3 | 107 | 964 | `prefill-r3` |
| `r4` | Role 4 | 107 | 960 | `prefill-r4` |

You never type a case range: the script reads your share from the CSV.

## Steps (replace `r2` with your share everywhere)

**1. Get the latest code and make your branch**
```
git checkout main
git pull
git checkout -b prefill-r2
```

**2. Setup (once)**
- Python 3.10 or newer: `pip install -r requirements.txt`
- `pdftotext` (from Poppler) must be on your PATH:
  - Ubuntu: `sudo apt install poppler-utils`
  - Mac: `brew install poppler`
  - Windows: `conda install -c conda-forge poppler`, or download a Poppler for Windows build and add its `bin` folder to PATH. Check by running `pdftotext -v`.

On Windows, use `python` where these steps say `python` (not `python3`). The commands are otherwise the same in PowerShell.

**3. Your own Gemini key (once)**
1. Go to https://aistudio.google.com/apikey and click "Create API key". The free tier is enough, so no billing is needed.
2. Copy `.env.example` to `.env` in the repo root, and paste your key after `GEMINI_API_KEY=`. Leave `GEMINI_MODEL=gemini-3.5-flash-lite` and `GEMINI_RPM=12` as they are.
3. Test it with `python -m src.common.llm ping gemini`. It should print a small JSON with `"days": 29`.

`.env` is in `.gitignore`. Never commit it and never paste your key into chat or docs.

**4. Download the PDFs (about 1 minute)**
```
python scripts/fetch_data.py --reasoned-only
```

**5. Run your share**
```
python -m src.prefill.prefill --share r2
```
- It prints one line per case, then a summary:
  - `ok`: the record passed all checks.
  - `saved, flag for review`: some quotes weren't found word for word, or a rule check failed. This is fine; the review step fixes it.
  - `FAILED` / `SKIPPED`: see Problems below.
- The run makes about 215 calls and takes about 45–60 minutes. You can leave it running.
- If it says `STOPPED` (daily quota used up) or you close the laptop, **run the same command again later**. Finished cases are skipped, so nothing is lost or paid for twice. The free quota resets daily.
- Output goes to `data/prefill/v1/<cnr>.json`, one file per case. Each file records the model and `prompt_version`.

**6. Commit only your output, push, open a pull request**
```
git add data/prefill/v1/
git commit -m "Pre-fill share r2"
git push -u origin prefill-r2
```
Then open a pull request into `main` on GitHub. Everyone writes different files, so the four pull requests merge without conflicts.

## Rules
- **Don't change the code or the prompt on this branch.** Everyone must run the same prompt, or the drafts can't be compared. If something breaks, tell Neill; the fix goes into `main` and you pull it.
- **Don't edit the JSON by hand now.** Corrections happen in the review step, so we can measure how often the model was wrong.
- Stick to your share. If you finish early and someone is stuck on quota, they can send you their leftover cases, and you run them with `python -m src.prefill.prefill <cnr> <cnr> ...`.

## Problems
| Message | What to do |
|---|---|
| `Set GEMINI_API_KEY in .env` | Step 3 |
| `pdftotext: not found` / `No such file` | Step 2 (Poppler) |
| `SKIPPED (no PDF ...)` | Step 4, then run again |
| `STOPPED: gemini HTTP 429 ...` | Daily or per-minute quota hit; run again later (or the next day) |
| `FAILED: facts: ...` | The model gave broken output twice; run again (it retries). If the same case fails again, leave it and tell Neill |
| A very long judgment takes minutes | Normal: a few judgments are over 100 pages |

## What comes next
Review: each person checks their own share's drafts.
- **Always check findings** (`defect_found` / `defect_rejected` / `not_decided`). On hard cases the model's answer can change from one run to the next.
- **Quick-check facts.** In the pilot, Flash Lite never got a stated fact wrong, but it sometimes left one empty.
- **Fix every quote flagged in `checks`.**

A second person double-checks a sample. Instructions and the review tool: [`review_guide.md`](review_guide.md). The decided labelling rules are in [`schema_proposal_v0_1.md`](schema_proposal_v0_1.md) (rules 1–13 and the "Judgement calls" section).
