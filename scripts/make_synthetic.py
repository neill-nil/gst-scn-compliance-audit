"""Synthetic stress set (proposal deliverable 2): proceeding records with ONE planted procedural defect, plus clean
controls with none. Unlike the real test set, every fact the checks need is stated, so this measures (a) whether a
system catches a defect when the facts are there and (b) its false-alarm rate on valid proceedings.

100 cases, seed 15: 8 per defect type x 7 types = 56 defective, 44 clean. Every record is built so all 7 types are
decidable from its facts; the answer key labels the planted type defect_found and the other 6 defect_rejected.
Types not built here (adjournment, demand beyond notice, consolidated notice, s.74 ingredients, extension
notifications, other) are not labelled; flags on them count as "unargued".

Facts follow the schema 0.1 facts format with a short synthetic "quote" for each (as if from a judgment), so the
verifier can check quotes. Dates use FY 2021-22 and 2022-23 (annual-return due dates verified, no s.168A extension).
Deadlines come from the CGST Act s.73(10)/73(2): order within 3 years of the annual-return due date, notice at least
3 months before that.

Usage: python -m scripts.make_synthetic  ->  data/synthetic/{records.jsonl, full_record.jsonl}, data/splits/synthetic.txt
"""
import json
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "synthetic"
TYPES = ["hearing_75_4", "signature", "summary_only", "service_169", "limitation", "reply_not_considered",
         "non_speaking_order"]
DEADLINES = {"2021-22": ("2025-09-30", "2025-12-31"), "2022-23": ("2026-09-30", "2026-12-31")}  # notice, order
N_PER_TYPE, N_CLEAN, SEED = 8, 44, 15
TRADES = ["trading of steel pipes", "civil works contracts", "wholesale of textiles", "restaurant services",
          "transport of goods by road", "manufacture of plastic containers", "sale of electronic goods"]
GROUNDS = ["excess input tax credit compared with GSTR-2B", "short payment of tax on outward supplies declared in GSTR-1",
           "input tax credit on invoices from suppliers whose registration was cancelled",
           "mismatch between turnover in GSTR-1 and GSTR-3B"]
SERVICE_OK = ["registered_post", "hand_delivery", "portal_notices_tab"]
SERVICE_TEXT = {"registered_post": "was sent by registered post with acknowledgement due and received by the taxpayer",
                "hand_delivery": "was delivered by hand to the taxpayer's authorised signatory",
                "portal_notices_tab": "was uploaded under the 'Notices' tab of the GST portal and the taxpayer viewed it",
                "not_served": "was never served on the taxpayer by any of the modes in section 169",
                "portal_additional_notices_tab": "was only uploaded under the 'Additional Notices and Orders' tab of the "
                                                 "GST portal and was not sent by any other mode"}


def d(x):
    return date.fromisoformat(x) if isinstance(x, str) else x


def fmt(x):
    return d(x).strftime("%d.%m.%Y")


def F(value, quote, para):
    return {"value": value, "quote": quote, "para": para}


