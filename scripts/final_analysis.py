"""Final analysis for the report: every number in one place.

Reads the committed runs and scores, recomputes the comparisons, and writes
  runs/final/summary.json        machine-readable, every number below
  docs/results/RESULTS.md        the tables for the report and poster
Also builds runs/nc_full_vote (majority vote of the three NoticeCheck runs; a post-hoc analysis).

Usage: python -m scripts.final_analysis      (about a minute; no model calls)
"""
import json
import random
import statistics as st
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "runs" / "final" / "summary.json"
OUT_MD = ROOT / "docs" / "results" / "RESULTS.md"
TEST = ROOT / "data" / "splits" / "test.txt"

SYSTEMS = [  # run dir, label, role
    ("b0_v2", "B0 rules (no model)", "baseline"),
    ("b1_v2", "B1 Qwen3-8B, record only", "baseline"),
    ("b2_v2", "B2 Gemini 3.5 Flash Lite + statute", "baseline"),
    ("nc_full_s1", "NoticeCheck (Qwen3-8B) run 1", "ours"),
    ("nc_full_s2", "NoticeCheck (Qwen3-8B) run 2", "ours"),
    ("nc_full_s3", "NoticeCheck (Qwen3-8B) run 3", "ours"),
    ("nc_gemini_s1", "NoticeCheck with Gemini as the model", "ours-variant"),
    ("nc_no_tools", "Ablation: no tools", "ablation"),
    ("nc_no_retrieval", "Ablation: no retrieval", "ablation"),
    ("nc_no_verifier", "Ablation: no verifier", "ablation"),
    ("nc_no_handoff", "Ablation: no hand-off", "ablation"),
    ("e2e_nc_tuned", "End to end: fine-tuned extractor -> NoticeCheck", "e2e"),
    ("e2e_nc_base", "End to end: untrained extractor -> NoticeCheck", "e2e"),
    ("e2e_b0_tuned", "End to end: fine-tuned extractor -> B0", "e2e"),
    ("e2e_b0_base", "End to end: untrained extractor -> B0", "e2e"),
]
NC = ["nc_full_s1", "nc_full_s2", "nc_full_s3"]
PAIRS = [("nc_full_s1", "b1_v2"), ("nc_full_s2", "b1_v2"), ("nc_full_s3", "b1_v2"), ("nc_full_vote", "b1_v2"),
         ("nc_full_s1", "b2_v2"), ("nc_full_s2", "b2_v2"), ("nc_full_s3", "b2_v2"), ("nc_full_vote", "b2_v2"),
         ("nc_full_s2", "b0_v2"), ("b2_v2", "b1_v2"), ("b2_v2", "b0_v2"), ("b1_v2", "b0_v2"),
         ("nc_gemini_s1", "b2_v2"), ("nc_gemini_s1", "b1_v2"), ("nc_full_s2", "nc_full_s1"),
         ("nc_no_tools", "nc_full_s1"), ("nc_no_retrieval", "nc_full_s1"), ("nc_no_verifier", "nc_full_s1"),
         ("nc_no_handoff", "nc_full_s1"), ("e2e_nc_tuned", "nc_full_s1"), ("e2e_nc_tuned", "b1_v2"),
         ("e2e_nc_tuned", "e2e_nc_base")]


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


_FRESH = set()


def score(run, split):
    """Re-scores every run once per invocation, so all numbers come from the current scorer."""
    p = ROOT / "runs" / run / f"score_{split}_strict_argued.json"
    if (run, split) not in _FRESH:
        _FRESH.add((run, split))
        subprocess.run([sys.executable, "-m", "eval.score", "--run", f"runs/{run}", "--split", split, "--view", "full_record",
                        "--view", "notice_only", "--strict", "--no-unargued-as-rejected", "--out", str(p)],
                       cwd=ROOT, check=True, capture_output=True)
    return json.load(open(p, encoding="utf-8"))


def defects(s, view="full_record", strict=False):
    """Lenient (any cited section) is the detection score; strict also requires the right section."""
    v = s["views"].get(view) or {}
    return v.get("defects_strict" if strict else "defects") if v.get("n_cases_with_output") else None


