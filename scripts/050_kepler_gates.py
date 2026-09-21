"""Kepler gates KG2, KG4, KG5, KG6, the reference arms, and the A-40 40.9 transfer verdict.

scripts/035_gates_g2_g6.py, adapted to PREREGISTRATION.md section 11.10. WRITTEN AND COMMITTED
WITH A-41, BEFORE THE STEP 5 RUN: every comparison, split, clause set and threshold below was
fixed before any Kepler Jev feature existed, and the verdict is computed, not read off.

Everything statistical is IMPORTED from scripts/026_noise_floor.py (A-6 aggregation, paired
group bootstrap, CatBoost config) and B+meta from scripts/044_kepler_step2.py, so these arms
and the step-2 reference arms cannot drift apart.

  B        8 cumulative covariates (TESS B, column for column)        <- the comparator
  B+N      B + k = 6 pure-noise columns                               <- A-1 dilution reference
  B+meta   A-7 exactly (note count, chars, authors, top-8 author one-hot)
  C        TF-IDF + logistic on the text                              <- reported, never evidence
  D        B + the 6 TIER_PREDICTIVE Jev features                     <- THE HEADLINE
  E        B + all 8 Jev features                                     <- contaminated upper bound

  KG2  D - B, S1, paired bootstrap 10,000 over kepid: CI excludes 0      (A-40 40.7)
  KG4  D - B under S2: train host < 3865, test host >= 3865              (40.5)
  KG5  D - B on the KEPLER_PATTERNS-stripped arm, WITH L7 (headline) and without (sensitivity)
  KG6  D - B with explicit missingness indicators on B and D
  (KG3 is scripts/049_kepler_kg3_stability.py -- it needs API calls.)

TRANSFERS (40.9) requires ALL FOUR: KG2 passes with point estimate >= the registered MDE;
D beats B+meta (CI excludes 0); KG5 (with L7) passes; KG6 passes.

Run (after 048):  .venv/bin/python scripts/050_kepler_gates.py
Idempotent: yes. No network, no API calls, fixed seeds.
"""
import importlib.util, json, pathlib, sys, warnings

import duckdb, numpy as np, pandas as pd

warnings.filterwarnings("ignore")
ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "kepler.duckdb"
OUT = ROOT / "research" / "data"


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


nf = _load("nf", "026_noise_floor.py")
k2 = _load("k2", "044_kepler_step2.py")
sys.path.insert(0, str(ROOT / "src"))
from exonotes.leakage import KEPLER_PATTERNS, KEPLER_PATTERNS_NO_L7  # noqa: E402
from exonotes.questions_kepler import (  # noqa: E402
    QUESTION_SET_VERSION, TIER_LABEL_ECHO, TIER_PREDICTIVE)

FROZEN = "kepler-2026-09-21.r3"
NUMERIC, N_BOOT = k2.NUMERIC, nf.N_BOOT
PRED = list(TIER_PREDICTIVE)
ALLQ = PRED + list(TIER_LABEL_ECHO)
S2_HOST_CUTOFF = 3865                       # A-40 40.5
MDE_FILE = OUT / "kepler_cfop_step2_k6_2026-09-20.json"   # A-41: the registered MDE, k = 6


def fit(X, y, g):
    return nf.oof_by_repeat(X.reset_index(drop=True), y, g)


def compare(PB, PX, y, g, label, note=""):
    b, x = nf.score(PB, y), nf.score(PX, y)
    lo, hi, se = nf.paired_group_bootstrap(PB, PX, y, g, N_BOOT)
    ex = lo > 0 or hi < 0
    print(f"  {label:<30} B={b:.4f}  X={x:.4f}  dAUC={x - b:+.4f}  [{lo:+.4f}, {hi:+.4f}]  "
          f"{'EXCLUDES 0' if ex else 'includes 0'}{note}")
    return dict(label=label, auc_B=b, auc_X=x, dauc=x - b, ci_lo=lo, ci_hi=hi, se=se,
                excludes_zero=bool(ex))


