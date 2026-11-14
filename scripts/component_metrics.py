"""Component metrics promised in the proposal / required by the brief, from the committed runs (no model calls):
  - tool calling: calls per tool, valid-argument rate, refusals, and whether the model called the limitation
    calculator when the record allowed it;
  - verifier: defects it dropped (no verified record quote), split by what the court decided;
  - retrieval (RAG): Recall@k of the gold provision for statute_search, hierarchical vs flat chunks;
  - false alarms: which defect types NoticeCheck called wrongly on argued complaints.
Writes runs/final/components.json; scripts/final_analysis.py adds it to docs/results/RESULTS.md.

Usage: python -m scripts.component_metrics
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from src.common.provisions import provision_for
from src.tools.statute import parse_ref, statute_search

ROOT = Path(__file__).resolve().parents[1]
NC = ["nc_full_s1", "nc_full_s2", "nc_full_s3"]
u = lambda n: n.get("value") if isinstance(n, dict) else n


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def gold_test():
    return {r["cnr"]: r for r in jl(ROOT / "data/gold/records.jsonl") if r["annotation"].get("set", "test") == "test"}


def traces(run):
    d = ROOT / "runs" / run / "traces"
    for p in sorted((d / "full_record" if (d / "full_record").exists() else d).glob("*.jsonl")):
        yield p.stem, jl(p)


def tool_metrics(run, inputs):
    calls, ok, refused, arg_err = Counter(), Counter(), Counter(), Counter()
    called_limit, could_limit, err_cases, recovered = 0, 0, 0, 0
    for cnr, tr in traces(run):
        model_calls = [t for t in tr if t.get("tool") and t.get("by") == "model"]
        lc = [t for t in model_calls if t["tool"] == "limitation_check"]
        if any(not t["ok"] and "s.74A" not in (t.get("output_summary") or "") for t in lc):
            err_cases += 1
            recovered += any(t["ok"] for t in lc)
        for t in model_calls:
            calls[t["tool"]] += 1
            if t["ok"]:
                ok[t["tool"]] += 1
            elif "s.74A" in (t.get("output_summary") or "") or "no annual-return due date" in (t.get("output_summary") or ""):
                refused[t["tool"]] += 1   # tool correctly refuses: FY 2024-25 onward is out of scope
            else:
                arg_err[t["tool"]] += 1
        rec = inputs.get(cnr, {})
        prov, fys, odate = u(rec.get("provision")), u(rec.get("financial_years")) or [], u((rec.get("order") or {}).get("date"))
        if prov in ("73", "74") and fys and odate and all(fy <= "2023-24" for fy in fys):
            could_limit += 1
            called_limit += any(t["tool"] == "limitation_check" for t in model_calls)
    n = sum(calls.values())
    return {"calls_by_tool": dict(calls), "valid_args_rate": (sum(ok.values()) + sum(refused.values())) / n,
            "argument_errors": dict(arg_err), "correct_refusals_out_of_scope_fy": dict(refused),
            "limitation_check_called_when_applicable": called_limit / could_limit if could_limit else None,
            "n_cases_limitation_applicable": could_limit, "n_model_tool_calls": n,
            "cases_with_argument_error": err_cases, "recovered_with_valid_call": recovered}


def verifier_metrics(run, gold):
    res = Counter()
    for cnr, tr in traces(run):
        for t in tr:
            if t.get("stage") == "verify" and "dropped" in (t.get("output_summary") or ""):
                g = {u(d["type"]): u(d["finding"]) for d in (gold.get(cnr) or {}).get("defects_argued", [])}
                if cnr not in gold:
                    res["held_out_case"] += 1
                else:
                    res[{"defect_found": "true_defect_dropped", "defect_rejected": "false_alarm_removed",
                         "not_decided": "not_decided"}.get(g.get(t["defect"]), "unargued_flag_removed")] += 1
    return dict(res)


def section(ref):
    m = re.match(r"(CGST (?:Act s|Rules r)\.\d+[A-Z]*)", ref or "")
    return m.group(1) if m else None


def retrieval(gold, ks=(1, 3, 5)):
    """Each argued complaint's quote (the court's or counsel's words) is a query; the target is the defect type's
    provision from the fixed table. Hierarchical = sub-section units with parent context; flat = 120-word chunks."""
    queries = []
    for r in gold.values():
        for d in r["defects_argued"]:
            target = provision_for(u(d["type"]), r)
            if target and d.get("quote"):
                queries.append((d["quote"], target, u(d["type"])))
    out = {"n_queries": len(queries)}
    for mode, flat in (("hierarchical", False), ("flat", True)):
        hits_sec, hits_sub = Counter(), Counter()
        per_type = defaultdict(lambda: [0, 0])
        for q, target, t in queries:
            refs = [h["ref"] for h in statute_search(q, k=max(ks), flat=flat)["result"]]
            secs = [section(x) for x in refs]
            for k in ks:
                hits_sec[k] += section(target) in secs[:k]
                hits_sub[k] += target in refs[:k]
            per_type[t][0] += section(target) in secs[:5]
            per_type[t][1] += 1
        out[mode] = {f"recall@{k}_section": hits_sec[k] / len(queries) for k in ks}
        if not flat:
            out[mode].update({f"recall@{k}_subsection": hits_sub[k] / len(queries) for k in ks})
        out[mode]["recall@5_section_by_type"] = {t: round(a / b, 2) for t, (a, b) in per_type.items()}
    return out


def false_alarms(run, gold):
    out = {(o["cnr"]): o for o in jl(ROOT / "runs" / run / "outputs.jsonl") if o["view"] == "full_record"}
    fa = Counter()
    for cnr, g in gold.items():
        f = {x["type"]: x for x in out[cnr]["findings"]}
        for d in g["defects_argued"]:
            if u(d["finding"]) == "defect_rejected" and f.get(u(d["type"]), {}).get("verdict") == "defect":
                fa[u(d["type"])] += 1
    return dict(fa)


def unargued_flags(run, gold):
    """Per test case: defect calls on types nobody argued."""
    out = {o["cnr"]: o for o in jl(ROOT / "runs" / run / "outputs.jsonl") if o["view"] == "full_record"}
    res = {}
    for cnr, g in gold.items():
        argued = {u(d["type"]) for d in g["defects_argued"]}
        res[cnr] = sum(f["verdict"] == "defect" and f["type"] not in argued for f in out[cnr]["findings"])
    return res


def unargued_ci(sys_run, base_run, gold, n_boot=5000):
    import random
    a, b = unargued_flags(sys_run, gold), unargued_flags(base_run, gold)
    cnrs = sorted(gold)
    rng = random.Random(0)
    diffs = sorted(sum(a[c] - b[c] for c in (cnrs[rng.randrange(len(cnrs))] for _ in cnrs)) for _ in range(n_boot))
    return {"system": sum(a.values()), "baseline": sum(b.values()), "diff": sum(a.values()) - sum(b.values()),
            "ci95": [diffs[int(.025 * n_boot)], diffs[int(.975 * n_boot) - 1]],
            "cases_with_any_system": sum(v > 0 for v in a.values()), "cases_with_any_baseline": sum(v > 0 for v in b.values())}


def main():
    gold = gold_test()
    inputs = {json.loads(l)["cnr"]: json.loads(l)["record"] for l in open(ROOT / "data/interim/inputs/full_record.jsonl")}
    res = {"tools": {r: tool_metrics(r, inputs) for r in NC + ["nc_gemini_s1"]},
           "verifier": {r: verifier_metrics(r, gold) for r in NC + ["nc_gemini_s1", "e2e_nc_tuned"]},
           "retrieval": retrieval(gold),
           "false_alarms_by_type": {r: false_alarms(r, gold) for r in NC + ["b1_v2", "b2_v2"]},
           "unargued_flags_vs_b1": {r: unargued_ci(r, "b1_v2", gold) for r in NC + ["nc_gemini_s1", "e2e_nc_tuned", "b2_v2"]}}
    out = ROOT / "runs/final/components.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1)[:4000])


if __name__ == "__main__":
    main()
