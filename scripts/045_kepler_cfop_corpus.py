"""ExoNotes Kepler - build the CFOP observer-note corpus, the like-for-like transfer test.

The Kepler Community Follow-up Observing Program (CFOP) was merged into the unified ExoFOP, and
its observer notes now sit in the same `download_obsnotes.php` dump the TESS study pulls, each
carrying a migration prefix naming its KOI host:

    Extracted KOI5952 observing note from ExoFOP-Kepler on 2020-11-02 Robo-AO LP600-imaging ...

Applies the definition fixed in WORKLOG.md 2026-09-21 ("KEPLER TRANSFER CORPUS SWITCHED TO
CFOP"), BEFORE any CFOP label was joined -- a copy of PREREGISTRATION.md sections 1.1 / 1.3:

    notes   cleaned text begins with the ExoFOP-Kepler migration prefix; Groupname empty
            (asserted). K2 notes, unprefixed notes and TESS-era notes are out of scope.
    text    prefix stripped; the host's notes joined by one space, ascending Lastmod, ties by ID
    unit    one KOI; per-host notes attached to every KOI of that host (as TESS: per-TIC notes
            on every TOI of the TIC)
    label   cumulative koi_disposition CONFIRMED -> 1, FALSE POSITIVE -> 0; others excluded
    groups  kepid;  power floor: minority < 100 -> STOP, no model call

Parsing and cleaning are IMPORTED UNCHANGED from scripts/028_obsnotes_pull.py (`parse_pipe`,
`plain`), so the Kepler text is produced by exactly the code that produced the TESS text. The
parse is then checked against a second, independent parser of the same bytes (records anchored
on `^ID|TIC|user|group|tag|YYYY-MM-DD hh:mm:ss|`): same record count, same IDs, same note text.

Stages, run in order by default; `--stage NAME` runs exactly one:

    fetch   bulk pipe dump -> data/kepler/obsnotes_bulk.txt, unless cached (`--refresh`)
    build   parse, verify, filter, aggregate, join labels -> data/kepler.duckdb, report

Idempotent: yes. Requires scripts/043_kepler_corpus.py's cumulative snapshot.
"""
import argparse, datetime, hashlib, importlib.util, json, pathlib, re, sys

import duckdb, pandas as pd, requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "kepler" / "obsnotes_bulk.txt"
META = ROOT / "data" / "kepler" / "obsnotes_bulk_fetch.json"
CUM = ROOT / "data" / "kepler" / "cumulative.csv"
DB = ROOT / "data" / "kepler.duckdb"
URL = "https://exofop.ipac.caltech.edu/tess/download_obsnotes.php"

_spec = importlib.util.spec_from_file_location("obs", ROOT / "scripts" / "028_obsnotes_pull.py")
obs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(obs)

NUMERIC = ["koi_period", "koi_depth", "koi_duration", "koi_prad",
           "koi_kepmag", "koi_steff", "koi_srad", "koi_slogg"]
PREFIX = re.compile(r"^Extracted KOI(\d+) observing note from ExoFOP-Kepler on \d{4}-\d\d-\d\d\s*")
ANCHOR = re.compile(r"^(\d+)\|(\d+)\|[^|\n]*\|[^|\n]*\|[^|\n]*\|\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\|",
                    re.M)
POSITIVE, NEGATIVE = "CONFIRMED", "FALSE POSITIVE"
POWER_FLOOR = 100


def fetch() -> None:
    r = requests.get(URL, params={"output": "pipe"}, timeout=(10, 300))
    r.raise_for_status()
    if not r.text.startswith("|".join(obs.COLUMNS)):
        sys.exit(f"unexpected bulk header: {r.text[:200]!r}")
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_bytes(r.content)
    META.write_text(json.dumps({
        "pulled_utc": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%MZ"),
        "url": f"{URL}?output=pipe", "bytes": len(r.content),
        "sha256_16": hashlib.sha256(r.content).hexdigest()[:16]}, indent=2) + "\n")
    print(f"fetched bulk obsnotes: {len(r.content):,} bytes")


def verify_parse(text: str, recs: list[dict]) -> None:
    """Second, independent parser over the same bytes. Must agree record for record."""
    body = text.split("\n", 1)[1]
    ms = list(ANCHOR.finditer(body))
    alt = {int(a[1]): body[a.end(): b.start() if b else len(body)].rstrip("\r\n")
           for a, b in zip(ms, ms[1:] + [None])}
    ids = [int(r["ID"]) for r in recs]
    same_text = sum((r["notes"] or "") == alt.get(int(r["ID"]), None) for r in recs)
    checks = {
        f"parse_pipe records ({len(recs):,}) == anchored records ({len(ms):,})": len(recs) == len(ms),
        "IDs unique": len(set(ids)) == len(ids),
        "same ID set": set(ids) == set(alt),
        f"note text identical on {same_text:,} of {len(recs):,}": same_text == len(recs),
    }
    for k, ok in checks.items():
        print(f"  [{'ok' if ok else 'FAIL'}] {k}")
    if not all(checks.values()):
        sys.exit("parse verification failed; nothing built")


