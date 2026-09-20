"""Reliability diagrams and the gate forest plot (PREREGISTRATION.md §9 item 7).

§9 item 7 asks for `RESULTS.md` "with reliability diagrams and CIs". This produces the two
figures that write-up needs, plus the JSON behind them.

**What is being calibrated here.** These diagrams are for **CatBoost's** `predict_proba` under
split S1, for baselines B (numeric only) and D (numeric + TIER_PREDICTIVE Jev features).
`PLAN.md` §1 forbids thresholding on Jev's own `confidence`; that guardrail is about the
model's self-reported distribution statistic and is untouched here. No Jev probability is
thresholded, and no Jev output is treated as a conclusion.

**Everything statistical is IMPORTED from scripts/026_noise_floor.py** -- the S1 construction,
the A-6 aggregation, the CatBoost config and the NUMERIC list -- and the dataframe is built by
the SAME query as scripts/035_gates_g2_g6.py, so the probabilities plotted here are the
probabilities that produced the gate verdicts. Do not re-implement either.

**How the three S1 repeats are handled.** Each row gets one out-of-fold prediction per repeat,
so the three OOF vectors are correlated, not independent replicates:
  * Brier / ECE / MCE are computed PER REPEAT and reported as mean with min-max range.
  * The plotted curve pools all three repeats, and its per-bin Wilson 95% interval is computed
    at n_eff = count / N_REPEATS -- the independent row count -- rather than at the pooled
    count, which would claim 3x the precision the data has.

**A second B.** `scripts/030_gate_g1_obsnotes.py` reports B = 0.9051 and
`scripts/035_gates_g2_g6.py` reports B = 0.9044 on the same 1,482 rows. The two scripts read
those rows in different orders (035 adds `order by a.toi` for the feature join). This script
fits B both ways and prints the gap, so that 0.0007 is a measured property of CatBoost's
sensitivity to input row order rather than an unexplained discrepancy between two files.

Run:  .venv/bin/python scripts/037_reliability.py
Idempotent: yes. No network, no API calls, fixed seeds, outputs overwritten in place.
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
FIG = ROOT / "assets"

_spec = importlib.util.spec_from_file_location("nf", ROOT / "scripts" / "026_noise_floor.py")
nf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nf)

sys.path.insert(0, str(ROOT / "src"))
from exonotes.questions import QUESTION_SET_VERSION, TIER_PREDICTIVE  # noqa: E402

NUMERIC = nf.NUMERIC
PRED = list(TIER_PREDICTIVE)
N_BINS = 10

# dataviz reference palette, categorical slots 1 and 2. Validated for this 2-slot pairing:
# CVD dE 24.7 (protan) / 32.7 (tritan), normal-vision dE 33.6, both >= 3:1 on the surface.
C_B, C_D = "#2a78d6", "#eb6834"
INK, INK2, MUTED, SURF = "#0b0b0b", "#52514e", "#8a8984", "#fcfcfb"


def wilson(k: float, n: float, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval. Degrades gracefully on an empty bin."""
    if n <= 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def calib(y: np.ndarray, p: np.ndarray, n_bins: int = N_BINS) -> dict:
    """Equal-width reliability bins plus Brier, ECE and MCE for one prediction vector."""
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1], right=False), 0, n_bins - 1)
    rows, ece, mce = [], 0.0, 0.0
    for b in range(n_bins):
        m = idx == b
        n = int(m.sum())
        if n == 0:
            rows.append(dict(bin=b, lo=edges[b], hi=edges[b + 1], n=0,
                             mean_pred=np.nan, obs_freq=np.nan, n_pos=0))
            continue
        mp, of = float(p[m].mean()), float(y[m].mean())
        gap = abs(of - mp)
        ece += n / len(y) * gap
        mce = max(mce, gap)
        rows.append(dict(bin=b, lo=float(edges[b]), hi=float(edges[b + 1]), n=n,
                         mean_pred=mp, obs_freq=of, n_pos=int(y[m].sum())))
    return dict(bins=rows, brier=float(np.mean((p - y) ** 2)), ece=float(ece), mce=float(mce))


def summarise(P: np.ndarray, y: np.ndarray, name: str) -> dict:
    """Per-repeat metrics (mean + range) and the pooled curve with n_eff Wilson intervals."""
    per = [calib(y, P[r]) for r in range(P.shape[0])]
    n_rep = P.shape[0]

    pooled_y = np.tile(y, n_rep)
    pooled_p = np.concatenate([P[r] for r in range(n_rep)])
    pooled = calib(pooled_y, pooled_p)
    for row in pooled["bins"]:
        n_eff = row["n"] / n_rep
        lo, hi = wilson(row["n_pos"] / n_rep, n_eff)
        row["n_eff"] = n_eff
        row["ci_lo"], row["ci_hi"] = float(lo), float(hi)

    def spread(k):
        v = [d[k] for d in per]
        return dict(mean=float(np.mean(v)), min=float(np.min(v)), max=float(np.max(v)))

    return dict(name=name, auc=nf.score(P, y), n_repeats=n_rep,
                brier=spread("brier"), ece=spread("ece"), mce=spread("mce"),
                per_repeat=per, pooled=pooled)


