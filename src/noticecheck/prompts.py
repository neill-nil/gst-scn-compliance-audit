"""Prompts and output schemas for the two model steps: planning (tool calls) and the model-judged checks."""
import json

from src.noticecheck.cards import MODEL_CARDS

PLAN_TOOLS = ("limitation_check", "statute_lookup", "statute_search", "caselaw_search", "date_diff")

PLAN = """You plan the checks for a GST demand proceeding (CGST Act s.73 or s.74). You do not decide any defect.
Choose the tool calls whose results the checks need, and list facts that are needed but not in the record.

Facts of the proceeding (as of {as_of}):
{facts}

Tools:
{tools}

Guidance:
- If the provision and the financial years are known, call limitation_check once per financial year, passing
  the notice date as scn_date and the order date as order_date when the record gives them.
- Call statute_lookup for the provisions the checks rely on (for example s.75(4) hearing, s.75(6) reasons,
  s.75(7) demand beyond the notice, s.169 service, s.73(10) or s.74(10) time limits).
- If the notice covers several financial years, or the order relies on the s.168A extension notifications, call
  caselaw_search for how High Courts treat that point.
- At most {max_calls} calls. Use only values from the record; never invent dates.
"""

PLAN_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["tool_calls", "missing_facts"],
    "properties": {
        "tool_calls": {"type": "array", "maxItems": 10, "items": {
            "type": "object", "additionalProperties": False, "required": ["tool", "args"],
            "properties": {"tool": {"enum": list(PLAN_TOOLS)}, "args": {"type": "object"},
                           "purpose": {"type": "string"}}}},
        "missing_facts": {"type": "array", "items": {"type": "string"}}},
}

FIX_CALLS = """These tool calls failed:
{errors}
Reply with corrected tool calls (same format), or an empty list if a call cannot be fixed from the record."""

CHECK = """You check one GST demand proceeding for specific procedural defects. Use only the facts below and the
statute text given; nothing else is known about the case.

Facts of the proceeding (as of {as_of}):
{facts}
{statute}
For each check below answer:
- "defect" only if the record itself shows the defect; copy the supporting record quote(s) exactly into "evidence";
- "no_defect" if the record shows the step was done properly (with the quote);
- "cant_tell" if the record does not say enough; list what is missing in "missing_facts".
Do not guess. A quote must be copied word for word from a [record: "..."] entry above.

Checks:
{checks}
"""


def check_schema(types: list[str]) -> dict:
    return {
        "type": "object", "additionalProperties": False, "required": ["findings"],
        "properties": {"findings": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["type", "verdict", "evidence", "missing_facts", "confidence"],
            "properties": {"type": {"enum": types}, "verdict": {"enum": ["defect", "no_defect", "cant_tell"]},
                           "evidence": {"type": "array", "maxItems": 3, "items": {"type": "string"}},
                           "missing_facts": {"type": "array", "maxItems": 4, "items": {"type": "string"}},
                           "confidence": {"type": "number", "minimum": 0, "maximum": 1}}}}},
    }


def check_list(types: list[str], extra: dict | None = None) -> str:
    cards = {**MODEL_CARDS, **(extra or {})}
    return "\n".join(f"- {t}: {cards[t]['question']}" for t in types)


def tool_specs(specs: list[dict]) -> str:
    return "\n".join(f"- {s['name']}({json.dumps(s['parameters']['properties'])}): {s['description']}"
                     for s in specs if s["name"] in PLAN_TOOLS)
