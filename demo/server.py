"""NoticeCheck demo: saved Qwen replay and an optional streamed Gemini live run.

Run: python -m demo.server --port 8765
"""
import argparse
import csv
import gzip
import json
import os
import re
import sys
import threading
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_segment import clean, segment  # noqa: E402
from src.baselines.inputs import build_view  # noqa: E402
from src.common import llm  # noqa: E402  # loads the project .env, if present

LIVE_LOCK = threading.Lock()

CASES = (
    ("HCMA011063142025", "fresh_nc", "Findings with contested points"),
    ("WBCHCA0084902025", "fresh_nc", "A contested, incomplete record"),
    ("HCMD010677412024", "nc_full_s2", "Five research systems on the same human-checked facts"),
)
LIVE_EXAMPLE = "HCMA010421202024"


@lru_cache(maxsize=None)
def jsonl(path: str) -> dict:
    file = ROOT / path
    if not file.exists():
        return {}
    return {row["cnr"]: row for line in file.read_text(encoding="utf-8").splitlines()
            if line.strip() for row in [json.loads(line)]}


@lru_cache(maxsize=None)
def jsonl_view(path: str, view: str) -> dict:
    file = ROOT / path
    return {row["cnr"]: row for line in file.read_text(encoding="utf-8").splitlines()
            if line.strip() for row in [json.loads(line)] if row.get("view") == view}


@lru_cache(maxsize=1)
def manifest() -> dict:
    with (ROOT / "data/manifests/screened.csv").open(newline="", encoding="utf-8") as f:
        return {row["cnr"]: row for row in csv.DictReader(f)}


def sharded(run: str) -> dict:
    rows = {}
    for path in sorted((ROOT / "runs" / run).glob("outputs_*.jsonl")):
        rows.update(jsonl(str(path.relative_to(ROOT))))
    return rows


def source(cnr: str) -> list[dict]:
    meta = manifest()[cnr]
    path = ROOT / "data/text" / meta["court"] / f"{cnr}.txt.gz"
    if not path.exists():
        bundled = ROOT / "demo/sources" / f"{cnr}.json"
        paragraphs = json.loads(bundled.read_text(encoding="utf-8")) if bundled.exists() else []
    else:
        pages = gzip.open(path, "rt", encoding="utf-8", errors="replace").read().split("\f")
        kept, _ = clean(pages)
        paragraphs = [{"n": p["n"], "text": p["text"]} for p in segment(kept) if p["text"]]
    # Some PDF extractions collapse every numbered paragraph onto one line.
    # Recover only a clear, increasing run of inline paragraph markers.
    if len(paragraphs) == 1:
        text = paragraphs[0]["text"]
        markers = list(re.finditer(r"(?<!\w)(\d{1,2})\.(?=[A-Z])", text))
        numbers = [int(m.group(1)) for m in markers]
        if len(markers) >= 2 and numbers == list(range(numbers[0], numbers[0] + len(numbers))):
            paragraphs = ([{"n": 0, "text": text[:markers[0].start()].strip()}]
                          if text[:markers[0].start()].strip() else [])
            paragraphs += [{"n": numbers[i], "text": text[m.end():markers[i + 1].start() if i + 1 < len(markers) else len(text)].strip()}
                           for i, m in enumerate(markers)]
    return paragraphs


def trace(row: dict) -> list[dict]:
    relative = row.get("trace_file")
    cnr = row.get("cnr", "")
    if not cnr.isalnum():
        return []
    candidates = [ROOT / relative] if relative else []
    # Sharded Kaggle traces were consolidated under these directories, but
    # outputs.jsonl retains the original per-shard trace_file value.
    candidates += [ROOT / "runs/fresh_nc/traces" / f"{cnr}.jsonl",
                   ROOT / "runs/e2e_nc_tuned/traces" / f"{cnr}.jsonl",
                   ROOT / "runs/nc_full_s2/traces/full_record" / f"{cnr}.jsonl"]
    path = next((p.resolve() for p in candidates if p.resolve().is_relative_to(ROOT.resolve()) and p.exists()), None)
    if path is None:
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def case_summary(cnr: str, run: str, description: str) -> dict:
    meta = manifest()[cnr]
    row = jsonl(f"runs/{run}/outputs.jsonl").get(cnr)
    if row is None:
        raise FileNotFoundError(f"Saved output for {cnr} is missing from runs/{run}")
    counts = {v: sum(f.get("verdict") == v for f in row["findings"])
              for v in ("defect", "contested", "cant_tell", "no_defect")}
    return {"id": cnr, "run": run, "title": meta["title"], "court": meta["court_name"],
            "decision_date": meta["decision_date"], "description": description,
            "input_label": "Human-checked facts shared with Plain Qwen" if run == "nc_full_s2"
                           else "Fine-tuned extraction from this judgment",
            "counts": counts, "source_available": bool(source(cnr)),
            "source_pdf_url": "https://indian-high-court-judgments.s3.ap-south-1.amazonaws.com/"
                              + quote(meta["s3_key"], safe="/")}


