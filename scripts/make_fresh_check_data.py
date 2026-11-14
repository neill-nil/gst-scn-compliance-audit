"""Data for the fresh-case check page: each reviewer's 5 cases with the judgment's numbered paragraphs and every
NoticeCheck call (defect / contested / no defect), same numbering as docs/team_plan/fresh_check/rN.csv.

Usage: python -m scripts.make_fresh_check_data OUT.json
"""
import csv
import json
import re
import sys
from pathlib import Path

from scripts.make_fresh_check import ORDER, PLAIN
from src.prefill.verify_quotes import judgment_paragraphs

ROOT = Path(__file__).resolve().parents[1]
norm = lambda s: re.sub(r"\s+", " ", (s or "").replace("“", '"').replace("”", '"').replace("’", "'")).strip().lower()


def clean(q):
    q = re.sub(r'^\s*\[?\s*record\s*:\s*', "", q or "", flags=re.I).strip()
    q = re.sub(r'\]\s*$', "", q).strip().strip('"').strip()
    m = re.search(r'\[record:\s*"(.+)', q)  # compact-view lines such as 'order reasoning  [record: "..."'
    return m.group(1).rstrip('"]').strip() if m else q


def find_para(quote, paras):
    q = norm(clean(quote))
    for probe in (q, q[:80], q[:40]):
        if len(probe) >= 20:
            for p in paras:
                if probe in norm(p["text"]):
                    return p["n"]
    return None


def main(out):
    queue = list(csv.DictReader(open(ROOT / "data/splits/review_queue_v3.csv", encoding="utf-8")))
    manifest = {r["cnr"]: r for r in csv.DictReader(open(ROOT / "data/manifests/screened.csv", encoding="utf-8"))}
    outs = {json.loads(l)["cnr"]: json.loads(l) for l in open(ROOT / "runs/fresh_nc/outputs.jsonl", encoding="utf-8")}
    data = {"reviewers": {}, "plain": PLAIN}
    found = total = 0
    for reviewer in sorted({q["reviewer"] for q in queue}):
        cases, n = [], 0
        for q in sorted((q for q in queue if q["reviewer"] == reviewer), key=lambda q: int(q["order"])):
            paras = [{"n": p["n"], "text": p["text"]} for p in judgment_paragraphs(q["cnr"])]
            calls = []
            for f in sorted((f for f in outs[q["cnr"]]["findings"] if f["verdict"] in ORDER), key=lambda f: ORDER[f["verdict"]]):
                n += 1
                ev = []
                for e in f["evidence"]:
                    if not e.get("quote"):
                        continue
                    item = {"source": e["source"], "ref": e.get("ref"), "quote": clean(e["quote"])[:600]}
                    if e["source"] == "record":
                        item["para"] = find_para(e["quote"], paras)
                        total += 1; found += item["para"] is not None
                    ev.append(item)
                calls.append({"check": n, "type": f["type"], "says": f["verdict"], "section": f.get("provision"),
                              "note": f.get("note"), "evidence": ev})
            n += 1
            m = manifest[q["cnr"]]
            cases.append({"order": int(q["order"]), "cnr": q["cnr"], "court": q["court_name"], "title": q["title"],
                          "date": m["decision_date"], "pages": q["pages"], "paragraphs": paras, "calls": calls,
                          "missed_check": n})
        data["reviewers"][reviewer] = cases
    Path(out).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out}: {Path(out).stat().st_size // 1024} KB; judgment quotes located {found}/{total}")


if __name__ == "__main__":
    main(sys.argv[1])
