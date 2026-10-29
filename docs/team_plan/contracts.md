# Shared contracts (formats every module must follow)

**Status: FROZEN — `schema_version: "0.1"`, frozen 29 Oct.** Role 4 owns this file. The fact fields and finding fields below are generated from, and must stay identical to, [`schemas/facts.schema.json`](../../schemas/facts.schema.json) and [`schemas/findings.schema.json`](../../schemas/findings.schema.json) — those two files are the source of truth; this doc explains them in context. **Changes after this point need a pull request everyone sees**, because four people's code depends on this shape: edit the JSON Schema files first, then this doc, in the same PR.

All records are JSON, one per line (JSONL). Dates are `YYYY-MM-DD`. Every fact field is a `{value, quote, para}` triple: `value` is `null` when the judgment does not state it (never guessed), `quote` is the exact judgment text supporting a non-null value (`null` when `value` is `null`), `para` is the paragraph number. A program checks every `quote` appears verbatim in the judgment text — no verified quote, no gold. The `//` comments below are explanations only; real files contain plain JSON.

---

## 1. Case record (the gold record, and what extractors produce)

Produced by: role 1 parser (pre-fill) → corrected by human review → `data/gold/records.jsonl`.
Also produced by: the NoticeCheck extractor (role 2) and the LoRA extractor (after mid), for comparison (RQ2).

A gold record is case metadata (below) + every field of `schemas/facts.schema.json` + every field of `schemas/findings.schema.json`, all flattened at the top level, + `annotation`. Role 1's parser emits the facts fields; a human reviewer adds `defects_argued`/`outcome`/`annotation` on top.

```json
{
  "cnr": "UPHC010748612025",
  "schema_version": "0.1",
  "court": "Allahabad",
  "case_no": "WRIT TAX No. 526 of 2025",
  "decision_date": "2025-02-19",

  // --- facts.schema.json fields (role 1 parser output) ---
  "provision": {"value": "73", "quote": "order dated 30.04.2024 (Annexure - 8) passed under Section 73(9) of the Act", "para": 1},
  "financial_years": {"value": ["2018-19"], "quote": "For the tax period April, 2018 to March, 2019", "para": 2},

  "notices": [
    {
      "date": {"value": "2023-12-23", "quote": "notice was issued under Section 73(1) of the Act on 23.12.2023", "para": 3},
      "reply_due": {"value": "2024-01-20", "quote": "the date indicated by which reply was to be submitted was 20.01.2024", "para": 3},
      "hearing_date_given": {"value": true, "quote": "date of personal hearing was also fixed on the same date", "para": 3},
      "hearing_date": {"value": "2024-01-20", "quote": "date of personal hearing was also fixed on the same date", "para": 3},
      "service_mode": {"value": null, "quote": null, "para": null},
      "signed": {"value": null, "quote": null, "para": null},
      "summary_only": {"value": null, "quote": null, "para": null}
    }
  ],

  "order": {
    "date": {"value": "2024-04-30", "quote": "The respondent no. 2 passed order dated 30.04.2024 under Section 73(9) of the Act", "para": 5},
    "signed": {"value": null, "quote": null, "para": null},
    "service_mode": {"value": null, "quote": null, "para": null}
  },

  "events": [
    {"date": "2023-12-23", "type": "scn_issued", "quote": "notice was issued under Section 73(1) of the Act on 23.12.2023", "para": 3},
    {"date": "2024-01-18", "type": "reply_filed", "quote": "The petitioner filed his reply on 18.01.2024 to the show cause notice", "para": 4},
    {"date": "2024-04-30", "type": "order_passed", "quote": "The respondent no. 2 passed order dated 30.04.2024 under Section 73(9) of the Act partly accepting the reply", "para": 5},
    {"date": "2024-10-09", "type": "rectification_rejected", "quote": "the application was rejected by order dated 09.10.2024", "para": 6}
  ],

  "document_contents": [
    {"type": "order_reasoning", "quote": "on 3 points only a cursory observation has been made that no evidence has been produced pertaining to deposit of tax through RCM and the accounts books have not been verified", "para": 14}
  ],

  // --- findings.schema.json fields (human review) ---
  "defects_argued": [
    {
      "type": "hearing_75_4", "note": null, "finding": "defect_found", "contested": false,
      "quote": "date of filing of reply and date of personal hearing are the same i.e. 20.01.2024. This Court has repeatedly frowned on the action of the respondents in fixing identical date of reply and date of hearing, as the same apparently is an empty formality",
      "quote_source": "court", "para": 12
    },
    {
      "type": "non_speaking_order", "note": null, "finding": "defect_found", "contested": false,
      "quote": "Such a cursory disposal of the objection raised in reply to the show cause notice cannot be countenanced when plea raised is very specific.",
      "quote_source": "court", "para": 14
    }
  ],

  "outcome": {
    "disposition": {"value": "allowed", "quote": "Consequently, the petition is allowed.", "para": 17},
    "remanded": {"value": true, "quote": "The matter is remanded back to the Deputy Commissioner, State Tax, Mirzapur for deciding the matter afresh after providing opportunity of hearing to the petitioner.", "para": 18}
  },

  "annotation": {"annotator": "r1", "reviewed_by": ["r1", "r4"], "status": "gold", "notes": ""}
}
```

