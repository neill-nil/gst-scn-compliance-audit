"""Pre-fill a schema 0.1 case record from a judgment with a frontier model (2 calls: facts, findings).

The output is a draft for human review, never gold by itself. Every quote is later checked by
verify_quotes.py and every record by schema.py.

Usage:
    python -m src.prefill.prefill --share r2            # your share from data/splits/prefill_shares.csv
    python -m src.prefill.prefill <cnr> [<cnr> ...]      # specific cases
Records go to data/prefill/v1/<cnr>.json (change with --out). Finished cases are skipped, so a run
stopped by the daily quota continues where it left off when started again.
"""
import argparse
import csv
import json
from pathlib import Path

from src.common.llm import complete
from src.prefill.schema import FACTS_SCHEMA, FINDINGS_SCHEMA, SCHEMA_VERSION, validate_record
from src.prefill.verify_quotes import ROOT, judgment_paragraphs, verify

PROMPT_VERSION = "2026-10-29.1"  # change whenever COMMON / FACTS_TASK / FINDINGS_TASK change

COMMON = """You are reading an Indian High Court judgment about a GST demand proceeding (show cause notice under
section 73 or 74 of the CGST/SGST Act, then a demand order). The judgment is given paragraph by paragraph;
the number in [brackets] is the paragraph number to report as "para" ([0] is the header).

Rules:
- Never guess. If the judgment does not state something, use null (or leave a list empty).
- Every quote must be copied exactly, word for word, from ONE paragraph of the judgment, and kept short
  (one sentence or less). The para must be the paragraph the quote comes from. Do not correct, reword or
  tidy the text, even if it has typos, stray numbers or odd characters. Skip text that is not readable
  English (garbled characters).
- Write dates as YYYY-MM-DD whatever format the judgment uses. Financial years as "2018-19".
- Ignore other judgments quoted inside this one: their facts, notices and findings belong to other cases.
"""

FACTS_TASK = """Task: extract the FACTS of this proceeding (what happened before the case reached the court).
- provision: "73" or "74", the section under which the notice / demand order was issued.
- notices: one entry per show cause notice (Form DRC-01) in this proceeding, usually one. Add the entry
  whenever the judgment states ANY fact about the notice, even if its date is unknown.
  hearing_date_given is false if the notice gave no hearing date, wrote "NA", or no date was fixed
  (this may be stated by either side, e.g. the department's counsel admitting no date was fixed).
- financial_years: convert a stated tax period to financial years (April to March), e.g. "July 2019 to
  June 2021" -> ["2019-20", "2020-21", "2021-22"].
- order: the demand order being challenged (DRC-07 / order under s.73(9) or 74(9)).
- events: every step in date order, including steps without a date (scrutiny notice, DRC-01A
  intimation, hearing attended). If one sentence states two steps ("the petitioner neither replied nor
  attended the hearing"), add two events. Use reply_not_filed or hearing_missed only when the judgment says so.
  A request is dated the day it was made; hearing_adjourned is dated the hearing day that was put off,
  and the new hearing date is a separate hearing_scheduled event.
- document_contents: what the notice, the reply and the order SAID, as the judgment reports it, only
  where it bears on a procedural complaint. Describe the document, never the court's opinion of it:
  "the order states that the invoices produced were not verified" is allowed; "the order is cursory" or
  "the order does not consider the reply" is the court's opinion and must NOT be included.
- Do not report what the court decided; that is a separate task.
"""

FINDINGS_TASK = """Task: list the PROCEDURAL complaints the taxpayer (petitioner) made against the tax department,
and what the High Court decided on each, plus the outcome.
- defects_argued: one entry per complaint type that the petitioner actually argued. Only these types:
  hearing_75_4 (no personal hearing or a sham one before the order), adjournment_75_5 (adjournments
  refused or mishandled), reply_not_considered (reply filed but ignored), non_speaking_order (order gives
  no real reasons), demand_beyond_scn (order goes beyond the notice, s.75(7)), service_169 (notice or order
  not properly served), signature (notice or order not signed), summary_only (only the DRC-01 summary, no
  detailed notice), limitation (notice or order issued after the time limit), extension_notification_validity
  (challenge to the s.168A extension notifications themselves; then do not also add limitation unless a
  separate lateness argument is made), consolidated_scn (one notice for several financial years),
  section_74_ingredients (s.74 used without fraud/suppression), other_procedural (any other procedural
  ground; say what it is in "note"). "note" is null for every other type.
- finding:
  defect_found = the court says in its own words that the department made this mistake.
  defect_rejected = the court says the mistake did not happen or is not a valid ground.
  not_decided = argued but no firm ruling: consent remand, "one more opportunity", "contentions kept open",
  "prima facie" views, left to the appeal, pending in the Supreme Court.
  If the court sets the order aside because the notice was uploaded only under the portal's "Additional
  Notices" tab, that is service_169 defect_found.
  A remand alone is NOT defect_found. Granting another chance "in the interest of justice" or "on
  equitable grounds" is not a finding either way.
  If the court says a point involves disputed facts, cannot be decided without the records, or should be
  raised in the appeal, it is not_decided, even when the petition is dismissed. Use defect_rejected only
  when the court itself says this complaint is wrong.
  Check each complaint separately: e.g. a complaint about the hearing (hearing_75_4) and one about
  adjournments (adjournment_75_5) are two entries if both were argued.
- quote / quote_source: for defect_found and defect_rejected, quote the COURT's own words (quote_source
  "court"), never a lawyer's argument. For not_decided with no court words on it, quote the argument
  (quote_source "argument").
- contested: true only if this judgment itself mentions conflicting court decisions or a pending Supreme
  Court case on that point.
- outcome.disposition: allowed / partly_allowed / dismissed / disposed / withdrawn, as the judgment says;
  remanded = true if the matter goes back to the officer to decide again. Quashing with liberty to issue
  a fresh notice is not a remand (remanded = false).
"""


