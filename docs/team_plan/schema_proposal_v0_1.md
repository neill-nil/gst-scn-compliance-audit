# Schema 0.1 — proposal for the schema meeting

**Status: FROZEN on 29 Oct 2026 as `schema_version: "0.1"`.** Drafted by role 1 from 5 pilot cases, revised after role 2's review of 4 more (Tata Play, Nspira, Aswath, Kalika), then tested with Gemini Flash Lite on all 9 (results below). Changes from now on go through a pull request everyone sees. The meeting accepts, changes or rejects each part; then role 4 freezes it in [`contracts.md`](contracts.md).

**Files:** [`schemas/facts.schema.json`](../../schemas/facts.schema.json), [`schemas/findings.schema.json`](../../schemas/findings.schema.json), validator [`src/prefill/schema.py`](../../src/prefill/schema.py). Five real cases already in this format (all valid, all 69 quotes verified): [`data/pilot_drafts/role1/v0_1/`](../../data/pilot_drafts/role1/v0_1/).

## Design goals
1. **Only what we use.** A field stays only if the system reasons with it or we score against it. The draft in `contracts.md` had ~35 fields; this has 12 facts plus the timeline, the document contents and the findings.
2. **Easy for a small model.** Two short extraction calls per case (facts, then findings), fixed lists of allowed values, and "leave it empty" always allowed. This is what Gemini Flash Lite has to fill.
3. **Checkable.** Every value carries the exact words from the judgment and the paragraph number. A program checks the words are really there.

## Shape of a record
```
{ "cnr": "...", "schema_version": "0.1",
  "facts":    { ... },   <- extraction call 1 (schemas/facts.schema.json)
  "findings": { ... },   <- extraction call 2 (schemas/findings.schema.json)
  "review":   { ... } }  <- humans only: status, who reviewed, notes
```
Court, case number and decision date are **not** extracted: they come from `data/manifests/screened.csv`.

Every fact has the same three parts:
```
{"value": "2024-01-20", "quote": "exact words from the judgment", "para": 3}
{"value": null, "quote": null, "para": null}        <- the judgment doesn't say
```

## Facts (call 1): what the system reasons with

| Field | Allowed values | Used for |
|---|---|---|
| `provision` | `"73"`, `"74"` | Which time limits and rules apply; s.74 needs fraud/suppression |
| `financial_years` | list like `["2018-19"]` | Time-limit check; more than one year = consolidated notice |
| `notices[]` (usually one) | | |
| &nbsp;&nbsp;`date` | YYYY-MM-DD | Time limits; order of events |
| &nbsp;&nbsp;`reply_due` | YYYY-MM-DD | Hearing before/on reply date = sham hearing |
| &nbsp;&nbsp;`hearing_date_given` | true / false | false = notice said "NA", left it blank, or no date was fixed |
| &nbsp;&nbsp;`hearing_date` | YYYY-MM-DD | Compared with `reply_due` and the order date |
| &nbsp;&nbsp;`service_mode` | `portal_additional_notices_tab`, `portal_notices_tab`, `portal_unspecified`, `email`, `registered_post`, `hand_delivery`, `not_served` | Service defect (s.169) |
| &nbsp;&nbsp;`signed` | true / false | Signature defect |
| &nbsp;&nbsp;`summary_only` | true / false | Only the DRC-01 summary, no detailed notice |
| `order` | | The demand order being challenged |
| &nbsp;&nbsp;`date` | YYYY-MM-DD | Time limits; order vs hearing |
| &nbsp;&nbsp;`signed` | true / false | Unsigned-order defect |
| &nbsp;&nbsp;`service_mode` | same list as for notices | Order not served (s.169) |
| `events[]` | `date`, `type`, `quote`, `para` | The story: replies, adjournments, missed hearings, appeals |
| `document_contents[]` (max 8) | `type`: `scn_ground`, `fraud_allegation`, `reply_point`, `order_reasoning`; plus `quote`, `para` | What the notice, reply and order **said**. Without it the system cannot judge `non_speaking_order`, `reply_not_considered`, `demand_beyond_scn` or `section_74_ingredients` |

