# Fine-tuning run on Kaggle (RQ2): notebooks E and F

**What this tests (RQ2):** can our small model, Qwen3-8B, learn to read a judgment and fill in the case facts
(notice date, hearing, reply, order, events) as well as a big model? Notebook **E** trains it (QLoRA) on 196
examples and then extracts the facts of the 137 test cases. Notebook **F** extracts the same 137 cases with the
untrained model, for comparison. Both run in the background, and both can run **at the same time**
(on one account if Kaggle allows two GPU sessions, or on two accounts).

| Notebook | Name | What it does | Time | Download |
|---|---|---|---|---|
| E | `nc-E-train` | trains on GPU 0 (stops itself at 2.5 h at most), then extracts the 137 test cases on both GPUs | about 3.5–4.5 h | `rq2_E.zip` |
| F | `nc-F-base` | extracts the 137 test cases with the untrained model on both GPUs | about 1.5–2 h | `rq2_F.zip` |

Together about 6 GPU hours.

## How to run a notebook (same steps as before)
**When pasting a cell, its first line must start at the very left edge** (no spaces before it). If the first
line is indented, Jupyter strips that indent from every line of the cell and the cell fails with `IndentationError`.

1. kaggle.com → **Create → New Notebook**.
2. Right-hand panel → **Session options**: Accelerator **GPU T4 x2**, Internet **On**.
3. Delete the starter cell. Add 3 code cells and paste **Cell 1**, **Cell 2** and the notebook's **Cell 3**, in that order.
4. Rename the notebook (top left) to the name above.
5. Top right → **Save Version** → **Save & Run All (Commit)** → **Save**. You can close the tab.
6. When the version shows **complete**: open it → **Output** → download the zip → put it in the repo root.

---

## Cell 1: libraries (same in E and F, about 5 minutes)
```python
!apt-get -qq update && apt-get -qq install -y poppler-utils zip > /dev/null
!pip install -q unsloth jsonschema
!python -c "import unsloth, torch; print('unsloth', unsloth.__version__, 'torch', torch.__version__, 'GPUs', torch.cuda.device_count())"
```
The last line must print `GPUs 2`.

## Cell 2: code, judgments, training data, model download (same in E and F, about 10 minutes)
```python
import os, subprocess, time
!git clone -b noticecheck-core https://github.com/neill-nil/gst-scn-compliance-audit.git /kaggle/working/repo
%cd /kaggle/working/repo
!git log --oneline -1
!python scripts/fetch_data.py --reasoned-only      # judgment PDFs, about 1 minute
!python -m scripts.build_rq2_data                   # must print train 196, val 21, test 137
!md5sum data/interim/rq2/*.jsonl
!python -c "from huggingface_hub import snapshot_download; snapshot_download('unsloth/Qwen3-8B-unsloth-bnb-4bit')"
```

---

## Notebook E: `nc-E-train` → download `rq2_E.zip`
Cell 1, Cell 2, then this Cell 3:
```python
# 1) train on GPU 0 (about 1.5-2.5 h; stops itself at 2.5 h and saves)
!CUDA_VISIBLE_DEVICES=0 python -m src.rq2.train --out runs/rq2_lora 2>&1 | tee train.log
!ls -la runs/rq2_lora/adapter
# 2) extract the 137 test cases with the trained model, half on each GPU (about 1-1.5 h)
procs = [subprocess.Popen(["python", "-m", "src.rq2.extract", "--run-id", "rq2_tuned", "--adapter", "runs/rq2_lora/adapter",
                           "--shard", str(k), "--shards", "2"],
                          env=dict(os.environ, CUDA_VISIBLE_DEVICES=str(k)),
                          stdout=open(f"extract_tuned_{k}.log", "w"), stderr=subprocess.STDOUT) for k in (0, 1)]
while any(p.poll() is None for p in procs): time.sleep(60)
!tail -n 3 extract_tuned_*.log
!wc -l runs/rq2_tuned/outputs_*.jsonl
!zip -qr /kaggle/working/rq2_E.zip runs/rq2_lora/adapter runs/rq2_lora/train_log.json runs/rq2_tuned train.log extract_tuned_*.log
%cd /kaggle/working
!rm -rf /kaggle/working/repo
!ls -la /kaggle/working
```

## Notebook F: `nc-F-base` → download `rq2_F.zip`
Cell 1, Cell 2, then this Cell 3:
```python
# extract the 137 test cases with the untrained model, half on each GPU (about 1-1.5 h)
procs = [subprocess.Popen(["python", "-m", "src.rq2.extract", "--run-id", "rq2_base", "--shard", str(k), "--shards", "2"],
                          env=dict(os.environ, CUDA_VISIBLE_DEVICES=str(k)),
                          stdout=open(f"extract_base_{k}.log", "w"), stderr=subprocess.STDOUT) for k in (0, 1)]
while any(p.poll() is None for p in procs): time.sleep(60)
!tail -n 3 extract_base_*.log
!wc -l runs/rq2_base/outputs_*.jsonl
!zip -qr /kaggle/working/rq2_F.zip runs/rq2_base extract_base_*.log
%cd /kaggle/working
!rm -rf /kaggle/working/repo
!ls -la /kaggle/working
```

