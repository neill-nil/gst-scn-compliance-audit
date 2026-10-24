"""Sample GST-candidate PDFs per High Court from the AWS eCourts bucket and report text quality.

Usage: python survey_pdfs.py <gst_candidates.parquet> <out_dir> [per_court]
"""
import json
import random
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

import duckdb

BUCKET = "https://indian-high-court-judgments.s3.ap-south-1.amazonaws.com"
COURTS = {
    "33_10": "Madras", "21_11": "Orissa", "7_26": "Delhi", "9_13": "Allahabad",
    "27_1": "Bombay", "29_3": "Karnataka", "19_16": "Calcutta", "36_29": "Telangana",
}
FINAL_MARKERS = re.compile(
    r"(petition is (hereby )?(allowed|dismissed|disposed)|stands? (allowed|dismissed|disposed)"
    r"|impugned order[^.]{0,80}(set aside|quashed)|remanded|remitted)", re.I)
INTERIM_MARKERS = re.compile(r"(list (the matter )?on|issue notice|renotify|next date of hearing|stand over)", re.I)
GST_MARKERS = re.compile(r"(DRC-0[1-7]|section 7[34]\b|75\s*\(4\)|show cause notice)", re.I)


def pdf_key(row):
    year, court, bench = row["y"], row["court"], re.search(r"bench=([^/]+)", row["filename"]).group(1)
    return f"data/pdf/year={year}/court={court}/bench={bench}/{Path(row['pdf_link']).name}"


def text_stats(pdf: Path):
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1)) if "Pages:" in info else 0
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    chars_per_page = len(text.strip()) / max(pages, 1)
    return pages, chars_per_page, text


def main():
    cand, out = Path(sys.argv[1]), Path(sys.argv[2])
    per_court = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    rows = con.sql(f"select * from '{cand}' where y between 2024 and 2026").df().to_dict("records")
    random.seed(7)
    report = []
    for code, name in COURTS.items():
        pool = [r for r in rows if r["court"] == code]
        for r in random.sample(pool, min(per_court, len(pool))):
            key = pdf_key(r)
            dest = out / Path(key).name
            try:
                urllib.request.urlretrieve(f"{BUCKET}/{key}", dest)
                pages, cpp, text = text_stats(dest)
            except Exception as e:  # missing object or broken PDF
                report.append({"court": name, "cnr": r["cnr"], "error": str(e)[:80]})
                continue
            (out / (dest.stem + ".txt")).write_text(text)
            report.append({
                "court": name, "cnr": r["cnr"], "title": r["title"][:90], "pages": pages,
                "chars_per_page": round(cpp), "has_text": cpp > 200,
                "final_marker": bool(FINAL_MARKERS.search(text)),
                "interim_marker": bool(INTERIM_MARKERS.search(text)),
                "gst_procedure_marker": bool(GST_MARKERS.search(text)),
                "s3_key": key,
            })
    (out / "survey.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
