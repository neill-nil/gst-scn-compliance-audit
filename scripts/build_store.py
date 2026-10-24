"""Build the project data store from screening results.

- data/manifests/screened.csv : one row per screened case (IDs, hash, bucket, flags, reasons). No text.
- data/text/<court>/<cnr>.txt.gz : extracted text for in-scope, non-duplicate cases only.
- data/raw/<court>/<cnr>.pdf : frozen PDF copies for reasoned cases, verified against the recorded sha256.

Later screen files override earlier ones for the same CNR.

Usage: python build_store.py <data_dir> <text_cache_dir> <screen.jsonl> [<screen.jsonl> ...]
"""
import csv
import hashlib
import json
import shutil
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BUCKET = "https://indian-high-court-judgments.s3.ap-south-1.amazonaws.com"
COURT_NAMES = {
    "7_26": "Delhi", "33_10": "Madras", "21_11": "Orissa", "9_13": "Allahabad", "27_1": "Bombay",
    "29_3": "Karnataka", "19_16": "Calcutta", "36_29": "Telangana", "28_2": "Andhra Pradesh",
    "5_15": "Uttarakhand", "3_22": "Punjab and Haryana", "24_17": "Gujarat", "20_7": "Jharkhand",
    "22_18": "Chhattisgarh", "8_9": "Rajasthan", "32_4": "Kerala", "18_6": "Gauhati", "1_12": "Jammu and Kashmir",
    "23_23": "Madhya Pradesh", "17_21": "Meghalaya", "11_24": "Sikkim", "16_20": "Tripura", "10_8": "Patna",
    "14_25": "Manipur",
}
TEXT_BUCKETS = {"reasoned", "remand_or_short", "no_procedural_defect_argued"}
PDF_BUCKETS = {"reasoned"}
COLUMNS = ["cnr", "court", "court_name", "title", "decision_date", "s3_key", "sha256", "pages", "chars_per_page",
           "bucket", "in_scope", "excluded", "defects", "final", "consent_equity", "holdings",
           "duplicate_of_earlier", "s74A", "pre_gst_only", "rule_version", "error"]


def load(paths):
    rows = {}
    for p in paths:
        for line in Path(p).read_text().splitlines():
            r = json.loads(line)
            rows[r["cnr"]] = r
    return list(rows.values())


def fetch_pdf(r, raw_dir: Path):
    dest = raw_dir / r["court"] / f"{r['cnr']}.pdf"
    if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() == r["sha256"]:
        return "kept"
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = urllib.request.urlopen(f"{BUCKET}/{r['s3_key']}").read()
    if hashlib.sha256(data).hexdigest() != r["sha256"]:
        return f"HASH MISMATCH {r['cnr']}"
    dest.write_bytes(data)
    return "downloaded"


def main():
    data_dir, cache = Path(sys.argv[1]), Path(sys.argv[2])
    rows = load(sys.argv[3:])
    (data_dir / "manifests").mkdir(parents=True, exist_ok=True)
    with open(data_dir / "manifests" / "screened.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r["court"], r["cnr"])):
            out = dict(r, court_name=COURT_NAMES.get(r["court"], r["court"]))
            for k in ("excluded", "defects"):
                out[k] = ";".join(r.get(k, []))
            w.writerow(out)

    keep = [r for r in rows if r.get("bucket") in TEXT_BUCKETS and not r.get("duplicate_of_earlier")]
    for r in keep:
        src = cache / (Path(r["s3_key"]).stem + ".txt.gz")
        dest = data_dir / "text" / r["court"] / f"{r['cnr']}.txt.gz"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)

    pdf_rows = [r for r in keep if r["bucket"] in PDF_BUCKETS]
    with ThreadPoolExecutor(16) as ex:
        results = list(ex.map(lambda r: fetch_pdf(r, data_dir / "raw"), pdf_rows))
    problems = [x for x in results if x.startswith("HASH")]

    print(f"manifest rows: {len(rows)}")
    print(f"text stored (in-scope, non-duplicate): {len(keep)}")
    print(f"PDFs frozen (reasoned): {len(pdf_rows)}; hash problems: {len(problems)}")
    for p in problems:
        print("  ", p)


if __name__ == "__main__":
    main()
