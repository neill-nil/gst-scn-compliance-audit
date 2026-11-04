"""Tests for src/tools (python -m pytest tests/test_tools.py). Legal values are checked against the corpus
text and corpus/limitation_dates.json, whose dates were read from the official PDFs."""
import json
from pathlib import Path

import pytest

from src.tools import SPECS, call_tool
from src.tools.caselaw import CACHE, blocked
from src.tools.statute import parse_ref

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("ref,canonical", [
    ("CGST Act s.75(4)", "CGST Act s.75(4)"), ("s 75(4)", "CGST Act s.75(4)"),
    ("Section 75 (4) of CGST Act", "CGST Act s.75(4)"), ("sec.73(10)", "CGST Act s.73(10)"),
    ("CGST Rules r.142(1A)", "CGST Rules r.142(1A)"), ("rule 26(3)", "CGST Rules r.26(3)"),
    ("section 168A", "CGST Act s.168A"), ("Rule 142", "CGST Rules r.142"),
])
def test_parse_ref(ref, canonical):
    assert parse_ref(ref) == canonical


def test_statute_lookup():
    r = call_tool("statute_lookup", {"ref": "s.75(4)"})
    assert r["ok"] and r["result"]["text"].startswith("(4) An opportunity of hearing shall be granted")
    assert r["result"]["parent_ref"] == "CGST Act s.75"
    assert "six months prior" in call_tool("statute_lookup", {"ref": "CGST Act s.74(2)"})["result"]["text"]
    assert "DRC-01A" in call_tool("statute_lookup", {"ref": "CGST Rules r.142(1A)"})["result"]["text"]
    assert call_tool("statute_lookup", {"ref": "s.999"})["ok"] is False
    assert call_tool("statute_lookup", {"ref": "nothing here"})["ok"] is False


def test_statute_search():
    r = call_tool("statute_search", {"query": "opportunity of hearing before adverse decision", "k": 5})
    assert r["ok"] and "CGST Act s.75(4)" in [h["ref"] for h in r["result"]]
    assert all(h["parent_text"] for h in r["result"])
    flat = call_tool("statute_search", {"query": "opportunity of hearing", "k": 3, "flat": True})
    assert flat["ok"] and all(h["parent_text"] is None for h in flat["result"])
    assert call_tool("statute_search", {"query": " "})["ok"] is False


def test_limitation_s73_with_extensions():
    # FY 2018-19: annual return due 31.12.2020 -> 3 years = 31.12.2023; Notification 56/2023 extends to 30.04.2024.
    r = call_tool("limitation_check", {"provision": "73", "financial_year": "2018-19",
                                       "scn_date": "2023-12-01", "order_date": "2024-04-12"})["result"]
    assert r["annual_return_due"] == "2020-12-31" and r["order_last_date"] == "2024-04-30"
    assert r["scn_last_date"] == "2024-01-30" and r["order_in_time"] is True
    assert r["contested"] is True  # without the notifications the order (after 31.12.2023) would be late
    plain = call_tool("limitation_check", {"provision": "73", "financial_year": "2018-19", "order_date": "2024-04-12",
                                           "apply_extensions": False})["result"]
    assert plain["order_last_date"] == "2023-12-31" and plain["order_in_time"] is False


def test_limitation_s74_and_errors():
    r = call_tool("limitation_check", {"provision": "74", "financial_year": "2017-18"})["result"]
    assert r["order_last_date"] == "2025-02-05" and r["scn_last_date"] == "2024-08-05"
    assert r["extension_notifications_used"] == [] and r["contested"] is False
    assert call_tool("limitation_check", {"provision": "74", "financial_year": "2024-25"})["ok"] is False
    assert call_tool("limitation_check", {"provision": "75", "financial_year": "2019-20"})["ok"] is False
    assert call_tool("limitation_check", {"provision": "73", "financial_year": "2019-21"})["ok"] is False


def test_date_diff_and_validation():
    assert call_tool("date_diff", {"start": "2024-01-01", "end": "2024-03-01"})["result"]["days"] == 60
    assert call_tool("date_diff", {"start": "2024-01-01"})["ok"] is False
    assert call_tool("no_such_tool", {})["ok"] is False
    assert {s["name"] for s in SPECS} == {"statute_lookup", "statute_search", "limitation_check", "date_diff",
                                          "caselaw_search", "record_lookup", "send_reply"}


def test_record_lookup_and_send_reply():
    record = {"notices": [{"hearing_date": {"value": "2024-02-01"}}]}
    assert call_tool("record_lookup", {"field": "notices.0.hearing_date"}, record)["result"]["value"] == "2024-02-01"
    assert call_tool("record_lookup", {"field": "notices.3"}, record)["ok"] is False
    refused = call_tool("send_reply", {"cnr": "TEST", "text": "x", "approved": False})
    assert refused["ok"] is False and "approval" in refused["error"]


@pytest.mark.skipif(not CACHE.exists(), reason="build the precedent cache first: python -m src.tools.caselaw")
def test_caselaw_never_returns_protected_cases():
    protected = blocked()
    test_ids = {l.strip() for l in (ROOT / "data/splits/test.txt").read_text().splitlines() if l.strip()}
    assert test_ids <= protected
    for q in ["consolidated show cause notice multiple financial years", "Additional Notices tab not served",
              "opportunity of personal hearing section 75(4)", "Notification 56/2023 extension of time limit"]:
        r = call_tool("caselaw_search", {"query": q, "k": 10})
        assert r["ok"] and r["result"]
        assert not {h["cnr"] for h in r["result"]} & protected