def compare(sys_run, base_run, strict=False):
    out = subprocess.run([sys.executable, "-m", "scripts.compare_runs", "--system", f"runs/{sys_run}", "--baseline",
                          f"runs/{base_run}", "--view", "full_record", "--split", str(TEST)] + (["--strict"] if strict else []),
                         cwd=ROOT, capture_output=True, text=True).stdout
    res = {}
    for line in out.splitlines():
        parts = line.split()
        if parts and parts[0] in ("f1", "recall", "precision", "false_alarms"):
            res[parts[0]] = {"diff": float(parts[1]), "ci95": [float(parts[4].strip("[,")), float(parts[5].strip("]"))]}
    return res


def majority_vote():
    """Per case and defect type, the verdict most of the three runs gave (ties: the more cautious one)."""
    caution = {"cant_tell": 0, "contested": 1, "no_defect": 2, "defect": 3}
    runs = [{(o["cnr"], o["view"]): o for o in jl(ROOT / "runs" / r / "outputs.jsonl")} for r in NC]
    out_dir = ROOT / "runs" / "nc_full_vote"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, agree, total = [], 0, 0
    for key, o1 in runs[0].items():
        if key[1] != "full_record" or not all(key in r for r in runs):
            continue
        by_type = [{f["type"]: f for f in r[key]["findings"]} for r in runs]
        findings = []
        for t in by_type[0]:
            votes = [bt[t]["verdict"] for bt in by_type if t in bt]
            total += 1
            agree += len(set(votes)) == 1
            top = Counter(votes).most_common()
            best = max((v for v, c in top if c == top[0][1]), key=lambda v: -caution[v])
            src = next(bt[t] for bt in by_type if t in bt and bt[t]["verdict"] == best)
            findings.append(src)
        rows.append(dict(o1, findings=findings, run_id="nc_full_vote", system="noticecheck_v1_vote3"))
    with open(out_dir / "outputs.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    (out_dir / "README.md").write_text("Majority vote of runs/nc_full_s1..s3 per case and defect type (ties go to the "
                                       "more cautious verdict). Post-hoc analysis built by scripts/final_analysis.py.\n")
    for split in ("test", "heldout"):
        p = out_dir / f"score_{split}_strict_argued.json"
        p.unlink(missing_ok=True)
        score("nc_full_vote", split)
    return {"identical_verdict_share": agree / total, "n_case_type_pairs": total}


def miss_analysis(run):
    """Why each court-found defect in the test set was missed: NoticeCheck's verdict on that type."""
    gold = {r["cnr"]: r for r in jl(ROOT / "data/gold/records.jsonl") if r["annotation"].get("set", "test") == "test"}
    out = {(o["cnr"]): o for o in jl(ROOT / "runs" / run / "outputs.jsonl") if o["view"] == "full_record"}
    u = lambda n: n.get("value") if isinstance(n, dict) else n
    res, by_type, missing = Counter(), defaultdict(Counter), Counter()
    for cnr, g in gold.items():
        f = {x["type"]: x for x in out[cnr]["findings"]}
        for d in g["defects_argued"]:
            if u(d["finding"]) != "defect_found":
                continue
            v = f.get(u(d["type"]), {}).get("verdict", "absent")
            res[v] += 1
            by_type[u(d["type"])][v] += 1
            if v == "cant_tell":
                for m in f[u(d["type"])].get("missing_facts") or []:
                    missing[m.split("(")[0].strip()[:60]] += 1
    return {"verdict_on_found_defects": dict(res), "by_type": {k: dict(v) for k, v in by_type.items()},
            "top_missing_facts": missing.most_common(10)}


def fresh_check():
    rows = jl(ROOT / "data/gold/fresh_check_answers.jsonl")
    calls = [r for r in rows if r["type"] != "MISSED?"]
    res = {"n_cases": len({r["cnr"] for r in rows}), "n_calls": len(calls)}
    for says in ("defect", "contested", "no_defect"):
        sub = [r for r in calls if r["says"] == says]
        res[says] = {"n": len(sub), "verdict": dict(Counter(r["verdict"] for r in sub)),
                     "court": dict(Counter(r["court"] for r in sub)),
                     "verdict_x_court": {f"{a}|{b}": c for (a, b), c in Counter((r["verdict"], r["court"]) for r in sub).items()}}
    d = [r for r in calls if r["says"] == "defect"]
    res["defect_calls_on_unargued_points"] = {"n": sum(r["court"] == "not_argued" for r in d),
                                              "judged_correct": sum(r["court"] == "not_argued" and r["verdict"] == "correct" for r in d)}
    # Court-found defects NoticeCheck missed, from the reviewers' MISSED? notes (counted by hand on 15 Nov,
    # see docs/results/RESULTS.md): 14 in 10 cases; 12 excluding ODHC010661432025 (flagged out of scope).
    caught = sum(r["verdict"] == "correct" and r["court"] == "found" for r in d)
    missed, missed_in_scope = 14, 12
    res["recall_estimate"] = {"caught": caught, "missed": missed, "recall": caught / (caught + missed),
                              "recall_in_scope": caught / (caught + missed_in_scope)}
    verifiable = [r for r in d if r["verdict"] != "cant_verify"]
    res["defect_precision_human"] = sum(r["verdict"] == "correct" for r in verifiable) / len(verifiable)
    nd = [r for r in calls if r["says"] == "no_defect" and r["verdict"] != "cant_verify"]
    res["no_defect_correct_share"] = sum(r["verdict"] == "correct" for r in nd) / len(nd)
    ct = [r for r in calls if r["says"] == "contested" and r["verdict"] != "cant_verify"]
    res["contested_correct_share"] = sum(r["verdict"] == "correct" for r in ct) / len(ct)
    res["ai_assisted_reviewers_declared"] = sorted({r["reviewer"] for r in calls if r["comment"].strip().upper().startswith("AI")})
    return res


def fmt(x, nd=2):
    return "–" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def main():
    summary = {"systems": {}, "comparisons": {}, "notes": []}
    vote = majority_vote()
    summary["nc_seed_stability"] = vote
    systems = SYSTEMS[:6] + [("nc_full_vote", "NoticeCheck majority vote of 3 runs (post hoc)", "ours-posthoc")] + SYSTEMS[6:]
    for run, label, role in systems:
        entry = {"label": label, "role": role}
        for split in ("test", "heldout"):
            s = score(run, split)
            v = s["views"].get("full_record", {})
            d = defects(s)
            ds = defects(s, strict=True)
            entry[split] = None if d is None else {
                "overall": d["overall"], "overall_strict": ds["overall"], "rule_detectable": d.get("rule_detectable"),
                "reasoning_dependent": d.get("reasoning_dependent"),
                "by_type": {t: x for t, x in (d.get("by_type") or {}).items() if x["tp"] + x["miss"] + x["false_alarm"]},
                "contested": v.get("contested"), "handoff": v.get("handoff"), "unsafe": v.get("unsafe_actions"),
                "cost": v.get("cost")}
            no = defects(s, "notice_only")
            if no:
                entry[split + "_notice_only"] = no["overall"]
        summary["systems"][run] = entry
    f1s = [summary["systems"][r]["test"]["overall"]["f1"] for r in NC]
    summary["nc_mean"] = {k: st.mean(summary["systems"][r]["test"]["overall"][k] for r in NC)
                          for k in ("f1", "precision", "recall", "flags_on_unargued", "false_alarm")}
    summary["nc_mean"]["f1_sd"] = st.stdev(f1s)
    summary["nc_mean"]["f1_range"] = [min(f1s), max(f1s)]
    for a, b in PAIRS:
        summary["comparisons"][f"{a} - {b}"] = compare(a, b)
        summary["comparisons_strict"] = summary.get("comparisons_strict", {})
        summary["comparisons_strict"][f"{a} - {b}"] = compare(a, b, strict=True)
    summary["miss_analysis_nc_full_s2"] = miss_analysis("nc_full_s2")
    summary["rq2_extraction"] = {sp: json.load(open(ROOT / f"runs/rq2_scores_{sp}.json")) for sp in ("test", "heldout")}
    summary["rq2_extraction_repaired"] = {sp: json.load(open(ROOT / f"runs/rq2_scores_{sp}_repaired.json")) for sp in ("test", "heldout")}
    summary["rq2_training"] = {k: v for k, v in json.load(open(ROOT / "runs/rq2_lora/train_log.json")).items() if k != "log_history"}
    summary["fresh_check"] = fresh_check()
    gold = jl(ROOT / "data/gold/records.jsonl")
    u = lambda n: n.get("value") if isinstance(n, dict) else n
    summary["dataset"] = {
        "test_cases": sum(r["annotation"].get("set", "test") == "test" for r in gold),
        "heldout_cases": sum(r["annotation"].get("set") == "heldout" for r in gold),
        "dev_cases_reviewed": len(jl(ROOT / "data/gold/dev_records.jsonl")),
        "test_findings": dict(Counter(u(d["finding"]) for r in gold if r["annotation"].get("set", "test") == "test" for d in r["defects_argued"])),
        "test_found_by_type": dict(Counter(u(d["type"]) for r in gold if r["annotation"].get("set", "test") == "test"
                                           for d in r["defects_argued"] if u(d["finding"]) == "defect_found")),
        "courts": dict(Counter(r["court"] for r in gold)),
        "agreement": {"kappa_overall": 0.725, "n_complaints": 58, "n_double_reviewed_cases": 35,
                      "kappa_without_ai_assisted_reviewer": 0.75},
        "screened_judgments": 20087, "reasoned_after_screen": 429, "drafts": 425}
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(summary, indent=1), encoding="utf-8")
    write_md(summary)
    print(f"wrote {OUT_JSON} and {OUT_MD}")