def build(i, planted, rng):
    fy = rng.choice(list(DEADLINES))
    scn_last, order_last = map(d, DEADLINES[fy])
    scn = scn_last - timedelta(days=rng.randint(90, 400))
    reply_due = scn + timedelta(days=30)
    hearing = reply_due + timedelta(days=rng.randint(7, 21))
    order = min(hearing + timedelta(days=rng.randint(30, 120)), order_last - timedelta(days=rng.randint(5, 40)))
    trade, ground = rng.choice(TRADES), rng.choice(GROUNDS)
    amount = rng.randint(3, 90) * 100000 + rng.randint(0, 99999)
    mode = rng.choice(SERVICE_OK)
    reply_filed, signed_notice, signed_order, summary_only, hearing_given = True, True, True, False, True
    variant = rng.random() < 0.5

    if planted == "limitation":
        if variant:   # order after the time limit
            order = order_last + timedelta(days=rng.randint(15, 200))
        else:         # notice later than 3 months before the order deadline (and the order after it too)
            scn = scn_last + timedelta(days=rng.randint(10, 60))
            reply_due, hearing = scn + timedelta(days=30), scn + timedelta(days=45)
            order = order_last + timedelta(days=rng.randint(10, 90))
    if planted == "service_169":
        mode = "not_served" if variant else "portal_additional_notices_tab"
    if planted == "signature":
        signed_notice, signed_order = (False, True) if variant else (True, False)
    if planted == "summary_only":
        summary_only = True
    if planted == "non_speaking_order":
        reply_filed = False   # keeps "reply ignored" out of it: there is no reply to ignore

    p = iter(range(2, 40))
    notice = {"date": F(scn.isoformat(), f"A show cause notice dated {fmt(scn)} was issued to the petitioner", next(p)),
              "reply_due": F(reply_due.isoformat(), f"The notice required a reply on or before {fmt(reply_due)}", next(p)),
              "hearing_date_given": F(None, None, None), "hearing_date": F(None, None, None),
              "service_mode": F(mode, f"The show cause notice {SERVICE_TEXT[mode]}", next(p)),
              "signed": F(signed_notice, "The show cause notice was digitally signed by the proper officer" if signed_notice
                          else "The show cause notice uploaded on the portal does not bear the signature of the proper officer", next(p)),
              "summary_only": F(summary_only, "Only a summary of the notice in Form GST DRC-01 was uploaded; no show cause "
                                "notice setting out the grounds was issued" if summary_only else
                                "The show cause notice set out the grounds in full, with a summary in Form GST DRC-01", next(p))}
    events = [{"date": scn.isoformat(), "type": "scn_issued", "quote": notice["date"]["quote"], "para": notice["date"]["para"]}]
    if planted == "hearing_75_4":
        notice["hearing_date_given"] = F(False, "The notice did not fix any date for a personal hearing, and no hearing "
                                         "was offered before the order" if variant else
                                         "The column for the date of personal hearing in the notice reads 'NA', and no "
                                         "hearing was held before the adverse order", next(p))
    else:
        q = f"The notice fixed the personal hearing on {fmt(hearing)}"
        para = next(p)
        notice["hearing_date_given"] = F(True, q, para)
        notice["hearing_date"] = F(hearing.isoformat(), q, para)
    if reply_filed:
        rdate = reply_due - timedelta(days=rng.randint(0, 10))
        events.append({"date": rdate.isoformat(), "type": "reply_filed", "para": next(p),
                       "quote": f"The petitioner filed a reply dated {fmt(rdate)} with copies of the invoices and e-way bills"})
    else:
        events.append({"date": None, "type": "reply_not_filed", "para": next(p),
                       "quote": "The petitioner did not file any reply to the show cause notice"})
    if planted != "hearing_75_4":
        para = next(p)
        events.append({"date": hearing.isoformat(), "type": "hearing_scheduled", "para": para,
                       "quote": f"A personal hearing was scheduled on {fmt(hearing)}"})
        events.append({"date": hearing.isoformat(), "type": "hearing_attended", "para": para,
                       "quote": f"The petitioner's representative attended the hearing on {fmt(hearing)}"})
    events.append({"date": order.isoformat(), "type": "order_passed", "para": next(p),
                   "quote": f"The proper officer passed the order dated {fmt(order)} under section 73(9) confirming a demand of Rs.{amount:,}"})

    docs = [{"type": "scn_ground", "para": next(p),
             "quote": f"The notice proposed a demand of Rs.{amount:,} on the ground of {ground}"}]
    if reply_filed:
        docs.append({"type": "reply_point", "para": next(p),
                     "quote": "The reply stated that every invoice was issued by a registered supplier who had filed returns, "
                              "and enclosed the supplier-wise reconciliation"})
    if planted == "reply_not_considered":
        q = ("The order states that no reply was received from the petitioner and confirms the demand on the basis of the "
             "GSTR-2B figures" if variant else
             "The order sets out the GSTR-2B figures and confirms the demand; it does not mention the reply or the "
             "supplier-wise reconciliation filed with it")
    elif planted == "non_speaking_order":
        q = ("The order reads in full: 'The demand proposed in the show cause notice is confirmed.'" if variant else
             "The order states only that the proposal in the notice is confirmed, without referring to any fact, document or reason")
    elif reply_filed:
        q = ("The order discusses the reply and the reconciliation, accepts the invoices of suppliers who filed returns, "
             f"and confirms Rs.{amount // 3:,} because the remaining suppliers' registrations were cancelled before the invoice dates")
    else:
        q = (f"The order notes that no reply was filed, compares the GSTR-1 and GSTR-3B figures for {fy} month by month, "
             "and confirms the difference with interest under section 50")
    docs.append({"type": "order_reasoning", "para": next(p), "quote": q})

    facts = {"provision": F("73", "The proceedings were initiated under Section 73 of the CGST Act, 2017", 1),
             "financial_years": F([fy], f"for the financial year {fy}", 1),
             "notices": [notice],
             "order": {"date": F(order.isoformat(), f"order dated {fmt(order)}", events[-1]["para"]),
                       "signed": F(signed_order, "The order was digitally signed by the proper officer" if signed_order else
                                   "The order uploaded on the portal is unsigned", next(p)),
                       "service_mode": F(mode if planted != "service_169" else "registered_post",
                                         "The order was served on the petitioner" + (" by registered post" if planted == "service_169" else ""), next(p))},
             "events": events, "document_contents": docs}
    cnr = f"SYN{i:04d}"
    gold = {"cnr": cnr, "schema_version": "0.1", "court": "Synthetic", "case_no": f"SYN/{i}/{fy}",
            "decision_date": (order + timedelta(days=200)).isoformat(), **facts,
            "defects_argued": [{"type": t, "finding": "defect_found" if t == planted else "defect_rejected",
                                "contested": False, "quote": None, "para": None, "note": "synthetic, planted" if t == planted else "synthetic, clean"}
                               for t in TYPES],
            "outcome": {"disposition": "synthetic", "remanded": False},
            "annotation": {"set": "synthetic", "planted": planted, "variant": "a" if variant else "b", "seed": SEED}}
    return gold


def main():
    rng = random.Random(SEED)
    plan = [t for t in TYPES for _ in range(N_PER_TYPE)] + [None] * N_CLEAN
    rng.shuffle(plan)
    golds = [build(i + 1, planted, rng) for i, planted in enumerate(plan)]
    from src.baselines.inputs import build_view
    from src.prefill.schema import FACTS_SCHEMA
    import jsonschema
    v = jsonschema.Draft202012Validator(FACTS_SCHEMA)
    for g in golds:
        errs = list(v.iter_errors({k: g[k] for k in ("provision", "financial_years", "notices", "order", "events", "document_contents")}))
        assert not errs, (g["cnr"], errs[0].message)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "records.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(g, ensure_ascii=False) + "\n" for g in golds)
    with open(OUT / "full_record.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(build_view(g, "full_record"), ensure_ascii=False) + "\n" for g in golds)
    (ROOT / "data/splits/synthetic.txt").write_text("".join(g["cnr"] + "\n" for g in golds))
    from collections import Counter
    print(f"wrote {len(golds)} cases: " + ", ".join(f"{k or 'clean'} {v}" for k, v in Counter(g["annotation"]["planted"] for g in golds).items()))


if __name__ == "__main__":
    main()