def case_detail(cnr: str) -> dict:
    item = next(((c, r, d) for c, r, d in CASES if c == cnr), None)
    if item is None:
        raise KeyError("Unknown demo case")
    _, run, description = item
    main = jsonl(f"runs/{run}/outputs.jsonl")[cnr]
    comparison = None
    systems = {"nc_qwen": main}
    if run == "nc_full_s2":
        gold = jsonl("data/gold/records.jsonl").get(cnr)
        baselines = {key: jsonl_view(f"runs/{folder}/outputs.jsonl", "full_record").get(cnr)
                     for key, folder in (("b0", "b0_v2"), ("b1", "b1_v2"), ("b2", "b2_v2"))}
        research_gemini = jsonl_view("runs/nc_gemini_s1/outputs.jsonl", "full_record").get(cnr)
        if gold and research_gemini and all(baselines.values()):
            shared = build_view(gold, "full_record")
            comparison = {"input": shared, "plain": baselines["b1"],
                          "reference_defects": [d["type"] for d in gold.get("defects_argued", [])
                                                if d.get("finding") == "defect_found"]}
            systems.update(baselines, nc_gemini=research_gemini)
    gemini_path = ROOT / "demo/gemini_runs" / f"{cnr}.json"
    gemini = json.loads(gemini_path.read_text(encoding="utf-8")) if gemini_path.exists() else None
    if run == "nc_full_s2" and comparison:
        research_gemini = systems["nc_gemini"]
        model = next((s.get("model") for s in trace(research_gemini) if s.get("model")), "Gemini")
        gemini = {"cnr": cnr, "input": "human-checked full_record facts", "extractor": "human-checked facts",
                  "checker": model, "precedent_index": "research_corpus",
                  "facts": comparison["input"]["record"],
                  "events": ([{"type": "stage", "stage": "check", "message": "NoticeCheck with Gemini on the shared human-checked facts."}]
                             + [{"type": "step", "step": step} for step in trace(research_gemini)]
                             + [{"type": "result", "result": research_gemini}]),
                  "result": research_gemini}
    elif gemini:
        systems["nc_gemini"] = gemini["result"]
    return {**case_summary(cnr, run, description), "mode": "saved_qwen_run",
            "paragraphs": source(cnr), "main": main, "trace": trace(main),
            "comparison": comparison, "gemini": gemini, "systems": systems}


def live_example() -> dict:
    meta = manifest()[LIVE_EXAMPLE]
    text = (ROOT / "demo/examples/sri_lakshmi_silvers_live_only.txt").read_text(encoding="utf-8")
    return {"id": LIVE_EXAMPLE, "title": meta["title"], "text": text,
            "source_pdf_url": "https://indian-high-court-judgments.s3.ap-south-1.amazonaws.com/"
                              + quote(meta["s3_key"], safe="/")}


class Handler(BaseHTTPRequestHandler):
    def send(self, status: int, data, content_type="application/json"):
        body = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path in ("/", "/index.html"):
                self.send(200, (ROOT / "demo/index.html").read_bytes(), "text/html")
            elif path == "/demo.js":
                self.send(200, (ROOT / "demo/demo.js").read_bytes(), "text/javascript")
            elif path == "/tailwindcdn.js":
                self.send(200, (ROOT / "demo/tailwindcdn.js").read_bytes(), "text/javascript")
            elif path in ("/text-fonts.css", "/material-symbols.css"):
                self.send(200, (ROOT / "demo" / path.lstrip("/")).read_bytes(), "text/css")
            elif path in ("/manrope.woff2", "/jetbrains-mono.woff2"):
                self.send(200, (ROOT / "demo" / path.lstrip("/")).read_bytes(), "font/woff2")
            elif path == "/material-symbols.ttf":
                self.send(200, (ROOT / "demo/material-symbols.ttf").read_bytes(), "font/ttf")
            elif path == "/api/health":
                self.send(200, {"ok": True, "mode": "saved_qwen_run", "cases": len(CASES),
                                "live_available": bool(os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_MODEL")),
                                "live_precedents": "full_index" if (ROOT / "data/interim/caselaw_paragraphs.jsonl.gz").exists()
                                                   else "bundled_excerpts"})
            elif path == "/api/cases":
                self.send(200, [case_summary(*item) for item in CASES])
            elif path == "/api/live-example":
                self.send(200, live_example())
            elif path.startswith("/api/cases/"):
                self.send(200, case_detail(path.removeprefix("/api/cases/")))
            else:
                self.send(404, {"error": "Not found"})
        except (KeyError, FileNotFoundError) as exc:
            self.send(404, {"error": str(exc)})
        except Exception as exc:
            self.send(500, {"error": f"{type(exc).__name__}: {exc}"})

    def do_POST(self):
        if urlparse(self.path).path != "/api/live":
            self.send(404, {"error": "Not found"})
            return
        if not (os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_MODEL")):
            self.send(503, {"error": "Set GEMINI_API_KEY and GEMINI_MODEL in the repository .env, then restart the server."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 120_000:
                raise ValueError("Request is empty or too large (120 KB maximum).")
            payload = json.loads(self.rfile.read(length))
            text = payload.get("text") if isinstance(payload, dict) else None
            if not isinstance(text, str) or not 80 <= len(text.strip()) <= 30_000:
                raise ValueError("Paste 80 to 30,000 characters from a High Court GST judgment.")
        except (ValueError, json.JSONDecodeError) as exc:
            self.send(400, {"error": str(exc)})
            return
        if not LIVE_LOCK.acquire(blocking=False):
            self.send(409, {"error": "A live run is already in progress on this server."})
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        def emit(event):
            try:
                self.wfile.write(json.dumps(event, ensure_ascii=False).encode("utf-8") + b"\n")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass  # The model call cannot be cancelled, but the browser is no longer waiting.

        try:
            from demo.live import run_live
            run_live(text, emit)
        except Exception as exc:
            emit({"type": "error", "message": f"{type(exc).__name__}: {str(exc)[:350]}"})
        finally:
            LIVE_LOCK.release()

    def log_message(self, format, *args):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    address = ("127.0.0.1", args.port)
    print(f"NoticeCheck saved-run demo: http://{address[0]}:{address[1]}", flush=True)
    ThreadingHTTPServer(address, Handler).serve_forever()


if __name__ == "__main__":
    main()
