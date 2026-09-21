"""ExoNotes Kepler step 2 - zero-cost baselines, dilution floor and MDE, before any model call.

The Kepler analogue of scripts/026_noise_floor.py (A-1/A-2) plus the zero-cost arms of
scripts/035_gates_g2_g6.py, run BEFORE any Kepler model call so the pre-registration
(PREREGISTRATION.md section 11.10 / A-40) can state an MDE measured at the realised n.

S1 is imported from 026 UNCHANGED -- GroupKFold 5 x 3 repeats, the same CatBoost settings, the
A-6 aggregation, the paired group bootstrap -- with `kepid` as the group. Arms:

    B           the 8 covariates mirroring TESS B                          (G1 analogue)
    B+meta      fpwg: B + comment length (one comment per KOI, no author field)
                cfop: A-7 exactly -- note count, total chars, author count, top-8 author one-hot
    C           TF-IDF + logistic on the comment, 035's exact settings
    B+N         B + k pure-noise columns, averaged over seeds    -> dilution floor, SE, MDE
    oracle      B + one synthetic text feature of graded accuracy -> the feature-AUC bar
    B+verdict   B + one-hot `fpwg_status`: DIAGNOSTIC ONLY. The ceiling on what the text can
                add by restating the FPWG's own call. `fpwg_status` is never a candidate
                feature, and this arm is never a comparator for a gate. fpwg only: CFOP
                notes have no verdict source.

`--corpus` picks the row set: `fpwg` (kepler_corpus, the withdrawn FPWG definition -- kept so
its step 2 stays reproducible) or `cfop` (kepler_cfop_corpus, the transfer test).

k defaults to 7 (the TESS predictive count) and is PROVISIONAL: the MDE is a function of k and
must be re-run at whatever k the Kepler question set freezes at.

Run:  .venv/bin/python scripts/044_kepler_step2.py --corpus {fpwg,cfop} [--k K] [--seeds S]
Idempotent: yes. No network, no API calls, fixed seeds, CREATE OR REPLACE output.
"""
import argparse, importlib.util, json, pathlib, sys, time, warnings

import duckdb, numpy as np, pandas as pd

warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "kepler.duckdb"
OUT = ROOT / "research" / "data"

_spec = importlib.util.spec_from_file_location("nf", ROOT / "scripts" / "026_noise_floor.py")
nf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nf)

NUMERIC = ["koi_period", "koi_depth", "koi_duration", "koi_prad",
           "koi_kepmag", "koi_steff", "koi_srad", "koi_slogg"]
CORPORA = {"fpwg": ("kepler_corpus", "kepler_step2", "kepler_step2"),
           "cfop": ("kepler_cfop_corpus", "kepler_cfop_step2", "kepler_cfop_step2")}


def meta_frame(df, corpus):
    """B+meta's extra columns. cfop copies 035's A-7 `meta_frame` construction."""
    if corpus == "fpwg":
        return pd.DataFrame({"text_len": df["text_len"].to_numpy()})
    with duckdb.connect(str(DB), read_only=True) as con:
        au = con.execute("select host, username, count(*) n from kepler_cfop_notes "
                         "group by 1, 2").df()
    top = au.groupby("username")["n"].sum().sort_values(ascending=False).head(8).index.tolist()
    wide = (au[au.username.isin(top)]
            .pivot_table(index="host", columns="username", values="n", fill_value=0))
    wide.columns = [f"auth_{c}" for c in wide.columns]
    m = df[["host", "n_notes", "n_chars", "n_authors"]].merge(
        wide, left_on="host", right_index=True, how="left").fillna(0)
    return m.drop(columns=["host"]).reset_index(drop=True)


def compare(PB, PX, y, groups, label, n_boot):
    b, x = nf.score(PB, y), nf.score(PX, y)
    lo, hi, se = nf.paired_group_bootstrap(PB, PX, y, groups, n_boot)
    print(f"  {label:<24} B={b:.4f}  X={x:.4f}  dAUC={x - b:+.4f}  [{lo:+.4f}, {hi:+.4f}]  "
          f"{'EXCLUDES 0' if (lo > 0 or hi < 0) else 'includes 0'}")
    return dict(label=label, auc_B=b, auc_X=x, dauc=x - b, ci_lo=lo, ci_hi=hi, se=se)


