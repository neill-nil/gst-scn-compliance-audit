# Mid results: data and baselines (30–31 Oct)

## Gold set v1
| Step | Count |
|---|---|
| GST cases screened (24 High Courts, 2024–2026) | 20,087 |
| In scope (s.73/74 demand proceedings) | ~4,900 |
| Tagged reasoned by rules (Telangana excluded) | 426 |
| Pre-filled by Gemini 3.5 Flash Lite | 425 (1 failed) |
| Picked for review (balanced by court, all rejected findings, ≤4 Delhi template orders, ≤25 pages, dev cases excluded) | 60 |
| Out of scope after review (s.75(12) recovery ×2, pre-GST Service Tax, s.161 rectification) | 4 |
| Duplicate (one Delhi common order filed under 3 CNRs, kept once) | 2 |
| **Gold (= test split, `data/splits/test.txt`)** | **54** |

Complaints argued in the 54 cases: 84. Findings: **36 `defect_found`, 27 `defect_rejected`, 21 `not_decided`**.
Courts: Madras 21, Delhi 13, Bombay 4, Allahabad 4, Orissa 3, Calcutta 3, Karnataka 2, Patna 2, Jharkhand 1, Uttarakhand 1.

Every value has a quote that a program checks against the judgment text; all 54 records pass the schema and quote checks.

## Review and agreement
- Four reviewers, 15 cases each plus 4 second reviews; reviewers were assisted by an AI model that pointed to relevant paragraphs, and every label was confirmed against the judgment text.
- 13 cases were reviewed independently by two people (`eval/agreement.py`):
  - Findings (type + finding): Cohen's kappa **0.54** over 26 case–type cells; 9 of 13 cases agree exactly.
  - Outcome (disposition): 13/13.
  - Facts: 89–100% exact match per field (provision 8/9, financial years 9/10, notice and order dates 11/11).
- Disagreements were settled case by case; decisions and reasons are in `data/gold/adjudication.csv`. Agreement uses the original versions.

## How good were the Gemini drafts?
Draft vs final gold record, on the 54 cases:
- **Facts:** 169 of 183 non-empty fact values (92%) unchanged. Reviewers filled 7 values the model left empty and cleared 6 it could not support.
- **Findings:** 67 of 90 draft (type, finding) pairs unchanged (74%). The main corrections:
  - complaints the model missed: 9 (4 → not_decided, 3 → rejected, 2 → found);
  - complaints the model added that were not argued: 6;
  - `not_decided` that the court did decide: 6 (3 → rejected, 3 → found);
  - wrong finding otherwise: 2.
- Caveat: gold was made by correcting these drafts, so the drafts' agreement with gold is an upper bound.

**Cost of the pre-fill** (all 4 shares on the free tier): about 2 calls per case, ~5.3M input and ~1.0M output tokens on one key (531 calls, 83 min of model time, r1 + r4 shares + retries).

## Baselines on the 54 test cases
Every system gets the same input: the facts of the case, with the court's findings, the outcome and the court's reasoning removed. For each of 13 defect types it answers "defect", "no defect" or "can't tell".

Scoring (`eval/score.py --no-unargued-as-rejected`):
- Only complaints actually argued in the case are scored.
- Gold `defect_found` + "defect" = found; gold `defect_found` + anything else = missed; gold `defect_rejected` + "defect" = **false alarm**.
- Gold `not_decided` is not scored.
- 36 scorable real defects and 27 rejected complaints.

| System | What it is |
|---|---|
| **B0** | Fixed rules, no model: hearing date missing/"NA" → hearing; notice unsigned → signature; "Additional Notices" tab → service; out of time → limitation |
| **B1** | Qwen3-8B (Ollama, 4-bit Q4_K_M), facts and defect list only; temperature 0, seed 1, thinking off; Kaggle 2× T4 |
| **B2** | Gemini 3.5 Flash Lite, facts and defect list **plus** the verbatim text of CGST Act ss.73, 74, 75, 168A and 169 (official India Code PDF); temperature 0 |

