"""caselaw_search: paragraph-level BM25 over the precedent split only (data/splits/precedent.txt).

The index is built from the local judgment texts (data/text/, from scripts/fetch_data.py), cleaned and split
with scripts/clean_segment.py, and cached in data/interim/caselaw_paragraphs.jsonl.gz. A case in the dev,
test, held-out or reserved split can never be returned: it is kept out of the index and filtered again at
query time.
"""
import csv
import gzip
import importlib.util
import json
from functools import lru_cache
from pathlib import Path

from src.tools.bm25 import BM25

ROOT = Path(__file__).resolve().parents[2]
SPLITS = ROOT / "data" / "splits"
CACHE = ROOT / "data" / "interim" / "caselaw_paragraphs.jsonl.gz"
BLOCKED_SPLITS = ("dev.txt", "test.txt", "heldout.txt", "reserved.txt", "fresh.txt")


def _ids(name: str) -> set[str]:
    path = SPLITS / name
    return {l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()} if path.exists() else set()


@lru_cache(maxsize=1)
def blocked() -> frozenset[str]:
    queued = set()
    for name in ("review_queue.csv", "review_queue_v2.csv", "review_queue_v3.csv"):  # cases being reviewed for dev, test or held-out
        path = SPLITS / name
        if path.exists():
            with open(path, newline="", encoding="utf-8") as f:
                queued |= {r["cnr"] for r in csv.DictReader(f)}
    return frozenset(queued).union(*(_ids(n) for n in BLOCKED_SPLITS))


def build_cache() -> int:
    spec = importlib.util.spec_from_file_location("clean_segment", ROOT / "scripts" / "clean_segment.py")
    cs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cs)
    with open(ROOT / "data" / "manifests" / "screened.csv", newline="", encoding="utf-8") as f:
        meta = {r["cnr"]: r for r in csv.DictReader(f)}
    allowed = _ids("precedent.txt") - blocked()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with gzip.open(CACHE, "wt", encoding="utf-8") as out:
        for cnr in sorted(allowed):
            m = meta[cnr]
            path = ROOT / "data" / "text" / m["court"] / f"{cnr}.txt.gz"
            if not path.exists():
                continue
            pages = gzip.open(path, "rt", encoding="utf-8", errors="replace").read().split("\f")
            kept, _ = cs.clean(pages)
            for p in cs.segment(kept):
                if p["n"] == 0 or len(p["text"]) < 80:
                    continue
                out.write(json.dumps({"cnr": cnr, "court": m["court_name"], "decision_date": m["decision_date"],
                                      "para": p["n"], "text": p["text"][:2500]}, ensure_ascii=False) + "\n")
                n += 1
    return n


@lru_cache(maxsize=1)
def _index():
    if not CACHE.exists():
        build_cache()
    with gzip.open(CACHE, "rt", encoding="utf-8") as f:
        paras = [json.loads(l) for l in f]
    paras = [p for p in paras if p["cnr"] not in blocked()]
    return paras, BM25([p["text"] for p in paras])


def caselaw_search(query: str, k: int = 5) -> dict:
    if not query or not query.strip():
        return {"ok": False, "error": "empty query"}
    if not isinstance(k, int) or not 1 <= k <= 20:
        return {"ok": False, "error": "k must be an integer from 1 to 20"}
    paras, index = _index()
    hits = []
    for i, score in index.search(query, k * 3):
        p = paras[i]
        if p["cnr"] in blocked():  # belt and braces: never return a protected case
            continue
        hits.append({**p, "text": p["text"][:1200], "score": round(score, 3)})
        if len(hits) == k:
            break
    return {"ok": True, "result": hits}


if __name__ == "__main__":
    print(f"wrote {build_cache()} paragraphs to {CACHE}")
