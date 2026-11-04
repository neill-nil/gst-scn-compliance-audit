"""The provision behind each defect type: one table shared by NoticeCheck (what it cites) and the strict score
(what the gold label is matched against, contracts.md section 3). Decision D3; role 3 checks it against the Act."""
import re

PROVISION = {
    "hearing_75_4": "CGST Act s.75(4)", "adjournment_75_5": "CGST Act s.75(5)",
    "reply_not_considered": "CGST Act s.75(6)", "non_speaking_order": "CGST Act s.75(6)",
    "demand_beyond_scn": "CGST Act s.75(7)", "service_169": "CGST Act s.169(1)",
    "signature": "CGST Rules r.26(3)", "summary_only": "CGST Rules r.142(1)",
    "limitation": None,  # s.73(10) or s.74(10), from the record's provision
    "extension_notification_validity": "CGST Act s.168A", "consolidated_scn": None,  # s.73(1) or s.74(1)
    "section_74_ingredients": "CGST Act s.74(1)", "other_procedural": None,  # no single provision
}


def provision_for(defect: str, record: dict) -> str | None:
    if defect in ("limitation", "consolidated_scn"):
        p = record.get("provision")
        p = p.get("value") if isinstance(p, dict) else p
        return f"CGST Act s.{p}({'10' if defect == 'limitation' else '1'})" if p in ("73", "74") else None
    return PROVISION[defect]


def provisions_match(predicted: str | None, gold: str | None) -> bool:
    """Same section (or rule); if both name a sub-section, the sub-sections must agree. No gold provision: any."""
    from src.tools.statute import parse_ref
    if gold is None:
        return True
    a, b = parse_ref(predicted or ""), parse_ref(gold)
    if a is None or b is None:
        return False
    split = lambda ref: re.match(r"(.*?\.\d+[A-Z]*)(\(.*\))?$", ref).groups()
    (sa, ua), (sb, ub) = split(a), split(b)
    return sa == sb and (ua is None or ub is None or ua == ub)
