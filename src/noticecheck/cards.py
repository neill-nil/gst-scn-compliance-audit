"""Check cards: one per defect type. A card says which provision applies, which facts the check needs, and
whether the verdict comes from a rule over the facts and tool results ("rule") or from the model ("model").

If a card's required facts are missing, the verdict is "can't tell", decided here, never by the model
(B1's main failure was answering "no defect" when the facts were silent).
These cards are a design decision (final_plan.md D1-D3); tune them on the dev split only.
"""
from src.noticecheck.record import contents, events, fact, has

from src.common.provisions import PROVISION, provision_for  # noqa: E402  (shared with the strict score)
MODEL_CARDS = {
    "reply_not_considered": {
        "needs": "a reply that was filed, and what the order says",
        "question": "A reply was filed. Does the record show the order rejected or ignored it without engaging with "
                    "its points (e.g. a one-line 'reply not satisfactory', or the order says no reply was filed)?"},
    "non_speaking_order": {
        "needs": "what the order says",
        "question": "Does the record show the order gives no real reasons: no facts and no basis for the decision "
                    "(s.75(6)), e.g. it only repeats the notice or says the reply is not satisfactory?"},
    "demand_beyond_scn": {
        "needs": "what the notice proposed and what the order demanded",
        "question": "Does the record show the order demands more than, or on grounds other than, those in the "
                    "notice (s.75(7)), e.g. a penalty or amount the notice did not propose?"},
    "section_74_ingredients": {
        "needs": "what the s.74 notice alleged",
        "question": "The notice was under s.74. Does the record show it alleges no fraud, wilful misstatement or "
                    "suppression of facts at all (only a mismatch or a technical difference)?"},
    "other_procedural": {
        "needs": "a specific procedural step described in the record",
        "question": "Apart from hearing, adjournment, reply, reasons, demand beyond the notice, service, signature, "
                    "summary-only notice, limitation and consolidated notices, does the record show any other clear "
                    "breach of GST procedure by the department? Answer can't tell unless the record states it plainly."},
}
CONTESTED = {"extension_notification_validity", "consolidated_scn"}  # D2: always contested when the point arises
TYPES = list(PROVISION)


def finding(defect, verdict, record, evidence=(), missing=(), confidence=0.9, note=None):
    out = {"type": defect, "verdict": verdict, "provision": provision_for(defect, record),
           "evidence": [{"source": "record", "ref": ref, "quote": q} for ref, q in evidence if q],
           "missing_facts": list(missing), "confidence": confidence}
    if note:
        out["note"] = note
    return out


def _ev(record, path):
    v, q, ref = fact(record, path)
    return (ref, q)


def _event_ev(evs):
    return [(f"events[{e.get('type')}]", e.get("quote")) for e in evs]


# --- rule cards -------------------------------------------------------------------------------------------
def hearing(record, tools):
    if not record.get("notices"):
        return finding("hearing_75_4", "cant_tell", record, missing=["notices.0.hearing_date_given", "hearing events"])
    given = fact(record, "notices.0.hearing_date_given")[0]
    hdate, rdue = fact(record, "notices.0.hearing_date")[0], fact(record, "notices.0.reply_due")[0]
    if given is False:
        return finding("hearing_75_4", "defect", record, [_ev(record, "notices.0.hearing_date_given")])
    if hdate and rdue and hdate <= rdue:  # hearing fixed on or before the day the reply is due
        return finding("hearing_75_4", "defect", record,
                       [_ev(record, "notices.0.hearing_date"), _ev(record, "notices.0.reply_due")], confidence=0.75)
    held = events(record, "hearing_attended", "hearing_scheduled")
    if held or given is True:
        return finding("hearing_75_4", "no_defect", record,
                       _event_ev(held) or [_ev(record, "notices.0.hearing_date_given")], confidence=0.7)
    return finding("hearing_75_4", "cant_tell", record,
                   missing=["notices.0.hearing_date_given", "notices.0.hearing_date", "hearing events"])


def signature(record, tools):
    for path in ("notices.0.signed", "order.signed"):
        if fact(record, path)[0] is False:
            return finding("signature", "defect", record, [_ev(record, path)])
    if has(record, "notices.0.signed") or has(record, "order.signed"):
        return finding("signature", "no_defect", record,
                       [_ev(record, p) for p in ("notices.0.signed", "order.signed") if has(record, p)], confidence=0.8)
    return finding("signature", "cant_tell", record, missing=["notices.0.signed", "order.signed"])


def service(record, tools):
    modes = [(p, fact(record, p)[0]) for p in ("notices.0.service_mode", "order.service_mode") if has(record, p)]
    if not modes:
        return finding("service_169", "cant_tell", record, missing=["notices.0.service_mode", "order.service_mode"])
    emailed = any(m == "email" for _, m in modes)
    bad = [(p, m) for p, m in modes if m in ("portal_additional_notices_tab", "not_served")]
    if bad and emailed:  # D2: courts split when the notice was also emailed
        return finding("service_169", "contested", record, [_ev(record, p) for p, _ in modes], confidence=0.6,
                       note="uploaded to the Additional Notices tab but also emailed; High Courts differ")
    if bad:
        return finding("service_169", "defect", record, [_ev(record, p) for p, _ in bad], confidence=0.8)
    if all(m == "portal_unspecified" for _, m in modes):
        return finding("service_169", "cant_tell", record, missing=["which portal tab or other mode was used"])
    return finding("service_169", "no_defect", record, [_ev(record, p) for p, _ in modes], confidence=0.7)


