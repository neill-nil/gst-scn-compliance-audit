# Shared contracts (formats every module must follow)

**Status: DRAFT v0.** Role 4 owns this file. The team edits it in the schema meeting on 27 Oct and then freezes it as `schema_version: "0.1"`. After freezing, changes need a pull request that everyone sees, because four people's code depends on it.

All records are JSON, one per line (JSONL). Dates are `YYYY-MM-DD`. Unknown values are `null`, never guessed. The `//` comments below are explanations only; real files contain plain JSON.

---

## 1. Case record (the gold record, and what extractors produce)

Produced by: role 1 parser (pre-fill) → corrected by human review → `data/gold/records.jsonl`.
Also produced by: the NoticeCheck extractor (role 2) and the LoRA extractor (after mid), for comparison (RQ2).

```json
{
  "cnr": "DLHC010209162025",
  "schema_version": "0.1",
  "court": "Delhi",
  "case_no": "W.P.(C) 4781/2025",
  "decision_date": "2025-07-29",

  "proceeding": {
    "provision": "73",                      // "73" | "74" | "unclear"
    "tax_period_from": "2020-04",            // YYYY-MM or null
    "tax_period_to": "2021-03",
    "financial_years": ["2020-21"],          // more than one => consolidated notice
    "authority": "Sales Tax Officer Class II, AVATO",
    "jurisdiction": "state",                 // "state" | "central" | "unclear"
    "evidence": [{"field": "provision", "quote": "...", "para": 12}]
  },

  "notice": {
    "form": "DRC-01",                        // "DRC-01" | "DRC-01A" | "other" | null
    "date": "2024-11-30",
    "reply_due": "2024-12-30",
    "signed": null,                          // true | false | null (not stated)
    "service_mode": "portal_unspecified",    // see enum below
    "summary_only": null,                    // true if only the DRC-01 summary was issued, no detailed notice
    "hearing": {"date": "2025-01-17", "time": "13:15", "venue": "Ward Office, 13th Floor", "stated_as_na": false},
    "demand_amount": null,                   // rupees, number, or null
    "evidence": [{"field": "notice.hearing.date", "quote": "Date of personal hearing 17-01-2025", "para": 7}]
  },

  "events": [
    {"date": "2024-12-27", "type": "extension_requested", "details": "15 days sought", "quote": "...", "para": 8},
    {"date": "2025-01-20", "type": "hearing_adjourned", "details": "to 2025-01-27", "quote": "...", "para": 9}
  ],

  "order": {
    "form": "DRC-07",                        // "DRC-07" | "other" | null
    "date": "2025-02-28",
    "demand_amount": 56352147,
    "evidence": [{"field": "order.date", "quote": "...", "para": 12}]
  },

  "defects_argued": [
    {
      "type": "limitation",                  // see defect enum below
      "finding": "defect_rejected",          // "defect_found" | "defect_rejected" | "not_decided"
      "contested": true,                     // courts disagree on this point
      "provision": "CGST Act s.73(10)",
      "quote": "...",                        // the court's own words giving the finding
      "para": 36
    }
  ],

  "outcome": {
    "disposition": "dismissed",              // "allowed" | "partly_allowed" | "dismissed" | "disposed" | "remanded"
    "remanded": false,
    "quote": "...", "para": 54
  },

  "annotation": {"annotator": "r1", "reviewed_by": ["r1", "r4"], "status": "gold", "notes": ""}
}
```

### Enums (draft — finalise on 27 Oct)

**`events[].type`**: `scn_issued`, `scn_uploaded`, `reminder_issued`, `reply_filed`, `extension_requested`, `extension_granted`, `extension_refused`, `hearing_scheduled`, `hearing_adjourned`, `hearing_attended`, `hearing_missed`, `order_passed`, `order_uploaded`, `rectification_filed`, `appeal_filed`, `other`.

**`notice.service_mode`**: `portal_additional_notices_tab`, `portal_notices_tab`, `portal_unspecified`, `email`, `registered_post`, `hand_delivery`, `not_served`, `unclear`.

**`defects_argued[].type`** (each needs a one-paragraph definition with an example in the guidelines):
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
| `other_procedural` | Any other procedural ground (write it in `notes`) | — |

**Finding rules**
- `defect_found`: the court says, in its own words, that this defect happened.
- `defect_rejected`: the court says it did not happen or is not a valid ground.
- `not_decided`: argued but the court did not rule (consent remand, "one more opportunity", "contentions kept open", relegated to appeal, left open pending the Supreme Court).
- `contested: true` when the judgment itself notes conflicting High Court views or a pending Supreme Court case on the point.

---

## 2. Checker input (what systems see)

Built by role 4's input builder from a gold record. **Court findings, outcome and court reasoning are always removed.**

```json
{"cnr": "...", "view": "full_record", "as_of_date": "2025-03-01", "record": { ...case record without defects_argued, outcome, annotation... }}
```
| view | Contents | Used for |
|---|---|---|
| `full_record` | proceeding, notice, events, order | main RQ1 evaluation |
| `notice_only` | proceeding + notice only (no events, no order) | "can't tell yet" evaluation |
| `raw_text` | facts paragraphs of the judgment (paragraph roles: notice/history only) | input ablation (no structured extraction) |

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
