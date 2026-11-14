# Synthetic stress set on Kaggle: notebook S

**What this is.** Our proposal promised a *synthetic stress set*: proceeding records we build ourselves, with exactly
one procedural defect planted, plus clean records with no defect at all. On real judgments many facts are missing,
so every system often says "can't tell". Here every fact is stated, so the test answers two questions the real
data cannot:
1. When the facts are there, does the system catch the defect?
2. On clean, valid proceedings, how often does it raise a false alarm?

**The set:** 100 records (`data/synthetic/`, built by `python -m scripts.make_synthetic`, already in the repo):
8 each for 7 defect types (no hearing, unsigned notice or order, summary-only notice, notice not served, time limit
missed, reply ignored, order without reasons) = 56 with a defect, and 44 clean.

**This notebook runs** NoticeCheck (Qwen3-8B, same settings as the test runs) and baseline B1 (the same Qwen3-8B,
record only) on all 100. B0 (rules), NoticeCheck with Gemini, and B2 (Gemini) are run on a laptop, so they are not
needed here.

| Notebook | Name | Time | Download |
|---|---|---|---|
| S | `nc-S-synthetic` | about 2 hours (20 min setup, ~70 min NoticeCheck, ~30 min B1) | `syn_S.zip` |

## How to run (same as before)
1. kaggle.com → **Create → New Notebook**. Right-hand panel → Session options: **GPU T4 x2**, Internet **On**.
2. Delete the starter cell, add 3 code cells, paste **Cell 1**, **Cell 2**, **Cell 3** below in that order.
   **Each cell's first line must start at the very left edge** (no spaces before it), or the cell fails.
3. Rename the notebook to `nc-S-synthetic`.
4. **Save Version → Save & Run All (Commit) → Save.** You can close the tab.
5. When the version shows **complete**: open it → **Output** → download `syn_S.zip` → send it to Neill.

---

## Cell 1: two model servers, one per GPU (about 5 minutes)
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

## Cell 2: code and tools (about 15 minutes)
```python
!git clone -b noticecheck-core https://github.com/neill-nil/gst-scn-compliance-audit.git /kaggle/working/repo
%cd /kaggle/working/repo
!git log --oneline -1
!pip -q install jsonschema pytest
os.environ.update(LOCAL_BASE_URL="http://localhost:11434/v1", LOCAL_MODEL="qwen3:8b", LOCAL_RPM="0")
!python scripts/fetch_data.py                 # all in-scope texts: the case-law index needs them (10-15 min)
!python -m src.tools.caselaw
!python -m pytest -q tests/test_tools.py      # all must pass
!wc -l data/synthetic/full_record.jsonl       # must be 100
```

## Cell 3: NoticeCheck, then B1 (about 1.5 hours)
```python
# 1) NoticeCheck on the 100 synthetic records: 4 quarters, 2 per GPU
cnrs = [json.loads(l)["cnr"] for l in open("data/synthetic/full_record.jsonl")]
parts = [cnrs[i::4] for i in range(4)]
procs = [subprocess.Popen(["python", "-m", "src.noticecheck.cli", "--inputs", "data/synthetic/full_record.jsonl", "--config", "configs/nc_full.json", "--run-id", f"syn_nc_{i}", "--seed", "1", "--cnr", *ids], env=dict(os.environ, LOCAL_BASE_URL=f"http://localhost:{11434 + i % 2}/v1"), stdout=open(f"syn_nc_{i}.log", "w"), stderr=subprocess.STDOUT) for i, ids in enumerate(parts)]
while any(p.poll() is None for p in procs): time.sleep(60)
!tail -n 2 syn_nc_*.log
# 2) B1 on the same records: 4 quarters, 2 per GPU
lines = open("data/synthetic/full_record.jsonl").readlines()
for i in range(4): open(f"/kaggle/working/syn_b1_in_{i}.jsonl", "w").writelines(lines[i::4])
os.makedirs("runs/syn_b1", exist_ok=True)
procs = [subprocess.Popen(["python", "-m", "src.baselines.b1_plain", "--input", f"/kaggle/working/syn_b1_in_{i}.jsonl", "--out", f"runs/syn_b1/part_{i}.jsonl", "--run-id", "syn_b1", "--model", "qwen3:8b", "--seed", "1"], env=dict(os.environ, LOCAL_BASE_URL=f"http://localhost:{11434 + i % 2}/v1"), stdout=open(f"syn_b1_{i}.log", "w"), stderr=subprocess.STDOUT) for i in range(4)]
while any(p.poll() is None for p in procs): time.sleep(60)
!tail -n 2 syn_b1_*.log
!cat runs/syn_b1/part_*.jsonl > runs/syn_b1/outputs.jsonl
!wc -l runs/syn_nc_*/outputs.jsonl runs/syn_b1/outputs.jsonl
!zip -qr /kaggle/working/syn_S.zip runs/syn_nc_* runs/syn_b1 syn_nc_*.log syn_b1_*.log /kaggle/working/ollama_0.log /kaggle/working/ollama_1.log
%cd /kaggle/working
!rm -rf /kaggle/working/repo
!ls -la /kaggle/working
```
The `wc -l` line should show 25 for each `syn_nc_*` folder and 100 for `syn_b1`.

## If something goes wrong
| What you see | What to do |
|---|---|
| A cell fails with `IndentationError` | The cell's first line had spaces before it. Remove them and Save Version again |
| `ollama list` doesn't show `qwen3:8b` twice | Session options → **GPU T4 x2**, then Save Version again |
| A test fails in Cell 2 | Check Cell 2 has `fetch_data.py` **without** `--reasoned-only`; send Neill the last lines |
| The version shows **error** | Open the version → **Logs**; send Neill the last 30 lines |
| Fewer lines than expected from `wc -l` | Send the zip anyway; finished cases are kept |

## What happens with the results
Neill merges the four NoticeCheck parts into `runs/syn_nc` and scores everything with
`python -m eval.score --gold data/synthetic/records.jsonl --split data/splits/synthetic.txt --run runs/syn_nc --view full_record --no-unargued-as-rejected`,
then adds the table to `docs/results/RESULTS.md` (section "Synthetic stress set").
