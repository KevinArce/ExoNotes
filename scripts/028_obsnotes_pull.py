"""ExoNotes TASK A - acquire the observer-note corpus (PREREGISTRATION.md section 1).

Pulls ExoFOP-TESS observing notes for every TIC in `analysis_set`, strips HTML, keeps only
`Groupname != 'tfopwg'` (the observer notes), persists them to DuckDB, and reports the
coverage and base-rate statistics section 1.4 commits to reporting as measured.

Stages, run in order by default; `--stage NAME` runs exactly one:

    repair   re-serialise existing cache files as valid RFC-8259 JSON       (A-11)
    pull     fetch every TIC, cache-first, bounded thread pool
    verify   re-fetch every cached-empty TIC once more, to catch throttled empties
    persist  build the DuckDB tables, assert the Groupname domain (A-10), report

Idempotent: yes, at every stage. Per-TIC responses are cached under data/cache/obsnotes/,
so a re-run does no network I/O and reproduces exactly. DuckDB writes are CREATE OR REPLACE.

Three response conditions are distinguished, which 027_obsnotes_recon.py did not:

    >= 1 data row                notes exist                    -> cache
    header-only (51 bytes)       TIC genuinely has no notes     -> cache as [], no retry
    ZERO-byte body               throttle / transport failure   -> RETRY, never cached

The third is the silent-failure mode. ExoFOP throttles by returning HTTP 200 with an empty
body; `pd.read_csv` turns that into `EmptyDataError`, which reads exactly like "no notes".
Caching it as `[]` would write "this TIC has no observer notes" into the corpus for every
throttled fetch -- shrinking the corpus silently, and non-randomly. Measured on the wire:
TIC 9155187 returned [480, 0, 480] bytes over three consecutive tries.

A *mis-parameterised* call (positional first arg binds to `tag`, not `tic`) returns the same
header-only response as a genuinely empty TIC, so those two are NOT distinguishable per-TIC.
The sentinel check is the only defence against it, and against a site-wide throttle.
See WORKLOG.md 2026-09-20T17:34Z, which corrects 17:12Z.

`etta` is deliberately NOT used for the bulk pull. It calls pd.read_csv(url) with no timeout,
and ExoFOP throttles by withholding the response body -- the handshake completes, zero bytes
follow, the call hangs forever (scripts/01_ingest.py documents the same hazard for the bulk
TOI table). Identical URL, identical parse, explicit timeout. `--check-etta` verifies that the
two paths agree row-for-row before the pull proceeds.
"""
import argparse, concurrent.futures as cf, datetime, hashlib, html, io, json, pathlib
import re, statistics, sys, threading, time

import duckdb, pandas as pd, requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache" / "obsnotes"
DB = ROOT / "data" / "exonotes.duckdb"
OUT = ROOT / "research" / "data"

URL = "https://exofop.ipac.caltech.edu/tess/download_obsnotes.php"
COLUMNS = ["ID", "TIC ID", "Username", "Groupname", "TAG ID", "Lastmod", "notes"]

# TICs verified to carry >=1 note. Used to prove the endpoint is still answering: an empty
# body is otherwise indistinguishable from a throttle.
SENTINELS = (156648452, 1003831)

# PREREGISTRATION.md section 1.1 -- the notes that are NOT the TFOPWG summary.
TFOPWG = "tfopwg"

TAG_RX = re.compile(r"<[^>]+>")
# Some pasted-e-mail notes end on an UNTERMINATED tag ("<a target=\"_blank\"" with no closing
# `>`), which TAG_RX cannot match. Restricted to real HTML tag names on purpose: a permissive
# `<[a-zA-Z]` pattern would eat scientific text like "depth <1 ppt" or "<Teff".
_HTML_TAGS = (r"a|b|i|u|p|br|div|span|img|font|table|tr|td|th|tbody|thead|ul|ol|li|h[1-6]|"
              r"strong|em|body|html|head|style|script|meta|link|hr|blockquote|pre|code|sub|"
              r"sup|center|o:p")
