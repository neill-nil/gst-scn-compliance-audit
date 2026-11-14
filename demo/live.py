"""Run a pasted judgment through Gemini extraction and the real NoticeCheck pipeline.

The callback receives events as they occur. No run output or pasted text is saved by
the demo; Gemini receives the text because it supplies the live model calls.
"""
import json
import re
from pathlib import Path
from uuid import uuid4

from scripts.build_e2e_inputs import clean as clean_extracted_facts
from src.baselines.inputs import build_view
from src.common.llm import complete
from src.prefill.prefill import COMMON, FACTS_TASK
from src.prefill.schema import FACTS_SCHEMA
from src.prefill.verify_quotes import norm as quote_norm
from src.tools.caselaw import use_cache

ROOT = Path(__file__).resolve().parents[1]
from src.noticecheck.pipeline import run_case  # noqa: E402

MAX_TEXT_LENGTH = 30000
PARA_START = re.compile(r"(?m)^\s*(?:¶\s*(\d{1,3})\s*[.:-]?|\[\s*(\d{1,3})\s*\]\s*|(\d{1,3})\s*[.)]\s+)")


def paragraphs_from_text(raw: str) -> list[dict]:
    text = raw.replace("\r\n", "\n").replace("\r", "\n").strip()
    markers = list(PARA_START.finditer(text))
    paragraphs = []
    if markers:
        if text[:markers[0].start()].strip():
            paragraphs.append({"n": 0, "text": text[:markers[0].start()].strip()})
        for i, marker in enumerate(markers):
            end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
            body = text[marker.end():end].strip()
            if body:
                paragraphs.append({"n": int(next(x for x in marker.groups() if x is not None)), "text": body})
    else:
        blocks = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
        paragraphs = [{"n": i, "text": block} for i, block in enumerate(blocks, 1)]
    # Duplicate paragraph numbers occur in pasted judgments. Give each DOM anchor a unique number.
    used = set()
    for paragraph in paragraphs:
        n = paragraph["n"]
        while n in used:
            n += 1
        paragraph["n"] = n
        used.add(n)
    return paragraphs


def ground_facts(facts: dict, paragraphs: list[dict]) -> tuple[dict, dict]:
    """Keep only verbatim-supported extracted values and correct their paragraph anchors."""
    stats = {"quotes_located": 0, "ungrounded_items_removed": 0}
    search = [(p["n"], quote_norm(p["text"])) for p in paragraphs]

    def para_for(quote):
        q = quote_norm(quote or "")
        return next((n for n, text in search if q and q in text), None)

    def visit(node):
        if isinstance(node, list):
            kept = [visit(item) for item in node]
            return [item for item in kept if item is not None]
        if not isinstance(node, dict):
            return node
        if "quote" in node:
            n = para_for(node.get("quote"))
            if n is None:
                if node.get("quote") or node.get("value") is not None:
                    stats["ungrounded_items_removed"] += 1
                if "value" not in node:
                    return None
                node.update(value=None, quote=None, para=None)
            else:
                stats["quotes_located"] += 1
                node["para"] = n
            return node
        return {key: visit(value) for key, value in node.items()}

    return visit(facts), stats


def run_live(text: str, emit) -> dict:
    if not isinstance(text, str) or len(text.strip()) < 80:
        raise ValueError("Paste at least 80 characters from a High Court GST judgment.")
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"Judgment text is too long; paste at most {MAX_TEXT_LENGTH:,} characters.")
    paragraphs = paragraphs_from_text(text)
    if not paragraphs:
        raise ValueError("No judgment paragraphs were found in the pasted text.")
    emit({"type": "input", "paragraphs": paragraphs})
    emit({"type": "stage", "stage": "extract", "message": "Gemini is extracting procedural facts from the pasted judgment."})
    numbered = "\n\n".join(f"[{p['n']}] {p['text']}" for p in paragraphs)
    response = complete("gemini", [{"role": "user", "content": f"{COMMON}\n{FACTS_TASK}\nJUDGMENT:\n{numbered}"}],
                        json_schema=FACTS_SCHEMA, max_tokens=8192, temperature=0.0,
                        use_cache=False, tag="demo:live_facts")
    if response["json"] is None:
        raise RuntimeError(f"Gemini did not return usable extracted facts: {response.get('error', 'empty reply')}")
    facts, grounding = ground_facts(clean_extracted_facts(response["json"]), paragraphs)
    emit({"type": "extraction", "facts": facts, "grounding": grounding, "model": response["model"]})
    record = {"cnr": "LIVE" + uuid4().hex[:10].upper(), "schema_version": "0.1", "court": "Not supplied",
              "case_no": "Pasted judgment", "decision_date": None, **facts}
    try:
        inp = build_view(record, "full_record")
    except ValueError as exc:
        raise ValueError("The extracted order date was invalid; check the pasted judgment.") from exc
    cfg = json.loads((ROOT / "configs/nc_full_gemini.json").read_text(encoding="utf-8"))
    cfg.update(use_cache=False, trace_responses=True)
    emit({"type": "stage", "stage": "check", "message": "NoticeCheck is planning, calling tools, checking statutory conditions and verifying evidence with Gemini."})
    full_index = ROOT / "data/interim/caselaw_paragraphs.jsonl.gz"
    preview_index = ROOT / "demo/precedents.jsonl.gz"
    with use_cache(full_index if full_index.exists() else preview_index,
                   min_score=0.0 if full_index.exists() else 2.0):
        result, _ = run_case(inp, cfg, on_step=lambda step: emit({"type": "step", "step": step}))
    result.update(system="noticecheck_live_gemini", mode="live_gemini", extractor="gemini")
    emit({"type": "result", "result": result})
    return result
