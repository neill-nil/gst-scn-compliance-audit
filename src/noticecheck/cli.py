"""Run NoticeCheck over checker inputs and write outputs in the shared format (contracts.md sections 3 and 5).

Usage:
    python -m src.noticecheck.cli --inputs data/interim/inputs/full_record.jsonl --config configs/nc_full.json \
        --run-id nc_full_seed1 [--seed 1] [--limit 5] [--cnr CNR ...]
Writes runs/<run_id>/outputs.jsonl, runs/<run_id>/traces/<cnr>.jsonl and runs/<run_id>/experiment.json.
Cases already in outputs.jsonl are skipped, so a stopped run continues where it left off.
"""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

from src.noticecheck.pipeline import run_case

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = "noticecheck_v1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--seed", type=int, default=None, help="overrides the config's seed")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--cnr", nargs="*", default=None)
    args = ap.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    if args.seed is not None:
        cfg["seed"] = args.seed
    run_dir = ROOT / "runs" / args.run_id
    (run_dir / "traces").mkdir(parents=True, exist_ok=True)
    out_path = run_dir / "outputs.jsonl"
    done = {json.loads(l)["cnr"] for l in out_path.open(encoding="utf-8")} if out_path.exists() else set()
    inputs = [json.loads(l) for l in args.inputs.open(encoding="utf-8") if l.strip()]
    if args.cnr:
        inputs = [i for i in inputs if i["cnr"] in set(args.cnr)]
    todo = [i for i in inputs if i["cnr"] not in done][: args.limit]

    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    (run_dir / "experiment.json").write_text(json.dumps({
        "system": SYSTEM, "run_id": args.run_id, "config": cfg, "commit": commit,
        "inputs": str(args.inputs), "inputs_sha256": sha256(args.inputs),
        "corpus_sha256": sha256(ROOT / "corpus" / "units.jsonl"), "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }, indent=1), encoding="utf-8")

    print(f"{len(todo)} cases to run ({len(done)} already done) -> {run_dir}")
    for n, inp in enumerate(todo, 1):
        t0 = time.time()
        try:
            out, trace = run_case(inp, cfg)
        except RuntimeError as e:  # model server down or quota exhausted: stop, the run resumes later
            print(f"STOPPED at {inp['cnr']}: {e}")
            break
        out.update(system=SYSTEM, run_id=args.run_id, trace_file=f"runs/{args.run_id}/traces/{inp['cnr']}.jsonl")
        with open(run_dir / "traces" / f"{inp['cnr']}.jsonl", "w", encoding="utf-8") as f:
            for step in trace:
                f.write(json.dumps(step, ensure_ascii=False) + "\n")
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
        verdicts = {}
        for fnd in out["findings"]:
            verdicts[fnd["verdict"]] = verdicts.get(fnd["verdict"], 0) + 1
        print(f"[{n}/{len(todo)}] {inp['cnr']} {verdicts} calls={out['usage']['calls']} {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
