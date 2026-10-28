"""Shared model client for every part of the project.

One function, `complete`, talks to any OpenAI-compatible chat endpoint:
  - "gemini": Google's Gemini API through its OpenAI-compatible endpoint (free tier, key in .env)
  - "local":  a local or Kaggle server (vLLM or Ollama) serving Qwen3 / Gemma 3

Features: JSON output validated against a schema (one corrective retry), retry with backoff on rate
limits and server errors, request pacing (requests per minute), a disk cache so identical calls
are never paid for twice, and a log line per call in runs/llm_calls.jsonl for cost reporting.

Settings come from environment variables or a .env file in the repo root (see .env.example).

Usage:
    from src.common.llm import complete
    out = complete("gemini", [{"role": "user", "content": "..."}], json_schema={...})
    out["json"], out["text"], out["tokens_in"], out["tokens_out"], out["seconds"]

    python -m src.common.llm models gemini      # list model names your key can use
    python -m src.common.llm ping gemini        # one tiny test call
"""
import hashlib
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "runs" / "cache"
CALL_LOG = ROOT / "runs" / "llm_calls.jsonl"

BACKENDS = {
    "gemini": {
        "base_url": ("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai"),
        "api_key": ("GEMINI_API_KEY", None),
        "model": ("GEMINI_MODEL", None),
        "rpm": ("GEMINI_RPM", "8"),
    },
    "local": {
        "base_url": ("LOCAL_BASE_URL", "http://localhost:8000/v1"),
        "api_key": ("LOCAL_API_KEY", "none"),
        "model": ("LOCAL_MODEL", None),
        "rpm": ("LOCAL_RPM", "0"),
    },
}

_last_call = {}
_lock = threading.Lock()


def _load_dotenv():
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()


def _setting(backend: str, name: str):
    var, default = BACKENDS[backend][name]
    value = os.environ.get(var, default)
    if value is None:
        raise RuntimeError(f"Set {var} in .env (see .env.example)")
    return value


def _pace(backend: str):
    rpm = float(_setting(backend, "rpm"))
    if rpm <= 0:
        return
    with _lock:
        wait = _last_call.get(backend, 0) + 60.0 / rpm - time.time()
        if wait > 0:
            time.sleep(wait)
        _last_call[backend] = time.time()


def _post(backend: str, path: str, body: dict | None, timeout: int = 180) -> dict:
    url = _setting(backend, "base_url").rstrip("/") + path
    headers = {"Authorization": f"Bearer {_setting(backend, 'api_key')}", "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if body is not None else "GET")
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            if e.code in (429, 500, 502, 503, 504) and attempt < 5:
                retry_after = e.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after and retry_after.isdigit() else min(60, 2 ** (attempt + 1)))
                continue
            raise RuntimeError(f"{backend} HTTP {e.code}: {detail}") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt < 5:
                time.sleep(min(60, 2 ** (attempt + 1)))
                continue
            raise RuntimeError(f"{backend} unreachable at {url}: {e}") from None


def _extract_json(text: str):
    """Parse the first JSON object or array in a reply, tolerating ```json fences and <think> blocks."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S)
    if fenced:
        text = fenced.group(1).strip()
    for opener in ("{", "["):
        start = text.find(opener)
        if start == -1:
            continue
        try:
            obj, _ = json.JSONDecoder().raw_decode(text[start:])
            return obj
        except json.JSONDecodeError:
            continue
    raise ValueError("no JSON object found in model output")


def _validate(obj, schema: dict):
    try:
        import jsonschema
    except ImportError:
        return
    jsonschema.validate(obj, schema)


def _log(record: dict):
    CALL_LOG.parent.mkdir(parents=True, exist_ok=True)
    with _lock, open(CALL_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")


def complete(backend: str, messages: list, json_schema: dict | None = None, temperature: float = 0.0,
             seed: int = 0, max_tokens: int = 4096, model: str | None = None, use_cache: bool = True,
             tag: str = "") -> dict:
    """Send a chat request. Returns {"text", "json", "tokens_in", "tokens_out", "seconds", "model", "cached"}.

    With json_schema, the schema is appended to the prompt, the reply is parsed and validated, and one
    corrective retry is made on failure; if that also fails, "json" is None and "error" says why.
    `tag` is free text stored in the call log (e.g. "triage", "prefill:notice") for cost breakdowns.
    """
    model = model or _setting(backend, "model")
    msgs = [dict(m) for m in messages]
    if json_schema is not None:
        msgs[-1]["content"] += ("\n\nReply with a single JSON object that matches this JSON schema, and nothing else:\n"
                                + json.dumps(json_schema))
    key = hashlib.sha256(json.dumps([backend, model, msgs, json_schema, temperature, seed, max_tokens],
                                    sort_keys=True).encode()).hexdigest()
    cache_file = CACHE_DIR / f"{key}.json"
    if use_cache and cache_file.exists():
        out = json.loads(cache_file.read_text())
        out["cached"] = True
        return out

    body = {"model": model, "messages": msgs, "temperature": temperature, "max_tokens": max_tokens}
    if backend == "local":
        body["seed"] = seed
        if "qwen3" in model.lower():
            body["chat_template_kwargs"] = {"enable_thinking": False}  # vLLM: plain answers, no reasoning trace

    tokens_in = tokens_out = 0
    start = time.time()
    result, error = None, None
    for attempt in range(2):
        _pace(backend)
        resp = _post(backend, "/chat/completions", body)
        usage = resp.get("usage") or {}
        tokens_in += usage.get("prompt_tokens", 0)
        tokens_out += usage.get("completion_tokens", 0)
        text = resp["choices"][0]["message"].get("content") or ""
        if json_schema is None:
            break
        try:
            result = _extract_json(text)
            _validate(result, json_schema)
            error = None
            break
        except Exception as e:  # malformed or schema-violating JSON: ask once more with the error
            result, error = None, f"{type(e).__name__}: {str(e)[:300]}"
            body["messages"] = msgs + [{"role": "assistant", "content": text},
                                       {"role": "user", "content": f"That reply was not valid: {error}. "
                                                                   "Reply again with only the corrected JSON."}]
    out = {"text": text, "json": result, "tokens_in": tokens_in, "tokens_out": tokens_out,
           "seconds": round(time.time() - start, 2), "model": model, "cached": False}
    if error:
        out["error"] = error
    _log({"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "backend": backend, "model": model, "tag": tag,
          "tokens_in": tokens_in, "tokens_out": tokens_out, "seconds": out["seconds"], "ok": not error})
    if not error:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(out))
    return out


def list_models(backend: str) -> list[str]:
    resp = _post(backend, "/models", None)
    return sorted(m["id"] for m in resp.get("data", []))


if __name__ == "__main__":
    cmd, backend = (sys.argv[1:3] + ["", ""])[:2]
    if cmd == "models" and backend:
        print("\n".join(list_models(backend)))
    elif cmd == "ping" and backend:
        out = complete(backend, [{"role": "user", "content": "Return the number of days in a leap-year February."}],
                       json_schema={"type": "object", "properties": {"days": {"type": "integer"}},
                                    "required": ["days"]}, use_cache=False, tag="ping")
        print(json.dumps(out, indent=1))
    else:
        print(__doc__)
