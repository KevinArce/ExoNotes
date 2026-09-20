"""Gate G2's noise floor — the B+N dilution control and the minimum detectable effect.

PREREGISTRATION.md §6 asks whether model D (numeric + Jev features) beats model B (numeric
only) on ΔAUC with a paired group bootstrap CI excluding zero. That test has no zero point.

**Adding k uninformative columns to a fixed-capacity CatBoost costs AUC.** Measured here, at
the projected obsnotes scale, the cost of eight pure-Gaussian columns is about -0.011 AUC —
roughly four times the bootstrap SE of the ΔAUC statistic itself. So:

  * a reported ΔAUC of 0.000 is NOT a null. It is ~+0.011 of real signal cancelling dilution.
  * a reported ΔAUC of +0.008 with a CI excluding zero understates the effect by the same.

Without this arm, PREREGISTRATION.md §8's decision table maps a manufactured artifact onto
"Stop. Write the negative result." This script produces the reference the table needs.

It answers three questions, none of which cost a single API call:

  1. **B+N** — what does adding k *known-worthless* columns do to B? (the dilution floor)
  2. **MDE** — what is the SE of the paired-group-bootstrap ΔAUC, hence the smallest effect
     this study can detect at 80% power?
  3. **Oracle** — how accurate must a text feature be, in its own univariate AUC against the
     label, before G2 can see it? This is the bar TASK B's question set has to clear.

It also fixes something PREREGISTRATION.md §6 left undefined: **how ΔAUC is aggregated across
the three S1 repeats.** Here, and in Step 3: pool out-of-fold predictions within a repeat,
score each repeat, average the repeat AUCs; bootstrap resamples TIC groups and recomputes that
same average, using the SAME resample for both models (paired).

Run:  .venv/bin/python scripts/026_noise_floor.py [--groups N] [--k K] [--seeds S]
Idempotent: yes. No network, no API calls, fixed seeds, CREATE OR REPLACE output.

--groups N subsamples to N TIC groups to match a projected corpus size. The obsnotes corpus is
projected at ~1,715 TIC (PREREGISTRATION.md §1.4), so that is the default. Pass --groups 0 to
use every row. **After TASK A this script must be re-run on the real obsnotes row set**, because
the dilution penalty is a function of n, and a different row set is a different pipeline.
"""
import argparse
import json
import pathlib
import sys
import time
import warnings

import duckdb
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.model_selection import GroupKFold

warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "exonotes.duckdb"
OUT = ROOT / "research" / "data"

# S1 as registered (PREREGISTRATION.md §4): GroupKFold on TIC, 5 folds x 3 repeats.
N_SPLITS, N_REPEATS, RANDOM_STATE = 5, 3, 20260919
N_BOOT = 10_000          # PREREGISTRATION.md §6 G2 specifies 10,000 resamples over TIC groups
Z80 = 2.802              # z(0.975) + z(0.80): two-sided 95% test at 80% power

NUMERIC = ["pl_orbper", "pl_trandep", "pl_trandurh", "pl_rade",
           "st_tmag", "st_teff", "st_rad", "st_logg"]

# CatBoost exactly as scripts/02_baselines.py fits baseline B. Do not "improve" these here:
# the point of this arm is to measure THIS configuration's dilution cost, not a better one.
CB = dict(iterations=500, depth=4, learning_rate=0.05, loss_function="Logloss",
          verbose=0, allow_writing_files=False)


def fast_auc(y: np.ndarray, p: np.ndarray) -> float:
    """Rank-based AUC. `rankdata` averages ties, which matters: Jev returns two decimals."""
    n1 = int(y.sum())
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return np.nan
    r = rankdata(p)
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def repeated_group_kfold(groups, n_splits, n_repeats, seed):
    """Same construction as scripts/02_baselines.py — GroupKFold has no shuffle or repeats."""
    uniq = np.unique(groups)
    for r in range(n_repeats):
        rng = np.random.default_rng(seed + r)
        remap = dict(zip(uniq, rng.permutation(len(uniq))))
        shuffled = np.array([remap[g] for g in groups])
        for tr, te in GroupKFold(n_splits=n_splits).split(shuffled, groups=shuffled):
            yield r, tr, te


