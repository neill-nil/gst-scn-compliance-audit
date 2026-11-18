# Run the NoticeCheck demo

You need **Git, Python 3.10 or newer, and a browser**. You do **not** need the Qwen model, LoRA weights, or a GPU.

## 1. Get the demo

In a terminal:

```sh
git clone -b noticecheck-demo https://github.com/neill-nil/gst-scn-compliance-audit.git
cd gst-scn-compliance-audit
```

If you already have the repository, switch to the `noticecheck-demo` branch and pull its latest changes instead.

## 2. Show the saved runs (no key needed)

```sh
python3 -m demo.server --port 8765
```

Open **http://127.0.0.1:8765/** in your browser. Pick a case, press **Analyse Case**, then use **Play**, **Pause**, or **Next step**. Click a quoted finding to jump to the matching judgment paragraph. **What each system flagged** shows the checks side by side; expand the table to see all 13. On any case, switch between the saved **NoticeCheck · Qwen** and **NoticeCheck · Gemini** runs. Case C additionally has **B0 rules**, **B1 plain Qwen**, and **B2 Gemini with statute text** on the same human-checked fact record.

These are genuine recorded outputs, so replay needs no API key or internet. Cases A and B are fresh judgments: their Qwen and Gemini runs independently extracted facts, and B0/B1/B2 were not run on them. Case C uses the saved research outputs for all five systems on **one shared human-checked fact record**. Baselines provide saved checklists; the NoticeCheck runs also have step traces. The traces show recorded decisions, tool calls, checks and hand-off; they do not expose private model thoughts. A system flag is not automatically a correct defect, and “cannot tell” is not automatically a miss.

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

Open **http://127.0.0.1:8765/**, expand **Paste a High Court judgment · live Gemini preview**, paste judgment text, and press **Run live with Gemini**. Use **Load a separate example judgment** if you want an example used nowhere else in the demo or evaluation splits. The page shows extracted facts, tool calls and provisional findings as they arrive, highlights cited paragraphs, then shows the final checklist. **Return to last live run (this tab)** brings its trace back after you visit another case. It is kept only in the open browser tab; reloading the page clears it. A real live run needs internet and may take longer if the model or API is busy.

**Windows PowerShell:** use `py` instead of `python3`, `.venv\Scripts\python` instead of `.venv/bin/python`, and `Copy-Item .env.example .env` instead of `cp .env.example .env`.

## What to know before presenting

- The system was evaluated on **High Court judgments describing GST proceedings**, not on original show cause notices. Paste a judgment, not a notice.
- In Case C, B0, B1, B2 and both NoticeCheck variants use the **same human-checked facts**. The human annotation identifies the hearing issue; other check differences are displayed as system decisions, not declared correct or incorrect without a reference label.
- Prepared Gemini outputs are saved with the demo and need no key to replay. For A/B, these are demo runs with Gemini extraction and the bundled precedent excerpts. For C, the Gemini pipeline output is the saved research run on the shared facts. New paste-in runs use your own key. The live-only example is M/s Sri Lakshmi Silvers v. State Tax Officer (reserved case `HCMA010421202024`); it has no prepared result on this page.
- A quote match only confirms that words appear in the text. It does not establish that the fact concerns the correct proceeding or that the legal conclusion is right.
- Live case-law search uses nine bundled precedent excerpts unless the full local precedent index is installed. The page labels this limit. The saved Qwen results do not change.
- The Gemini key stays on the local server, not in the web page. Pasted text and model replies are not saved in the demo cache; the project's normal LLM usage log records call metadata.

The saved demo bundles the three judgments, all available system outputs, NoticeCheck traces, styling, fonts, and a separate live-only judgment text. Internet is needed only for a new live Gemini call or for opening a linked source PDF.
