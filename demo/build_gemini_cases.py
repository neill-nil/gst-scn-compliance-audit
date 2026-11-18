"""Record the three prepared judgments through the optional Gemini pipeline.

Run with a configured .env: python -m demo.build_gemini_cases
The generated artifacts contain public judgment text and model output, never keys.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from demo.live import run_live
from demo.server import CASES, ROOT, source

OUTPUT = ROOT / "demo/gemini_runs"


def record_case(cnr: str) -> Path:
    paragraphs = source(cnr)
    if not paragraphs:
        raise FileNotFoundError(f"No prepared judgment text for {cnr}")
    judgment = "\n\n".join(f"¶{p['n']}\n{p['text']}" for p in paragraphs)
    events = []
    result = run_live(judgment, events.append)
    if not events or events[-1].get("type") != "result":
        raise RuntimeError(f"Gemini run for {cnr} ended without a final result")
    extraction = next(e for e in events if e["type"] == "extraction")
    artifact = {
        "cnr": cnr,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": "prepared judgment text",
        "extractor": extraction["model"],
        "checker": extraction["model"],
        "precedent_index": "full_index" if (ROOT / "data/interim/caselaw_paragraphs.jsonl.gz").exists()
                           else "bundled_excerpts",
        "grounding": extraction["grounding"],
        "events": [e for e in events if e["type"] != "input"],
        "result": result,
    }
    OUTPUT.mkdir(exist_ok=True)
    path = OUTPUT / f"{cnr}.json"
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cnr", nargs="*", help="Prepared case IDs; defaults to all three")
    args = parser.parse_args()
    allowed = {cnr for cnr, _, _ in CASES}
    for cnr in args.cnr or sorted(allowed):
        if cnr not in allowed:
            parser.error(f"Not a prepared demo case: {cnr}")
        print(f"Running Gemini for {cnr}…", flush=True)
        print(f"Saved {record_case(cnr)}", flush=True)


if __name__ == "__main__":
    main()