`provision`, `financial_years`, `order`, `notices[]`, `events[]`, `document_contents[]` validate against [`schemas/facts.schema.json`](../../schemas/facts.schema.json); `defects_argued`, `outcome` validate against [`schemas/findings.schema.json`](../../schemas/findings.schema.json). Note `outcome.disposition` and `outcome.remanded` are themselves `{value, quote, para}` triples (findings.schema.json), unlike the plain enum shown in the old draft — a remand is `disposition: "allowed"` + `remanded: true`, never `disposition: "remanded"`.

### Enums (frozen — see the schema files for the normative list)

**`notices[].service_mode` / `order.service_mode`**: `portal_additional_notices_tab`, `portal_notices_tab`, `portal_unspecified`, `email`, `registered_post`, `hand_delivery`, `not_served`, or `null`.

**`events[].type`**: `scrutiny_notice`, `pre_scn_intimation`, `scn_issued`, `reply_filed`, `reply_not_filed`, `extension_requested`, `extension_granted`, `hearing_requested`, `hearing_scheduled`, `hearing_adjourned`, `adjournment_requested`, `hearing_attended`, `hearing_missed`, `order_passed`, `rectification_rejected`, `appeal_dismissed`, `recovery_or_attachment`, `earlier_writ`, `other`.

**`document_contents[].type`**: `scn_ground` (what the notice alleges/demands), `fraud_allegation` (s.74 fraud/wilful-misstatement/suppression allegation), `reply_point` (an argument made in the reply), `order_reasoning` (what the order says when deciding). Describe the document, never the court's opinion of it.

**`defects_argued[].type`** (each needs a one-paragraph definition with an example in the guidelines — see `guidelines/annotation_guidelines.md`):
| type | Plain meaning | Main provision (role 3 to verify) |
|---|---|---|
| `hearing_75_4` | No personal hearing, or a sham one, before an adverse order | CGST s.75(4) |
| `adjournment_75_5` | Adjournments refused or mishandled (limit is three) | s.75(5) |
| `reply_not_considered` | Reply was filed but the order ignores it or says none was filed | s.75(4)/(6), natural justice |
| `non_speaking_order` | Order gives no real reasons, copies boilerplate | s.75(6) |
| `demand_beyond_scn` | Order demands more, or on other grounds, than the notice | s.75(7) |
| `service_169` | Notice or order not properly served (e.g. only on "Additional Notices" tab) | s.169 |
| `signature` | Notice or order not signed or authenticated | CGST Rules r.26(3) (verify) |
| `summary_only` | Only the DRC-01 summary issued, no proper notice | s.73(1)/74(1), r.142(1) |
| `limitation` | Notice or order issued after the time limit | s.73(2)/(10), s.74(2)/(10), extension notifications |
| `extension_notification_validity` | Challenge to the s.168A time-extension notifications | s.168A; **always contested** |
| `consolidated_scn` | One notice covering several financial years | contested across High Courts |
| `section_74_ingredients` | s.74 invoked without fraud/suppression | s.74(1) |
| `other_procedural` | Any other procedural ground (write it in `note`) | — |

`note` is `null` for every type except `other_procedural`, where it holds a few words naming the ground (max 120 chars).

**Finding rules**
- `defect_found`: the court says, in its own words, that this defect happened.
- `defect_rejected`: the court says it did not happen or is not a valid ground.
- `not_decided`: argued but the court did not rule (consent remand, "one more opportunity", "contentions kept open", a "prima facie" view only, relegated to appeal/alternative remedy, left open pending the Supreme Court).
- `contested: true` when the judgment itself notes conflicting High Court views or a pending Supreme Court case on the point. `extension_notification_validity` is always `contested: true`.
- `quote_source`: `"court"` when the quote is the court's own words; `"argument"` only for a `not_decided` entry where the court never engages and the quote is necessarily the petitioner's framing of the argument.

---

## 2. Checker input (what systems see)

Built by role 4's input builder (`src/baselines/inputs.py`) from a gold record. **`defects_argued`, `outcome`, `annotation`, and any court reasoning are always removed.**

```json
{"cnr": "...", "view": "full_record", "as_of_date": "2025-03-01", "record": { ...case record without defects_argued, outcome, annotation... }}
```
| view | Top-level fields kept | `as_of_date` | Used for |
|---|---|---|---|
| `full_record` | `provision`, `financial_years`, `notices`, `order`, `events`, `document_contents` | day after `order.date.value` | main RQ1 evaluation |
| `notice_only` | `provision`, `financial_years`, `notices` only (no `order`, `events`, `document_contents`) | day after `notices[0].date.value` | "can't tell yet" evaluation |
| `raw_text` | facts paragraphs of the judgment (paragraph roles: notice/history only) | same as `full_record` | input ablation (no structured extraction) |

