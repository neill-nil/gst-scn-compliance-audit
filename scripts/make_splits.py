"""Write the dev / held-out / reserved / precedent splits (data/splits/*.txt, one CNR per line).

- test.txt      : written by scripts/build_gold.py (the human-verified test cases); never touched here.
- dev.txt       : schema-pilot and hand-labelled cases, plus any cases in data/splits/dev_queue.csv.
                  Prompts, check cards and thresholds are tuned on these only.
- heldout.txt   : every in-scope case from HELDOUT_COURT (a whole court kept out of all tuning and retrieval).
- reserved.txt  : reasoned drafts not yet in any split: the pool for test v2 and dev; kept out of retrieval
                  until test v2 is frozen.
- precedent.txt : everything else that is in scope and readable. caselaw_search may only return these.

Usage: python -I scripts/make_splits.py
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / "data" / "splits"
HELDOUT_COURT = "Karnataka"     # decision D4 in docs/team_plan/final_plan.md
EXCLUDED_COURTS = {"36_29"}     # Telangana: unreadable OCR


def cnrs(name: str) -> set[str]:
    path = SPLITS / name
    if not path.exists():
        return set()
    if path.suffix == ".txt":
        return {l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()}
    with open(path, newline="", encoding="utf-8") as f:
        return {r["cnr"] for r in csv.DictReader(f)}


def write(name: str, ids: set[str]):
    (SPLITS / name).write_text("".join(c + "\n" for c in sorted(ids)), encoding="utf-8")
    print(f"{name}: {len(ids)}")


def main():
    with open(ROOT / "data" / "manifests" / "screened.csv", newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["in_scope"] == "True" and r["duplicate_of_earlier"] == "False"
                and r["court"] not in EXCLUDED_COURTS]
    test = cnrs("test.txt") | cnrs("review_queue.csv") | cnrs("review_queue_v2.csv")
    dev = cnrs("schema_pilot.csv") | cnrs("hand_labels_reasoned.csv") | cnrs("dev_queue.csv")
    heldout = {r["cnr"] for r in rows if r["court_name"] == HELDOUT_COURT} - dev
    reserved = {r["cnr"] for r in rows if r["bucket"] == "reasoned"} - test - dev - heldout
    precedent = {r["cnr"] for r in rows} - test - dev - heldout - reserved
    assert not (test & precedent or dev & precedent or heldout & precedent)
    write("dev.txt", dev)
    write("heldout.txt", heldout)
    write("reserved.txt", reserved)
    write("precedent.txt", precedent)


if __name__ == "__main__":
    main()
