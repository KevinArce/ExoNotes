"""Build the LABEL-BLINDED case set for the obsnotes question gate (TASK B, PLAN.md §6 Step 2.5).

The r4 gate cases carried `y=` in the source file, so the expectations were written with the
label in view. The audit (WORKLOG 2026-09-20 audit block; HANDOFF_PROMPT TASK B) requires this
round be blinded. This script is the blinding mechanism:

  * cases are selected PROGRAMMATICALLY -- by length stratum and by over-broad topic regex --
    with a fixed seed, never by hand-picking a row that "looks good";
  * the emitted case file carries cid / toi / tic / length / text and **no label**;
  * `y` is read only by `--unblind`, which is run after every answer has been inspected.

Run:  .venv/bin/python scripts/031_gate_cases_obsnotes.py            # write the blinded cases
      .venv/bin/python scripts/031_gate_cases_obsnotes.py --unblind  # after inspection only

Idempotent: yes. Read-only against DuckDB, fixed seed, deterministic output.
"""
import argparse
import json
import pathlib
import random
import re

import duckdb

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "exonotes.duckdb"
OUT = ROOT / "research" / "data" / "gate_cases_obsnotes_2026-09-20.json"

SEED = 20260920

# Length strata for the backbone sample. The corpus runs min 20 / p50 870 / p95 3,261 /
# max 41,268, and jev-1.13 documents accuracy loss on large states carrying irrelevant
# detail, so the long tail is deliberately over-sampled relative to its density.
STRATA = [
    ("S1_short",     0,    300, 3),
    ("S2_median",  300,    900, 3),
    ("S3_typical", 900,   2000, 3),
    ("S4_long",   2000,   5000, 3),
    ("S5_verylong", 5000, 10**9, 3),
]

# One case per topic, so every candidate question gets a positive and a nearest confusable.
# These regexes are over-broad ON PURPOSE: they select SUBJECT MATTER, not the answer.
TOPICS = [
    ("T01_neb_beb",        r"(?i)\b(NEB|BEB)\b|nearby eclipsing|background eclipsing"),
    ("T02_sb",             r"(?i)\b(SB1|SB2|SEB1|SEB2)\b|double-?lined"),
    ("T03_imaging_clean",  r"(?i)no secondary sources? (were |was )?detected"),
    # NOTE: the obvious regex here -- "(companion|secondary source) ... detected" -- is WRONG.
    # It matches the negated boilerplate "No secondary sources were detected", because ExoFOP's
    # raw HTML glues it to the preceding token as "832nmNo secondary sources were detected", so
    # a leading-\bno\b guard does not bind either. Select a genuine detection by its separation.
    ("T04_imaging_comp",   r"(?i)(companion|source|star)[^.]{0,40}\bat\s+\d+(\.\d+)?\s*(arcsec|\"|mas)"),
    ("T05_rv_rules_out",   r"(?i)rules? out[^.]{0,60}(stellar|brown dwarf|companion)"),
    ("T06_rv_binary",      r"(?i)(large|huge|significant)[^.]{0,30}(velocity|RV)[^.]{0,30}(variation|shift)|is a binary"),
    ("T07_giant_host",     r"(?i)\b(giant|subgiant|evolved)\b"),
    ("T08_ephemeris",      r"(?i)out of phase|wrong period|alias|harmonic"),
    ("T09_kepler_note",    r"(?i)ExoFOP-Kepler|\bKOI\s*\d"),
    ("T10_validated",      r"(?i)validat|confirmed planet|published"),
    ("T11_double_lined",   r"(?i)double-?lined binary"),
    # The same speckle boilerplate reaches us in a clean form and in a run-together form
    # ("…832nmNo secondary sources were detected.See…"). Both are sampled on purpose: the pair
    # is a controlled test of whether the glued negation flips a judgment. See WORKLOG 19:31Z.
    ("T12_glued_negation", r"nmNo secondary sources"),
]

# Topic cases are kept readable so every answer can genuinely be inspected by eye.
TOPIC_MAX_LEN = 2500


def load():
    con = duckdb.connect(str(DB), read_only=True)
    rows = con.execute(
        "select toi, tic_id, notes from analysis_set_obsnotes order by toi, tic_id"
    ).fetchall()
    con.close()
    return [{"toi": str(t), "tic": int(c), "text": n, "len": len(n)} for t, c, n in rows]


def build(rows):
    rng = random.Random(SEED)
    picked, used = [], set()

    for name, lo, hi, k in STRATA:
        pool = [r for r in rows if lo <= r["len"] < hi and (r["toi"], r["tic"]) not in used]
        pool.sort(key=lambda r: (r["toi"], r["tic"]))
        for r in rng.sample(pool, min(k, len(pool))):
            used.add((r["toi"], r["tic"]))
            picked.append({"stratum": name, **r})

    for name, rx in TOPICS:
        pat = re.compile(rx)
        pool = [r for r in rows
                if r["len"] <= TOPIC_MAX_LEN
                and (r["toi"], r["tic"]) not in used
                and pat.search(r["text"])]
        pool.sort(key=lambda r: (r["toi"], r["tic"]))
        if not pool:
            print(f"  !! {name}: no match under {TOPIC_MAX_LEN} chars")
            continue
        r = rng.choice(pool)
        used.add((r["toi"], r["tic"]))
        picked.append({"stratum": name, **r})

    picked.sort(key=lambda r: (r["stratum"], r["toi"]))
    for i, r in enumerate(picked, 1):
        r["cid"] = f"B{i:02d}"
    return picked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unblind", action="store_true",
                    help="print the labels; run ONLY after every answer has been inspected")
    args = ap.parse_args()

    rows = load()
    cases = build(rows)

    if args.unblind:
        con = duckdb.connect(str(DB), read_only=True)
        print(f"{'cid':5s} {'toi':10s} {'tic':>12s} {'len':>7s}  y")
        for c in cases:
            y = con.execute(
                "select y from analysis_set_obsnotes where toi=? and tic_id=?",
                [c["toi"], c["tic"]]).fetchone()[0]
            print(f"{c['cid']:5s} {c['toi']:10s} {c['tic']:12d} {c['len']:7d}  {y}")
        con.close()
        return

    OUT.parent.mkdir(parents=True, exist_ok=True)
    # The label is deliberately absent from this file. That absence is the blinding.
    OUT.write_text(json.dumps(
        {"seed": SEED, "n": len(cases), "blinded": True,
         "note": "y is intentionally omitted; see scripts/031_gate_cases_obsnotes.py",
         "cases": [{k: c[k] for k in ("cid", "stratum", "toi", "tic", "len", "text")}
                   for c in cases]}, indent=2))
    print(f"{len(cases)} blinded cases -> {OUT.relative_to(ROOT)}")
    for c in cases:
        print(f"  {c['cid']}  {c['stratum']:12s} TOI {c['toi']:10s} {c['len']:6d} ch")


if __name__ == "__main__":
    main()