FRAG_RX = re.compile(rf"</?(?:{_HTML_TAGS})\b(?:\s+[a-zA-Z-]+\s*=\s*(?:\"[^\"]*\"|'[^']*'))*\s*/?>?",
                     re.I)
# Corpus-integrity probe only (section 1.2). The G5 clause set is TASK B2's job, not this one.
ANY_DISP = re.compile(r"(?i)\b(?:master|phot|spec)\s*disp\s*:")

ABORT = threading.Event()
_abort_reason: list[str] = []


class Throttled(RuntimeError):
    """HTTP 200 with a zero-byte body: ExoFOP declining to answer. Always retryable."""


class BadSchema(RuntimeError):
    """The response parsed, but it is not the obsnotes table."""


def plain(raw: str) -> str:
    """HTML-stripped, entity-decoded, whitespace-collapsed.

    Extends 027's transform, which stripped complete tags only. Two defects measured on the
    full corpus that 027's 30-TIC sample was too small to show:

      * **HTML entities were never decoded** -- `&nbsp;` alone occurs 5,746 times across
        1,061 of 1,482 corpus rows (71.6%). Jev would have read them as literal text.
      * One note ends on an unterminated `<a target="_blank"` that TAG_RX cannot match.

    Order matters and is not interchangeable. TAG_RX must run BEFORE FRAG_RX: run the other
    way round, FRAG_RX consumes an unquoted `href=...` attribute and swallows the note body
    (measured: TIC 164652245 reduces to the empty string). Unescaping runs LAST so that a
    literal `&lt;b&gt;` an author typed survives as text instead of being stripped as a tag.
    """
    s = TAG_RX.sub(" ", raw or "")
    s = FRAG_RX.sub(" ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def parse_pipe(text: str, tic: int) -> list[dict]:
    """Parse the pipe-delimited response WITHOUT pandas. Correct by construction.

    `notes` is the last column, so splitting each line with maxsplit=6 absorbs any literal
    `|` inside the note body. `pd.read_csv(..., delimiter='|')` -- which is what `etta` uses
    -- cannot do this, and fails two different ways on the two TICs in this corpus whose
    notes contain a pipe (measured 2 of 2,573):

      * TIC 70513361  -- the offending line is not the first, so the column count is already
        fixed at 7 and pandas raises ParserError. The TIC is lost, loudly.
      * TIC 462715015 -- the offending line IS the first, so pandas infers a 2-level INDEX
        from the two extra fields and shifts every column left. `notes` becomes NULL, the
        note text lands in `TAG ID`, and `Groupname` becomes a TIMESTAMP. Silent.

    The second is the dangerous one: it would have tripped the A-10 `Groupname` domain
    assertion in the persist stage, which reads a third Groupname value as "PREREGISTRATION
    section 1.1 no longer describes what is being selected" -- a corpus-definition alarm
    raised by a parser bug. See WORKLOG.md 2026-09-20T17:52Z.
    """
    lines = text.split("\n")
    header = lines[0].rstrip("\r").split("|")
    if header != COLUMNS:
        raise BadSchema(f"TIC {tic}: unexpected header {header[:9]}")
    recs: list[dict] = []
    for ln in lines[1:]:
        ln = ln.rstrip("\r")
        if not ln.strip():
            continue
        parts = ln.split("|", len(COLUMNS) - 1)
        if len(parts) < len(COLUMNS):
            # A raw newline inside a note body. Re-attach it rather than emit a short row,
            # which is how pandas silently manufactures a junk record (it pads with NaN).
            if recs:
                prev = recs[-1][COLUMNS[-1]]
                recs[-1][COLUMNS[-1]] = (prev or "") + "\n" + ln
                continue
            raise BadSchema(f"TIC {tic}: {len(parts)}-field line with no record to attach to")
        recs.append({c: (v if v != "" else None) for c, v in zip(COLUMNS, parts)})
    return recs


def to_records(df: pd.DataFrame) -> list[dict]:
    """Column order preserved, NaN -> None, everything else -> str. Used only by --check-etta,
    to render etta's DataFrame in the same shape `parse_pipe` returns.

    A-11: 20 of the 30 files 027 wrote contain bare `NaN` and are not valid RFC-8259 JSON,
    because pandas 3 `astype(str)` preserves NA rather than producing the string 'nan'.
    """
    out = []
    for row in df.to_dict("records"):
        out.append({str(k): (None if pd.isna(row[k]) else str(row[k])) for k in df.columns})
    return out


def cache_write(path: pathlib.Path, recs: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(recs, indent=1, allow_nan=False))


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = "ExoNotes/1.0 (research; github.com/KevinArce/ExoNotes)"
    return s


_local = threading.local()


def session() -> requests.Session:
    if not hasattr(_local, "s"):
        _local.s = _session()
    return _local.s


def fetch_raw(tic: int, timeout=(10, 90), tries: int = 6) -> list[dict]:
    """One TIC, no cache. [] means the TIC genuinely has no notes.

    Raises BadSchema, or the last transport error after `tries` attempts. A zero-byte body
    is retried as a throttle, never returned as "no notes".
    """
    last = None
    for attempt in range(tries):
        if ABORT.is_set():
            raise RuntimeError("aborted")
        try:
            r = session().get(URL, params={"output": "pipe", "tid": int(tic)}, timeout=timeout)
            r.raise_for_status()
            text = r.text
            if not text.strip():
                # NOT "no notes" -- this is the throttle. Retry it.
                raise Throttled(f"TIC {tic}: HTTP 200 with a zero-byte body")
            return parse_pipe(text, tic)  # [] == genuine "this TIC has no notes"
        except BadSchema:
            raise
        except Exception as e:  # noqa: BLE001 - any transport failure is retryable
            last = e
            if attempt < tries - 1:
                time.sleep(1.5 * (2 ** attempt))
    raise RuntimeError(f"TIC {tic}: {type(last).__name__}: {last}") from last


def fetch_cached(tic: int) -> tuple[list[dict], bool]:
    """(records, was_cached). Cache hit costs no network I/O."""
    hit = CACHE / f"{tic}.json"
    if hit.exists():
        return json.loads(hit.read_text()), True
    recs = fetch_raw(tic)
    cache_write(hit, recs)
    return recs, False


def check_sentinel(where: str) -> None:
    """Prove the endpoint still answers. An empty sentinel means every empty since the last
    good check is suspect, so it aborts rather than poisoning the coverage statistic."""
    for tic in SENTINELS:
        try:
            recs = fetch_raw(tic)
        except Exception as e:  # noqa: BLE001
            _abort_reason.append(f"sentinel TIC {tic} at {where}: {type(e).__name__}: {e}")
            ABORT.set()
            return
        if not recs:
            _abort_reason.append(
                f"sentinel TIC {tic} at {where} came back EMPTY but is known to have notes -- "
                "the endpoint is throttling. Every empty result since the last good sentinel "
                "is suspect; aborting rather than recording them as 'no notes'.")
            ABORT.set()
            return
    return


# --------------------------------------------------------------------------- stages

def stage_repair() -> int:
    """A-11: rewrite every cache file as valid RFC-8259 JSON. Content is unchanged."""
    files = sorted(CACHE.glob("*.json"))
    fixed = ok = 0
    for p in files:
        raw = p.read_text()
        try:  # strict: reject NaN/Infinity, which RFC 8259 does not allow
            json.loads(raw, parse_constant=_reject_constant)
            ok += 1
            continue
        except ValueError:
            pass
        recs = json.loads(raw)  # permissive reader accepts the bare NaN
        recs = [{k: (None if (isinstance(v, float) and v != v) else v) for k, v in r.items()}
                for r in recs]
        cache_write(p, recs)
        fixed += 1
    print(f"repair  : {len(files)} cache files - {ok} already valid, {fixed} re-serialised "
          f"(bare NaN -> null)")
    return 0


def _reject_constant(c):
    raise ValueError(c)


def stage_pull(tics: list[int], workers: int, sentinel_every: int) -> int:
    todo = [t for t in tics if not (CACHE / f"{t}.json").exists()]
    print(f"pull    : {len(tics)} TIC total, {len(tics) - len(todo)} already cached, "
          f"{len(todo)} to fetch, {workers} workers")
    if not todo:
        return 0

    check_sentinel("start")
    if ABORT.is_set():
        print("\n".join(_abort_reason), file=sys.stderr)
        return 2

    t0, done, net, empties, failures = time.time(), 0, 0, 0, []
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fetch_cached, t): t for t in todo}
        for fut in cf.as_completed(futs):
            tic = futs[fut]
            done += 1
            try:
                recs, cached = fut.result()
            except BadSchema as e:
                _abort_reason.append(str(e))
                ABORT.set()
                break
            except Exception as e:  # noqa: BLE001
                if ABORT.is_set():
                    break
                failures.append((tic, f"{type(e).__name__}: {e}"))
                continue
            if not cached:
                net += 1
            if not recs:
                empties += 1
            if net and sentinel_every and net % sentinel_every == 0:
                check_sentinel(f"after {net} network fetches")
                if ABORT.is_set():
                    break
            if done % 100 == 0 or done == len(todo):
                el = time.time() - t0
                rate = done / el if el else 0
                print(f"  {done}/{len(todo)}  {empties} empty  {len(failures)} failed  "
                      f"{rate:.1f}/s  eta {(len(todo)-done)/rate/60:.1f} min" if rate else
                      f"  {done}/{len(todo)}")
        if ABORT.is_set():
            for f in futs:
                f.cancel()

    if ABORT.is_set():
        print("\nABORTED:\n" + "\n".join(_abort_reason), file=sys.stderr)
        return 2
    print(f"pull    : done in {(time.time()-t0)/60:.1f} min - {net} fetched, "
          f"{empties} with no notes, {len(failures)} failed")
    if failures:
        for tic, err in failures[:20]:
            print(f"    FAILED TIC {tic}: {err}", file=sys.stderr)
        print(f"    ({len(failures)} failures; re-run to retry -- cache makes it cheap)",
              file=sys.stderr)
        return 1
    return 0


