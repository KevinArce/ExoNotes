"""Kepler Step 5 -- the Jev feature matrix over the CFOP corpus (PREREGISTRATION.md 11.10).

scripts/034_step3_features.py, adapted -- the machinery is kept as it is, including the fixes
that cost the TESS study something to learn:
  A-4  state is {"notes": ...}; no KOI or TIC identifier is sent
  A-5  MODEL pinned to "jev-1.13.0"; response["model"] asserted BEFORE anything is cached
  A-38 per-key locks: one call per distinct state however many workers land on it
  1    one request per state, all questions per request

What differs, and why:
  * the question set is `exonotes.questions_kepler` (kepler-2026-09-21.r3, frozen by A-41),
    never `exonotes.questions` (r6, frozen for TESS);
  * states are per HOST, so 4,720 KOI rows carry 3,843 distinct states;
  * the token model is re-fitted on the 60 r3 gate calls: 3621 + 0.4110 x chars (R^2 0.970);
  * the cost tripwire is $0.80 against a $0.6265 projection (A-41), registered before the run;
  * the paid run is recorded in a WRITE-ONCE file. 034 hard-coded its paid-run block after
    the fact because a cached re-run had overwritten a cost JSON (WORKLOG defect 24). Here the
    first run that makes calls writes research/data/kepler_step3_paid_run.json, and no later
    run may overwrite it; a re-run reports its own `*_this_run` numbers beside it.

Run:  .venv/bin/python scripts/048_kepler_step3_features.py --dry-run  # project only
      .venv/bin/python scripts/048_kepler_step3_features.py            # project, then run
Idempotent: yes. Cached on sha256(model + version + state + questions) under
data/cache/kepler_step3/; a re-run makes no calls and rebuilds a byte-identical matrix.
"""
import argparse, datetime, hashlib, http.client, json, os, pathlib, sys, threading, time
import urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import duckdb, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "kepler.duckdb"
CACHE = ROOT / "data" / "cache" / "kepler_step3"
OUTDIR = ROOT / "research" / "data"
PAID = OUTDIR / "kepler_step3_paid_run.json"

MODEL = "jev-1.13.0"                 # A-5
CONCURRENCY = 8
MAX_PROJECTED_USD = 0.80             # A-41
USD_PER_MTOK = 0.042
TOK_FIXED, TOK_PER_CHAR = 3621, 0.4110   # A-41, fitted on the 60 r3 gate calls

_envfile = ROOT / ".env"
if _envfile.exists():
    for line in _envfile.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip('"').strip("'")
KEY = os.environ.get("TYPESAFE_API_KEY", "")
if not KEY:
    raise SystemExit("no TYPESAFE_API_KEY found")

sys.path.insert(0, str(ROOT / "src"))
from exonotes.questions_kepler import (  # noqa: E402
    QUESTION_SET_VERSION, QUESTIONS, TIER_LABEL_ECHO, TIER_PREDICTIVE)

FROZEN = "kepler-2026-09-21.r3"
if QUESTION_SET_VERSION != FROZEN:
    raise SystemExit(f"question set is {QUESTION_SET_VERSION!r}, A-41 froze {FROZEN!r}. STOPPING.")

_QJSON = json.dumps(QUESTIONS, sort_keys=True, separators=(",", ":"))
_lock = threading.Lock()
_stats = {"new": 0, "cached": 0, "tokens": 0, "failed": 0}
_keylocks_guard = threading.Lock()
_keylocks: dict[str, threading.Lock] = {}


def _keylock(key):
    with _keylocks_guard:
        return _keylocks.setdefault(key, threading.Lock())


def cache_key(state):
    return hashlib.sha256((MODEL + QUESTION_SET_VERSION
                           + json.dumps(state, sort_keys=False, separators=(",", ":"))
                           + _QJSON).encode()).hexdigest()


def call(state):
    key = cache_key(state)
    hit = CACHE / f"{key}.json"
    if hit.exists():
        with _lock:
            _stats["cached"] += 1
        return json.loads(hit.read_text())
    with _keylock(key):
        if hit.exists():
            with _lock:
                _stats["cached"] += 1
            return json.loads(hit.read_text())
        return _fetch(state, hit)


