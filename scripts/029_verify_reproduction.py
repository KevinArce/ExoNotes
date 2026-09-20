"""Verify that a from-scratch build reproduces the published result (PLAN.md §11.6 item 10).

This is the assertion behind the clean-clone reproduction check. It runs after
`01_ingest.py` and `02_baselines.py` and compares what they produced against the
reference values recorded on 2026-09-19.

**It deliberately does not demand equality.** PLAN.md §11.2: ExoFOP updates continuously and
the NASA Exoplanet Archive syncs weekly, so a later pull *will* differ. Insisting on 0.9154
exactly would turn normal archive drift into a red build and train everyone to ignore it.
What must hold is the *finding*: baseline B beats the prior by a wide margin, the prior sits
at chance, and the corpus is still roughly the size we described.

Exit 0 = reproduced. Exit 1 = a check failed. Exit 2 = the inputs are not there to check.

Run:  .venv/bin/python scripts/029_verify_reproduction.py
Idempotent: yes - read-only.
"""
import argparse
import pathlib
import sys

import duckdb

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "exonotes.duckdb"

# Reference values measured 2026-09-19 (WORKLOG.md, PROVENANCE.md).
REF = {
    "rows_analysis": 2721,
    "unique_tic_analysis": 2573,
    "A_prior_auc": 0.5000,
    "B_numeric_auc": 0.9154,
    "C_tfidf_auc": 0.9691,
}

# Tolerances. Wide enough to absorb archive drift, tight enough that a broken pipeline fails.
ROW_TOLERANCE = 0.25    # analysis-set size may drift +/-25%
PRIOR_TOLERANCE = 0.02  # a prior-only model must stay at chance
B_FLOOR = 0.85          # baseline B must remain clearly predictive


class Check:
    def __init__(self):
        self.failures = []

    def ok(self, label, passed, detail):
        mark = "PASS" if passed else "FAIL"
        print(f"  [{mark}] {label:<44} {detail}")
        if not passed:
            self.failures.append(f"{label}: {detail}")
        return passed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=pathlib.Path, default=DEFAULT_DB,
                    help="DuckDB file to verify (default: data/exonotes.duckdb)")
    db = ap.parse_args().db
    if not db.exists():
        print(f"ERROR: {db} does not exist - did 01_ingest.py run?", file=sys.stderr)
        return 2
    con = duckdb.connect(str(db), read_only=True)

    tables = {r[0] for r in con.execute(
        "select table_name from information_schema.tables").fetchall()}
    missing = {"analysis_set", "ingest_stats", "baseline_summary"} - tables
    if missing:
        print(f"ERROR: missing tables {sorted(missing)} - did 02_baselines.py run?",
              file=sys.stderr)
        return 2

    stats = dict(con.execute("select key, value from ingest_stats").fetchall())
    summary = {m: (auc, brier) for m, auc, brier in con.execute(
        "select model, auc_mean, brier_mean from baseline_summary").fetchall()}

    print("\n=== corpus ===")
    c = Check()
    rows = int(stats.get("rows_analysis", 0))
    tics = int(stats.get("unique_tic_analysis", 0))
    lo, hi = (int(REF["rows_analysis"] * (1 - ROW_TOLERANCE)),
              int(REF["rows_analysis"] * (1 + ROW_TOLERANCE)))
    c.ok("analysis rows within +/-25% of reference", lo <= rows <= hi,
         f"{rows} (ref {REF['rows_analysis']}, band {lo}-{hi})")
    c.ok("unique TIC > 0", tics > 0, f"{tics} (ref {REF['unique_tic_analysis']})")
    c.ok("snapshot date recorded", bool(stats.get("snapshot_date")),
         stats.get("snapshot_date", "MISSING"))

    print("\n=== gate G1 ===")
    for name in ("A_prior", "B_numeric"):
        if name not in summary:
            c.ok(f"{name} present", False, "MISSING from baseline_summary")
    if "A_prior" in summary and "B_numeric" in summary:
        a_auc, a_brier = summary["A_prior"]
        b_auc, b_brier = summary["B_numeric"]
        c.ok("A (prior) sits at chance",
             abs(a_auc - 0.5) <= PRIOR_TOLERANCE, f"AUC {a_auc:.4f} (ref 0.5000)")
        c.ok(f"B (numeric) AUC >= {B_FLOOR}",
             b_auc >= B_FLOOR, f"AUC {b_auc:.4f} (ref {REF['B_numeric_auc']:.4f}, "
                               f"delta {b_auc - REF['B_numeric_auc']:+.4f})")
        c.ok("B beats A on AUC", b_auc > a_auc, f"{b_auc:.4f} > {a_auc:.4f}")
        c.ok("B beats A on Brier", b_brier < a_brier, f"{b_brier:.4f} < {a_brier:.4f}")

    print("\n=== baseline C (reported, NOT a pass criterion) ===")
    if "C_tfidf" in summary:
        c_auc = summary["C_tfidf"][0]
        print(f"  [INFO] C_tfidf AUC {c_auc:.4f} (ref {REF['C_tfidf_auc']:.4f})")
        print("         This number is LEAKAGE, not signal - PLAN.md §2.0. ~48% of labelled")
        print("         comments carry a near-deterministic label marker. Never cite it as")
        print("         evidence for the hypothesis. It is not asserted on here.")

    print()
    if c.failures:
        print(f"REPRODUCTION FAILED - {len(c.failures)} check(s):", file=sys.stderr)
        for f in c.failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("REPRODUCTION VERIFIED - gate G1 reproduces from a clean build.")
    print()
    print("Reading the delta: compare the checksums in PROVENANCE.md against the committed")
    print("ones. DIFFERENT checksums mean the archives moved - expected, and exactly why this")
    print("check asserts the finding rather than the numbers. IDENTICAL checksums with a")
    print("non-zero delta mean the inputs were the same and the difference is compute")
    print("nondeterminism across platforms, not data drift. Measured 2026-09-20: identical")
    print("checksums, B = 0.9149 on linux/x64 vs 0.9154 on macos/arm64, i.e. ~5e-4 of")
    print("cross-platform wobble from floating point alone. Keep model-vs-model comparisons")
    print("within one platform, and treat any claimed gain smaller than that as noise.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
