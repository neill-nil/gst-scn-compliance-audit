"""Review tool: turn pre-filled drafts into gold records. No packages beyond requirements.txt.

Opens a page in your browser with the judgment on the left and the draft on the right. Every change is
checked live against the schema and the judgment text (quotes must appear word for word).
Your reviews are saved to data/gold/annotations/<reviewer>/<cnr>.json.

Usage: python -m review_app.server            # then pick your reviewer id (r1..r4) on the page
       python -m review_app.server --port 8600
"""
import argparse
import csv
import json
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.prefill.schema import FACTS_SCHEMA, FINDINGS_SCHEMA, validate_record
from src.prefill.verify_quotes import ROOT, judgment_paragraphs, norm, quotes_in

DRAFTS = ROOT / "data" / "prefill" / "v1"
ANNOTATIONS = ROOT / "data" / "gold" / "annotations"
QUEUE = ROOT / "data" / "splits" / "review_queue.csv"
PAGE = Path(__file__).with_name("index.html")

_paras, _lock = {}, threading.Lock()


def paragraphs(cnr: str) -> list[dict]:
    with _lock:
        if cnr not in _paras:
            _paras[cnr] = [{"n": p["n"], "text": p["text"]} for p in judgment_paragraphs(cnr)]
        return _paras[cnr]


def queue() -> list[dict]:
    with open(QUEUE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def annotation_path(reviewer: str, cnr: str) -> Path:
    return ANNOTATIONS / reviewer / f"{cnr}.json"


def check(record: dict) -> dict:
    """Schema and rule problems, plus where each quote was found in the judgment."""
    paras = paragraphs(record["cnr"])
    normed = [(p["n"], norm(p["text"])) for p in paras]
    quotes = []
    for where, quote, para in quotes_in({"facts": record.get("facts"), "findings": record.get("findings")}):
        q = norm(quote)
        found_in = [n for n, t in normed if q in t]
        path, label = where.split(":", 1)
        quotes.append({"where": path if label == path else where, "quote": quote, "para": para, "found_in": found_in})
    return {"problems": validate_record(record), "quotes": quotes}


def case(cnr: str, reviewer: str) -> dict:
    saved = annotation_path(reviewer, cnr)
    source = saved if saved.exists() else DRAFTS / f"{cnr}.json"
    if not source.exists():
        raise FileNotFoundError(f"no draft for {cnr}: pull main (data/prefill/v1) first")
    record = json.loads(source.read_text(encoding="utf-8"))
    draft = json.loads((DRAFTS / f"{cnr}.json").read_text(encoding="utf-8"))
    meta = next((r for r in queue() if r["cnr"] == cnr), {"cnr": cnr})
    return {"meta": meta, "record": record, "saved": saved.exists(), "draft_checks": draft.get("checks"),
            "paragraphs": paragraphs(cnr), "check": check(record),
            "enums": {"type": FINDINGS_SCHEMA["properties"]["defects_argued"]["items"]["properties"]["type"]["enum"],
                      "disposition": FINDINGS_SCHEMA["properties"]["outcome"]["properties"]["disposition"]["enum"]}}


def save(body: dict) -> dict:
    reviewer, record = body["reviewer"], body["record"]
    draft = json.loads((DRAFTS / f"{record['cnr']}.json").read_text(encoding="utf-8"))
    result = check(record)
    missing = [q for q in result["quotes"] if not q["found_in"]]
    status = body["status"]
    if status == "reviewed" and (result["problems"] or missing):
        status = "needs_fix"  # kept, but not gold until the problems are fixed
    record["review"] = {
        "status": status, "kind": body.get("kind", "first"), "reviewed_by": reviewer,
        "drafted_by": draft["review"]["drafted_by"], "prompt_version": draft["review"]["prompt_version"],
        "notes": body.get("notes", ""), "seconds": body.get("seconds"),
        "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    record.pop("checks", None)
    record.pop("usage", None)
    path = annotation_path(reviewer, record["cnr"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"status": status, **result}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if url.path == "/":
                self._send(200, PAGE.read_bytes(), "text/html")
            elif url.path == "/api/queue":
                rows = [dict(r, done=(json.loads(annotation_path(q["reviewer"], r["cnr"]).read_text(encoding="utf-8"))
                                      ["review"]["status"] if annotation_path(q["reviewer"], r["cnr"]).exists() else ""))
                        for r in queue() if r["reviewer"] == q["reviewer"]]
                self._send(200, rows)
            elif url.path == "/api/case":
                self._send(200, case(q["cnr"], q["reviewer"]))
            else:
                self._send(404, {"error": "not found"})
        except Exception as e:  # show the reason on the page instead of a blank screen
            self._send(500, {"error": f"{type(e).__name__}: {e}"})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8"))
        try:
            if self.path == "/api/check":
                self._send(200, check(body["record"]))
            elif self.path == "/api/save":
                self._send(200, save(body))
            else:
                self._send(404, {"error": "not found"})
        except Exception as e:
            self._send(500, {"error": f"{type(e).__name__}: {e}"})

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8501)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    url = f"http://127.0.0.1:{args.port}/"
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Review tool running at {url}  (Ctrl+C to stop)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