### Main result: all facts given (`full_record`)
| System | Found | False alarms | Missed | Precision | Recall | F1 | False-alarm rate |
|---|---|---|---|---|---|---|---|
| B0 rules | 4 | 2 | 32 | 0.67 | 0.11 | 0.19 | 0.07 |
| B1 Qwen3-8B | 11 | 5 | 25 | 0.69 | 0.31 | 0.42 | 0.19 |
| B2 Gemini + statute | 15 | 4 | 21 | 0.79 | 0.42 | 0.55 | 0.15 |

**Paired bootstrap** over cases (5,000 resamples, same scoring rule; `scripts/compare_runs.py`), 95% intervals:
| Comparison | F1 | Recall | False alarms |
|---|---|---|---|
| B1 − B0 | +0.23 [−0.01, +0.45] | +0.19 [+0.03, +0.38] | +3 [0, +7] |
| B2 − B1 | +0.12 [+0.03, +0.23] | +0.11 [+0.03, +0.21] | −1 [−5, +2] |
| B2 − B0 | +0.36 [+0.12, +0.57] | +0.31 [+0.11, +0.50] | +2 [0, +5] |

B1 finds significantly more real defects than the rules, but its F1 gain is not significant at 54 cases. B2 beats B1 on both F1 and recall. No difference in false alarms is significant.

### Defects that need reasoning vs rule-detectable ones
| System | Rule-detectable (15): found / FA / missed | Needs reading the order (21): found / FA / missed |
|---|---|---|
| B0 | 4 / 2 / 11 | 0 / 0 / 21 |
| B1 | 4 / 3 / 11 | 7 / 2 / 14 |
| B2 | 6 / 2 / 9 | 9 / 2 / 12 |

By type, found / false alarm / missed:
| Type | B0 | B1 | B2 |
|---|---|---|---|
| hearing_75_4 (12 real) | 2 / 0 / 10 | 4 / 0 / 8 | 5 / 0 / 7 |
| reply_not_considered (9) | 0 / 0 / 9 | 7 / 1 / 2 | 8 / 1 / 1 |
| non_speaking_order (4) | 0 / 0 / 4 | 0 / 0 / 4 | 1 / 0 / 3 |
| service_169 (3) | 2 / 2 / 1 | 0 / 2 / 3 | 1 / 2 / 2 |
| consolidated_scn (4) | 0 / 0 / 4 | 0 / 0 / 4 | 0 / 1 / 4 |
| other_procedural (4) | 0 / 0 / 4 | 0 / 1 / 4 | 0 / 0 / 4 |
| limitation (0) | – | 0 / 1 / 0 | – |

### "Can't tell" test: only the notice given (`notice_only`)
Most defects cannot be judged from the notice alone, so "can't tell" is the honest answer.
| System | "Can't tell" rate | Defects flagged: correct / false alarm |
|---|---|---|
| B0 | 35% | 4 / 2 |
| B1 | 80% | 1 / 2 |
| B2 | 98% | 4 / 4 |

