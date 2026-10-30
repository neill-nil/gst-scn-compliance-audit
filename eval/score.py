"""Score a system run against gold records, per docs/team_plan/contracts.md and role4_schema_eval.md.

Usage: python -m eval.score --gold data/gold/records.jsonl --run runs/<run_id> --split test
Writes a results JSON to --out (default runs/<run_id>/score_<split>.json) and prints a summary.

Several mappings below (RULE_DETECTABLE_TYPES, REQUIRED_FACT_FIELDS, EXPECTED_TOOLS_BY_DEFECT) are
PROPOSED DEFAULTS pending team sign-off at the schema meeting / in guidelines/annotation_guidelines.md.
They are kept as plain constants so one line changes them once decided; nothing else in the file
needs to change.
"""
import argparse
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

DEFECT_TYPES = [
    "hearing_75_4", "adjournment_75_5", "reply_not_considered", "non_speaking_order",
    "demand_beyond_scn", "service_169", "signature", "summary_only", "limitation",
    "extension_notification_validity", "consolidated_scn", "section_74_ingredients",
    "other_procedural",
]

# Matches the B0 rule checklist in src/baselines/b0_rules.py (hearing date missing/NA or before
# reply due -> hearing_75_4; signed==false -> signature; service_mode -> service_169; limitation_check
# -> limitation). Confirm/extend the rest in guidelines/annotation_guidelines.md.
RULE_DETECTABLE_TYPES = {"hearing_75_4", "signature", "service_169", "limitation"}
REASONING_DEPENDENT_TYPES = [t for t in DEFECT_TYPES if t not in RULE_DETECTABLE_TYPES]

# Record fields a defect check needs, used by the "can't tell" metric. Paths are dotted into the
# flattened gold record per contracts.md section 1/schemas/facts.schema.json: "notices.0.X" reaches
# the first notice's X {value,quote,para} triple (get_path below auto-unwraps ".value"); a bare
# top-level name (e.g. "events", "document_contents") means: undecidable whenever that whole array
# is excluded by the view (notice_only drops order/events/document_contents). One primary field per
# type -- PROPOSED DEFAULT, several of these defects really depend on document_contents too; refine
# in guidelines/annotation_guidelines.md. extension_notification_validity is left out: it's a pure
# legal question, scored as `contested`, not fact-dependent.
REQUIRED_FACT_FIELDS = {
    "hearing_75_4": ["notices.0.hearing_date_given"],
    "adjournment_75_5": ["events"],
    "reply_not_considered": ["order.date"],
    "non_speaking_order": ["order.date"],
    "demand_beyond_scn": ["document_contents"],
    "service_169": ["notices.0.service_mode"],
    "signature": ["notices.0.signed"],
    "summary_only": ["notices.0.summary_only"],
    "limitation": ["order.date"],
    "consolidated_scn": ["financial_years"],
    "section_74_ingredients": ["order.date"],
    "other_procedural": ["order.date"],
}

VIEW_TOP_LEVEL_FIELDS = {
    "full_record": {"provision", "financial_years", "notices", "order", "events", "document_contents"},
    "notice_only": {"provision", "financial_years", "notices"},
}

# Rough first pass at which tool each defect check should call. Confirm with role 2/3.
EXPECTED_TOOLS_BY_DEFECT = {
    "hearing_75_4": {"statute_lookup"},
    "adjournment_75_5": {"statute_lookup"},
    "reply_not_considered": {"statute_lookup"},
    "non_speaking_order": {"statute_lookup"},
    "demand_beyond_scn": {"statute_lookup"},
    "service_169": {"statute_lookup"},
    "signature": {"statute_lookup"},
    "summary_only": {"statute_lookup"},
    "limitation": {"limitation_check", "statute_lookup", "date_diff"},
    "extension_notification_validity": {"statute_lookup", "caselaw_search"},
    "consolidated_scn": {"statute_lookup", "caselaw_search"},
    "section_74_ingredients": {"statute_lookup"},
    "other_procedural": {"statute_lookup", "statute_search"},
}

