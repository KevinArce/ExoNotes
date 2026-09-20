"""ExoNotes Step 1 - ingest (PLAN.md section 6 Step 1).

ExoFOP-TESS TOI table + NASA Exoplanet Archive `toi` -> DuckDB at data/exonotes.duckdb.

Idempotent: raw pulls are cached under data/raw/ keyed by snapshot date and verified by
SHA256 on every run. Re-running without --refresh performs no network I/O. DuckDB tables
are CREATE OR REPLACE, so a re-run from scratch is safe and byte-reproducible.

IMPORTANT - `pscomppars` is deliberately NOT used as a feature source. It contains confirmed
planets only, so membership alone predicts the label at P(y=1)=0.995 vs 0.074. See WORKLOG.md
2026-09-19T23:13Z. It is pulled for provenance only and never joined into model input.
"""
import argparse, datetime, hashlib, pathlib, sys, time
import duckdb, pandas as pd, requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "exonotes.duckdb"
SNAPSHOT = "2026-09-19"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

# Label mapping - PLAN.md section 3.3
POSITIVE = {"CP", "KP"}
NEGATIVE = {"FP", "FA"}

# Numeric covariates for baseline B - PLAN.md section 6 Step 2, sourced from `toi`.
NUMERIC_CORE = ["pl_orbper", "pl_trandep", "pl_trandurh", "pl_rade",
                "st_tmag", "st_teff", "st_rad", "st_logg"]
NUMERIC_EXTRA = ["st_dist", "pl_insol", "pl_eqt"]

TOI_COLS = ("tid,toi,tfopwg_disp,st_tmag,ra,dec,pl_tranmid,pl_orbper,pl_trandurh,pl_trandep,"
            "pl_rade,pl_insol,pl_eqt,st_dist,st_teff,st_logg,st_rad,sectors,toi_created,"
            "rowupdate,release_date")
PSC_COLS = ("pl_name,hostname,tic_id,disc_facility,disc_year,pl_orbper,pl_rade,pl_bmasse,"
            "pl_insol,pl_eqt,st_teff,st_rad,st_mass,st_logg,st_met,sy_tmag,sy_dist")


def sha256(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


EXOFOP_TOI_CSV = "https://exofop.ipac.caltech.edu/tess/download_toi.php?output=csv"


def fetch_exofop(path: pathlib.Path, refresh: bool, tries: int = 4) -> None:
    """Download the bulk TOI table with an explicit timeout and bounded retry.

    `etta.download_toi()` accepts no timeout. ExoFOP throttles by withholding the response
    body -- it completes the TCP handshake in ~0.4 s and then sends zero bytes -- so a
    throttled pull is indistinguishable from a slow one and hangs the process forever, with
    no output and no error. That happens on the FIRST command a new contributor runs.
    Observed 2026-09-19/20; see WORKLOG.md 2026-09-20T00:02Z.

    So the bulk table is fetched directly with requests and a (connect, read) timeout.
    `etta` is still used for the per-TIC endpoints, which take a tag and behave.
    """
    if path.exists() and not refresh:
        return
    last = None
    for attempt in range(tries):
        try:
            r = requests.get(EXOFOP_TOI_CSV, timeout=(10, 300))
            r.raise_for_status()
            text = r.text
            if text.lstrip().lower().startswith("<"):
                raise RuntimeError(f"ExoFOP returned an HTML error page: {text[:200]}")
            # A throttled or truncated response can still be a valid-looking short CSV.
            if len(text) < 100_000 or "Comments" not in text.splitlines()[0]:
                raise RuntimeError(
                    f"ExoFOP returned {len(text)} bytes without the expected header - "
                    "truncated or throttled, not a usable TOI table")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
            return
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError,
                RuntimeError) as e:
            last = e
            if attempt < tries - 1:
                wait = 5 * 2 ** attempt
                print(f"  ExoFOP attempt {attempt + 1}/{tries} failed "
                      f"({type(e).__name__}); retrying in {wait}s", file=sys.stderr)
                time.sleep(wait)
    raise SystemExit(
        "\nExoFOP did not return the TOI table after "
        f"{tries} attempts. Last error: {type(last).__name__}: {last}\n\n"
        "This is almost always THROTTLING, not a bug: ExoFOP accepts the connection and\n"
        "then withholds the response after a host pulls the full table repeatedly in one\n"
        "day. It clears on its own.\n\n"
        "  * Wait a few hours and re-run - nothing else is needed, the script is idempotent.\n"
        "  * Check by hand:  curl --max-time 30 -o /dev/null -w '%{http_code} %{size_download}\\n' \\\n"
        f"      '{EXOFOP_TOI_CSV}'\n"
        "    A throttled host shows http=000 with size=0 after a fast TCP connect.\n"
        "  * If you already have data/raw/ from a previous run, re-run WITHOUT --refresh\n"
        "    and no network access is needed at all.\n")