def build() -> None:
    text = RAW.read_text(encoding="utf-8")
    recs = obs.parse_pipe(text, tic=0)
    verify_parse(text, recs)

    notes = []
    for r in recs:
        clean = obs.plain(r["notes"])
        m = PREFIX.match(clean)
        if not m:
            continue
        notes.append(dict(note_id=int(r["ID"]), tic_id=int(r["TIC ID"]), host=int(m[1]),
                          username=r["Username"], groupname=r["Groupname"],
                          lastmod=r["Lastmod"], text=clean[m.end():].strip()))
    nd = pd.DataFrame(notes)
    bad_group = nd["groupname"].notna().sum()
    tics = nd.groupby("host")["tic_id"].nunique()
    print(f"in-scope notes {len(nd):,} on {nd.host.nunique():,} KOI hosts · non-empty "
          f"Groupname {bad_group} · hosts with >1 TIC {int((tics > 1).sum())} · "
          f"empty after prefix strip {int((nd.text == '').sum())}")
    if bad_group or (tics > 1).any():
        sys.exit("Groupname / host->TIC assertion failed: the definition no longer describes "
                 "what is being selected. STOPPING.")

    nd = nd[nd.text != ""].sort_values(["host", "lastmod", "note_id"], kind="stable")
    per_host = nd.groupby("host").agg(
        text=("text", " ".join), n_notes=("text", "size"),
        n_authors=("username", "nunique"), first_note=("lastmod", "min"),
        last_note=("lastmod", "max")).reset_index()
    per_host["n_chars"] = per_host.text.str.len()

    cum = pd.read_csv(CUM, dtype={"kepoi_name": str, "koi_disposition": str})
    cum["host"] = cum.kepoi_name.str.slice(1, 6).astype(int)
    kep_per_host = cum.groupby("host")["kepid"].nunique()
    if (kep_per_host > 1).any():
        sys.exit(f"KOI host numbers map to >1 kepid: {kep_per_host[kep_per_host > 1].index[:5].tolist()}")

    j = cum.merge(per_host, on="host", how="inner")
    print("koi_disposition over KOIs with in-scope notes:\n"
          + j.koi_disposition.value_counts().to_string())
    corpus = j[j.koi_disposition.isin([POSITIVE, NEGATIVE])].copy()
    corpus["y"] = (corpus.koi_disposition == POSITIVE).astype(int)
    corpus = corpus[["kepoi_name", "kepid", "host", "y", "text", "n_notes", "n_authors",
                     "n_chars", "first_note", "last_note", "koi_vet_date"] + NUMERIC]
    corpus = corpus.sort_values("kepoi_name").reset_index(drop=True)

    with duckdb.connect(str(DB)) as con:
        con.register("nd_df", nd)
        con.execute("create or replace table kepler_cfop_notes as select * from nd_df")
        con.register("corpus_df", corpus)
        con.execute("create or replace table kepler_cfop_corpus as select * from corpus_df")

    n, pos = len(corpus), int(corpus.y.sum())
    minority = min(pos, n - pos)
    grp = corpus.groupby("kepid").size()
    print(f"\nCORPUS n = {n:,}   y=1 {pos:,}   y=0 {n - pos:,}   base rate {pos / n:.4f}")
    print(f"minority {minority:,} vs power floor {POWER_FLOOR}: "
          f"{'CLEARS' if minority >= POWER_FLOOR else 'FAILS -> STOP, no model calls'}")
    print(f"groups (kepid) {grp.size:,}; rows/group max {grp.max()}; multi-KOI groups "
          f"{int((grp > 1).sum()):,}")
    for col in ("n_chars", "n_notes", "n_authors"):
        med = corpus.groupby("y")[col].median()
        print(f"{col:>9} median  y=0 {med.get(0, float('nan')):.0f}  y=1 {med.get(1, float('nan')):.0f}")
    print("covariate missingness: "
          + ", ".join(f"{c} {corpus[c].isna().mean():.1%}" for c in NUMERIC))
    sha = hashlib.sha256(corpus.to_csv(index=False).encode()).hexdigest()[:16]
    print(f"kepler_cfop_corpus sha256(to_csv)[:16] = {sha}")


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