def oof_by_repeat(X, y, groups):
    """Pooled out-of-fold predictions, one n-vector per repeat. Shape (n_repeats, n)."""
    from catboost import CatBoostClassifier
    P = np.zeros((N_REPEATS, len(y)))
    for r, tr, te in repeated_group_kfold(groups, N_SPLITS, N_REPEATS, RANDOM_STATE):
        clf = CatBoostClassifier(random_seed=RANDOM_STATE + r, **CB)
        clf.fit(X.iloc[tr], y[tr])
        P[r, te] = clf.predict_proba(X.iloc[te])[:, 1]
    return P


def score(P, y):
    """The registered aggregation: mean over repeats of each repeat's pooled-OOF AUC."""
    return float(np.mean([fast_auc(y, P[r]) for r in range(P.shape[0])]))


def paired_group_bootstrap(PB, PD, y, groups, n_boot=N_BOOT, seed=RANDOM_STATE):
    """ΔAUC = score(D) - score(B), resampling TIC groups, SAME resample for both models.

    Pairing is not optional. An unpaired bootstrap would inflate the CI by the between-model
    covariance, which is large here because D and B share every numeric column.
    """
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    idx = {u: np.flatnonzero(groups == u) for u in uniq}
    members = [idx[u] for u in uniq]
    out = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, len(uniq), len(uniq))
        ii = np.concatenate([members[j] for j in pick])
        yy = y[ii]
        if yy.min() == yy.max():
            out[b] = np.nan
            continue
        out[b] = np.mean([fast_auc(yy, PD[r][ii]) - fast_auc(yy, PB[r][ii])
                          for r in range(PB.shape[0])])
    lo, hi = np.nanpercentile(out, [2.5, 97.5])
    return float(lo), float(hi), float(np.nanstd(out))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--groups", type=int, default=1715,
                    help="subsample to N TIC groups (0 = all). Default 1,715 = projected obsnotes scale.")
    ap.add_argument("--k", type=int, default=8,
                    help="number of noise columns; set to the final Jev feature count.")
    ap.add_argument("--seeds", type=int, default=5, help="noise-draw seeds to average over.")
    ap.add_argument("--boot", type=int, default=N_BOOT)
    args = ap.parse_args()

    con = duckdb.connect(str(DB), read_only=True)
    df = con.execute("select * from analysis_set").df()
    con.close()

    if args.groups and args.groups < df.tic_id.nunique():
        rng = np.random.default_rng(RANDOM_STATE)
        keep = set(rng.choice(df.tic_id.unique(), args.groups, replace=False))
        df = df[df.tic_id.isin(keep)].reset_index(drop=True)

    y = df["y"].astype(int).to_numpy()
    groups = df["tic_id"].to_numpy()
    X = df[NUMERIC].apply(pd.to_numeric, errors="coerce").reset_index(drop=True)

    print(f"rows {len(df)} · TIC groups {df.tic_id.nunique()} · base rate {y.mean():.4f}")
    print(f"S1: GroupKFold({N_SPLITS}) x {N_REPEATS} repeats · bootstrap {args.boot:,} over groups\n")

    t0 = time.time()
    PB = oof_by_repeat(X, y, groups)
    auc_b = score(PB, y)
    print(f"B  (numeric only, {len(NUMERIC)} features)          AUC {auc_b:.4f}\n")

    # ---- 1. the dilution floor -------------------------------------------------------------
    print(f"--- B+N: {args.k} PURE-NOISE columns, {args.seeds} seeds ---")
    print(f"{'seed':>5} {'AUC':>8} {'dAUC':>9}  {'paired 95% CI':>22} {'SE':>8}")
    floor = []
    for s in range(args.seeds):
        rs = np.random.default_rng(9_000 + s)
        Xn = X.copy()
        for j in range(args.k):
            Xn[f"noise_{j}"] = rs.normal(size=len(df))
        PN = oof_by_repeat(Xn, y, groups)
        d = score(PN, y) - auc_b
        lo, hi, se = paired_group_bootstrap(PB, PN, y, groups, args.boot)
        floor.append(dict(seed=s, auc=score(PN, y), dauc=d, ci_lo=lo, ci_hi=hi, se=se))
        print(f"{s:>5} {score(PN, y):>8.4f} {d:>+9.4f}  [{lo:+.4f}, {hi:+.4f}] {se:>8.4f}")

    delta_floor = float(np.mean([f["dauc"] for f in floor]))
    se_mean = float(np.mean([f["se"] for f in floor]))
    mde = Z80 * se_mean
    print(f"\n  DILUTION FLOOR  delta_N = {delta_floor:+.4f}   (mean of {args.seeds} seeds)")
    print(f"  BOOTSTRAP SE    of dAUC = {se_mean:.4f}")
    print(f"  MDE (80% power) = {Z80} x SE = {mde:+.4f} of observed dAUC")
    print(f"  => a real effect must exceed {mde:.4f} - ({delta_floor:.4f}) = "
          f"{mde - delta_floor:.4f} of TRUE signal to be both visible and unambiguous.\n")

    # ---- 2. how good must a text feature be? ------------------------------------------------
    print("--- graded oracle: one text feature agreeing with truth with probability q ---")
    print(f"{'q':>5} {'feat AUC':>9} {'D AUC':>8} {'dAUC':>9}  {'paired 95% CI':>22} {'detect':>7}")
    oracle = []
    for q in (0.55, 0.60, 0.65, 0.70, 0.75, 0.80):
        rs = np.random.default_rng(4_000 + int(q * 100))
        f = np.where(rs.random(len(df)) < q, y, 1 - y).astype(float)
        f = f * 0.8 + rs.normal(0, 0.1, len(df))     # soften into a probability-like column
        Xo = X.copy()
        Xo["text_oracle"] = f
        PO = oof_by_repeat(Xo, y, groups)
        d = score(PO, y) - auc_b
        lo, hi, _ = paired_group_bootstrap(PB, PO, y, groups, args.boot)
        fa = fast_auc(y, f)
        oracle.append(dict(q=q, feature_auc=fa, auc=score(PO, y), dauc=d, ci_lo=lo, ci_hi=hi))
        print(f"{q:>5.2f} {fa:>9.3f} {score(PO, y):>8.4f} {d:>+9.4f}  "
              f"[{lo:+.4f}, {hi:+.4f}] {'YES' if lo > 0 else 'no':>7}")

    detect = [o for o in oracle if o["ci_lo"] > 0]
    bar = min((o["feature_auc"] for o in detect), default=float("nan"))
    print(f"\n  A single Jev feature needs univariate AUC >= ~{bar:.2f} against the label "
          f"before G2 can see it.")
    print(f"  That is the bar the TASK B question set has to clear. ({time.time() - t0:.0f}s)\n")

    # ---- persist ----------------------------------------------------------------------------
    res = dict(
        generated=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        corpus="Comments analysis_set, subsampled to obsnotes-projected scale"
               if args.groups else "Comments analysis_set, full",
        n_rows=int(len(df)), n_groups=int(df.tic_id.nunique()), base_rate=float(y.mean()),
        k_noise=args.k, n_seeds=args.seeds, n_boot=args.boot,
        auc_B=auc_b, dilution_floor=delta_floor, bootstrap_se=se_mean, mde_80pct=mde,
        detectable_feature_auc=None if np.isnan(bar) else float(bar),
        noise_arms=floor, oracle=oracle,
        catboost=CB, split=dict(n_splits=N_SPLITS, n_repeats=N_REPEATS, seed=RANDOM_STATE))

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"noise_floor_{time.strftime('%Y-%m-%d')}.json"
    path.write_text(json.dumps(res, indent=2))

    con = duckdb.connect(str(DB))
    con.execute("CREATE OR REPLACE TABLE noise_floor AS SELECT * FROM (SELECT ?::JSON AS result)",
                [json.dumps(res)])
    con.close()
    print(f"raw -> {path.relative_to(ROOT)}  ·  duckdb::noise_floor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
