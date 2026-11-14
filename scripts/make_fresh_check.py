"""Check sheets for the fresh-case hand check (round 3): one CSV per reviewer listing every call NoticeCheck made
on that reviewer's fresh cases (defect, contested, no defect; "can't tell" is left out), for a person to mark against
the judgment. Reviewers come from data/splits/review_queue_v3.csv; outputs from runs/fresh_nc (notebook H).

Usage: python -m scripts.make_fresh_check   ->  docs/team_plan/fresh_check/r1.csv ... r4.csv
Score the filled sheets with: python -m scripts.make_fresh_check --score
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "team_plan" / "fresh_check"
PLAIN = {
    "hearing_75_4": "No personal hearing before the order (s.75(4))",
    "adjournment_75_5": "Adjournment wrongly refused (s.75(5))",
    "reply_not_considered": "Order ignores the taxpayer's reply (s.75(6))",
    "non_speaking_order": "Order gives no reasons (s.75(6))",
    "demand_beyond_scn": "Order demands more than / other than the notice (s.75(7))",
    "service_169": "Notice or order not properly served (s.169)",
    "signature": "Notice or order unsigned (Rule 26(3))",
    "summary_only": "Only the DRC-01 summary was sent, no full notice (Rule 142(1))",
    "limitation": "Notice or order issued after the time limit (s.73(10)/74(10))",
    "extension_notification_validity": "Relies on the disputed COVID extension notifications (s.168A)",
    "consolidated_scn": "One notice covers several financial years",
    "section_74_ingredients": "s.74 used without fraud/suppression being alleged",
    "other_procedural": "Other procedural complaint",
}
FIELDS = ["case", "cnr", "court", "title", "judgment_pdf", "check", "defect_type", "what_it_means",
          "noticecheck_says", "section", "noticecheck_evidence", "noticecheck_note",
          "YOUR_VERDICT", "COURT_DECIDED", "COMMENT"]
ORDER = {"defect": 0, "contested": 1, "no_defect": 2}


def make():
    queue = list(csv.DictReader(open(ROOT / "data/splits/review_queue_v3.csv", encoding="utf-8")))
    manifest = {r["cnr"]: r for r in csv.DictReader(open(ROOT / "data/manifests/screened.csv", encoding="utf-8"))}
    outs = {json.loads(l)["cnr"]: json.loads(l) for l in open(ROOT / "runs/fresh_nc/outputs.jsonl", encoding="utf-8")}
    OUT.mkdir(parents=True, exist_ok=True)
    for reviewer in sorted({q["reviewer"] for q in queue}):
        rows, n = [], 0
        for q in sorted((q for q in queue if q["reviewer"] == reviewer), key=lambda q: int(q["order"])):
            m, o = manifest[q["cnr"]], outs[q["cnr"]]
            base = {"case": q["order"], "cnr": q["cnr"], "court": q["court_name"], "title": q["title"][:90],
                    "judgment_pdf": f"data/raw/{m['court']}/{q['cnr']}.pdf"}
            calls = sorted((f for f in o["findings"] if f["verdict"] in ORDER), key=lambda f: ORDER[f["verdict"]])
            for f in calls:
                n += 1
                label = lambda e: {"record": "judgment", "statute": f"law {e['ref']}"}.get(e["source"], f"other case {e['ref']}")
                ev = " | ".join(f'[{label(e)}] "{e["quote"][:350]}"' for e in f["evidence"] if e.get("quote"))
                rows.append({**base, "check": n, "defect_type": f["type"], "what_it_means": PLAIN.get(f["type"], f["type"]),
                             "noticecheck_says": f["verdict"].replace("_", " "), "section": f.get("provision") or "",
                             "noticecheck_evidence": ev, "noticecheck_note": (f.get("note") or "")[:300],
                             "YOUR_VERDICT": "", "COURT_DECIDED": "", "COMMENT": ""})
            n += 1
            rows.append({**base, "check": n, "defect_type": "MISSED?", "what_it_means":
                         "Any procedural defect the court found that NoticeCheck did not call a defect? Name the type(s) in COMMENT, or write none.",
                         "noticecheck_says": "", "section": "", "noticecheck_evidence": "", "noticecheck_note": "",
                         "YOUR_VERDICT": "", "COURT_DECIDED": "", "COMMENT": ""})
        with open(OUT / f"{reviewer}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        c = Counter(r["noticecheck_says"] for r in rows if r["defect_type"] != "MISSED?")
        print(f"{reviewer}: {len({r['cnr'] for r in rows})} cases, {sum(c.values())} calls {dict(c)}")


def score():
    rows = [r for p in sorted(OUT.glob("r*.csv")) for r in csv.DictReader(open(p, encoding="utf-8"))]
    calls = [r for r in rows if r["defect_type"] != "MISSED?"]
    todo = [r for r in calls if not r["YOUR_VERDICT"].strip()]
    print(f"{len(calls)} calls, {len(todo)} not yet marked")
    for says in ("defect", "contested", "no defect"):
        sub = [r for r in calls if r["noticecheck_says"] == says and r["YOUR_VERDICT"].strip()]
        v = Counter(r["YOUR_VERDICT"].strip().lower().replace("'", "").replace(" ", "_") for r in sub)
        print(f"  {says:10} {len(sub):3} checked: {dict(v)}")
    d = [r for r in calls if r["noticecheck_says"] == "defect" and r["YOUR_VERDICT"].strip()]
    print("  defect calls by what the court did:", dict(Counter(r["COURT_DECIDED"].strip().lower() for r in d)))
    missed = [r for r in rows if r["defect_type"] == "MISSED?" and r["COMMENT"].strip().lower() not in ("", "none", "no")]
    print(f"  cases with a missed defect noted: {len(missed)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--score", action="store_true")
    score() if ap.parse_args().score else make()