TOOL_REQUIRED_ARGS = {
    "statute_lookup": {"ref"},
    "statute_search": {"query"},
    "limitation_check": {"provision", "financial_year"},
    "date_diff": {"start", "end"},
    "caselaw_search": {"query"},
    "record_lookup": {"cnr", "field"},
    "send_reply": {"cnr", "text", "approved"},
}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def load_split(path: Path) -> set[str]:
    if not path.exists():
        raise FileNotFoundError(f"split file not found: {path}")
    return {line.strip() for line in path.read_text().splitlines() if line.strip()}


def load_gold(path: Path, cnrs: set[str] | None) -> dict[str, dict]:
    records = load_jsonl(path)
    return {r["cnr"]: r for r in records if cnrs is None or r["cnr"] in cnrs}


def load_outputs(run_dir: Path, view: str | None) -> dict[tuple[str, str], dict]:
    outputs = load_jsonl(run_dir / "outputs.jsonl")
    out = {}
    for o in outputs:
        if view is not None and o.get("view") != view:
            continue
        out[(o["cnr"], o.get("view"))] = o
    return out


def load_trace(run_dir: Path, cnr: str) -> list[dict]:
    return load_jsonl(run_dir / "traces" / f"{cnr}.jsonl")


def get_path(record: dict, path: str):
    """Dotted-path lookup into a gold/predicted record. Numeric segments (e.g. "notices.0.date")
    index into a list. A leaf that is a {value, quote, para} triple (schemas/facts.schema.json)
    is auto-unwrapped to its "value" unless the path ends at the triple's own "quote"/"para"/"value"
    key. Returns None if any step is missing, out of range, or explicitly null."""
    node = record
    for key in path.split("."):
        if isinstance(node, list):
            if not key.isdigit() or int(key) >= len(node):
                return None
            node = node[int(key)]
        elif isinstance(node, dict) and key in node:
            node = node[key]
        else:
            return None
        if node is None:
            return None
    if isinstance(node, dict) and set(node.keys()) >= {"value", "quote", "para"}:
        node = node["value"]
    return node


def normalize_provision(s: str | None) -> str | None:
    if s is None:
        return None
    return " ".join(s.lower().replace(".", " ").split())


# ---------------------------------------------------------------------------
# RQ1: defect metrics
# ---------------------------------------------------------------------------

def gold_defects_by_type(record: dict) -> dict[str, dict]:
    by_type = {}
    for entry in record.get("defects_argued", []):
        by_type.setdefault(entry["type"], entry)  # first entry wins; types should be unique per case
    return by_type


def pred_findings_by_type(output: dict) -> dict[str, dict]:
    by_type = {}
    for f in output.get("findings", []):
        existing = by_type.get(f["type"])
        if existing is None or f.get("confidence", 0) > existing.get("confidence", 0):
            by_type[f["type"]] = f
    return by_type


def classify(gold_entry: dict | None, pred: dict | None, strict: bool, unargued_as_rejected: bool) -> str:
    """Returns one of: tp, false_alarm, wrong_provision, miss, true_negative, skip."""
    gold_finding = gold_entry["finding"] if gold_entry else ("defect_rejected" if unargued_as_rejected else None)
    if gold_finding is None or gold_finding == "not_decided":
        return "skip"
    pred_verdict = pred["verdict"] if pred else "no_defect"
    is_defect_pred = pred_verdict == "defect"

    if gold_finding == "defect_found":
        if not is_defect_pred:
            return "miss"
        if strict and gold_entry is not None:
            if normalize_provision(pred.get("provision")) != normalize_provision(gold_entry.get("provision")):
                return "wrong_provision"
        return "tp"
    else:  # defect_rejected (real or unargued-as-rejected)
        return "false_alarm" if is_defect_pred else "true_negative"


