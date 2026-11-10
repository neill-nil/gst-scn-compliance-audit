"""Review queue for the final: dev cases (for tuning), test v2 additions, and the held-out court.

Pool: reasoned drafts in data/splits/reserved.txt (dev and test) and data/splits/heldout.txt (held-out court),
with at least one defect argued and at most MAX_PAGES pages.
- dev:     DEV_PER_GROUP Madras + DEV_PER_GROUP Delhi cases. Reviewed first, because tuning waits on them.
- test:    every case from the other courts, plus Madras and Delhi up to their quotas (Madras kept under 40% of
           the whole test set, at most MAX_DELHI_TAB more Delhi "Additional Notices" template orders).
           Cases with a rejected finding go first, so false alarms stay measurable.
- heldout: every held-out-court case.
DOUBLE more test cases get a second, independent review (no AI help), bringing the total to 40.
Reviewer load follows WEIGHT (Neill has the design work, so a smaller share).
Deterministic. Usage: python -I scripts/make_review_queue_v2.py  ->  data/splits/review_queue_v2.csv
"""
import csv
import gzip
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWERS = {"r1": 0.6, "r2": 1.0, "r3": 1.0, "r4": 1.0}   # relative share of first reviews
MAX_PAGES = 40
DEV_PER_GROUP = 10
MADRAS_NEW, DELHI_NEW, MAX_DELHI_TAB = 32, 14, 3
DOUBLE = 27          # 13 double-reviewed in v1 + 27 = 40
SEED = 1105


def ids(name):
    return [l.strip() for l in (ROOT / "data/splits" / name).read_text().splitlines() if l.strip()]


def main():
    with open(ROOT / "data/manifests/screened.csv", newline="", encoding="utf-8") as f:
        meta = {r["cnr"]: r for r in csv.DictReader(f)}

    def usable(c):
        p = ROOT / "data/prefill/v1" / f"{c}.json"
        if not p.exists() or int(meta[c]["pages"]) > MAX_PAGES:
            return None
        d = json.loads(p.read_text(encoding="utf-8"))["findings"]["defects_argued"]
        return d or None

    def tab(c):
        p = ROOT / "data/text" / meta[c]["court"] / f"{c}.txt.gz"
        return p.exists() and "additional notices" in gzip.open(p, "rt", errors="replace").read().lower()

    with open(ROOT / "data/splits/review_queue.csv", newline="", encoding="utf-8") as f:
        reviewed_v1 = {r["cnr"] for r in csv.DictReader(f)}  # already reviewed at the mid
    rng = random.Random(SEED)
    # The pool is computed from the manifest, not reserved.txt, so rerunning after make_splits gives the same queue.
    with open(ROOT / "data/splits/schema_pilot.csv", newline="", encoding="utf-8") as f:
        pilot = {r["cnr"] for r in csv.DictReader(f)}
    with open(ROOT / "data/splits/hand_labels_reasoned.csv", newline="", encoding="utf-8") as f:
        pilot |= {r["cnr"] for r in csv.DictReader(f)}
    heldout_all = set(ids("heldout.txt"))
    candidates = [c for c, m in meta.items() if m["bucket"] == "reasoned" and m["in_scope"] == "True"
                  and m["duplicate_of_earlier"] == "False" and m["court"] != "36_29"]
    pool = {c: d for c in sorted(candidates) if c not in pilot and c not in heldout_all and c not in reviewed_v1 and (d := usable(c))}
    held = sorted(c for c in ids("heldout.txt") if meta[c]["bucket"] == "reasoned" and c not in reviewed_v1 and usable(c))

    def ordered(cs):  # rejected-finding cases first, each part shuffled
        rej = [c for c in cs if any(x["finding"] == "defect_rejected" for x in pool[c])]
        rest = [c for c in cs if c not in rej]
        rng.shuffle(rej), rng.shuffle(rest)
        return rej + rest

    madras = sorted(c for c in pool if meta[c]["court_name"] == "Madras")
    delhi = sorted(c for c in pool if meta[c]["court_name"] == "Delhi")
    other = sorted(c for c in pool if c not in madras and c not in delhi)
    rng.shuffle(madras), rng.shuffle(delhi)
    dev = madras[:DEV_PER_GROUP] + [c for c in delhi if not tab(c)][:DEV_PER_GROUP]
    madras_t = ordered([c for c in madras if c not in dev])[:MADRAS_NEW]
    delhi_left = ordered([c for c in delhi if c not in dev])
    delhi_tab = [c for c in delhi_left if tab(c)][:MAX_DELHI_TAB]
    delhi_t = (delhi_tab + [c for c in delhi_left if not tab(c)])[:DELHI_NEW]
    test = ordered(other) + madras_t + delhi_t
    rng.shuffle(test)

    # First reviews, spread by weight; dev first in everyone's list.
    names, weights = list(REVIEWERS), list(REVIEWERS.values())
    load = dict.fromkeys(names, 0.0)
    lists = {r: [] for r in names}
    for kind_set, cases in (("dev", dev), ("test", test), ("heldout", held)):
        for c in cases:
            r = min(names, key=lambda n: (load[n] / REVIEWERS[n], n))
            load[r] += 1
            lists[r].append(("first", kind_set, c))
    # Second reviews of test cases, by a different reviewer, spread through the lists.
    firsts = {c: r for r, items in lists.items() for _, s, c in items if s == "test"}
    for k, c in enumerate([c for c in test if c in firsts][:DOUBLE]):
        r = sorted((n for n in names if n != firsts[c]), key=lambda n: (len(lists[n]) / REVIEWERS[n], n))[0]
        n_dev = sum(1 for x in lists[r] if x[1] == "dev")  # after the dev block, every third place
        pos = min(len(lists[r]), n_dev + 1 + 3 * sum(1 for x in lists[r] if x[0] == "second"))
        lists[r].insert(pos, ("second", "test", c))

    # Review order (11 Nov, 4 days left): held-out first, then test (second reviews spread through it), dev last
    # and optional (NoticeCheck can be tuned on drafts if dev reviews do not get done). Assignments are unchanged.
    priority = {"heldout": 0, "test": 1, "dev": 2}
    lists = {r: sorted(items, key=lambda x: priority[x[1]]) for r, items in lists.items()}

    rows = [{"reviewer": r, "order": n, "cnr": c, "kind": kind, "set": s, "court_name": meta[c]["court_name"],
             "pages": meta[c]["pages"], "title": meta[c]["title"]}
            for r in names for n, (kind, s, c) in enumerate(lists[r], 1)]
    path = ROOT / "data/splits/review_queue_v2.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"dev {len(dev)}, test {len(test)}, heldout {len(held)}, second reviews {DOUBLE} -> {path}")
    for r in names:
        mine = [x for x in rows if x["reviewer"] == r]
        print(f"  {r}: {len(mine)} reviews ({sum(x['set'] == 'dev' for x in mine)} dev, last)")


if __name__ == "__main__":
    main()
