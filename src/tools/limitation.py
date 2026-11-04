"""limitation_check and date_diff. Dates and their official sources are in corpus/limitation_dates.json.

s.73: order within 3 years of the annual-return due date (s.73(10)); notice at least 3 months before that (s.73(2)).
s.74: 5 years and 6 months (s.74(10), s.74(2)). The s.168A notifications extend the s.73 order limit for
FY 2017-18 to 2019-20; their validity is under challenge, so an answer that depends on them is contested.
"""
import calendar
import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FY = re.compile(r"^(\d{4})-(\d{2})$")


@lru_cache(maxsize=1)
def table() -> dict:
    return json.loads((ROOT / "corpus" / "limitation_dates.json").read_text(encoding="utf-8"))


def _date(s: str, name: str) -> date:
    try:
        return date.fromisoformat(s)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a date as YYYY-MM-DD, got {s!r}") from None


def _add_months(d: date, months: int) -> date:
    y, m = divmod(d.month - 1 + months, 12)
    y, m = d.year + y, m + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def date_diff(start: str, end: str) -> dict:
    try:
        return {"ok": True, "result": {"days": (_date(end, "end") - _date(start, "start")).days}}
    except ValueError as e:
        return {"ok": False, "error": str(e)}


def limitation_check(provision: str, financial_year: str, scn_date: str | None = None,
                     order_date: str | None = None, apply_extensions: bool = True) -> dict:
    try:
        provision = str(provision).strip()
        if provision not in ("73", "74"):
            raise ValueError(f"provision must be \"73\" or \"74\", got {provision!r}")
        m = FY.match(str(financial_year).strip())
        if not m or int(m.group(2)) != (int(m.group(1)) + 1) % 100:
            raise ValueError(f"financial_year must look like \"2020-21\", got {financial_year!r}")
        due_entry = table()["annual_return_due"].get(financial_year)
        if due_entry is None:
            raise ValueError(f"no annual-return due date for {financial_year} (covered: "
                             f"{', '.join(table()['annual_return_due'])}); FY 2024-25 onward falls under s.74A")
        scn = _date(scn_date, "scn_date") if scn_date else None
        order = _date(order_date, "order_date") if order_date else None
    except ValueError as e:
        return {"ok": False, "error": str(e)}

    period = table()["periods"][provision]
    due = date.fromisoformat(due_entry["date"])
    base_order_last = _add_months(due, 12 * period["order_years"])
    order_last, used = base_order_last, []
    extensions = table()["section_168A_order_extensions_s73"].get(financial_year, []) if provision == "73" else []
    if apply_extensions and extensions:
        latest = max(extensions, key=lambda e: e["until"])
        order_last = max(order_last, date.fromisoformat(latest["until"]))
        used = [e["notification"] for e in extensions]
    scn_last = _add_months(order_last, -period["scn_months_before_order_limit"])
    base_scn_last = _add_months(base_order_last, -period["scn_months_before_order_limit"])

    scn_in_time = None if scn is None else scn <= scn_last
    order_in_time = None if order is None else order <= order_last
    # Contested when the answer would change without the s.168A notifications.
    contested = bool(used) and ((scn is not None and (scn <= base_scn_last) != scn_in_time) or
                                (order is not None and (order <= base_order_last) != order_in_time))
    notes = [f"annual return due {due} ({due_entry['source']})",
             f"{period['source']}: order within {period['order_years']} years, notice at least "
             f"{period['scn_months_before_order_limit']} months before that"]
    if not due_entry["verified"]:
        notes.append("UNVERIFIED annual-return date: check the official notification before relying on this")
    if used:
        notes.append(f"s.168A extensions applied: {'; '.join(used)}; without them the order limit is {base_order_last}")
    return {"ok": True, "result": {
        "annual_return_due": str(due), "scn_last_date": str(scn_last), "order_last_date": str(order_last),
        "scn_in_time": scn_in_time, "order_in_time": order_in_time, "extension_notifications_used": used,
        "contested": contested, "verified": due_entry["verified"], "notes": "; ".join(notes)}}