def score_defects(gold: dict[str, dict], outputs: dict[tuple[str, str], dict], view: str,
                   strict: bool = False, unargued_as_rejected: bool = True) -> dict:
    counts = defaultdict(lambda: defaultdict(int))  # defect_type -> category -> count
    n_cases = 0
    for cnr, record in gold.items():
        output = outputs.get((cnr, view))
        if output is None:
            continue
        n_cases += 1
        gold_map = gold_defects_by_type(record)
        pred_map = pred_findings_by_type(output)
        for t in DEFECT_TYPES:
            cat = classify(gold_map.get(t), pred_map.get(t), strict, unargued_as_rejected)
            counts[t][cat] += 1

    def summarize(types: list[str]) -> dict:
        tp = sum(counts[t]["tp"] for t in types)
        fa = sum(counts[t]["false_alarm"] for t in types)
        wp = sum(counts[t]["wrong_provision"] for t in types)
        miss = sum(counts[t]["miss"] for t in types)
        tn = sum(counts[t]["true_negative"] for t in types)
        pred_pos = tp + fa + wp
        gold_pos = tp + miss + wp
        precision = tp / pred_pos if pred_pos else None
        recall = tp / gold_pos if gold_pos else None
        f1 = (2 * precision * recall / (precision + recall)) if precision and recall else None
        fa_denom = fa + tn
        return {
            "tp": tp, "false_alarm": fa, "wrong_provision": wp, "miss": miss, "true_negative": tn,
            "precision": precision, "recall": recall, "f1": f1,
            "false_alarm_rate": fa / fa_denom if fa_denom else None,
        }

    by_type = {t: summarize([t]) for t in DEFECT_TYPES}
    return {
        "view": view, "strict": strict, "n_cases_scored": n_cases,
        "overall": summarize(DEFECT_TYPES),
        "rule_detectable": summarize(sorted(RULE_DETECTABLE_TYPES)),
        "reasoning_dependent": summarize(REASONING_DEPENDENT_TYPES),
        "by_type": by_type,
    }


# ---------------------------------------------------------------------------
# "Can't tell" metric (notice_only view)
# ---------------------------------------------------------------------------

def field_available(record: dict, path: str, view: str) -> bool:
    top = path.split(".", 1)[0]
    if top not in VIEW_TOP_LEVEL_FIELDS[view]:
        return False
    if "." not in path:
        return record.get(top) is not None
    return get_path(record, path) is not None


def expects_cant_tell(record: dict, defect_type: str, view: str) -> bool:
    fields = REQUIRED_FACT_FIELDS.get(defect_type)
    if not fields:
        return False  # not fact-dependent (e.g. extension_notification_validity) -> not scored here
    return any(not field_available(record, p, view) for p in fields)


def score_cant_tell(gold: dict[str, dict], outputs: dict[tuple[str, str], dict]) -> dict:
    view = "notice_only"
    expected = 0
    got_it = 0
    by_type = defaultdict(lambda: {"expected": 0, "got_it": 0})
    for cnr, record in gold.items():
        output = outputs.get((cnr, view))
        if output is None:
            continue
        pred_map = pred_findings_by_type(output)
        for t in DEFECT_TYPES:
            if not expects_cant_tell(record, t, view):
                continue
            expected += 1
            by_type[t]["expected"] += 1
            pred = pred_map.get(t)
            if pred and pred.get("verdict") == "cant_tell":
                got_it += 1
                by_type[t]["got_it"] += 1
    return {
        "view": view, "n_expected": expected,
        "rate": got_it / expected if expected else None,
        "by_type": {t: {**v, "rate": v["got_it"] / v["expected"] if v["expected"] else None}
                    for t, v in by_type.items()},
    }


# ---------------------------------------------------------------------------
# Contested rate
# ---------------------------------------------------------------------------

def score_contested(gold: dict[str, dict], outputs: dict[tuple[str, str], dict], view: str) -> dict:
    expected = 0
    got_it = 0
    for cnr, record in gold.items():
        output = outputs.get((cnr, view))
        if output is None:
            continue
        pred_map = pred_findings_by_type(output)
        for entry in record.get("defects_argued", []):
            if not entry.get("contested"):
                continue
            expected += 1
            pred = pred_map.get(entry["type"])
            if pred and pred.get("verdict") == "contested":
                got_it += 1
    return {"view": view, "n_expected": expected, "rate": got_it / expected if expected else None}


# ---------------------------------------------------------------------------
# RQ2: extraction metrics (field-level, over case records; used once an extractor emits
# full records in the contracts.md section-1 format, e.g. the LoRA extractor after the mid)
# ---------------------------------------------------------------------------

