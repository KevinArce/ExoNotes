"""Gates G2, G4, G5, G6 and the reference arms (TASK C; PREREGISTRATION.md §6, §7).

Everything statistical is IMPORTED from scripts/026_noise_floor.py -- the A-6 aggregation
(pool OOF within a repeat, score each repeat, average), the paired group bootstrap (same
resample for both models), the CatBoost configuration and the NUMERIC column list -- so the
G2 arm and the noise-floor reference arm cannot drift apart. Do not re-implement them here.

Arms (PREREGISTRATION.md §3, A-1, A-7):
  A       prior only
  B       CatBoost on numeric covariates                      <- the comparator
  B+N     B plus k pure-noise columns                         <- A-1 dilution reference
  B+meta  B plus note count, total chars, author one-hot      <- A-7; no API calls
  C       TF-IDF + logistic on raw text                       <- leakage upper bound only
  D       B plus TIER_PREDICTIVE Jev features                 <- THE HEADLINE
  E       B plus all Jev features, both tiers                 <- contaminated upper bound

Gates:
  G2  D - B under S1, paired bootstrap 95% CI excluding zero
  G4  the G2 gain on TIER_PREDICTIVE only under S2 (with the S2a group-leak fix)
  G5  the G2 gain on the §11.4 leakage-stripped arm, plus the without-L6 sensitivity arm
  G6  missingness ablation: re-fit B and D with explicit missingness indicators

G3 lives in scripts/036_gate_g3_stability.py because it needs API calls.

Run:  .venv/bin/python scripts/035_gates_g2_g6.py
Idempotent: yes. No network, no API calls, fixed seeds, CREATE OR REPLACE output.
"""
import importlib.util
import json
import pathlib
import sys
import warnings

import duckdb
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "exonotes.duckdb"
OUT = ROOT / "research" / "data"

_spec = importlib.util.spec_from_file_location("nf", ROOT / "scripts" / "026_noise_floor.py")
nf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nf)

sys.path.insert(0, str(ROOT / "src"))
from exonotes.leakage import OBSNOTES_PATTERNS  # noqa: E402
from exonotes.questions import (  # noqa: E402
    QUESTION_SET_VERSION, TIER_LABEL_ECHO, TIER_PREDICTIVE)

NUMERIC, N_BOOT = nf.NUMERIC, nf.N_BOOT
PRED = list(TIER_PREDICTIVE)
ALLQ = PRED + list(TIER_LABEL_ECHO)
S2_CUTOFF = "2021-10-28"          # PREREGISTRATION.md §4, fixed before any result


def fit(X, y, groups):
    return nf.oof_by_repeat(X.reset_index(drop=True), y, groups)


def compare(PB, PD, y, groups, label, note=""):
    b, d = nf.score(PB, y), nf.score(PD, y)
    lo, hi, se = nf.paired_group_bootstrap(PB, PD, y, groups, N_BOOT)
    verdict = "EXCLUDES 0" if (lo > 0 or hi < 0) else "includes 0"
    print(f"  {label:<26} B={b:.4f}  X={d:.4f}  dAUC={d - b:+.4f}  "
          f"[{lo:+.4f}, {hi:+.4f}]  {verdict}{note}")
    return dict(label=label, auc_B=b, auc_X=d, dauc=d - b, ci_lo=lo, ci_hi=hi, se=se,
                excludes_zero=bool(lo > 0 or hi < 0))


def meta_frame(df):
    """A-7's B+meta: note count, total characters, author one-hot. Zero API calls."""
    con = duckdb.connect(str(DB), read_only=True)
    au = con.execute("""
        select tic_id, username, count(*) n from obsnotes_raw
        where groupname is null group by 1,2""").df()
    con.close()
    top = au.groupby("username")["n"].sum().sort_values(ascending=False).head(8).index.tolist()
    wide = (au[au.username.isin(top)]
            .pivot_table(index="tic_id", columns="username", values="n", fill_value=0))
    wide.columns = [f"auth_{c}" for c in wide.columns]
    m = df[["tic_id", "n_notes_obs", "n_chars", "n_authors"]].merge(
        wide, left_on="tic_id", right_index=True, how="left").fillna(0)
    return m.drop(columns=["tic_id"]).reset_index(drop=True)


