"""B0: rule-based checklist baseline, no model. Per role4_schema_eval.md Tue step 9 and
docs/team_plan/contracts.md section 3 (checker output format).

Rules (checked in this order; a case can trigger more than one):
  - hearing date missing, "NA", or before reply due  -> hearing_75_4
  - signed == false (on the notice)                  -> signature
  - service_mode == portal_additional_notices_tab     -> service_169
  - limitation_check says out of time                 -> limitation
  - none of the above                                  -> no_defect for every type

Usage:
    python -m src.baselines.b0_rules --input data/interim/inputs/full_record.jsonl --out runs/b0/outputs.jsonl
"""
import argparse
import json
from datetime import date
from pathlib import Path

from eval.score import DEFECT_TYPES

RUN_ID_DEFAULT = "b0_rules_v1"
SYSTEM_NAME = "b0_rules"


def _unwrap(node):
    if isinstance(node, dict) and set(node.keys()) >= {"value", "quote", "para"}:
        return node["value"]
    return node


def _first_notice(record: dict) -> dict:
    notices = record.get("notices") or []
    return notices[0] if notices else {}


def check_hearing_75_4(record: dict) -> dict | None:
    notice = _first_notice(record)
    hearing_given = _unwrap(notice.get("hearing_date_given"))
    hearing_date = _unwrap(notice.get("hearing_date"))
    reply_due = _unwrap(notice.get("reply_due"))

    if hearing_given is None:
        return {"verdict": "cant_tell", "missing_facts": ["notices.0.hearing_date_given"]}
    if hearing_given is False or hearing_date is None:
        return {"verdict": "defect", "evidence_note": "hearing date missing or NA"}
    if reply_due is not None and date.fromisoformat(hearing_date) < date.fromisoformat(reply_due):
        return {"verdict": "defect", "evidence_note": "hearing date before reply due"}
    return {"verdict": "no_defect"}


def check_signature(record: dict) -> dict | None:
    notice = _first_notice(record)
    signed = _unwrap(notice.get("signed"))
    if signed is None:
        return {"verdict": "cant_tell", "missing_facts": ["notices.0.signed"]}
    return {"verdict": "defect" if signed is False else "no_defect"}


def check_service_169(record: dict) -> dict | None:
    notice = _first_notice(record)
    service_mode = _unwrap(notice.get("service_mode"))
    if service_mode is None:
        return {"verdict": "cant_tell", "missing_facts": ["notices.0.service_mode"]}
    return {"verdict": "defect" if service_mode == "portal_additional_notices_tab" else "no_defect"}


def check_limitation(record: dict, limitation_check_fn) -> dict | None:
    """limitation_check_fn: the src/tools/limitation.py function from contracts.md section 4
    (provision, financial_year, scn_date, order_date, apply_extensions) -> result dict with
    scn_in_time/order_in_time. Role 3 delivers this; until it exists, pass a stub so B0 can still
    run end to end (see --no-limitation-tool below)."""
    provision = _unwrap(record.get("provision"))
    financial_years = _unwrap(record.get("financial_years")) or []
    order_date = _unwrap((record.get("order") or {}).get("date"))
    notice_date = _unwrap(_first_notice(record).get("date"))
    if provision is None or not financial_years or order_date is None:
        return {"verdict": "cant_tell", "missing_facts": ["provision", "financial_years", "order.date"]}

    result = limitation_check_fn(
        provision=provision, financial_year=financial_years[0],
        scn_date=notice_date, order_date=order_date, apply_extensions=True,
    )
    if not result.get("ok", True):
        return {"verdict": "cant_tell", "missing_facts": ["limitation_check unavailable"]}
    out_of_time = (result.get("scn_in_time") is False) or (result.get("order_in_time") is False)
    verdict = {"verdict": "defect" if out_of_time else "no_defect"}
    if result.get("contested"):
        verdict["verdict"] = "contested"
    return verdict


def stub_limitation_check(**_kwargs) -> dict:
    """Placeholder until role 3's src/tools/limitation_check lands (contracts.md section 4).
    Always reports "cant tell" rather than guessing, per CLAUDE.md: never guess a label."""
    return {"ok": False}


CHECKS = {
    "hearing_75_4": check_hearing_75_4,
    "signature": check_signature,
    "service_169": check_service_169,
    # "limitation" handled separately below (needs the limitation_check tool)
}


def score_case(record: dict, limitation_check_fn) -> list[dict]:
    findings = []
    for defect_type, check_fn in CHECKS.items():
        result = check_fn(record)
        findings.append({
            "type": defect_type, "verdict": result["verdict"], "provision": None,
            "evidence": [], "missing_facts": result.get("missing_facts", []), "confidence": 1.0,
        })
    limitation_result = check_limitation(record, limitation_check_fn)
    findings.append({
        "type": "limitation", "verdict": limitation_result["verdict"], "provision": None,
        "evidence": [], "missing_facts": limitation_result.get("missing_facts", []), "confidence": 1.0,
    })
    for defect_type in DEFECT_TYPES:
        if defect_type not in CHECKS and defect_type != "limitation":
            findings.append({
                "type": defect_type, "verdict": "no_defect", "provision": None,
                "evidence": [], "missing_facts": [], "confidence": 1.0,
            })
    return findings


def run_b0(input_path: Path, run_id: str, limitation_check_fn) -> list[dict]:
    outputs = []
    with input_path.open() as f:
        for line in f:
            if not line.strip():
                continue
            checker_input = json.loads(line)
            findings = score_case(checker_input["record"], limitation_check_fn)
            outputs.append({
                "cnr": checker_input["cnr"], "system": SYSTEM_NAME, "view": checker_input["view"],
                "run_id": run_id, "findings": findings,
                "handoff": {"escalate": any(f["verdict"] == "defect" for f in findings), "reasons": []},
                "actions": [], "trace_file": None,
                "usage": {"calls": 0, "tokens_in": 0, "tokens_out": 0, "seconds": 0.0},
            })
    return outputs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True, help="a views file from src.baselines.inputs, e.g. full_record.jsonl")
    ap.add_argument("--out", type=Path, required=True, help="runs/<run_id>/outputs.jsonl")
    ap.add_argument("--run-id", default=RUN_ID_DEFAULT)
    args = ap.parse_args()

    try:
        from src.tools.limitation import limitation_check as limitation_check_fn  # role 3
    except ImportError:
        limitation_check_fn = stub_limitation_check

    outputs = run_b0(args.input, args.run_id, limitation_check_fn)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as f:
        for o in outputs:
            f.write(json.dumps(o) + "\n")
    print(f"wrote {len(outputs)} outputs to {args.out}")


if __name__ == "__main__":
    main()
