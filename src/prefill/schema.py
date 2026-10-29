"""Load the case-record schemas and validate records (schema 0.1).

A case record is {"cnr", "schema_version", "facts", "findings", "review"}. `facts` and `findings`
each have a JSON schema in schemas/, so each can be produced by its own model call.

Usage: python -m src.prefill.schema <record.json> [...]   # prints problems, exit 1 if any
"""
import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "0.1"
FACTS_SCHEMA = json.loads((ROOT / "schemas" / "facts.schema.json").read_text(encoding="utf-8"))
FINDINGS_SCHEMA = json.loads((ROOT / "schemas" / "findings.schema.json").read_text(encoding="utf-8"))


def _facts_with_values(facts: dict):
    """Yield (path, fact) for every {"value", "quote", "para"} object in the facts block."""
    for name in ("provision", "financial_years"):
        yield name, facts[name]
    for i, notice in enumerate(facts["notices"]):
        for name, fact in notice.items():
            yield f"notices[{i}].{name}", fact
    for name, fact in facts["order"].items():
        yield f"order.{name}", fact


def rule_problems(record: dict) -> list[str]:
    """Checks the JSON schema can't express."""
    problems = []
    for path, fact in _facts_with_values(record["facts"]):
        has_value = fact["value"] not in (None, [])
        if has_value != (fact["quote"] is not None):
            problems.append(f"facts.{path}: a value needs a quote, and no value means no quote")
    for i, d in enumerate(record["findings"]["defects_argued"]):
        if d["finding"] != "not_decided" and d["quote_source"] != "court":
            problems.append(f"findings.defects_argued[{i}]: found/rejected must quote the court, not an argument")
        if (d["type"] == "other_procedural") != bool(d["note"]):
            problems.append(f"findings.defects_argued[{i}]: note is required for other_procedural and must be null otherwise")
    findings_quotes = [d["quote"] for d in record["findings"]["defects_argued"]]
    for i, c in enumerate(record["facts"]["document_contents"]):
        if any(c["quote"] in q or q in c["quote"] for q in findings_quotes):
            problems.append(f"facts.document_contents[{i}]: same words as a court finding (would leak the answer)")
    return problems


def validate_record(record: dict) -> list[str]:
    problems = []
    if record.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"schema_version should be {SCHEMA_VERSION}")
    for part, schema in (("facts", FACTS_SCHEMA), ("findings", FINDINGS_SCHEMA)):
        for err in jsonschema.Draft202012Validator(schema).iter_errors(record.get(part, {})):
            problems.append(f"{part}.{'.'.join(map(str, err.absolute_path))}: {err.message[:150]}")
    try:
        problems += rule_problems(record)
    except (KeyError, TypeError, AttributeError):
        pass  # structure too broken for rule checks; the schema errors above already say why
    return problems


if __name__ == "__main__":
    bad = 0
    for p in sys.argv[1:]:
        rec = json.loads(Path(p).read_text(encoding="utf-8"))
        probs = validate_record(rec)
        bad += bool(probs)
        print(f"{rec.get('cnr')}: {'OK' if not probs else f'{len(probs)} problem(s)'}")
        for x in probs:
            print("   ", x)
    sys.exit(1 if bad else 0)
