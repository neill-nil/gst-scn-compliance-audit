"""RQ2: run an extractor (Qwen3-8B untuned, or Qwen3-8B + our LoRA adapter) over the RQ2 test set.

Every system sees the same prompt (data/interim/rq2/test.jsonl: instructions, output format, judgment text cut
at 12k characters). Greedy decoding, thinking off. Score with eval/score_extraction.py.

Usage (Kaggle; one process per GPU, each takes every second case):
    CUDA_VISIBLE_DEVICES=0 python -m src.rq2.extract --run-id rq2_base --shard 0 --shards 2
    CUDA_VISIBLE_DEVICES=1 python -m src.rq2.extract --run-id rq2_base --shard 1 --shards 2
    ... --run-id rq2_tuned --adapter runs/rq2_lora/adapter
Writes runs/<run_id>/outputs_<shard>.jsonl (one line per case; finished cases are skipped on a restart).
"""
import argparse
import json
import time
from pathlib import Path

from src.common.llm import _extract_json
from src.rq2.train import BASE_MODEL, DATA, ROOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--adapter", default=None, help="LoRA adapter folder; omit for the untuned model")
    ap.add_argument("--split", default="test")
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--max-new-tokens", type=int, default=2048)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    from unsloth import FastLanguageModel

    rows = [json.loads(l) for l in open(DATA / f"{args.split}.jsonl", encoding="utf-8")]
    rows = [r for i, r in enumerate(rows) if i % args.shards == args.shard][: args.limit]
    out_dir = ROOT / "runs" / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"outputs_{args.shard}.jsonl"
    done = {json.loads(l)["cnr"] for l in open(out_path, encoding="utf-8")} if out_path.exists() else set()

    model, tok = FastLanguageModel.from_pretrained(args.adapter or BASE_MODEL, max_seq_length=8192 + args.max_new_tokens,
                                                   load_in_4bit=True, dtype=None)
    FastLanguageModel.for_inference(model)
    todo = [r for r in rows if r["cnr"] not in done]
    print(f"{args.run_id} shard {args.shard}: {len(todo)} cases to run ({len(done)} done)", flush=True)
    with open(out_path, "a", encoding="utf-8") as f:
        for n, r in enumerate(todo, 1):
            t0 = time.time()
            prompt = tok.apply_chat_template([r["messages"][0]], tokenize=False, add_generation_prompt=True,
                                             enable_thinking=False)
            ids = tok(prompt, return_tensors="pt", add_special_tokens=False).to("cuda")
            gen = model.generate(**ids, max_new_tokens=args.max_new_tokens, do_sample=False, use_cache=True)
            new = gen[0][ids["input_ids"].shape[1]:]
            text = tok.decode(new, skip_special_tokens=True)
            try:
                facts, error = _extract_json(text), None
            except Exception as e:  # unparseable output is scored as an empty record
                facts, error = None, f"{type(e).__name__}: {str(e)[:200]}"
            rec = {"cnr": r["cnr"], "system": args.run_id, "facts": facts, "error": error, "text": text,
                   "tokens_in": int(ids["input_ids"].shape[1]), "tokens_out": int(len(new)),
                   "hit_max_tokens": int(len(new)) >= args.max_new_tokens, "seconds": round(time.time() - t0, 1)}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            print(f"[{n}/{len(todo)}] {r['cnr']} json={'ok' if facts is not None else 'FAIL'} "
                  f"tokens_out={rec['tokens_out']} {rec['seconds']}s", flush=True)


if __name__ == "__main__":
    main()
