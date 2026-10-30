"""Turn eval/score.py outputs into the Tables 1-5 for docs/results_mid.md, per
role4_schema_eval.md Thu step 16.

Usage:
    python -m eval.report --view full_record \\
        --system noticecheck=runs/nc_full_seed1/score_test.json \\
        --system b0=runs/b0/score_test.json \\
        --system b1=runs/b1/score_test.json \\
        --system b2=runs/b2/score_test.json \\
        --out docs/results_mid_tables.md

Each --system is name=path to a score_<split>.json written by `python -m eval.score`. All systems
must have been scored on the same --view and --split for the tables to be comparable.
"""
import argparse
import json
from pathlib import Path


def load_scores(system_paths: dict[str, Path], view: str) -> dict[str, dict]:
    out = {}
    for name, path in system_paths.items():
        data = json.loads(path.read_text())
        if view not in data.get("views", {}):
            raise SystemExit(f"{path}: no scores for view={view!r} (has: {list(data.get('views', {}))})")
        out[name] = data["views"][view]
    return out


def fmt(x, pct=False, digits=3):
    if x is None:
        return "n/a"
    if pct:
        return f"{100 * x:.1f}%"
    return f"{x:.{digits}f}"


def fmt_ci(d: dict | None) -> str:
    if not d:
        return "n/a"
    return f"{d['point']:.3f} [{d['ci_low']:.3f}, {d['ci_high']:.3f}] (n={d['n_cases']})"


# ---------------------------------------------------------------------------
# Table 1: main results
# ---------------------------------------------------------------------------

def table1_main_results(scores: dict[str, dict]) -> str:
    lines = ["## Table 1: main results", "", "| system | F1 | precision | recall | false-alarm rate | strict F1 | F1 minus baseline |",
              "|---|---|---|---|---|---|---|"]
    for name, r in scores.items():
        d = r["defects"]["overall"]
        strict = r.get("defects_strict", {}).get("overall", {})
        boot = r.get("bootstrap_f1_minus_baseline")
        lines.append(
            f"| {name} | {fmt(d['f1'])} | {fmt(d['precision'])} | {fmt(d['recall'])} | "
            f"{fmt(d['false_alarm_rate'], pct=True)} | {fmt(strict.get('f1'))} | {fmt_ci(boot)} |"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Table 2: per defect type, rule-detectable vs reasoning-dependent
# ---------------------------------------------------------------------------

def table2_by_type(scores: dict[str, dict]) -> str:
    lines = ["## Table 2: per defect type (rule-detectable vs reasoning-dependent)", ""]
    for name, r in scores.items():
        d = r["defects"]
        lines.append(f"### {name}")
        lines.append("| group | F1 | precision | recall | false-alarm rate |")
        lines.append("|---|---|---|---|---|")
        for group in ("rule_detectable", "reasoning_dependent"):
            g = d[group]
            lines.append(f"| {group} | {fmt(g['f1'])} | {fmt(g['precision'])} | {fmt(g['recall'])} | {fmt(g['false_alarm_rate'], pct=True)} |")
        lines.append("")
        lines.append("| defect type | F1 | precision | recall | false-alarm rate |")
        lines.append("|---|---|---|---|---|")
        for t, s in d["by_type"].items():
            lines.append(f"| {t} | {fmt(s['f1'])} | {fmt(s['precision'])} | {fmt(s['recall'])} | {fmt(s['false_alarm_rate'], pct=True)} |")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Table 3: notice_only can't-tell accuracy
# ---------------------------------------------------------------------------

def table3_cant_tell(scores: dict[str, dict]) -> str:
    lines = ["## Table 3: notice_only view -- \"can't tell\" accuracy", "",
              "| system | can't-tell rate | n expected |", "|---|---|---|"]
    for name, r in scores.items():
        ct = r.get("cant_tell")
        if ct is None:
            lines.append(f"| {name} | n/a (not scored on notice_only) | - |")
            continue
        lines.append(f"| {name} | {fmt(ct['rate'], pct=True)} | {ct['n_expected']} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Table 4: tool-call accuracy, error recovery, unsafe actions, hand-off
# ---------------------------------------------------------------------------

def table4_agentic(scores: dict[str, dict]) -> str:
    lines = ["## Table 4: tool-call accuracy, error recovery, unsafe actions, hand-off", "",
              "| system | right-tool rate | valid-args rate | error-recovery rate | unsafe-action rate | hand-off precision | hand-off recall |",
              "|---|---|---|---|---|---|---|"]
    for name, r in scores.items():
        tr = r["traces"]
        ua = r["unsafe_actions"]
        ho = r["handoff"]
        lines.append(
            f"| {name} | {fmt(tr['tool_call_right_tool_rate'], pct=True)} | {fmt(tr['tool_call_valid_args_rate'], pct=True)} | "
            f"{fmt(tr['error_recovery_rate'], pct=True)} | {fmt(ua['unsafe_rate'], pct=True)} (n={ua['n_send_reply_actions']}) | "
            f"{fmt(ho['precision'])} | {fmt(ho['recall'])} |"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Table 5: cost per case
# ---------------------------------------------------------------------------

def table5_cost(scores: dict[str, dict]) -> str:
    lines = ["## Table 5: cost per case", "",
              "| system | mean calls | mean tokens in | mean tokens out | mean seconds |", "|---|---|---|---|---|"]
    for name, r in scores.items():
        for sys_name, cost in r["cost"].items():
            def mean_of(key):
                v = cost.get(key)
                return v["mean"] if v else None
            lines.append(f"| {name} ({sys_name}) | {fmt(mean_of('calls'), digits=1)} | {fmt(mean_of('tokens_in'), digits=0)} | "
                         f"{fmt(mean_of('tokens_out'), digits=0)} | {fmt(mean_of('seconds'), digits=1)} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--system", action="append", required=True, dest="systems",
                     help="name=path/to/score_<split>.json, repeatable")
    ap.add_argument("--view", default="full_record")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    system_paths = {}
    for spec in args.systems:
        name, _, path = spec.partition("=")
        if not path:
            raise SystemExit(f"--system must be name=path, got: {spec!r}")
        system_paths[name] = Path(path)

    scores = load_scores(system_paths, args.view)
    tables = "\n\n".join([
        table1_main_results(scores),
        table2_by_type(scores),
        table3_cant_tell(scores),
        table4_agentic(scores),
        table5_cost(scores),
    ])
    print(tables)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(tables + "\n")
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