**Event types:** `scrutiny_notice` (s.61), `pre_scn_intimation` (DRC-01A), `scn_issued`, `reply_filed`, `reply_not_filed`, `extension_requested`, `extension_granted`, `hearing_requested`, `hearing_scheduled`, `adjournment_requested`, `hearing_adjourned`, `hearing_attended`, `hearing_missed`, `order_passed`, `rectification_rejected`, `appeal_dismissed`, `recovery_or_attachment` (needed for the hand-off rule), `earlier_writ`, `other`.

## Findings (call 2): the answer key

| Field | Allowed values | Meaning |
|---|---|---|
| `defects_argued[].type` | 13 types (below) | Which mistake by the tax department the taxpayer complained about |
| `defects_argued[].note` | a few words, or null | Only for `other_procedural`: what the ground is |
| `defects_argued[].finding` | `defect_found`, `defect_rejected`, `not_decided` | What the court decided |
| `defects_argued[].contested` | true / false | This judgment notes conflicting court views or a pending Supreme Court case |
| `defects_argued[].quote` + `quote_source` | `court` / `argument` | The court's words for the finding; for `not_decided` with no court words, the argument |
| `outcome.disposition` | `allowed`, `partly_allowed`, `dismissed`, `disposed`, `withdrawn` | Used only for the leakage check |
| `outcome.remanded` | true / false | Sent back to the officer |

**Defect types:** `hearing_75_4`, `adjournment_75_5`, `reply_not_considered`, `non_speaking_order`, `demand_beyond_scn`, `service_169`, `signature`, `summary_only`, `limitation`, `extension_notification_validity`, `consolidated_scn`, `section_74_ingredients`, `other_procedural` (meanings in `contracts.md`; role 3 confirms the provisions).

## Rules (the validator enforces 1–3, 8 and 9)
1. **Never guess.** No value without a quote; no quote means no value.
2. **Dates** are written YYYY-MM-DD, whatever format the judgment uses.
3. **`defect_found` and `defect_rejected` must quote the court**, never a lawyer's argument.
4. **"Prima facie" alone is not a ruling.** A tentative view with no conclusion ("prima facie view") is `not_decided`. But if the court states a clear conclusion on the point, use it even when the sentence says "prima facie" (Garg: "the order cannot be said to be non-speaking" → `defect_rejected`).
5. **`contested` comes from the judgment's own text** (it mentions other courts disagreeing, or a pending Supreme Court case). The system keeps its own list of contested points separately; we don't label from outside knowledge.
6. **Ignore quoted judgments.** Facts and outcomes inside a quoted precedent belong to that other case.
7. A **remand alone is not `defect_found`**: the court must say the mistake happened.
8. **`note` is filled only for `other_procedural`**, and null for every other type.
9. **Document contents describe the document, never the court's opinion of it.** "The order states no evidence of RCM payment was produced" is fine; "the order is cursory" is the court's finding and must not go in. The validator rejects contents that repeat a finding's quote; the reviewer checks the rest. If the judgment only gives the court's opinion, leave it out: the system should then answer "can't tell", which is the honest answer.
10. **`extension_notification_validity` vs `limitation`:** a challenge to the extension notifications themselves is only `extension_notification_validity`. Use `limitation` when the argument is that the notice or order came too late. Label both only when both arguments are made.
11. **Event dates:** the date is the day that step happened. A request is dated the day it was made. `hearing_adjourned` is dated the hearing day that was put off; the new date is a separate `hearing_scheduled` event.
12. **Missing is not "no".** Record `reply_not_filed` or `hearing_missed` only when the judgment says so. No `reply_filed` event means "not stated", not "no reply".
13. **Two orders** (an adjudication order plus its DRC-07 summary, as in Kalika): `order` is the adjudication order; a summary with a different date becomes an `order_passed` event.

