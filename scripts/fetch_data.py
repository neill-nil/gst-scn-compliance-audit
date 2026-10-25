"""Download the in-scope data listed in the committed manifest, so teammates don't need to re-screen.

Reads data/manifests/screened.csv, downloads each selected PDF from the AWS eCourts bucket,
verifies its sha256 against the manifest, writes extracted text to data/text/ and keeps PDFs
of reasoned cases in data/raw/.

Usage: python fetch_data.py [--reasoned-only] [--data-dir data]
  --reasoned-only   only the reasoned cases (~400 PDFs, about a minute)
  default           all in-scope non-duplicate cases (~4,800 PDFs, about 10–15 minutes)
"""
import argparse
import csv
import gzip
import hashlib
import subprocess
import tempfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BUCKET = "https://indian-high-court-judgments.s3.ap-south-1.amazonaws.com"
TEXT_BUCKETS = {"reasoned", "remand_or_short", "no_procedural_defect_argued"}


def download(key: str) -> bytes:
    for attempt in range(4):
        try:
            return urllib.request.urlopen(f"{BUCKET}/{key}", timeout=60).read()
        except OSError:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def fetch(row, data_dir: Path) -> str:
    text_path = data_dir / "text" / row["court"] / f"{row['cnr']}.txt.gz"
    pdf_path = data_dir / "raw" / row["court"] / f"{row['cnr']}.pdf"
    keep_pdf = row["bucket"] == "reasoned"
    if text_path.exists() and (not keep_pdf or pdf_path.exists()):
        return "kept"
    try:
        data = download(row["s3_key"])
    except OSError as e:
        return f"FAILED {row['cnr']}: {e}"
    if hashlib.sha256(data).hexdigest() != row["sha256"]:
        return f"HASH MISMATCH {row['cnr']}"
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(data)
        tmp.flush()
        text = subprocess.run(["pdftotext", "-layout", tmp.name, "-"], capture_output=True, text=True).stdout
    text_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.write_bytes(gzip.compress(text.encode()))
    if keep_pdf:
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(data)
    return "downloaded"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reasoned-only", action="store_true")
    ap.add_argument("--data-dir", default="data")
    args = ap.parse_args()
    data_dir = Path(args.data_dir)
    with open(data_dir / "manifests" / "screened.csv", newline="") as f:
        rows = [r for r in csv.DictReader(f)
                if r["bucket"] in TEXT_BUCKETS and r["duplicate_of_earlier"] == "False"]
    if args.reasoned_only:
        rows = [r for r in rows if r["bucket"] == "reasoned"]
    with ThreadPoolExecutor(16) as ex:
        results = list(ex.map(lambda r: fetch(r, data_dir), rows))
    problems = [x for x in results if x not in ("kept", "downloaded")]
    print(f"selected {len(rows)}; downloaded {results.count('downloaded')}; already present {results.count('kept')}; problems {len(problems)}")
    for p in problems:
        print("  ", p)


if __name__ == "__main__":
    main()
