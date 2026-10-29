"""B1: the same Qwen3-8B as NoticeCheck, given only the full_record input and the defect list,
asked for findings in the shared format -- no tools, no retrieval. Same decoding settings and
seeds as NoticeCheck (role 2), so the comparison isolates "agent scaffolding + tools" as the
variable. Per role4_schema_eval.md Wed step 11.

Depends on role 1's src/llm.py (not yet delivered) for the actual model call. This file is wired
to call it by name so it runs the moment that lands; until then --dry-run lets you exercise the
prompt/parsing path without a model.

Usage:
    python -m src.baselines.b1_plain --input data/interim/inputs/full_record.jsonl --out runs/b1/outputs.jsonl \\
        --model qwen3-8b --seed 1
"""
import argparse
import json
import time
from pathlib import Path

from src.baselines.common import build_prompt, parse_model_findings, wrap_output

SYSTEM_NAME = "b1_plain"


def dry_run_llm_call(prompt: str, model: str, seed: int) -> tuple[str, dict]:
    """Stand-in for src.llm.generate until role 1 delivers it. Returns an empty findings array
    (every type cant_tell would be a more honest default, but an empty list is simplest and
    parse_model_findings already treats a missing type as "not predicted")."""
    return "[]", {"tokens_in": 0, "tokens_out": 0}


def run_b1(input_path: Path, run_id: str, model: str, seed: int, llm_call) -> list[dict]:
    outputs = []
    with input_path.open() as f:
        for line in f:
            if not line.strip():
                continue
            checker_input = json.loads(line)
            prompt = build_prompt(checker_input)
            t0 = time.monotonic()
            raw_text, usage = llm_call(prompt, model, seed)
            seconds = time.monotonic() - t0
            findings = parse_model_findings(raw_text)
            outputs.append(wrap_output(
                checker_input["cnr"], SYSTEM_NAME, checker_input["view"], run_id, findings,
                {"calls": 1, "tokens_in": usage.get("tokens_in", 0),
                 "tokens_out": usage.get("tokens_out", 0), "seconds": seconds},
            ))
    return outputs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--run-id", default="b1_plain_v1")
    ap.add_argument("--model", default="qwen3-8b")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true", help="skip the real model call (src.llm not ready yet)")
    args = ap.parse_args()

    if args.dry_run:
        llm_call = dry_run_llm_call
    else:
        try:
            from src.llm import generate as llm_call  # role 1
        except ImportError:
            raise SystemExit("src.llm.generate not found yet (role 1 deliverable) -- pass --dry-run to test the prompt/parsing path without it")

    outputs = run_b1(args.input, args.run_id, args.model, args.seed, llm_call)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as f:
        for o in outputs:
            f.write(json.dumps(o) + "\n")
    print(f"wrote {len(outputs)} outputs to {args.out}")


if __name__ == "__main__":
    main()
