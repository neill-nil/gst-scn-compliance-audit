"""RQ2 scorer: compare extracted facts with the human-verified facts in data/gold/records.jsonl, field by field.

Scored, per case:
  - fact fields (a value or null): provision, financial_years, the first notice's 7 fields, the order's 3 fields.
    A correct value is a TP; a value where gold has none is a FP; a missing value where gold has one is a FN;
    a wrong value counts as both FP and FN. Both null is not counted.
  - events: (type, date) pairs, matched as multisets.  document_contents: types, matched as multisets.
  - valid JSON rate, schema-valid rate, and the share of quotes found word for word in the judgment text.
Paired bootstrap (cases resampled) for the fact-field F1 of each system minus the first system.

Usage:
    python -m eval.score_extraction --system gemini=prefill --system base=runs/rq2_base --system tuned=runs/rq2_tuned
    (a run dir holds outputs*.jsonl lines {"cnr", "facts"}; "prefill" means the Gemini drafts in data/prefill/v1)
    [--split test|heldout|all] [--out runs/rq2_scores.json] [--repair]
--repair: when an output is not valid JSON (usually cut off at the token limit), keep its longest valid beginning
and close the open brackets (same rule for every system). Reported separately from the raw scores.
"""
import argparse
import json
import random
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTICE_FIELDS = ("date", "reply_due", "hearing_date_given", "hearing_date", "service_mode", "signed", "summary_only")
ORDER_FIELDS = ("date", "signed", "service_mode")
FIELDS = ["provision", "financial_years"] + [f"notice.{f}" for f in NOTICE_FIELDS] + [f"order.{f}" for f in ORDER_FIELDS]


def norm(s) -> str:
    return re.sub(r"\s+", " ", str(s).replace("“", '"').replace("”", '"').replace("’", "'")).strip().lower()


def value(node):
    if isinstance(node, dict) and "value" in node:
        node = node["value"]
    if isinstance(node, list):
        return tuple(sorted(norm(v) for v in node)) or None
    if isinstance(node, str):
        return norm(node) or None
    return node  # bool, int or None


def field_values(facts) -> dict:
    facts = facts if isinstance(facts, dict) else {}
    notices = facts.get("notices") if isinstance(facts.get("notices"), list) else []
    n0 = notices[0] if notices and isinstance(notices[0], dict) else {}
    order = facts.get("order") if isinstance(facts.get("order"), dict) else {}
    out = {"provision": value(facts.get("provision")), "financial_years": value(facts.get("financial_years"))}
    out.update({f"notice.{f}": value(n0.get(f)) for f in NOTICE_FIELDS})
    out.update({f"order.{f}": value(order.get(f)) for f in ORDER_FIELDS})
    return out


def items(facts, key, fields) -> Counter:
    rows = facts.get(key) if isinstance(facts, dict) and isinstance(facts.get(key), list) else []
    return Counter(tuple(norm(r.get(f)) if r.get(f) is not None else None for f in fields)
                   for r in rows if isinstance(r, dict))