def summary_only(record, tools):
    v = fact(record, "notices.0.summary_only")[0]
    if v is True:
        return finding("summary_only", "defect", record, [_ev(record, "notices.0.summary_only")])
    if v is False:
        return finding("summary_only", "no_defect", record, [_ev(record, "notices.0.summary_only")], confidence=0.8)
    return finding("summary_only", "cant_tell", record, missing=["notices.0.summary_only"])


def _limitation_results(tools):
    return [t for t in tools if t["tool"] == "limitation_check" and t["out"].get("ok")]


def limitation(record, tools):
    results = _limitation_results(tools)
    if not results:
        need = [p for p in ("provision", "financial_years", "notices.0.date", "order.date") if not has(record, p)]
        return finding("limitation", "cant_tell", record, missing=need or ["limitation_check result"])
    late = [r for r in results if r["out"]["result"]["scn_in_time"] is False or r["out"]["result"]["order_in_time"] is False]
    contested = [r for r in results if r["out"]["result"]["contested"]]
    ev = [_ev(record, p) for p in ("financial_years", "notices.0.date", "order.date") if has(record, p)]
    if contested:
        return finding("limitation", "contested", record, ev, confidence=0.6,
                       note="in time only because of the s.168A extension notifications, whose validity is challenged")
    if late:
        return finding("limitation", "defect", record, ev, confidence=0.85)
    known = any(r["out"]["result"]["scn_in_time"] is not None or r["out"]["result"]["order_in_time"] is not None
                for r in results)
    return finding("limitation", "no_defect" if known else "cant_tell", record, ev,
                   missing=[] if known else ["notices.0.date", "order.date"], confidence=0.8)


def extension_validity(record, tools):
    results = _limitation_results(tools)
    if any(r["out"]["result"]["contested"] for r in results):
        return finding("extension_notification_validity", "contested", record,
                       [_ev(record, p) for p in ("financial_years", "order.date") if has(record, p)], confidence=0.7,
                       note="the order is in time only under the s.168A extension notifications")
    if results:
        return finding("extension_notification_validity", "no_defect", record, confidence=0.7,
                       note="the dates are in time (or late) whether or not the extensions apply")
    return finding("extension_notification_validity", "cant_tell", record,
                   missing=["provision", "financial_years", "order.date"])


def consolidated(record, tools):
    fys = fact(record, "financial_years")[0]
    if not fys:
        return finding("consolidated_scn", "cant_tell", record, missing=["financial_years"])
    if len(fys) > 1 and len(record.get("notices") or []) <= 1:
        return finding("consolidated_scn", "contested", record, [_ev(record, "financial_years")], confidence=0.7,
                       note="one notice for several financial years; High Courts differ on whether this is allowed")
    return finding("consolidated_scn", "no_defect", record, [_ev(record, "financial_years")], confidence=0.8)


def adjournment(record, tools):
    asked = events(record, "adjournment_requested")  # a request for more time to reply is not a hearing adjournment
    if not asked:
        return finding("adjournment_75_5", "cant_tell", record, missing=["adjournment requests"])
    granted = events(record, "hearing_adjourned")
    if len(granted) >= 3:  # s.75(5): no more than three adjournments
        return finding("adjournment_75_5", "no_defect", record, _event_ev(granted), confidence=0.7)
    if not granted:
        return finding("adjournment_75_5", "defect", record, _event_ev(asked), confidence=0.55,
                       note="adjournment asked for and none recorded as granted")
    return finding("adjournment_75_5", "cant_tell", record, _event_ev(asked + granted),
                   missing=["whether the request was refused"])


RULE_CARDS = {"hearing_75_4": hearing, "signature": signature, "service_169": service, "summary_only": summary_only,
              "limitation": limitation, "extension_notification_validity": extension_validity,
              "consolidated_scn": consolidated, "adjournment_75_5": adjournment}


def model_card_ready(defect: str, record: dict) -> tuple[bool, list[str]]:
    """Gate for model-judged cards: are the facts they need present? (Missing -> can't tell, decided here.)"""
    order = contents(record, "order_reasoning")
    if defect == "reply_not_considered":
        if events(record, "reply_not_filed") and not events(record, "reply_filed"):
            return False, ["__no_reply__"]
        return bool(events(record, "reply_filed") and order), [p for p, ok in (
            ("reply_filed event", events(record, "reply_filed")), ("order contents", order)) if not ok]
    if defect == "non_speaking_order":
        return bool(order), ([] if order else ["order contents"])
    if defect == "demand_beyond_scn":
        scn = contents(record, "scn_ground")
        return bool(scn and order), [p for p, ok in (("notice grounds", scn), ("order contents", order)) if not ok]
    if defect == "section_74_ingredients":
        if fact(record, "provision")[0] == "73":
            return False, ["__not_74__"]
        ground = contents(record, "scn_ground", "fraud_allegation")
        return bool(fact(record, "provision")[0] == "74" and ground), ([] if ground else ["notice grounds"])
    return bool(record.get("events") or record.get("document_contents")), ["procedural history"]
