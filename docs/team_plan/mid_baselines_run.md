# Running baseline B1 (Qwen3-8B) on Kaggle

**What this is.** B1 is our main baseline: the same small model as NoticeCheck (Qwen3-8B), given only the facts of each case and asked, for each of 13 procedural defect types, "defect / no defect / can't tell". It runs on our 54 gold cases twice:
- `full_record`: all the facts.
- `notice_only`: only the notice, which tests whether it admits "can't tell".

That makes 108 model calls. You don't need to understand the code: the steps below are copy-paste.

**Time:** about 10 minutes of setup, then about 40–60 minutes of running, which you can leave unattended. It uses about 1.5 h of your weekly Kaggle GPU quota (30 h).

**What you send back at the end:** one file, `b1_results.zip` (step 7).

---

## 1. Kaggle account (once)
1. Log in at https://www.kaggle.com.
2. **Verify your phone number:** profile picture → Settings → Phone verification. Without it, notebooks have no internet and no GPU.

## 2. Create the notebook
1. Click **+ Create** → **New Notebook**.
2. In the right-hand panel (open it with the `>|` icon if hidden), under **Session options**:
   - **Accelerator:** `GPU T4 x2`.
   - **Internet:** `On`.
   - **Persistence:** `Files only` (optional; it keeps outputs if the session restarts).
3. Delete the starter cell. You'll add the cells below one at a time: click **+ Code**, paste, then press **Shift+Enter** to run. Wait for each cell to finish before running the next.

## 3. Cell 1: start the model server (about 5 minutes)
```python
!apt-get -qq update && apt-get -qq install -y zstd pciutils lshw > /dev/null
!curl -fsSL https://ollama.com/install.sh | sh
import os, subprocess, time
os.environ.update(OLLAMA_CONTEXT_LENGTH="16384", OLLAMA_NUM_PARALLEL="2", OLLAMA_KEEP_ALIVE="-1")
subprocess.Popen(["ollama", "serve"], stdout=open("/kaggle/working/ollama.log", "w"), stderr=subprocess.STDOUT)
time.sleep(10)
!ollama pull qwen3:8b
!nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv
```
**Expected:** the download ends with `success`, and `nvidia-smi` lists two `Tesla T4`.

## 4. Cell 2: get our code and build the inputs (about 1 minute)
```python
!git clone -b mid-baselines https://github.com/neill-nil/gst-scn-compliance-audit.git /kaggle/working/repo
%cd /kaggle/working/repo
!pip -q install jsonschema
os.environ.update(LOCAL_BASE_URL="http://localhost:11434/v1", LOCAL_MODEL="qwen3:8b", LOCAL_RPM="0")
!python -m src.baselines.inputs --gold data/gold/records.jsonl --out data/interim/inputs
```
**Expected:** three lines, `wrote 54 cases to data/interim/inputs/full_record.jsonl`, then the same for `notice_only` and `raw_text`.

The inputs come from `data/gold/records.jsonl` (the 54 reviewed cases). The court's findings, the outcome and the court's reasoning are removed, so the model only sees facts.

## 5. Cell 3: test one case (about 1 minute)
```python
!head -1 data/interim/inputs/full_record.jsonl > /tmp/one.jsonl
!python -m src.baselines.b1_plain --input /tmp/one.jsonl --out /tmp/one/outputs.jsonl --model qwen3:8b
!head -c 1200 /tmp/one/outputs.jsonl
!ollama ps
```
**Expected:**
- `wrote 1 outputs`.
- The printed text contains `"findings": [{"type": "hearing_75_4", "verdict": ...` with several entries.
- `ollama ps` shows `qwen3:8b` with **`100% GPU`**.

**Stop and message Neill if:**
- `"findings": []` is empty. The model's answer couldn't be read.
- `ollama ps` says `CPU`. The GPU isn't being used, and the run would take many hours.

## 6. Cell 4: the full run (about 40–60 minutes, leave it running)
```python
procs = [subprocess.Popen(["python", "-m", "src.baselines.b1_plain", "--input", f"data/interim/inputs/{v}.jsonl",
                           "--out", f"runs/b1_{v}/outputs.jsonl", "--model", "qwen3:8b", "--seed", "1"],
                          stdout=open(f"b1_{v}.log", "w"), stderr=subprocess.STDOUT)
         for v in ("full_record", "notice_only")]
while any(p.poll() is None for p in procs):
    time.sleep(60)
    done = len(os.listdir("runs/cache")) if os.path.isdir("runs/cache") else 0
    print(time.strftime("%H:%M"), done, "of about 109 calls done", flush=True)
print("exit codes:", [p.returncode for p in procs], "(both should be 0)")
!tail -2 b1_full_record.log b1_notice_only.log
```
**Expected:** the count goes up by about 2–4 every minute. At the end, `exit codes: [0, 0]`, and each log ends with `wrote 54 outputs`.

