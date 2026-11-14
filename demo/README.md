# NoticeCheck demo

This local page has two distinct modes: **saved Qwen replay** and an optional **live Gemini preview**. The saved mode replays actual project outputs without running the 8B model. The three included judgments have bundled source text, so replay works without an API key, GPU, or internet.

## Run

From the repository root, with Python 3.10 or newer:

```sh
python3 -m demo.server --port 8765
```

Open <http://127.0.0.1:8765/>. Choose a case, press **Analyse Case**, and use **Play**, **Pause**, or **Next step**. A finding's quote jumps to the matching judgment paragraph. **Open source PDF** links to the public judgment.

Case C also has the research controls:

- **RQ2:** saved base and fine-tuned extractor outputs for the same judgment.
- **RQ1:** saved plain Qwen and NoticeCheck outputs on the same human-checked fact record. This is separate from the full pipeline output, which used fine-tuned extraction.

The replay shows the recorded plan calls, tool arguments and output summaries, checks, verification, hand-off, and final checklist. It cannot show private model reasoning because that was not saved. Quote matching only locates text; it does not validate legal conclusions.

## Enable live paste

Live mode needs Python's `jsonschema` package, a Gemini API key, an available Gemini model, and internet:

```sh
python3 -m venv .venv
.venv/bin/pip install jsonschema
cp .env.example .env
```

Put `GEMINI_API_KEY` and `GEMINI_MODEL` in `.env`, then start or restart with `.venv/bin/python -m demo.server --port 8765`. Use `python -m src.common.llm models gemini` after configuring the key if you need to see available model names. Open the paste section, paste 80–30,000 characters from a High Court GST judgment, and press **Run live with Gemini**.

The server sends the text to Gemini for fact extraction, checks literal quote matches, normalizes the facts, then runs `configs/nc_full_gemini.json` through the real NoticeCheck pipeline. The page receives each recorded step over a streaming response, shows provisional checks beside the text, and replaces them with the verified final checklist. The API key stays on the server. The live path does not save the pasted text or model replies in the project cache; the normal LLM usage log still records call metadata.

**Live is a preview, not a Qwen evaluation:** Gemini replaces Qwen in both stages. The RQ1/RQ2 research comparisons remain in saved Case C only. Unless the full local precedent index has been built, live case-law search uses nine bundled excerpts from the project's saved precedent evidence; the UI labels this limit. Live runtime depends on the configured model and API quota. A matching quote confirms literal presence in the pasted text, not the legal correctness of a finding.

The demo bundles its styling, fonts, source text, and saved outputs. Internet is needed for live Gemini calls and the optional public source PDF link.

## Data wiring

- `runs/fresh_nc/outputs.jsonl` and `runs/e2e_nc_tuned/outputs.jsonl`: final full-pipeline findings and trace paths.
- `runs/*/traces/`: recorded execution steps.
- `runs/rq2_*/outputs_*.jsonl`: extractor comparison.
- `runs/b1_full_record/outputs.jsonl` and `runs/nc_full_s2/outputs.jsonl`: RQ1 comparison on the shared human-checked record in `data/gold/records.jsonl`.
- `demo/sources/*.json`: judgment text extracted from the public PDFs and bundled for local replay. `data/text/` takes precedence if it is present.
- `demo/precedents.jsonl.gz`: nine real precedent excerpts used for limited live retrieval when the full local case-law index is absent.

`GET /api/cases` lists the prepared cases, `GET /api/cases/{cnr}` returns a complete saved case, `GET /api/health` reports live availability, and `POST /api/live` streams newline-delimited JSON events for a pasted judgment.
