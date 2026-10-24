"""Find GST-related High Court orders in the AWS eCourts bucket without downloading full metadata.

DuckDB reads only the needed parquet columns over HTTPS, so no AWS account is required.

Usage: python find_candidates.py <out.parquet> [years, default 2024-2026]
"""
import re
import sys
import urllib.parse
import urllib.request

import duckdb

BUCKET = "https://indian-high-court-judgments.s3.ap-south-1.amazonaws.com"
TERMS = r"(goods and services? tax|cgst|sgst|dgst|igst|\bgst\b|state tax officer|sales tax officer|commercial tax|drc-0)"


def metadata_keys(year: int) -> list[str]:
    keys, token = [], None
    while True:
        url = f"{BUCKET}/?list-type=2&prefix=metadata/parquet/year={year}/"
        if token:
            url += "&continuation-token=" + urllib.parse.quote(token)
        xml = urllib.request.urlopen(url).read().decode()
        keys += re.findall(r"<Key>([^<]+\.parquet)</Key>", xml)
        m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", xml)
        if not m:
            return keys
        token = m.group(1)


def main():
    out = sys.argv[1]
    years = range(int(sys.argv[2]), int(sys.argv[3]) + 1) if len(sys.argv) > 3 else range(2024, 2027)
    urls = [f"{BUCKET}/{k}" for y in years for k in metadata_keys(y)]
    con = duckdb.connect()
    con.sql("install httpfs; load httpfs; set enable_progress_bar=false")
    con.sql(f"""
        copy (
          select court, year(decision_date) as y, cnr, title, description, judge, decision_date,
                 disposal_nature, pdf_link, filename
          from read_parquet({urls}, filename=true, union_by_name=true)
          where regexp_matches(lower(title || ' ' || coalesce(description, '')), '{TERMS}')
        ) to '{out}'""")
    print(con.sql(f"select court, y, count(distinct cnr) as cases from '{out}' group by all order by court, y"))


if __name__ == "__main__":
    main()
