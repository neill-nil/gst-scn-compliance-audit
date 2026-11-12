# Running NoticeCheck and B1 on Kaggle (background runs)

NoticeCheck and baseline B1 both use Qwen3-8B (Ollama, 4-bit), which needs Kaggle's free GPUs. Every run here
is a **background run**: you click "Save & Run All", and Kaggle runs the notebook on its own servers. You can close
the browser and turn off your laptop. When it finishes, you download one zip file and send it to Neill.

There are two sessions:
- **Session 1 (12 Nov):** notebook A (NoticeCheck dev run) and notebook B (B1 re-run).
- **Session 2 (13 Nov, only after Neill says "frozen"):** notebooks C1, C2, D1, D2 (the test runs that go in the paper).

Each notebook has exactly **3 cells**. Cell 2 is the same in every notebook; Session 2 uses its own Cell 1; Cell 3 changes per notebook.

---

## How to run a notebook (same steps every time)
1. kaggle.com → **Create → New Notebook**.
2. Right-hand panel → **Session options**: Accelerator **GPU T4 x2**, Internet **On**.
   (Internet needs a phone-verified Kaggle account.)
3. Delete the starter cell. Add 3 code cells and paste **Cell 1**, **Cell 2** and the notebook's **Cell 3** below, in that order.
4. Rename the notebook (top left) to the name given below, e.g. `nc-A-dev`.
5. Top right → **Save Version** → choose **Save & Run All (Commit)** → **Save**.
6. You can now close the tab. Progress: kaggle.com → **Your Work** → the notebook → **Versions**.
7. When the version shows **complete** (green tick): open it → **Output** tab (or "Data" → Output files) →
   download the zip named below → send it to Neill.

Don't click "Run All" in the editor: that runs it in the foreground, and it stops when you leave.

---

## Cell 1: model server (same in every notebook, about 5 minutes)
```python
!apt-get -qq update && apt-get -qq install -y zstd pciutils lshw poppler-utils zip > /dev/null
!curl -fsSL https://ollama.com/install.sh | sh
import os, subprocess, time
os.environ.update(OLLAMA_CONTEXT_LENGTH="16384", OLLAMA_NUM_PARALLEL="2", OLLAMA_KEEP_ALIVE="-1")
subprocess.Popen(["ollama", "serve"], stdout=open("/kaggle/working/ollama.log", "w"), stderr=subprocess.STDOUT)
time.sleep(10)
!ollama pull qwen3:8b
!ollama list
```

## Cell 2: code, judgments and case-law index (same in every notebook, about 15 minutes)
```python
!git clone -b noticecheck-core https://github.com/neill-nil/gst-scn-compliance-audit.git /kaggle/working/repo
%cd /kaggle/working/repo
!git log --oneline -1
!pip -q install jsonschema pytest
os.environ.update(LOCAL_BASE_URL="http://localhost:11434/v1", LOCAL_MODEL="qwen3:8b", LOCAL_RPM="0")
!python scripts/fetch_data.py                 # all in-scope judgments, checked against the manifest
!python -m src.tools.caselaw                  # builds the precedent index (seconds)
!python -m pytest -q tests/test_tools.py      # all must pass
!python -m scripts.build_dev_inputs           # 49 dev cases
!python -m src.baselines.inputs --gold data/gold/records.jsonl --out data/interim/inputs   # 137 test + held-out cases
```

---

## Session 1 (12 Nov): notebooks A and B
Start **A first**. Start **B right after** if Kaggle lets you run a second GPU session at once; if it refuses,
start B as soon as A is complete. Together they use about 4–5 of your 30 weekly GPU hours.

### Notebook A: `nc-A-dev`, NoticeCheck dev run (about 1.5 hours) → download `dev_full_s1.zip`
**Send this one to Neill as soon as it's done**: tuning NoticeCheck starts from it.

