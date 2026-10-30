"""Build checker inputs from gold records, per docs/team_plan/contracts.md section 2.

For each gold record, emits the views every system/baseline sees -- full_record, notice_only,
raw_text -- with defects_argued, outcome, annotation and any court reasoning always removed.

Usage:
    python -m src.baselines.inputs --gold data/gold/records.jsonl --out data/interim/inputs --view full_record notice_only raw_text

Leakage test (role4_schema_eval.md step 8): give B1 the full_record input and ask it ONLY to
predict the case outcome. B1 itself lives in src/baselines/b1_plain.py (depends on role 1's
llm.py); this module scores whatever predictions B1 produces, so the test can be reported without
this file depending on a model call:
    python -m src.baselines.inputs --leakage-report runs/<run_id>/leakage_predictions.jsonl --gold data/gold/records.jsonl
`leakage_predictions.jsonl` lines look like {"cnr": "...", "predicted_disposition": "allowed"}.
"""
import argparse
import json
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

GOLD_ONLY_FIELDS = {"defects_argued", "outcome", "annotation"}
FULL_RECORD_FIELDS = {"provision", "financial_years", "notices", "order", "events", "document_contents"}
NOTICE_ONLY_FIELDS = {"provision", "financial_years", "notices"}
METADATA_FIELDS = {"cnr", "schema_version", "court", "case_no", "decision_date"}

VIEWS = ("full_record", "notice_only", "raw_text")


# ---------------------------------------------------------------------------
# View construction
# ---------------------------------------------------------------------------

def _unwrap(node):
    """{"value": x, "quote": ..., "para": ...} -> x; passes through anything else unchanged."""
    if isinstance(node, dict) and set(node.keys()) >= {"value", "quote", "para"}:
        return node["value"]
    return node


def _day_after(date_str: str | None) -> str | None:
    if not date_str:
        return None
    return (date.fromisoformat(date_str) + timedelta(days=1)).isoformat()


def _order_date(record: dict) -> str | None:
    return _unwrap(record.get("order", {}).get("date"))


def _first_notice_date(record: dict) -> str | None:
    notices = record.get("notices") or []
    if not notices:
        return None
    return _unwrap(notices[0].get("date"))


def strip_gold_only(record: dict, keep_fact_fields: set[str]) -> dict:
    """METADATA_FIELDS + whichever fact fields the view allows; never defects_argued/outcome/annotation."""
    out = {k: v for k, v in record.items() if k in METADATA_FIELDS}
    for k in keep_fact_fields:
        if k in record:
            out[k] = record[k]
    assert not (GOLD_ONLY_FIELDS & out.keys()), "leak: gold-only field survived stripping"
    return out


def build_raw_text(record: dict) -> list[dict]:
    """Pseudo "raw text" ablation input: the verbatim quotes behind the facts fields, in paragraph
    order, excluding document_contents.order_reasoning (that's the order's own reasoning, closer to
    court reasoning than to a notice/history fact -- kept out per contracts.md section 2's
    "paragraph roles: notice/history only"). This stands in for role 1's paragraph-role field if/when
    one is added to facts.schema.json; revisit this function then rather than duplicating logic."""
    quotes: list[dict] = []

    def add(node):
        if isinstance(node, dict) and "quote" in node and node.get("quote"):
            quotes.append({"para": node.get("para"), "quote": node["quote"]})

    add(record.get("provision"))
    add(record.get("financial_years"))
    for notice in record.get("notices") or []:
        for field in ("date", "reply_due", "hearing_date_given", "hearing_date", "service_mode", "signed", "summary_only"):
            add(notice.get(field))
    order = record.get("order") or {}
    for field in ("date", "signed", "service_mode"):
        add(order.get(field))
    for event in record.get("events") or []:
        if event.get("quote"):
            quotes.append({"para": event.get("para"), "quote": event["quote"]})
    for dc in record.get("document_contents") or []:
        if dc.get("type") != "order_reasoning" and dc.get("quote"):
            quotes.append({"para": dc.get("para"), "quote": dc["quote"]})

    quotes.sort(key=lambda q: (q["para"] is None, q["para"]))
    return quotes


def build_view(record: dict, view: str) -> dict:
    if view == "full_record":
        return {
            "cnr": record["cnr"], "view": view,
            "as_of_date": _day_after(_order_date(record)),
            "record": strip_gold_only(record, FULL_RECORD_FIELDS),
        }
    if view == "notice_only":
        return {
            "cnr": record["cnr"], "view": view,
            "as_of_date": _day_after(_first_notice_date(record)),
            "record": strip_gold_only(record, NOTICE_ONLY_FIELDS),
        }
    if view == "raw_text":
        return {
            "cnr": record["cnr"], "view": view,
            "as_of_date": _day_after(_order_date(record)),
            "record": {"paragraphs": build_raw_text(record)},
        }
    raise ValueError(f"unknown view: {view}")


# ---------------------------------------------------------------------------
# Leakage test (role4_schema_eval.md Tue step 8)
# ---------------------------------------------------------------------------

def majority_class(labels: list[str]) -> tuple[str, float]:
    counts = Counter(labels)
    label, n = counts.most_common(1)[0]
    return label, n / len(labels)


def score_leakage(gold: dict[str, dict], predictions: dict[str, str]) -> dict:
    """predictions: cnr -> predicted outcome.disposition.value (model saw ONLY full_record, asked
    only for the outcome). If accuracy is clearly above the majority-class rate, the full_record
    view leaks outcome-predictive signal (likely via defects_argued/outcome having not been fully
    stripped, or a proxy like a late event date) -- find and remove it before trusting RQ1 numbers."""
    labels = [_unwrap(r["outcome"]["disposition"]) for r in gold.values()]
    maj_label, maj_rate = majority_class(labels)
    n = correct = 0
    for cnr, record in gold.items():
        if cnr not in predictions:
            continue
        n += 1
        gold_label = _unwrap(record["outcome"]["disposition"])
        if predictions[cnr] == gold_label:
            correct += 1
    accuracy = correct / n if n else None
    return {
        "n_scored": n, "majority_class": maj_label, "majority_rate": maj_rate,
        "accuracy": accuracy,
        "leak_suspected": accuracy is not None and accuracy > maj_rate + 0.10,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gold", type=Path, default=Path("data/gold/records.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("data/interim/inputs"))
    ap.add_argument("--view", nargs="+", choices=VIEWS, default=list(VIEWS))
    ap.add_argument("--leakage-report", type=Path, default=None,
                     help="score an existing leakage_predictions.jsonl instead of building views")
    args = ap.parse_args()

    gold_records = load_jsonl(args.gold)

    if args.leakage_report is not None:
        gold = {r["cnr"]: r for r in gold_records}
        preds = {p["cnr"]: p["predicted_disposition"] for p in load_jsonl(args.leakage_report)}
        result = score_leakage(gold, preds)
        print(json.dumps(result, indent=2))
        return

    args.out.mkdir(parents=True, exist_ok=True)
    for view in args.view:
        out_path = args.out / f"{view}.jsonl"
        with out_path.open("w") as f:
            for record in gold_records:
                f.write(json.dumps(build_view(record, view)) + "\n")
        print(f"wrote {len(gold_records)} cases to {out_path}")


if __name__ == "__main__":
    main()
