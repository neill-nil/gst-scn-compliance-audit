"""Pick a FRESH evaluation set: in-scope cases never reviewed, trained on, queued or used anywhere, in which the
court actually decides at least one procedural complaint. Run after the system was frozen, so these labels are blind.

1. Candidates from the manifest: buckets remand_or_short / no_procedural_defect_argued (the screen's weaker
   buckets; every "reasoned" case is already used or is a duplicate), in scope, not duplicates, not Telangana
   (bad OCR), not Karnataka (held-out court), 4-40 pages, at least one holding phrase, decided 2025 or later.
2. Gemini triage on the opening and closing text: does the court rule on a procedural complaint?
3. Keep up to --n cases, spread over courts -> data/splits/fresh.txt and data/splits/fresh_triage.jsonl.
Triage is only a filter; the labels come from human review (review_queue_v3.csv).

Usage: python -m scripts.triage_fresh [--sample 70] [--n 20]
"""
import argparse
import csv
import gzip
import json
import random
from collections import defaultdict
from pathlib import Path

from src.common.llm import complete

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / "data" / "splits"
SCHEMA = {"type": "object", "required": ["gst_demand_73_74", "rules_on_procedural_complaint", "complaints", "reason"],
          "properties": {"gst_demand_73_74": {"type": "boolean"},
                         "rules_on_procedural_complaint": {"type": "boolean"},
                         "complaints": {"type": "array", "items": {"type": "object", "required": ["complaint", "court_finding"],
                                        "properties": {"complaint": {"type": "string"},
                                                       "court_finding": {"enum": ["defect_found", "defect_rejected", "not_decided"]}}}},
                         "reason": {"type": "string"}}}
PROMPT = """Below are the opening and closing parts of an Indian High Court judgment.
Answer: (1) Is the case about a GST demand proceeding under section 73 or 74 of the CGST/SGST Act (show cause
notice, then a demand order)? (2) Does the court itself rule on at least one complaint about the department's
PROCEDURE (hearing not given, reply ignored, order without reasons, notice unsigned or not served, time limit,
demand beyond the notice, one notice for several years, etc.)? A remand by consent or "for one more opportunity"
without deciding the complaint does NOT count. List each procedural complaint and the court's finding.

OPENING:
{head}

CLOSING:
{tail}
"""


def ids(name):
    p = SPLITS / name
    return {l.strip() for l in p.read_text().splitlines() if l.strip()} if p.exists() else set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=70)
    ap.add_argument("--n", type=int, default=20)
    args = ap.parse_args()

    used = ids("test.txt") | ids("heldout.txt") | ids("dev.txt") | ids("reserved.txt")
    for q in ("review_queue.csv", "review_queue_v2.csv"):
        used |= {r["cnr"] for r in csv.DictReader(open(SPLITS / q, encoding="utf-8"))}
    used |= {r["cnr"] for r in csv.DictReader(open(ROOT / "data/gold/out_of_scope.csv", encoding="utf-8"))}
    rows = [r for r in csv.DictReader(open(ROOT / "data/manifests/screened.csv", encoding="utf-8"))
            if r["bucket"] in ("remand_or_short", "no_procedural_defect_argued") and r["in_scope"] == "True"
            and r["duplicate_of_earlier"] != "True" and r["court"] not in ("36_29", "29_3") and r["cnr"] not in used
            and 4 <= int(r["pages"] or 0) <= 40 and int(r["holdings"] or 0) >= 1 and r["decision_date"] >= "2025-01-01"
            and (ROOT / "data/text" / r["court"] / f"{r['cnr']}.txt.gz").exists()]
    by_court = defaultdict(list)
    for r in sorted(rows, key=lambda r: r["cnr"]):
        by_court[r["court_name"]].append(r)
    rng = random.Random(14)
    for v in by_court.values():
        rng.shuffle(v)
    sample = []
    while len(sample) < args.sample and any(by_court.values()):  # round robin over courts
        for court in sorted(by_court):
            if by_court[court] and len(sample) < args.sample:
                sample.append(by_court[court].pop())
    print(f"{len(rows)} candidates; triaging {len(sample)}")

    out = []
    for i, r in enumerate(sample, 1):
        text = gzip.decompress((ROOT / "data/text" / r["court"] / f"{r['cnr']}.txt.gz").read_bytes()).decode()
        text = "\n".join(l.strip() for l in text.splitlines() if l.strip())
        res = complete("gemini", [{"role": "user", "content": PROMPT.format(head=text[:2500], tail=text[-6000:])}],
                       json_schema=SCHEMA, tag="triage:fresh")
        j = res["json"] or {}
        keep = bool(j.get("gst_demand_73_74") and j.get("rules_on_procedural_complaint")
                    and any(c["court_finding"] != "not_decided" for c in j.get("complaints", [])))
        out.append({"cnr": r["cnr"], "court": r["court_name"], "pages": r["pages"], "keep": keep, "triage": j})
        print(f"[{i}/{len(sample)}] {r['cnr']} {r['court_name']} keep={keep}", flush=True)

    kept = defaultdict(list)
    for o in out:
        if o["keep"]:
            kept[o["court"]].append(o)
    chosen = []
    while len(chosen) < args.n and any(kept.values()):
        for court in sorted(kept):
            if kept[court] and len(chosen) < args.n:
                chosen.append(kept[court].pop(0))
    with open(SPLITS / "fresh_triage.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(o, ensure_ascii=False) + "\n" for o in out)
    (SPLITS / "fresh.txt").write_text("".join(o["cnr"] + "\n" for o in chosen))
    print(f"kept {sum(o['keep'] for o in out)} of {len(out)}; chose {len(chosen)}: "
          + ", ".join(f"{c} {sum(o['court'] == c for o in chosen)}" for c in sorted({o['court'] for o in chosen})))


if __name__ == "__main__":
    main()
