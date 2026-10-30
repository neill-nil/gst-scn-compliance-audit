"""Shared prompt/parsing/output-wrapping for the LLM baselines (b1_plain.py, b2_frontier.py).
Both ask a model for findings in the shared output format (docs/team_plan/contracts.md section 3)
over the full_record view; they differ only in which model answers and whether statute text is
pasted in. Kept here once rather than duplicated in both files.
"""
import json

from eval.score import DEFECT_TYPES

VERDICTS = {"defect", "no_defect", "cant_tell", "contested"}

PROMPT_TEMPLATE = """You are reviewing a GST demand proceeding for procedural defects only.
Facts of the case (as of {as_of_date}; nothing after this date is known to you):
{record_json}

For EACH of the following defect types, decide one verdict: "defect" (the facts show this defect
happened), "no_defect" (the facts show it did not), or "cant_tell" (the facts given don't say).
Defect types: {defect_types}
{provisions_block}
Base your answer only on the facts above, never on outcome or reasoning you are not given (you
have not been given any). Respond with ONLY a JSON array, one object per defect type, each:
{{"type": "<defect type>", "verdict": "defect"|"no_defect"|"cant_tell", "provision": "<CGST Act/Rules ref or null>", "missing_facts": ["<record path>", ...], "confidence": <0-1>}}
"""


def build_prompt(checker_input: dict, provisions_text: dict[str, str] | None = None) -> str:
    provisions_block = ""
    if provisions_text:
        joined = "\n".join(f"{ref}: {text}" for ref, text in provisions_text.items())
        provisions_block = f"\nRelevant statute text:\n{joined}\n"
    return PROMPT_TEMPLATE.format(
        as_of_date=checker_input.get("as_of_date"),
        record_json=json.dumps(checker_input["record"]),
        defect_types=", ".join(DEFECT_TYPES),
        provisions_block=provisions_block,
    )


def parse_model_findings(raw_text: str) -> list[dict]:
    """Parses the model's JSON array; drops (doesn't crash on) any entry with an unknown type or
    verdict, since a baseline must survive malformed model output rather than raising mid-run."""
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        start, end = raw_text.find("["), raw_text.rfind("]")
        if start == -1 or end == -1:
            return []
        try:
            parsed = json.loads(raw_text[start:end + 1])
        except json.JSONDecodeError:
            return []

    findings = []
    for entry in parsed if isinstance(parsed, list) else []:
        if not isinstance(entry, dict):
            continue
        if entry.get("type") not in DEFECT_TYPES or entry.get("verdict") not in VERDICTS:
            continue
        findings.append({
            "type": entry["type"], "verdict": entry["verdict"],
            "provision": entry.get("provision"), "evidence": [],
            "missing_facts": entry.get("missing_facts", []),
            "confidence": entry.get("confidence", 0.5),
        })
    return findings


def wrap_output(cnr: str, system: str, view: str, run_id: str, findings: list[dict], usage: dict) -> dict:
    return {
        "cnr": cnr, "system": system, "view": view, "run_id": run_id, "findings": findings,
        "handoff": {"escalate": any(f["verdict"] == "defect" for f in findings), "reasons": []},
        "actions": [], "trace_file": f"runs/{run_id}/traces/{cnr}.jsonl", "usage": usage,
    }