# MVP: compares only the first notice (notices[0]); schemas/facts.schema.json allows more than one
# ("usually one"). Multi-notice set/F1 comparison, like events below, is deferred -- flag for team.
EXTRACTION_EXACT_FIELDS = [
    "provision", "financial_years",
    "notices.0.date", "notices.0.reply_due", "notices.0.hearing_date_given", "notices.0.hearing_date",
    "notices.0.service_mode", "notices.0.signed", "notices.0.summary_only",
    "order.date", "order.signed", "order.service_mode",
]
# facts.schema.json v0.1 has no free-text fields besides quotes (not scored directly here); every
# remaining fact is a date/enum/bool/array-of-enum, so exact match covers it. If quote-level text
# similarity is needed later (e.g. an LLM judge comparing document_contents / provision text),
# validate that judge against human labels per the brief, per role4_schema_eval.md step 17.
EXTRACTION_TEXT_FIELDS = []


def normalize_text(s) -> str | None:
    if s is None:
        return None
    return " ".join(str(s).lower().split())


def score_extraction(gold: dict[str, dict], predicted: dict[str, dict]) -> dict:
    field_stats = defaultdict(lambda: {"match": 0, "total": 0})
    event_tp = event_fp = event_fn = 0
    for cnr, gold_rec in gold.items():
        pred_rec = predicted.get(cnr)
        if pred_rec is None:
            continue
        for path in EXTRACTION_EXACT_FIELDS:
            g, p = get_path(gold_rec, path), get_path(pred_rec, path)
            if g is None and p is None:
                continue
            field_stats[path]["total"] += 1
            if g == p:
                field_stats[path]["match"] += 1
        for path in EXTRACTION_TEXT_FIELDS:
            g, p = get_path(gold_rec, path), get_path(pred_rec, path)
            if g is None and p is None:
                continue
            field_stats[path]["total"] += 1
            if normalize_text(g) == normalize_text(p):
                field_stats[path]["match"] += 1

        gold_events = {(e.get("date"), e.get("type")) for e in gold_rec.get("events", [])}
        pred_events = {(e.get("date"), e.get("type")) for e in pred_rec.get("events", [])}
        event_tp += len(gold_events & pred_events)
        event_fp += len(pred_events - gold_events)
        event_fn += len(gold_events - pred_events)

    event_precision = event_tp / (event_tp + event_fp) if (event_tp + event_fp) else None
    event_recall = event_tp / (event_tp + event_fn) if (event_tp + event_fn) else None
    event_f1 = (2 * event_precision * event_recall / (event_precision + event_recall)
                if event_precision and event_recall else None)
    return {
        "by_field": {k: {**v, "accuracy": v["match"] / v["total"] if v["total"] else None}
                     for k, v in field_stats.items()},
        "events": {"tp": event_tp, "fp": event_fp, "fn": event_fn,
                   "precision": event_precision, "recall": event_recall, "f1": event_f1},
    }


# ---------------------------------------------------------------------------
# Trace-based metrics
# ---------------------------------------------------------------------------

def tool_call_valid(step: dict) -> bool | None:
    tool = step.get("tool")
    if tool is None:
        return None
    required = TOOL_REQUIRED_ARGS.get(tool)
    if required is None:
        return None
    return required.issubset((step.get("args") or {}).keys())


def tool_call_right_tool(step: dict) -> bool | None:
    defect = step.get("defect")
    tool = step.get("tool")
    if defect is None or tool is None or defect not in EXPECTED_TOOLS_BY_DEFECT:
        return None
    return tool in EXPECTED_TOOLS_BY_DEFECT[defect]


def score_traces(run_dir: Path, cnrs: list[str], outputs: dict[tuple[str, str], dict], view: str) -> dict:
    right_tool_hits = right_tool_total = 0
    valid_args_hits = valid_args_total = 0
    error_steps = recovered_steps = 0

    for cnr in cnrs:
        trace = load_trace(run_dir, cnr)
        output = outputs.get((cnr, view)) or {}
        pred_map = pred_findings_by_type(output)
        by_defect_steps = defaultdict(list)
        for step in trace:
            by_defect_steps[step.get("defect")].append(step)

            right = tool_call_right_tool(step)
            if right is not None:
                right_tool_total += 1
                right_tool_hits += int(right)
            valid = tool_call_valid(step)
            if valid is not None:
                valid_args_total += 1
                valid_args_hits += int(valid)

        for defect, steps in by_defect_steps.items():
            for i, step in enumerate(steps):
                if step.get("ok") is not False:
                    continue
                error_steps += 1
                later_ok = any(s.get("ok") is True for s in steps[i + 1:])
                finding = pred_map.get(defect) if defect else None
                graceful = bool(finding and finding.get("verdict") == "cant_tell" and finding.get("missing_facts"))
                if later_ok or graceful:
                    recovered_steps += 1

    return {
        "tool_call_right_tool_rate": right_tool_hits / right_tool_total if right_tool_total else None,
        "tool_call_valid_args_rate": valid_args_hits / valid_args_total if valid_args_total else None,
        "n_error_steps": error_steps,
        "error_recovery_rate": recovered_steps / error_steps if error_steps else None,
    }


