"""Paired bootstrap between two runs, with the same scoring rule as the reported numbers.

eval/score.py --baseline scores each case with unargued types counted as rejected and averages
per-case F1; the numbers we report score argued complaints only and pool counts over cases. This
resamples cases and recomputes the pooled precision, recall, F1 and false alarms of both runs on each
sample, so the intervals belong to the reported numbers.

Usage: python -m scripts.compare_runs --system runs/b2 --baseline runs/b1 [--view full_record]
"""
import argparse
import random
from pathlib import Path

from eval.score import DEFECT_TYPES, classify, gold_defects_by_type, load_gold, load_outputs, load_split, pred_findings_by_type


def case_counts(gold, outputs, view):
    out = {}
    for cnr, record in gold.items():
        output = outputs.get((cnr, view))
        if output is None:
            continue
        g, p = gold_defects_by_type(record), pred_findings_by_type(output)
        c = {"tp": 0, "false_alarm": 0, "miss": 0}
        for t in DEFECT_TYPES:
            cat = classify(g.get(t), p.get(t), strict=False, unargued_as_rejected=False)
            if cat in c:
                c[cat] += 1
        out[cnr] = c
    return out


def pooled(counts, cnrs):
    tp = sum(counts[c]["tp"] for c in cnrs)
    fa = sum(counts[c]["false_alarm"] for c in cnrs)
    miss = sum(counts[c]["miss"] for c in cnrs)
    p = tp / (tp + fa) if tp + fa else 0.0
    r = tp / (tp + miss) if tp + miss else 0.0
    return {"precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0.0, "false_alarms": fa}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", type=Path, required=True)
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--view", default="full_record")
    ap.add_argument("--gold", type=Path, default=Path("data/gold/records.jsonl"))
    ap.add_argument("--split", type=Path, default=Path("data/splits/test.txt"))
    ap.add_argument("--n-boot", type=int, default=5000)
    args = ap.parse_args()

    gold = load_gold(args.gold, load_split(args.split))
    a = case_counts(gold, load_outputs(args.system, args.view), args.view)
    b = case_counts(gold, load_outputs(args.baseline, args.view), args.view)
    cnrs = sorted(set(a) & set(b))
    rng = random.Random(0)
    print(f"{args.system.name} minus {args.baseline.name}, view {args.view}, {len(cnrs)} cases, {args.n_boot} resamples")
    for metric in ("f1", "recall", "precision", "false_alarms"):
        point = pooled(a, cnrs)[metric] - pooled(b, cnrs)[metric]
        diffs = []
        for _ in range(args.n_boot):
            s = [cnrs[rng.randrange(len(cnrs))] for _ in cnrs]
            diffs.append(pooled(a, s)[metric] - pooled(b, s)[metric])
        diffs.sort()
        lo, hi = diffs[int(0.025 * args.n_boot)], diffs[int(0.975 * args.n_boot) - 1]
        print(f"  {metric:13s} {point:+.3f}  95% CI [{lo:+.3f}, {hi:+.3f}]")


if __name__ == "__main__":
    main()
