"""NoticeCheck: plan -> precondition checks -> verify -> hand-off, for one checker input.

Configuration switches (each really removes its component, for the ablations):
  tools:     the model plans tool calls (limitation_check, statute_lookup, ...) and the rule cards use the
             results. Off: no tool calls; limitation and extension-validity are judged by the model from dates.
  retrieval: statute text of each provision is looked up and given to the model and attached as evidence.
  verifier:  a "defect" needs a record quote that really is in the record (else can't tell); contested points
             are flagged with case law. Off: findings pass through unchanged.
  handoff:   escalation rules. Off: never escalates.
"""
import re
import time
from datetime import date

from src.common.llm import complete
from src.noticecheck import cards, prompts
from src.noticecheck.record import all_quotes, compact, events, fact
from src.tools import SPECS, call_tool

DEFAULT = {"backend": "local", "model": None, "seed": 1, "temperature": 0.0, "tools": True, "retrieval": True,
           "verifier": True, "handoff": True, "max_tool_calls": 8, "max_tokens": 1500}
NO_TOOL_CARDS = {
    "limitation": {"question": "Using the dates in the record and the statute text, was the notice or the order issued "
                               "after the time limit in s.73(10)/s.73(2) or s.74(10)/s.74(2)?"},
    "extension_notification_validity": {"question": "Does the order's timeliness depend on the s.168A extension "
                                                    "notifications for FY 2017-18 to 2019-20?"},
}
CONTEST_QUERY = {"consolidated_scn": "single show cause notice for multiple financial years consolidated",
                 "extension_notification_validity": "validity of Notification 9/2023 56/2023 extension section 168A",
                 "service_169": "notice uploaded additional notices tab not communicated email",
                 "limitation": "time limit section 73(10) extension notification 168A validity"}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("“", '"').replace("”", '"').replace("’", "'")).strip().lower()


class Run:
    """Holds one case's state and its trace."""

    def __init__(self, inp: dict, cfg: dict):
        self.inp, self.cfg, self.record = inp, {**DEFAULT, **cfg}, inp["record"]
        self.trace, self.tools, self.step = [], [], 0
        self.usage = {"calls": 0, "tokens_in": 0, "tokens_out": 0, "seconds": 0.0}

    def log(self, stage, **kw):
        self.step += 1
        self.trace.append({"step": self.step, "stage": stage, **kw})

    def llm(self, prompt: str, schema: dict, stage: str):
        cfg = self.cfg
        model = cfg["model"]
        text = prompt + ("\n\n/no_think" if model and "qwen3" in model.lower() else "")
        out = complete(cfg["backend"], [{"role": "user", "content": text}], json_schema=schema,
                       temperature=cfg["temperature"], seed=cfg["seed"], max_tokens=cfg["max_tokens"],
                       model=model, tag=f"noticecheck:{stage}")
        for k in ("tokens_in", "tokens_out", "seconds"):
            self.usage[k] += out[k]
        self.usage["calls"] += 1
        self.log(stage, tool=None, model=out["model"], ok=out["json"] is not None, tokens_in=out["tokens_in"],
                 tokens_out=out["tokens_out"], seconds=out["seconds"], error=out.get("error"))
        return out["json"]

    def tool(self, name: str, args: dict, by: str, stage: str):
        t0 = time.time()
        res = call_tool(name, args, record=self.record)
        self.tools.append({"tool": name, "args": args, "out": res, "by": by})
        summary = (res.get("error") if not res["ok"] else str(res["result"])[:200])
        self.log(stage, tool=name, args=args, by=by, ok=res["ok"], output_summary=summary,
                 seconds=round(time.time() - t0, 3))
        return res


def plan(run: Run):
    facts = compact(run.record)
    p = prompts.PLAN.format(as_of=run.inp.get("as_of_date"), facts=facts, tools=prompts.tool_specs(SPECS),
                            max_calls=run.cfg["max_tool_calls"])
    out = run.llm(p, prompts.PLAN_SCHEMA, "plan") or {"tool_calls": [], "missing_facts": []}
    calls = out["tool_calls"][: run.cfg["max_tool_calls"]]
    failed = []
    for c in calls:
        res = run.tool(c["tool"], c["args"], "model", "plan")
        if not res["ok"]:
            failed.append({"tool": c["tool"], "args": c["args"], "error": res["error"]})
    if failed:  # error recovery: one chance to correct the failed calls
        fix = run.llm(p + "\n" + prompts.FIX_CALLS.format(errors=failed), prompts.PLAN_SCHEMA, "plan") or {}
        for c in (fix.get("tool_calls") or [])[: len(failed)]:
            run.tool(c["tool"], c["args"], "model", "plan")
    return out.get("missing_facts", [])


def statute_texts(run: Run, types: list[str]) -> dict[str, str]:
    texts = {}
    if not run.cfg["retrieval"]:
        return texts
    for t in run.tools:  # reuse what the planner already looked up
        if t["tool"] == "statute_lookup" and t["out"]["ok"]:
            texts[t["out"]["result"]["ref"]] = t["out"]["result"]["text"]
    for d in types:
        ref = cards.provision_for(d, run.record)
        if ref and ref not in texts:
            res = run.tool("statute_lookup", {"ref": ref}, "code", "precondition_check")
            if res["ok"]:
                texts[res["result"]["ref"]] = res["result"]["text"]
    return texts


