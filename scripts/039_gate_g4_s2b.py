"""Gate G4 with S2b applied — the note-level temporal filter (TASK E; PREREGISTRATION.md §4).

§4 registers three parts to the temporal split and TASK C applied only two:

  S2   date cutoff 2021-10-28 on `date_toi_alerted`                      applied in 035
  S2a  drop from TEST any row whose tic_id also appears in train         applied in 035
  S2b  for the TRAINING side only, include a note iff Lastmod < cutoff   NOT applied  <- this

A-28 says so explicitly rather than leaving it implicit: "G4 is therefore the S2 + S2a result."
This script closes that gap, so G4 is measured on the split as registered.

WHAT S2b DOES TO THE DATA (measured, WORKLOG.md 21:58Z):
  * 2,865 of 3,963 observer notes survive the cutoff (72.3%). Lastmod is non-null on all
    6,855 notes, so §4's undated-note case does not arise on this corpus.
  * Of 1,070 training rows: 669 are unchanged, 401 change, and 186 of those lose ALL their
    text and therefore leave the corpus (§1.1 requires >=1 observer note of non-zero length).
    Training goes 1,070 -> 884.

FOUR DECISIONS, fixed before the run and recorded in WORKLOG.md 21:58Z:
  1. A row whose S2b text is empty leaves the training set. That is §4's own "tests on LESS
     text, not on OLDER text", made concrete.
  2. B and D both train on those same 884 rows, so dAUC is not conflating the text filter with
     a sample-size change. B on the full 1,070 is ALSO reported so that component is visible.
  3. The test side is untouched -- the same 390 rows as A-28's G4, so G4 and G4b are directly
     comparable. Shrinking train can only shrink the train-TIC set, so S2a's fix stays valid on
     a fixed test set; re-running S2a would only add test rows back. Fixed is conservative.
  4. New responses cache to data/cache/s2b/, NEVER to data/cache/step3/, which is exactly 1,382
     files = its distinct-state count and is committed to that number in PROVENANCE.md. A
     legitimate hit in step3/ is used (identical request -> free); writes only ever land in s2b/.
     This is WORKLOG.md 21:31Z defect 1 inverted -- there s3.CACHE was NOT patched and paraphrase
     responses leaked into step3/. Here it is patched deliberately.

Run:  .venv/bin/python scripts/039_gate_g4_s2b.py [--dry-run]
Idempotent: yes. Content-addressed cache, fixed seeds, CREATE OR REPLACE output. Re-run: $0.
"""
import argparse
import importlib.util
import json
import pathlib
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

import duckdb
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "exonotes.duckdb"
OUT = ROOT / "research" / "data"
STEP3_CACHE = ROOT / "data" / "cache" / "step3"
S2B_CACHE = ROOT / "data" / "cache" / "s2b"

S2_CUTOFF = "2021-10-28"          # §4, fixed before any result


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


nf = _load("nf", ROOT / "scripts" / "026_noise_floor.py")
s3 = _load("s3", ROOT / "scripts" / "034_step3_features.py")

sys.path.insert(0, str(ROOT / "src"))
from exonotes.questions import QUESTION_SET_VERSION, QUESTIONS, TIER_PREDICTIVE  # noqa: E402

NUMERIC = nf.NUMERIC
PRED = list(TIER_PREDICTIVE)

# Decision 4. Patched ONCE, before any worker starts, so s3.call writes here and never to
# step3/. The step3 lookup below is read-only.
s3.CACHE = S2B_CACHE


def call_s2b(state):
    """Free if Step 3 already holds this exact request; otherwise call and cache in s2b/."""
    hit = STEP3_CACHE / f"{s3.cache_key(state)}.json"
    if hit.exists():
        return json.loads(hit.read_text()), True
    return s3.call(state)


