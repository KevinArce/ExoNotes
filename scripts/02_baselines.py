"""ExoNotes Step 2 - baselines A/B/C (PLAN.md section 6 Step 2, section 7 split S1).

A - prior:      predict the training-fold base rate. The floor.
B - numeric:    CatBoost on catalogue columns. THE baseline that matters; gate G1 is B > A.
C - TF-IDF:     logistic regression on comment text. Shows whether any gain is semantic
                rather than lexical.

Split S1: GroupKFold on TIC ID, 5 folds x 3 repeats. Two planets around one star share a
host and a comment record, so a within-system split would leak.

Re-running is free and deterministic: fixed seeds, no network, CREATE OR REPLACE output.
"""
import pathlib, sys
import duckdb, numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "exonotes.duckdb"
N_SPLITS, N_REPEATS, RANDOM_STATE = 5, 3, 20260919

NUMERIC = ["pl_orbper", "pl_trandep", "pl_trandurh", "pl_rade",
           "st_tmag", "st_teff", "st_rad", "st_logg"]


def repeated_group_kfold(groups, n_splits, n_repeats, seed):
    """GroupKFold has no shuffle/repeats; permute the group labels per repeat instead."""
    uniq = np.unique(groups)
    for r in range(n_repeats):
        rng = np.random.default_rng(seed + r)
        perm = rng.permutation(len(uniq))
        remap = dict(zip(uniq, perm))
        shuffled = np.array([remap[g] for g in groups])
        for tr, te in GroupKFold(n_splits=n_splits).split(shuffled, groups=shuffled):
            yield r, tr, te


def main() -> int:
    con = duckdb.connect(str(DB), read_only=True)
    df = con.execute("select * from analysis_set").df()
    con.close()

    y = df["y"].astype(int).to_numpy()
    groups = df["tic_id"].to_numpy()
    X_num = df[NUMERIC].apply(pd.to_numeric, errors="coerce")
    text = df["comment"].astype(str).to_numpy()

    print(f"analysis set: {len(df)} rows, {len(np.unique(groups))} groups (TIC), "
          f"base rate {y.mean():.4f}")
    print(f"split S1: GroupKFold({N_SPLITS}) x {N_REPEATS} repeats on TIC ID\n")

    from catboost import CatBoostClassifier
    rows = []
    for r, tr, te in repeated_group_kfold(groups, N_SPLITS, N_REPEATS, RANDOM_STATE):
        preds = {}

        # A - prior
        preds["A_prior"] = np.full(len(te), y[tr].mean())

        # B - numeric only
        clf = CatBoostClassifier(iterations=500, depth=4, learning_rate=0.05,
                                 loss_function="Logloss", random_seed=RANDOM_STATE + r,
                                 verbose=0, allow_writing_files=False)
        clf.fit(X_num.iloc[tr], y[tr])
        preds["B_numeric"] = clf.predict_proba(X_num.iloc[te])[:, 1]

        # C - TF-IDF on comment text
        tfidf = make_pipeline(
            TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=2,
                            strip_accents="unicode", lowercase=True),
            LogisticRegression(max_iter=2000, C=1.0))
        tfidf.fit(text[tr], y[tr])
        preds["C_tfidf"] = tfidf.predict_proba(text[te])[:, 1]

        for name, p in preds.items():
            auc = np.nan if len(np.unique(y[te])) < 2 else roc_auc_score(y[te], p)
            rows.append({"model": name, "repeat": r, "auc": auc,
                         "brier": brier_score_loss(y[te], p), "n_test": len(te)})

    res = pd.DataFrame(rows)
    summary = (res.groupby("model")
                  .agg(auc_mean=("auc", "mean"), auc_std=("auc", "std"),
                       brier_mean=("brier", "mean"), brier_std=("brier", "std"),
                       n_folds=("auc", "size"))
                  .reset_index().sort_values("auc_mean", ascending=False))

    print(summary.to_string(index=False, float_format=lambda v: f"{v:.4f}"))

    a = summary.loc[summary.model == "A_prior", "auc_mean"].iloc[0]
    b = summary.loc[summary.model == "B_numeric", "auc_mean"].iloc[0]
    ab = summary.loc[summary.model == "A_prior", "brier_mean"].iloc[0]
    bb = summary.loc[summary.model == "B_numeric", "brier_mean"].iloc[0]
    passed = (b > a) and (bb < ab)
    print(f"\nGATE G1 (B must beat A): AUC {b:.4f} vs {a:.4f} | "
          f"Brier {bb:.4f} vs {ab:.4f} -> {'PASS' if passed else 'FAIL'}")

    con = duckdb.connect(str(DB))
    con.execute("CREATE OR REPLACE TABLE baseline_results AS SELECT * FROM res")
    con.execute("CREATE OR REPLACE TABLE baseline_summary AS SELECT * FROM summary")
    con.close()
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
