"""Read-only NoticeCheck demo over the project's saved, real model runs.

Run: python -m demo.server --port 8765
The optional live Gemini route is deliberately separate from the saved Qwen runs.
"""
import argparse
import csv
import gzip
import json
import sys
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_segment import clean, segment  # noqa: E402
from src.baselines.inputs import build_view  # noqa: E402

CASES = (
    ("HCMA011063142025", "fresh_nc", "Findings with contested points"),
    ("WBCHCA0084902025", "fresh_nc", "A contested, incomplete record"),
    ("HCMD010677412024", "e2e_nc_tuned", "Compare both research questions"),
)


@lru_cache(maxsize=None)
def jsonl(path: str) -> dict:
    file = ROOT / path
    if not file.exists():
        return {}
    return {row["cnr"]: row for line in file.read_text(encoding="utf-8").splitlines()
            if line.strip() for row in [json.loads(line)]}


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
        return json.loads(bundled.read_text(encoding="utf-8")) if bundled.exists() else []
    pages = gzip.open(path, "rt", encoding="utf-8", errors="replace").read().split("\f")
    kept, _ = clean(pages)
    return [{"n": p["n"], "text": p["text"]} for p in segment(kept) if p["text"]]


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
            "counts": counts, "source_available": bool(source(cnr)),
            "source_pdf_url": "https://indian-high-court-judgments.s3.ap-south-1.amazonaws.com/"
                              + quote(meta["s3_key"], safe="/")}


def case_detail(cnr: str) -> dict:
    item = next(((c, r, d) for c, r, d in CASES if c == cnr), None)
    if item is None:
        raise KeyError("Unknown demo case")
    _, run, description = item
    main = jsonl(f"runs/{run}/outputs.jsonl")[cnr]
    extraction_run = "rq2_fresh" if run == "fresh_nc" else "rq2_tuned"
    tuned = sharded(extraction_run).get(cnr)
    base = sharded("rq2_base").get(cnr) if run != "fresh_nc" else None
    rq1 = None
    if run != "fresh_nc":
        gold = jsonl("data/gold/records.jsonl").get(cnr)
        plain = jsonl("runs/b1_full_record/outputs.jsonl").get(cnr)
        structured = jsonl("runs/nc_full_s2/outputs.jsonl").get(cnr)
        if gold and plain and structured:
            rq1 = {"input": build_view(gold, "full_record"), "plain": plain,
                   "noticecheck": structured, "trace": trace(structured)}
    return {**case_summary(cnr, run, description), "mode": "saved_qwen_run",
            "paragraphs": source(cnr), "main": main, "trace": trace(main),
            "rq2": {"input": "same judgment text", "base": base, "fine_tuned": tuned},
            "rq1": rq1}


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
                self.send(200, {"ok": True, "mode": "saved_qwen_run", "cases": len(CASES)})
            elif path == "/api/cases":
                self.send(200, [case_summary(*item) for item in CASES])
            elif path.startswith("/api/cases/"):
                self.send(200, case_detail(path.removeprefix("/api/cases/")))
            else:
                self.send(404, {"error": "Not found"})
        except (KeyError, FileNotFoundError) as exc:
            self.send(404, {"error": str(exc)})
        except Exception as exc:
            self.send(500, {"error": f"{type(exc).__name__}: {exc}"})

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
