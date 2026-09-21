"""ExoNotes Kepler task 1b - label the FPWG comments and build the Kepler corpus.

WITHDRAWN as the transfer test (PREREGISTRATION.md section 11.10, A-40 40.0): TF-IDF on
`fpwg_comment` alone beats every covariate and the FPWG's own verdict agrees with the label on
98.1% of rows, so a transfer test here could not come out negative. Kept so that measurement
stays reproducible; the transfer corpus is scripts/045_kepler_cfop_corpus.py. This script also
owns the cumulative snapshot that 045 reuses.

Applies the corpus definition fixed in WORKLOG.md 2026-09-21 (entry headed "02:38Z"), BEFORE any
label was joined:

    unit    one KOI (`kepoi_name`)
    text    `fpwg_comment`, trimmed; in the corpus only if non-empty
    label   cumulative `koi_disposition`: CONFIRMED -> 1, FALSE POSITIVE -> 0;
            CANDIDATE / NOT DISPOSITIONED excluded, as TESS excluded PC/APC
    groups  `kepid` (host star), the analogue of TESS's TIC
    floor   minority class < 100 rows -> the Kepler arm is underpowered and STOPS

Only the label, `kepid`, `koi_vet_date` and the eight covariates mirroring TESS baseline B are
pulled from `CUMULATIVE`. The excluded sources -- `koi_comment`, `koi_pdisposition`,
`koi_score`, `koi_disp_prov`, every `koi_fpflag_*` -- are never requested, so they cannot reach
a feature by accident. The structured `fpwg_*` fields stay in `kepler_fpwg_raw` and are NOT
copied into the corpus table, except `fpwg_disp_status`, which is carried as `fpwg_status` for
the label-independence diagnostic and must never become a feature.

Stages, run in order by default; `--stage NAME` runs exactly one:

    fetch    TAP `CUMULATIVE` -> data/kepler/cumulative.csv, unless cached (`--refresh`)
    build    join, apply the definition, write data/kepler.duckdb::kepler_corpus, report

Idempotent: yes. Requires scripts/042_kepler_fpwg_pull.py to have run.
"""
import argparse, datetime, hashlib, json, pathlib, sys

import duckdb, pandas as pd, requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "kepler" / "cumulative.csv"
META = ROOT / "data" / "kepler" / "cumulative_fetch.json"
DB = ROOT / "data" / "kepler.duckdb"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

# Mirrors TESS baseline B (scripts/02_baselines.py NUMERIC), column for column:
# pl_orbper, pl_trandep, pl_trandurh, pl_rade, st_tmag, st_teff, st_rad, st_logg.
NUMERIC = ["koi_period", "koi_depth", "koi_duration", "koi_prad",
           "koi_kepmag", "koi_steff", "koi_srad", "koi_slogg"]
CUM_COLS = ["kepid", "kepoi_name", "koi_disposition", "koi_vet_date"] + NUMERIC

POSITIVE, NEGATIVE = "CONFIRMED", "FALSE POSITIVE"
POWER_FLOOR = 100


def fetch() -> None:
    q = f"select {','.join(CUM_COLS)} from cumulative"
    r = requests.get(TAP, params={"query": q, "format": "csv"}, timeout=600)
    r.raise_for_status()
    if r.text.lstrip().lower().startswith("<"):
        sys.exit(f"TAP returned an error page: {r.text[:400]}")
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(r.text)
    META.write_text(json.dumps({
        "pulled_utc": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%MZ"),
        "query": q, "sha256_16": hashlib.sha256(r.content).hexdigest()[:16]}, indent=2) + "\n")
    print(f"fetched cumulative: {len(r.content):,} bytes")


def build() -> None:
    cum = pd.read_csv(RAW, dtype={"kepid": "Int64", "kepoi_name": str,
                                  "koi_disposition": str, "koi_vet_date": str})
    if list(cum.columns) != CUM_COLS or not cum["kepoi_name"].is_unique:
        sys.exit(f"cumulative schema/uniqueness check failed: {list(cum.columns)}")

    with duckdb.connect(str(DB)) as con:
        fpwg = con.execute("""
            select kepid, kepoi_name, fpwg_disp_status as fpwg_status, fpwg_vet_date,
                   trim(fpwg_comment) as text
            from kepler_fpwg_raw""").fetchdf()

    commented = fpwg[fpwg["text"] != ""]
    j = commented.merge(cum, on="kepoi_name", how="left", suffixes=("_fpwg", ""),
                        indicator=True)
    no_match = int((j["_merge"] == "left_only").sum())
    kepid_mismatch = int((j["_merge"] == "both").sum()
                         - (j.loc[j["_merge"] == "both", "kepid_fpwg"].astype("Int64")
                            == j.loc[j["_merge"] == "both", "kepid"]).sum())
    disp_counts = j["koi_disposition"].fillna("<no match>").value_counts()

    corpus = j[j["koi_disposition"].isin([POSITIVE, NEGATIVE])].copy()
    corpus["y"] = (corpus["koi_disposition"] == POSITIVE).astype(int)
    corpus["text_len"] = corpus["text"].str.len()
    corpus = corpus[["kepoi_name", "kepid", "y", "text", "text_len", "fpwg_status",
                     "fpwg_vet_date", "koi_vet_date"] + NUMERIC]
    corpus = corpus.sort_values("kepoi_name").reset_index(drop=True)

    with duckdb.connect(str(DB)) as con:
        con.register("corpus_df", corpus)
        con.execute("create or replace table kepler_corpus as select * from corpus_df")

    n, pos = len(corpus), int(corpus["y"].sum())
    minority = min(pos, n - pos)
    per_group = corpus.groupby("kepid").size()
    sha = hashlib.sha256(corpus.to_csv(index=False).encode()).hexdigest()[:16]

    print(f"commented FPWG rows: {len(commented):,}; no cumulative match: {no_match}; "
          f"kepid disagreements between tables: {kepid_mismatch}")
    print("koi_disposition over commented rows:\n" + disp_counts.to_string())
    print(f"\nCORPUS n = {n:,}   y=1 (CONFIRMED) {pos:,}   y=0 (FALSE POSITIVE) {n - pos:,}   "
          f"base rate {pos / n:.4f}")
    print(f"minority class {minority:,} vs power floor {POWER_FLOOR}: "
          f"{'CLEARS' if minority >= POWER_FLOOR else 'FAILS -> STOP, no model calls'}")
    print(f"groups (kepid) {per_group.size:,}; rows/group max {per_group.max()}, "
          f"multi-KOI groups {int((per_group > 1).sum()):,}")
    print("text length by class (median / p10 / p90):")
    for yv, g in corpus.groupby("y")["text_len"]:
        print(f"  y={yv}: {int(g.median())} / {int(g.quantile(.1))} / {int(g.quantile(.9))}")
    print("covariate missingness: "
          + ", ".join(f"{c} {corpus[c].isna().mean():.1%}" for c in NUMERIC))
    print("\nlabel-independence diagnostic -- fpwg_status x y (NOT a feature):")
    print(pd.crosstab(corpus["fpwg_status"], corpus["y"], margins=True).to_string())
    print(f"\nkepler_corpus sha256(to_csv)[:16] = {sha}")


STAGES = {"fetch": fetch, "build": build}

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
    if a.stage in (None, "build"):
        build()
