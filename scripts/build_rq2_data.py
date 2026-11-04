"""RQ2 data: teach Qwen3-8B (QLoRA) to read a judgment and fill the proceeding record (schema 0.1 facts).

- train / val: Gemini pre-fill drafts (silver labels) of reasoned cases in data/splits/reserved.txt only, so
  no test, held-out, dev or queued case is ever trained on.
- test: the human-verified facts of the gold test and held-out cases (data/gold/records.jsonl).
Every example has the same instruction and the judgment text cut at MAX_CHARS (facts sit in the opening
paragraphs; ~75% of judgments fit whole). The same examples serve the untuned 8B (B3) and the frontier
model, so all three systems see identical inputs.

Usage: python -m scripts.build_rq2_data   ->  data/interim/rq2/{train,val,test}.jsonl  (needs data/raw PDFs)
"""
import json
import random
from pathlib import Path

from src.prefill.prefill import COMMON, FACTS_TASK, judgment_text

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "rq2"
MAX_CHARS = 12000
VAL_SHARE = 0.1
SEED = 2


def prompt(cnr: str) -> tuple[str, bool]:
    text = judgment_text(cnr)
    cut = len(text) > MAX_CHARS
    return f"{COMMON}\n{FACTS_TASK}\nJUDGMENT:\n{text[:MAX_CHARS]}", cut


def facts_of(record: dict) -> dict:
    keys = ("provision", "financial_years", "notices", "order", "events", "document_contents")
    return {k: record[k] for k in keys}


def example(cnr, split, target, source):
    p, cut = prompt(cnr)
    return {"cnr": cnr, "split": split, "source": source, "truncated": cut,
            "messages": [{"role": "user", "content": p},
                         {"role": "assistant", "content": json.dumps(target, ensure_ascii=False)}]}


def main():
    ids = lambda n: [l.strip() for l in (ROOT / "data/splits" / n).read_text().splitlines() if l.strip()]
    train_pool = []
    for c in ids("reserved.txt"):
        p = ROOT / "data/prefill/v1" / f"{c}.json"
        if p.exists() and json.loads(p.read_text(encoding="utf-8")).get("facts"):
            train_pool.append(c)
    rng = random.Random(SEED)
    rng.shuffle(train_pool)
    n_val = max(1, int(len(train_pool) * VAL_SHARE))
    OUT.mkdir(parents=True, exist_ok=True)
    counts = {}
    for split, cnrs in (("val", train_pool[:n_val]), ("train", train_pool[n_val:])):
        rows = [example(c, split, json.loads((ROOT / "data/prefill/v1" / f"{c}.json").read_text(encoding="utf-8"))["facts"],
                        "silver_gemini_draft") for c in cnrs]
        counts[split] = (len(rows), sum(r["truncated"] for r in rows))
        with open(OUT / f"{split}.jsonl", "w", encoding="utf-8") as f:
            f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    with open(ROOT / "data/gold/records.jsonl", encoding="utf-8") as f:
        gold = [json.loads(l) for l in f]
    rows = [example(g["cnr"], "test", facts_of(g), "gold_" + g["annotation"].get("set", "test")) for g in gold]
    counts["test"] = (len(rows), sum(r["truncated"] for r in rows))
    with open(OUT / "test.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    for k, (n, cut) in counts.items():
        print(f"{k}: {n} examples ({cut} truncated at {MAX_CHARS} chars)")
    leak = {r for r in train_pool} & {g["cnr"] for g in gold}
    assert not leak, f"test cases in training data: {leak}"


if __name__ == "__main__":
    main()
