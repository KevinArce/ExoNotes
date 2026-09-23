"""P1 — score the frozen T0 corpus and publish the registry's predictions (PREREGISTRATION.md
§11.14, A-45).

The order is part of the registration, and this script enforces it:

  1. A-45 is committed and on origin/master. `--registration-commit SHA` must be an ancestor of
     origin/master after a `git fetch`, and PREREGISTRATION.md at SHA must contain A-45.
  2. The frozen corpus is the one A-45 pinned. train_t0 / predict_t0 digests and the obsnotes
     manifest must equal research/data/prospective_freeze_manifest.json *as committed at SHA*.
  3. Jev scores every distinct text, training and prediction alike, in ONE session, into its
     own cache (data/cache/prospective/). That keeps train and predict features on the same
     side of any model drift. step3's cache is never read or written.
  4. Five arms are fit on train_t0, with ten CatBoost seeds each, and the probabilities averaged.
  5. The predictions (TOI ids and floats, no note text) are written to research/data/ with their
     sha256, together with a disposition snapshot taken at run time. That snapshot defines which
     candidates were still open when the predictions were made (053 evaluates only those).

Arms (A-45 45.4), identical CatBoost configuration to every TESS arm (`026`'s CB):
    B       8 numeric TOI columns
    Bmeta   B + note count, characters, authors, top-8 author one-hot (A-7's control)
    BTFIDF  B + C's TF-IDF + logistic pipeline as a stacked out-of-fold column (A-44)
    D       B + the 7 TIER_PREDICTIVE r6 features            <- the primary comparison is D vs B
    Dmeta   D + meta                                          <- the content test is Dmeta vs Bmeta

Run:
    .venv/bin/python scripts/052_prospective_predict.py --dry-run
        $0. No API call and no git check. It projects the cost, then runs every fit with MOCK
        features (a seeded random matrix) into data/prospective/dryrun/, to prove the
        pipeline end to end.
    .venv/bin/python scripts/052_prospective_predict.py --registration-commit <sha>
        The real run, ~$0.5-1.0 (A-45 45.9). Idempotent from the cache: re-running makes no new
        calls and rebuilds byte-identical predictions.
"""
import argparse
import hashlib
import http.client
import importlib.util
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import duckdb
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "prospective.duckdb"
CACHE = ROOT / "data" / "cache" / "prospective"
MANIFEST = ROOT / "research" / "data" / "prospective_freeze_manifest.json"
OUT_CSV = ROOT / "research" / "data" / "prospective_predictions_t0.csv"
OUT_META = ROOT / "research" / "data" / "prospective_predictions_t0.json"
DRY = ROOT / "data" / "prospective" / "dryrun"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

MODEL = "jev-1.13.0"            # A-5, unchanged
CONCURRENCY = 8
USD_PER_MTOK = 0.042
TOK_PER_CHAR, TOK_PER_STATE = 0.4177, 3376     # A-21's fit
MAX_PROJECTED_USD = 1.50                       # A-45 45.9 tripwire
N_SEEDS = 10                                   # A-45 45.4
REG_MARK = "### A-45"

_s = importlib.util.spec_from_file_location("nf", ROOT / "scripts" / "026_noise_floor.py")
nf = importlib.util.module_from_spec(_s)
_s.loader.exec_module(nf)
sys.path.insert(0, str(ROOT / "src"))
from exonotes.leakage import OBSNOTES_PATTERNS  # noqa: E402
from exonotes.questions import (  # noqa: E402
    QUESTION_SET_VERSION, QUESTIONS, TIER_PREDICTIVE)

