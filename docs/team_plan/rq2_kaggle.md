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
while any(p.poll() is None for p in procs):
    time.sleep(60)
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
while any(p.poll() is None for p in procs):
    time.sleep(60)
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