def main() -> int:
    if QUESTION_SET_VERSION != FROZEN:
        raise SystemExit(f"question set {QUESTION_SET_VERSION!r} is not the frozen {FROZEN!r}")
    mde_rec = json.loads(MDE_FILE.read_text())
    assert mde_rec["k_noise"] == len(PRED) == 6, "registered MDE must be the k = 6 run"
    MDE = mde_rec["mde_80pct"]

    with duckdb.connect(str(DB), read_only=True) as con:
        df = con.execute("""
            select c.*, f.* exclude (kepoi_name, host)
            from kepler_cfop_corpus c join kepler_jev_features f using (kepoi_name)
            order by c.kepoi_name""").df()
    assert len(df) == 4720, f"expected 4,720 joined rows, got {len(df)}"
    y, g = df["y"].astype(int).to_numpy(), df["kepid"].to_numpy()
    Xnum = df[NUMERIC].apply(pd.to_numeric, errors="coerce").reset_index(drop=True)
    Xpred = df[PRED].apply(pd.to_numeric, errors="coerce").reset_index(drop=True)
    Xall = df[ALLQ].apply(pd.to_numeric, errors="coerce").reset_index(drop=True)
    print(f"question set {QUESTION_SET_VERSION} · n={len(df):,} · kepid={len(set(g)):,} · "
          f"base={y.mean():.4f} · registered MDE {MDE:+.4f}\n")

    res = {"registered_mde": MDE}
    PB = fit(Xnum, y, g)
    res["B"] = {"auc": nf.score(PB, y)}
    print(f"B (8 covariates) AUC {res['B']['auc']:.4f}\n--- reference arms ---")
    rng = np.random.default_rng(nf.RANDOM_STATE)
    Xn = pd.concat([Xnum, pd.DataFrame(rng.normal(size=(len(df), len(PRED))),
                                       columns=[f"noise_{i}" for i in range(len(PRED))])], axis=1)
    res["B+N"] = compare(PB, fit(Xn, y, g), y, g, "B+N (dilution floor)")
    PM = fit(pd.concat([Xnum, k2.meta_frame(df, "cfop")], axis=1), y, g)
    res["B+meta"] = compare(PB, PM, y, g, "B+meta (A-7)")

    print("\n--- KG2: D vs B, TIER_PREDICTIVE only (THE HEADLINE) ---")
    PD = fit(pd.concat([Xnum, Xpred], axis=1), y, g)
    res["KG2"] = compare(PB, PD, y, g, "D - B  (KG2)")
    print("\n--- criterion 2: D vs B+meta -- content, or how much follow-up happened? ---")
    res["D_vs_meta"] = compare(PM, PD, y, g, "D - B+meta")
    print("\n--- E: all 8 questions, contaminated upper bound (never the headline) ---")
    res["E"] = compare(PB, fit(pd.concat([Xnum, Xall], axis=1), y, g), y, g, "E - B (contaminated)")

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    PC = np.zeros((nf.N_REPEATS, len(y)))
    for r, tr, te in nf.repeated_group_kfold(g, nf.N_SPLITS, nf.N_REPEATS, nf.RANDOM_STATE):
        pipe = make_pipeline(TfidfVectorizer(min_df=3, max_features=50_000, sublinear_tf=True),
                             LogisticRegression(max_iter=2000, C=1.0))
        pipe.fit(df["text"].iloc[tr], y[tr])
        PC[r, te] = pipe.predict_proba(df["text"].iloc[te])[:, 1]
    res["C"] = {"auc": nf.score(PC, y)}
    print(f"\n--- C: TF-IDF + logistic, text only (reported, never evidence) --- AUC {res['C']['auc']:.4f}")

    print("\n--- KG5: KEPLER_PATTERNS-stripped arms (A-40 40.6, A-41) ---")
    for key, name, pats in (("KG5", "KG5 (registered, WITH L7)", KEPLER_PATTERNS),
                            ("KG5_noL7", "KG5 sensitivity (no L7)", KEPLER_PATTERNS_NO_L7)):
        keep = ~df["text"].map(lambda t: any(rx.search(t) for rx in pats.values())).to_numpy()
        sub = df[keep].reset_index(drop=True)
        yy, gg = sub["y"].astype(int).to_numpy(), sub["kepid"].to_numpy()
        xb = sub[NUMERIC].apply(pd.to_numeric, errors="coerce")
        xd = pd.concat([xb, sub[PRED].apply(pd.to_numeric, errors="coerce")], axis=1)
        res[key] = compare(fit(xb, yy, gg), fit(xd, yy, gg), yy, gg, name,
                           note=f"  n={len(sub):,} base={yy.mean():.3f}")
        res[key].update(n=int(len(sub)), base=float(yy.mean()))

    print("\n--- KG6: missingness ablation ---")
    miss = Xnum.isna().astype(int)
    miss.columns = [f"miss_{c}" for c in NUMERIC]
    res["KG6"] = compare(fit(pd.concat([Xnum, miss], axis=1), y, g),
                         fit(pd.concat([Xnum, miss, Xpred], axis=1), y, g), y, g,
                         "D - B (+missingness)")

    print(f"\n--- KG4: S2 on KOI host number, test = host >= {S2_HOST_CUTOFF} (S2a by construction) ---")
    te = (df["host"] >= S2_HOST_CUTOFF).to_numpy()
    tr = ~te
    assert not set(df.kepid[tr]) & set(df.kepid[te]), "a kepid straddles S2"
    from catboost import CatBoostClassifier

    def s2(X):
        m = CatBoostClassifier(random_seed=nf.RANDOM_STATE, **nf.CB)
        m.fit(X[tr], y[tr])
        return m.predict_proba(X[te])[:, 1]
    pb2, pd2 = s2(Xnum.to_numpy()), s2(pd.concat([Xnum, Xpred], axis=1).to_numpy())
    ab, ad = nf.fast_auc(y[te], pb2), nf.fast_auc(y[te], pd2)
    lo, hi, se = nf.paired_group_bootstrap(pb2[None, :], pd2[None, :], y[te], df.kepid[te].to_numpy(), N_BOOT)
    res["KG4"] = dict(n_train=int(tr.sum()), n_test=int(te.sum()), train_base=float(y[tr].mean()),
                      test_base=float(y[te].mean()), auc_B=ab, auc_D=ad, dauc=ad - ab,
                      ci_lo=lo, ci_hi=hi, se=se, excludes_zero=bool(lo > 0 or hi < 0))
    print(f"  train {tr.sum():,} (base {y[tr].mean():.3f}) · test {te.sum():,} (base {y[te].mean():.3f})")
    print(f"  S2  B={ab:.4f}  D={ad:.4f}  dAUC={ad - ab:+.4f}  [{lo:+.4f}, {hi:+.4f}]  "
          f"{'EXCLUDES 0' if (lo > 0 or hi < 0) else 'includes 0'}")

    # ---- the A-40 40.9 verdict, computed ------------------------------------------------
    pos = lambda r: r["excludes_zero"] and r["dauc"] > 0   # noqa: E731
    c1 = pos(res["KG2"]) and res["KG2"]["dauc"] >= MDE
    c2, c3, c4 = pos(res["D_vs_meta"]), pos(res["KG5"]), pos(res["KG6"])
    kg4 = pos(res["KG4"])
    kg3_file = OUT / "kepler_kg3_stability.json"
    kg3 = json.loads(kg3_file.read_text())["verdict"] if kg3_file.exists() else "NOT YET RUN"
    if not (pos(res["KG2"]) and res["KG2"]["dauc"] >= MDE):
        reading = ("DOES NOT TRANSFER" if not pos(res["KG2"]) else
                   "DETECTED, BELOW THE REGISTERED MDE -- not transfer")
    elif not c2:
        reading = "TRANSFERS ONLY AS FOLLOW-UP VOLUME -- the content claim does not transfer"
    elif not c3:
        reading = "LABEL ECHO ON KEPLER -- negative"
    elif not c4:
        reading = "TRACKS MISSINGNESS -- negative"
    else:
        reading = "TRANSFERS" if kg4 else "QUALIFIED TRANSFER -- holds under S1, not for later-identified KOIs"
    headroom = res["KG2"]["dauc"] / (1 - res["B"]["auc"])
    res["verdict"] = dict(criterion1_KG2_ge_MDE=c1, criterion2_D_beats_meta=c2,
                          criterion3_KG5=c3, criterion4_KG6=c4, KG4=kg4, KG3=kg3,
                          KG5_noL7_flip=bool(pos(res["KG5"]) != pos(res["KG5_noL7"])),
                          reading=reading, share_of_headroom=headroom)
    (OUT / "kepler_gates.json").write_text(json.dumps(res, indent=2, default=float))
    print("\n" + "=" * 78)
    for k, v in res["verdict"].items():
        print(f"  {k:<28} {v}")
    print(f"\nREADING (A-40 40.9): {reading}")
    print("raw -> research/data/kepler_gates.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