Cell 3:
```python
!python -m src.noticecheck.cli --inputs data/interim/dev/full_record.jsonl --config configs/nc_full.json --run-id dev_full_s1 > dev_full_s1.log 2>&1
!tail -3 dev_full_s1.log
!python -m eval.score --gold data/interim/dev/records.jsonl --run runs/dev_full_s1 --split data/interim/dev/dev.txt --view full_record --no-unargued-as-rejected > dev_score.txt 2>&1
!cat dev_score.txt
!zip -qr /kaggle/working/dev_full_s1.zip runs/dev_full_s1 dev_full_s1.log dev_score.txt runs/llm_calls.jsonl /kaggle/working/ollama.log
%cd /kaggle/working
!rm -rf /kaggle/working/repo    # only the zip and the log are kept as output
!ls -la /kaggle/working
```

### Notebook B: `nc-B-b1`, B1 re-run on the new test set (about 2.5–3 hours) → download `b1_v2.zip`
Cell 3:
```python
os.makedirs("runs/b1_v2", exist_ok=True)
lines = open("data/interim/inputs/full_record.jsonl").readlines()   # two halves, so both model slots are busy
open("/kaggle/working/b1_a.jsonl", "w").writelines(lines[:69])
open("/kaggle/working/b1_b.jsonl", "w").writelines(lines[69:])
b1 = [subprocess.Popen(["python", "-m", "src.baselines.b1_plain", "--input", f"/kaggle/working/b1_{h}.jsonl",
                        "--out", f"runs/b1_v2/part_{h}.jsonl", "--run-id", "b1_v2", "--model", "qwen3:8b", "--seed", "1"],
                       stdout=open(f"b1_v2_{h}.log", "w"), stderr=subprocess.STDOUT) for h in ("a", "b")]
while any(p.poll() is None for p in b1):
    time.sleep(60)
!tail -2 b1_v2_a.log b1_v2_b.log
!cat runs/b1_v2/part_a.jsonl runs/b1_v2/part_b.jsonl > runs/b1_v2/full_record.jsonl
!wc -l runs/b1_v2/full_record.jsonl        # should be 137
!zip -qr /kaggle/working/b1_v2.zip runs/b1_v2 b1_v2_a.log b1_v2_b.log runs/llm_calls.jsonl /kaggle/working/ollama.log
%cd /kaggle/working
!rm -rf /kaggle/working/repo /kaggle/working/b1_a.jsonl /kaggle/working/b1_b.jsonl
!ls -la /kaggle/working
```

---

## Session 2 (13 Nov): notebooks C1, C2, D1, D2. Only after Neill says "frozen"
These are the runs reported in the paper. In Session 1 Kaggle used only one of the two GPUs, so Session 2
starts **two model servers, one per GPU**, and each notebook runs 2 jobs. That's **about 3–3.5 hours per notebook**.

**Order:** start C1 and C2 together (or one after the other if Kaggle allows only one GPU session), then D1 and D2.
All four need about 13 GPU hours; with Session 1 that's about 18 of the 30 weekly hours, so one account is enough.

Each notebook: Cell 1 is the **Session 2 Cell 1** below (not the Session 1 one), Cell 2 is the usual **Cell 2**,
and Cell 3 is the notebook's own cell. Then **Save Version → Save & Run All (Commit)**, as always.

### Session 2 Cell 1: two model servers, one per GPU (same in C1, C2, D1, D2)
```python
!apt-get -qq update && apt-get -qq install -y zstd pciutils lshw poppler-utils zip > /dev/null
!curl -fsSL https://ollama.com/install.sh | sh
import os, subprocess, time
base = dict(os.environ, OLLAMA_CONTEXT_LENGTH="16384", OLLAMA_NUM_PARALLEL="2", OLLAMA_KEEP_ALIVE="-1")
for gpu in (0, 1):
    subprocess.Popen(["ollama", "serve"], env=dict(base, CUDA_VISIBLE_DEVICES=str(gpu), OLLAMA_HOST=f"127.0.0.1:{11434 + gpu}"),
                     stdout=open(f"/kaggle/working/ollama_{gpu}.log", "w"), stderr=subprocess.STDOUT)
time.sleep(10)
!ollama pull qwen3:8b
!ollama list
!OLLAMA_HOST=127.0.0.1:11435 ollama list
```
Both `ollama list` lines must show `qwen3:8b`.

