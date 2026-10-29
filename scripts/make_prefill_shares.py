"""Split the reasoned pool into 4 equal shares (r1..r4) for parallel Gemini pre-fill.

Cases are sorted by page count, longest first, and each goes to the share with the fewest pages so far
(among shares not yet full). Every share gets the same number of cases (±1), about the same number of
pages (= API tokens) and a mix of courts.
Deterministic: rerunning gives the same shares.

Usage: python scripts/make_prefill_shares.py   ->  data/splits/prefill_shares.csv
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARES = ["r1", "r2", "r3", "r4"]
EXCLUDED_COURTS = {"36_29"}  # Telangana: bad OCR, excluded from gold


def main():
    with open(ROOT / "data" / "manifests" / "screened.csv", newline="") as f:
        rows = [r for r in csv.DictReader(f)
                if r["bucket"] == "reasoned" and r["duplicate_of_earlier"] == "False"
                and r["court"] not in EXCLUDED_COURTS]
    rows.sort(key=lambda r: (-int(r["pages"]), r["cnr"]))
    cap = -(-len(rows) // len(SHARES))
    count, pages = dict.fromkeys(SHARES, 0), dict.fromkeys(SHARES, 0)
    out = []
    for r in rows:
        share = min((s for s in SHARES if count[s] < cap), key=lambda s: (pages[s], count[s], s))
        count[share] += 1
        pages[share] += int(r["pages"])
        out.append({"cnr": r["cnr"], "share": share, "court": r["court"], "court_name": r["court_name"],
                    "pages": r["pages"], "title": r["title"]})
    out.sort(key=lambda r: (r["share"], r["cnr"]))
    path = ROOT / "data" / "splits" / "prefill_shares.csv"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    for s in SHARES:
        mine = [r for r in out if r["share"] == s]
        print(s, len(mine), "cases,", sum(int(r["pages"]) for r in mine), "pages")


if __name__ == "__main__":
    main()