def stage_verify(tics: list[int], workers: int) -> int:
    """Re-fetch every cached-empty TIC once more.

    A header-only response is the same on the wire whether the TIC genuinely has no notes or
    the call was mis-parameterised. Sentinels bound that risk; this closes what remains of it.
    A TIC that comes back header-only twice, on two separate occasions with sentinels passing
    in between, is empty. Re-run until it flips nothing.
    """
    empty = [t for t in tics if (CACHE / f"{t}.json").exists()
             and json.loads((CACHE / f"{t}.json").read_text()) == []]
    print(f"verify  : re-fetching {len(empty)} cached-empty TIC")
    if not empty:
        return 0
    check_sentinel("verify start")
    if ABORT.is_set():
        print("\n".join(_abort_reason), file=sys.stderr)
        return 2

    flipped, failed, t0 = [], [], time.time()
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fetch_raw, t): t for t in empty}
        for i, fut in enumerate(cf.as_completed(futs), 1):
            tic = futs[fut]
            try:
                recs = fut.result()
            except Exception as e:  # noqa: BLE001
                failed.append((tic, f"{type(e).__name__}: {e}"))
                continue
            if recs:
                cache_write(CACHE / f"{tic}.json", recs)
                flipped.append(tic)
            if i % 100 == 0:
                print(f"  {i}/{len(empty)}  {len(flipped)} flipped non-empty")
    check_sentinel("verify end")
    print(f"verify  : done in {(time.time()-t0)/60:.1f} min - {len(flipped)} of {len(empty)} "
          f"came back NON-empty on the second attempt, {len(failed)} failed")
    if flipped:
        print(f"    flipped: {flipped[:20]}{' ...' if len(flipped) > 20 else ''}")
        print("    ^ these were false empties. The pass was worth running; run it again "
              "until it flips nothing.")
    if ABORT.is_set():
        print("\n".join(_abort_reason), file=sys.stderr)
        return 2
    return 1 if (flipped or failed) else 0