## Dropped from the earlier draft, and why
| Dropped | Why |
|---|---|
| Court, case number, decision date | Already in the manifest |
| Officer's name, state/central | The system doesn't reason with them |
| Hearing time and venue | Never decides a defect |
| Demand amounts | Not used by any check; often not stated |
| `tax_period_from/to` | Repeats `financial_years` |
| Event `details` text | Free text the model can't be scored on; the quote already holds it |
| Per-group `evidence` lists | Replaced by one quote on every value |

## Questions for the meeting (with proposed answers)
| # | Question (from the pilot) | Proposed answer |
|---|---|---|
| 1 | Two show cause notices in one case (AR Traders) | `notices` is a list |
| 2 | "Contested": from the judgment or our own list? (Bombay found a consolidated-notice defect, Calcutta rejected one) | From the judgment's own text (rule 5) |
| 3 | Prima facie rejection (Garg) | **Decided:** a clear conclusion wins, so `defect_rejected` (rule 4) |
| 4 | "Partly allowed, liberty to re-issue" (AR Traders) | `partly_allowed`, `remanded: false` |
| 5 | Appeal order also quashed (Agarwal); scrutiny notice before the SCN (Rajesh) | Events `appeal_dismissed`, `scrutiny_notice` |
| 6 | Same-day reply and hearing (Rajesh) | No extra field: `reply_due` = `hearing_date` already shows it |
| 7 | Should we keep amounts for the hand-off rule? | No; hand-off uses `recovery_or_attachment` events instead |
| 8 | Strict scoring compares provisions, but gold has no provision field | Role 4 derives it from a fixed table (defect type → provision; `limitation` uses `facts.provision`). No extra model field |
| 9 | `contested`: contracts said `extension_notification_validity` is "always contested" | Gold `contested` comes only from the judgment (rule 5). "Always contested" is the system's own list and decides when it answers `contested` |

