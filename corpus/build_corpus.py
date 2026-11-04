"""Build the frozen statute corpus from the official PDFs listed in corpus/SOURCES.md.

Each PDF is checked against its SHA-256, converted with pdftotext, and split into section (rule) units and
sub-section (sub-rule) units. Cleaning is deletion-only: page numbers, "Page x of y" lines, amendment
footnotes and the arrangement of sections are dropped; the statutory text itself is never rewritten.

Usage: python -I corpus/build_corpus.py      ->  corpus/units.jsonl
Needs the PDFs in corpus/source_files/ (download them from the URLs in corpus/SOURCES.md).
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = {
    "CGST Act": {"file": "cgst_act_2017.pdf", "unit": "s", "version_date": "2026-06-11",
                 "sha256": "c4dbd51f0355360e63d8a25560547f9e7e00b3af349d8666265ab60b4610cf24",
                 "start": "1. Short title, extent and commencement.—", "end": r"^THE FIRST SCHEDULE"},
    "CGST Rules": {"file": "cgst_rules_part_a.pdf", "unit": "r", "version_date": "2022-01-01",
                   "sha256": "483c56f0d2a5e674348c617c63275dacee965809e8fe96a40c5fffecdf186a15",
                   "start": "1. Short title and Commencement.-", "end": None},
}
HEADING = re.compile(r"^\[?\s?(\d{1,3})([A-Z]{0,3})\.\s?\[?\s?([A-Z(][^\n]*)")
FOOTNOTE = re.compile(r"^\d+\.\s+(Ins\.|Subs\.|The words|Omitted|Renumbered|Added|Clause|Sub-section|Section|"
                      r"Explanation|Proviso|Brought|Vide|Notification|w\.e\.f)")
JUNK = re.compile(r"^(\d{1,3}|Page \d+ of \d+)$")
# Rules PDF: amendment notes such as "Inserted vide Notf no. 49/2019-CT dt. 09.10.2019"
NOTE = re.compile(r"^(Inserted|Substituted|Subsitituted|Omitted|Words|Rule|Sub-rule|Clause|For|The words)\b.*\b(vide|Notf|Notification)\b")
SUBSECTION = re.compile(r"(?:^|(?<=[\s—–\-]))\[?\((\d{1,2}[A-Z]?)\)(?:\s|(?=[A-Z\[(]))")


def key(num: str, suffix: str):
    return int(num), suffix


def section_units(name: str, cfg: dict) -> list[dict]:
    pdf = HERE / "source_files" / cfg["file"]
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if digest != cfg["sha256"]:
        raise SystemExit(f"{pdf.name}: sha256 {digest} does not match corpus/SOURCES.md")
    text = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), "-"], capture_output=True,
                          encoding="utf-8", errors="replace", check=True).stdout
    lines = [l.strip() for l in text.replace("\f", "\n").split("\n")]
    # A heading number alone on its line ("62.") belongs to the next line.
    lines = [l + " " + lines[i + 1] if re.fullmatch(r"\[?\d{1,3}[A-Z]{0,3}\.", l) and i + 1 < len(lines) else l
             for i, l in enumerate(lines) if not (i and re.fullmatch(r"\[?\d{1,3}[A-Z]{0,3}\.", lines[i - 1]))]
    start = next(i for i, l in enumerate(lines) if l.strip().startswith(cfg["start"]))
    sections, last = [], (0, "")
    for line in lines[start:]:
        s = line.strip()
        if cfg["end"] and re.match(cfg["end"], s):
            break
        if not s or JUNK.match(s) or FOOTNOTE.match(s) or NOTE.match(s):
            continue
        m = HEADING.match(s)
        if m and (key(m.group(1), m.group(2)) > last) and int(m.group(1)) <= last[0] + 6:
            last = key(m.group(1), m.group(2))
            sections.append({"num": m.group(1) + m.group(2), "lines": [s.lstrip("[ ")]})
        elif sections:
            sections[-1]["lines"].append(s)

    units = []
    for sec in sections:
        body = re.sub(r"\s+", " ", " ".join(sec["lines"])).strip()
        heading = re.split(r"\.?\s?(?:——|––|—|–|\.-|\.–)", body[len(sec["num"]) + 1:], maxsplit=1)[0].strip(" .[")
        ref = f"{name} {cfg['unit']}.{sec['num']}"
        base = {"source": name, "version_date": cfg["version_date"], "source_sha256": cfg["sha256"]}
        units.append({"ref": ref, "kind": "section", "heading": heading, "text": body, "parent_ref": None, **base})
        # Sub-sections: "(1)", "(2)", "(2A)" ... in order; the first may follow the heading's dash.
        marks, expect = [], 1
        for m in SUBSECTION.finditer(body):
            n = int(re.match(r"\d+", m.group(1)).group())
            if n == expect or (marks and n == expect - 1 and m.group(1)[-1].isalpha()):
                marks.append((m.start(), m.group(1)))
                expect = n + 1 if not m.group(1)[-1].isalpha() else expect
        for i, (pos, label) in enumerate(marks):
            end = marks[i + 1][0] if i + 1 < len(marks) else len(body)
            units.append({"ref": f"{ref}({label})", "kind": "subsection", "heading": heading,
                          "text": body[pos:end].strip(" [;"), "parent_ref": ref, **base})
    return units


def main():
    units = []
    for name, cfg in SOURCES.items():
        u = section_units(name, cfg)
        print(f"{name}: {sum(x['kind'] == 'section' for x in u)} sections, {sum(x['kind'] == 'subsection' for x in u)} sub-sections")
        units += u
    out = HERE / "units.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for u in units:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")
    print(f"wrote {len(units)} units to {out}")


if __name__ == "__main__":
    main()