def fig_reliability(sb: dict, sd: dict, base: float, n: int, n_tic: int) -> pathlib.Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(9.0, 6.4), dpi=200, facecolor=SURF)
    gs = fig.add_gridspec(2, 1, height_ratios=[3.0, 1.0], hspace=0.10)
    ax, axh = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])

    for a in (ax, axh):
        a.set_facecolor(SURF)
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            a.spines[s].set_color(MUTED)
            a.spines[s].set_linewidth(0.8)
        a.tick_params(colors=INK2, labelsize=8.5, length=3, width=0.8)

    ax.plot([0, 1], [0, 1], color=MUTED, lw=1.0, ls=(0, (4, 3)), zorder=1)
    ax.annotate("perfectly calibrated", xy=(0.80, 0.80), xytext=(0.82, 0.71),
                color=MUTED, fontsize=8, ha="left", rotation=0)
    ax.axhline(base, color=MUTED, lw=0.8, ls=(0, (1, 3)), zorder=1)
    ax.annotate(f"base rate {base:.4f}", xy=(0.015, base), xytext=(0.015, base + 0.022),
                color=MUTED, fontsize=8)

    for s, c, label in ((sb, C_B, "B — numeric only"), (sd, C_D, "D — numeric + Jev")):
        b = [r for r in s["pooled"]["bins"] if r["n"] > 0]
        x = np.array([r["mean_pred"] for r in b])
        yv = np.array([r["obs_freq"] for r in b])
        lo = np.array([r["ci_lo"] for r in b])
        hi = np.array([r["ci_hi"] for r in b])
        ax.vlines(x, lo, hi, color=c, lw=2.0, alpha=0.45, zorder=2)
        ax.plot(x, yv, color=c, lw=2.0, zorder=3,
                label=f"{label}   AUC {s['auc']:.4f} · Brier {s['brier']['mean']:.4f} "
                      f"· ECE {s['ece']['mean']:.4f}")
        ax.plot(x, yv, "o", ms=6, color=c, mec=SURF, mew=1.6, zorder=4)

    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.04, 1.04)
    ax.set_ylabel("observed fraction positive", color=INK2, fontsize=9)
    ax.set_xticklabels([])
    ax.grid(axis="y", color=MUTED, alpha=0.18, lw=0.7)
    ax.set_axisbelow(True)
    leg = ax.legend(loc="upper left", frameon=False, fontsize=8.5, handlelength=1.6,
                    borderpad=0.2, labelspacing=0.5)
    for t in leg.get_texts():
        t.set_color(INK2)
    ax.set_title("Reliability of the predicted probabilities, split S1 out-of-fold",
                 color=INK, fontsize=11.5, loc="left", pad=36)
    ax.annotate(f"n = {n:,} rows · {n_tic:,} TIC groups · GroupKFold(5) × 3 repeats · "
                f"question set {QUESTION_SET_VERSION}\n"
                f"bars are Wilson 95% at the independent row count; CatBoost probabilities, "
                f"not Jev's",
                xy=(0, 1.005), xycoords="axes fraction", va="bottom",
                color=MUTED, fontsize=8)

    edges = np.linspace(0, 1, N_BINS + 1)
    w = (edges[1] - edges[0]) / 2 - 0.006
    for s, c, off in ((sb, C_B, -w / 2 - 0.003), (sd, C_D, +w / 2 + 0.003)):
        ctr = np.array([(r["lo"] + r["hi"]) / 2 for r in s["pooled"]["bins"]])
        cnt = np.array([r["n"] / s["n_repeats"] for r in s["pooled"]["bins"]])
        axh.bar(ctr + off, cnt, width=w, color=c, linewidth=0)
    axh.set_xlim(-0.02, 1.02)
    axh.set_xlabel("predicted probability of a confirmed planet", color=INK2, fontsize=9)
    axh.set_ylabel("rows per bin", color=INK2, fontsize=9)
    axh.grid(axis="y", color=MUTED, alpha=0.18, lw=0.7)
    axh.set_axisbelow(True)

    p = FIG / "reliability_b_d.png"
    fig.savefig(p, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)
    return p


