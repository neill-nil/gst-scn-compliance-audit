# NoticeCheck — team plan (mid submission 31 Oct, final 15 Nov)

**How to use this folder:** read this page, then your own role file. When you work with an AI assistant, give it three files: your role file, [`contracts.md`](contracts.md) (the shared data formats) and [`../../data/README.md`](../../data/README.md).

| Role | File | Owner |
|---|---|---|
| 1. Gold data pipeline | [role1_gold_data.md](role1_gold_data.md) | Neill |
| 2. NoticeCheck system (the agent) | [role2_noticecheck_system.md](role2_noticecheck_system.md) | _fill in_ |
| 3. Legal corpus, tools, synthetic data | [role3_corpus_tools.md](role3_corpus_tools.md) | _fill in_ |
| 4. Schema, guidelines, evaluation, baselines | [role4_schema_eval.md](role4_schema_eval.md) | _fill in_ |

The TA wants the **major chunk of the whole project in the 31 Oct submission**: a working end-to-end system and first real results, not just data.

---

## 1. Already done

**Data source.** We use the AWS Open Data bucket of official High Court judgments from eCourts (`s3://indian-high-court-judgments`, CC-BY-4.0, free, no login). We are not waiting for the Indian Kanoon API; if it is approved, it is used only for finding extra cases and cross-checking, never for gold labels.

**Screening (done for all 24 High Courts, decisions 2024–2026).**

| Step | Count |
|---|---|
| Cases with GST terms in title/opening text | 20,087 |
| Out of scope (bail, detention, registration, refunds, appeal-only, pre-GST, withdrawn, etc.) | 13,258 |
| Duplicate judgments (same text, different case numbers) | 1,701 |
| **In scope**: GST demand proceedings under s.73/74 | **~4,900** |
| of which tagged **reasoned** (court actually rules on a procedural defect) | **429** (Madras 221, Delhi 117, others 91) |
| of which remand/short order (court sends it back without ruling) | 3,657 |

The "reasoned" tag comes from keyword rules and is about 75% accurate (checked by hand on 22 cases), so it is confirmed by an LLM triage step and by humans before anything becomes gold. Realistic pool of truly reasoned judgments: about 320–350.

**Key findings that shape the plan**
- Most GST court orders are remands "by consent" or "one more chance" that never decide whether the defect existed. Our finding labels are therefore `defect_found`, `defect_rejected`, `not_decided`.
- Remand cases are **not** used as gold for "can't tell". The "can't tell" test is built from reasoned cases by hiding facts (for example, giving only the notice).
- Telangana PDFs have bad OCR text; they are excluded from gold.
- Many Delhi orders reuse one template; we cap how many go into the test set.
- Live contested law: validity of the time-limit extension notifications (pending in the Supreme Court) and consolidated multi-year notices. The system should flag these as contested, not decide them.

**Code in the repo (`scripts/`)**
| Script | What it does |
|---|---|
| `fetch_data.py` | **Teammates start here.** Downloads the data listed in the manifest, checks hashes |
| `find_candidates.py` | Finds GST cases in the bucket's metadata |
| `screen_fulltext.py` | Applies scope rules to the full text, tags buckets |
| `clean_segment.py` | Removes court boilerplate (deletion only) and splits into numbered paragraphs |
| `build_store.py` | Builds `data/` from screening results |
| `survey_pdfs.py` | Text-quality survey |

**Data in the repo**
- `data/manifests/screened.csv`: every screened case with bucket, flags and reasons.
- `data/splits/schema_pilot.csv`: 19 reasoned cases for the schema session (become the dev set; never test).
- `data/splits/hand_labels_reasoned.csv`: 22 cases labelled by hand as reasoned or not, used to check the triage (also dev; never test).
- Text and PDFs are downloaded locally with `fetch_data.py` (not in git).

---

## 2. Timeline

| Date | Everyone | Milestone |
|---|---|---|
| **Sun 26 Oct** | Pull repo, run `python scripts/fetch_data.py --reasoned-only`, read your pilot cases ([`pilot_reading.md`](pilot_reading.md)), start your role's "can start now" steps | — |
| **Mon 27 Oct** | 1-hour schema meeting (led by role 4) | **Schema v0 frozen by evening** (hard deadline) |
| **Tue 28 Oct** | Role work | Parser pre-fills ~100 cases; system runs end-to-end on pilot cases; eval harness runs |
| **Wed 29 – Thu 30 Oct** | **Each person reviews pre-filled cases ~2 h/day** | 60–80 gold cases (30 reviewed by two people); all systems run on gold |
| **Fri 31 Oct** | Write-up | **Mid submission**: results, ablations started, error analysis |
| 1–15 Nov | Role work | Scale to 150 gold, LoRA extractor, full ablations, held-out court, judge validation, paper |

**Pilot reading:** the case list per person, reading tips, a glossary, a worked example and the note template are in [`pilot_reading.md`](pilot_reading.md). Bring your notes to the meeting.

---

## 3. Workflow and dependencies

