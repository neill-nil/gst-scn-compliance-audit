"""The tools of contracts.md section 4. Every call goes through call_tool, which validates the arguments
against the spec and never raises: it returns {"ok": true, "result": ...} or {"ok": false, "error": ...}.

    from src.tools import call_tool, SPECS
    call_tool("statute_lookup", {"ref": "CGST Act s.75(4)"})
"""
import json
from pathlib import Path

import jsonschema

from src.tools.caselaw import caselaw_search
from src.tools.limitation import date_diff, limitation_check
from src.tools.sandbox import record_lookup, send_reply
from src.tools.statute import statute_lookup, statute_search

SPECS = json.loads((Path(__file__).with_name("specs.json")).read_text(encoding="utf-8"))
FUNCTIONS = {"statute_lookup": statute_lookup, "statute_search": statute_search, "limitation_check": limitation_check,
             "date_diff": date_diff, "caselaw_search": caselaw_search, "record_lookup": record_lookup,
             "send_reply": send_reply}


def call_tool(name: str, args: dict, record: dict | None = None) -> dict:
    """Run one tool. `record` is the case being checked (record_lookup reads it; the model never passes it)."""
    spec = next((s for s in SPECS if s["name"] == name), None)
    if spec is None:
        return {"ok": False, "error": f"unknown tool {name!r}; tools are {', '.join(FUNCTIONS)}"}
    try:
        jsonschema.validate(args, spec["parameters"])
    except jsonschema.ValidationError as e:
        return {"ok": False, "error": f"invalid arguments for {name}: {e.message}"}
    try:
        if name == "record_lookup":
            return record_lookup(record or {}, **args)
        return FUNCTIONS[name](**args)
    except Exception as e:  # a tool bug must not crash the agent; it is reported like any tool error
        return {"ok": False, "error": f"{name} failed: {type(e).__name__}: {e}"}