def s2b_text(raw: pd.DataFrame, cutoff: str) -> pd.Series:
    """Per-TIC observer text over notes with Lastmod < cutoff.

    Identical construction to scripts/028_obsnotes_pull.py: observer notes only, ascending
    (lastmod, seq), space-joined. A note with no Lastmod does not satisfy "Lastmod < cutoff"
    and is dropped -- §4's safe direction. On this corpus Lastmod is never null, so the branch
    is defensive only.
    """
    obs = raw[~raw.is_tfopwg].copy()
    obs = obs[obs.lastmod.notna() & (obs.lastmod < cutoff)]
    obs["_sort"] = obs.lastmod.fillna("9999")
    obs = obs.sort_values(["tic_id", "_sort", "seq"], kind="stable")
    return obs.groupby("tic_id")["notes_text"].apply(lambda s: " ".join(x for x in s if x))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="project cost and exit")
    ap.add_argument("--seeds", type=int, default=10,
                    help="CatBoost seeds for the S2 fit-variance arm")
    args = ap.parse_args()

    con = duckdb.connect(str(DB))
    df = con.execute("""
        select a.*, f.* exclude (tic_id, toi)
        from analysis_set_obsnotes a
        join jev_features_obsnotes f on f.toi = cast(a.toi as varchar)
        order by a.toi""").df()
    raw = con.execute("select * from obsnotes_raw").df()
    df = df.loc[:, ~df.columns.duplicated()].reset_index(drop=True)

    y = df["y"].astype(int).to_numpy()
    d = pd.to_datetime(df["date_toi_alerted"], errors="coerce")
    tr_mask = (d < S2_CUTOFF).to_numpy()
    te_mask = (d >= S2_CUTOFF).to_numpy()
    leak = te_mask & df["tic_id"].isin(set(df.loc[tr_mask, "tic_id"])).to_numpy()
    te_mask = te_mask & ~leak                                   # S2a, exactly as in 035

    new_text = df["tic_id"].map(s2b_text(raw, S2_CUTOFF)).fillna("")
    changed = tr_mask & (new_text.to_numpy() != df["notes"].to_numpy())
    emptied = tr_mask & (new_text.str.len().to_numpy() == 0)
    need = changed & ~emptied
    keep_tr = tr_mask & ~emptied                                # decision 1

    print(f"question set {QUESTION_SET_VERSION} · model {s3.MODEL} · cutoff {S2_CUTOFF}")
    print(f"S2+S2a  train {tr_mask.sum()} · test {te_mask.sum()} "
          f"(S2a dropped {leak.sum()})")
    print(f"S2b     train text unchanged {int((tr_mask & ~changed).sum())} · "
          f"changed {int(changed.sum())} · emptied {int(emptied.sum())}")
    print(f"        training set {tr_mask.sum()} -> {keep_tr.sum()} rows · "
          f"base {y[tr_mask].mean():.4f} -> {y[keep_tr].mean():.4f}")

    states = {t for t in new_text[need].unique() if t}
    todo = [t for t in states
            if not (STEP3_CACHE / f"{s3.cache_key({'notes': t})}.json").exists()
            and not (S2B_CACHE / f"{s3.cache_key({'notes': t})}.json").exists()]
    proj_tok = s3.TOK_PER_CHAR * sum(len(t) for t in todo) + 3376 * len(todo)
    proj_usd = proj_tok / 1e6 * s3.USD_PER_MTOK
    print(f"        rows needing features {int(need.sum())} over {len(states)} distinct "
          f"states · {len(todo)} uncached · projected ${proj_usd:.4f}")
    if proj_usd > s3.MAX_PROJECTED_USD:
        raise SystemExit(f"COST TRIPWIRE: ${proj_usd:.4f} > ${s3.MAX_PROJECTED_USD:.2f}. STOP.")
    if args.dry_run:
        return 0

    # --- score the S2b training text --------------------------------------------------
    t0 = time.time()
    feats, failed = {}, 0
    S2B_CACHE.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=s3.CONCURRENCY) as ex:
        futs = {ex.submit(call_s2b, {"notes": t}): t for t in states}
        for i, f in enumerate(as_completed(futs), 1):
            t = futs[f]
            try:
                out, _ = f.result()
            except Exception as e:                                # noqa: BLE001
                failed += 1
                print(f"  FAILED state len={len(t)}: {type(e).__name__}: {e}", file=sys.stderr)
                continue
            feats[t] = {q: (out["answers"][q]["noul"] if out["answers"][q]["type"] == "noul"
                            else out["answers"][q]["score"]) for q in QUESTIONS}
            if i % 50 == 0 or i == len(futs):
                print(f"  {i}/{len(futs)}  new={s3._stats['new']} "
                      f"cached={s3._stats['cached']}  {time.time() - t0:.0f}s  "
                      f"${s3._stats['tokens'] / 1e6 * s3.USD_PER_MTOK:.4f}")
    if failed:
        raise SystemExit(f"{failed} states failed; not reporting a partial gate. Re-run is free.")
    usd = s3._stats["tokens"] / 1e6 * s3.USD_PER_MTOK
    print(f"  new calls {s3._stats['new']} · cached {s3._stats['cached']} · "
          f"tokens {s3._stats['tokens']:,} · ${usd:.4f}\n")

    # --- the S2b feature matrix: replace ONLY the changed training rows ----------------
    Xpred_s2b = df[PRED].apply(pd.to_numeric, errors="coerce").copy()
    for i in np.flatnonzero(need):
        Xpred_s2b.loc[i, PRED] = [feats[new_text.iloc[i]][q] for q in PRED]
    Xnum = df[NUMERIC].apply(pd.to_numeric, errors="coerce")

    def arm(train_mask, X):
        from catboost import CatBoostClassifier
        m = CatBoostClassifier(random_seed=nf.RANDOM_STATE, **nf.CB)
        m.fit(X[train_mask], y[train_mask])
        return m.predict_proba(X[te_mask])[:, 1]

    gte = df.loc[te_mask, "tic_id"].to_numpy()
    yte = y[te_mask]
    res = {}

    def report(name, pb, pdd, note=""):
        ab, ad = nf.fast_auc(yte, pb), nf.fast_auc(yte, pdd)
        lo, hi, se = nf.paired_group_bootstrap(pb[None, :], pdd[None, :], yte, gte, nf.N_BOOT)
        ok = bool(lo > 0 or hi < 0)
        print(f"  {name:<34} B={ab:.4f}  D={ad:.4f}  dAUC={ad - ab:+.4f}  "
              f"[{lo:+.4f}, {hi:+.4f}]  {'EXCLUDES 0' if ok else 'includes 0'}{note}")
        res[name] = dict(auc_B=ab, auc_D=ad, dauc=ad - ab, ci_lo=lo, ci_hi=hi, se=se,
                         excludes_zero=ok)
        return res[name]

    Xd_full = pd.concat([Xnum, df[PRED].apply(pd.to_numeric, errors="coerce")], axis=1).to_numpy()
    Xd_s2b = pd.concat([Xnum, Xpred_s2b], axis=1).to_numpy()
    Xn = Xnum.to_numpy()

    print("--- G4 as published (S2 + S2a), reproduced for comparison ---")
    report("G4  S2+S2a (train 1,070)", arm(tr_mask, Xn), arm(tr_mask, Xd_full))
    print("\n--- G4b: S2b applied. Both arms train on the SAME surviving rows (decision 2) ---")
    report("G4b S2+S2a+S2b (train 884)", arm(keep_tr, Xn), arm(keep_tr, Xd_s2b))
    print("\n--- the sample-size component, isolated: same 884 rows, UNFILTERED text ---")
    pd_s2b, pd_full = arm(keep_tr, Xd_s2b), arm(keep_tr, Xd_full)
    report("G4c 884 rows, full text", arm(keep_tr, Xn), pd_full,
           note="  <- not a gate; isolates decision 1")

    # G4b and G4c share an identical B (same rows, same numeric columns), so the difference
    # between their dAUCs IS AUC(D_s2b) - AUC(D_full). Their CIs overlap heavily, so the
    # difference must be tested directly rather than read off the two intervals.
    print("\n--- S2 is ONE fit, not fifteen: how much does the seed alone move it? ---")
    print("  (measured below, after the paired test)\n")
    print("--- does the text filter ITSELF move D? paired on the same test rows ---")
    lo, hi, se = nf.paired_group_bootstrap(pd_full[None, :], pd_s2b[None, :], yte, gte,
                                           nf.N_BOOT)
    diff = nf.fast_auc(yte, pd_s2b) - nf.fast_auc(yte, pd_full)
    ok = bool(lo > 0 or hi < 0)
    print(f"  {'D(S2b text) - D(full text)':<34} dAUC={diff:+.4f}  [{lo:+.4f}, {hi:+.4f}]  "
          f"{'EXCLUDES 0' if ok else 'INCLUDES 0'}")
    res["S2b text effect on D"] = dict(dauc=diff, ci_lo=lo, ci_hi=hi, se=se, excludes_zero=ok)

    # --- fit variance, because S2 is ONE fit where S1 averages fifteen -----------------
    # The paired bootstrap resamples TEST GROUPS; it does not resample the model fit. Under
    # S1 the A-6 aggregation averages 5 folds x 3 repeats, so fit variance is largely averaged
    # out. Under S2 there is exactly one train/test split and one CatBoost fit per arm, so the
    # point estimate carries fit noise the CI does not show. Measured here rather than asserted.
    from catboost import CatBoostClassifier

    def arm_seed(train_mask, X, seed):
        m = CatBoostClassifier(random_seed=seed, **nf.CB)
        m.fit(X[train_mask], y[train_mask])
        return m.predict_proba(X[te_mask])[:, 1]

    seeds = [nf.RANDOM_STATE + i for i in range(args.seeds)]
    spread = {}
    for name, tm, Xd in (("G4 S2+S2a", tr_mask, Xd_full),
                         ("G4b S2+S2a+S2b", keep_tr, Xd_s2b),
                         ("G4c 884 full text", keep_tr, Xd_full)):
        v = [nf.fast_auc(yte, arm_seed(tm, Xd, sd)) - nf.fast_auc(yte, arm_seed(tm, Xn, sd))
             for sd in seeds]
        v = np.array(v)
        spread[name] = dict(mean=float(v.mean()), sd=float(v.std(ddof=1)),
                            min=float(v.min()), max=float(v.max()), n_seeds=len(seeds))
        print(f"  {name:<22} over {len(seeds)} CatBoost seeds: mean {v.mean():+.4f} · "
              f"sd {v.std(ddof=1):.4f} · [{v.min():+.4f}, {v.max():+.4f}]")

    out = dict(
        generated=pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        seed_spread=spread,
        question_set_version=QUESTION_SET_VERSION, model=s3.MODEL, cutoff=S2_CUTOFF,
        n_train_s2=int(tr_mask.sum()), n_train_s2b=int(keep_tr.sum()),
        n_test=int(te_mask.sum()), s2a_dropped=int(leak.sum()),
        train_base_s2=float(y[tr_mask].mean()), train_base_s2b=float(y[keep_tr].mean()),
        test_base=float(yte.mean()),
        notes_kept=int(((~raw.is_tfopwg) & raw.lastmod.notna()
                        & (raw.lastmod < S2_CUTOFF)).sum()),
        notes_total_observer=int((~raw.is_tfopwg).sum()),
        rows_unchanged=int((tr_mask & ~changed).sum()), rows_changed=int(changed.sum()),
        rows_emptied=int(emptied.sum()), rows_rescored=int(need.sum()),
        distinct_states=len(states),
        # "this run" figures, same semantics as step3_features_*.json. A cached re-run
        # legitimately reports zero; the paid run is recorded in WORKLOG.md 2026-09-20T22:09Z
        # (203 calls, 804,981 tokens, $0.0338).
        new_calls_this_run=s3._stats["new"],
        input_tokens_this_run=s3._stats["tokens"], usd_this_run=usd,
        paid_run=dict(new_calls=203, input_tokens=804_981, usd=0.0338,
                      recorded="WORKLOG.md 2026-09-20T22:09Z"),
        arms=res,
        note=("S2b applied to the TRAINING side only, per PREREGISTRATION.md §4. Test side is "
              "the same 390 rows as A-28's G4. Rows whose S2b text is empty leave training; "
              "both arms train on the survivors. G4c isolates that sample-size component."))
    (OUT / "gate_g4_s2b_2026-09-20.json").write_text(json.dumps(out, indent=2, default=float))
    con.execute("create or replace table jev_features_obsnotes_s2b as select * from Xpred_s2b")
    con.close()

    g4b = res["G4b S2+S2a+S2b (train 884)"]
    print("\n" + "=" * 78)
    print(f"G4b VERDICT: dAUC {g4b['dauc']:+.4f}  CI [{g4b['ci_lo']:+.4f}, {g4b['ci_hi']:+.4f}]"
          f"  -> {'PASS' if g4b['excludes_zero'] and g4b['dauc'] > 0 else 'FAIL'}")
    print(f"raw -> research/data/gate_g4_s2b_2026-09-20.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
