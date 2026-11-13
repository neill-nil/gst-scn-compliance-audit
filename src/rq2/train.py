"""RQ2: QLoRA fine-tune of Qwen3-8B to fill the proceeding record (facts) from a judgment. Runs on one Kaggle T4.

Training data: data/interim/rq2/train.jsonl (196 Gemini drafts of reserved cases, built by scripts/build_rq2_data.py;
no test, held-out, dev or queued case is in it). The loss is on the answer only (the prompt tokens are masked).

Usage (Kaggle, one GPU):
    CUDA_VISIBLE_DEVICES=0 python -m src.rq2.train --out runs/rq2_lora [--epochs 2] [--max-hours 2.5]
Writes runs/rq2_lora/adapter/ (the LoRA weights) and runs/rq2_lora/train_log.json.
"""
import argparse
import json
import statistics
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_MODEL = "unsloth/Qwen3-8B-unsloth-bnb-4bit"
DATA = ROOT / "data" / "interim" / "rq2"


def encode(tok, row: dict) -> tuple[list[int], list[int]]:
    """(prompt ids, answer ids). The prompt ends with the assistant header and an empty think block, exactly as
    at inference time with thinking off; the answer ends with the end-of-turn token."""
    prompt = tok.apply_chat_template([row["messages"][0]], tokenize=False, add_generation_prompt=True,
                                     enable_thinking=False)
    p = tok(prompt, add_special_tokens=False)["input_ids"]
    a = tok(row["messages"][1]["content"] + "<|im_end|>", add_special_tokens=False)["input_ids"]
    return p, a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/rq2_lora")
    ap.add_argument("--epochs", type=float, default=2.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--grad-accum", type=int, default=8)
    ap.add_argument("--max-len", type=int, default=8192, help="longer examples are skipped (counted in the log)")
    ap.add_argument("--max-hours", type=float, default=2.5, help="stop training after this long and save")
    ap.add_argument("--seed", type=int, default=3407)
    args = ap.parse_args()

    from unsloth import FastLanguageModel, is_bfloat16_supported  # import before transformers
    from transformers import DataCollatorForSeq2Seq, Trainer, TrainerCallback, TrainingArguments

    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    model, tok = FastLanguageModel.from_pretrained(BASE_MODEL, max_seq_length=args.max_len, load_in_4bit=True,
                                                   dtype=None)
    model = FastLanguageModel.get_peft_model(
        model, r=args.rank, lora_alpha=2 * args.rank, lora_dropout=0, bias="none",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        use_gradient_checkpointing="unsloth", random_state=args.seed)

    def load(split):
        feats, lengths, skipped = [], [], []
        for row in map(json.loads, open(DATA / f"{split}.jsonl", encoding="utf-8")):
            p, a = encode(tok, row)
            lengths.append(len(p) + len(a))
            if len(p) + len(a) > args.max_len:
                skipped.append(row["cnr"])
                continue
            ids = p + a
            feats.append({"input_ids": ids, "attention_mask": [1] * len(ids), "labels": [-100] * len(p) + a})
        print(f"{split}: {len(feats)} examples, tokens median {statistics.median(lengths):.0f} max {max(lengths)}, "
              f"skipped {len(skipped)} longer than {args.max_len}", flush=True)
        return feats, {"n": len(feats), "tokens_median": statistics.median(lengths), "tokens_max": max(lengths),
                       "skipped": skipped}

    train, train_info = load("train")
    val, val_info = load("val")

    start = time.time()

    class Progress(TrainerCallback):
        def on_log(self, a, state, control, logs=None, **kw):
            if logs and "loss" in logs:
                print(f"step {state.global_step}/{state.max_steps} loss {logs['loss']:.4f} "
                      f"elapsed {(time.time() - start) / 60:.0f} min", flush=True)

        def on_step_end(self, a, state, control, **kw):
            if time.time() - start > args.max_hours * 3600:
                print(f"time limit {args.max_hours} h reached at step {state.global_step}; stopping", flush=True)
                control.should_training_stop = True

    trainer = Trainer(
        model=model, train_dataset=train, eval_dataset=val,
        data_collator=DataCollatorForSeq2Seq(tok, padding=True, label_pad_token_id=-100),
        callbacks=[Progress()],
        args=TrainingArguments(
            output_dir=str(out / "checkpoints"), per_device_train_batch_size=1, per_device_eval_batch_size=1,
            gradient_accumulation_steps=args.grad_accum, num_train_epochs=args.epochs, learning_rate=args.lr,
            warmup_steps=3, lr_scheduler_type="linear", weight_decay=0.01, optim="adamw_8bit",
            fp16=not is_bfloat16_supported(), bf16=is_bfloat16_supported(), logging_steps=1,
            save_strategy="no", report_to="none", seed=args.seed, remove_unused_columns=False, disable_tqdm=True))
    result = trainer.train()
    minutes = (time.time() - start) / 60
    val_loss = trainer.evaluate().get("eval_loss")
    print(f"done: {result.global_step} steps in {minutes:.0f} min, val loss {val_loss:.4f}", flush=True)

    model.save_pretrained(out / "adapter")
    tok.save_pretrained(out / "adapter")
    (out / "train_log.json").write_text(json.dumps({
        "base_model": BASE_MODEL, "args": vars(args), "train": train_info, "val": val_info,
        "steps": result.global_step, "minutes": round(minutes, 1), "train_loss": result.training_loss,
        "val_loss": val_loss, "log_history": trainer.state.log_history}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
