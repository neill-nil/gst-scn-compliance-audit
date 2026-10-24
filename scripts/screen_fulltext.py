"""Screen GST-candidate High Court orders on their full text and tag which ones fit NoticeCheck.

For each case (latest order per CNR) it downloads the PDF, extracts text, and records
rule-based flags: in scope (CGST s.73/74 demand proceeding), excluded topics, which
procedural-defect families are argued, whether the order is final, whether it is a
consent/equity remand, and whether it contains an explicit holding.

Usage: python screen_fulltext.py <candidates.parquet> <work_dir> <court_code>[:sample] ...
  e.g. python screen_fulltext.py cands.parquet work 7_26 33_10:200 29_3:200
"""
import gzip
import hashlib
import json
import random
import re
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import duckdb

BUCKET = "https://indian-high-court-judgments.s3.ap-south-1.amazonaws.com"
RULE_VERSION = "2026-10-25.2"


def rx(p):
    return re.compile(p, re.I)


GST_STATUTE = rx(r"\b(C|S|D|TN|K|O|WB|UP|M|G|T|AP|I)?GST\s*Act|Goods and Services? Tax Act")
DEMAND_73_74 = rx(r"section\s*7[34]\b(?!\s*A)|\b7[34]\s*\(\s*(1|5|8|9|10)\s*\)|DRC\s*-?\s*0?[17]\b")
SCN = rx(r"show[\s-]*cause\s+notice|\bSCN\b|DRC\s*-?\s*0?1\b")
S74A = rx(r"section\s*74\s*A\b")
PRE_GST = rx(r"Central Excise Act|Finance Act,? 1994|Customs Act|Value Added Tax Act|\bVAT Act|Sales Tax Act")
EXCLUDE = {
    "bail_arrest": rx(r"\b(anticipatory\s+)?bail\b"),
    "detention_129_130": rx(r"section\s*1(29|30)\b|\bMOV\s*-?\s*\d|detention of (the )?(goods|vehicle|conveyance)"),
    "registration_cancellation": rx(r"cancell?ation of (the |its |his )?(GST )?registration|REG\s*-?\s*(17|19|31)\b"),
    "refund_54": rx(r"section\s*54\b|RFD\s*-?\s*0\d"),
    "appeal_only_107": rx(r"section\s*107\b|APL\s*-?\s*0\d"),
    "attachment_83": rx(r"section\s*83\b|provisional(ly)? attach"),
    "revocation_rule_23": rx(r"revocation of (the )?cancell?ation|rule\s*23\b"),
    "section_74A": rx(r"section\s*74\s*A\b"),
}
# Short orders with no facts of their own: excluded on a single hit when the order is <= 3 pages.
FACTLESS = rx(r"dismissed as withdrawn|withdrawn with liberty|disposed of in (the same )?terms of|"
              r"covered by (the )?(judgment|decision|order) (dated|of this court|passed)")
DEFECTS = {
    "hearing_75_4": rx(r"personal hearing|opportunity of (personal )?hearing|75\s*\(\s*4\s*\)|natural justice"),
    "service_169": rx(r"additional notices|section\s*169\b|not (been )?served|non[\s-]*service"),
    "limitation": rx(r"time[\s-]*barred|barred by limitation|7[34]\s*\(\s*10\s*\)|168\s*A\b"),
    "signature": rx(r"unsigned|not (been )?signed|without (any |the )?signature"),
    "summary_only_142": rx(r"summary of (the )?(show cause|SCN)|rule\s*142\s*\(\s*1\s*\)|only (a |the )?summary"),
    "non_speaking": rx(r"non[\s-]*speaking|non[\s-]*application of mind|cryptic|without (assigning|giving) (any )?reasons"),
    "beyond_scn_75_7": rx(r"75\s*\(\s*7\s*\)|beyond the (scope of the )?(show cause|SCN)"),
    "consolidated_scn": rx(r"consolidated (show cause|SCN|notice)|single (show cause|SCN) for (multiple|several|different)"),
    "adjournment_75_5": rx(r"75\s*\(\s*5\s*\)"),
}
FINAL = rx(r"(petition|appeal)s? (is|are|stands?|stand) (hereby )?(allowed|dismissed|disposed)|disposed of"
           r"|impugned (order|notice|SCN|demand)[^.]{0,80}(set aside|quashed)|(remanded|remitted) (back )?to")
CONSENT_EQUITY = rx(r"by consent|consent of (the )?(learned counsel|parties)|(does|do) not (have any )?(serious )?object"
                    r"|contentions (of the parties )?(are )?(kept|left) open|without (going into|expressing any (view|opinion) on|entering into) the merits"
                    r"|one more (chance|opportunity)|ends of justice|deposit\w*[^.]{0,40}\b(10|25)\s*(%|per\s?cent)")
