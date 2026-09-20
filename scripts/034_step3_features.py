"""Step 3 — compute the Jev feature matrix over the obsnotes corpus (TASK C; PLAN.md §6).

One request per row, all questions per request, bounded concurrency, content-addressed
cache, full raw response JSON persisted.

Registered constraints honoured here:
  A-4  state is {"notes": ...} -- `toi` is NOT sent
  A-5  MODEL pinned to "jev-1.13.0"; response["model"] asserted BEFORE anything is cached
  §1   one request per row, many questions per request (never several TOIs in one state)
  §6   cost tripwire: if the projection exceeds MAX_PROJECTED_USD, stop before spending

DEVIATION from the handoff's "async client, bounded semaphore", logged per PLAN.md §0.5 rule 4:
`aiohttp` and `httpx` are not installed and this project does not add dependencies mid-study
(`requirements.txt` is part of the reproduction contract). A `ThreadPoolExecutor` with
`max_workers=CONCURRENCY` is the same bounded-concurrency guarantee over the same blocking
`urllib` transport `scripts/025` and `032` already use. Same semantics, no new dependency.

NOTE ON CACHE HITS: the state is per-TIC text, so the 1,482 rows carry only ~1,388 distinct
states. Duplicate states hash to the same key and are served from cache, so the run makes
~1,388 calls, not 1,482.

Run:  .venv/bin/python scripts/034_step3_features.py            # project cost, then run
      .venv/bin/python scripts/034_step3_features.py --dry-run  # project only, no calls
Idempotent: yes. Every response is cached on
sha256(model + question_set_version + state + questions); a re-run makes no API calls and
returns byte-identical results. Bump QUESTION_SET_VERSION to force a real re-run.
"""
import argparse
import hashlib
import http.client
import json
import os
import pathlib
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import duckdb

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "exonotes.duckdb"
CACHE = ROOT / "data" / "cache" / "step3"
OUTDIR = ROOT / "research" / "data"

MODEL = "jev-1.13.0"                 # A-5
CONCURRENCY = 8                      # the bounded semaphore; limits are 1,200 req/min
MAX_PROJECTED_USD = 0.50             # §6 tripwire
USD_PER_MTOK = 0.042

# Fitted on the 27 TASK B gate calls (A-21): input_tokens = 0.4177*chars + 3376.
# Re-fitted here against the r6 question payload actually being sent.
TOK_PER_CHAR = 0.4177

for line in (ROOT / ".env").read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ[k.strip()] = v.strip().strip('"').strip("'")
KEY = os.environ.get("TYPESAFE_API_KEY", "")
if not KEY:
    raise SystemExit("no TYPESAFE_API_KEY found")

sys.path.insert(0, str(ROOT / "src"))
from exonotes.questions import (  # noqa: E402
    QUESTION_SET_VERSION, QUESTIONS, TIER_LABEL_ECHO, TIER_PREDICTIVE)

_QJSON = json.dumps(QUESTIONS, sort_keys=True, separators=(",", ":"))
_lock = threading.Lock()
_stats = {"new": 0, "cached": 0, "tokens": 0, "failed": 0}

# Per-key locks. The first run made 1,462 calls for 1,382 distinct states: the cache was
# checked at the top of call() and written at the bottom, so two workers landing on the same
# state both missed and both paid (80 duplicate calls, ~$0.013). Serialising per key makes the
# second worker wait and then hit the cache. The key, the request body and the response
# handling are untouched, so cached responses stay valid.
_keylocks_guard = threading.Lock()
_keylocks: dict[str, threading.Lock] = {}


def _keylock(key: str) -> threading.Lock:
    with _keylocks_guard:
        return _keylocks.setdefault(key, threading.Lock())


def cache_key(state):
    return hashlib.sha256(
        (MODEL + QUESTION_SET_VERSION
         + json.dumps(state, sort_keys=False, separators=(",", ":"))
         + _QJSON).encode()).hexdigest()


def call(state):
    """One request. Returns (response, from_cache). Raises on unrecoverable failure."""
    key = cache_key(state)
    hit = CACHE / f"{key}.json"
    if hit.exists():
        with _lock:
            _stats["cached"] += 1
        return json.loads(hit.read_text()), True

    # Only one worker per distinct state gets to call; the rest wait and take the cache.
    with _keylock(key):
        if hit.exists():
            with _lock:
                _stats["cached"] += 1
            return json.loads(hit.read_text()), True
        return _fetch(state, hit)


