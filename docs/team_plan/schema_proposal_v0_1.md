# Schema 0.1 — proposal for the schema meeting

**Status:** proposal from role 1, after reading 5 pilot cases. The meeting accepts, changes or rejects each part; then role 4 freezes it in [`contracts.md`](contracts.md).

**Files:** [`schemas/facts.schema.json`](../../schemas/facts.schema.json), [`schemas/findings.schema.json`](../../schemas/findings.schema.json), validator [`src/prefill/schema.py`](../../src/prefill/schema.py). Five real cases already in this format (all valid, all 62 quotes verified): [`data/pilot_drafts/role1/v0_1/`](../../data/pilot_drafts/role1/v0_1/).

## Design goals
1. **Only what we use.** A field stays only if the system reasons with it or we score against it. The draft in `contracts.md` had ~35 fields; this has 11 facts plus the timeline and the findings.
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
| `order_date` | YYYY-MM-DD | Time limits; order vs hearing |
| `events[]` | `date`, `type`, `quote`, `para` | The story: replies, adjournments, missed hearings, appeals |

**Event types:** `scrutiny_notice` (s.61), `pre_scn_intimation` (DRC-01A), `scn_issued`, `reply_filed`, `extension_requested`, `extension_granted`, `hearing_scheduled`, `hearing_adjourned`, `hearing_attended`, `hearing_missed`, `order_passed`, `rectification_rejected`, `appeal_dismissed`, `recovery_or_attachment` (needed for the hand-off rule), `earlier_writ`, `other`.

## Findings (call 2): the answer key

| Field | Allowed values | Meaning |
|---|---|---|
| `defects_argued[].type` | 13 types (below) | Which mistake by the tax department the taxpayer complained about |
| `defects_argued[].finding` | `defect_found`, `defect_rejected`, `not_decided` | What the court decided |
| `defects_argued[].contested` | true / false | This judgment notes conflicting court views or a pending Supreme Court case |
| `defects_argued[].quote` + `quote_source` | `court` / `argument` | The court's words for the finding; for `not_decided` with no court words, the argument |
| `outcome.disposition` | `allowed`, `partly_allowed`, `dismissed`, `disposed`, `withdrawn` | Used only for the leakage check |
| `outcome.remanded` | true / false | Sent back to the officer |

**Defect types:** `hearing_75_4`, `adjournment_75_5`, `reply_not_considered`, `non_speaking_order`, `demand_beyond_scn`, `service_169`, `signature`, `summary_only`, `limitation`, `extension_notification_validity`, `consolidated_scn`, `section_74_ingredients`, `other_procedural` (meanings in `contracts.md`; role 3 confirms the provisions).

## Rules (the validator enforces 1–3)
1. **Never guess.** No value without a quote; no quote means no value.
2. **Dates** are written YYYY-MM-DD, whatever format the judgment uses.
3. **`defect_found` and `defect_rejected` must quote the court**, never a lawyer's argument.
4. **"Prima facie" is not a ruling.** A tentative view ("prima facie sufficient reason…", "prima facie view") is `not_decided`.
5. **`contested` comes from the judgment's own text** (it mentions other courts disagreeing, or a pending Supreme Court case). The system keeps its own list of contested points separately; we don't label from outside knowledge.
6. **Ignore quoted judgments.** Facts and outcomes inside a quoted precedent belong to that other case.
7. A **remand alone is not `defect_found`**: the court must say the mistake happened.

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
| 3 | Prima facie rejection (Garg) | `not_decided` (rule 4) |
| 4 | "Partly allowed, liberty to re-issue" (AR Traders) | `partly_allowed`, `remanded: false` |
| 5 | Appeal order also quashed (Agarwal); scrutiny notice before the SCN (Rajesh) | Events `appeal_dismissed`, `scrutiny_notice` |
| 6 | Same-day reply and hearing (Rajesh) | No extra field: `reply_due` = `hearing_date` already shows it |
| 7 | Should we keep amounts for the hand-off rule? | No; hand-off uses `recovery_or_attachment` events instead |

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
  "order_date": {"value": "2024-04-30", "quote": "The respondent no. 2 passed order dated 30.04.2024 under Section 73(9) of the Act", "para": 5},
  "events": [{"date": "2024-01-18", "type": "reply_filed", "quote": "The petitioner filed his reply on 18.01.2024", "para": 4}, "…"]},
 "findings": {
  "defects_argued": [{"type": "hearing_75_4", "finding": "defect_found", "contested": false,
    "quote": "This Court has repeatedly frowned on the action of the respondents in fixing identical date of reply and date of hearing",
    "quote_source": "court", "para": 12}, "…"],
  "outcome": {"disposition": "allowed", "remanded": true, "quote": "The matter is remanded back to …", "para": 18}},
 "review": {"status": "draft_for_review", "reviewed_by": [], "notes": "…"}}
```
