# Mid baselines: how to run B1 and B2 on the 54 gold cases

Branch `mid-baselines` = main + role 4's eval code (`r4-eval`) + `src/llm.py`, which connects the baselines to `src/common/llm.py`. Every system sees the same inputs, built from `data/gold/records.jsonl` with findings, outcome and court reasoning removed. Two views:
- `full_record`: all the facts.
- `notice_only`: only the notice, which tests "can't tell".

## B1: Qwen3-8B on Kaggle (about 1 hour)
Notebook settings: **GPU T4 x2**, **Internet on**. Run these cells in order.

**Cell 1: model server (about 5 minutes)**
```python
!curl -fsSL https://ollama.com/install.sh | sh
import os, subprocess, time
os.environ.update(OLLAMA_CONTEXT_LENGTH="16384", OLLAMA_NUM_PARALLEL="2", OLLAMA_KEEP_ALIVE="-1")
subprocess.Popen(["ollama", "serve"], stdout=open("/kaggle/working/ollama.log", "w"), stderr=subprocess.STDOUT)
time.sleep(5)
!ollama pull qwen3:8b
```

**Cell 2: code and inputs**
```python
!git clone -b mid-baselines https://github.com/neill-nil/gst-scn-compliance-audit.git /kaggle/working/repo
%cd /kaggle/working/repo
!pip -q install jsonschema
os.environ.update(LOCAL_BASE_URL="http://localhost:11434/v1", LOCAL_MODEL="qwen3:8b", LOCAL_RPM="0")
!python -m src.baselines.inputs --gold data/gold/records.jsonl --out data/interim/inputs
```

**Cell 3: one-case test.** It should print findings with verdicts, not `[]`.
```python
!head -1 data/interim/inputs/full_record.jsonl > /tmp/one.jsonl
!python -m src.baselines.b1_plain --input /tmp/one.jsonl --out /tmp/one/outputs.jsonl --model qwen3:8b
!head -c 800 /tmp/one/outputs.jsonl
```

**Cell 4: both views in parallel (about 40–60 minutes)**
```python
procs = [subprocess.Popen(["python", "-m", "src.baselines.b1_plain", "--input", f"data/interim/inputs/{v}.jsonl",
                           "--out", f"runs/b1_{v}/outputs.jsonl", "--model", "qwen3:8b", "--seed", "1"],
                          stdout=open(f"b1_{v}.log", "w"), stderr=subprocess.STDOUT)
         for v in ("full_record", "notice_only")]
while any(p.poll() is None for p in procs):
    time.sleep(60); print(len(os.listdir("runs/cache")) if os.path.isdir("runs/cache") else 0, "calls done of 108")
print([p.returncode for p in procs])
```
If it stops part-way, run Cell 4 again. Finished calls are cached, so it only redoes the missing ones.

**Cell 5: score and download**
```python
!mkdir -p runs/b1 && cat runs/b1_full_record/outputs.jsonl runs/b1_notice_only/outputs.jsonl > runs/b1/outputs.jsonl
!python -m eval.score --gold data/gold/records.jsonl --run runs/b1 --split test --no-unargued-as-rejected
!cp runs/b1/outputs.jsonl /kaggle/working/b1_outputs.jsonl
```
Download `b1_outputs.jsonl` from the Output panel and put it in `runs/b1/outputs.jsonl` locally.

## B2: frontier model with the statute text (about 15 minutes, on a Gemini key that has quota left)
The statute text is in `data/corpus/provisions_b2.json`: CGST Act ss.73, 74, 75, 168A and 169, verbatim from the official India Code PDF (sha256 in the file, matching `corpus/SOURCES.md`), with amendment footnotes and page numbers removed.
```
python -m src.baselines.b2_frontier --input data/interim/inputs/full_record.jsonl --out runs/b2_full_record/outputs.jsonl --provisions data/corpus/provisions_b2.json
python -m src.baselines.b2_frontier --input data/interim/inputs/notice_only.jsonl --out runs/b2_notice_only/outputs.jsonl --provisions data/corpus/provisions_b2.json
```
Caveat for the write-up: B2 uses Gemini 3.5 Flash Lite, the model that drafted the gold records before review, so it may have a home advantage.

## Scoring rule we report
`--no-unargued-as-rejected`: only complaints actually argued in the case are scored. A complaint nobody argued is not evidence that the defect is absent. Gold `not_decided` is never scored.
