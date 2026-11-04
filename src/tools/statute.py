"""statute_lookup and statute_search over the frozen corpus (corpus/units.jsonl).

Search is hierarchical by default: sub-section units are ranked, and each hit carries its section's heading
and text so the reader sees the context (proposal: hierarchy preserved). `flat=True` ranks plain fixed-size
chunks without parent context instead, for the retrieval ablation.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

from src.tools.bm25 import BM25

ROOT = Path(__file__).resolve().parents[2]
UNITS = ROOT / "corpus" / "units.jsonl"
REF = re.compile(r"(?P<kind>rule|r\.|r\b|section|sec\.?|s\.|s\b|§)?\s*(?P<num>\d{1,3}[A-Z]{0,3})\s*(?P<sub>\(\s*\d{1,2}[A-Z]?\s*\))?",
                 re.I)


@lru_cache(maxsize=1)
def units() -> dict[str, dict]:
    with open(UNITS, encoding="utf-8") as f:
        return {u["ref"]: u for u in map(json.loads, f)}


def parse_ref(ref: str) -> str | None:
    """'s 75(4)', 'Section 75 (4) of CGST Act', 'rule 142(1A)', 'CGST Rules r.26(3)' -> canonical ref."""
    text = ref.strip()
    is_rule = bool(re.search(r"\brules?\b|\br\.\s*\d", text, re.I))
    body = re.sub(r"CGST\s+(Act|Rules)(,?\s*2017)?|of the|of", " ", text, flags=re.I)
    m = REF.search(body)
    if not m:
        return None
    num = m.group("num").upper()
    sub = re.sub(r"\s+", "", m.group("sub") or "").upper()
    return f"{'CGST Rules r' if is_rule else 'CGST Act s'}.{num}{sub}"


def statute_lookup(ref: str) -> dict:
    canonical = parse_ref(ref)
    if canonical is None:
        return {"ok": False, "error": f"could not read a section or rule number from {ref!r}"}
    u = units().get(canonical)
    if u is None:
        return {"ok": False, "error": f"{canonical} is not in the corpus (check the number; ss.105-106 and "
                                      f"rr.74, 78, 122, 124, 127 are not split out)"}
    parent = units().get(u["parent_ref"]) if u["parent_ref"] else None
    return {"ok": True, "result": {"ref": u["ref"], "text": u["text"], "heading": u["heading"],
                                   "parent_ref": u["parent_ref"], "version_date": u["version_date"],
                                   "parent_heading": parent["heading"] if parent else None}}


@lru_cache(maxsize=2)
def _index(flat: bool):
    if flat:  # plain 120-word chunks over whole sections, no hierarchy
        chunks = []
        for u in units().values():
            if u["kind"] != "section":
                continue
            words = u["text"].split()
            for i in range(0, len(words), 100):
                chunks.append({"ref": u["ref"], "text": " ".join(words[i:i + 120]), "heading": u["heading"]})
        return chunks, BM25([c["text"] for c in chunks])
    leaves = [u for u in units().values()
              if u["kind"] == "subsection" or not any(v["parent_ref"] == u["ref"] for v in units().values())]
    return leaves, BM25([f"{u['heading']} {u['text']}" for u in leaves])


def statute_search(query: str, k: int = 5, flat: bool = False) -> dict:
    if not query or not query.strip():
        return {"ok": False, "error": "empty query"}
    if not isinstance(k, int) or not 1 <= k <= 20:
        return {"ok": False, "error": "k must be an integer from 1 to 20"}
    docs, index = _index(flat)
    hits = []
    for i, score in index.search(query, k):
        d = docs[i]
        parent = units().get(d.get("parent_ref") or "") if not flat else None
        hits.append({"ref": d["ref"], "text": d["text"], "heading": d["heading"],
                     "parent_text": parent["text"][:1500] if parent else None, "score": round(score, 3)})
    return {"ok": True, "result": hits}
