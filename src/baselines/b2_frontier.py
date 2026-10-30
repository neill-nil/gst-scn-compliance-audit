"""B2: a frontier API model, given the full_record input, the defect list, AND the full text of
the relevant CGST/SGST provisions pasted directly into the prompt (from role 3's statute corpus,
contracts.md section 4's `statute_lookup`) -- no tool calls, no retrieval, just the text in
context. Budget: test set x 1 run. Per role4_schema_eval.md Wed step 12.

Depends on:
  - a frontier-model call, e.g. src.llm.generate_frontier (role 1) or an Anthropic/OpenAI SDK
    call directly -- wire whichever is actually used once decided.
  - role 3's statute corpus, to look up provision text per defect type. Until that exists, pass
    --provisions a JSON file of {"CGST Act s.75(4)": "...text...", ...}; omitted provisions are
    simply left out of the prompt (graceful, not a crash).

Usage:
    python -m src.baselines.b2_frontier --input data/interim/inputs/full_record.jsonl --out runs/b2/outputs.jsonl \\
        --provisions data/corpus/provisions_for_b2.json
"""
import argparse
import json
import time
from pathlib import Path

from src.baselines.common import build_prompt, parse_model_findings, wrap_output

SYSTEM_NAME = "b2_frontier"


def dry_run_llm_call(prompt: str, model: str) -> tuple[str, dict]:
    """Stand-in until a real frontier-model call is wired up."""
    return "[]", {"tokens_in": 0, "tokens_out": 0}


def run_b2(input_path: Path, run_id: str, model: str, provisions_text: dict[str, str] | None, llm_call) -> list[dict]:
    outputs = []
    with input_path.open() as f:
        for line in f:
            if not line.strip():
                continue
            checker_input = json.loads(line)
            prompt = build_prompt(checker_input, provisions_text=provisions_text)
            t0 = time.monotonic()
            raw_text, usage = llm_call(prompt, model)
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
    ap.add_argument("--run-id", default="b2_frontier_v1")
    ap.add_argument("--model", default="frontier-tbd")
    ap.add_argument("--provisions", type=Path, default=None, help="JSON {provision_ref: text} from role 3's corpus")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    provisions_text = json.loads(args.provisions.read_text()) if args.provisions else None

    if args.dry_run:
        llm_call = dry_run_llm_call
    else:
        try:
            from src.llm import generate_frontier as llm_call  # role 1
        except ImportError:
            raise SystemExit("src.llm.generate_frontier not found yet (role 1 deliverable) -- pass --dry-run to test the prompt/parsing path without it")

    outputs = run_b2(args.input, args.run_id, args.model, provisions_text, llm_call)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as f:
        for o in outputs:
            f.write(json.dumps(o) + "\n")
    print(f"wrote {len(outputs)} outputs to {args.out}")


if __name__ == "__main__":
    main()
