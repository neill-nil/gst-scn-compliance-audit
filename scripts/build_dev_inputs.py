"""Checker inputs for the dev split, for building and tuning NoticeCheck without touching test cases.

For each dev case it takes the best record available: a human-reviewed one from data/gold/annotations/dev/
(once the dev queue is reviewed), else the role-1 pilot record (data/pilot_drafts/role1/v0_1/), else the
Gemini draft (data/prefill/v1/). It flattens it like scripts/build_gold.py and builds the views with
src/baselines/inputs.py. It also writes the dev answer key (data/interim/dev/records.jsonl) for scoring.
Drafts are unreviewed, so dev scores are only for spotting problems, never for reporting.

Usage: python -m scripts.build_dev_inputs     ->  data/interim/dev/{records,full_record,notice_only}.jsonl
"""
import csv
import json
from pathlib import Path

from src.baselines.inputs import build_view

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "dev"


def best_record(cnr: str):
    for path, source in ((ROOT / "data/gold/annotations/dev" / f"{cnr}.json", "reviewed"),
                         (ROOT / "data/pilot_drafts/role1/v0_1" / f"{cnr}.json", "pilot_reviewed"),
                         (ROOT / "data/prefill/v1" / f"{cnr}.json", "draft")):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8")), source
    return None, None


def main():
    with open(ROOT / "data/manifests/screened.csv", newline="", encoding="utf-8") as f:
        meta = {r["cnr"]: r for r in csv.DictReader(f)}
    dev = [l.strip() for l in (ROOT / "data/splits/dev.txt").read_text().splitlines() if l.strip()]
    OUT.mkdir(parents=True, exist_ok=True)
    records, sources = [], {}
    for cnr in dev:
        rec, source = best_record(cnr)
        if rec is None or not rec.get("facts") or not rec.get("findings"):
            continue
        m = meta[cnr]
        records.append({"cnr": cnr, "schema_version": "0.1", "court": m["court_name"],
                        "case_no": m["title"].split(" of ")[0], "decision_date": m["decision_date"],
                        **rec["facts"], **rec["findings"], "annotation": {"source": source}})
        sources[source] = sources.get(source, 0) + 1
    with open(OUT / "records.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    for view in ("full_record", "notice_only"):
        with open(OUT / f"{view}.jsonl", "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(build_view(r, view), ensure_ascii=False) + "\n")
    (OUT / "dev.txt").write_text("".join(r["cnr"] + "\n" for r in records), encoding="utf-8")
    print(f"{len(records)} dev cases ({sources}) -> {OUT}")


if __name__ == "__main__":
    main()
