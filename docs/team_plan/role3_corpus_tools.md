# Role 3 — Legal corpus, tools and synthetic data

**Goal:** give the system the law and the tools it reasons with. That means a frozen, correctly structured copy of the CGST Act, Rules, forms and key circulars; search and lookup over it; a tested deadline/limitation calculator; case-law search over our own precedent collection; and the sandboxed action tool. After that, a generator of synthetic DRC-01 notices for fine-tuning.

**Give your AI:** this file, [`contracts.md`](contracts.md) (section 4 is your interface; it must match exactly), and [`README.md`](README.md) section 4.

**Legal accuracy matters most in this role.** Every provision number, time limit and due date in your code must be checked against the official text, with the source written next to it. If you're unsure, mark it `UNVERIFIED` and tell the team; never let the AI fill in law from memory.

## Outputs you deliver
| Output | Path | Who needs it | Due |
|---|---|---|---|
| Source list (URLs, download dates, hashes, version date) | `corpus/SOURCES.md` | write-up | 26 Oct |
| Structured statute units | `corpus/*.jsonl` | your tools | 27 Oct |
| `statute_lookup`, `statute_search` | `src/tools/statute.py` | R2 | 27 Oct |
| `limitation_check`, `date_diff` + unit tests | `src/tools/limitation.py`, `tests/` | R2, R4 (B0) | 27–28 Oct |
| `caselaw_search` | `src/tools/caselaw.py` | R2 | 28 Oct |
| `record_lookup`, `send_reply` (sandbox) | `src/tools/sandbox.py` | R2 | 28 Oct |
| Function-calling specs | `src/tools/specs.json` | R2 | 28 Oct |
| Statute retrieval evaluation | `eval/retrieval_eval.md` | write-up | 30 Oct |
| Synthetic notice generator | `src/synthetic/` | R1/R2 (LoRA) | starts 30 Oct |

## Steps

### Sun 26 Oct
1. **Collect the official sources** and freeze one version date:
   - CGST Act, 2017 as amended: India Code (indiacode.nic.in).
   - CGST Rules, 2017 with forms (DRC-01, DRC-01A, DRC-06, DRC-07): CBIC GST site (cbic-gst.gov.in) consolidated rules and forms.
   - Notifications extending time limits under s.168A for s.73 (e.g. 13/2022, 9/2023, 56/2023; confirm numbers and contents from the official text), and the notification(s) fixing annual-return due dates for each financial year 2017-18 to 2023-24.
   - CBIC circulars relevant to adjudication, personal hearing, and s.73/74 procedure (list what you include and why).
   - Record URL, download date and SHA-256 for each in `corpus/SOURCES.md`.
2. **Structure the text** into units, one JSON line each:
   `{"ref": "CGST Act s.75(4)", "act": "CGST Act", "chapter": "XV", "section": "75", "subsection": "4", "clause": null, "kind": "subsection|proviso|explanation|rule|form_field|circular_para", "heading": "General provisions relating to determination of tax", "text": "...", "parent_ref": "CGST Act s.75"}`
   Keep provisos and Explanations as their own units, linked to their parent. Spot-check 20 units against the PDF by hand.
3. Read your 5 pilot cases (rows 11–15 of `data/splits/schema_pilot.csv`) and list every provision the courts cite.

### Mon 27 Oct
4. **`statute_lookup(ref)`**: exact match on `ref`, plus tolerant parsing ("s 75(4)", "Section 75 (4)", "sec.75(4) of CGST Act").
5. **`statute_search(query, k)`**: hybrid BM25 + a small embedding model (e.g. `bge-small-en-v1.5`), returning each hit with its parent unit's text (hierarchy preserved, as in the IntrAgent paper). Keep a flag for **flat** search (no parent context, plain chunks) so we can compare them (the RAG ablation).
6. **`limitation_check`**: for each financial year, the annual-return due date (with source); s.73(10) order deadline = 3 years from that date, s.73(2) notice deadline = at least 3 months before the order deadline; s.74(10) = 5 years, s.74(2) = 6 months before (verify all four against the Act). Option `apply_extensions` applies the s.168A notifications for the years they cover, and sets `contested: true` whenever an extension notification changes the answer.
   - **Unit tests** using dates stated in real judgments. Example: Tata Play (Delhi HC, W.P.(C) 4781/2025): FY 2020-21, notice 30 Nov 2024, order 28 Feb 2025; the court held the notice within time. Add at least 5 such cases from the pilot set.
7. **Schema meeting.** Confirm the provision for each defect type in the table in `contracts.md`, and correct it there.

### Tue 28 Oct
8. **`caselaw_search(query, k)`**: paragraph-level index over the texts of cases listed in `data/splits/precedent.txt` (from role 1, 27 Oct); clean them with `scripts/clean_segment.py` first. It must refuse to return any case in `dev`, `test` or `heldout`; add a test that checks this.
9. **`record_lookup`** (reads from the checker input given to it) and **`send_reply`** (returns an error unless `approved=true`; writes only to `runs/sandbox_outbox/`; logs every call, including refused ones).
10. **`date_diff`**, and make every tool return `{"ok": ..., "result" | "error"}` without raising (wrong `ref`, bad dates, unknown year → `ok: false` with a clear message).
11. **`src/tools/specs.json`**: JSON function-calling specs for all tools. Hand over to role 2.

### Wed 29 Oct
12. **Statute retrieval evaluation:** for each gold `defects_argued[].provision` (gold arrives 30 Oct; start with the pilot cases), make a query from the record facts and measure Recall@1/3/5 of the gold provision, for hierarchical vs flat search. Write `eval/retrieval_eval.md`.
13. Review pre-filled cases (~2 h).

### Thu 30 Oct
14. Review pre-filled cases (~2 h).
15. **Start the synthetic generator `src/synthetic/`:** fill the DRC-01 template with random but valid facts (dates, sections, periods, hearing details) to produce (a) the notice text and (b) its correct case record (correct by construction). Plant defects on purpose (hearing "NA", hearing before reply due, notice after the deadline, missing signature line, consolidated years) and record them. Target 1,000–2,000 for training and ~100 stress cases, reported separately from real data.

### Fri 31 Oct
16. Corpus and tools section of the write-up: sources and version date, unit counts, tool list, retrieval results, limitation test results.

## Depends on / blocks
- **Needs:** `data/splits/precedent.txt` (R1, 27 Oct) for case-law search; the frozen schema (27 Oct) for the synthetic generator; gold provisions (30 Oct) for the full retrieval evaluation.
- **Blocks:** role 2's real-tool runs (28–29 Oct); role 4's B0 baseline (it uses `limitation_check`).

## After the mid (1–15 Nov)
- Finish synthetic data; hand to role 1/2 for LoRA training.
- State GST Acts: confirm the provisions mirror the CGST ones for the states in our data; note any differences.
- Add circulars the system cited wrongly in failure cases.

## Done when (31 Oct)
- All tools in `contracts.md` section 4 exist, pass their tests, and never raise.
- `limitation_check` passes ≥ 6 tests taken from real judgments.
- Retrieval Recall@k reported for hierarchical vs flat search.
