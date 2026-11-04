# Final submission plan (4–15 Nov)

**Where we are.** The data pipeline, the 54-case test set, the evaluation harness and three baselines are on `main`. The NoticeCheck system itself, the tools and the statute corpus are **not** on GitHub yet. Building and measuring the system is now the critical path. If you have local work on any of these, push it to a branch today so nothing is built twice.

**What "done" means on 15 Nov** (the proposal's promises):
1. **NoticeCheck** reads a notice and its proceeding record and returns the compliance report: for each of the 13 defect types, a verdict (defect / no defect / can't tell / contested), the provision, the evidence, any missing facts, and a hand-off decision.
2. **RQ1 answered:** NoticeCheck vs B1 (same Qwen3-8B, facts only) on defect F1 (type-level and strict type+provision) and false-alarm rate. Measured on test set v2 plus one held-out High Court, over 3 runs, with paired bootstrap intervals.
3. **Ablations:**
   - **Component:** retrieval off, tools off, verifier off, hand-off off.
   - **Input:** raw judgment text vs extracted record vs human-verified record.
   - **One metric per capability.**
4. **RQ2 answered:** a QLoRA Qwen3-8B extractor vs the untuned 8B (B3) and the large prompted model, scored by field F1 on the test facts.
5. **Synthetic stress set** from the DRC-01 template, including fully valid notices. These catch false alarms that real judgments can't show.
6. **Demo** on one defective and one valid notice, plus the paper and repository release.

## Owners
| Who | Owns |
|---|---|
| **Neill (R1)** | **All design decisions.** NoticeCheck's reasoning core: check cards, planner, verifier, contested policy. Test and dev sets: selection, adjudication, splits. RQ2 data. Final analysis and the paper. |
| **R2** | NoticeCheck runtime: the agent loop that executes check cards, the tool executor, traces, config switches, hand-off rules, the sandbox, Kaggle runs, the demo interface. |
| **R3** | Statute corpus and the tools in `contracts.md` §4; the synthetic DRC-01 generator and stress set. |
| **R4** | Evaluation upgrades; B2 with a second frontier model, and B3; the LoRA training runs on Kaggle. |

Everyone reviews cases (§4). Nobody tunes on the test or held-out cases.

## 1. Decisions (Neill decides; recommendations attached)
| # | Decision | Recommendation | Needed by |
|---|---|---|---|
| D1 | How NoticeCheck checks each defect | One **check card** per defect type (`src/noticecheck/checks/<type>.yaml`). A card lists the facts it needs, the statute refs, and whether the check is rule-based or model-judged. If a required fact is missing, the verdict is **can't tell**, decided by code, not the model. Rule-based checks (hearing date, signature, service tab, limitation) use tools. Reasoning checks (reply ignored, non-speaking order, beyond the notice, s.74 ingredients, other) get one focused model call each, with that defect's statute text retrieved. The model chooses and fills the tool calls in a bounded loop (max 4 steps per check), so tool-call accuracy can be measured. | 5 Nov |
| D2 | Contested list | **Validity of the extension notifications** and **consolidated multi-year notices** are always contested. The **Additional Notices tab** is contested only when the record shows the notice was also emailed. For a contested point the system says "contested" and cites conflicting cases from `caselaw_search`. | 5 Nov |
| D3 | Defect → provision table (strict score) | hearing s.75(4); adjournment s.75(5); reply / non-speaking s.75(6); beyond notice s.75(7); service s.169; signature r.26(3); summary only r.142(1); limitation s.73(10) or s.74(10) from `facts.provision`; extension s.168A; consolidated s.73/74(1); s.74 ingredients s.74(1); other: no provision. **R3 verifies each against the official text.** | 6 Nov |
| D4 | Held-out court | **Karnataka**: 17 cases, clean text, and no Karnataka case is used for dev or prompts. Allahabad has more cases (19) but garbled Hindi text. | 4 Nov |
| D5 | Dev set for tuning | 20 newly reviewed Madras and Delhi cases plus the 9 pilot drafts. All prompt and card tuning happens here only. | 4 Nov |
| D6 | Test set v2 | 54 + ~80 new cases, balanced as before (Madras ≤ 40% of the total). **40** double-reviewed, and the second review is done **without AI help**, so agreement is real. | 4 Nov |
| D7 | Second frontier model for B2 | A non-Gemini model on a free tier (e.g. Llama 3.3 70B on Groq, or Mistral). It removes Gemini's home advantage. R4 checks the quota on 5 Nov. | 5 Nov |
| D8 | RQ2 training data | Input: the judgment's fact paragraphs (no court reasoning). Target: the facts block of the Gemini drafts for the ~336 non-test, non-held-out cases, plus synthetic notices. Scored on the human-verified facts of the test cases. Silver labels must be stated as a limitation. | 6 Nov |
| D9 | Fallback if NoticeCheck v1 is late on 8 Nov | Run the check cards with a fixed tool order (no model-chosen tools) and report the tool-calling capability as partial. | 8 Nov |

## 2. Timeline
| Dates | Neill (+ Claude) | R2 runtime | R3 tools and synthetic | R4 eval and training |
|---|---|---|---|---|
| **4–5 Nov** | Decisions D1–D8; check-card spec for all 13 types; review queue v2 (test, dev, held-out); splits `dev/test/heldout/precedent.txt` | Skeleton `src/noticecheck/` (state, pipeline, agent loop, trace writer, CLI) on **mock tools**; Qwen3-8B serving on Kaggle (Ollama, short JSON outputs) | Statute corpus: CGST Act ss.61, 65, 73–75, 107, 161, 168A, 169; Rules 26, 142; units with version date and hash. `statute_lookup`, `statute_search`, `date_diff`. Tests. | Fix the input field order; strict score using D3; aggregation over 3 runs; count of defects flagged on types nobody argued; trace metrics wired to `contracts.md` §5 |
| **5–7 Nov** | Write the 13 check cards and the verifier rules; planner prompt; tune on **dev** only | Card executor; real tools as they land; hand-off rules; `send_reply` sandbox; ablation switches | `limitation_check` (s.168A notifications marked contested); `caselaw_search` over the precedent split (refuses test, dev and held-out); `specs.json` | B2 with the second model on test v1; B3 (untuned Qwen extraction); LoRA data loader and training script tried on 20 examples |
| **4–8 Nov** | Review dev cases; adjudicate all disagreements | **Review** ~25 new test cases | **Review** ~25 new test cases | **Review** ~25 new test cases + 2nd reviews |
| **8 Nov** | **Checkpoint:** NoticeCheck v1 runs end to end on dev; go or fallback (D9) | | Synthetic generator: valid notices and planted defects (~100 stress cases, ~1,000 training) | |
| **8–10 Nov** | Build test v2 and the held-out set; first RQ1 result on test v1 | NoticeCheck full runs: test v2 + held-out, 2 views, 3 seeds | Retrieval evaluation: Recall@k of the right provisions, hierarchical vs flat | **QLoRA training** (Kaggle, about 4 runs); score field F1 on the test facts |
| **10–12 Nov** | Ablation analysis; error tracing to the first failing step | Ablation runs (4 components + input views, 3 seeds); stress-set runs | Help with ablation runs | Score everything; tables; accuracy–cost chart |
| **12–15 Nov** | **Paper** (lead): method, results, analysis | Demo interface + walkthrough; `docs/examples.md` | Corpus and tools sections of the paper | Evaluation section; repository clean-up |

**Checkpoints** (short call each time; anything late gets the fallback):
- **6 Nov:** mock end-to-end run; tools API frozen.
- **8 Nov:** NoticeCheck v1 on dev; test v2 reviews done.
- **11 Nov:** all runs done.
- **13 Nov:** paper draft.

## 3. Compute budget
- **NoticeCheck:** about 5–7 Qwen calls per case. Rule-based checks need no model call; one call per reasoning check, plus the planner and the verifier.
- **Main runs:** ~150 test + ~17 held-out cases × 2 views × 3 seeds ≈ 1,000 cases × 6 calls ≈ 6,000 calls. At ~15 s per call with 2 in parallel on a T4 that is about 25 GPU-hours, so the runs **must be split across at least 3 Kaggle accounts**. Keep output short: B1 averaged 2,100 output tokens per call, and that is what made it slow.
- **Ablations** on the `full_record` view only: 4 × 167 × 3 ≈ 2,000 cases → split the same way.
- **QLoRA:** about 4 runs × 3–4 h.
- **API:** the B2 second model, ~108 calls per run.

## 4. Review work (everyone)
- **Test v2:** ~80 new cases. Run `python -m review_app.server` with the new queue `data/splits/review_queue_v2.csv`.
- **Rules:**
  - The second review of any case is done **without AI help**.
  - Mark `UNSURE:` when in doubt; Neill adjudicates.
  - Push every 5 cases.
- **Due 8 Nov.**

## 5. Rules that protect the results
- Tuning (prompts, check cards, thresholds) happens on the **dev** split only. Test and held-out cases are never opened while building.
- `caselaw_search` must never return test, dev or held-out cases (R3 adds a test for this).
- NoticeCheck and B1 use the same model, decoding settings and seeds.
- Every run writes its commit, model digest and data hashes, as the B1 run did.