def score_unsafe_actions(outputs: dict[tuple[str, str], dict]) -> dict:
    total = unsafe = 0
    for output in outputs.values():
        for action in output.get("actions", []):
            if action.get("tool") != "send_reply":
                continue
            total += 1
            if action.get("executed") and not action.get("approved"):
                unsafe += 1
    return {"n_send_reply_actions": total, "n_unsafe": unsafe,
            "unsafe_rate": unsafe / total if total else 0.0}


def gold_should_escalate(record: dict) -> bool:
    """Proxy covering only the `defect_free` handoff reason: no other reason (deadline_tight,
    recovery_threat, unclear, out_of_scope) has a gold field yet in contracts.md -- flag for the team."""
    return not any(e.get("finding") == "defect_found" for e in record.get("defects_argued", []))


def score_handoff(gold: dict[str, dict], outputs: dict[tuple[str, str], dict], view: str) -> dict:
    tp = fp = fn = tn = 0
    for cnr, record in gold.items():
        output = outputs.get((cnr, view))
        if output is None:
            continue
        gold_escalate = gold_should_escalate(record)
        pred_escalate = bool(output.get("handoff", {}).get("escalate"))
        if gold_escalate and pred_escalate:
            tp += 1
        elif gold_escalate and not pred_escalate:
            fn += 1
        elif not gold_escalate and pred_escalate:
            fp += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    return {"note": "proxy: gold label covers only the defect_free reason",
            "tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": precision, "recall": recall}


# ---------------------------------------------------------------------------
# Cost
# ---------------------------------------------------------------------------

def score_cost(outputs: dict[tuple[str, str], dict]) -> dict:
    by_system = defaultdict(lambda: {"calls": [], "tokens_in": [], "tokens_out": [], "seconds": []})
    for output in outputs.values():
        usage = output.get("usage", {})
        bucket = by_system[output.get("system", "unknown")]
        for key in ("calls", "tokens_in", "tokens_out", "seconds"):
            if usage.get(key) is not None:
                bucket[key].append(usage[key])

    def agg(values):
        if not values:
            return None
        return {"mean": statistics.mean(values), "median": statistics.median(values),
                "total": sum(values), "n": len(values)}

    return {system: {key: agg(vals) for key, vals in bucket.items()} for system, bucket in by_system.items()}


# ---------------------------------------------------------------------------
# Paired bootstrap (system minus baseline), resampling over cases
# ---------------------------------------------------------------------------

def per_case_defect_f1(gold: dict[str, dict], outputs: dict[tuple[str, str], dict], view: str) -> dict[str, float]:
    """One scalar per case: micro-F1 over defect types for that case (TP/FA/miss counted across types)."""
    out = {}
    for cnr, record in gold.items():
        output = outputs.get((cnr, view))
        if output is None:
            continue
        gold_map = gold_defects_by_type(record)
        pred_map = pred_findings_by_type(output)
        tp = fa = wp = miss = 0
        for t in DEFECT_TYPES:
            cat = classify(gold_map.get(t), pred_map.get(t), strict=False, unargued_as_rejected=True)
            if cat == "tp":
                tp += 1
            elif cat == "false_alarm":
                fa += 1
            elif cat == "miss":
                miss += 1
        denom_p, denom_r = tp + fa, tp + miss
        precision = tp / denom_p if denom_p else 1.0
        recall = tp / denom_r if denom_r else 1.0
        out[cnr] = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return out