def auc_ci(P, y, groups, n_boot, seed=nf.RANDOM_STATE):
    """Group-bootstrap CI on a single arm's A-6 AUC (G1's form)."""
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    members = [np.flatnonzero(groups == u) for u in uniq]
    out = np.empty(n_boot)
    for b in range(n_boot):
        ii = np.concatenate([members[j] for j in rng.integers(0, len(uniq), len(uniq))])
        out[b] = np.mean([nf.fast_auc(y[ii], P[r][ii]) for r in range(P.shape[0])])
    lo, hi = np.nanpercentile(out, [2.5, 97.5])
    return float(lo), float(hi)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=CORPORA, default="fpwg")
    ap.add_argument("--k", type=int, default=7, help="noise columns; set to the frozen Kepler k")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--boot", type=int, default=nf.N_BOOT)
    a = ap.parse_args()

    table, out_tbl, out_stem = CORPORA[a.corpus]
    with duckdb.connect(str(DB), read_only=True) as con:
        df = con.execute(f"select * from {table} order by kepoi_name").df()
    y = df["y"].astype(int).to_numpy()
    groups = df["kepid"].to_numpy()
    X = df[NUMERIC].apply(pd.to_numeric, errors="coerce").reset_index(drop=True)
    print(f"{table} n={len(df):,} · kepid groups={df.kepid.nunique():,} · "
          f"base={y.mean():.4f} · positives={int(y.sum())}")
    print(f"S1: GroupKFold({nf.N_SPLITS}) x {nf.N_REPEATS} · bootstrap {a.boot:,} over kepid\n")
    t0 = time.time()
    res = {}

    PB = nf.oof_by_repeat(X, y, groups)
    auc_b = nf.score(PB, y)
    lo, hi = auc_ci(PB, y, groups, a.boot)
    res["B"] = dict(auc=auc_b, ci_lo=lo, ci_hi=hi)
    print(f"B  (numeric, {len(NUMERIC)} features)   AUC {auc_b:.4f}  [{lo:.4f}, {hi:.4f}]  "
          f"G1-analogue (>= 0.85, CI > 0.5): {'PASS' if auc_b >= 0.85 and lo > 0.5 else 'FAIL'}\n")

    print("--- zero-cost comparators ---")
    Xm = pd.concat([X, meta_frame(df, a.corpus)], axis=1)
    res["B+meta"] = compare(PB, nf.oof_by_repeat(Xm, y, groups), y, groups,
                            f"B+meta ({Xm.shape[1] - X.shape[1]} cols)", a.boot)

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    PC = np.zeros((nf.N_REPEATS, len(y)))
    for r, tr, te in nf.repeated_group_kfold(groups, nf.N_SPLITS, nf.N_REPEATS, nf.RANDOM_STATE):
        pipe = make_pipeline(TfidfVectorizer(min_df=3, max_features=50_000, sublinear_tf=True),
                             LogisticRegression(max_iter=2000, C=1.0))
        pipe.fit(df["text"].iloc[tr], y[tr])
        PC[r, te] = pipe.predict_proba(df["text"].iloc[te])[:, 1]
    lo, hi = auc_ci(PC, y, groups, a.boot)
    res["C"] = dict(auc=nf.score(PC, y), ci_lo=lo, ci_hi=hi)
    print(f"  C  TF-IDF + logistic, text only   AUC {res['C']['auc']:.4f}  [{lo:.4f}, {hi:.4f}]")

    if a.corpus == "fpwg":
        print("\n--- DIAGNOSTIC: B+verdict (never a feature, never a gate comparator) ---")
        Xv = pd.concat([X, pd.get_dummies(df["fpwg_status"], prefix="v", dtype=float)], axis=1)
        res["B+verdict"] = compare(PB, nf.oof_by_repeat(Xv, y, groups), y, groups,
                                   "B+verdict (echo ceiling)", a.boot)

    print(f"\n--- B+N: {a.k} pure-noise columns x {a.seeds} seeds -> dilution floor and MDE ---")
    floor = []
    for s in range(a.seeds):
        rs = np.random.default_rng(9_000 + s)
        Xn = X.copy()
        for j in range(a.k):
            Xn[f"noise_{j}"] = rs.normal(size=len(df))
        floor.append(compare(PB, nf.oof_by_repeat(Xn, y, groups), y, groups,
                             f"B+N seed {s}", a.boot))
    delta_floor = float(np.mean([f["dauc"] for f in floor]))
    se = float(np.mean([f["se"] for f in floor]))
    mde = nf.Z80 * se
    print(f"\n  DILUTION FLOOR {delta_floor:+.4f} · bootstrap SE {se:.4f} · "
          f"MDE(80%) {mde:+.4f} · true signal needed {mde - delta_floor:.4f}")

    print("\n--- graded oracle: one text feature agreeing with truth w.p. q ---")
    oracle = []
    for q in (0.55, 0.60, 0.65, 0.70, 0.75, 0.80):
        rs = np.random.default_rng(4_000 + int(q * 100))
        f = np.where(rs.random(len(df)) < q, y, 1 - y).astype(float)
        f = f * 0.8 + rs.normal(0, 0.1, len(df))
        o = compare(PB, nf.oof_by_repeat(X.assign(text_oracle=f), y, groups), y, groups,
                    f"oracle q={q:.2f} fAUC={nf.fast_auc(y, f):.3f}", a.boot)
        oracle.append(dict(q=q, feature_auc=nf.fast_auc(y, f), **o))
    bar = min((o["feature_auc"] for o in oracle if o["ci_lo"] > 0), default=float("nan"))
    print(f"\n  a single feature needs univariate AUC >= ~{bar:.2f} for G2 to see it "
          f"({time.time() - t0:.0f}s)")

    res.update(dict(
        generated=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        corpus=f"{table} (WORKLOG 2026-09-21 corpus definition)",
        n_rows=int(len(df)), n_groups=int(df.kepid.nunique()), n_pos=int(y.sum()),
        base_rate=float(y.mean()), k_noise=a.k, n_seeds=a.seeds, n_boot=a.boot,
        dilution_floor=delta_floor, bootstrap_se=se, mde_80pct=mde,
        detectable_feature_auc=None if np.isnan(bar) else float(bar),
        noise_arms=floor, oracle=oracle, catboost=nf.CB,
        split=dict(n_splits=nf.N_SPLITS, n_repeats=nf.N_REPEATS, seed=nf.RANDOM_STATE)))
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{out_stem}_k{a.k}_{time.strftime('%Y-%m-%d')}.json"
    path.write_text(json.dumps(res, indent=2))
    with duckdb.connect(str(DB)) as con:
        con.execute(f"create or replace table {out_tbl} as select * from (select ?::JSON as result)",
                    [json.dumps(res)])
    print(f"raw -> {path.relative_to(ROOT)} · duckdb::{out_tbl}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
