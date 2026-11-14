"""End-to-end inputs: turn an extractor's output (RQ2) into checker inputs, so NoticeCheck can run on facts that
no human made (judgment -> extractor -> NoticeCheck).

Each extracted record is first made schema-valid with the same rules for every extractor: values of the wrong type
or outside the allowed list become null, unknown event types become "other", malformed entries are dropped, and an
output cut off at the token limit is salvaged (eval.score_extraction.salvage). Case metadata (court, case number,
decision date) comes from the gold record; facts never do.

Usage:
    python -m scripts.build_e2e_inputs --run runs/rq2_tuned      -> runs/rq2_tuned/checker_full_record.jsonl
"""
import argparse
import json
import re
from pathlib import Path

from eval.score_extraction import salvage
from src.baselines.inputs import METADATA_FIELDS, _day_after
from src.prefill.schema import FACTS_SCHEMA

ROOT = Path(__file__).resolve().parents[1]
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FY = re.compile(r"^\d{4}-\d{2}$")
P = FACTS_SCHEMA["properties"]
SERVICE = set(P["notices"]["items"]["properties"]["service_mode"]["properties"]["value"]["anyOf"][0]["enum"])
EVENT_TYPES = set(P["events"]["items"]["properties"]["type"]["enum"])
DOC_TYPES = set(P["document_contents"]["items"]["properties"]["type"]["enum"])


def _str(x):
    return x if isinstance(x, str) and x.strip() else None


def _int(x):
    return x if isinstance(x, int) and not isinstance(x, bool) else None


def fact(node, ok) -> dict:
    """A clean {value, quote, para}; value kept only if ok(value)."""
    node = node if isinstance(node, dict) else {"value": node}
    v = node.get("value")
    if not ok(v):
        return {"value": None, "quote": None, "para": None}
    return {"value": v, "quote": _str(node.get("quote")), "para": _int(node.get("para"))}


is_date = lambda v: isinstance(v, str) and bool(DATE.match(v))
is_bool = lambda v: isinstance(v, bool)


def clean(facts) -> dict:
    facts = facts if isinstance(facts, dict) else {}
    prov = facts.get("provision")
    if isinstance(prov, dict) and isinstance(prov.get("value"), int):
        prov = dict(prov, value=str(prov["value"]))
    fys = facts.get("financial_years")
    out = {
        "provision": fact(prov, lambda v: v in ("73", "74")),
        "financial_years": fact(fys, lambda v: isinstance(v, list) and v and all(isinstance(y, str) and FY.match(y) for y in v)),
        "notices": [], "order": {}, "events": [], "document_contents": []}
    for n in facts.get("notices") or []:
        if isinstance(n, dict):
            out["notices"].append({
                "date": fact(n.get("date"), is_date), "reply_due": fact(n.get("reply_due"), is_date),
                "hearing_date_given": fact(n.get("hearing_date_given"), is_bool),
                "hearing_date": fact(n.get("hearing_date"), is_date),
                "service_mode": fact(n.get("service_mode"), lambda v: v in SERVICE),
                "signed": fact(n.get("signed"), is_bool), "summary_only": fact(n.get("summary_only"), is_bool)})
    o = facts.get("order") if isinstance(facts.get("order"), dict) else {}
    out["order"] = {"date": fact(o.get("date"), is_date), "signed": fact(o.get("signed"), is_bool),
                    "service_mode": fact(o.get("service_mode"), lambda v: v in SERVICE)}
    for e in facts.get("events") or []:
        if isinstance(e, dict) and _str(e.get("quote")):
            out["events"].append({"date": e.get("date") if is_date(e.get("date")) else None,
                                  "type": e.get("type") if e.get("type") in EVENT_TYPES else "other",
                                  "quote": e["quote"], "para": _int(e.get("para"))})
    for d in facts.get("document_contents") or []:
        if isinstance(d, dict) and d.get("type") in DOC_TYPES and _str(d.get("quote")):
            out["document_contents"].append({"type": d["type"], "quote": d["quote"], "para": _int(d.get("para"))})
    # repeated entries (a looping model) are dropped, and lists are cut to the schema's maximum length
    for key in ("notices", "events", "document_contents"):
        seen, kept = set(), []
        for item in out[key]:
            k = json.dumps(item, sort_keys=True)
            if k not in seen:
                seen.add(k)
                kept.append(item)
        out[key] = kept[: P[key].get("maxItems", len(kept))]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="a run dir with outputs*.jsonl from src.rq2.extract")
    args = ap.parse_args()
    import jsonschema

    run = ROOT / args.run
    gold = {r["cnr"]: r for r in map(json.loads, open(ROOT / "data/gold/records.jsonl", encoding="utf-8"))}
    import csv  # cases outside the gold set (the fresh set): metadata from the manifest
    for m in csv.DictReader(open(ROOT / "data/manifests/screened.csv", encoding="utf-8")):
        if m["cnr"] not in gold and m["bucket"] != "out_of_scope":
            gold[m["cnr"]] = {"cnr": m["cnr"], "schema_version": "0.1", "court": m["court_name"],
                              "case_no": m["title"].split(" of ")[0], "decision_date": m["decision_date"]}
    order = {c: i for i, c in enumerate(gold)}
    rows = [json.loads(l) for p in sorted(run.glob("outputs*.jsonl")) for l in open(p, encoding="utf-8")]
    validator = jsonschema.Draft202012Validator(FACTS_SCHEMA)
    salvaged = 0
    out_path = run / "checker_full_record.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for r in sorted(rows, key=lambda r: order[r["cnr"]]):
            facts = r.get("facts")
            if facts is None:
                facts, salvaged = salvage(r.get("text")), salvaged + 1
            facts = clean(facts)
            errors = list(validator.iter_errors(facts))
            assert not errors, (r["cnr"], errors[0].message)
            record = {k: v for k, v in gold[r["cnr"]].items() if k in METADATA_FIELDS}
            record.update(facts)
            f.write(json.dumps({"cnr": r["cnr"], "view": "full_record", "as_of_date": _day_after(facts["order"]["date"]["value"]),
                                "record": record, "extractor": r.get("system")}, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} cases to {out_path} ({salvaged} salvaged from cut-off output)")


if __name__ == "__main__":
    main()