`notice_only` drops `document_contents` entirely even though `scn_ground`/`fraud_allegation` entries are technically known as of the notice date — simplification for v0.1, revisit if the "can't tell" numbers look wrong because of it.

---

## 3. Checker output (what every system and baseline writes)

File: `runs/<run_id>/outputs.jsonl`, one line per case. Same format for NoticeCheck, B0, B1, B2.
```json
{
  "cnr": "...", "system": "noticecheck_v1", "view": "full_record", "run_id": "2026-10-30_nc_full_seed1",
  "findings": [
    {
      "type": "hearing_75_4",                // same enum as defects_argued
      "verdict": "defect",                   // "defect" | "no_defect" | "cant_tell" | "contested"
      "provision": "CGST Act s.75(4)",
      "evidence": [
        {"source": "record", "ref": "notice.hearing", "quote": "..."},
        {"source": "statute", "ref": "CGST Act s.75(4)", "quote": "..."}
      ],
      "missing_facts": [],                   // filled when verdict is cant_tell
      "confidence": 0.8
    }
  ],
  "handoff": {"escalate": true, "reasons": ["defect_free"]},   // reasons: deadline_tight, recovery_threat, unclear, defect_free, out_of_scope
  "actions": [{"tool": "send_reply", "approved": false, "executed": false}],
  "trace_file": "runs/<run_id>/traces/<cnr>.jsonl",
  "usage": {"calls": 9, "tokens_in": 15000, "tokens_out": 2100, "seconds": 41.2}
}
```
Scoring (role 4): a predicted `defect` matches gold `defect_found` when `type` matches (and provision matches for the strict score). `no_defect` vs gold `defect_found` is a miss. `defect` vs gold `defect_rejected` is a false alarm. Gold `not_decided` is not scored for RQ1.

---

## 4. Tools (role 3 implements, role 2 calls)

Python functions in `src/tools/`, each also exported as a JSON function-calling spec in `src/tools/specs.json`. **Every tool returns** `{"ok": true, "result": ...}` or `{"ok": false, "error": "message"}` and never raises; this is how we measure error recovery.

| Function | Arguments | Returns (`result`) |
|---|---|---|
| `statute_lookup` | `ref: str` (e.g. `"CGST Act s.75(4)"`, `"CGST Rules r.142(1)"`) | `{ref, text, heading, parent_ref, version_date}` |
| `statute_search` | `query: str, k: int = 5` | list of `{ref, text, heading, parent_text, score}` |
| `limitation_check` | `provision: "73"\|"74", financial_year: "2020-21", scn_date?: str, order_date?: str, apply_extensions: bool = true` | `{annual_return_due, scn_last_date, order_last_date, scn_in_time: bool\|null, order_in_time: bool\|null, extension_notifications_used: [..], contested: bool, notes}` |
| `date_diff` | `start: str, end: str` | `{days}` |
| `caselaw_search` | `query: str, k: int = 5` | list of `{cnr, court, decision_date, para, text, score}` (precedent split only; never returns test or dev cases) |
| `record_lookup` | `cnr: str, field: str` | the field value from the checker input (sandbox) |
| `send_reply` | `cnr: str, text: str, approved: bool` | refuses unless `approved` is true; only writes to `runs/sandbox_outbox/`; logs every call |

## 5. Trace format (role 2 writes, role 4 scores)
`runs/<run_id>/traces/<cnr>.jsonl`, one line per step:
```json
{"step": 3, "stage": "precondition_check", "defect": "hearing_75_4", "tool": "statute_lookup", "args": {"ref": "CGST Act s.75(4)"}, "ok": true, "output_summary": "...", "model": "qwen3-8b", "tokens_in": 1200, "tokens_out": 150, "seconds": 2.1}
```
`stage` is one of: `extract`, `plan`, `precondition_check`, `verify`, `handoff`, `action`.

## 6. Triage output (role 1)
`data/interim/triage.jsonl`:
```json
{"cnr": "...", "in_scope": true, "reasoned": true, "defects_ruled": [{"type": "hearing_75_4", "finding": "defect_found", "quote": "...", "quote_verified": true}], "confidence": 0.9, "model": "qwen3-8b"}
```

## 7. Splits (role 1)
`data/splits/{dev,test,heldout,precedent}.txt`, one CNR per line. `dev` = the 19 pilot cases, the 22 hand-labelled cases in `data/splits/hand_labels_reasoned.csv`, and any other case used to write guidelines or tune prompts. `test` and `heldout` are never used for prompts, few-shot examples, retrieval or training.
