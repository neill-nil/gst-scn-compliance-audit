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


# A short description of the output format. The full JSON schema is ~3k tokens, too long to repeat in every
# training example; this lists the same keys and allowed values, so the untuned model knows the format too.
OUTPUT_FORMAT = """Reply with one JSON object and nothing else, with exactly these keys:
{"provision": F, "financial_years": F, "notices": [NOTICE, ...], "order": ORDER, "events": [EVENT, ...],
 "document_contents": [DOC, ...]}
F (a fact) = {"value": ..., "quote": "exact words from the judgment" or null, "para": paragraph number or null};
  if the judgment does not state the value, all three are null.
provision.value: "73", "74" or null. financial_years.value: list like ["2018-19"] or null.
NOTICE = {"date": F, "reply_due": F, "hearing_date_given": F, "hearing_date": F, "service_mode": F,
  "signed": F, "summary_only": F}; dates are "YYYY-MM-DD"; hearing_date_given, signed, summary_only are
  true/false; service_mode is one of portal_additional_notices_tab, portal_notices_tab, portal_unspecified,
  email, registered_post, hand_delivery, not_served.
ORDER = {"date": F, "signed": F, "service_mode": F}.
EVENT = {"date": "YYYY-MM-DD" or null, "type": T, "quote": "...", "para": n}; T is one of scrutiny_notice,
  pre_scn_intimation, scn_issued, reply_filed, reply_not_filed, extension_requested, extension_granted,
  hearing_requested, hearing_scheduled, hearing_adjourned, adjournment_requested, hearing_attended,
  hearing_missed, order_passed, rectification_rejected, appeal_dismissed, recovery_or_attachment,
  earlier_writ, other.
DOC = {"type": "scn_ground" | "fraud_allegation" | "reply_point" | "order_reasoning", "quote": "...", "para": n}.
"""


def prompt(cnr: str) -> tuple[str, bool]:
    text = judgment_text(cnr)
    cut = len(text) > MAX_CHARS
    return f"{COMMON}\n{FACTS_TASK}\n{OUTPUT_FORMAT}\nJUDGMENT:\n{text[:MAX_CHARS]}", cut


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
