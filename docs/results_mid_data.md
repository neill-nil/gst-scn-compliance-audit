# Mid results: data and B0 (30 Oct)

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

## B0: rule checklist (no model), 54 test cases
Rules: hearing date missing or "NA" → hearing defect; notice not signed → signature; "Additional Notices" tab → service; out of time → limitation. Scored on argued complaints only (`--no-unargued-as-rejected`); `not_decided` is not scored.

| | Found by B0 | False alarms | Missed | Precision | Recall |
|---|---|---|---|---|---|
| All complaints | 4 | 2 | 32 | 0.67 | 0.11 |
| Rule-detectable types | 4 | 2 | 11 | 0.67 | 0.27 |
| Reasoning-dependent types (reply ignored, non-speaking order, consolidated notice, other) | 0 | 0 | 21 | – | 0.00 |

By type: hearing 2 found / 10 missed; service 2 found / 2 false alarms / 1 missed; every reasoning-dependent defect missed.
False-alarm rate 2 of 27 rejected complaints (0.07). On the `notice_only` view, B0 says "can't tell" for 35% of cells.

This is the floor the model systems must beat: fixed rules catch a few date/portal defects and nothing that needs reading the order.

## Not yet run
- **B1** (Qwen3-8B, record only), **B2** (frontier model with statute text) and **NoticeCheck** on the same 54 cases.
- Note for B2: if it uses Gemini, it has a home advantage, because the gold started from Gemini drafts. Use another frontier model or report this.
