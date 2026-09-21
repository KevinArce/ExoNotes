"""ExoNotes Kepler task 0 - acquire the Kepler Certified False Positive table (`fpwg`).

`PLAN.md` section 8 item 2. The table is documented
(https://exoplanetarchive.ipac.caltech.edu/docs/API_fpwg_columns.html) but NOT served by any
programmatic interface: it is absent from TAP_SCHEMA.tables, and the legacy API answers
"not a valid table" for `fpwg` and every variant tried (WORKLOG.md 2026-09-21T02:05Z).

It IS served by the archive's interactive table viewer, and this script replays exactly what
that viewer's "Download Table" button does, found by reading its JavaScript
(applications/TblView10.4/tblView.js, applications/IceTable10.4/iceTable.js):

    1. GET  /cgi-bin/TblView/nph-tblView?app=ExoTbls&config=fpwg
            -> the server provisions a fresh workspace and embeds its id in the page
    2. GET  /cgi-bin/FileDownload/nph-download?url=<ws>/fpwg_params.json
            -> `tblPaths['fpwg']`, the server-side path of the table file
    3. GET  /cgi-bin/IceTable/nph-iceTbl?...&cmd=newtable
            -> seeds the workspace; the XML reply carries `total_count`
    4. POST /cgi-bin/IceTable/nph-iceTblDownload  format=CSV columns=all rows=all
            -> the full table as CSV

Stages, run in order by default; `--stage NAME` runs exactly one:

    fetch    download to data/kepler/fpwg.csv, unless it exists (`--refresh` to force)
    persist  parse, assert integrity, write data/kepler.duckdb::kepler_fpwg_raw

Idempotent: yes. The raw CSV is cached, so a re-run does no network I/O. The DuckDB write is
CREATE OR REPLACE, into a SEPARATE database file: the TESS study's data/exonotes.duckdb and
its registered matrix checksum are never touched by the Kepler work.

The raw file's own sha256 changes on every download, because the archive stamps the download
time into a `#` header line. The checksum reported is therefore over the header-stripped body,
which is stable for as long as the table itself is.

Integrity is asserted, not assumed (`pd.read_csv` has mis-parsed this project's data silently
before -- WORKLOG defect 15):
    * data rows == the `total_count` the server reported at step 3
    * every row has the header's field count, under the stdlib csv parser
    * the stdlib parser and pandas agree on the row count
    * `kepoi_name` is unique, and `fpwg_comment` is present

Every column is kept as VARCHAR, unmodified. Nothing here chooses a corpus or a label; that is
registered in PREREGISTRATION.md before it is computed.
"""
import argparse, csv, hashlib, io, json, pathlib, re, sys

import duckdb, pandas as pd, requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "kepler"
RAW = RAW_DIR / "fpwg.csv"
META = RAW_DIR / "fpwg_fetch.json"
DB = ROOT / "data" / "kepler.duckdb"

BASE = "https://exoplanetarchive.ipac.caltech.edu"
CONFIG = "fpwg"
TIMEOUT = 300

WS_RX = re.compile(r"'(\d[\d._]*/TblView/\d[\d._]*)'")
COUNT_RX = re.compile(r'total_count="(\d+)"')


def fetch() -> None:
    s = requests.Session()
    page = s.get(f"{BASE}/cgi-bin/TblView/nph-tblView",
                 params={"app": "ExoTbls", "config": CONFIG}, timeout=TIMEOUT)
    page.raise_for_status()
    ws = WS_RX.findall(page.text)
    if len(set(ws)) != 1:
        sys.exit(f"expected exactly one workspace id in the viewer page, found {sorted(set(ws))}")
    ws = ws[0]

    params = s.get(f"{BASE}/cgi-bin/FileDownload/nph-download",
                   params={"url": f"{ws}/{CONFIG}_params.json"}, timeout=TIMEOUT)
    params.raise_for_status()
    tbl = params.json()["tblPaths"][CONFIG]

    seed = s.get(f"{BASE}/cgi-bin/IceTable/nph-iceTbl", timeout=TIMEOUT, params={
        "log": "TblView.ExoplanetArchive", "workspace": ws, "table": tbl,
        "pltxaxis": "", "pltyaxis": "", "checkbox": 1, "initialcheckedval": 0,
        "splitlabel": 0, "cmd": "newtable"})
    seed.raise_for_status()
    m = COUNT_RX.search(seed.text)
    if not m or "<![CDATA[ok]]>" not in seed.text:
        sys.exit(f"workspace seed did not report ok + total_count: {seed.text[:400]!r}")
    total = int(m.group(1))

    dl = s.post(f"{BASE}/cgi-bin/IceTable/nph-iceTblDownload", timeout=TIMEOUT, data={
        "workspace": ws, "table": tbl, "format": "CSV", "user": "", "label": "",
        "columns": "all", "rows": "all", "mission": "ExoplanetArchive"})
    dl.raise_for_status()
    if not dl.headers.get("content-type", "").startswith("text/csv"):
        sys.exit(f"download is not CSV ({dl.headers.get('content-type')}): {dl.text[:400]!r}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    RAW.write_bytes(dl.content)
    META.write_text(json.dumps({"server_total_count": total, "table_path": tbl,
                                "bytes": len(dl.content)}, indent=2) + "\n")
    print(f"fetched {len(dl.content):,} bytes; server total_count={total:,}")


def split(raw: str) -> tuple[list[str], str]:
    lines = raw.splitlines(keepends=True)
    return ([l for l in lines if l.startswith("#")],
            "".join(l for l in lines if not l.startswith("#")))


def persist() -> None:
    raw = RAW.read_text(encoding="utf-8")
    total = json.loads(META.read_text())["server_total_count"]
    _, body = split(raw)

    rows = list(csv.reader(io.StringIO(body)))
    header, data = rows[0], rows[1:]
    bad = [i for i, r in enumerate(data) if len(r) != len(header)]
    df = pd.read_csv(io.StringIO(body), dtype=str, keep_default_na=False)

    checks = {
        f"rows == server total_count ({total:,})": len(data) == total,
        f"every row has {len(header)} fields": not bad,
        "csv and pandas agree on rows": len(df) == len(data),
        "kepoi_name unique": df["kepoi_name"].is_unique,
        "fpwg_comment present": "fpwg_comment" in df.columns,
    }
    for name, ok in checks.items():
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if not all(checks.values()):
        sys.exit("integrity check failed; nothing persisted")

    body_sha = hashlib.sha256(body.encode()).hexdigest()[:16]
    with duckdb.connect(str(DB)) as con:
        con.register("fpwg_df", df)
        con.execute("create or replace table kepler_fpwg_raw as select * from fpwg_df")
        n = con.execute("select count(*) from kepler_fpwg_raw").fetchone()[0]
    has_text = int((df["fpwg_comment"].str.strip() != "").sum())
    print(f"persisted kepler_fpwg_raw: {n:,} rows x {len(df.columns)} cols; "
          f"non-empty fpwg_comment {has_text:,}; body sha256[:16] = {body_sha}")


STAGES = {"fetch": fetch, "persist": persist}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stage", choices=STAGES)
    ap.add_argument("--refresh", action="store_true", help="re-download even if cached")
    a = ap.parse_args()
    if a.stage in (None, "fetch"):
        if RAW.exists() and META.exists() and not a.refresh:
            print(f"cached: {RAW.relative_to(ROOT)} (use --refresh to re-download)")
        else:
            fetch()
    if a.stage in (None, "persist"):
        persist()