def stage_persist() -> int:
    con = duckdb.connect(str(DB))
    aset = con.execute("select * from analysis_set").df()
    tics = sorted({int(t) for t in aset.tic_id})

    raw, missing, bad_group = [], [], {}
    for tic in tics:
        p = CACHE / f"{tic}.json"
        if not p.exists():
            missing.append(tic)
            continue
        for i, r in enumerate(json.loads(p.read_text())):
            g = r.get("Groupname")
            if g is not None and g != TFOPWG:
                bad_group.setdefault(g, []).append(tic)
            raw.append(dict(
                tic_id=tic, seq=i, note_id=r.get("ID"), username=r.get("Username"),
                groupname=g, tag_id=r.get("TAG ID"), lastmod=r.get("Lastmod"),
                notes_html=r.get("notes"), notes_text=plain(r.get("notes") or ""),
                is_tfopwg=(g == TFOPWG)))

    if missing:
        print(f"persist : ABORT - {len(missing)} TIC have no cache file "
              f"(e.g. {missing[:5]}). Run the pull stage first.", file=sys.stderr)
        return 2

    # --- A-10 assertion: the Groupname domain is exactly {'tfopwg', NULL} -------------
    if bad_group:
        print("persist : ABORT - `Groupname` took a value outside {'tfopwg', NULL}:",
              file=sys.stderr)
        for g, ts in sorted(bad_group.items()):
            print(f"    {g!r}: {len(ts)} notes, e.g. TIC {ts[:5]}", file=sys.stderr)
        print("  PREREGISTRATION.md section 1.1 selects the corpus as `Groupname != 'tfopwg'`.\n"
              "  A-10 records that this is in practice `Groupname IS NULL`. A third value means\n"
              "  section 1.1 no longer describes what is being selected. STOPPING, per TASK A.",
              file=sys.stderr)
        return 2

    rawdf = pd.DataFrame(raw)
    n_null = int(rawdf.groupname.isna().sum())
    n_tfop = int((rawdf.groupname == TFOPWG).sum())
    print(f"persist : {len(rawdf):,} notes over {len(tics):,} TIC")
    print(f"          Groupname domain asserted = {{'tfopwg', NULL}}  "
          f"(tfopwg {n_tfop:,} · NULL {n_null:,})   <- A-10 holds")

    # --- per-TIC observer text, ascending Lastmod (section 1.1) ----------------------
    obs = rawdf[~rawdf.is_tfopwg].copy()
    obs["_sort"] = obs.lastmod.fillna("9999")  # undated notes sort last, stably
    obs = obs.sort_values(["tic_id", "_sort", "seq"], kind="stable")
    g = obs.groupby("tic_id")
    text = g.agg(
        n_notes_obs=("notes_text", "size"),
        n_authors=("username", "nunique"),
        text=("notes_text", lambda s: " ".join(x for x in s if x)),
    ).reset_index()
    text["n_chars"] = text.text.str.len()
    text = text[text.n_chars > 0]
    allc = rawdf.groupby("tic_id").size().rename("n_notes_all").reset_index()
    text = text.merge(allc, on="tic_id", how="left")

    con.execute("create or replace table obsnotes_raw as select * from rawdf")
    con.execute("create or replace table obsnotes_text as select * from text")

    # --- the corpus: labelled TOI rows whose TIC has >=1 observer note ---------------
    con.execute("""
        create or replace table analysis_set_obsnotes as
        select a.*, t.text as notes, t.n_notes_obs, t.n_notes_all, t.n_authors, t.n_chars
        from analysis_set a join obsnotes_text t on a.tic_id = t.tic_id
    """)
    con.execute("""
        create or replace table obsnotes_coverage as
        select a.tic_id, a.toi, a.y,
               (t.tic_id is not null) as has_obsnote,
               coalesce(t.n_notes_obs, 0) as n_notes_obs,
               coalesce(t.n_chars, 0)     as n_chars
        from analysis_set a left join obsnotes_text t on a.tic_id = t.tic_id
    """)

    # --- report ----------------------------------------------------------------------
    cov = con.execute("select * from obsnotes_coverage").df()
    corpus = con.execute("select * from analysis_set_obsnotes").df()
    n_rows, n_tic = len(cov), cov.tic_id.nunique()
    k_rows, k_tic = len(corpus), corpus.tic_id.nunique()
    p1 = cov[cov.y == 1].has_obsnote.mean()
    p0 = cov[cov.y == 0].has_obsnote.mean()

    stats = {
        "analysis_set rows / TIC": f"{n_rows:,} / {n_tic:,}",
        "analysis_set base rate": f"{cov.y.mean():.4f}",
        "CORPUS rows / TIC": f"{k_rows:,} / {k_tic:,}",
        "CORPUS base rate": f"{corpus.y.mean():.4f}",
        "row coverage": f"{k_rows/n_rows:.3f}",
        "TIC coverage": f"{k_tic/n_tic:.3f}",
        "P(has note | y=1)": f"{p1:.4f}",
        "P(has note | y=0)": f"{p0:.4f}",
        "selection ratio": f"{p1/p0:.3f}" if p0 else "n/a",
        "chars / row  median": f"{corpus.n_chars.median():.0f}",
        "chars / row  mean": f"{corpus.n_chars.mean():.0f}",
        "obs notes / row median": f"{corpus.n_notes_obs.median():.0f}",
        "authors / row median": f"{corpus.n_authors.median():.0f}",
    }
    w = max(len(k) for k in stats)
    print("\n--- TASK A realised corpus (PREREGISTRATION.md section 1.4) ---")
    for k, v in stats.items():
        print(f"{k:<{w}} : {v}")

    print("\n--- corpus integrity: disposition leakage after the Groupname filter ---")
    leak = corpus[corpus.notes.str.contains(ANY_DISP, regex=True, na=False)]
    print(f"rows whose observer text contains '*Disp:' : {len(leak)}/{k_rows} "
          f"({100*len(leak)/max(k_rows,1):.2f}%)   <- section 1.2 measured 0/20 on the recon")
    if len(leak):
        print("  NOT a TASK A stop condition -- L5 is TASK B2's tripwire. Recording it here so\n"
              "  B2 starts from the measured number rather than the 30-TIC estimate.")
        for r in leak.head(5).itertuples():
            m = ANY_DISP.search(r.notes)
            print(f"    TIC {r.tic_id} TOI {r.toi} y={r.y}: ...{r.notes[max(0,m.start()-60):m.start()+60]}...")

    proj = {"rows": 1814, "tic": 1715}
    print(f"\nprojection check: section 1.4 said ~{proj['rows']:,} rows / ~{proj['tic']:,} TIC; "
          f"realised {k_rows:,} / {k_tic:,} "
          f"({100*(k_tic-proj['tic'])/proj['tic']:+.1f}% on TIC)")
    print("A-8 note: the projection was 20/30 extrapolated, binomial interval ~1,200-2,140 TIC.")

    OUT.mkdir(parents=True, exist_ok=True)
    art = OUT / f"obsnotes_corpus_{datetime.date.today().isoformat()}.json"
    art.write_text(json.dumps({
        "generated_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "stats": stats, "groupname_domain": {"tfopwg": n_tfop, "null": n_null},
        "disp_leak_rows": int(len(leak)),
        "projection": proj, "realised": {"rows": k_rows, "tic": k_tic},
    }, indent=2))
    write_provenance(con, len(rawdf), k_rows, k_tic)
    print(f"\nwrote {DB.relative_to(ROOT)} (obsnotes_raw, obsnotes_text, "
          f"analysis_set_obsnotes, obsnotes_coverage)")
    print(f"wrote {art.relative_to(ROOT)}")
    return 0