def quotes(facts) -> list[str]:
    found = []

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("quote"), str) and o["quote"].strip():
                found.append(o["quote"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(facts)
    return found


def case_counts(pred, gold, text_norm: str) -> dict:
    c = Counter()
    pv, gv = field_values(pred), field_values(gold)
    for f in FIELDS:
        p, g = pv[f], gv[f]
        if g is not None and p == g:
            c["tp"] += 1; c[f + ":tp"] += 1
        else:
            if p is not None:
                c["fp"] += 1; c[f + ":fp"] += 1
            if g is not None:
                c["fn"] += 1; c[f + ":fn"] += 1
    for key, fields, tag in (("events", ("type", "date"), "ev"), ("document_contents", ("type",), "doc")):
        p, g = items(pred, key, fields), items(gold, key, fields)
        m = sum((p & g).values())
        c[tag + "_tp"] += m; c[tag + "_fp"] += sum(p.values()) - m; c[tag + "_fn"] += sum(g.values()) - m
    qs = quotes(pred)
    c["quotes"] += len(qs)
    c["quotes_found"] += sum(norm(q) in text_norm for q in qs)
    return c


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    f = 2 * p * r / (p + r) if p and r else 0.0
    return {"precision": p, "recall": r, "f1": f}


def summarise(per_case: dict) -> dict:
    tot = sum(per_case.values(), Counter())
    out = {"fields": prf(tot["tp"], tot["fp"], tot["fn"]),
           "events": prf(tot["ev_tp"], tot["ev_fp"], tot["ev_fn"]),
           "document_contents": prf(tot["doc_tp"], tot["doc_fp"], tot["doc_fn"]),
           "quotes_found_share": tot["quotes_found"] / tot["quotes"] if tot["quotes"] else None,
           "per_field": {f: prf(tot[f + ":tp"], tot[f + ":fp"], tot[f + ":fn"]) for f in FIELDS}}
    return out


def salvage(text: str):
    """Longest prefix of a broken JSON object that parses once its open brackets are closed; None if nothing does."""
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    start = text.find("{")
    if start < 0:
        return None
    text = text[start:]
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        limit = e.pos
    cuts, stack, in_str, esc = [], [], False, False
    for i, ch in enumerate(text[:limit]):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]":
            if stack:
                stack.pop()
            cuts.append((i + 1, tuple(stack)))
        elif ch == ",":
            cuts.append((i, tuple(stack)))
    for cut, open_ in reversed(cuts[-200:]):
        try:
            obj = json.loads(text[:cut] + "".join(reversed(open_)))
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            continue
    return None


def load_system(spec: str, repair: bool = False) -> dict:
    if spec == "prefill":
        out = {}
        for p in (ROOT / "data" / "prefill" / "v1").glob("*.json"):
            out[p.stem] = json.loads(p.read_text(encoding="utf-8")).get("facts")
        return out
    out = {}
    for p in sorted((ROOT / spec).glob("outputs*.jsonl")):
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            facts = r.get("facts")
            if facts is None and repair:
                facts = salvage(r.get("text"))
            out[r["cnr"]] = facts
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", action="append", required=True, help="name=run_dir or name=prefill")
    ap.add_argument("--split", default="test", choices=("test", "heldout", "all"))
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--out", default=None)
    ap.add_argument("--repair", action="store_true")
    args = ap.parse_args()

    from src.prefill.schema import FACTS_SCHEMA
    try:
        import jsonschema
    except ImportError:
        jsonschema = None

    gold = {r["cnr"]: r for r in map(json.loads, open(ROOT / "data/gold/records.jsonl", encoding="utf-8"))}
    if args.split != "all":
        gold = {c: r for c, r in gold.items() if r["annotation"].get("set", "test") == args.split}
    texts = {}
    for r in map(json.loads, open(ROOT / "data/interim/rq2/test.jsonl", encoding="utf-8")):
        p = r["messages"][0]["content"]
        texts[r["cnr"]] = norm(p[p.find("JUDGMENT:"):])
    cnrs = sorted(gold)

    results, per_system = {}, {}
    for spec in args.system:
        name, path = spec.split("=", 1)
        preds = load_system(path, args.repair)
        per_case = {c: case_counts(preds.get(c), gold[c], texts.get(c, "")) for c in cnrs}
        s = summarise(per_case)
        have = [c for c in cnrs if preds.get(c) is not None]
        s["n_cases"], s["n_with_json"] = len(cnrs), len(have)
        s["schema_valid"] = (sum(not list(jsonschema.Draft202012Validator(FACTS_SCHEMA).iter_errors(preds[c]))
                                 for c in have) if jsonschema else None)
        results[name], per_system[name] = s, per_case

    names = list(results)
    rng = random.Random(0)
    for name in names[1:]:
        diffs = []
        for _ in range(args.n_boot):
            sample = [rng.choice(cnrs) for _ in cnrs]
            f = lambda n: prf(*(sum(per_system[n][c][k] for c in sample) for k in ("tp", "fp", "fn")))["f1"]
            diffs.append(f(name) - f(names[0]))
        diffs.sort()
        results[name]["fields_f1_minus_" + names[0]] = {
            "diff": results[name]["fields"]["f1"] - results[names[0]]["fields"]["f1"],
            "ci95": [diffs[int(0.025 * len(diffs))], diffs[int(0.975 * len(diffs)) - 1]]}

    fmt = lambda x: "  -  " if x is None else f"{x:.2f}"
    print(f"split {args.split}: {len(cnrs)} cases")
    print(f"{'system':10} {'json':>5} {'schema':>6} {'fieldP':>6} {'fieldR':>6} {'fieldF1':>7} {'eventF1':>7} {'docF1':>6} {'quotesOK':>8}")
    for n, s in results.items():
        print(f"{n:10} {s['n_with_json']:>5} {s['schema_valid'] if s['schema_valid'] is not None else '-':>6} "
              f"{fmt(s['fields']['precision']):>6} {fmt(s['fields']['recall']):>6} {fmt(s['fields']['f1']):>7} "
              f"{fmt(s['events']['f1']):>7} {fmt(s['document_contents']['f1']):>6} {fmt(s['quotes_found_share']):>8}")
    for n in names[1:]:
        d = results[n]["fields_f1_minus_" + names[0]]
        print(f"{n} - {names[0]} field F1: {d['diff']:+.3f}  95% CI [{d['ci95'][0]:+.3f}, {d['ci95'][1]:+.3f}]")
    print("\nper-field F1:")
    print(f"{'field':26}" + "".join(f"{n:>10}" for n in names))
    for f in FIELDS:
        print(f"{f:26}" + "".join(f"{fmt(results[n]['per_field'][f]['f1']):>10}" for n in names))
    if args.out:
        Path(args.out).write_text(json.dumps(results, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