### Notebook C1: `nc-C1`, main system, runs 1 and 2 → download `test_C1.zip`
Cell 1: **Session 2 Cell 1** (above). Cell 2: the usual **Cell 2**. Cell 3:
```python
import json
jobs = [("nc_full", "full_record", 1), ("nc_full", "full_record", 2)]
cnrs = [json.loads(l)["cnr"] for l in open("data/interim/inputs/full_record.jsonl")]
halves = {"a": cnrs[:69], "b": cnrs[69:]}
procs = []
for k, (cfg, view, seed) in enumerate(jobs):          # job 1 on GPU 0, job 2 on GPU 1
    for h, ids in halves.items():                      # each job split in two, so each GPU serves 2 requests at a time
        rid = f"{cfg}_{view}_s{seed}_{h}"
        procs.append(subprocess.Popen(
            ["python", "-m", "src.noticecheck.cli", "--inputs", f"data/interim/inputs/{view}.jsonl",
             "--config", f"configs/{cfg}.json", "--run-id", rid, "--seed", str(seed), "--cnr", *ids],
            env=dict(os.environ, LOCAL_BASE_URL=f"http://localhost:{11434 + k}/v1"),
            stdout=open(f"{rid}.log", "w"), stderr=subprocess.STDOUT))
while any(p.poll() is None for p in procs):
    time.sleep(60)
!tail -n 2 *.log
!zip -qr /kaggle/working/test_C1.zip runs *.log /kaggle/working/ollama_0.log /kaggle/working/ollama_1.log -x 'runs/cache/*'
%cd /kaggle/working
!rm -rf /kaggle/working/repo
!ls -la /kaggle/working
```

### Notebook C2: `nc-C2`, main system run 3 + notice-only → download `test_C2.zip`
Cell 1: **Session 2 Cell 1** (above). Cell 2: the usual **Cell 2**. Cell 3:
```python
import json
jobs = [("nc_full", "full_record", 3), ("nc_full", "notice_only", 1)]
cnrs = [json.loads(l)["cnr"] for l in open("data/interim/inputs/full_record.jsonl")]
halves = {"a": cnrs[:69], "b": cnrs[69:]}
procs = []
for k, (cfg, view, seed) in enumerate(jobs):          # job 1 on GPU 0, job 2 on GPU 1
    for h, ids in halves.items():                      # each job split in two, so each GPU serves 2 requests at a time
        rid = f"{cfg}_{view}_s{seed}_{h}"
        procs.append(subprocess.Popen(
            ["python", "-m", "src.noticecheck.cli", "--inputs", f"data/interim/inputs/{view}.jsonl",
             "--config", f"configs/{cfg}.json", "--run-id", rid, "--seed", str(seed), "--cnr", *ids],
            env=dict(os.environ, LOCAL_BASE_URL=f"http://localhost:{11434 + k}/v1"),
            stdout=open(f"{rid}.log", "w"), stderr=subprocess.STDOUT))
while any(p.poll() is None for p in procs):
    time.sleep(60)
!tail -n 2 *.log
!zip -qr /kaggle/working/test_C2.zip runs *.log /kaggle/working/ollama_0.log /kaggle/working/ollama_1.log -x 'runs/cache/*'
%cd /kaggle/working
!rm -rf /kaggle/working/repo
!ls -la /kaggle/working
```

