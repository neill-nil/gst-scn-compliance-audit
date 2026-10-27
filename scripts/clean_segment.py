"""Clean a High Court judgment PDF and split it into numbered paragraphs.

Cleaning is deletion-only: whole boilerplate lines are dropped and whitespace is
collapsed, but no character inside a kept line is changed. Any quote taken from
the cleaned text therefore also exists, token for token, in the raw PDF text.

Usage: python clean_segment.py <judgment.pdf> <out_dir>
Writes <out_dir>/<stem>.json with provenance, cleaning stats and paragraphs.
"""
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

BOILERPLATE = [re.compile(p, re.I) for p in [
    # Delhi
    r"^Signature Not Verified$", r"^Digitally Signed", r"^By:\s*[A-Z .]+$", r"^Signing Date:",
    r"^\d{2}:\d{2}:\d{2}$", r"^This is a digitally signed order\.?$",
    r"^The authenticity of the order can be re-verified", r"^The Order is downloaded from the DHC Server",
    r"Page \d+ of \d+\s*$",
    # Madras
    r"^https?://www\.mhc\.tn\.gov\.in/judis", r"^\(?\d{1,3}/\d{1,3}\)?$",
    # Orissa and other e-signed orders
    r"^Signed by:", r"^Designation:", r"^Reason:\s*Authentication", r"^Location:\s*High Court", r"^Date:\s*\d",
    # Karnataka
    r"^NC:\s*\d{4}:KHC", r"^HC-KAR$", r"^-\s*\d+\s*-$",
]]
PARA_START = re.compile(r"^\s*[“\"]?\s*(\d{1,3})\s*\.\s+\S")


def pdf_text_pages(pdf: Path) -> list[str]:
    out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True)
    return out.stdout.split("\f")


def repeated_lines(pages: list[str]) -> set[str]:
    """Short lines that recur on at least half the pages are running headers or footers."""
    if len(pages) < 3:
        return set()
    seen = Counter()
    for page in pages:
        seen.update({re.sub(r"\d+", "#", l.strip()) for l in page.splitlines() if 0 < len(l.strip()) < 60})
    return {l for l, n in seen.items() if n >= max(3, len(pages) // 2)}


def clean(pages: list[str]):
    repeats = repeated_lines(pages)
    kept, dropped = [], []
    for page_no, page in enumerate(pages, 1):
        for line in page.splitlines():
            s = line.strip()
            if not s:
                continue
            if any(p.search(s) for p in BOILERPLATE) or re.sub(r"\d+", "#", s) in repeats:
                dropped.append(s)
                continue
            kept.append((page_no, s))
    return kept, dropped


def segment(lines: list[tuple[int, str]]):
    """Split on numbered paragraphs; a number only starts a paragraph if it is the next in sequence.

    Some courts (Madras, Orissa) leave the first paragraph unnumbered, so numbering may start at 2.
    """
    paras = [{"n": 0, "role_hint": "cause_title", "page": 1, "lines": []}]
    expected = 1
    # Paragraphs of a quoted judgment must not be taken as ours. Two signals: the quoted paragraph's
    # line opens with a quotation mark, or we are inside an open quotation. Real text often leaves a
    # quotation unclosed, so an open quote stops counting after 25 lines.
    in_quote, lines_in_quote = False, 0
    for page_no, s in lines:
        m = PARA_START.match(s)
        n = int(m.group(1)) if m else None
        quoted_line = s.lstrip().startswith(("“", '"'))
        inside = in_quote and lines_in_quote <= 25
        if not quoted_line and not inside and n is not None and (n == expected or (expected == 1 and n == 2)):
            paras.append({"n": n, "page": page_no, "lines": []})
            expected = n + 1
            in_quote, lines_in_quote = False, 0
        paras[-1]["lines"].append(s)
        for ch in s:
            if ch == "“":
                in_quote = True
            elif ch == "”" or (ch == '"' and in_quote):
                in_quote = False
        lines_in_quote = lines_in_quote + 1 if in_quote else 0
    for p in paras:
        p["text"] = re.sub(r"\s+", " ", " ".join(p.pop("lines"))).strip()
    return paras


def main():
    pdf, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    pages = pdf_text_pages(pdf)
    raw = "\n".join(pages)
    kept, dropped = clean(pages)
    paras = segment(kept)
    raw_tokens = raw.split()
    kept_tokens = " ".join(p["text"] for p in paras).split()
    record = {
        "source_pdf": pdf.name,
        "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
        "pages": len([p for p in pages if p.strip()]),
        "raw_chars": len(raw),
        "dropped_lines": len(dropped),
        "dropped_examples": sorted(set(dropped))[:8],
        "kept_token_ratio": round(len(kept_tokens) / max(len(raw_tokens), 1), 3),
        "num_paragraphs": len(paras) - 1,
        "segmentation": "numbered" if len(paras) > 1 else "unnumbered_single_block",
        "paragraphs": paras,
    }
    (out / f"{pdf.stem}.json").write_text(json.dumps(record, indent=1, ensure_ascii=False))
    summary = {k: v for k, v in record.items() if k != "paragraphs"}
    print(json.dumps(summary, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