**If the session disconnects or the cell stops part-way,** re-run Cells 1, 2 and 4. Finished calls are saved in `runs/cache`, so it only redoes the missing ones. This only works if Persistence was on; otherwise it starts over.

## 7. Cell 5: score it and package the results
```python
!mkdir -p runs/b1 && cat runs/b1_full_record/outputs.jsonl runs/b1_notice_only/outputs.jsonl > runs/b1/outputs.jsonl
!python -m eval.score --gold data/gold/records.jsonl --run runs/b1 --split test --no-unargued-as-rejected
!cd runs && zip -qr /kaggle/working/b1_results.zip b1 b1_full_record b1_notice_only llm_calls.jsonl
!ls -la /kaggle/working/b1_results.zip
```
**Expected:** a summary per view, e.g. `defects overall: P=... R=... F1=... FA_rate=...` and `cant_tell rate` for `notice_only`, then the zip file listed.

**Send back:**
1. **`b1_results.zip`.** Right-hand panel → **Output** (`/kaggle/working`) → the `⋮` next to the file → **Download**. Send it to Neill.
2. A screenshot or copy of the Cell 5 printout.

The zip contains:
- the model's answers for all 108 calls (`outputs.jsonl`);
- the score (`score_test.json`);
- the call log with tokens and seconds per call (`llm_calls.jsonl`), for the cost table.

**When you're done:** click **Stop session** (top right) so the GPU quota stops counting.

---

## Problems
| What you see | What to do |
|---|---|
| `curl: ... Could not resolve host` / `pip` can't download | Internet is off. Turn it on in Session options (needs phone verification). |
| `requires zstd` during the Ollama install | Cell 1's first line didn't run. Run it again. |
| `ollama ps` shows `CPU`, or calls take minutes each | Accelerator isn't `GPU T4 x2`. Change it (the session restarts), then re-run from Cell 1. |
| `local unreachable at http://localhost:11434/v1` | The model server stopped. Re-run Cell 1 (the model download is skipped if already there), then the cell that failed. |
| `local HTTP 404 ... model "qwen3:8b" not found` | `ollama pull qwen3:8b` didn't finish. Run it again. |
| `fatal: destination path ... already exists` when re-running Cell 2 | Fine: the code is already there. The rest of the cell still runs. |
| Count stuck for more than 5 minutes | Check `!tail -5 /kaggle/working/ollama.log` and `!tail -5 b1_full_record.log`, and send them to Neill. |

## Settings, for the write-up
- Model: `qwen3:8b` from Ollama (Qwen3-8B, 4-bit Q4_K_M).
- Temperature 0, seed 1, thinking off (`/no_think`).
- Context 16k tokens, 2 requests in parallel on 2× T4.
- Prompt and parsing are in `src/baselines/common.py`; the model call is in `src/llm.py` and `src/common/llm.py`.
- Scoring (`--no-unargued-as-rejected`): only complaints actually argued in the case are scored, and gold `not_decided` is never scored.

---

## B2 (Neill runs this locally; not part of the Kaggle job)
B2 is a frontier model (Gemini 3.5 Flash Lite) given the facts plus the statute text. The text is CGST Act ss.73, 74, 75, 168A and 169, verbatim from the official India Code PDF (sha256 in `data/corpus/provisions_b2.json`, matching `corpus/SOURCES.md`), with amendment footnotes and page numbers removed.
```
python -m src.baselines.inputs --gold data/gold/records.jsonl --out data/interim/inputs
python -m src.baselines.b2_frontier --input data/interim/inputs/full_record.jsonl --out runs/b2_full_record/outputs.jsonl --provisions data/corpus/provisions_b2.json
python -m src.baselines.b2_frontier --input data/interim/inputs/notice_only.jsonl --out runs/b2_notice_only/outputs.jsonl --provisions data/corpus/provisions_b2.json
```
Caveat: Gemini also drafted the gold records before review, so B2 may have a home advantage.
