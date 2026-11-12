# Running NoticeCheck and B1 on Kaggle (background runs)

NoticeCheck and baseline B1 both use Qwen3-8B (Ollama, 4-bit), which needs Kaggle's free GPUs. Every run here
is a **background run**: you click "Save & Run All", and Kaggle runs the notebook on its own servers. You can close
the browser and turn off your laptop. When it finishes, you download one zip file and send it to Neill.

There are two sessions:
- **Session 1 (12 Nov):** notebook A (NoticeCheck dev run) and notebook B (B1 re-run).
- **Session 2 (13 Nov, only after Neill says "frozen"):** notebooks C and D (the test runs that go in the paper).

Each notebook has exactly **3 cells**. Cells 1 and 2 are the same in every notebook; only Cell 3 changes.

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

## Session 2 (13 Nov): notebooks C and D. Only after Neill says "frozen"
These are the runs reported in the paper. Each notebook runs 4 jobs, two at a time. Neill will confirm the time
per notebook after the dev run (current estimate: about 5 hours each). Run C and D on **two different accounts**
so each stays within its weekly GPU hours.

### Notebook C: `nc-C-main`, main system 3 times + notice-only → download `test_main.zip`
Cell 3:
```python
jobs = [("nc_full", "full_record", 1), ("nc_full", "full_record", 2),
        ("nc_full", "full_record", 3), ("nc_full", "notice_only", 1)]
def run(cfg, view, seed):
    rid = f"{cfg}_{view}_s{seed}"
    return subprocess.Popen(["python", "-m", "src.noticecheck.cli", "--inputs", f"data/interim/inputs/{view}.jsonl",
                             "--config", f"configs/{cfg}.json", "--run-id", rid, "--seed", str(seed)],
                            stdout=open(f"{rid}.log", "w"), stderr=subprocess.STDOUT)
for i in range(0, len(jobs), 2):
    ps = [run(*j) for j in jobs[i:i + 2]]
    while any(p.poll() is None for p in ps):
        time.sleep(60)
    print(time.strftime("%H:%M"), "done:", jobs[i:i + 2], [p.returncode for p in ps], flush=True)
!zip -qr /kaggle/working/test_main.zip runs *.log -x 'runs/cache/*'
%cd /kaggle/working
!rm -rf /kaggle/working/repo
!ls -la /kaggle/working
```

### Notebook D: `nc-D-ablations`, the four ablations → download `test_ablations.zip`
Cell 3: the same as notebook C, with only the first line and the zip name changed:
```python
jobs = [("nc_no_tools", "full_record", 1), ("nc_no_retrieval", "full_record", 1),
        ("nc_no_verifier", "full_record", 1), ("nc_no_handoff", "full_record", 1)]
def run(cfg, view, seed):
    rid = f"{cfg}_{view}_s{seed}"
    return subprocess.Popen(["python", "-m", "src.noticecheck.cli", "--inputs", f"data/interim/inputs/{view}.jsonl",
                             "--config", f"configs/{cfg}.json", "--run-id", rid, "--seed", str(seed)],
                            stdout=open(f"{rid}.log", "w"), stderr=subprocess.STDOUT)
for i in range(0, len(jobs), 2):
    ps = [run(*j) for j in jobs[i:i + 2]]
    while any(p.poll() is None for p in ps):
        time.sleep(60)
    print(time.strftime("%H:%M"), "done:", jobs[i:i + 2], [p.returncode for p in ps], flush=True)
!zip -qr /kaggle/working/test_ablations.zip runs *.log -x 'runs/cache/*'
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
