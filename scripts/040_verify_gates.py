"""Assert that a from-scratch run still clears all six gates (RESULTS.md §9 item 5).

`029_verify_reproduction.py` covers ingest and G1 only, makes no API calls, and never touches
the corpus table, Step 3 or G2-G6. This is the other half: it runs after the full pipeline and
checks every registered gate criterion.

WHAT IT ASSERTS, AND WHY IT IS NOT EQUALITY
-------------------------------------------
A CI run differs from the published run in two independent ways, and only one of them is small:

  1. **Model drift.** A-31: byte-identical requests an hour apart differ by mean |d| 0.0049.
     A-33 mapped that to the headline: dAUC moves by sd 0.0010, and G2 still passes at 10x.
  2. **Corpus drift.** ExoFOP gains observing notes continuously. A cold CI run re-pulls the
     archive, so the rows, the note text and some dispositions are simply *different data*.
     This is unbounded and is NOT covered by (1).

So demanding +0.0432 exactly would turn normal archive drift into a red build and train
everyone to ignore it -- the failure mode `029_verify_reproduction.py` already warns about.
What must hold is each gate's **registered criterion**, which is what the study committed to
before the run. Point estimates are reported with their delta from publication, and a delta
beyond model drift alone raises a NOTICE (not a failure), because corpus drift can legitimately
produce one and a human should look rather than a build turning red.

THE ONE THING IT DOES DEMAND EXACTLY
------------------------------------
`--require-paid`: in CI the cache starts cold, so Step 3 *must* have made API calls. A run
reporting 0 new calls against an empty cache has not tested anything -- that is defect 20 (a
G3 arm scored a perfect rho because it never made a call) and defect 24 (a cached re-run
silently overwrote the record of the run that paid). Without this flag those pass as green.

Exit 0 = every gate holds.  Exit 1 = a gate failed.  Exit 2 = inputs missing.

Run:  .venv/bin/python scripts/040_verify_gates.py [--require-paid]
Idempotent: yes - read-only.
"""
import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "research" / "data"

# Published values, from the cache-consistent matrix (PREREGISTRATION.md §11.8 A-38).
#
# These are CONSTANTS ON PURPOSE. The result JSONs have hardcoded filenames, so a pipeline run
# OVERWRITES them -- reading the "published" number out of the same file the run just rewrote
# would compare the run against itself and pass vacuously. That is defect 24's mechanism.
REF = {
    "corpus_rows": 1482,
    "corpus_tic": 1388,
    "base_rate": 0.5378,
    "B_auc_g1": 0.9051,
    "G1_dauc": 0.4212,
    "G2_dauc": 0.0432,
    "G4_dauc": 0.1296,
    "G5_dauc": 0.0391,
    "G6_dauc": 0.0425,
    "BN_dauc": -0.0073,   # dilution floor: must stay NEGATIVE, it is why dAUC=0 is not a null
    "Bmeta_dauc": 0.0212,
    "D_vs_meta_dauc": 0.0220,
}

MDE = 0.0082          # A-20, 80% power. G2 must clear this or the study was not powered for it.
AUC_FLOOR = 0.85      # G1's registered floor on baseline B.
ROW_TOLERANCE = 0.25  # archive drift, same allowance as 029_verify_reproduction.py.
DRIFT_SD = 0.0010     # A-33: sd of dAUC under the measured model drift.
NOTICE_AT = 5 * DRIFT_SD  # a shift this large is not model drift alone -- look at the corpus.

# G4's registered arm. The `G4` key in gates_g2_g6_*.json is the PRE-S2b +0.0936; reading it
# instead of this one is what produced a forest plot contradicting the table beside it.
G4_ARM = "G4b S2+S2a+S2b (train 884)"
G5_ARM = "G5 (registered, with L6)"


def newest(pattern):
    """The run's own output. Globbed rather than hardcoded so a future rename fails loudly."""
    hits = sorted(DATA.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0] if hits else None


def load(pattern, missing):
    p = newest(pattern)
    if p is None:
        missing.append(pattern)
        return None, None
    return json.loads(p.read_text()), p.name


