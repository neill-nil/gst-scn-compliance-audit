# Run the NoticeCheck demo

You need **Git, Python 3.10 or newer, and a browser**. You do **not** need the Qwen model, LoRA weights, or a GPU.

## 1. Get the demo

In a terminal:

```sh
git clone -b noticecheck-demo https://github.com/neill-nil/gst-scn-compliance-audit.git
cd gst-scn-compliance-audit
```

If you already have the repository, switch to the `noticecheck-demo` branch and pull its latest changes instead.

## 2. Show the saved Qwen run (no key needed)

```sh
python3 -m demo.server --port 8765
```

Open **http://127.0.0.1:8765/** in your browser. Pick a case, press **Analyse Case**, then use **Play**, **Pause**, or **Next step**. Click a quoted finding to jump to the matching judgment paragraph. Case C also has the separate RQ1 and RQ2 comparison controls.

This is a replay of the project's real saved Qwen outputs. It works without an API key or internet. It shows recorded decisions, tool calls, checks, verification and hand-off; it cannot show private model thoughts that were never saved.

## 3. Optional: run a pasted judgment live

Each person running the demo on their **own computer** needs their **own Gemini API key** for this mode. The saved replay above needs no key. Live mode sends the pasted judgment text to Gemini, which replaces Qwen for both fact extraction and NoticeCheck.

Stop the server with **Ctrl+C**. Then, from the repository folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install jsonschema
cp .env.example .env
```

Open `.env` in a text editor. Fill in `GEMINI_API_KEY` and check that `GEMINI_MODEL` names a model your key can use. Keep this file private; it is excluded from Git. If you need to see available model names, run `.venv/bin/python -m src.common.llm models gemini` after adding the key.

Start the server again:

```sh
.venv/bin/python -m demo.server --port 8765
```

Open **http://127.0.0.1:8765/**, expand **Paste a High Court judgment · live Gemini preview**, paste judgment text, and press **Run live with Gemini**. The page shows extracted facts, tool calls and provisional findings as they arrive, highlights cited paragraphs, then shows the verified final checklist. A real live run needs internet and may take longer if the model or API is busy.

**Windows PowerShell:** use `py` instead of `python3`, `.venv\Scripts\python` instead of `.venv/bin/python`, and `Copy-Item .env.example .env` instead of `cp .env.example .env`.

## What to know before presenting

- The system was evaluated on **High Court judgments describing GST proceedings**, not on original show cause notices. Paste a judgment, not a notice.
- Saved Case C's RQ1 checkers use the **same human-checked facts**; its RQ2 extractors use the **same judgment text**. These are separate comparisons. Live Gemini is a preview, not an RQ1 or RQ2 evaluation result.
- A quote match only confirms that words appear in the text. It does not establish that the fact concerns the correct proceeding or that the legal conclusion is right.
- Live case-law search uses nine bundled precedent excerpts unless the full local precedent index is installed. The page labels this limit. The saved Qwen results do not change.
- The Gemini key stays on the local server, not in the web page. Pasted text and model replies are not saved in the demo cache; the project's normal LLM usage log records call metadata.

The saved demo bundles the three judgments, model outputs, traces, styling, and fonts. Internet is needed only for the live Gemini call or for opening a linked source PDF.