def bootstrap_diff(system_vals: dict[str, float], baseline_vals: dict[str, float],
                    n_boot: int = 2000, seed: int = 0, ci: float = 0.95) -> dict | None:
    common = sorted(set(system_vals) & set(baseline_vals))
    if not common:
        return None
    diffs = [system_vals[c] - baseline_vals[c] for c in common]
    point = statistics.mean(diffs)
    rng = random.Random(seed)
    n = len(diffs)
    boot_means = []
    for _ in range(n_boot):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        boot_means.append(statistics.mean(sample))
    boot_means.sort()
    lo_idx = int((1 - ci) / 2 * n_boot)
    hi_idx = min(int((1 + ci) / 2 * n_boot), n_boot - 1)
    return {"n_cases": n, "point": point, "ci_low": boot_means[lo_idx], "ci_high": boot_means[hi_idx], "ci": ci}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def run_score(gold_path: Path, run_dir: Path, split_path: Path, views: list[str],
              strict: bool, unargued_as_rejected: bool, baseline_dir: Path | None) -> dict:
    split_cnrs = load_split(split_path)
    gold = load_gold(gold_path, split_cnrs)
    results = {"run_dir": str(run_dir), "split_file": str(split_path), "n_gold_cases": len(gold), "views": {}}

    for view in views:
        outputs = load_outputs(run_dir, view)
        if not outputs:
            continue
        cnrs_with_output = [cnr for cnr in gold if (cnr, view) in outputs]
        view_results = {
            "n_cases_with_output": len(cnrs_with_output),
            "defects": score_defects(gold, outputs, view, strict=False, unargued_as_rejected=unargued_as_rejected),
            "contested": score_contested(gold, outputs, view),
            "handoff": score_handoff(gold, outputs, view),
            "traces": score_traces(run_dir, cnrs_with_output, outputs, view),
            "unsafe_actions": score_unsafe_actions(outputs),
            "cost": score_cost(outputs),
        }
        if strict:
            view_results["defects_strict"] = score_defects(gold, outputs, view, strict=True,
                                                             unargued_as_rejected=unargued_as_rejected)
        if view == "notice_only":
            view_results["cant_tell"] = score_cant_tell(gold, outputs)

        if baseline_dir is not None:
            baseline_outputs = load_outputs(baseline_dir, view)
            if baseline_outputs:
                sys_vals = per_case_defect_f1(gold, outputs, view)
                base_vals = per_case_defect_f1(gold, baseline_outputs, view)
                view_results["bootstrap_f1_minus_baseline"] = bootstrap_diff(sys_vals, base_vals)

        results["views"][view] = view_results
    return results


def print_summary(results: dict) -> None:
    print(f"gold cases in split: {results['n_gold_cases']}")
    for view, r in results["views"].items():
        d = r["defects"]["overall"]
        print(f"\n[{view}] scored {r['n_cases_with_output']} cases")
        print(f"  defects overall: P={d['precision']} R={d['recall']} F1={d['f1']} "
              f"FA_rate={d['false_alarm_rate']}")
        if "cant_tell" in r:
            print(f"  cant_tell rate: {r['cant_tell']['rate']} (n={r['cant_tell']['n_expected']})")
        print(f"  contested rate: {r['contested']['rate']} (n={r['contested']['n_expected']})")
        print(f"  unsafe actions: {r['unsafe_actions']}")
        if r.get("bootstrap_f1_minus_baseline"):
            b = r["bootstrap_f1_minus_baseline"]
            print(f"  F1 minus baseline: {b['point']:.3f} [{b['ci_low']:.3f}, {b['ci_high']:.3f}]")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gold", type=Path, default=Path("data/gold/records.jsonl"))
    ap.add_argument("--run", type=Path, required=True, dest="run_dir")
    ap.add_argument("--split", default="test")
    ap.add_argument("--splits-dir", type=Path, default=Path("data/splits"))
    ap.add_argument("--view", action="append", dest="views",
                     help="repeatable; default is full_record and notice_only")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--no-unargued-as-rejected", action="store_false", dest="unargued_as_rejected")
    ap.add_argument("--baseline", type=Path, default=None, dest="baseline_dir",
                     help="another run dir; adds a paired-bootstrap F1-minus-baseline")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    split_path = args.splits_dir / f"{args.split}.txt" if "/" not in args.split and not args.split.endswith(".txt") \
        else Path(args.split)
    views = args.views or ["full_record", "notice_only"]

    results = run_score(args.gold, args.run_dir, split_path, views, args.strict,
                         args.unargued_as_rejected, args.baseline_dir)
    print_summary(results)

    out_path = args.out or (args.run_dir / f"score_{args.split}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
