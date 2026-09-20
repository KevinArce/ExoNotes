"""How much does G2 move under a drift-sized perturbation of the Jev features?

PREREGISTRATION.md §11.5 A-31 records that `jev-1.13.0` drifts over time: byte-identical
requests an hour apart return features differing by mean |Δ| = 0.0049. A-31 and PROVENANCE.md
both then assert that "no gate verdict is at risk", on the argument that G5's +0.0272 lower
bound is far beyond what a 0.005 feature perturbation could move.

**That was an argument, not a measurement.** This script measures it. The gates were never
re-run from a cold cache, so the map from feature perturbation to ΔAUC perturbation was never
established. It is cheap to establish with no API calls at all.

Method: perturb every TIER_PREDICTIVE column of the frozen feature matrix by Gaussian noise
scaled so its mean |Δ| equals the measured drift, clip to the feature's own range, re-quantise
to the two decimals Jev actually returns (§10.5), re-fit D, recompute ΔAUC(D − B) under S1 with
the registered A-6 aggregation. Repeat over N_SEEDS independent draws.

Two things this is NOT:
  * It is not a cold-cache re-run. Real drift is not i.i.d. Gaussian -- it is whatever the
    serving fleet does, and may be correlated across rows or concentrated in hard cases. This
    arm perturbs every row independently, which is the tractable stand-in, not the real thing.
  * It is not a registered gate. It is a robustness check on a published claim, reported as one.

Run:  .venv/bin/python scripts/038_drift_sensitivity.py [--seeds N] [--drift D]
Idempotent: yes. No network, no API calls, fixed seeds, JSON overwritten in place.
"""
import argparse
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
from exonotes.questions import QUESTION_SET_VERSION, TIER_PREDICTIVE  # noqa: E402

NUMERIC = nf.NUMERIC
PRED = list(TIER_PREDICTIVE)
DRIFT = 0.0049          # A-31: measured mean |Δ| per feature at a ~1 hour gap
QUANT = 0.01            # §10.5: Jev returns two decimals

# For a zero-mean Gaussian, E|X| = sigma * sqrt(2/pi). Solve for the sigma that reproduces
# the measured mean |Δ| BEFORE quantisation, so the perturbation matches the observed drift.
SIGMA = DRIFT / np.sqrt(2 / np.pi)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--drift", type=float, default=DRIFT,
                    help="mean |delta| per feature to simulate; default is A-31's measured 0.0049")
    ap.add_argument("--boot", type=int, default=nf.N_BOOT,
                    help="paired bootstrap resamples for the worst-case seed")
    args = ap.parse_args()
    sigma = args.drift / np.sqrt(2 / np.pi)

    con = duckdb.connect(str(DB), read_only=True)
    # Identical query to scripts/035_gates_g2_g6.py, so the reference arm IS the gate arm.
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
    lo, hi = Xpred.min().to_numpy(), Xpred.max().to_numpy()

    print(f"question set {QUESTION_SET_VERSION} · n={len(df):,} · TIC={df.tic_id.nunique():,}")
    print(f"simulated drift: mean |Δ| = {args.drift:.4f} per feature  (sigma {sigma:.4f}), "
          f"re-quantised to {QUANT}")
    print(f"{args.seeds} independent draws · S1 GroupKFold({nf.N_SPLITS}) x {nf.N_REPEATS}\n")

    PB = nf.oof_by_repeat(Xnum, y, groups)
    auc_B = nf.score(PB, y)
    PD0 = nf.oof_by_repeat(pd.concat([Xnum, Xpred], axis=1), y, groups)
    ref = nf.score(PD0, y) - auc_B
    print(f"  reference (unperturbed):  B {auc_B:.4f}  D {nf.score(PD0, y):.4f}  "
          f"ΔAUC {ref:+.4f}\n")

    draws, worst = [], None
    for s in range(args.seeds):
        rng = np.random.default_rng(nf.RANDOM_STATE + 1000 + s)
        noise = rng.normal(scale=sigma, size=Xpred.shape)
        Xp = np.clip(Xpred.to_numpy() + noise, lo, hi)
        Xp = np.round(Xp / QUANT) * QUANT
        realised = float(np.mean(np.abs(Xp - Xpred.to_numpy())))
        Xp = pd.DataFrame(Xp, columns=PRED)
        P = nf.oof_by_repeat(pd.concat([Xnum, Xp], axis=1), y, groups)
        d = nf.score(P, y) - auc_B
        draws.append(dict(seed=s, realised_mean_abs_delta=realised, auc_D=nf.score(P, y),
                          dauc=d, shift=d - ref))
        if worst is None or d < worst[0]:
            worst = (d, P)
        print(f"  seed {s:>2}  realised |Δ| {realised:.4f}  D {nf.score(P, y):.4f}  "
              f"ΔAUC {d:+.4f}  ({d - ref:+.4f} vs reference)")

    v = np.array([x["dauc"] for x in draws])
    print(f"\n  ΔAUC over {args.seeds} draws: mean {v.mean():+.4f} · sd {v.std(ddof=1):.4f} · "
          f"min {v.min():+.4f} · max {v.max():+.4f}")
    print(f"  worst-case shift from the reference: {v.min() - ref:+.4f}")

    # The full registered test on the worst draw: does G2 still pass?
    blo, bhi, bse = nf.paired_group_bootstrap(PB, worst[1], y, groups, args.boot)
    passes = bool(blo > 0)
    print(f"\n  worst draw, full paired bootstrap ({args.boot:,}): ΔAUC {worst[0]:+.4f}  "
          f"[{blo:+.4f}, {bhi:+.4f}]  -> G2 {'PASS' if passes else 'FAIL'}")

    mde = json.loads((OUT / "noise_floor_analysis_set_obsnotes_2026-09-20.json")
                     .read_text())["mde_80pct"]
    print(f"  MDE {mde:+.4f} · worst draw is {v.min() / mde:.1f}x the MDE")

    out = dict(
        generated=pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        question_set_version=QUESTION_SET_VERSION,
        simulated_drift=args.drift, sigma=float(sigma), quantisation=QUANT,
        n_seeds=args.seeds, auc_B=auc_B, reference_dauc=ref,
        dauc_mean=float(v.mean()), dauc_sd=float(v.std(ddof=1)),
        dauc_min=float(v.min()), dauc_max=float(v.max()),
        worst_shift=float(v.min() - ref),
        worst_case_bootstrap=dict(dauc=float(worst[0]), ci_lo=blo, ci_hi=bhi, se=bse,
                                  g2_passes=passes, n_boot=args.boot),
        mde=mde, draws=draws,
        caveat=("Gaussian i.i.d. per row is a tractable stand-in for real server-side drift, "
                "which may be correlated across rows. Not a cold-cache re-run, and not a "
                "registered gate."))
    # Named by the drift multiple so a sweep keeps every level rather than overwriting.
    out["drift_multiple_of_measured"] = args.drift / DRIFT
    name = f"drift_sensitivity_x{args.drift / DRIFT:g}_2026-09-20.json"
    (OUT / name).write_text(json.dumps(out, indent=2, default=float))
    print(f"\nraw -> research/data/{name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