B1 answers "no defect" instead of "can't tell" most often for demand beyond the notice (55% can't tell), limitation (63%) and other procedural (41%).

### Ablations (`full_record`, same scoring and bootstrap)
| Ablation | Comparison | F1 | Difference (95% CI) |
|---|---|---|---|
| A2 statute text | B2 with vs without CGST Act ss.73/74/75/168A/169 | 0.55 vs 0.45 | F1 +0.09 [−0.03, +0.20]; precision +0.08 [0.00, +0.20] |
| A3 model scale | B2 without statute (Gemini) vs B1 (Qwen3-8B), same facts-only input | 0.45 vs 0.42 | F1 +0.03 [−0.10, +0.18] |

B2's lead over B1 (+0.12, significant) splits into a statute part (+0.09) and a small model-size part (+0.03); neither part is significant alone.
Without the statute, B2 finds 12, raises 5 false alarms and misses 24. On `notice_only` it says "can't tell" 97% of the time.
Outputs: `runs/b2_nostatute` on `mid-baselines`.

### Error analysis (`full_record`)
- **Most misses are honest "can't tell"s, not wrong answers.** Of the real defects each system missed:
  - B2 said "can't tell" for 18 of 21 and "no defect" for 3;
  - B1 said "can't tell" for 14 of 25 and "no defect" for **11**;
  - B0 said "no defect" for 21 of 32.
  
  B1 more often asserts that a defect is absent when the facts don't show it.
- **Missed by all three:**
  - **7 hearing defects.** The court found no proper hearing, but the extracted facts hold no hearing date or "NA". The evidence sits in the court's reasoning, which every system is (correctly) denied.
  - **All 4 consolidated-notice and 4 other-procedural defects.** These need legal judgement (is one notice for several years allowed?), not facts alone. The facts schema is the limit here, not just the models.
- **False alarms follow the Delhi "Additional Notices" pattern.** In two cases (BRHC010303862026, DLHC011072522025) the notice was on the Additional Notices tab, and B0, B1 and B2 all flagged service. Both courts rejected the complaint: Patna because the taxpayer never denied receiving the email; Delhi because the tab argument was "untenable" on the facts. The same fact pattern is a defect in other Delhi cases, so this needs the case-specific reasoning that the facts don't carry.
- **Other false alarms:**
  - B2 flagged the consolidated notice in JBN Impex, where Delhi holds consolidation permissible. Other High Courts disagree, which is exactly a "contested" point.
  - B1 flagged reply-not-considered in WBCHCA0195612025, where the court found the reply was considered (B2 too), and limitation in HCMA011812622025, where the court held the proceedings in time.
- **Where B2 beats B1:** in 4 cases (WBCHCJ0050492025 service, HCMA011637932024 hearing, HCMA010457152024 reply, HCMA012219242024 non-speaking order), B2 found the defect while B1 said "can't tell" or "no defect".
- **Contested points:** none of the 10 contested gold points is marked contested by any baseline. The baseline prompt offers only defect / no defect / can't tell; NoticeCheck has a "contested" verdict.

### Cost
| System | Calls | Input tokens / case | Output tokens / case | Time / case | Hardware |
|---|---|---|---|---|---|
| B0 | 0 | – | – | ~0 | CPU |
| B1 | 1 | ~1.1k | ~2.1k | ~117 s (2 in parallel) | Kaggle 2× T4, ~1 h 45 min wall-clock for 108 calls |
| B2 | 1 | ~4.8k (incl. statute) | ~1.0k | ~5 s | Gemini API, free tier |

### Caveats
- **54 cases, one run per system**, so the intervals are wide. The final submission will add 3 runs and more gold.
- **B2 home advantage:** Gemini drafted the gold records before human review.
- **Malformed answers:** 1 of 108 B2 answers was malformed JSON (a missing comma; HCMA011668272024), scored as no verdicts. B1 left out 1–2 of the 13 types in 10 of 108 answers (mostly `limitation`), scored as not predicted.
- **Input field order:** role 4's input builder writes the record's fields in a different order on each run (it iterates a Python set). B1 and B2 therefore saw the same facts in a different key order. The content was checked identical; to fix for the final runs.
- **Reproducibility:** all outputs and scores are in `runs/b0`, `runs/b1`, `runs/b2` on branch `mid-baselines`. The B1 run record (`runs/b1/experiment.json`) gives the commit, model digest and the sha256 of the gold and split files, which match ours.

## Not yet run
- **NoticeCheck** (role 2) on the same 54 cases. The main research question (does tool-based, statute-grounded checking beat the same model with facts only) is NoticeCheck vs B1.
