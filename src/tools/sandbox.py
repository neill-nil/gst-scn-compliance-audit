"""record_lookup (reads the checker input) and send_reply (the only state-changing tool, sandboxed).

send_reply refuses unless approved is true, writes only to runs/sandbox_outbox/, and logs every call,
including refused ones, to runs/sandbox_outbox/log.jsonl (used for the unsafe-action rate).
"""
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTBOX = ROOT / "runs" / "sandbox_outbox"


def record_lookup(record: dict, field: str) -> dict:
    """field is a dotted path into the record, e.g. "notices.0.hearing_date" or "events"."""
    node = record
    for part in str(field).split("."):
        if isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        elif isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return {"ok": False, "error": f"no field {field!r} in the record"}
    return {"ok": True, "result": node}


def send_reply(cnr: str, text: str, approved: bool = False) -> dict:
    OUTBOX.mkdir(parents=True, exist_ok=True)
    entry = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "cnr": cnr, "approved": approved is True,
             "executed": approved is True, "chars": len(text or "")}
    with open(OUTBOX / "log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    if approved is not True:
        return {"ok": False, "error": "send_reply needs explicit human approval (approved=true); nothing was sent"}
    (OUTBOX / f"{cnr}_{int(time.time())}.txt").write_text(text, encoding="utf-8")
    return {"ok": True, "result": {"written_to": "runs/sandbox_outbox/"}}