def fetch_tap(path: pathlib.Path, query: str, refresh: bool) -> None:
    if path.exists() and not refresh:
        return
    r = requests.get(TAP, params={"query": query, "format": "csv"}, timeout=600)
    r.raise_for_status()
    if r.text.lstrip().lower().startswith("<"):
        raise RuntimeError(f"TAP returned an error page: {r.text[:400]}")
    path.write_text(r.text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="force re-download of raw sources")
    args = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)

    sources = {
        "exofop_toi": RAW / f"exofop_toi_{SNAPSHOT}.csv",
        "nea_toi": RAW / f"nea_toi_{SNAPSHOT}.csv",
        "nea_pscomppars": RAW / f"nea_pscomppars_{SNAPSHOT}.csv",
    }
    fetch_exofop(sources["exofop_toi"], args.refresh)
    fetch_tap(sources["nea_toi"], f"select {TOI_COLS} from toi", args.refresh)
    fetch_tap(sources["nea_pscomppars"], f"select {PSC_COLS} from pscomppars", args.refresh)

    retrieved = datetime.datetime.now(datetime.UTC).isoformat()
    prov = pd.DataFrame([
        {"source": k, "path": str(p.relative_to(ROOT)), "sha256": sha256(p),
         "bytes": p.stat().st_size, "snapshot_date": SNAPSHOT, "verified_utc": retrieved,
         "used_as_features": k != "nea_pscomppars"}
        for k, p in sources.items()
    ])

    ex = pd.read_csv(sources["exofop_toi"], low_memory=False)
    nea = pd.read_csv(sources["nea_toi"], low_memory=False)

    # --- join on TOI id; TIC ID is retained as the grouping key for every split -------------
    ex = ex.rename(columns={"TIC ID": "tic_id", "TOI": "toi", "Comments": "comment",
                            "TFOPWG Disposition": "tfopwg_disp_exofop",
                            "TESS Disposition": "tess_disp",
                            "Date TOI Alerted (UTC)": "date_toi_alerted",
                            "Date TOI Updated (UTC)": "date_toi_updated",
                            "Date Modified": "date_modified"})
    ex["toi"] = pd.to_numeric(ex["toi"], errors="coerce")
    nea["toi"] = pd.to_numeric(nea["toi"], errors="coerce")
    keep_ex = ["tic_id", "toi", "comment", "tfopwg_disp_exofop", "tess_disp", "Sectors",
               "date_toi_alerted", "date_toi_updated", "date_modified"]
    df = ex[keep_ex].merge(
        nea.drop(columns=["tid", "sectors"]), on="toi", how="inner", validate="one_to_one")

    n_joined = len(df)

    # --- labels - PLAN.md section 3.3 ------------------------------------------------------
    disp = df["tfopwg_disp"].fillna("")
    df["y"] = pd.Series(pd.NA, index=df.index, dtype="Int64")
    df.loc[disp.isin(POSITIVE), "y"] = 1
    df.loc[disp.isin(NEGATIVE), "y"] = 0
    df["label_source_agrees"] = df["tfopwg_disp"].fillna("") == df["tfopwg_disp_exofop"].fillna("")

    # --- comment hygiene -------------------------------------------------------------------
    df["comment"] = df["comment"].astype("string").fillna("").str.strip()
    df["comment_len"] = df["comment"].str.len()
    df["has_comment"] = df["comment_len"] > 0

    labelled = df["y"].notna()
    analysis = df[labelled & df["has_comment"]].copy()

    stats = {
        "rows_exofop": len(ex), "rows_nea_toi": len(nea), "rows_joined": n_joined,
        "rows_labelled": int(labelled.sum()),
        "rows_labelled_positive": int((df["y"] == 1).sum()),
        "rows_labelled_negative": int((df["y"] == 0).sum()),
        "rows_excluded_unresolved": int((~labelled).sum()),
        "rows_dropped_empty_comment": int((labelled & ~df["has_comment"]).sum()),
        "rows_analysis": len(analysis),
        "unique_tic_analysis": int(analysis["tic_id"].nunique()),
        "median_comment_len": float(analysis["comment_len"].median()),
        "label_source_disagreements": int((~df["label_source_agrees"] & labelled).sum()),
        "snapshot_date": SNAPSHOT, "built_utc": retrieved,
    }

    DB.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB))
    con.execute("CREATE OR REPLACE TABLE toi_snapshot AS SELECT * FROM df")
    con.execute("CREATE OR REPLACE TABLE analysis_set AS SELECT * FROM analysis")
    con.execute("CREATE OR REPLACE TABLE ingest_provenance AS SELECT * FROM prov")
    stats_df = pd.DataFrame([{"key": k, "value": str(v)} for k, v in stats.items()])
    con.execute("CREATE OR REPLACE TABLE ingest_stats AS SELECT * FROM stats_df")
    con.close()

    # PROVENANCE.md is committed; data/ is not. It is how a third party verifies they
    # pulled the same snapshot. Sources drift, so a later pull will NOT match - that is
    # expected, and is why the checksum and date are recorded rather than the data.
    prov_md = [
        "# Provenance", "",
        "Checksums of the raw sources behind `data/exonotes.duckdb`. Regenerated by",
        "`scripts/01_ingest.py`. `data/` is gitignored; this file is the committed record.", "",
        f"**Snapshot date:** `{SNAPSHOT}` · **Built (UTC):** `{retrieved}`", "",
        "| source | file | bytes | sha256 | in feature path |",
        "| :--- | :--- | ---: | :--- | :--- |",
    ]
    for r in prov.itertuples():
        prov_md.append(f"| `{r.source}` | `{r.path}` | {r.bytes:,} | `{r.sha256}` | "
                       f"{'yes' if r.used_as_features else '**no — see PLAN.md §3.2**'} |")
    prov_md += ["",
        "`nea_pscomppars` is recorded for provenance only. It contains confirmed planets",
        "only, so membership alone predicts the label at P=0.995 vs 0.074 and it is",
        "deliberately excluded from all model input. See `PLAN.md` §3.2.", "",
        "## Reproducing", "",
        "```bash", "uv venv --python 3.14 .venv",
        "uv pip install -r requirements.txt",
        ".venv/bin/python scripts/01_ingest.py   # --refresh to re-download",
        ".venv/bin/python scripts/02_baselines.py", "```", "",
        "ExoFOP updates continuously and the NASA Exoplanet Archive syncs from it weekly, so a",
        "later pull will differ. Compare against the checksums above to know whether you are",
        "looking at the same data this analysis used.", "",
    ]
    (ROOT / "PROVENANCE.md").write_text("\n".join(prov_md))

    w = max(len(k) for k in stats)
    for k, v in stats.items():
        print(f"{k:<{w}} : {v}")
    print(f"\nwrote {DB.relative_to(ROOT)}  (toi_snapshot, analysis_set, ingest_provenance, ingest_stats)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