NUMERIC, CB, SEED0 = nf.NUMERIC, nf.CB, nf.RANDOM_STATE
PRED = list(TIER_PREDICTIVE)
ARMS = ["B", "Bmeta", "BTFIDF", "D", "Dmeta"]
_QJSON = json.dumps(QUESTIONS, sort_keys=True, separators=(",", ":"))
# A-45 45.6: the TESS analogue of Kepler's K10 (reassessment E5). A named system exists only
# once a planet in it has been confirmed, so a note naming one can echo the label.
SURVEY_RX = re.compile(r"\b(?:WASP|HAT-P|HATS|KELT|XO|TrES|Qatar|NGTS|WTS|CoRoT|K2|Kepler|"
                       r"MASCARA|KPS)-\d+")


# --------------------------------------------------------------------------- the featurizer
def cache_key(state: dict) -> str:
    """034's key, unchanged: model + question-set version + state + questions."""
    return hashlib.sha256((MODEL + QUESTION_SET_VERSION
                           + json.dumps(state, sort_keys=False, separators=(",", ":"))
                           + _QJSON).encode()).hexdigest()


class Jev:
    """034's request path with its per-key locks, pointed at this script's own cache.

    Deliberately a copy, not an import: 034's `call` reads 034's module-global CACHE, and
    swapping another module's globals from worker threads is defect 34.
    """

    def __init__(self, key: str):
        self.key = key
        self.lock = threading.Lock()
        self.guard = threading.Lock()
        self.keylocks: dict[str, threading.Lock] = {}
        self.stats = {"new": 0, "cached": 0, "tokens": 0}

    def _keylock(self, k):
        with self.guard:
            return self.keylocks.setdefault(k, threading.Lock())

    def call(self, state: dict) -> dict:
        k = cache_key(state)
        hit = CACHE / f"{k}.json"
        if hit.exists():
            with self.lock:
                self.stats["cached"] += 1
            return json.loads(hit.read_text())
        with self._keylock(k):
            if hit.exists():
                with self.lock:
                    self.stats["cached"] += 1
                return json.loads(hit.read_text())
            return self._fetch(state, hit)

    def _fetch(self, state, hit):
        body = json.dumps({"model": MODEL, "state": state, "questions": QUESTIONS}).encode()
        transient = (urllib.error.URLError, http.client.RemoteDisconnected,
                     ConnectionError, TimeoutError)
        last = None
        for attempt in range(6):
            req = urllib.request.Request(
                "https://api.typesafe.ai/v1/systemone", data=body,
                headers={"Authorization": f"Bearer {self.key}",
                         "Content-Type": "application/json"})
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
            raise SystemExit(f"MODEL MISMATCH: pinned {MODEL!r}, got {out.get('model')!r}. "
                             "Nothing cached. STOPPING (A-5; A-45 45.10 says what happens next).")
        CACHE.mkdir(parents=True, exist_ok=True)
        hit.write_text(json.dumps(out, indent=2))
        with self.lock:
            self.stats["new"] += 1
            self.stats["tokens"] += out["usage"]["input_tokens"]
        return out


def encode(out: dict) -> dict:
    """034's encoding: noul -> probability, score -> expected level."""
    rec = {}
    for q in PRED:
        a = out["answers"][q]
        rec[q] = a["noul"] if a["type"] == "noul" else a["score"]
    return rec


def mock_features(texts: list[str]) -> dict[str, dict]:
    """Dry-run stand-in: deterministic per text, two decimals like Jev, no API call."""
    feats = {}
    for t in texts:
        rng = np.random.default_rng(int(hashlib.sha256(t.encode()).hexdigest()[:8], 16))
        feats[t] = {q: (round(float(rng.uniform(0, 4)), 2) if QUESTIONS[q]["type"] == "score"
                        else round(float(rng.uniform(0, 1)), 2)) for q in PRED}
    return feats


# --------------------------------------------------------------------------- guards
def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True,
                          text=True).stdout