class Report:
    def __init__(self):
        self.rows, self.failed, self.notices = [], [], []

    def check(self, gate, criterion, ok, detail):
        self.rows.append((gate, criterion, ok, detail))
        if not ok:
            self.failed.append(f"{gate}: {criterion} -- {detail}")

    def delta(self, gate, observed, published):
        d = observed - published
        if abs(d) > NOTICE_AT:
            self.notices.append(
                f"{gate}: {observed:+.4f} vs published {published:+.4f} "
                f"(delta {d:+.4f}, beyond {NOTICE_AT:.4f} = 5x the A-33 model-drift sd). "
                f"Corpus drift is the likely cause; confirm before trusting the run.")
        return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--require-paid", action="store_true",
                    help="demand that Step 3 actually made API calls (use in CI: cold cache)")
    args = ap.parse_args()

    missing = []
    g1, f_g1 = load("gate_g1_obsnotes_*.json", missing)
    g26, f_g26 = load("gates_g2_g6_*.json", missing)
    g3, f_g3 = load("gate_g3_stability_*.json", missing)
    g4, f_g4 = load("gate_g4_s2b_*.json", missing)
    s3, f_s3 = load("step3_features_*.json", missing)

    if missing:
        print("INPUTS MISSING - the pipeline did not produce:", file=sys.stderr)
        for m in missing:
            print(f"  research/data/{m}", file=sys.stderr)
        print("\nRun 028 -> 034 -> 035 -> 036 -> 039 first.", file=sys.stderr)
        return 2

    print("Reading this run's outputs:")
    for f in (f_g1, f_g26, f_g3, f_g4, f_s3):
        print(f"  research/data/{f}")

    r = Report()

    # ---- the run must actually have run -------------------------------------------------
    calls = s3.get("new_calls_this_run", 0)
    cached = s3.get("cached_calls_this_run", 0)
    if args.require_paid:
        r.check("STEP3", "made API calls (cold cache)", calls > 0,
                f"new_calls_this_run={calls}, cached={cached}. Zero new calls against a cold "
                f"cache means nothing was tested (defect 20/24).")
    else:
        print(f"\n[step3] new calls {calls} · from cache {cached} "
              f"(--require-paid not set, so a warm run is accepted)")

    # ---- corpus ---------------------------------------------------------------------------
    corpus = next((a for a in g1["arms"] if "obsnotes" in a["label"].lower()), None)
    if corpus is None:
        print("FAIL: no obsnotes arm in the G1 result", file=sys.stderr)
        return 1
    n = corpus["n"]
    lo, hi = REF["corpus_rows"] * (1 - ROW_TOLERANCE), REF["corpus_rows"] * (1 + ROW_TOLERANCE)
    r.check("CORPUS", f"rows within +/-{ROW_TOLERANCE:.0%} of {REF['corpus_rows']}",
            lo <= n <= hi, f"n={n} (published {REF['corpus_rows']}, allowed {lo:.0f}-{hi:.0f})")

    # ---- G1 -------------------------------------------------------------------------------
    r.check("G1", f"baseline B >= {AUC_FLOOR}", corpus["auc_B"] >= AUC_FLOOR,
            f"B={corpus['auc_B']:.4f} (published {REF['B_auc_g1']:.4f})")
    r.check("G1", "B - A CI excludes zero", corpus["ci_lo"] > 0,
            f"dAUC={corpus['dauc']:+.4f} [{corpus['ci_lo']:+.4f}, {corpus['ci_hi']:+.4f}]")
    r.delta("G1", corpus["dauc"], REF["G1_dauc"])

    # ---- G2, the headline -----------------------------------------------------------------
    g2 = g26["G2"]
    r.check("G2", "D beats B, CI excludes zero", g2["ci_lo"] > 0,
            f"dAUC={g2['dauc']:+.4f} [{g2['ci_lo']:+.4f}, {g2['ci_hi']:+.4f}]")
    r.check("G2", f"dAUC clears the registered MDE {MDE:+.4f}", g2["dauc"] >= MDE,
            f"dAUC={g2['dauc']:+.4f} vs MDE {MDE:+.4f} "
            f"({g2['dauc'] / MDE:.1f}x; published was {REF['G2_dauc'] / MDE:.1f}x)")
    r.delta("G2", g2["dauc"], REF["G2_dauc"])

    # ---- G3 -------------------------------------------------------------------------------
    fails = g3.get("failing_predictive", [])
    npred = sum(1 for v in g3["features"].values() if v["tier"] == "predictive")
    npass = sum(1 for v in g3["features"].values()
                if v["tier"] == "predictive" and v["passed"])
    r.check("G3", f"all {npred} TIER_PREDICTIVE stable under paraphrase", not fails,
            f"{npass}/{npred} pass"
            + (f"; failing: {', '.join(fails)}" if fails else ""))

    # ---- G4, the registered temporal split ------------------------------------------------
    if G4_ARM not in g4.get("arms", {}):
        print(f"FAIL: G4 arm {G4_ARM!r} absent; found {list(g4.get('arms', {}))}",
              file=sys.stderr)
        return 1
    a4 = g4["arms"][G4_ARM]
    r.check("G4", "survives the temporal split, CI excludes zero", a4["ci_lo"] > 0,
            f"dAUC={a4['dauc']:+.4f} [{a4['ci_lo']:+.4f}, {a4['ci_hi']:+.4f}] ({G4_ARM})")
    r.delta("G4", a4["dauc"], REF["G4_dauc"])

    # ---- G5 -------------------------------------------------------------------------------
    a5 = g26[G5_ARM]
    r.check("G5", "survives leakage stripping, CI excludes zero", a5["ci_lo"] > 0,
            f"dAUC={a5['dauc']:+.4f} [{a5['ci_lo']:+.4f}, {a5['ci_hi']:+.4f}]")
    r.delta("G5", a5["dauc"], REF["G5_dauc"])

    # ---- G6 -------------------------------------------------------------------------------
    a6 = g26["G6"]
    r.check("G6", "survives the missingness ablation, CI excludes zero", a6["ci_lo"] > 0,
            f"dAUC={a6['dauc']:+.4f} [{a6['ci_lo']:+.4f}, {a6['ci_hi']:+.4f}]")
    r.delta("G6", a6["dauc"], REF["G6_dauc"])

    # ---- controls: not gates, but the study leans on them ---------------------------------
    bn = g26["B+N"]
    r.check("CONTROL", "dilution floor B+N stays NEGATIVE", bn["dauc"] < 0,
            f"dAUC={bn['dauc']:+.4f} [{bn['ci_lo']:+.4f}, {bn['ci_hi']:+.4f}]. If this went "
            f"positive, adding known-worthless columns would be HELPING and the whole "
            f"dilution argument (A-1) would be void.")
    dm = g26["D_vs_meta"]
    r.check("CONTROL", "D beats B+meta -- prose adds beyond provenance", dm["ci_lo"] > 0,
            f"dAUC={dm['dauc']:+.4f} [{dm['ci_lo']:+.4f}, {dm['ci_hi']:+.4f}]. RESULTS.md §2 "
            f"calls this the single most important control in the study.")
    r.delta("CONTROL D-B+meta", dm["dauc"], REF["D_vs_meta_dauc"])

    c = g26["C"]["auc"]
    print(f"\n[reported, not asserted] baseline C (TF-IDF) AUC {c:.4f} "
          f"vs B {g2['auc_B']:.4f} -- published C was 0.8766, BELOW B. "
          f"{'still below B' if c < g2['auc_B'] else 'ABOVE B this run - see RESULTS.md §4'}")

    # ---- report ---------------------------------------------------------------------------
    print("\n" + "=" * 78)
    for gate, criterion, ok, detail in r.rows:
        print(f"{'PASS' if ok else 'FAIL':<5} {gate:<16} {criterion}")
        print(f"      {detail}")
    print("=" * 78)

    if r.notices:
        print("\nNOTICES - not failures. A gate held, but the point estimate moved further")
        print("than model drift alone explains (A-33 sd = 0.0010). Corpus drift can do this.")
        for n_ in r.notices:
            print(f"  * {n_}")

    if r.failed:
        print(f"\nFAILED: {len(r.failed)} criterion/criteria did not hold.")
        for f in r.failed:
            print(f"  - {f}")
        return 1

    print(f"\nAll {len(r.rows)} criteria hold. Every registered gate still passes from scratch.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