def main() -> int:
    con = duckdb.connect(str(DB))
    have = {r[0] for r in con.execute(
        "select table_name from information_schema.tables where table_schema='main'").fetchall()}
    if "jev_features_obsnotes" not in have:
        print("ABORT: jev_features_obsnotes does not exist. Run Step 3 first:\n"
              "  .venv/bin/python scripts/034_step3_features.py", file=sys.stderr)
        return 2

    df = con.execute("""
        select a.*, f.* exclude (tic_id, toi)
        from analysis_set_obsnotes a
        join jev_features_obsnotes f on f.toi = cast(a.toi as varchar)
        order by a.toi""").df()
    con.close()
    df = df.loc[:, ~df.columns.duplicated()].reset_index(drop=True)

    y = df["y"].astype(int).to_numpy()
    groups = df["tic_id"].to_numpy()
    Xnum = df[NUMERIC].apply(pd.to_numeric, errors="coerce").reset_index(drop=True)
    Xpred = df[PRED].apply(pd.to_numeric, errors="coerce").reset_index(drop=True)
    Xall = df[ALLQ].apply(pd.to_numeric, errors="coerce").reset_index(drop=True)

    print(f"question set {QUESTION_SET_VERSION} · n={len(df):,} · TIC={df.tic_id.nunique():,} "
          f"· base={y.mean():.4f}")
    print(f"S1: GroupKFold({nf.N_SPLITS}) x {nf.N_REPEATS} repeats · paired bootstrap "
          f"{N_BOOT:,} over TIC groups · A-6 aggregation\n")

    res = {}
    PB = fit(Xnum, y, groups)
    print(f"B  (numeric, {len(NUMERIC)} features)        AUC {nf.score(PB, y):.4f}\n")

    # ---- reference arms --------------------------------------------------------------
    print("--- reference arms (A-1 dilution floor, A-7 metadata control) ---")
    rng = np.random.default_rng(nf.RANDOM_STATE)
    Xn = pd.concat([Xnum, pd.DataFrame(
        rng.normal(size=(len(df), len(PRED))),
        columns=[f"noise_{i}" for i in range(len(PRED))])], axis=1)
    res["B+N"] = compare(PB, fit(Xn, y, groups), y, groups, "B+N (dilution floor)")
    Xm = pd.concat([Xnum, meta_frame(df)], axis=1)
    PM = fit(Xm, y, groups)
    res["B+meta"] = compare(PB, PM, y, groups, "B+meta (A-7 control)")

    # ---- G2: the headline ------------------------------------------------------------
    print("\n--- G2: D vs B, TIER_PREDICTIVE only (THE HEADLINE) ---")
    PD = fit(pd.concat([Xnum, Xpred], axis=1), y, groups)
    res["G2"] = compare(PB, PD, y, groups, "D - B  (G2)")
    print("\n--- D vs B+meta: is the gain about prose, or about how much follow-up happened? ---")
    res["D_vs_meta"] = compare(PM, PD, y, groups, "D - B+meta")
    print("\n--- E: all questions, LEAKAGE-CONTAMINATED upper bound (never the headline) ---")
    res["E"] = compare(PB, fit(pd.concat([Xnum, Xall], axis=1), y, groups), y, groups,
                       "E - B  (contaminated)")

    # ---- C: TF-IDF leakage upper bound ------------------------------------------------
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    PC = np.zeros((nf.N_REPEATS, len(y)))
    for r, tr, te in nf.repeated_group_kfold(groups, nf.N_SPLITS, nf.N_REPEATS, nf.RANDOM_STATE):
        pipe = make_pipeline(TfidfVectorizer(min_df=3, max_features=50_000, sublinear_tf=True),
                             LogisticRegression(max_iter=2000, C=1.0))
        pipe.fit(df["notes"].iloc[tr], y[tr])
        PC[r, te] = pipe.predict_proba(df["notes"].iloc[te])[:, 1]
    res["C"] = {"auc": nf.score(PC, y)}
    print(f"\n--- C: TF-IDF + logistic on raw text = LEAKAGE, not evidence ---")
    print(f"  C AUC {nf.score(PC, y):.4f}")

    # ---- G5: leakage-stripped arms ----------------------------------------------------
    print("\n--- G5: leakage-stripped arm (§11.4) ---")
    def leaky(txt, pats):
        s = (txt or "").strip()
        return any(rx.search(s) for rx in pats.values())
    no6 = {k: v for k, v in OBSNOTES_PATTERNS.items() if k != "L6_archive_provenance"}
    for name, pats in [("G5 (registered, with L6)", OBSNOTES_PATTERNS),
                       ("G5 sensitivity (no L6)", no6)]:
        keep = ~df["notes"].map(lambda t: leaky(t, pats)).to_numpy()
        sub = df[keep].reset_index(drop=True)
        yy, gg = sub["y"].astype(int).to_numpy(), sub["tic_id"].to_numpy()
        xb = sub[NUMERIC].apply(pd.to_numeric, errors="coerce")
        xd = pd.concat([xb, sub[PRED].apply(pd.to_numeric, errors="coerce")], axis=1)
        res[name] = compare(fit(xb, yy, gg), fit(xd, yy, gg), yy, gg, name,
                            note=f"  n={len(sub)} base={yy.mean():.3f}")

    # ---- G6: missingness ablation -----------------------------------------------------
    print("\n--- G6: missingness ablation (numeric missingness is label-correlated) ---")
    miss = Xnum.isna().astype(int)
    miss.columns = [f"miss_{c}" for c in NUMERIC]
    xb6 = pd.concat([Xnum, miss], axis=1)
    xd6 = pd.concat([Xnum, miss, Xpred], axis=1)
    res["G6"] = compare(fit(xb6, y, groups), fit(xd6, y, groups), y, groups,
                        "D - B  (+missingness)")

    # ---- G4: S2 temporal, with the S2a group-leak fix ---------------------------------
    print(f"\n--- G4: S2 temporal split at {S2_CUTOFF} (S2a group-leak fix applied) ---")
    d = pd.to_datetime(df["date_toi_alerted"], errors="coerce")
    tr_mask = (d < S2_CUTOFF).to_numpy()
    te_mask = (d >= S2_CUTOFF).to_numpy()
    tr_tic = set(df.loc[tr_mask, "tic_id"])
    leak = te_mask & df["tic_id"].isin(tr_tic).to_numpy()
    te_mask = te_mask & ~leak
    print(f"  train {tr_mask.sum()} · test {te_mask.sum()} "
          f"({100 * te_mask.sum() / len(df):.1f}%) · S2a dropped {leak.sum()} leaked test rows")
    print(f"  train base {y[tr_mask].mean():.4f} · test base {y[te_mask].mean():.4f} "
          f"(base-rate shift is expected; an S2 AUC is not an S1 AUC)")
    from catboost import CatBoostClassifier
    def s2(X):
        m = CatBoostClassifier(random_seed=nf.RANDOM_STATE, **nf.CB)
        m.fit(X[tr_mask], y[tr_mask])
        return m.predict_proba(X[te_mask])[:, 1]
    pb2 = s2(Xnum.to_numpy())
    pd2 = s2(pd.concat([Xnum, Xpred], axis=1).to_numpy())
    ab, ad = nf.fast_auc(y[te_mask], pb2), nf.fast_auc(y[te_mask], pd2)
    # Paired bootstrap over test-set TIC groups.
    gte = df.loc[te_mask, "tic_id"].to_numpy()
    lo, hi, se = nf.paired_group_bootstrap(pb2[None, :], pd2[None, :], y[te_mask], gte, N_BOOT)
    print(f"  S2  B={ab:.4f}  D={ad:.4f}  dAUC={ad - ab:+.4f}  [{lo:+.4f}, {hi:+.4f}]  "
          f"{'EXCLUDES 0' if (lo > 0 or hi < 0) else 'includes 0'}")
    res["G4"] = dict(n_train=int(tr_mask.sum()), n_test=int(te_mask.sum()),
                     s2a_dropped=int(leak.sum()), train_base=float(y[tr_mask].mean()),
                     test_base=float(y[te_mask].mean()), auc_B=ab, auc_D=ad,
                     dauc=ad - ab, ci_lo=lo, ci_hi=hi, se=se,
                     excludes_zero=bool(lo > 0 or hi < 0),
                     note="S2b (note-level Lastmod filter) NOT applied; see WORKLOG")

    (OUT / "gates_g2_g6_2026-09-20.json").write_text(json.dumps(res, indent=2, default=float))
    print(f"\nraw -> research/data/gates_g2_g6_2026-09-20.json")

    g2 = res["G2"]
    print("\n" + "=" * 78)
    print(f"G2 VERDICT: dAUC {g2['dauc']:+.4f}  CI [{g2['ci_lo']:+.4f}, {g2['ci_hi']:+.4f}]  "
          f"-> {'PASS' if g2['excludes_zero'] and g2['dauc'] > 0 else 'FAIL'}")
    print(f"  dilution floor (B+N) {res['B+N']['dauc']:+.4f} · "
          f"B+meta {res['B+meta']['dauc']:+.4f} · D-vs-B+meta {res['D_vs_meta']['dauc']:+.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