def write_provenance(con, n_notes: int, k_rows: int, k_tic: int) -> None:
    """Append/refresh the obsnotes block in PROVENANCE.md, between markers.

    `scripts/01_ingest.py` rewrites PROVENANCE.md wholesale, so this block is re-created by
    re-running this stage. The ordering dependency is stated in the block itself.
    """
    files = sorted(CACHE.glob("*.json"), key=lambda p: int(p.stem))
    manifest = "\n".join(f"{p.stem} {hashlib.sha256(p.read_bytes()).hexdigest()}" for p in files)
    digest = hashlib.sha256(manifest.encode()).hexdigest()
    total = sum(p.stat().st_size for p in files)
    block = [
        "<!-- BEGIN obsnotes (scripts/028_obsnotes_pull.py) -->",
        "## Observer-note corpus (TASK A)", "",
        "Per-TIC ExoFOP observing notes behind `analysis_set_obsnotes`. Cached under",
        "`data/cache/obsnotes/` (gitignored); this block is the committed record.", "",
        f"**Pulled (UTC):** `{datetime.datetime.now(datetime.UTC).isoformat(timespec='seconds')}`", "",
        "| quantity | value |", "| :--- | ---: |",
        f"| cache files (one per TIC) | {len(files):,} |",
        f"| total cached bytes | {total:,} |",
        f"| notes parsed | {n_notes:,} |",
        f"| corpus rows / TIC | {k_rows:,} / {k_tic:,} |",
        f"| **manifest sha256** | `{digest}` |", "",
        "The manifest digest is `sha256` over the newline-joined `\"<tic> <sha256(file)>\"`",
        "lines, TIC ascending. It changes if any cached response changes.", "",
        "```bash",
        ".venv/bin/python scripts/028_obsnotes_pull.py           # all stages, cache-first",
        ".venv/bin/python scripts/028_obsnotes_pull.py --stage persist",
        "```", "",
        "`scripts/01_ingest.py` rewrites this file wholesale, so re-run the `persist` stage",
        "after any ingest re-run to restore this block.", "",
        "<!-- END obsnotes -->",
    ]
    path = ROOT / "PROVENANCE.md"
    cur = path.read_text()
    new = "\n".join(block)
    if "<!-- BEGIN obsnotes" in cur:
        cur = re.sub(r"<!-- BEGIN obsnotes.*?<!-- END obsnotes -->", new, cur, flags=re.S)
    else:
        cur = cur.rstrip() + "\n\n---\n\n" + new + "\n"
    path.write_text(cur)


