# Role 2 — The NoticeCheck system (the agent under test)

**Goal:** build the system the project is about. Given the record of a GST demand proceeding, it checks each procedural step against the law, uses tools and retrieved statute text, verifies every finding, says "can't tell yet" when facts are missing, decides whether to hand the case to a professional, and writes a report. By 30 Oct it must run end-to-end on the gold set and produce outputs in the shared format.

**Give your AI:** this file, [`contracts.md`](contracts.md) (sections 2–5 are your input, output, tools and traces), and [`README.md`](README.md) section 4 (shared rules).

## The five steps (from the proposal)
1. **Extract**: turn raw text into a case record. (For the mid, run on the structured `full_record` view, so this step is skipped. You still need it for the `raw_text` view and for RQ2 later.)
2. **Plan**: find the provision invoked (s.73 or s.74) and the tax period; list which defect checks apply; list facts that are needed but missing.
3. **Test each precondition**: one check per defect type, using tools (limitation calculator, statute lookup, statute search, case-law search).
4. **Verify**: drop any finding that isn't supported by a quote from the record *and* the text of a provision; mark contested points as `contested` instead of deciding them; turn unsupported findings into `cant_tell` with the missing facts listed.
5. **Hand-off**: escalate when a deadline is tight, recovery or bank attachment is threatened, the case is unclear, or **no defect is found** (a defect-free proceeding means the person must deal with the demand, so they should see a professional). The only state-changing tool, `send_reply`, runs only with explicit approval and only in the sandbox.

## Inputs you get
- Checker inputs (`contracts.md` section 2): from role 4's input builder (28 Oct). Until then, write 5 inputs by hand from the pilot cases.
- Tools (`contracts.md` section 4): from role 3 (28 Oct). Until then, use mock tools with the same signatures.
- Model client `src/common/llm.py`: from role 1 (26 Oct night).

## Outputs you deliver
| Output | Path | Due |
|---|---|---|
| Pipeline code | `src/noticecheck/` | 28 Oct (end-to-end), 29 Oct (real tools) |
| Run outputs | `runs/<run_id>/outputs.jsonl` + `traces/` | 30 Oct |
| Ablation switches | flags in `configs/*.yaml` | 29 Oct |
| Qualitative examples + failure cases | `docs/examples.md` | 31 Oct |

## Steps

### Sun 26 Oct
1. **Serve Qwen3-8B** on Kaggle (vLLM with a 4-bit AWQ build on T4 GPUs, or Ollama) as an OpenAI-compatible endpoint, or locally if you have a GPU. Record tokens per second. Fallback: Gemma 3 4B.
2. **Skeleton `src/noticecheck/`:**
   - `state.py`: one `CaseState` object carrying input, plan, findings, verified findings, hand-off and trace.
   - `pipeline.py`: `run(case_input, config) -> output` calling the five stages in order; each stage is a function taking and returning `CaseState`.
   - `agent_loop.py`: a tool-calling loop. The model outputs either a tool call (`{"tool": ..., "args": {...}}`) or a final answer; you execute the tool, append the result, and repeat, with a step limit (e.g. 8) per defect check.
   - `trace.py`: write every step in the trace format (`contracts.md` section 5).
   - `cli.py`: `python -m src.noticecheck.cli --inputs <jsonl> --config configs/nc_full.yaml --run-id <id>`.
3. **Mock tools** in `src/noticecheck/mock_tools.py`, matching the signatures in `contracts.md` exactly, so switching to role 3's real tools is a one-line change.
4. Read your 5 pilot cases (rows 6–10 of `data/splits/schema_pilot.csv`).

### Mon 27 Oct
5. **Schema meeting.** Bring a list of the facts each defect check needs (for example, the hearing check needs: was a hearing date given, was it "NA", was it before the reply was due, was the hearing adjourned, was it attended).
6. **Planner:** given the record, decide provision and period, then build the check list. For each defect type, write a short *precondition checklist* in `src/noticecheck/checks/<defect>.yaml`: which record fields are needed, which statute refs apply, and what pattern of facts means "defect". Ask role 3 to confirm the provisions.

### Tue 28 Oct
7. **Precondition checkers**, one per defect type, at least: `hearing_75_4`, `adjournment_75_5`, `reply_not_considered`, `non_speaking_order`, `service_169`, `signature`, `summary_only`, `limitation`, `consolidated_scn`, `demand_beyond_scn`. Each one: gathers the needed facts from the record, calls tools (statute lookup for the provision text; `limitation_check` for limitation; case-law search when a point may be contested), and returns a finding with evidence.
8. **Verifier:** for each finding, check it has (a) a record quote and (b) a statute quote, both copied from tool or record output (check programmatically, not by the model). Missing support → `cant_tell` with `missing_facts`. Points on a contested list (`extension_notification_validity`, `consolidated_scn`, plus whatever role 3 adds) → `contested`.
9. **Hand-off policy:** rules first (dates vs `as_of_date`, recovery/attachment words, no defects found), then the model only for "unclear". Output `handoff.escalate` and `reasons`.
10. **Run end-to-end on the 5 hand-made pilot inputs.** Fix crashes. Check traces are complete.

### Wed 29 Oct
11. **Switch to real tools** from role 3. Handle `{"ok": false}` results: retry with corrected arguments once, then continue without that tool and note it in the trace.
12. **Ablation switches** in the config: `retrieval: on/off`, `tools: on/off`, `verifier: on/off`, `handoff: on/off`, `view: full_record | notice_only | raw_text`. Each switch must really remove the component, not just hide its output.
13. Run on the `dev` split (pilot cases) with role 4's harness; look at failures; adjust prompts only on dev, never on test.

### Thu 30 Oct
14. **Run on the gold test set**: full configuration, `full_record` and `notice_only` views, 3 seeds. Then one run per ablation if time allows (otherwise after the mid).
15. Hand the run folders to role 4 for scoring.

### Fri 31 Oct
16. **`docs/examples.md`**: 3 good cases (a true defect found with its provision; a correct "no defect"; a correct "can't tell"), 3 failure cases, each traced to the first step that went wrong. Architecture diagram for the write-up.

## Depends on / blocks
- **Needs:** `llm.py` (R1, 26 Oct); frozen schema (all, 27 Oct); tools (R3, 28 Oct); checker inputs (R4, 28 Oct); gold (R1, 30 Oct).
- **Blocks:** the main results (30 Oct).

## Metrics your code must make possible
Defect F1 and false-alarm rate (from outputs); accuracy of each intermediate check (from traces); tool-call accuracy and error recovery (from traces); unsafe-action rate (any `send_reply` executed without approval; target 0); hand-off precision/recall; calls, tokens and seconds per case.

## After the mid (1–15 Nov)
- Extract step for the `raw_text` view; then swap in role 1's LoRA extractor (RQ2).
- Full ablation runs (3 seeds each), held-out court runs.
- Robustness: missing facts, contradictory facts.

## Done when (31 Oct)
- `python -m src.noticecheck.cli` runs on the gold set without crashing and writes valid outputs and traces.
- All four ablation switches work.
- Unsafe-action rate is 0 in every run.