def judgment_text(cnr: str) -> str:
    return "\n\n".join(f"[{p['n']}] {p['text']}" for p in judgment_paragraphs(cnr))


def prefill(cnr: str, backend: str = "gemini", model: str | None = None) -> dict:
    text = judgment_text(cnr)
    parts, usage, errors = {}, [], []
    for part, task, schema in (("facts", FACTS_TASK, FACTS_SCHEMA), ("findings", FINDINGS_TASK, FINDINGS_SCHEMA)):
        msg = f"{COMMON}\n{task}\nJUDGMENT:\n{text}"
        for temperature in (0.0, 0.4):  # a second, slightly varied try if both strict attempts were invalid
            out = complete(backend, [{"role": "user", "content": msg}], json_schema=schema, max_tokens=8192,
                           model=model, temperature=temperature, tag=f"prefill:{part}")
            if out["json"] is not None:
                break
        parts[part] = out["json"]
        usage.append({k: out[k] for k in ("tokens_in", "tokens_out", "seconds", "cached")})
        if out.get("error"):
            errors.append(f"{part}: {out['error']}")
    rec = {"cnr": cnr, "schema_version": SCHEMA_VERSION, "facts": parts["facts"], "findings": parts["findings"],
           "review": {"status": "prefill", "drafted_by": out["model"], "prompt_version": PROMPT_VERSION,
                      "reviewed_by": [], "notes": "; ".join(errors)},
           "usage": usage}
    if rec["facts"] is not None and rec["findings"] is not None:
        rec["checks"] = {"schema_problems": validate_record(rec),
                         "quotes_not_found": [q["where"] for q in verify(rec) if not q["found"]]}
    return rec


def share_cnrs(share: str) -> list[str]:
    with open(ROOT / "data" / "splits" / "prefill_shares.csv", newline="", encoding="utf-8") as f:
        return [r["cnr"] for r in csv.DictReader(f) if r["share"] == share]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--share", choices=["r1", "r2", "r3", "r4"])
    ap.add_argument("--out", default=str(ROOT / "data" / "prefill" / "v1"))
    ap.add_argument("--backend", default="gemini")
    ap.add_argument("--model")
    ap.add_argument("cnrs", nargs="*")
    a = ap.parse_args()
    cnrs = a.cnrs + (share_cnrs(a.share) if a.share else [])
    if not cnrs:
        ap.error("give --share or CNRs")
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    done = sum((out_dir / f"{c}.json").exists() for c in cnrs)
    print(f"{len(cnrs)} cases, {done} already done, writing to {out_dir}")
    tally = {"ok": 0, "flagged": 0, "failed": 0, "skipped": 0}
    for cnr in cnrs:
        out_file = out_dir / f"{cnr}.json"
        if out_file.exists():  # resume: a quota-limited run can be restarted the next day
            continue
        try:
            rec = prefill(cnr, a.backend, a.model)
        except RuntimeError as e:  # e.g. daily quota used up; stop and rerun later
            print(cnr, "STOPPED:", str(e)[:200])
            break
        except (FileNotFoundError, KeyError) as e:  # PDF not downloaded / CNR not in manifest
            print(cnr, "SKIPPED (no PDF; run scripts/fetch_data.py --reasoned-only):", e)
            tally["skipped"] += 1
            continue
        if rec["facts"] is None or rec["findings"] is None:
            print(cnr, "FAILED:", rec["review"]["notes"][:200])
            tally["failed"] += 1
            continue
        out_file.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        c = rec["checks"]
        flagged = bool(c["schema_problems"] or c["quotes_not_found"])
        tally["flagged" if flagged else "ok"] += 1
        print(cnr, "ok" if not flagged else
              f"saved, flag for review: {len(c['schema_problems'])} rule problem(s), "
              f"{len(c['quotes_not_found'])} quote(s) not found")
    left = sum(not (out_dir / f"{c}.json").exists() for c in cnrs)
    print(f"this run: {tally}; still to do: {left}" + (" (run the same command again)" if left else " - all done"))


if __name__ == "__main__":
    main()