def check_etta(n: int = 3) -> int:
    """Verify the requests path and `etta` return identical records on cached TICs."""
    import etta
    tics = [int(p.stem) for p in sorted(CACHE.glob("*.json"))][:n]
    bad = 0
    for tic in tics:
        mine = fetch_raw(tic)
        theirs = to_records(etta.download_obsnotes(tic=tic))
        same = mine == theirs
        bad += not same
        print(f"  TIC {tic}: requests {len(mine)} rows vs etta {len(theirs)} rows -> "
              f"{'IDENTICAL' if same else 'DIFFERENT'}")
    print(f"check-etta: {len(tics)-bad}/{len(tics)} identical")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["repair", "pull", "verify", "persist"])
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--limit", type=int, help="fetch only the first N TIC (smoke test)")
    ap.add_argument("--sentinel-every", type=int, default=200)
    ap.add_argument("--check-etta", action="store_true",
                    help="verify the requests path matches etta, then exit")
    a = ap.parse_args()

    if a.check_etta:
        return check_etta()

    con = duckdb.connect(str(DB), read_only=True)
    tics = [int(r[0]) for r in
            con.execute("select distinct tic_id from analysis_set order by tic_id").fetchall()]
    con.close()
    if a.limit:
        tics = tics[:a.limit]

    rc = 0
    if a.stage in (None, "repair"):
        rc = stage_repair() or rc
    if a.stage in (None, "pull"):
        rc2 = stage_pull(tics, a.workers, a.sentinel_every)
        if rc2 == 2:
            return 2
        rc = rc2 or rc
    if a.stage in (None, "verify"):
        rc2 = stage_verify(tics, a.workers)
        if rc2 == 2:
            return 2
    if a.stage in (None, "persist"):
        rc2 = stage_persist()
        if rc2:
            return rc2
    return rc


if __name__ == "__main__":
    sys.exit(main())