def check_registration(sha: str) -> dict:
    git("fetch", "--quiet", "origin")
    r = subprocess.run(["git", "merge-base", "--is-ancestor", sha, "origin/master"], cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit(f"REFUSING: {sha} is not on origin/master. A-45 must be public before "
                         "the first paid call (A-45 45.1). Push the registration first.")
    if REG_MARK not in git("show", f"{sha}:PREREGISTRATION.md"):
        raise SystemExit(f"REFUSING: PREREGISTRATION.md at {sha} does not contain {REG_MARK!r}.")
    registered = json.loads(git("show", f"{sha}:research/data/prospective_freeze_manifest.json"))
    when = git("show", "-s", "--format=%cI", sha).strip()
    print(f"registration: {sha[:12]} on origin/master, committed {when}")
    return registered


def check_freeze(con, registered: dict | None) -> dict:
    local = json.loads(MANIFEST.read_text())
    ref = registered or local
    train = con.execute("select * from train_t0 order by toi").df()
    pred = con.execute("select * from predict_t0 order by toi").df()
    got = {"train": hashlib.sha256(train.to_csv(index=False).encode()).hexdigest()[:16],
           "pred": hashlib.sha256(pred.to_csv(index=False).encode()).hexdigest()[:16]}
    want = {"train": ref["train_t0"]["sha16"], "pred": ref["predict_t0"]["sha16"]}
    if got != want or local["obsnotes_manifest_sha256"] != ref["obsnotes_manifest_sha256"]:
        raise SystemExit(f"REFUSING: the frozen corpus is not the one A-45 pinned "
                         f"(got {got}, registered {want}).")
    print(f"freeze      : train_t0 {got['train']} · predict_t0 {got['pred']} · manifest "
          f"{ref['obsnotes_manifest_sha256'][:16]}  = registered")
    return {"train": train, "pred": pred}


# --------------------------------------------------------------------------- the arms
def meta_frame(rows: pd.DataFrame, authors: pd.DataFrame, top: list[str]) -> pd.DataFrame:
    """A-7's B+meta columns. The top-8 authors are fixed on the TRAINING corpus only."""
    wide = (authors[authors.username.isin(top)]
            .pivot_table(index="tic_id", columns="username", values="n", fill_value=0))
    wide = wide.reindex(columns=top, fill_value=0)
    wide.columns = [f"auth_{c}" for c in wide.columns]
    m = rows[["tic_id", "n_notes_obs", "n_chars", "n_authors"]].merge(
        wide, left_on="tic_id", right_index=True, how="left").fillna(0)
    return m.drop(columns=["tic_id"]).reset_index(drop=True)


def tfidf_pipe():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    return make_pipeline(TfidfVectorizer(min_df=3, max_features=50_000, sublinear_tf=True),
                         LogisticRegression(max_iter=2000, C=1.0))


def tfidf_column(train, pred):
    """Training rows: inner GroupKFold(5) out-of-fold. Prediction rows: fit on all training."""
    from sklearn.model_selection import GroupKFold
    y, g = train.y.astype(int).to_numpy(), train.tic_id.to_numpy()
    t_tr, t_pr = train.notes.fillna("").to_numpy(), pred.notes.fillna("").to_numpy()
    oof = np.zeros(len(train))
    for a, b in GroupKFold(5).split(t_tr, groups=g):
        oof[b] = tfidf_pipe().fit(t_tr[a], y[a]).predict_proba(t_tr[b])[:, 1]
    return oof, tfidf_pipe().fit(t_tr, y).predict_proba(t_pr)[:, 1]


def fit_arm(Xtr: pd.DataFrame, y: np.ndarray, Xpr: pd.DataFrame) -> np.ndarray:
    from catboost import CatBoostClassifier
    P = np.zeros((N_SEEDS, len(Xpr)))
    for i in range(N_SEEDS):
        clf = CatBoostClassifier(random_seed=SEED0 + i, **CB)
        clf.fit(Xtr, y)
        P[i] = clf.predict_proba(Xpr[Xtr.columns])[:, 1]
    return P.mean(0)


def build_predictions(train, pred, feats, authors) -> pd.DataFrame:
    y = train.y.astype(int).to_numpy()
    num = lambda d: d[NUMERIC].apply(pd.to_numeric, errors="coerce").reset_index(drop=True)
    jf = lambda d: pd.DataFrame([feats[t] for t in d.notes]).reset_index(drop=True)[PRED]
    top = (authors[authors.tic_id.isin(set(train.tic_id))].groupby("username")["n"].sum()
           .sort_values(ascending=False).head(8).index.tolist())
    Mtr, Mpr = meta_frame(train, authors, top), meta_frame(pred, authors, top)
    oof, tf_pr = tfidf_column(train, pred)
    X = {
        "B": (num(train), num(pred)),
        "Bmeta": (pd.concat([num(train), Mtr], axis=1), pd.concat([num(pred), Mpr], axis=1)),
        "BTFIDF": (num(train).assign(tfidf=oof), num(pred).assign(tfidf=tf_pr)),
        "D": (pd.concat([num(train), jf(train)], axis=1), pd.concat([num(pred), jf(pred)], axis=1)),
        "Dmeta": (pd.concat([num(train), jf(train), Mtr], axis=1),
                  pd.concat([num(pred), jf(pred), Mpr], axis=1)),
    }
    out = pred[["toi", "tic_id", "tfopwg_disp", "tic_has_labelled_toi"]].reset_index(drop=True)
    for arm in ARMS:
        out[f"p_{arm}"] = fit_arm(X[arm][0], y, X[arm][1])
        print(f"  fitted {arm:<7} ({X[arm][0].shape[1]} columns, {N_SEEDS} seeds)")
    survey = OBSNOTES_PATTERNS | {"K10_survey_system_name": SURVEY_RX}
    out["leak_clause"] = [any(rx.search(t or "") for rx in survey.values()) for t in pred.notes]
    for q in PRED:
        out[f"f_{q}"] = jf(pred)[q]
    return out, top



def nea_disposition_snapshot(path: pathlib.Path) -> pd.DataFrame:
    q = urllib.parse.urlencode({"query": "select toi, tfopwg_disp from toi", "format": "csv"})
    with urllib.request.urlopen(f"{TAP}?{q}", timeout=600) as r:
        txt = r.read().decode()
    if txt.lstrip().lower().startswith("<") or "tfopwg_disp" not in txt.splitlines()[0]:
        raise SystemExit(f"TAP returned something that is not the toi table: {txt[:200]}")
    path.write_text(txt)
    return pd.read_csv(io.StringIO(txt))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--registration-commit")
    a = ap.parse_args()
    if not a.dry_run and not a.registration_commit:
        ap.error("the real run needs --registration-commit <sha> (A-45 45.1); or use --dry-run")

    registered = None if a.dry_run else check_registration(a.registration_commit)
    con = duckdb.connect(str(DB), read_only=True)
    frames = check_freeze(con, registered)
    authors = con.execute("""select tic_id, username, count(*) n from notes_raw_t0
                             where groupname is null group by 1, 2""").df()
    con.close()
    train, pred = frames["train"], frames["pred"]

    texts = sorted(set(train.notes) | set(pred.notes))
    todo = [t for t in texts if not (CACHE / f"{cache_key({'notes': t})}.json").exists()]
    proj_tok = sum(TOK_PER_CHAR * len(t) + TOK_PER_STATE for t in todo)
    proj_usd = proj_tok / 1e6 * USD_PER_MTOK
    print(f"corpus      : train {len(train):,} rows / {train.tic_id.nunique():,} TIC "
          f"(base {train.y.mean():.4f}) · predict {len(pred):,} rows / "
          f"{pred.tic_id.nunique():,} TIC")
    print(f"featurizer  : {MODEL} · {QUESTION_SET_VERSION} · {len(texts):,} distinct texts, "
          f"{len(texts) - len(todo):,} cached · to call {len(todo):,} · projected "
          f"{proj_tok:,.0f} tokens · ${proj_usd:.4f} (tripwire ${MAX_PROJECTED_USD:.2f})")
    if proj_usd > MAX_PROJECTED_USD:
        raise SystemExit("COST TRIPWIRE fired before any call. Check the state sizes.")

    t0 = time.time()
    if a.dry_run:
        feats = mock_features(texts)
        print("featurizer  : DRY RUN, mock features, no API call")
    else:
        envf = ROOT / ".env"
        if envf.exists():
            for line in envf.read_text().splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        key = os.environ.get("TYPESAFE_API_KEY", "")
        if not key:
            raise SystemExit("no TYPESAFE_API_KEY")
        jev, feats, failed = Jev(key), {}, 0
        with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
            futs = {ex.submit(jev.call, {"notes": t}): t for t in texts}
            for i, f in enumerate(as_completed(futs), 1):
                try:
                    feats[futs[f]] = encode(f.result())
                except Exception as e:  # noqa: BLE001
                    failed += 1
                    print(f"  FAILED: {type(e).__name__}: {e}", file=sys.stderr)
                if i % 250 == 0 or i == len(texts):
                    print(f"  {i:,}/{len(texts):,}  new={jev.stats['new']} "
                          f"cached={jev.stats['cached']}  "
                          f"${jev.stats['tokens'] / 1e6 * USD_PER_MTOK:.4f}", flush=True)
        if failed:
            raise SystemExit(f"{failed} texts failed; nothing written. Re-run (cache is free).")

    print("arms        :")
    out, top8 = build_predictions(train, pred, feats, authors)

    target = DRY if a.dry_run else OUT_CSV.parent
    target.mkdir(parents=True, exist_ok=True)
    csv_p = target / OUT_CSV.name
    snap_p = (DRY if a.dry_run else ROOT / "data" / "prospective" / "raw") / "nea_toi_at_prediction.csv"
    snap = nea_disposition_snapshot(snap_p)
    snap["toi"] = pd.to_numeric(snap.toi, errors="coerce")
    now_disp = out.toi.map(snap.set_index("toi").tfopwg_disp)
    out["disp_at_prediction"] = now_disp
    out["open_at_prediction"] = now_disp.isin(["PC", "APC"])
    out = out.sort_values("toi").reset_index(drop=True)
    csv_bytes = out.to_csv(index=False, float_format="%.6f").encode()
    csv_p.write_bytes(csv_bytes)
    meta = {
        "registration": "PREREGISTRATION.md §11.14 (A-45)",
        "registration_commit": a.registration_commit,
        "dry_run": a.dry_run,
        "predicted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": MODEL, "question_set_version": QUESTION_SET_VERSION,
        "arms": ARMS, "catboost": CB, "seeds": N_SEEDS, "top8_authors": top8,
        "rows": len(out), "open_at_prediction": int(out.open_at_prediction.sum()),
        "predictions_sha256": hashlib.sha256(csv_bytes).hexdigest(),
        "nea_toi_at_prediction_sha256": hashlib.sha256(snap_p.read_bytes()).hexdigest(),
        "featurizer": ({"mock": True} if a.dry_run else
                       {**jev.stats, "usd": jev.stats["tokens"] / 1e6 * USD_PER_MTOK,
                        "distinct_texts": len(texts)}),
        "elapsed_s": round(time.time() - t0, 1),
    }
    (target / OUT_META.name).write_text(json.dumps(meta, indent=2) + "\n")
    print(f"\nwrote {csv_p.relative_to(ROOT)}  sha256 {meta['predictions_sha256'][:16]}")
    print(f"      {len(out):,} predictions · {meta['open_at_prediction']:,} still open at prediction")
    if not a.dry_run:
        print("NEXT (A-45 45.1): commit and push research/data/prospective_predictions_t0.* "
              "within 24 hours. The push time is T_pub.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
