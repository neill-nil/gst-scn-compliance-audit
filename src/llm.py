"""The two model calls the baselines import, as thin wrappers over src.common.llm.complete.

    generate(prompt, model, seed)    -> B1: the local Qwen3 server (LOCAL_BASE_URL, e.g. Ollama or vLLM)
    generate_frontier(prompt, model) -> B2: the Gemini API (GEMINI_API_KEY)

Both return (text, {"tokens_in", "tokens_out"}). Every call is cached and logged by complete().
"""
import re

from src.common.llm import complete

# Qwen3's own switch for plain answers. vLLM gets enable_thinking=False from complete(); Ollama
# ignores that field, so the switch is also put in the prompt. Same text for every case.
NO_THINK = "\n\n/no_think"


def _strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


def generate(prompt: str, model: str, seed: int) -> tuple[str, dict]:
    out = complete("local", [{"role": "user", "content": prompt + NO_THINK}], temperature=0.0, seed=seed,
                   max_tokens=4096, model=model, tag="b1")
    return _strip_think(out["text"]), {"tokens_in": out["tokens_in"], "tokens_out": out["tokens_out"]}


def generate_frontier(prompt: str, model: str) -> tuple[str, dict]:
    out = complete("gemini", [{"role": "user", "content": prompt}], temperature=0.0, max_tokens=4096,
                   model=None if model == "frontier-tbd" else model, tag="b2")
    return _strip_think(out["text"]), {"tokens_in": out["tokens_in"], "tokens_out": out["tokens_out"]}