def fig_forest(gates: dict, mde: float, floor: float) -> pathlib.Path:
    """Every arm's ΔAUC with its 95% CI, grouped by what row set / split it was measured on."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    G = gates
    rows = [
        ("S1 — the registered corpus:  n = 1,482 · 1,388 TIC · base 0.5378", None, None),
        ("B+N — dilution floor (A-1)", G["B+N"], False),
        ("B+meta — metadata control (A-7)", G["B+meta"], False),
        ("D − B   ◄ HEADLINE (G2, §7)", G["G2"], True),
        ("D − B+meta — beyond provenance", G["D_vs_meta"], False),
        ("E − B — LEAKAGE-CONTAMINATED", G["E"], False),
        ("G6 — missingness ablation", G["G6"], True),
        ("S1, leakage-stripped rows only (§11.4) — a different row set and base rate",
         None, None),
        ("G5 — registered, with L6   n=1,114 · base 0.426",
         G["G5 (registered, with L6)"], True),
        ("G5 — sensitivity, no L6    n=1,196 · base 0.463",
         G["G5 sensitivity (no L6)"], False),
        ("S2 temporal split (§4) — NOT comparable to an S1 ΔAUC", None, None),
        ("G4 — train 1,070 / test 390 · base 0.4888 → 0.6487", G["G4"], True),
    ]

    fig, ax = plt.subplots(figsize=(9.4, 6.0), dpi=200, facecolor=SURF)
    ax.set_facecolor(SURF)

    ypos, labels, head_y = [], [], []
    y = 0.0
    for label, r, _ in rows:
        if r is None:
            y -= 0.85
            head_y.append(y)
            labels.append((y, label, True))
        else:
            y -= 1.0
            ypos.append(y)
            labels.append((y, label, False))

    i = 0
    for label, r, is_gate in rows:
        if r is None:
            continue
        yy = ypos[i]
        i += 1
        d, lo, hi = r["dauc"], r["ci_lo"], r["ci_hi"]
        c = C_B if is_gate else INK2
        ax.hlines(yy, lo, hi, color=c, lw=2.0, alpha=0.5 if not is_gate else 0.75)
        ax.plot([lo, hi], [yy, yy], "|", ms=7, color=c, alpha=0.9)
        ax.plot(d, yy, "o", ms=9 if is_gate else 6.5, color=c, mec=SURF, mew=1.6, zorder=4)
        # A negative arm is labelled to its LEFT so the text never straddles the zero line.
        anchor, dx, ha = ((lo, -6, "right") if hi < 0 else (hi, 6, "left"))
        ax.annotate(f"{d:+.4f}  [{lo:+.4f}, {hi:+.4f}]", xy=(anchor, yy), xytext=(dx, 0),
                    textcoords="offset points", va="center", ha=ha, fontsize=8.2,
                    color=INK if is_gate else INK2,
                    fontweight="bold" if is_gate else "normal")

    ax.axvline(0.0, color=INK, lw=1.0, zorder=2)
    y_note = min(ypos) - 0.82
    for x, txt in ((mde, f"MDE +{mde:.4f}"), (floor, f"dilution floor {floor:+.4f}")):
        ax.axvline(x, color=MUTED, lw=1.0, ls=(0, (4, 3)), zorder=1)
        ax.annotate(txt, xy=(x, y_note), color=MUTED, fontsize=8, rotation=90,
                    ha="right", va="bottom")

    ax.set_yticks([])
    for yy, label, is_head in labels:
        ax.annotate(label, xy=(0, yy), xycoords=("axes fraction", "data"),
                    xytext=(-8, 0), textcoords="offset points", ha="right", va="center",
                    fontsize=8.6 if not is_head else 8.2,
                    color=INK2 if not is_head else MUTED,
                    fontstyle="italic" if is_head else "normal")

    ax.set_xlim(-0.035, 0.195)
    ax.set_ylim(min(ypos) - 1.0, 1.4)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.tick_params(colors=INK2, labelsize=8.5, length=3, width=0.8)
    ax.grid(axis="x", color=MUTED, alpha=0.18, lw=0.7)
    ax.set_axisbelow(True)
    ax.set_xlabel("ΔAUC vs the matching numeric-only baseline  (paired bootstrap, "
                  "10,000 resamples over TIC groups)", color=INK2, fontsize=9)
    ax.set_title("Every arm, with its 95% confidence interval",
                 color=INK, fontsize=11.5, loc="left", pad=22, x=-0.001)
    ax.annotate("blue = a registered gate · grey = a reference arm, never a gate · "
                "each interval is paired against ITS own baseline",
                xy=(0, 1.012), xycoords="axes fraction", va="bottom",
                color=MUTED, fontsize=8)

    p = FIG / "gate_forest.png"
    fig.savefig(p, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)
    return p


def main() -> int:
    con = duckdb.connect(str(DB))
    have = {r[0] for r in con.execute(
        "select table_name from information_schema.tables where table_schema='main'").fetchall()}
    if "jev_features_obsnotes" not in have:
        print("ABORT: jev_features_obsnotes does not exist. Run Step 3 first:\n"
              "  .venv/bin/python scripts/034_step3_features.py", file=sys.stderr)
        return 2

    # Identical to scripts/035_gates_g2_g6.py, so the folds and fits match the gate verdicts.
    df = con.execute("""
        select a.*, f.* exclude (tic_id, toi)
        from analysis_set_obsnotes a
        join jev_features_obsnotes f on f.toi = cast(a.toi as varchar)
        order by a.toi""").df()
    unordered = con.execute("select * from analysis_set_obsnotes").df()
    con.close()
    df = df.loc[:, ~df.columns.duplicated()].reset_index(drop=True)

    y = df["y"].astype(int).to_numpy()
    groups = df["tic_id"].to_numpy()
    Xnum = df[NUMERIC].apply(pd.to_numeric, errors="coerce").reset_index(drop=True)
    Xpred = df[PRED].apply(pd.to_numeric, errors="coerce").reset_index(drop=True)

    n, n_tic, base = len(df), df.tic_id.nunique(), float(y.mean())
    print(f"question set {QUESTION_SET_VERSION} · n={n:,} · TIC={n_tic:,} · base={base:.4f}")
    print(f"S1: GroupKFold({nf.N_SPLITS}) x {nf.N_REPEATS} repeats · {N_BINS} equal-width bins\n")

    PB = nf.oof_by_repeat(Xnum, y, groups)
    PD = nf.oof_by_repeat(pd.concat([Xnum, Xpred], axis=1), y, groups)
    sb = summarise(PB, y, "B (numeric only)")
    sd = summarise(PD, y, "D (numeric + TIER_PREDICTIVE)")

    for s in (sb, sd):
        print(f"  {s['name']:<32} AUC {s['auc']:.4f}  "
              f"Brier {s['brier']['mean']:.4f} [{s['brier']['min']:.4f}–{s['brier']['max']:.4f}]  "
              f"ECE {s['ece']['mean']:.4f} [{s['ece']['min']:.4f}–{s['ece']['max']:.4f}]  "
              f"MCE {s['mce']['mean']:.4f}")

    # Why two values of B exist in this repository.
    uy = unordered["y"].astype(int).to_numpy()
    ug = unordered["tic_id"].to_numpy()
    uX = unordered[NUMERIC].apply(pd.to_numeric, errors="coerce").reset_index(drop=True)
    auc_unordered = nf.score(nf.oof_by_repeat(uX, uy, ug), uy)
    print(f"\n  row-order check: B = {sb['auc']:.4f} (035 order, `order by a.toi`) vs "
          f"{auc_unordered:.4f} (026/030 order)")
    print(f"  gap {abs(sb['auc'] - auc_unordered):+.4f} — same rows, same folds, same config; "
          f"CatBoost is sensitive to input row order")

    gates = json.loads((OUT / "gates_g2_g6_2026-09-20.json").read_text())
    floorj = json.loads((OUT / "noise_floor_analysis_set_obsnotes_2026-09-20.json").read_text())
    mde, floor = floorj["mde_80pct"], floorj["dilution_floor"]

    FIG.mkdir(exist_ok=True)
    p1 = fig_reliability(sb, sd, base, n, n_tic)
    p2 = fig_forest(gates, mde, floor)

    out = dict(
        generated=pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        question_set_version=QUESTION_SET_VERSION,
        n=n, n_tic=int(n_tic), base_rate=base, n_bins=N_BINS,
        split=dict(n_splits=nf.N_SPLITS, n_repeats=nf.N_REPEATS, seed=nf.RANDOM_STATE),
        note=("CatBoost predict_proba calibration, not Jev confidence (PLAN.md §1). "
              "Per-repeat metrics are mean [min-max] over the 3 S1 repeats; pooled-curve "
              "Wilson intervals use n_eff = count / n_repeats."),
        row_order_sensitivity=dict(
            auc_B_ordered=sb["auc"], auc_B_unordered=auc_unordered,
            gap=float(sb["auc"] - auc_unordered),
            explains="030_gate_g1_obsnotes.py reports 0.9051; 035_gates_g2_g6.py reports 0.9044"),
        B=sb, D=sd, figures=[str(p1.relative_to(ROOT)), str(p2.relative_to(ROOT))])
    (OUT / "reliability_2026-09-20.json").write_text(json.dumps(out, indent=2, default=float))

    print(f"\nfigures -> {p1.relative_to(ROOT)} · {p2.relative_to(ROOT)}")
    print(f"raw     -> research/data/reliability_2026-09-20.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