## Revision of 29 Oct (role 2's review of Tata Play, Nspira, Aswath, Kalika)
| Gap found | Change |
|---|---|
| No place for what the notice, reply and order said (Nspira: the court found the order was boilerplate, but the system's input had nothing to show it) | New `document_contents` list, with rule 9 against leaking the court's findings |
| Signature and service defects can concern the order, not only the notice | `order_date` became `order` with `date`, `signed`, `service_mode` |
| "No reply was filed" (Aswath), "hearing requested" and "adjournment requested" (Tata Play) had no event type | New events `reply_not_filed`, `hearing_requested`, `adjournment_requested`; rule 12 |
| `other_procedural` could not say what the ground was | New `note` field, rule 8 |
| `limitation` vs `extension_notification_validity`; two meanings of `contested`; provision scoring; event-date meaning | Rules 10, 11 and questions 8, 9 |

Not taken: amounts, GSTIN, business description, officer, hearing time and venue, detailed submissions, several quotes per finding. The review agreed none of these decide a defect.

## Flash Lite test on the 9 pilot cases (29 Oct)
Pre-fill: [`src/prefill/prefill.py`](../../src/prefill/prefill.py), 2 calls per case (`gemini-3.5-flash-lite`), about 25 s per case. Compared with role 1's reviewed drafts (5 cases, all fields) and role 2's findings (4 cases, findings and outcome only).

| What | Result (final prompt) |
|---|---|
| Records valid against the schema | 9 / 9 (one needed a retry) |
| Quotes found word for word in the judgment | 104 / 111. The 7 misses: 5 from a Madras judgment whose table text is jumbled by the PDF (Kalika), 2 where the PDF has a stray footnote number inside the sentence (Nspira) |
| Facts stated in the judgment, filled correctly | 23 / 25. 2 left empty, **0 wrong** |
| Timeline events found | 14 / 19; 1 wrong date (a reply deadline used as the scrutiny notice's date) |
| Court findings correct (type and finding) | 17 / 21 |
| `defect_found` correct | 8 / 8, and it never invented a `defect_found` |
| Outcome (disposition and remand) | 8 / 8 |

**Where it still goes wrong (what reviewers should check first):**
- **`not_decided` vs `defect_rejected`** on dismissed or equitable-remand cases (Garg, Kalika). This is also where people disagreed (below).
- **Missed complaints**: Tata Play's hearing complaint was folded into the adjournment complaint; Rajesh's s.161 complaint was missed.
- **Facts said by the department's lawyer**: Agarwal's "no date was fixed for personal hearing" was missed twice.
- **Garbled Hindi text** (old-font PDFs) sometimes gets copied as an `order_reasoning` quote. Delete it in review.

**Judgement calls, decided by the team on 29 Oct:**
1. Kalika: the court grants another chance "on equitable grounds" after noting the assessment was ex parte. Role 2's AI said the hearing complaint was `defect_rejected`; Flash Lite says `not_decided`. **Decided: `not_decided`** (equitable remand = no ruling). Role 2's label changes accordingly.
2. Garg: "though prima facie sufficient reason has been provided… the order cannot be said to be non-speaking, however, these are all disputed factual issues". **Decided: `defect_rejected`**: when the court states a clear conclusion, use it (rule 4 updated).
3. Priyanka (Delhi "Additional Notices tab" template): the court sets aside because the notice predates the department's fix to the tab, without saying "service was defective". Role 1 labelled `defect_found`. 115 Delhi orders in our store mention the tab (21 of them in the reasoned pool). **Decided: `service_169: defect_found`** when the court sets the order aside because the notice was on the Additional Notices tab before the department fixed the portal.

## Example (Rajesh Kumar Singh, Allahabad), shortened
```json
{"cnr": "UPHC010748612025", "schema_version": "0.1",
 "facts": {
  "provision": {"value": "73", "quote": "notice was issued under Section 73(1) of the Act on 23.12.2023", "para": 3},
  "financial_years": {"value": ["2018-19"], "quote": "For the tax period April, 2018 to March, 2019", "para": 2},
  "notices": [{
    "date": {"value": "2023-12-23", "quote": "notice was issued under Section 73(1) of the Act on 23.12.2023", "para": 3},
    "reply_due": {"value": "2024-01-20", "quote": "the date indicated by which reply was to be submitted was 20.01.2024 and date of personal hearing was also fixed on the same date", "para": 3},
    "hearing_date_given": {"value": true, "quote": "…same as above…", "para": 3},
    "hearing_date": {"value": "2024-01-20", "quote": "…same as above…", "para": 3},
    "service_mode": {"value": null, "quote": null, "para": null},
    "signed": {"value": null, "quote": null, "para": null},
    "summary_only": {"value": null, "quote": null, "para": null}}],
  "order": {"date": {"value": "2024-04-30", "quote": "The respondent no. 2 passed order dated 30.04.2024 under Section 73(9) of the Act", "para": 5},
            "signed": {"value": null, "quote": null, "para": null}, "service_mode": {"value": null, "quote": null, "para": null}},
  "events": [{"date": "2024-01-18", "type": "reply_filed", "quote": "The petitioner filed his reply on 18.01.2024", "para": 4}, "…"],
  "document_contents": [
   {"type": "reply_point", "quote": "in the case of petitioner, the tax is charged on Reverse Charge Mechanism (RCM) wherein the tax is to be paid by the recipient of the service and filed the relevant tax invoices of the transactions", "para": 4},
   {"type": "order_reasoning", "quote": "no evidence has been produced pertaining to deposit of tax through RCM and the accounts books have not been verified", "para": 14}, "…"]},
 "findings": {
  "defects_argued": [{"type": "hearing_75_4", "note": null, "finding": "defect_found", "contested": false,
    "quote": "This Court has repeatedly frowned on the action of the respondents in fixing identical date of reply and date of hearing",
    "quote_source": "court", "para": 12}, "…"],
  "outcome": {"disposition": "allowed", "remanded": true, "quote": "The matter is remanded back to …", "para": 18}},
 "review": {"status": "draft_for_review", "reviewed_by": [], "notes": "…"}}
```
