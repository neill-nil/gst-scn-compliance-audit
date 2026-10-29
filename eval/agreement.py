"""Inter-annotator agreement on the double-reviewed cases, per role4_schema_eval.md Wed step 13.
For role 1: exact-match rate per fact field, and Cohen's kappa for defects_argued type+finding,
over the cases two reviewers both annotated.

Each input file is one annotator's records in gold-record format (docs/team_plan/contracts.md
section 1), JSONL, one line per case -- i.e. the pre-merge per-reviewer file, not data/gold/records.jsonl
itself (that's already merged/adjudicated). Only cnrs present in BOTH files are scored.

Usage:
    python -m eval.agreement --a data/interim/annotations/r1.jsonl --b data/interim/annotations/r4.jsonl
"""
import argparse
import json
from collections import Counter
from pathlib import Path

FACT_FIELDS = [
    "provision", "financial_years",
    "notices.0.date", "notices.0.reply_due", "notices.0.hearing_date_given", "notices.0.hearing_date",
    "notices.0.service_mode", "notices.0.signed", "notices.0.summary_only",
    "order.date", "order.signed", "order.service_mode",
]


def load_jsonl(path: Path) -> dict[str, dict]:
    out = {}
    with path.open() as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                out[r["cnr"]] = r
    return out


def get_path(record: dict, path: str):
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


def field_agreement(a: dict[str, dict], b: dict[str, dict], common: list[str]) -> dict:
    out = {}
    for path in FACT_FIELDS:
        match = total = 0
        for cnr in common:
            va, vb = get_path(a[cnr], path), get_path(b[cnr], path)
            if va is None and vb is None:
                continue
            total += 1
            if va == vb:
                match += 1
        out[path] = {"match": match, "total": total, "rate": match / total if total else None}
    return out


def defects_by_type(record: dict) -> dict[str, str]:
    """cnr's defects_argued -> {type: finding}, for the type+finding kappa."""
    return {d["type"]: d["finding"] for d in record.get("defects_argued", [])}


def cohens_kappa(pairs: list[tuple[str, str]], labels: list[str]) -> float | None:
    """Standard Cohen's kappa over a list of (rater_a_label, rater_b_label) pairs."""
    n = len(pairs)
    if n == 0:
        return None
    confusion = Counter(pairs)
    observed = sum(confusion[(l, l)] for l in labels) / n

    a_marg = Counter(p[0] for p in pairs)
    b_marg = Counter(p[1] for p in pairs)
    expected = sum((a_marg[l] / n) * (b_marg[l] / n) for l in labels)

    if expected >= 1.0:
        return 1.0  # no variance to disagree on
    return (observed - expected) / (1 - expected)


def defect_type_finding_kappa(a: dict[str, dict], b: dict[str, dict], common: list[str],
                               defect_types: list[str], findings: list[str]) -> dict:
    """One kappa per defect type, over "did rater X say finding Y for this type on this case",
    plus an overall kappa pooling every (case, type) cell. Cases where NEITHER rater argued the
    type are skipped (both would trivially agree "not argued", inflating kappa)."""
    not_argued = "not_argued"
    all_findings = findings + [not_argued]
    by_type = {}
    overall_pairs = []
    for t in defect_types:
        pairs = []
        for cnr in common:
            fa = defects_by_type(a[cnr]).get(t, not_argued)
            fb = defects_by_type(b[cnr]).get(t, not_argued)
            if fa == not_argued and fb == not_argued:
                continue
            pairs.append((fa, fb))
        by_type[t] = {"n": len(pairs), "kappa": cohens_kappa(pairs, all_findings)}
        overall_pairs.extend(pairs)
    return {
        "by_type": by_type,
        "overall": {"n": len(overall_pairs), "kappa": cohens_kappa(overall_pairs, all_findings)},
    }


def main():
    from eval.score import DEFECT_TYPES

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--a", type=Path, required=True)
    ap.add_argument("--b", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    a, b = load_jsonl(args.a), load_jsonl(args.b)
    common = sorted(set(a) & set(b))
    if not common:
        raise SystemExit(f"no common cnrs between {args.a} and {args.b}")

    result = {
        "n_common_cases": len(common),
        "cnrs_a_only": sorted(set(a) - set(b)),
        "cnrs_b_only": sorted(set(b) - set(a)),
        "field_agreement": field_agreement(a, b, common),
        "defects_argued_kappa": defect_type_finding_kappa(
            a, b, common, DEFECT_TYPES, ["defect_found", "defect_rejected", "not_decided"]),
    }
    print(json.dumps(result, indent=2))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2))
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
