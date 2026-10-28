"""Check that every quote in a case record appears word for word in its judgment.

The judgment is cleaned and segmented with scripts/clean_segment.py logic. A quote passes if it occurs
in the cleaned text after collapsing whitespace. It also reports whether the quote sits in the paragraph
the record names (informational: the segmenter can merge paragraphs when numbering is unusual).

Usage: python -m src.prefill.verify_quotes <record.json> [<record.json> ...]
Each record's judgment is found at data/raw/<court_code>/<cnr>.pdf via the manifest.
"""
import csv
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("clean_segment", ROOT / "scripts" / "clean_segment.py")
clean_segment = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(clean_segment)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def court_code(cnr: str) -> str:
    with open(ROOT / "data" / "manifests" / "screened.csv", newline="") as f:
        for row in csv.DictReader(f):
            if row["cnr"] == cnr:
                return row["court"]
    raise KeyError(f"{cnr} not in manifest")


def judgment_paragraphs(cnr: str) -> list[dict]:
    pdf = ROOT / "data" / "raw" / court_code(cnr) / f"{cnr}.pdf"
    kept, _ = clean_segment.clean(clean_segment.pdf_text_pages(pdf))
    return clean_segment.segment(kept)


def quotes_in(record) -> list[tuple[str, str, int | None]]:
    """(location, quote, para) for every object in the record that has a "quote" key."""
    found = []

    def walk(obj, path):
        if isinstance(obj, dict):
            if isinstance(obj.get("quote"), str) and obj["quote"]:
                label = obj.get("field") or obj.get("type") or path
                found.append((f"{path}:{label}", obj["quote"], obj.get("para")))
            for k, v in obj.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{path}[{i}]")

    walk(record, "")
    return found


def verify(record: dict) -> list[dict]:
    paras = judgment_paragraphs(record["cnr"])
    full = norm(" ".join(p["text"] for p in paras))
    results = []
    for where, quote, para in quotes_in(record):
        q = norm(quote)
        ok = q in full
        in_para = any(p["n"] == para and q in norm(p["text"]) for p in paras) if para is not None else None
        results.append({"where": where, "para": para, "found": ok, "in_named_para": in_para, "quote": quote})
    return results


def main():
    bad = 0
    for path in sys.argv[1:]:
        record = json.loads(Path(path).read_text())
        res = verify(record)
        missing = [r for r in res if not r["found"]]
        bad += len(missing)
        moved = [r for r in res if r["found"] and r["in_named_para"] is False]
        print(f"{record['cnr']}: {len(res)} quotes, {len(res) - len(missing)} found verbatim, "
              f"{len(missing)} NOT FOUND, {len(moved)} found outside the named paragraph (splitter merge)")
        for r in missing:
            print(f"   NOT FOUND  {r['where']}  para {r['para']}: {r['quote'][:100]}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