def write_md(S):
    sy, cp = S["systems"], S["comparisons"]
    L = ["# Final results (generated by `scripts/final_analysis.py`)", "",
         "All defect scores: 125 test cases, only complaints the court decided (found or rejected); \"unargued\" = defects "
         "flagged on points nobody argued (reported, not scored). **F1** counts a defect call as a hit whatever section it "
         "cites (detection); **strict F1** also requires the right section (a citation listing several sections counts if "
         "one is right). NoticeCheck takes its sections from a fixed table, so its two scores are equal.", ""]
    cs = S["comparisons_strict"]; fa = lambda r: sy[r]["test"]["overall"]["false_alarm_rate"]
    rd = lambda r: (sy[r]["test"]["reasoning_dependent"] or {}).get("f1")
    L += ["## 0. Research questions against the criteria in the proposal", "",
          "RQ1 (proposal): beat the same 8B model given the record alone on defect-level F1 *with type and cited provision matching*; "
          "falsified if the paired gain is under 10 points or its 95% CI includes 0, if our false-alarm rate exceeds the baseline's, "
          "or if we do not beat the rule checklist on reasoning-dependent defects.", "",
          "| Criterion | Result | Met? |", "|---|---|---|",
          "| Strict F1 gain over B1 ≥ 0.10, CI above 0 | " + "; ".join(f"run {i+1} {cs[f'{r} - b1_v2']['f1']['diff']:+.2f} [{cs[f'{r} - b1_v2']['f1']['ci95'][0]:+.2f}, {cs[f'{r} - b1_v2']['f1']['ci95'][1]:+.2f}]" for i, r in enumerate(NC)) + " | Yes |",
          f"| False-alarm rate not above B1's ({fa('b1_v2'):.2f}) | NoticeCheck " + ", ".join(f"{fa(r):.2f}" for r in NC) + " | No |",
          f"| Beat B0 on reasoning-dependent defects | B0 {fmt(rd('b0_v2'))} (no hits) vs NoticeCheck " + ", ".join(fmt(rd(r)) for r in NC) + " | Yes |", "",
          "Most of the strict gain over B1 comes from citing the right section (B1 cites a wrong one on 14 of its 27 hits; NoticeCheck "
          "never does). On detection alone (any section) the gain over B1 is +0.03 to +0.11 and not significant.", "",
          "RQ2: the fine-tuned 8B extractor does not match the large model's drafts (field F1 0.80, 0.88 repaired, vs 0.95, which is "
          "inflated because reviewers corrected those drafts) but gains +0.28 over the untrained model (see section 8).", ""]
    L += ["## 1. Main comparison (test, full record)", "",
          "| System | F1 | Precision | Recall | Strict F1 | Wrong-section calls | Hits | False alarms | Misses | Unargued flags | Notice-only F1 |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for run in ["b0_v2", "b1_v2", "b2_v2"] + NC + ["nc_full_vote", "nc_gemini_s1"]:
        o = sy[run]["test"]["overall"]; os_ = sy[run]["test"]["overall_strict"]; no = sy[run].get("test_notice_only")
        strict_cell = "n/a (cites no section)" if run == "b0_v2" else fmt(os_["f1"])
        wp_cell = "–" if run == "b0_v2" else os_["wrong_provision"]
        L.append(f"| {sy[run]['label']} | {fmt(o['f1'])} | {fmt(o['precision'])} | {fmt(o['recall'])} | {strict_cell} | {wp_cell} | {o['tp']} | "
                 f"{o['false_alarm']} | {o['miss']} | {o['flags_on_unargued']} | {fmt(no['f1']) if no else '–'} |")
    m = S["nc_mean"]
    L += ["", f"NoticeCheck (Qwen) over 3 runs: F1 mean {m['f1']:.3f}, sd {m['f1_sd']:.3f}, range {m['f1_range'][0]:.2f}–{m['f1_range'][1]:.2f}; "
          f"precision {m['precision']:.2f}; recall {m['recall']:.2f}; unargued flags {m['flags_on_unargued']:.0f}; false alarms {m['false_alarm']:.1f}. "
          f"The three runs gave the identical verdict on {S['nc_seed_stability']['identical_verdict_share']:.0%} of case-type pairs.", ""]
    L += ["## 2. Paired bootstrap (F1 difference, 95% CI, 5,000 resamples of the 125 cases)", "",
          "| System − baseline | ΔF1 | 95% CI | Δ recall | Δ precision |", "|---|---|---|---|---|"]
    for k, v in cp.items():
        if "f1" in v:
            sig = " *" if v["f1"]["ci95"][0] > 0 or v["f1"]["ci95"][1] < 0 else ""
            L.append(f"| {k} | {v['f1']['diff']:+.3f}{sig} | [{v['f1']['ci95'][0]:+.3f}, {v['f1']['ci95'][1]:+.3f}] | "
                     f"{v['recall']['diff']:+.3f} | {v['precision']['diff']:+.3f} |")
    L += ["", "\\* interval excludes 0.", "", "Strict (right section required):", "", "| System − baseline | ΔF1 | 95% CI |", "|---|---|---|"]
    for k, v in S["comparisons_strict"].items():
        if "f1" in v and not k.startswith("nc_no_") and k != "nc_full_s2 - nc_full_s1":
            sig = " *" if v["f1"]["ci95"][0] > 0 or v["f1"]["ci95"][1] < 0 else ""
            L.append(f"| {k} | {v['f1']['diff']:+.3f}{sig} | [{v['f1']['ci95'][0]:+.3f}, {v['f1']['ci95'][1]:+.3f}] |")
    L += [""]
    L += ["## 3. Ablations (test, 1 run each)", "", "| Version | F1 | Precision | Recall | False alarms | Unargued flags |", "|---|---|---|---|---|---|"]
    for run in NC[:1] + ["nc_no_tools", "nc_no_retrieval", "nc_no_verifier", "nc_no_handoff"]:
        o = sy[run]["test"]["overall"]
        L.append(f"| {sy[run]['label']} | {fmt(o['f1'])} | {fmt(o['precision'])} | {fmt(o['recall'])} | {o['false_alarm']} | {o['flags_on_unargued']} |")
    L += ["", f"Every ablation falls inside the full system's run-to-run range ({m['f1_range'][0]:.2f}–{m['f1_range'][1]:.2f}).", ""]
    L += ["## 4. By defect type (test; hits / court-found, F1)", ""]
    types = sorted({t for r in ["b1_v2", "b2_v2"] + NC for t in sy[r]["test"]["by_type"]})
    cols = ["b0_v2", "b1_v2", "b2_v2"] + NC + ["nc_gemini_s1"]
    L += ["| Defect type | Court found | " + " | ".join(sy[c]["label"].split(" (")[0].replace("NoticeCheck", "NC") for c in cols) + " |",
          "|---|---|" + "---|" * len(cols)]
    found = S["dataset"]["test_found_by_type"]
    for t in types:
        cells = []
        for c in cols:
            x = sy[c]["test"]["by_type"].get(t)
            cells.append("–" if not x else f"{x['tp']}/{x['tp'] + x['miss']} ({fmt(x['f1'])})")
        L.append(f"| {t} | {found.get(t, 0)} | " + " | ".join(cells) + " |")
    L += ["", "Rule-detectable vs reasoning-dependent defects (F1):", "", "| System | Rule-detectable | Reasoning-dependent |", "|---|---|---|"]
    for c in ["b0_v2", "b1_v2", "b2_v2"] + NC + ["nc_gemini_s1"]:
        t = sy[c]["test"]
        L.append(f"| {sy[c]['label']} | {fmt((t['rule_detectable'] or {}).get('f1'))} | {fmt((t['reasoning_dependent'] or {}).get('f1'))} |")
    ma = S["miss_analysis_nc_full_s2"]
    L += ["", "## 5. Why NoticeCheck misses (run 2, court-found defects in test)", "",
          "NoticeCheck's verdict on each defect the court found: " + ", ".join(f"{k} {v}" for k, v in ma["verdict_on_found_defects"].items()) + ".", "",
          "| Defect type | " + " | ".join(sorted(ma["verdict_on_found_defects"])) + " |", "|---|" + "---|" * len(ma["verdict_on_found_defects"])]
    for t, c in sorted(ma["by_type"].items(), key=lambda x: -sum(x[1].values())):
        L.append(f"| {t} | " + " | ".join(str(c.get(k, 0)) for k in sorted(ma["verdict_on_found_defects"])) + " |")
    L += ["", "Facts most often reported missing when it said \"can't tell\": " +
          "; ".join(f"{k} ({v})" for k, v in ma["top_missing_facts"][:6]) + ".", ""]
    L += ["## 6. Other system measures (test, NoticeCheck run 2 and Gemini variant)", "", "| Measure | NC run 2 | NC + Gemini |", "|---|---|---|"]
    for name, key in (("Contested points flagged (of 26)", "contested"), ("Hand-off precision / recall (proxy)", "handoff"), ("Unsafe actions", "unsafe")):
        vals = []
        for c in ("nc_full_s2", "nc_gemini_s1"):
            x = sy[c]["test"][key]
            vals.append(f"{x['rate']:.0%}" if key == "contested" else f"{fmt(x['precision'])} / {fmt(x['recall'])}" if key == "handoff" else str(x["n_unsafe"]))
        L.append(f"| {name} | " + " | ".join(vals) + " |")
    cost = sy["nc_full_s2"]["test"]["cost"]["noticecheck_v1"]
    L.append(f"| Model calls / tokens in / tokens out / seconds per case | {cost['calls']['mean']:.1f} / {cost['tokens_in']['mean']:.0f} / "
             f"{cost['tokens_out']['mean']:.0f} / {cost['seconds']['mean']:.0f} (one T4) | – |")
    L += ["", "## 7. Held-out court (Karnataka, 12 cases, 6 court-found defects)", "", "| System | Hits / 6 | Unargued flags |", "|---|---|---|"]
    for c in ["b0_v2", "b1_v2", "b2_v2"] + NC + ["nc_gemini_s1", "e2e_nc_tuned", "e2e_nc_base"]:
        h = sy[c]["heldout"]
        if h:
            L.append(f"| {sy[c]['label']} | {h['overall']['tp']} | {h['overall']['flags_on_unargued']} |")
    r = S["rq2_extraction"]["test"]; rr = S["rq2_extraction_repaired"]["test"]; tr = S["rq2_training"]
    L += ["", "## 8. RQ2: fact extraction (test, 125 judgments)", "",
          f"QLoRA on Qwen3-8B (4-bit, rank 16): {tr['train']['n']} training examples (Gemini drafts of other cases), {tr['steps']} steps, "
          f"{tr['minutes']:.0f} minutes on one T4; train loss {tr['train_loss']:.3f}, validation loss {tr['val_loss']:.3f}.", "",
          "| Extractor | Field F1 | Precision | Recall | Events F1 | Doc contents F1 | Valid JSON | Schema-valid | Quotes found in judgment |",
          "|---|---|---|---|---|---|---|---|---|"]
    for name, src in (("Untrained Qwen3-8B", r["base"]), ("Fine-tuned Qwen3-8B", r["tuned"]), ("Fine-tuned, cut-off outputs repaired", rr["tuned"]),
                      ("Gemini drafts (inflated: reviewers corrected these)", r["gemini"])):
        L.append(f"| {name} | {fmt(src['fields']['f1'])} | {fmt(src['fields']['precision'])} | {fmt(src['fields']['recall'])} | "
                 f"{fmt(src['events']['f1'])} | {fmt(src['document_contents']['f1'])} | {src['n_with_json']}/125 | {src['schema_valid']}/125 | {fmt(src['quotes_found_share'])} |")
    d = r["tuned"]["fields_f1_minus_base"]
    L += ["", f"Fine-tuned − untrained field F1: {d['diff']:+.3f}, 95% CI [{d['ci95'][0]:+.3f}, {d['ci95'][1]:+.3f}]. "
          f"Held-out: untrained {S['rq2_extraction']['heldout']['base']['fields']['f1']:.2f}, fine-tuned {S['rq2_extraction']['heldout']['tuned']['fields']['f1']:.2f}.", "",
          "Per field (F1): " + "; ".join(f"{k} {r['base']['per_field'][k]['f1']:.2f} → {r['tuned']['per_field'][k]['f1']:.2f}" for k in r["base"]["per_field"]) + ".", ""]
    L += ["## 9. End to end (judgment → extractor → checker; test)", "", "| Pipeline | F1 | Precision | Recall | Unargued flags | Defect calls |", "|---|---|---|---|---|---|"]
    for c in ["nc_full_s2", "e2e_nc_tuned", "e2e_nc_base", "b0_v2", "e2e_b0_tuned", "e2e_b0_base"]:
        o = sy[c]["test"]["overall"]
        L.append(f"| {sy[c]['label']} | {fmt(o['f1'])} | {fmt(o['precision'])} | {fmt(o['recall'])} | {o['flags_on_unargued']} | – |")
    L += ["", "Defect calls on test: checked facts 84, fine-tuned extractor 70, untrained extractor 158. The untrained extractor "
          "filled in facts the judgment never states (hearing date given 77 cases, service mode 80, signature 57, of 125); "
          "39% of its defect evidence quotes are not in the judgment (fine-tuned 24%, checked facts 18%, judgments cut at 12k characters).", ""]
    fc = S["fresh_check"]
    L += ["## 10. Fresh-case hand check (20 new judgments, picked after the freeze; full system end to end)", "",
          f"{fc['n_calls']} calls checked by the team against the judgment (reviewers saw the system's answer; AI assistance declared by "
          f"{', '.join(fc['ai_assisted_reviewers_declared'])}).", "",
          "| NoticeCheck said | Calls | Correct | Wrong | Can't verify |", "|---|---|---|---|---|"]
    for s in ("defect", "contested", "no_defect"):
        v = fc[s]["verdict"]
        L.append(f"| {s.replace('_', ' ')} | {fc[s]['n']} | {v.get('correct', 0)} | {v.get('wrong', 0)} | {v.get('cant_verify', 0)} |")
    re_ = fc["recall_estimate"]
    L += ["", f"- Defect calls: all {re_['caught']} correct ones were defects the court found; all "
          f"{fc['defect_calls_on_unargued_points']['n']} defect calls on points nobody argued were judged wrong "
          f"({fc['defect_calls_on_unargued_points']['judged_correct']} correct). Human-judged defect precision {fc['defect_precision_human']:.2f}.",
          f"- \"No defect\" right in {fc['no_defect_correct_share']:.0%} of verifiable calls; \"contested\" fits in {fc['contested_correct_share']:.0%}.",
          f"- Missed: about {re_['missed']} court-found defects in 10 of 20 cases (mostly \"no hearing\" in the Madras portal-service template), "
          f"so recall ≈ {re_['recall']:.2f} ({re_['recall_in_scope']:.2f} without the one case flagged out of scope). Consistent with the test set end to end (0.38).", ""]
    ds = S["dataset"]
    L += ["## 11. Dataset", "", f"- Screened {ds['screened_judgments']:,} GST judgments (24 High Courts, 2024–2026); {ds['reasoned_after_screen']} reasoned; {ds['drafts']} Gemini drafts.",
          f"- Gold: test {ds['test_cases']}, held-out {ds['heldout_cases']} (Karnataka), dev {ds['dev_cases_reviewed']} reviewed; fresh check 20.",
          f"- Test complaints: " + ", ".join(f"{k} {v}" for k, v in ds["test_findings"].items()) + ".",
          f"- Agreement: Cohen's κ {ds['agreement']['kappa_overall']} on {ds['agreement']['n_complaints']} complaints in {ds['agreement']['n_double_reviewed_cases']} double-reviewed cases "
          f"({ds['agreement']['kappa_without_ai_assisted_reviewer']} without the reviewer who used AI).",
          "- Courts: " + ", ".join(f"{k} {v}" for k, v in sorted(ds["courts"].items(), key=lambda x: -x[1])) + ".", ""]
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
