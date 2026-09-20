"""TASK A2 - re-establish gate G1 on the realised observer-note row set.

G1 was passed on the `Comments` corpus (B = 0.9154 AUC vs A = 0.5000). The obsnotes corpus is
a DIFFERENT ROW SET, and a different row set is a different pipeline, so G1 is re-run here
before anything downstream reads it.

**Criterion, pre-registered (HANDOFF TASK A2 / PREREGISTRATION.md section 6):**

    B >= 0.85 AUC  AND  B > A by a paired group bootstrap 95% CI excluding zero.

`scripts/02_baselines.py` tests only `mean(B) > mean(A)` on 15 per-fold AUCs with a std across
folds, which is not a standard error and not the registered criterion. This script applies the
registered one, using the A-6 aggregation and the A-6 paired bootstrap:

    pool out-of-fold predictions within a repeat, score each repeat, average the repeats;
    the bootstrap resamples TIC groups and uses the SAME resample for both models.

`paired_group_bootstrap`, `oof_by_repeat`, `score` and the CatBoost configuration are IMPORTED
from scripts/026_noise_floor.py rather than copied, so the G1 arm and the G2 reference arm
cannot drift apart.

It also answers A-7: **B's AUC on the included rows versus the excluded rows.** The obsnotes
inclusion rule is a collider -- follow-up effort sits downstream of both the numeric properties
and the disposition -- so if B is materially weaker on the included subset, model D is being
compared on easier ground and RESULTS.md has to say so.

Run:  .venv/bin/python scripts/030_gate_g1_obsnotes.py
Idempotent: yes. No network, no API calls, fixed seeds, CREATE OR REPLACE output.
"""
import datetime, importlib.util, json, pathlib, sys, warnings

import duckdb, numpy as np, pandas as pd

warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "exonotes.duckdb"
OUT = ROOT / "research" / "data"

_spec = importlib.util.spec_from_file_location("nf", ROOT / "scripts" / "026_noise_floor.py")
nf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nf)

NUMERIC, N_BOOT = nf.NUMERIC, nf.N_BOOT
G1_AUC_FLOOR = 0.85


def arm_A(y, groups):
    """Prior: predict the training-fold base rate. Constant within a fold -> AUC 0.5."""
    P = np.zeros((nf.N_REPEATS, len(y)))
    for r, tr, te in nf.repeated_group_kfold(groups, nf.N_SPLITS, nf.N_REPEATS, nf.RANDOM_STATE):
        P[r, te] = y[tr].mean()
    return P


def run(df: pd.DataFrame, label: str):
    y = df["y"].astype(int).to_numpy()
    groups = df["tic_id"].to_numpy()
    X = df[NUMERIC].apply(pd.to_numeric, errors="coerce").reset_index(drop=True)
    PA, PB = arm_A(y, groups), nf.oof_by_repeat(X, y, groups)
    a, b = nf.score(PA, y), nf.score(PB, y)
    lo, hi, se = nf.paired_group_bootstrap(PA, PB, y, groups, N_BOOT)
    print(f"  {label:<22} n={len(df):>5,}  TIC={df.tic_id.nunique():>5,}  "
          f"base={y.mean():.4f}   A={a:.4f}  B={b:.4f}  dAUC={b-a:+.4f}  "
          f"[{lo:+.4f}, {hi:+.4f}]")
    return dict(label=label, n=int(len(df)), n_tic=int(df.tic_id.nunique()),
                base_rate=float(y.mean()), auc_A=a, auc_B=b, dauc=b - a,
                ci_lo=lo, ci_hi=hi, se=se)


def main() -> int:
    con = duckdb.connect(str(DB), read_only=True)
    have = {r[0] for r in con.execute(
        "select table_name from information_schema.tables where table_schema='main'").fetchall()}
    if "analysis_set_obsnotes" not in have:
        print("ABORT: `analysis_set_obsnotes` does not exist. Run TASK A first:\n"
              "  .venv/bin/python scripts/028_obsnotes_pull.py", file=sys.stderr)
        return 2
    full = con.execute("select * from analysis_set").df()
    corpus = con.execute("select * from analysis_set_obsnotes").df()
    con.close()

    excluded = full[~full.toi.astype(str).isin(corpus.toi.astype(str))].reset_index(drop=True)

    print(f"S1: GroupKFold({nf.N_SPLITS}) x {nf.N_REPEATS} repeats on TIC · "
          f"paired bootstrap {N_BOOT:,} over TIC groups · A-6 aggregation\n")
    print("--- gate G1: B must reach >= 0.85 AUC and beat A with a CI excluding zero ---")
    res_corpus = run(corpus, "CORPUS (obsnotes)")
    print("\n--- A-7: is the included subset easier or harder ground for B? ---")
    res_full = run(full, "full analysis_set")
    res_excl = run(excluded, "EXCLUDED rows") if len(excluded) else None

    b = res_corpus["auc_B"]
    passed = (b >= G1_AUC_FLOOR) and (res_corpus["ci_lo"] > 0)
    print(f"\nGATE G1 on the obsnotes row set: B = {b:.4f} (floor {G1_AUC_FLOOR}) · "
          f"B-A 95% CI [{res_corpus['ci_lo']:+.4f}, {res_corpus['ci_hi']:+.4f}] "
          f"-> {'PASS' if passed else 'FAIL'}")

    if res_excl:
        d = res_corpus["auc_B"] - res_excl["auc_B"]
        print(f"\nA-7 read-across: B scores {res_corpus['auc_B']:.4f} on the included rows vs "
              f"{res_excl['auc_B']:.4f} on the excluded rows ({d:+.4f}).")
        print("  B weaker on the included subset means D is compared on HARDER ground;\n"
              "  B stronger means EASIER ground and RESULTS.md must say so. Either way this\n"
              "  number is reported, not acted on -- A-7 fixes no criterion to it.")

    res = dict(generated=datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
               criterion=dict(auc_floor=G1_AUC_FLOOR, ci_excludes_zero=True),
               passed=bool(passed), n_boot=N_BOOT,
               arms=[a for a in (res_corpus, res_full, res_excl) if a],
               split=dict(n_splits=nf.N_SPLITS, n_repeats=nf.N_REPEATS, seed=nf.RANDOM_STATE),
               catboost=nf.CB)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"gate_g1_obsnotes_{datetime.date.today().isoformat()}.json"
    path.write_text(json.dumps(res, indent=2))
    con = duckdb.connect(str(DB))
    con.execute("CREATE OR REPLACE TABLE gate_g1_obsnotes AS SELECT * FROM (SELECT ?::JSON AS result)",
                [json.dumps(res)])
    con.close()
    print(f"\nraw -> {path.relative_to(ROOT)}  ·  duckdb::gate_g1_obsnotes")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