### Notebook D1: `nc-D1`, ablations: no tools, no retrieval → download `test_D1.zip`
Cell 1: **Session 2 Cell 1** (above). Cell 2: the usual **Cell 2**. Cell 3:
```python
import json
jobs = [("nc_no_tools", "full_record", 1), ("nc_no_retrieval", "full_record", 1)]
cnrs = [json.loads(l)["cnr"] for l in open("data/interim/inputs/full_record.jsonl")]
halves = {"a": cnrs[:69], "b": cnrs[69:]}
procs = []
for k, (cfg, view, seed) in enumerate(jobs):          # job 1 on GPU 0, job 2 on GPU 1
    for h, ids in halves.items():                      # each job split in two, so each GPU serves 2 requests at a time
        rid = f"{cfg}_{view}_s{seed}_{h}"
        procs.append(subprocess.Popen(
            ["python", "-m", "src.noticecheck.cli", "--inputs", f"data/interim/inputs/{view}.jsonl",
             "--config", f"configs/{cfg}.json", "--run-id", rid, "--seed", str(seed), "--cnr", *ids],
            env=dict(os.environ, LOCAL_BASE_URL=f"http://localhost:{11434 + k}/v1"),
            stdout=open(f"{rid}.log", "w"), stderr=subprocess.STDOUT))
while any(p.poll() is None for p in procs):
    time.sleep(60)
!tail -n 2 *.log
!zip -qr /kaggle/working/test_D1.zip runs *.log /kaggle/working/ollama_0.log /kaggle/working/ollama_1.log -x 'runs/cache/*'
%cd /kaggle/working
!rm -rf /kaggle/working/repo
!ls -la /kaggle/working
```

### Notebook D2: `nc-D2`, ablations: no verifier, no hand-off → download `test_D2.zip`
Cell 1: **Session 2 Cell 1** (above). Cell 2: the usual **Cell 2**. Cell 3:
```python
import json
jobs = [("nc_no_verifier", "full_record", 1), ("nc_no_handoff", "full_record", 1)]
cnrs = [json.loads(l)["cnr"] for l in open("data/interim/inputs/full_record.jsonl")]
halves = {"a": cnrs[:69], "b": cnrs[69:]}
procs = []
for k, (cfg, view, seed) in enumerate(jobs):          # job 1 on GPU 0, job 2 on GPU 1
    for h, ids in halves.items():                      # each job split in two, so each GPU serves 2 requests at a time
        rid = f"{cfg}_{view}_s{seed}_{h}"
        procs.append(subprocess.Popen(
            ["python", "-m", "src.noticecheck.cli", "--inputs", f"data/interim/inputs/{view}.jsonl",
             "--config", f"configs/{cfg}.json", "--run-id", rid, "--seed", str(seed), "--cnr", *ids],
            env=dict(os.environ, LOCAL_BASE_URL=f"http://localhost:{11434 + k}/v1"),
            stdout=open(f"{rid}.log", "w"), stderr=subprocess.STDOUT))
while any(p.poll() is None for p in procs):
    time.sleep(60)
!tail -n 2 *.log
!zip -qr /kaggle/working/test_D2.zip runs *.log /kaggle/working/ollama_0.log /kaggle/working/ollama_1.log -x 'runs/cache/*'
%cd /kaggle/working
!rm -rf /kaggle/working/repo
!ls -la /kaggle/working
```

---

## If something goes wrong
| What you see | What to do |
|---|---|
| Kaggle refuses a second GPU session | Wait for the first notebook to complete, then start the second |
| The version shows **error** or **cancelled** | Open the version → **Logs**, and send Neill a screenshot of the last lines. Then click Save Version again (it starts from scratch) |
| The version is complete but there's no zip under Output | Send Neill the version's **Logs** |
| "Internet is disabled" or the git clone fails | Session options → Internet **On** (phone-verify the account first) |
| It runs much longer than the times above (2×) | Leave it running and tell Neill; Kaggle stops a version at 12 hours anyway |