The `wc -l` lines should add up to 137 (69 + 68) in each notebook.

---

## If something goes wrong
| What you see | What to do |
|---|---|
| Cell 1 doesn't print `GPUs 2` | Session options → Accelerator **GPU T4 x2**, then Save Version again |
| The version shows **error** | Open the version → **Logs**; send Neill the last 30 lines |
| E finished but `rq2_E.zip` has no `adapter` folder | Training failed: send `train.log` (it's in the zip) |
| Fewer than 137 lines from `wc -l` | Send the zip anyway; finished cases are kept |
| It runs much longer than the times above (2×) | Leave it; tell Neill. Kaggle stops a version at 12 hours |

## What happens with the results
Neill scores them with `python -m eval.score_extraction --system gemini=prefill --system base=runs/rq2_base --system tuned=runs/rq2_tuned`:
how many fact fields (notice date, hearing date given, order date, ...) each system gets right compared with
the human-checked facts, plus events and quote accuracy. If the trained model is good, a later run feeds its
extracted facts into NoticeCheck (judgment in, defect report out, no human-made facts).

---

## Notebook G: `nc-G-e2e`, end to end → download `e2e_G.zip` (about 3.5 h)
NoticeCheck (Qwen3-8B, same as the test runs) on facts **extracted by a model** instead of checked by us:
job 1 uses the fine-tuned extractor's facts (from E), job 2 the untrained extractor's facts (from F).
Judgment in, defect report out, no human-made facts. Uses the Ollama setup from the main runs, not Unsloth.

**G Cell 1** (two model servers, one per GPU, about 5 minutes):
```python
!apt-get -qq update && apt-get -qq install -y zstd pciutils lshw poppler-utils zip > /dev/null
!curl -fsSL https://ollama.com/install.sh | sh
import os, subprocess, time, json
base = dict(os.environ, OLLAMA_CONTEXT_LENGTH="16384", OLLAMA_NUM_PARALLEL="2", OLLAMA_KEEP_ALIVE="-1")
servers = [subprocess.Popen(["ollama", "serve"], env=dict(base, CUDA_VISIBLE_DEVICES=str(g), OLLAMA_HOST=f"127.0.0.1:{11434 + g}"), stdout=open(f"/kaggle/working/ollama_{g}.log", "w"), stderr=subprocess.STDOUT) for g in (0, 1)]
time.sleep(10)
!ollama pull qwen3:8b
!ollama list
!OLLAMA_HOST=127.0.0.1:11435 ollama list
```
Both `ollama list` lines must show `qwen3:8b`.

**G Cell 2** (code and tools, about 15 minutes):
```python
!git clone -b noticecheck-core https://github.com/neill-nil/gst-scn-compliance-audit.git /kaggle/working/repo
%cd /kaggle/working/repo
!git log --oneline -1
!pip -q install jsonschema pytest
os.environ.update(LOCAL_BASE_URL="http://localhost:11434/v1", LOCAL_MODEL="qwen3:8b", LOCAL_RPM="0")
!python scripts/fetch_data.py
!python -m src.tools.caselaw
!python -m pytest -q tests/test_tools.py
!wc -l runs/rq2_tuned/checker_full_record.jsonl runs/rq2_base/checker_full_record.jsonl
```
The last line must show 137 for both files.

**G Cell 3:**
```python
# job 1 (fine-tuned extractor's facts) on GPU 0, job 2 (untrained extractor's facts) on GPU 1; each split in two halves
jobs = [("runs/rq2_tuned/checker_full_record.jsonl", "e2e_nc_tuned"), ("runs/rq2_base/checker_full_record.jsonl", "e2e_nc_base")]
cnrs = [json.loads(l)["cnr"] for l in open(jobs[0][0])]
halves = {"a": cnrs[:69], "b": cnrs[69:]}
procs = [subprocess.Popen(["python", "-m", "src.noticecheck.cli", "--inputs", inp, "--config", "configs/nc_full.json", "--run-id", f"{rid}_{h}", "--seed", "1", "--cnr", *ids], env=dict(os.environ, LOCAL_BASE_URL=f"http://localhost:{11434 + k}/v1"), stdout=open(f"{rid}_{h}.log", "w"), stderr=subprocess.STDOUT) for k, (inp, rid) in enumerate(jobs) for h, ids in halves.items()]
while any(p.poll() is None for p in procs): time.sleep(60)
!tail -n 2 *.log
!zip -qr /kaggle/working/e2e_G.zip runs/e2e_nc_* *.log /kaggle/working/ollama_0.log /kaggle/working/ollama_1.log
%cd /kaggle/working
!rm -rf /kaggle/working/repo
!ls -la /kaggle/working
```

---

## Notebook H: `nc-H-fresh`, the full system on 20 fresh cases → download `fresh_H.zip` (about 1 h)
20 judgments nobody has reviewed, trained on or used (`data/splits/fresh.txt`, picked on 14 Nov after the system
was frozen). The fine-tuned extractor reads each judgment, then NoticeCheck (Qwen) checks the facts. The team
reviews the same 20 cases separately (review_queue_v3.csv) without seeing these outputs; then we score.

**Before H, once: upload the fine-tuned weights as a private Kaggle dataset** (they are too big for GitHub)
1. kaggle.com → **Create → New Dataset**.
2. Drag in **all files** from the folder `runs/rq2_lora/adapter` on your laptop (adapter_model.safetensors,
   adapter_config.json, tokenizer.json, tokenizer_config.json, chat_template.jinja, README.md).
3. Title **noticecheck-adapter**, visibility **Private** → **Create**. Wait until it says the upload is complete.
4. In notebook H (before Save Version): right-hand panel → **Add Input** → **Your Work → Datasets** →
   **noticecheck-adapter** → **Add**.

**H Cell 1** (libraries and Ollama, about 6 minutes):
```python
!apt-get -qq update && apt-get -qq install -y zstd pciutils lshw poppler-utils zip > /dev/null
!pip install -q unsloth jsonschema pytest
!curl -fsSL https://ollama.com/install.sh | sh
!python -c "import unsloth, torch; print('unsloth', unsloth.__version__, 'GPUs', torch.cuda.device_count())"
```

**H Cell 2** (code, judgments, adapter, model download, about 10 minutes):
```python
import os, subprocess, time, json, glob
!git clone -b noticecheck-core https://github.com/neill-nil/gst-scn-compliance-audit.git /kaggle/working/repo
%cd /kaggle/working/repo
!git log --oneline -1
!python scripts/fetch_data.py --reasoned-only
!python -m scripts.build_rq2_data
!python -m src.tools.caselaw
!python -m pytest -q tests/test_tools.py
ADAPTER = os.path.dirname(glob.glob("/kaggle/input/**/adapter_config.json", recursive=True)[0])
print("adapter:", ADAPTER, os.listdir(ADAPTER))
!python -c "from huggingface_hub import snapshot_download; snapshot_download('unsloth/Qwen3-8B-unsloth-bnb-4bit')"
```
`build_rq2_data` must print `fresh: 20 prompts`, and the adapter line must list `adapter_model.safetensors`.

**H Cell 3** (extract with the fine-tuned model, then NoticeCheck; about 40 minutes):
```python
# 1) fine-tuned extractor on the 20 fresh judgments, half on each GPU
procs = [subprocess.Popen(["python", "-m", "src.rq2.extract", "--run-id", "rq2_fresh", "--split", "fresh", "--adapter", ADAPTER, "--shard", str(k), "--shards", "2"], env=dict(os.environ, CUDA_VISIBLE_DEVICES=str(k)), stdout=open(f"extract_fresh_{k}.log", "w"), stderr=subprocess.STDOUT) for k in (0, 1)]
while any(p.poll() is None for p in procs): time.sleep(30)
!tail -n 2 extract_fresh_*.log
!python -m scripts.build_e2e_inputs --run runs/rq2_fresh
# 2) two Ollama servers (one per GPU) and NoticeCheck on the extracted facts
base = dict(os.environ, OLLAMA_CONTEXT_LENGTH="16384", OLLAMA_NUM_PARALLEL="2", OLLAMA_KEEP_ALIVE="-1")
servers = [subprocess.Popen(["ollama", "serve"], env=dict(base, CUDA_VISIBLE_DEVICES=str(g), OLLAMA_HOST=f"127.0.0.1:{11434 + g}"), stdout=open(f"/kaggle/working/ollama_{g}.log", "w"), stderr=subprocess.STDOUT) for g in (0, 1)]
time.sleep(10)
!ollama pull qwen3:8b
os.environ.update(LOCAL_MODEL="qwen3:8b", LOCAL_RPM="0")
cnrs = [json.loads(l)["cnr"] for l in open("runs/rq2_fresh/checker_full_record.jsonl")]
parts = [cnrs[i::4] for i in range(4)]
procs = [subprocess.Popen(["python", "-m", "src.noticecheck.cli", "--inputs", "runs/rq2_fresh/checker_full_record.jsonl", "--config", "configs/nc_full.json", "--run-id", f"fresh_nc_{i}", "--seed", "1", "--cnr", *ids], env=dict(os.environ, LOCAL_BASE_URL=f"http://localhost:{11434 + i % 2}/v1"), stdout=open(f"fresh_nc_{i}.log", "w"), stderr=subprocess.STDOUT) for i, ids in enumerate(parts)]
while any(p.poll() is None for p in procs): time.sleep(30)
!tail -n 2 fresh_nc_*.log
!zip -qr /kaggle/working/fresh_H.zip runs/rq2_fresh runs/fresh_nc_* extract_fresh_*.log fresh_nc_*.log
%cd /kaggle/working
!rm -rf /kaggle/working/repo
!ls -la /kaggle/working
```