def _fetch(state, hit):
    """The network half of call(). Runs holding that state's key lock."""
    body = json.dumps({"model": MODEL, "state": state, "questions": QUESTIONS}).encode()
    transient = (urllib.error.URLError, http.client.RemoteDisconnected,
                 ConnectionError, TimeoutError)
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
                # Honour retry-after when the response carries one (docs: rate limits).
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

    got = out.get("model")
    if got != MODEL:
        raise SystemExit(
            f"MODEL MISMATCH: pinned {MODEL!r}, response says {got!r}. Nothing cached. "
            "The literal sits inside the cache key (A-5). STOPPING.")
    CACHE.mkdir(parents=True, exist_ok=True)
    hit.write_text(json.dumps(out, indent=2))
    with _lock:
        _stats["new"] += 1
        _stats["tokens"] += out["usage"]["input_tokens"]
    return out, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="project cost and exit")
    args = ap.parse_args()

    con = duckdb.connect(str(DB))
    rows = con.execute(
        "select tic_id, cast(toi as varchar), notes from analysis_set_obsnotes order by toi"
    ).fetchall()

    # --- §6 cost tripwire, evaluated on the DISTINCT states actually sent ----------------
    seen, distinct = set(), []
    for tic, toi, notes in rows:
        k = cache_key({"notes": notes})
        if k not in seen:
            seen.add(k)
            distinct.append(notes)
    already = sum(1 for k in seen if (CACHE / f"{k}.json").exists())
    todo_chars = sum(len(n) for n in distinct
                     if not (CACHE / f"{cache_key({'notes': n})}.json").exists())
    n_todo = len(distinct) - already
    proj_tok = TOK_PER_CHAR * todo_chars + 3376 * n_todo
    proj_usd = proj_tok / 1e6 * USD_PER_MTOK

    print(f"question set {QUESTION_SET_VERSION} · {len(QUESTIONS)} questions · model {MODEL}")
    print(f"rows {len(rows)} · distinct states {len(distinct)} "
          f"(dedup saves {len(rows) - len(distinct)} calls) · already cached {already}")
    print(f"to call: {n_todo} · projected {proj_tok:,.0f} input tokens · "
          f"projected ${proj_usd:.4f}")
    if proj_usd > MAX_PROJECTED_USD:
        raise SystemExit(
            f"COST TRIPWIRE: projected ${proj_usd:.4f} exceeds ${MAX_PROJECTED_USD:.2f}. "
            "STOPPING before any call. Check the state size (PLAN.md §6).")
    print(f"tripwire ${MAX_PROJECTED_USD:.2f}: not fired\n")
    if args.dry_run:
        return 0

    t0 = time.time()
    results = {}
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = {ex.submit(call, {"notes": n}): (tic, toi, n)
                for tic, toi, n in rows}
        done = 0
        for f in as_completed(futs):
            tic, toi, notes = futs[f]
            done += 1
            try:
                out, _ = f.result()
            except Exception as e:                       # noqa: BLE001
                _stats["failed"] += 1
                print(f"  FAILED TOI {toi} TIC {tic}: {type(e).__name__}: {e}",
                      file=sys.stderr)
                continue
            results[(tic, toi)] = out
            if done % 150 == 0 or done == len(rows):
                el = time.time() - t0
                print(f"  {done}/{len(rows)}  new={_stats['new']} cached={_stats['cached']} "
                      f"failed={_stats['failed']}  {el:.0f}s  "
                      f"${_stats['tokens'] / 1e6 * USD_PER_MTOK:.4f}")

    if _stats["failed"]:
        raise SystemExit(f"{_stats['failed']} rows failed; not persisting a partial matrix. "
                         "Re-run: cached rows cost nothing.")

    # --- build the feature matrix -------------------------------------------------------
    qids = list(QUESTIONS)
    cols = []
    for (tic, toi), out in results.items():
        rec = {"tic_id": tic, "toi": toi}
        for qid in qids:
            a = out["answers"][qid]
            rec[qid] = a["noul"] if a["type"] == "noul" else a["score"]
            if a["type"] == "score":
                rec[qid + "__conf"] = a["confidence"]
        cols.append(rec)

    import pandas as pd
    df = pd.DataFrame(cols).sort_values("toi").reset_index(drop=True)
    con.execute("create or replace table jev_features_obsnotes as select * from df")
    n_persisted = con.execute("select count(*) from jev_features_obsnotes").fetchone()[0]

    meta = {
        "question_set_version": QUESTION_SET_VERSION,
        "model": MODEL,
        "rows": len(rows),
        "distinct_states": len(distinct),
        # "this run" figures: a warm re-run legitimately reports zero. The run that actually
        # paid is recorded below and in PROVENANCE.md, so a cached re-run cannot erase it.
        "new_calls_this_run": _stats["new"],
        "cached_calls_this_run": _stats["cached"],
        "input_tokens_this_run": _stats["tokens"],
        "usd_this_run": _stats["tokens"] / 1e6 * USD_PER_MTOK,
        "paid_run": {
            "new_calls": 1462,
            "distinct_states": 1382,
            "duplicate_calls_from_cache_race": 80,
            "input_tokens": 5_763_547,
            "usd": 0.2421,
            "recorded": "PROVENANCE.md step3 block; WORKLOG.md 2026-09-20T20:48Z",
            "note": ("The matrix that run persisted was NOT reproducible from this cache -- see "
                     "PREREGISTRATION.md §11.8 A-38. A per-key lock fixed the cause; the "
                     "current matrix is rebuilt from the cache and is stable across re-runs."),
        },
        "tier_predictive": list(TIER_PREDICTIVE),
        "tier_label_echo": list(TIER_LABEL_ECHO),
        "persisted_rows": n_persisted,
        "elapsed_s": time.time() - t0,
    }
    (OUTDIR / "step3_features_2026-09-20.json").write_text(json.dumps(meta, indent=2))
    con.close()

    print(f"\npersisted {n_persisted} rows x {len(qids)} features "
          f"-> duckdb::jev_features_obsnotes")
    print(f"new calls {_stats['new']} · cached {_stats['cached']} · "
          f"tokens {_stats['tokens']:,} · **${_stats['tokens'] / 1e6 * USD_PER_MTOK:.4f}** "
          f"· {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