HOLDING = rx(r"(we are|this court is|i am) (of the )?(considered |prima facie )?(view|opinion)|\bwe (hold|find)\b|it is (thus )?(held|clear) that"
             r"|in (clear |gross )?violation of|contrary to (the )?(mandate|provisions?) of|violat\w+ (of )?(the )?principles of natural justice"
             r"|(cannot|can not) be sustained|is (not )?sustainable|is not time[\s-]*barred|is time[\s-]*barred|within (the )?(stipulated|prescribed) (time|period)")


def latest_order_per_case(cands: Path, court: str):
    con = duckdb.connect()
    return con.sql(f"""
        select * from '{cands}' where court = '{court}'
        qualify row_number() over (partition by cnr order by decision_date desc, pdf_link desc) = 1
    """).df().to_dict("records")


def s3_key(r):
    bench = re.search(r"bench=([^/]+)", r["filename"]).group(1)
    return f"data/pdf/year={r['y']}/court={r['court']}/bench={bench}/{Path(r['pdf_link']).name}"


def fetch_text(r, work: Path):
    key = s3_key(r)
    txt_path = work / "text" / (Path(key).stem + ".txt.gz")
    meta_path = work / "text" / (Path(key).stem + ".json")
    if txt_path.exists() and meta_path.exists():
        return json.loads(meta_path.read_text()), gzip.decompress(txt_path.read_bytes()).decode()
    pdf = work / "tmp" / Path(key).name
    try:
        urllib.request.urlretrieve(f"{BUCKET}/{key}", pdf)
        data = pdf.read_bytes()
        info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        pages = int(m.group(1)) if (m := re.search(r"Pages:\s+(\d+)", info)) else 0
        text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    except Exception as e:
        return {"s3_key": key, "error": str(e)[:100]}, ""
    finally:
        pdf.unlink(missing_ok=True)
    meta = {"s3_key": key, "sha256": hashlib.sha256(data).hexdigest(), "pages": pages}
    txt_path.write_bytes(gzip.compress(text.encode()))
    meta_path.write_text(json.dumps(meta))
    return meta, text


def screen(r, work: Path):
    meta, text = fetch_text(r, work)
    row = {"court": r["court"], "cnr": r["cnr"], "title": r["title"], "decision_date": str(r["decision_date"])[:10],
           "rule_version": RULE_VERSION, **meta}
    if not text:
        return row
    t = re.sub(r"\s+", " ", text)
    body = t[500:5500]
    row.update({
        "chars_per_page": round(len(t) / max(meta["pages"], 1)),
        "text_hash": hashlib.sha1(re.sub(r"\W+", "", body).lower().encode()).hexdigest(),
        "gst_statute": bool(GST_STATUTE.search(t)),
        "scn": bool(SCN.search(t)),
        "demand_73_74": bool(DEMAND_73_74.search(t)),
        "s74A": bool(S74A.search(t)),
        "pre_gst_only": bool(PRE_GST.search(t)) and not GST_STATUTE.search(t),
        "excluded": [k for k, p in EXCLUDE.items() if len(p.findall(t)) >= 2]
                    + (["factless_short_order"] if meta["pages"] <= 3 and FACTLESS.search(t) else []),
        "defects": [k for k, p in DEFECTS.items() if p.search(t)],
        "final": bool(FINAL.search(t)),
        "consent_equity": bool(CONSENT_EQUITY.search(t)),
        "holdings": len(HOLDING.findall(t)),
    })
    in_scope = row["scn"] and row["demand_73_74"] and not row["excluded"] and not row["pre_gst_only"]
    row["in_scope"] = in_scope
    if not in_scope:
        row["bucket"] = "out_of_scope"
    elif not row["final"]:
        row["bucket"] = "not_final"
    elif not row["defects"]:
        row["bucket"] = "no_procedural_defect_argued"
    elif row["holdings"] >= 2 and meta["pages"] >= 4 and not row["consent_equity"]:
        row["bucket"] = "reasoned"
    else:
        row["bucket"] = "remand_or_short"
    return row


def main():
    cands, work = Path(sys.argv[1]), Path(sys.argv[2])
    (work / "text").mkdir(parents=True, exist_ok=True)
    (work / "tmp").mkdir(parents=True, exist_ok=True)
    random.seed(13)
    jobs = []
    for spec in sys.argv[3:]:
        court, _, n = spec.partition(":")
        rows = latest_order_per_case(cands, court)
        jobs += random.sample(rows, min(int(n), len(rows))) if n else rows
    with ThreadPoolExecutor(16) as ex:
        results = list(ex.map(lambda r: screen(r, work), jobs))
    seen = set()
    for row in results:
        h = row.get("text_hash")
        row["duplicate_of_earlier"] = bool(h and h in seen)
        if h:
            seen.add(h)
    (work / "screen.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in results))
    print(f"screened {len(results)} cases -> {work / 'screen.jsonl'}")


if __name__ == "__main__":
    main()
