"""Merge finished reviews into the gold files that evaluation reads.

Reads data/gold/annotations/<reviewer>/<cnr>.json (written by the review tool) and writes:
  data/gold/records.jsonl          one gold record per case (the first reviewer's version; the second
                                   reviewer's if only they have finished)
  data/gold/double/first.jsonl     the two versions of each double-reviewed case, for the agreement score:
  data/gold/double/second.jsonl      python -m eval.agreement --a data/gold/double/first.jsonl --b data/gold/double/second.jsonl
  data/gold/out_of_scope.csv       cases reviewers marked out of scope, with their note
  data/splits/test.txt             the CNRs in records.jsonl
Records are written flat (facts and findings at the top level, plus court, case_no, decision_date and
annotation), the format eval/score.py reads. Only status "reviewed" counts; "needs_fix" and
"in_progress" are left out and listed.
Rerun it whenever more reviews come in.

Usage: python -I scripts/build_gold.py
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold"


def flat(record: dict, meta: dict, reviewed_by: list[str]) -> dict:
    review = record["review"]
    return {"cnr": record["cnr"], "schema_version": record["schema_version"], "court": meta["court_name"],
            "case_no": meta["title"].split(" of ")[0], "decision_date": meta["decision_date"],
            **record["facts"], **record["findings"],
            "annotation": {"annotator": review["reviewed_by"], "reviewed_by": reviewed_by, "status": "gold",
                           "drafted_by": review["drafted_by"], "prompt_version": review["prompt_version"],
                           "seconds": review["seconds"], "notes": review["notes"]}}


def write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    with open(ROOT / "data" / "manifests" / "screened.csv", newline="", encoding="utf-8") as f:
        meta = {r["cnr"]: r for r in csv.DictReader(f)}
    with open(ROOT / "data" / "splits" / "review_queue.csv", newline="", encoding="utf-8") as f:
        queue = list(csv.DictReader(f))

    reviews = {}  # (reviewer, cnr) -> record
    for path in sorted((GOLD / "annotations").glob("*/*.json")):
        reviews[(path.parent.name, path.stem)] = json.loads(path.read_text(encoding="utf-8"))

    def status(reviewer, cnr):
        r = reviews.get((reviewer, cnr))
        return r["review"]["status"] if r else "not started"

    gold, first, second, out_of_scope, open_items = [], [], [], [], []
    for cnr in dict.fromkeys(r["cnr"] for r in queue):
        who = {r["kind"]: r["reviewer"] for r in queue if r["cnr"] == cnr}
        done = [k for k in ("first", "second") if k in who and status(who[k], cnr) == "reviewed"]
        oos = [k for k in ("first", "second") if k in who and status(who[k], cnr) == "out_of_scope"]
        if oos and not done:
            out_of_scope.append({"cnr": cnr, "reviewer": who[oos[0]], "note": reviews[(who[oos[0]], cnr)]["review"]["notes"]})
            continue
        if not done:
            open_items.append(f"{cnr} ({who['first']}: {status(who['first'], cnr)})")
            continue
        reviewed_by = [who[k] for k in done]
        gold.append(flat(reviews[(who[done[0]], cnr)], meta[cnr], reviewed_by))
        if len(done) == 2:
            first.append(flat(reviews[(who["first"], cnr)], meta[cnr], reviewed_by))
            second.append(flat(reviews[(who["second"], cnr)], meta[cnr], reviewed_by))

    write_jsonl(GOLD / "records.jsonl", gold)
    write_jsonl(GOLD / "double" / "first.jsonl", first)
    write_jsonl(GOLD / "double" / "second.jsonl", second)
    with open(GOLD / "out_of_scope.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cnr", "reviewer", "note"])
        w.writeheader()
        w.writerows(out_of_scope)
    (ROOT / "data" / "splits" / "test.txt").write_text("".join(r["cnr"] + "\n" for r in gold), encoding="utf-8")

    print(f"gold: {len(gold)} cases   double-reviewed: {len(first)}   out of scope: {len(out_of_scope)}   "
          f"not finished: {len(open_items)}")
    for r in reviewers_left(queue, status):
        print("  ", r)


def reviewers_left(queue, status):
    left = {}
    for r in queue:
        if status(r["reviewer"], r["cnr"]) not in ("reviewed", "out_of_scope"):
            left.setdefault(r["reviewer"], []).append(r["cnr"])
    return [f"{rv}: {len(c)} left" for rv, c in sorted(left.items())]


if __name__ == "__main__":
    main()
