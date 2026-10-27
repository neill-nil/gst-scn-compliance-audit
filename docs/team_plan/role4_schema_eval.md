# Role 4 — Schema, guidelines, evaluation and baselines

**Goal:** own the definitions and the scoring. You freeze the schema the team agrees on, write the annotation guidelines, build the inputs every system sees (with court findings removed), run the baselines, and build the evaluation harness that turns run outputs into the numbers in our submission. By 30 Oct the harness must score every system on the gold set.

**Give your AI:** this file, [`contracts.md`](contracts.md) (you own it), [`README.md`](README.md) sections 2–4, and the assignment's evaluation requirements below.

## What the assignment requires (from the brief, keep these in view)
At least one baseline; a small evaluation set with known ground truth; at least one metric per capability (RAG, reasoning, tool calling, fine-tuning, agentic); an ablation of each capability the research question depends on; tool-call accuracy and an unsafe-action rate; qualitative examples and failure analysis; any LLM judge validated against human labels.

## Outputs you deliver
| Output | Path | Who needs it | Due |
|---|---|---|---|
| Frozen schema v0.1 | `docs/team_plan/contracts.md` | everyone | 27 Oct evening |
| Annotation guidelines | `guidelines/annotation_guidelines.md` | all reviewers | 28 Oct |
| Input builder + leakage test | `src/baselines/inputs.py` | R2, baselines | 28 Oct |
| B0 rule checklist | `src/baselines/b0_rules.py` | results | 28 Oct |
| B1 / B2 runners | `src/baselines/b1_plain.py`, `b2_frontier.py` | results | 29 Oct |
| Evaluation harness | `eval/score.py`, `eval/report.py` | results | 28 Oct (tested on dev) |
| Agreement (kappa) script | `eval/agreement.py` | R1 | 29 Oct |
| Results tables | `docs/results_mid.md` | write-up | 31 Oct |

## Steps

### Sun 26 Oct
1. **Read your pilot cases** (listed in `pilot_reading.md`) and the draft in `contracts.md`. List what the draft can't represent (for example: two notices in one case; a hearing offered but the date left blank; the order uploaded on a later date than it bears).
2. **Draft schema v0 changes** and a one-page agenda for the meeting: the open questions, each with a proposed answer.
3. **Harness skeleton `eval/score.py`:** `python -m eval.score --gold data/gold/records.jsonl --run runs/<run_id> --split test`.
   - **Defect metrics (RQ1):** per case, compare predicted findings to gold `defects_argued` (ignore gold `not_decided`). Predicted `defect` + gold `defect_found` = true positive; predicted `defect` + gold `defect_rejected` = **false alarm**; predicted `no_defect`/`cant_tell` + gold `defect_found` = miss. Report precision, recall, F1, false-alarm rate, per defect type and overall; a **strict** version that also requires the provision to match. Split into "rule-detectable" vs "reasoning-dependent" defect types (decide the split in the meeting).
   - **"Can't tell" metric:** on the `notice_only` view, defects whose facts are absent from the notice should get `cant_tell`. Report how often they do.
   - **Contested:** rate at which contested gold points get `contested`.
   - **Extraction metrics (RQ2):** field-level exact match for dates/enums/numbers, normalised match for text, F1 over `events`.
   - **From traces:** tool-call accuracy (right tool for the check, valid arguments), error-recovery rate (after `ok: false`), **unsafe-action rate** (any `send_reply` executed without approval), hand-off precision/recall.
   - **Cost:** calls, tokens, seconds per case per system.
   - **Statistics:** paired bootstrap 95% intervals over cases, 3 runs, for "system minus baseline".

### Mon 27 Oct
4. **Run the schema meeting (1 hour).** Go case by case through the pilot notes; decide every open question; then **freeze `contracts.md`** as `schema_version: "0.1"` and announce it. Changes after this need a pull request seen by everyone.
5. **Start the guidelines** (`guidelines/annotation_guidelines.md`): for every field and every defect type, a definition, what counts and what doesn't, and one example quote from a real pilot case. Hard cases to cover:
   - consent or "one more opportunity" remands → `not_decided`;
   - the court relying on another judgment ("covered by") → a finding only if the court applies it to this case's facts;
   - quoted passages from other cases → never this case's facts;
   - batch judgments covering many petitions → record only facts common to all, or mark per-petition facts `null`;
   - limitation questions involving the extension notifications → `contested: true`.