def model_checks(run: Run, types: list[str], extra: dict | None = None) -> list[dict]:
    if not types:
        return []
    texts = statute_texts(run, types)
    statute = ("\nStatute text:\n" + "\n".join(f"{r}: {t[:1500]}" for r, t in texts.items()) + "\n") if texts else ""
    p = prompts.CHECK.format(as_of=run.inp.get("as_of_date"), facts=compact(run.record), statute=statute,
                             checks=prompts.check_list(types, extra))
    out = run.llm(p, prompts.check_schema(types), "precondition_check") or {"findings": []}
    got = {f["type"]: f for f in out["findings"] if f["type"] in types}
    result = []
    for d in types:
        f = got.get(d)
        if f is None:
            result.append(cards.finding(d, "cant_tell", run.record, missing=["model gave no answer"], confidence=0.0))
            continue
        result.append({**cards.finding(d, f["verdict"], run.record, missing=f["missing_facts"],
                                       confidence=f["confidence"]),
                       "evidence": [{"source": "record", "ref": "model", "quote": q} for q in f["evidence"]]})
    return result


def verify(run: Run, findings: list[dict]) -> list[dict]:
    quotes = [norm(q) for q in all_quotes(run.record)]
    flagged = [f["type"] for f in findings if f["verdict"] in ("defect", "contested")]
    texts = statute_texts(run, flagged) if run.cfg["retrieval"] else {}  # statute evidence for flagged findings only
    out = []
    for f in findings:
        f = dict(f)
        if f["verdict"] == "defect":
            good = [e for e in f["evidence"] if e["source"] == "record" and e["quote"]
                    and any(norm(e["quote"]) in q or (len(q) >= 20 and q in norm(e["quote"])) for q in quotes if q)]
            if not good:
                f.update(verdict="cant_tell", evidence=[], missing_facts=f["missing_facts"] + ["a record quote showing the defect"])
                run.log("verify", defect=f["type"], ok=True, output_summary="defect dropped: no verified record quote")
            else:
                f["evidence"] = good
        if f["type"] in cards.CONTESTED and f["verdict"] == "defect":
            f["verdict"] = "contested"
        if f["provision"] in texts and f["verdict"] in ("defect", "contested"):
            f["evidence"] = f["evidence"] + [{"source": "statute", "ref": f["provision"], "quote": texts[f["provision"]][:400]}]
        if f["verdict"] == "contested" and run.cfg["tools"] and f["type"] in CONTEST_QUERY:
            res = run.tool("caselaw_search", {"query": CONTEST_QUERY[f["type"]], "k": 3}, "code", "verify")
            if res["ok"]:
                f["evidence"] += [{"source": "caselaw", "ref": f"{h['cnr']} para {h['para']}", "quote": h["text"][:300]}
                                  for h in res["result"]]
        out.append(f)
    return out


def handoff(run: Run, findings: list[dict]) -> dict:
    if not run.cfg["handoff"]:
        return {"escalate": False, "reasons": []}
    reasons = []
    as_of = run.inp.get("as_of_date")
    due = fact(run.record, "notices.0.reply_due")[0]
    if as_of and due:
        try:
            days = (date.fromisoformat(due) - date.fromisoformat(as_of)).days
            if 0 <= days <= 7:
                reasons.append("deadline_tight")
        except ValueError:
            pass
    if events(run.record, "recovery_or_attachment"):
        reasons.append("recovery_threat")
    fys = fact(run.record, "financial_years")[0] or []
    if fact(run.record, "provision")[0] not in (None, "73", "74") or any(fy >= "2024-25" for fy in fys):
        reasons.append("out_of_scope")
    if sum(f["verdict"] == "cant_tell" for f in findings) >= 10:
        reasons.append("unclear")
    if not any(f["verdict"] == "defect" for f in findings):
        reasons.append("defect_free")
    run.log("handoff", ok=True, output_summary=",".join(reasons))
    return {"escalate": bool(reasons), "reasons": reasons}


def run_case(inp: dict, cfg: dict) -> tuple[dict, list[dict]]:
    run = Run(inp, cfg)
    missing = plan(run) if run.cfg["tools"] else []
    findings, model_types, extra = {}, [], {}
    for d in cards.TYPES:
        if d in cards.RULE_CARDS and (run.cfg["tools"] or d not in NO_TOOL_CARDS):
            findings[d] = cards.RULE_CARDS[d](run.record, run.tools)
            run.log("precondition_check", defect=d, tool=None, by="rule", ok=True, output_summary=findings[d]["verdict"])
        elif d in NO_TOOL_CARDS:
            model_types.append(d)
            extra[d] = NO_TOOL_CARDS[d]
        else:
            ready, need = cards.model_card_ready(d, run.record)
            if ready:
                model_types.append(d)
            elif need and need[0].startswith("__"):  # the check does not apply (no reply filed; not a s.74 notice)
                findings[d] = cards.finding(d, "no_defect", run.record, confidence=0.8,
                                            note="does not apply: " + need[0].strip("_").replace("_", " "))
            else:
                findings[d] = cards.finding(d, "cant_tell", run.record, missing=need)
    for f in model_checks(run, model_types, extra):
        findings[f["type"]] = f
    ordered = [findings[d] for d in cards.TYPES]
    if run.cfg["verifier"]:
        ordered = verify(run, ordered)
    out = {"cnr": inp["cnr"], "view": inp.get("view"), "findings": ordered, "handoff": handoff(run, ordered),
           "actions": [], "missing_facts_asked": missing,
           "usage": {**run.usage, "seconds": round(run.usage["seconds"], 2)}}
    return out, run.trace