def _fetch(state, hit):
    body = json.dumps({"model": MODEL, "state": state, "questions": QUESTIONS}).encode()
    transient = (urllib.error.URLError, http.client.RemoteDisconnected, ConnectionError, TimeoutError)
    last = None
    for attempt in range(6):
        req = urllib.request.Request(
            "https://api.typesafe.ai/v1/systemone", data=body,
            headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                out = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504) and attempt < 5:
                ra = e.headers.get("retry-after") if e.headers else None
                time.sleep(float(ra) if ra and ra.replace(".", "").isdigit() else 2 ** attempt)
                continue
            raise
        except transient as e:
            last = e
            if attempt < 5:
                time.sleep(2 ** attempt)
                continue
            raise
    else:
        raise RuntimeError(f"exhausted retries: {last!r}")
    if out.get("model") != MODEL:
        raise SystemExit(f"MODEL MISMATCH: pinned {MODEL!r}, response says {out.get('model')!r}. "
                         "Nothing cached (A-5). STOPPING.")
    CACHE.mkdir(parents=True, exist_ok=True)
    hit.write_text(json.dumps(out, indent=2))
    with _lock:
        _stats["new"] += 1
        _stats["tokens"] += out["usage"]["input_tokens"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="project cost and exit")
    a = ap.parse_args()

    with duckdb.connect(str(DB), read_only=True) as con:
        rows = con.execute("select kepoi_name, host, text from kepler_cfop_corpus "
                           "order by kepoi_name").fetchall()
    states = {}                                   # host -> text; one state per host
    for _, host, text in rows:
        if states.setdefault(host, text) != text:
            raise SystemExit(f"host {host} carries two different texts. STOPPING.")
    todo = {h: t for h, t in states.items() if not (CACHE / f"{cache_key({'notes': t})}.json").exists()}
    proj_tok = sum(TOK_FIXED + TOK_PER_CHAR * len(t) for t in todo.values())
    proj_usd = proj_tok / 1e6 * USD_PER_MTOK
    print(f"question set {QUESTION_SET_VERSION} · {len(QUESTIONS)} questions · model {MODEL}")
    print(f"KOI rows {len(rows):,} · distinct host states {len(states):,} · "
          f"already cached {len(states) - len(todo):,} · to call {len(todo):,}")
    print(f"projected {proj_tok:,.0f} input tokens · ${proj_usd:.4f} · tripwire ${MAX_PROJECTED_USD:.2f}")
    if proj_usd > MAX_PROJECTED_USD:
        raise SystemExit(f"COST TRIPWIRE: ${proj_usd:.4f} > ${MAX_PROJECTED_USD:.2f}. STOPPING before any call.")
    if a.dry_run:
        return 0

    t0 = time.time()
    answers = {}
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = {ex.submit(call, {"notes": t}): h for h, t in states.items()}
        for i, f in enumerate(as_completed(futs), 1):
            h = futs[f]
            try:
                answers[h] = f.result()
            except Exception as e:                    # noqa: BLE001
                _stats["failed"] += 1
                print(f"  FAILED host {h}: {type(e).__name__}: {e}", file=sys.stderr)
            if i % 300 == 0 or i == len(futs):
                print(f"  {i}/{len(futs)}  new={_stats['new']} cached={_stats['cached']} "
                      f"failed={_stats['failed']}  {time.time() - t0:.0f}s  "
                      f"${_stats['tokens'] / 1e6 * USD_PER_MTOK:.4f}")
    if _stats["failed"]:
        raise SystemExit(f"{_stats['failed']} states failed; not persisting a partial matrix. "
                         "Re-run: cached states cost nothing.")

    recs = []
    for kepoi, host, _ in rows:
        rec = {"kepoi_name": kepoi, "host": host}
        for qid, ans in answers[host]["answers"].items():
            rec[qid] = ans["noul"] if ans["type"] == "noul" else ans["score"]
            if ans["type"] == "score":
                rec[qid + "__conf"] = ans["confidence"]
        recs.append(rec)
    df = pd.DataFrame(recs).sort_values("kepoi_name").reset_index(drop=True)
    with duckdb.connect(str(DB)) as con:
        con.register("feat_df", df)
        con.execute("create or replace table kepler_jev_features as select * from feat_df")
    sha = hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()[:16]

    this_run = {"new_calls": _stats["new"], "cached_calls": _stats["cached"],
                "input_tokens": _stats["tokens"], "usd": _stats["tokens"] / 1e6 * USD_PER_MTOK,
                "elapsed_s": round(time.time() - t0, 1)}
    if _stats["new"] and not PAID.exists():       # write-once: the run that actually paid
        PAID.write_text(json.dumps({
            "recorded_utc": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%MZ"),
            "question_set_version": QUESTION_SET_VERSION, "model": MODEL,
            "distinct_states": len(states), "projected_usd": proj_usd, **this_run,
            "matrix_sha256_16": sha}, indent=2) + "\n")
    (OUTDIR / "kepler_step3_features_latest.json").write_text(json.dumps({
        "question_set_version": QUESTION_SET_VERSION, "model": MODEL, "rows": len(rows),
        "distinct_states": len(states), "this_run": this_run,
        "paid_run": json.loads(PAID.read_text()) if PAID.exists() else None,
        "tier_predictive": list(TIER_PREDICTIVE), "tier_label_echo": list(TIER_LABEL_ECHO),
        "matrix_sha256_16": sha}, indent=2) + "\n")
    print(f"\npersisted {len(df):,} rows x {len(QUESTIONS)} questions -> kepler.duckdb::kepler_jev_features")
    print(f"matrix sha256(to_csv)[:16] = {sha}")
    print(f"this run: new {_stats['new']:,} · cached {_stats['cached']:,} · tokens {_stats['tokens']:,} "
          f"· ${this_run['usd']:.4f} · {this_run['elapsed_s']:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