### Tue 28 Oct
6. **Finish the guidelines** (reviewers start using them 29 Oct).
7. **Input builder `src/baselines/inputs.py`:** from each gold record, build the three views in `contracts.md` section 2 (`full_record`, `notice_only`, `raw_text`), removing `defects_argued`, `outcome`, `annotation` and any court reasoning. Set `as_of_date` to the day after the order date (for `notice_only`: the day after the notice date).
8. **Leakage test:** give B1 the `full_record` input and ask it only to predict the case outcome (allowed/dismissed). Accuracy should be near the majority-class rate; if it's clearly higher, find and remove what leaks.
9. **B0 rule checklist `src/baselines/b0_rules.py`** (no model): hearing date missing or "NA" → `hearing_75_4` defect; hearing date before reply due → defect; `signed == false` → `signature` defect; `service_mode == portal_additional_notices_tab` → `service_169` defect; `limitation_check` says out of time → `limitation` defect; otherwise `no_defect`. Output in the shared format.
10. **Test the harness on the dev split** with B0 outputs and a few hand-written outputs (including a false alarm and a `cant_tell`) to make sure the numbers are right.

### Wed 29 Oct
11. **B1 runner:** the same Qwen3-8B as the system, given only the `full_record` input and the defect list, asked for findings in the shared format. Same decoding settings and seeds as NoticeCheck.
12. **B2 runner:** the frontier API model with the full text of the relevant provisions pasted in (from role 3's corpus). Budget: test set × 1 run.
13. **Agreement script `eval/agreement.py`:** exact-match rate per field and Cohen's kappa for `defects_argued` type+finding on the 30 double-reviewed cases. Give to role 1.
14. Review pre-filled cases (~2 h).

### Thu 30 Oct
15. Review pre-filled cases (~2 h).
16. **Run B0, B1, B2 on the gold test set**; score all systems including role 2's NoticeCheck runs; produce `eval/report.py` tables:
    - Table 1: main results (F1, false-alarm rate, strict F1) with intervals, NoticeCheck vs B0/B1/B2.
    - Table 2: per defect type, rule-detectable vs reasoning-dependent.
    - Table 3: `notice_only` view, "can't tell" accuracy.
    - Table 4: tool-call accuracy, error recovery, unsafe actions, hand-off.
    - Table 5: cost per case.
    - Ablations as available.
17. **If any LLM judge is used** (for example, to compare free-text provisions), check it against 50 human judgments and report agreement.

### Fri 31 Oct
18. **`docs/results_mid.md`:** the tables, a paragraph on what they show, which falsification criteria from the proposal are met or not yet testable, and the error analysis (with role 2's examples).

## Depends on / blocks
- **Needs:** pilot notes from everyone (27 Oct); `llm.py` (R1, 26 Oct) for B1/B2; `limitation_check` (R3, 27–28 Oct) for B0; gold (R1, 30 Oct); NoticeCheck runs (R2, 30 Oct).
- **Blocks:** everyone (schema freeze, 27 Oct); reviewers (guidelines, 28 Oct); R2 (inputs, 28 Oct); the submission (results, 31 Oct).

## After the mid (1–15 Nov)
- Full ablations with 3 seeds; held-out court results; RQ2 extraction comparison (LoRA vs untuned 8B vs frontier).
- Accuracy-vs-cost chart; final falsification check against the proposal's criteria (F1 gain ≥ 10 points with the interval above zero, false alarms not higher than baseline, beats B0 on reasoning-dependent defects).

## Done when (31 Oct)
- Schema frozen and guidelines in use.
- `python -m eval.score` produces Tables 1–5 for every system run on the gold set.
- Leakage test reported.
