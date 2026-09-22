"""Mutation test for `040_verify_gates.py` -- proves it FAILS when a gate fails.

Why this exists: a verifier that has only ever been observed to pass is worthless, and this
repository has already paid for that lesson twice. Defect 20: a G3 repeat arm reported a
perfect rho = 1.000 because it never made a call. Defect 24 (§11.8 A-38): a "harmless" change
was accepted on `0 calls, $0.00, looks fine` and had silently corrupted the feature matrix.
`PLAN.md` §0.5: **verify a fix by checking its output, not by checking that it ran.**

So: copy the committed result JSONs, break exactly one thing, and assert the verifier notices.
Each case names the finding it protects.

Costs nothing and makes no API calls, so CI runs it BEFORE the paid pipeline -- there is no
point spending ~$0.33 to feed a verifier that cannot fail.

Exit 0 = every mutation was caught.  Exit 1 = the verifier missed one.  Exit 2 = no inputs.

Run:  .venv/bin/python scripts/041_test_verify_gates.py
Idempotent: yes - writes only to a temporary directory.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "research" / "data"
VERIFIER = ROOT / "scripts" / "040_verify_gates.py"

G1 = "gate_g1_obsnotes_*.json"
G26 = "gates_g2_g6_*.json"
G3 = "gate_g3_stability_*.json"
G4 = "gate_g4_s2b_*.json"
S3 = "step3_features_*.json"

CASES = []


def case(name, want_exit, want_text=None, args=()):
    def deco(fn):
        CASES.append((name, fn, want_exit, want_text, args))
        return fn
    return deco


def _edit(root, pattern, fn):
    hits = sorted((root / "research" / "data").glob(pattern))
    if not hits:
        raise SystemExit(f"no {pattern} to mutate")
    p = hits[-1]
    d = json.loads(p.read_text())
    fn(d)
    p.write_text(json.dumps(d, indent=2))


# --- the cases. Each one breaks a single claim the study rests on. ------------------------

@case("baseline: untouched results must PASS", 0, "criteria hold")
def _(root): pass


@case("G2 CI includes zero", 1, "G2: D beats B, CI excludes zero")
def _(root): _edit(root, G26, lambda d: d["G2"].update(ci_lo=-0.001))


@case("G2 positive but under the registered MDE", 1, "clears the registered MDE")
def _(root): _edit(root, G26, lambda d: d["G2"].update(dauc=0.004, ci_lo=0.0005))


@case("G4 temporal split collapses", 1, "G4: survives the temporal split")
def _(root):
    _edit(root, G4, lambda d: d["arms"]["G4b S2+S2a+S2b (train 884)"].update(ci_lo=-0.02))


@case("G5 leakage-stripped arm collapses", 1, "G5: survives leakage stripping")
def _(root): _edit(root, G26, lambda d: d["G5 (registered, with L6)"].update(ci_lo=-0.01))


@case("G6 missingness ablation collapses", 1, "G6: survives the missingness ablation")
def _(root): _edit(root, G26, lambda d: d["G6"].update(ci_lo=-0.01))


@case("G3 loses a TIER_PREDICTIVE feature", 1, "TIER_PREDICTIVE stable under paraphrase")
def _(root):
    def f(d):
        d["failing_predictive"] = ["author_certainty"]
        d["features"]["author_certainty"]["passed"] = False
    _edit(root, G3, f)


@case("G3 repeat arm compared with itself: 0.0000 (defect 34, CI run 35547134433)", 1,
      "G3: repeat arm measured real noise")
def _(root):
    def f(d):
        d["mean_abs_delta_repeat"] = 0.0
        for v in d["features"].values():
            v.update(repeat_rho=1.0, repeat_mean_abs_delta=0.0)
    _edit(root, G3, f)


@case("G3 repeat arm at v1.0.0's published 0.00006 (defect 34, local)", 1,
      "G3: repeat arm measured real noise")
def _(root): _edit(root, G3, lambda d: d.update(mean_abs_delta_repeat=0.00006))


@case("G1 baseline B falls below the 0.85 floor", 1, "baseline B >= 0.85")
def _(root): _edit(root, G1, lambda d: d["arms"][0].update(auc_B=0.72))


@case("dilution floor B+N flips positive (A-1 void)", 1, "dilution floor B+N stays NEGATIVE")
def _(root): _edit(root, G26, lambda d: d["B+N"].update(dauc=0.004))


@case("prose stops beating metadata (the key control)", 1, "D beats B+meta")
def _(root): _edit(root, G26, lambda d: d["D_vs_meta"].update(ci_lo=-0.004))


@case("corpus shrinks by half", 1, "rows within")
def _(root): _edit(root, G1, lambda d: d["arms"][0].update(n=700))


@case("--require-paid catches a zero-call run", 1, "made API calls", args=("--require-paid",))
def _(root): _edit(root, S3, lambda d: d.update(new_calls_this_run=0))


@case("--require-paid accepts a run that paid", 0, "criteria hold", args=("--require-paid",))
def _(root): _edit(root, S3, lambda d: d.update(new_calls_this_run=1382))


@case("drift past 5x the A-33 sd raises a NOTICE but still passes", 0, "NOTICE")
def _(root): _edit(root, G26, lambda d: d["G2"].update(dauc=0.0300, ci_lo=0.0200))


@case("missing inputs exit 2, not a false pass", 2, "INPUTS MISSING")
def _(root):
    for p in (root / "research" / "data").glob(G26):
        p.unlink()


def main() -> int:
    needed = [G1, G26, G3, G4, S3]
    absent = [p for p in needed if not list(DATA.glob(p))]
    if absent:
        print("INPUTS MISSING - cannot mutation-test without committed results:", file=sys.stderr)
        for a in absent:
            print(f"  research/data/{a}", file=sys.stderr)
        return 2

    ok = True
    for name, fn, want_exit, want_text, args in CASES:
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "scripts").mkdir()
            (root / "research").mkdir()
            shutil.copy(VERIFIER, root / "scripts" / VERIFIER.name)
            shutil.copytree(DATA, root / "research" / "data")
            fn(root)
            r = subprocess.run(
                [sys.executable, str(root / "scripts" / VERIFIER.name), *args],
                capture_output=True, text=True)
            out = r.stdout + r.stderr
            good = r.returncode == want_exit and (want_text is None or want_text in out)
            ok &= good
            print(f"{'ok  ' if good else 'FAIL'}  exit={r.returncode} (want {want_exit})  {name}")
            if not good:
                print(f"        expected text: {want_text!r}")
                print("        ---- verifier output ----")
                print("        " + out.replace("\n", "\n        ")[:2000])

    print()
    if ok:
        print(f"All {len(CASES)} mutations behaved correctly - the verifier can fail.")
        return 0
    print("SOME MUTATIONS WERE MISSED - the verifier cannot be trusted to fail.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