```
                       ┌────────────────────────── Role 3: corpus + tools ───────────────────────────┐
                       │ statute files (26) -> lookup/search (27) -> limitation calc (27) ->          │
                       │ case-law search (28, needs precedent list from R1) -> tool specs (28)  ──────┼──> R2 real tools (29)
                       └──────────────────────────────────────────────────────────────────────────────┘
 R1 llm.py (26) ──┬──> R1 triage (26–27) ──> R1 candidate gold list + splits (27) ──┐
                  ├──> R2 system skeleton (26–28) ─────────────────────────────────┐ │
                  └──> R4 baselines B1/B2 (28) ───────────────────────────────┐    │ │
                                                                               │    │ │
 SCHEMA v0 frozen (27, all, led by R4) ──┬──> R1 parser pre-fill (28) ──> REVIEW by all (29–30) ──> GOLD (30)
                                         ├──> R2 defect checks (28)                                      │
                                         ├──> R4 B0 + input builder (28) ──> R4 eval harness ready (28) ─┤
                                         └──> R3 synthetic generator (30 →)                              v
                                                                              ALL SYSTEMS RUN ON GOLD (30) -> RESULTS (31)
```

**Critical path:** schema (27) → pre-fill (28) → review (29–30) → gold (30) → evaluation runs (30) → write-up (31). If any of these slip, the submission slips. Everything else has slack.

**What blocks whom**
| Item | Owner | Due | Blocks |
|---|---|---|---|
| `src/common/llm.py` (shared model client) | R1 | 26 Oct night | R1 triage, R2 system, R4 baselines |
| Schema v0 frozen in `contracts.md` | R4 + all | 27 Oct evening | R1 pre-fill, R2 defect checks, R4 B0/input builder, R3 synthetic data |
| `data/splits/` (dev / test / precedent lists) | R1 | 27 Oct | R3 case-law search (must exclude test cases) |
| Tool functions with the signatures in `contracts.md` | R3 | 28 Oct | R2 switching from mock tools to real tools |
| Pre-filled cases in `data/interim/prefill/` | R1 | 28 Oct | Review by everyone |
| Eval harness | R4 | 28 Oct | Results |
| Gold records `data/gold/records.jsonl` | R1 (all review) | 30 Oct | All evaluation |

**Fallback:** if fewer than 60 gold cases exist on 30 Oct evening, evaluate on whatever is reviewed (minimum 40) and say so in the submission. Do not evaluate on the 19 pilot cases; they are used to write the guidelines.

---

## 4. Shared rules (tell your AI these)

1. **Court PDFs are the only source of truth for gold labels.** Never use Kanoon, Taxscan, LiveLaw or a model's memory as a label.
2. **Gold labels never come from the system under test.** The dataset parser (role 1) uses different, stronger models than the NoticeCheck system (role 2).
3. **Every extracted value carries a verbatim quote and paragraph number.** A program checks that the quote appears exactly in the judgment text. No verified quote, no gold.
4. **Cleaning only deletes boilerplate lines.** Never rewrite judgment text.
5. **Scope:** CGST/SGST s.73/74 demand proceedings, tax periods up to FY 2023-24. Section 74A (FY 2024-25 onward) is out of scope.
6. **Test-set cases must never appear** in the precedent corpus, few-shot examples, prompts or training data.
7. **No data in git** except `data/manifests/`, `data/splits/`, `data/gold/`. No API keys in git: use a `.env` file (already ignored).
8. **Every model call is logged**: model, tokens, seconds. We report cost per configuration.

## 5. Repo conventions
| Folder | Owner |
|---|---|
| `src/common/` (model client, shared IO) | R1 |
| `src/triage/`, `src/prefill/`, `review_app/` | R1 |
| `src/noticecheck/` | R2 |
| `corpus/`, `src/tools/`, `src/synthetic/` | R3 |
| `guidelines/`, `eval/`, `src/baselines/` | R4 |

- Branch per person (`r1-data`, `r2-system`, `r3-tools`, `r4-eval`); open a pull request into `main` at least once a day; keep pull requests small.
- Python 3.11+. Each module runnable as `python -m src.<module>`. JSONL for all records. Add packages to the root `requirements.txt`.
- Fix random seeds; write config files for every experiment run (`configs/*.yaml`).

## 6. Models
| Use | Model | Where |
|---|---|---|
| NoticeCheck system, baseline B1, triage | Qwen3-8B (4-bit), Gemma 3 4B fallback | Kaggle free GPU (each person has ~30 GPU-h/week) or local |
| Parser pre-fill, model A (gold data) | one free-tier frontier API (team picks; key in `.env`) | API |
| Parser pre-fill, model B (agreement check) | Gemma 3 12B (4-bit) | Kaggle |
| Baseline B2 | the same frontier API, statute pasted in | API, small budget |
| LoRA extractor (after mid) | Qwen3-8B + QLoRA | Kaggle |

For Qwen3, turn off "thinking" mode when you need plain JSON output.
