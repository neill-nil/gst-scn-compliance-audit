"""Read-only helpers over a checker input record (schema 0.1 facts, flattened as in data/gold/records.jsonl)."""


def fact(record: dict, path: str):
    """(value, quote, ref) of a {value, quote, para} fact at a dotted path like "notices.0.hearing_date"."""
    node = record
    for part in path.split("."):
        if isinstance(node, list):
            node = node[int(part)] if part.isdigit() and int(part) < len(node) else None
        elif isinstance(node, dict):
            node = node.get(part)
        if node is None:
            return None, None, path
    if isinstance(node, dict) and "value" in node:
        return node["value"], node.get("quote"), path
    return node, None, path


def has(record: dict, path: str) -> bool:
    return fact(record, path)[0] not in (None, [])


def events(record: dict, *types: str) -> list[dict]:
    return [e for e in record.get("events") or [] if not types or e.get("type") in types]


def contents(record: dict, *types: str) -> list[dict]:
    return [c for c in record.get("document_contents") or [] if not types or c.get("type") in types]


def all_quotes(record: dict) -> list[str]:
    """Every verbatim quote in the record; the verifier accepts evidence only if it is one of these (or inside one)."""
    out = []

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("quote"), str) and o["quote"]:
                out.append(o["quote"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk({k: v for k, v in record.items() if k not in ("cnr", "court", "case_no", "decision_date")})
    return out


def compact(record: dict) -> str:
    """A short, readable view of the facts for prompts: one line per known fact, with its quote."""
    lines = []

    def line(label, path):
        v, q, _ = fact(record, path)
        if v not in (None, []):
            lines.append(f"- {label}: {v}" + (f'  [record: "{q}"]' if q else ""))

    line("provision", "provision")
    line("financial years", "financial_years")
    for i, _ in enumerate(record.get("notices") or []):
        for name in ("date", "reply_due", "hearing_date_given", "hearing_date", "service_mode", "signed", "summary_only"):
            line(f"notice {i + 1} {name.replace('_', ' ')}", f"notices.{i}.{name}")
    for name in ("date", "signed", "service_mode"):
        line(f"order {name.replace('_', ' ')}", f"order.{name}")
    for e in events(record):
        lines.append(f"- event {e.get('type')} on {e.get('date') or 'date not stated'}"
                     + (f'  [record: "{e["quote"]}"]' if e.get("quote") else ""))
    for c in contents(record):
        lines.append(f"- {c['type'].replace('_', ' ')}  [record: \"{c['quote']}\"]")
    return "\n".join(lines) or "- (no facts stated)"
