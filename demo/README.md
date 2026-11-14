# NoticeCheck demo

This local page replays **saved outputs from the project's real Qwen runs**. It does not run the 8B model on your laptop or generate a new verdict. The three included judgments have bundled source text, so the saved-run API works without an API key or GPU.

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

The prepared judgments are the working demo. The paste box is explicitly disabled until a separate live Gemini API integration is configured. The demo bundles its styling, fonts, source text, and saved outputs. Internet is only needed if you click the public source PDF link.

## Data wiring

- `runs/fresh_nc/outputs.jsonl` and `runs/e2e_nc_tuned/outputs.jsonl`: final full-pipeline findings and trace paths.
- `runs/*/traces/`: recorded execution steps.
- `runs/rq2_*/outputs_*.jsonl`: extractor comparison.
- `runs/b1_full_record/outputs.jsonl` and `runs/nc_full_s2/outputs.jsonl`: RQ1 comparison on the shared human-checked record in `data/gold/records.jsonl`.
- `demo/sources/*.json`: judgment text extracted from the public PDFs and bundled for local replay. `data/text/` takes precedence if it is present.

`GET /api/cases` lists the prepared cases, `GET /api/cases/{cnr}` returns a complete case, and `GET /api/health` checks the server.
