# Running NoticeCheck on Kaggle

NoticeCheck runs on the same Qwen3-8B (Ollama, 4-bit) as baseline B1, so the comparison is fair. A run takes about 2–3 model calls per case.

There are two stages:
- **Stage A, dev:** tuning runs on the dev cases. Run these whenever Neill asks.
- **Stage B, test:** the reported runs. **Only after Neill says the system is frozen.** Prompts and check cards must not change after a test run.

## Setup (once per session, about 20 minutes)
Notebook: **GPU T4 x2**, **Internet on**, Persistence "Files only".

**Cell 1: model server**, the same as the B1 guide:
```python
!apt-get -qq update && apt-get -qq install -y zstd pciutils lshw poppler-utils > /dev/null
!curl -fsSL https://ollama.com/install.sh | sh
import os, subprocess, time
os.environ.update(OLLAMA_CONTEXT_LENGTH="16384", OLLAMA_NUM_PARALLEL="2", OLLAMA_KEEP_ALIVE="-1")
subprocess.Popen(["ollama", "serve"], stdout=open("/kaggle/working/ollama.log", "w"), stderr=subprocess.STDOUT)
time.sleep(10)
!ollama pull qwen3:8b
```

**Cell 2: code, data and the case-law index** (the download takes 10–15 minutes):
```python
!git clone -b noticecheck-core https://github.com/neill-nil/gst-scn-compliance-audit.git /kaggle/working/repo
%cd /kaggle/working/repo
!pip -q install jsonschema pytest
os.environ.update(LOCAL_BASE_URL="http://localhost:11434/v1", LOCAL_MODEL="qwen3:8b", LOCAL_RPM="0")
!python scripts/fetch_data.py                 # all in-scope judgments, checked against the manifest
!python -m src.tools.caselaw                  # builds the precedent index (seconds)
!python -m pytest -q tests/test_tools.py      # all must pass
```

## Stage A: dev runs
```python
!python -m scripts.build_dev_inputs
!python -m src.noticecheck.cli --inputs data/interim/dev/full_record.jsonl --config configs/nc_full.json --run-id dev_full_s1
!python -m eval.score --gold data/interim/dev/records.jsonl --run runs/dev_full_s1 --split data/interim/dev/dev.txt --view full_record --no-unargued-as-rejected
```
Send Neill the `runs/dev_full_s1` folder (zip it), not just the score. The traces are what tuning needs.

## Stage B: test runs (after the freeze)
Build the inputs, then run each configuration. Two runs can share the server (it serves 2 requests in parallel).
```python
!python -m src.baselines.inputs --gold data/gold/records.jsonl --out data/interim/inputs
jobs = [  # (config, view, seed): main system on both views, 3 seeds; ablations on full_record
    *[("nc_full", v, s) for v in ("full_record", "notice_only") for s in (1, 2, 3)],
    *[(f"nc_no_{a}", "full_record", s) for a in ("tools", "retrieval", "verifier", "handoff") for s in (1, 2, 3)],
]
def run(cfg, view, seed):
    rid = f"{cfg}_{view}_s{seed}"
    return subprocess.Popen(["python", "-m", "src.noticecheck.cli", "--inputs", f"data/interim/inputs/{view}.jsonl",
                             "--config", f"configs/{cfg}.json", "--run-id", rid, "--seed", str(seed)],
                            stdout=open(f"{rid}.log", "w"), stderr=subprocess.STDOUT)
```
Then, in a new cell, run the jobs **two at a time**:
```python
for i in range(0, len(jobs), 2):
    ps = [run(*j) for j in jobs[i:i + 2]]
    while any(p.poll() is None for p in ps): time.sleep(60)
    print(time.strftime("%H:%M"), "done:", jobs[i:i + 2], [p.returncode for p in ps], flush=True)
```
Each job resumes where it stopped (finished cases are skipped), so a cut session loses nothing: re-run Cells 1–2 and the job cell.

**Splitting the work across accounts:** each account takes a slice, e.g. `jobs[0:6]`, `jobs[6:12]`, `jobs[12:18]`. That's about 18 jobs × ~150 cases, roughly 18 GPU-hours in total.

**Send back:** zip `runs/` (outputs, traces, experiment.json) plus `runs/llm_calls.jsonl`.

## If something fails
| What you see | What to do |
|---|---|
| `STOPPED at ...: local unreachable` | The model server died: re-run Cell 1, then the same job cell |
| a test in `tests/test_tools.py` fails | Stop and send Neill the output |
| A case takes more than 5 minutes | Check `!tail -5 /kaggle/working/ollama.log`; `ollama ps` must show `100% GPU` |
