"""Pick the cases to review first and assign them to the 4 reviewers.

Pool: pre-filled drafts that exist, minus the dev cases (schema pilot, hand labels), minus drafts with no
defect argued (probably not a reasoned judgment), minus judgments over MAX_PAGES (slow to review).
The pick is balanced by court group (Madras / Delhi / others), caps the Delhi "Additional Notices tab"
template, and takes every case with a defect_rejected finding first, so the test set has some.
The final list is shuffled, so stopping part-way still leaves a balanced set.

Each reviewer gets PER_REVIEWER cases of their own, plus DOUBLE second reviews of another reviewer's cases
(for the agreement score), placed early in their list so they get done.
Deterministic: rerunning on the same drafts gives the same queue.

Usage: python -I scripts/make_review_queue.py [--drafts data/prefill/v1]  ->  data/splits/review_queue.csv
"""
import argparse
import csv
import gzip
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWERS = ["r1", "r2", "r3", "r4"]
PER_REVIEWER = 15
DOUBLE = 4          # second reviews per reviewer
MAX_PAGES = 25
QUOTA = {"Madras": 22, "Delhi": 15, "other": 23}
MAX_DELHI_TAB = 4   # Delhi template orders about the portal's "Additional Notices" tab
SEED = 30


def ids(name):
    with open(ROOT / "data" / "splits" / name, newline="", encoding="utf-8") as f:
        return {r["cnr"] for r in csv.DictReader(f)}


def delhi_tab(court, cnr):
    path = ROOT / "data" / "text" / court / f"{cnr}.txt.gz"
    return path.exists() and "additional notices" in gzip.open(path, "rt", encoding="utf-8", errors="replace").read().lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drafts", default=str(ROOT / "data" / "prefill" / "v1"))
    args = ap.parse_args()

    with open(ROOT / "data" / "splits" / "prefill_shares.csv", newline="", encoding="utf-8") as f:
        meta = {r["cnr"]: r for r in csv.DictReader(f)}
    dev = ids("schema_pilot.csv") | ids("hand_labels_reasoned.csv")

    groups = {g: {"rejected": [], "rest": [], "tab": []} for g in QUOTA}
    for path in sorted(Path(args.drafts).glob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        m = meta[rec["cnr"]]
        defects = (rec.get("findings") or {}).get("defects_argued") or []
        if rec["cnr"] in dev or not defects or int(m["pages"]) > MAX_PAGES:
            continue
        group = m["court_name"] if m["court_name"] in ("Madras", "Delhi") else "other"
        if group == "Delhi" and delhi_tab(m["court"], rec["cnr"]):
            kind = "tab"
        elif any(d["finding"] == "defect_rejected" for d in defects):
            kind = "rejected"
        else:
            kind = "rest"
        groups[group][kind].append(rec["cnr"])

    rng = random.Random(SEED)
    picked, spare = [], []
    for g, quota in QUOTA.items():
        for kind in groups[g].values():
            rng.shuffle(kind)
        # Rejected cases first, Delhi tab template only up to its cap, then the rest.
        order = groups[g]["rejected"] + groups[g]["tab"][:MAX_DELHI_TAB] + groups[g]["rest"]
        picked += order[:quota]
        spare += order[quota:]
    need = PER_REVIEWER * len(REVIEWERS) - len(picked)
    rng.shuffle(spare)
    picked += spare[:max(need, 0)]  # a group short of its quota is filled from the others
    rng.shuffle(picked)

    own = {r: picked[i::len(REVIEWERS)] for i, r in enumerate(REVIEWERS)}
    out = []
    for k, reviewer in enumerate(REVIEWERS):
        # Second reviews of the previous reviewer's first cases, at positions 2, 5, 8, 11.
        items = [("first", c) for c in own[reviewer]]
        for pos, cnr in zip((1, 4, 7, 10), own[REVIEWERS[k - 1]][:DOUBLE]):
            items.insert(pos, ("second", cnr))
        for n, (kind, cnr) in enumerate(items, 1):
            m = meta[cnr]
            out.append({"reviewer": reviewer, "order": n, "cnr": cnr, "kind": kind,
                        "court_name": m["court_name"], "pages": m["pages"], "title": m["title"]})

    path = ROOT / "data" / "splits" / "review_queue.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    firsts = [r for r in out if r["kind"] == "first"]
    print(f"{len(firsts)} cases, {len(out) - len(firsts)} second reviews -> {path}")
    for g in QUOTA:
        print(f"  {g}: {sum(1 for r in firsts if (r['court_name'] if r['court_name'] in ('Madras', 'Delhi') else 'other') == g)}")
    for reviewer in REVIEWERS:
        print(f"  {reviewer}: {sum(1 for r in out if r['reviewer'] == reviewer)} to review")


if __name__ == "__main__":
    main()
