"""Build the LABEL-BLINDED case set for the Kepler question gate (A-40 40.11 item 1; A-22's form).

The Kepler analogue of scripts/031_gate_cases_obsnotes.py, over CFOP host texts:

  * cases are selected PROGRAMMATICALLY -- by length stratum and by over-broad topic regex --
    with a fixed seed, never by hand-picking a text that "looks good";
  * one case per HOST: Jev's state is {"notes": host text}, so a host is the unit a question
    is ever asked about, whatever number of KOIs share it;
  * the emitted case file carries cid / host / stratum / len / text and **no label**;
  * labels are read only by `--unblind`, run after every answer has been inspected.

Run:  .venv/bin/python scripts/046_kepler_gate_cases.py            # write the blinded cases
      .venv/bin/python scripts/046_kepler_gate_cases.py --holdout  # a disjoint holdout set
      .venv/bin/python scripts/046_kepler_gate_cases.py --holdout2 # a second, disjoint from both
      .venv/bin/python scripts/046_kepler_gate_cases.py --unblind  # after inspection only

`--holdout` exists because the question set was repaired (r1 -> r2) on the main cases, so
passing them is partly a fit. It draws a fresh set -- new seed, two per length stratum plus five
trap topics, every host disjoint from the main set -- whose expectations are written before the
repaired set ever sees them. `--holdout2` exists because r2 failed holdout-1 and was repaired
again (r3) on it, so holdout-1 became a repair set too; holdout-2 decides the freeze under the
acceptance rule fixed in WORKLOG before any r3 answer existed.

Idempotent: yes. Read-only against data/kepler.duckdb, fixed seed, deterministic output.
"""
import argparse, json, pathlib, random, re

import duckdb

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "kepler.duckdb"
OUT = ROOT / "research" / "data" / "gate_cases_kepler_2026-09-21.json"
HOLDOUT = ROOT / "research" / "data" / "gate_cases_kepler_holdout_2026-09-21.json"
HOLDOUT2 = ROOT / "research" / "data" / "gate_cases_kepler_holdout2_2026-09-21.json"
SEED, HOLDOUT_SEED, HOLDOUT2_SEED = 20260921, 20260922, 20260923
HOLDOUT_TOPICS = ("T04_companion_flag", "T07_sb2_double", "T08_large_var", "T09_no_var",
                  "T10_looks_good")

# Host-text length runs p10 101 / p50 159 / p90 1,246 / p99 8,159 / max 43,412. jev-1.13
# documents accuracy loss on large states full of irrelevant detail, so the long tail is
# over-sampled relative to its density, as 031 did.
STRATA = [
    ("S1_short",       0,   120, 3),
    ("S2_median",    120,   300, 3),
    ("S3_typical",   300,  1200, 3),
    ("S4_long",     1200,  5000, 3),
    ("S5_verylong", 5000, 10**9, 3),
]

# One case per topic, so every question meets a positive and its nearest confusable. These
# regexes select SUBJECT MATTER, deliberately over-broad; they do not decide any answer.
TOPICS = [
    ("T01_roboao_clean",   r"No companions detected within"),
    ("T02_lick_mixed",     r"No companions visible from.{0,200}There is a companion"),
    ("T03_nearby_stars",   r"Nearby stars detected"),
    ("T04_companion_flag", r"Possible nearby companion = Yes"),
    ("T05_speckle_double", r"found to be double"),
    ("T06_guider_only",    r"guider snap"),
    ("T07_sb2_double",     r"(?i)\bSB2\b|double-?(?:lined|peaked)"),
    ("T08_large_var",      r"(?i)large velocity variation"),
    ("T09_no_var",         r"(?i)no (?:significant )?velocity variation"),
    ("T10_looks_good",     r"(?i)looks good"),
    ("T11_recon_done",     r"(?i)no more recon"),
    ("T12_precise_rv",     r"(?i)precise velocities"),
    ("T13_kebc_flag",      r"Possible eclipsing binary = Yes"),
    ("T14_fp_yes",         r"Possible false positive = Yes"),
    ("T15_fp_no",          r"Possible false positive = No"),
    ("T16_published",      r"(?i)accepted in|published|validat"),
]
TOPIC_MAX_LEN = 2500


def load():
    with duckdb.connect(str(DB), read_only=True) as con:
        return con.execute("""
            select host, any_value(text) as notes, any_value(n_chars) as n
            from kepler_cfop_corpus group by host order by host""").fetchall()


def build(rows, seed=SEED, exclude=(), per_stratum=None, topics=None, prefix=""):
    rng = random.Random(seed)
    used, cases = set(exclude), []
    for name, lo, hi, k in STRATA:
        pool = [r for r in rows if lo <= r[2] < hi and r[0] not in used]
        for i, (host, text, n) in enumerate(rng.sample(pool, per_stratum or k), 1):
            used.add(host)
            cases.append(dict(cid=f"{prefix}{name}_{i}", stratum=name, host=host, len=n, text=text))
    for name, rx in TOPICS:
        if topics is not None and name not in topics:
            continue
        pool = [r for r in rows if r[0] not in used and r[2] <= TOPIC_MAX_LEN and re.search(rx, r[1])]
        if not pool:
            print(f"  topic {name}: no host within {TOPIC_MAX_LEN} chars -- skipped")
            continue
        host, text, n = rng.choice(pool)
        used.add(host)
        cases.append(dict(cid=f"{prefix}{name}", stratum=name, host=host, len=n, text=text))
    return cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unblind", action="store_true", help="print labels; ONLY after inspection")
    ap.add_argument("--holdout", action="store_true", help="write the disjoint holdout case set")
    ap.add_argument("--holdout2", action="store_true", help="write the second disjoint holdout set")
    a = ap.parse_args()
    if a.holdout2 and not a.unblind:
        prior = {c["host"] for f in (OUT, HOLDOUT) for c in json.loads(f.read_text())["cases"]}
        cases = build(load(), seed=HOLDOUT2_SEED, exclude=prior, per_stratum=2,
                      topics=HOLDOUT_TOPICS, prefix="H2_")
        assert not prior & {c["host"] for c in cases}
        HOLDOUT2.write_text(json.dumps({"seed": HOLDOUT2_SEED, "label_blinded": True,
                                        "disjoint_from": [OUT.name, HOLDOUT.name],
                                        "cases": cases}, indent=2))
        print(f"{len(cases)} blinded HOLDOUT-2 cases -> {HOLDOUT2.relative_to(ROOT)}")
        for c in cases:
            print(f"  {c['cid']:24s} host {c['host']:5d}  {c['len']:6,} ch")
        return 0
    if a.holdout and not a.unblind:
        main_hosts = {c["host"] for c in json.loads(OUT.read_text())["cases"]}
        cases = build(load(), seed=HOLDOUT_SEED, exclude=main_hosts, per_stratum=2,
                      topics=HOLDOUT_TOPICS, prefix="H_")
        assert not main_hosts & {c["host"] for c in cases}
        HOLDOUT.write_text(json.dumps({"seed": HOLDOUT_SEED, "label_blinded": True,
                                       "disjoint_from": OUT.name, "cases": cases}, indent=2))
        print(f"{len(cases)} blinded HOLDOUT cases -> {HOLDOUT.relative_to(ROOT)}")
        for c in cases:
            print(f"  {c['cid']:24s} host {c['host']:5d}  {c['len']:6,} ch")
        return 0
    if a.unblind:
        cases = json.loads((HOLDOUT if a.holdout else OUT).read_text())["cases"]
        with duckdb.connect(str(DB), read_only=True) as con:
            for c in cases:
                ys = con.execute("select kepoi_name, y from kepler_cfop_corpus where host = ? "
                                 "order by kepoi_name", [c["host"]]).fetchall()
                print(f"{c['cid']:22s} host {c['host']:5d}  " + ", ".join(f"{k}:{y}" for k, y in ys))
        return 0
    cases = build(load())
    OUT.write_text(json.dumps({"seed": SEED, "label_blinded": True, "cases": cases}, indent=2))
    print(f"{len(cases)} blinded cases -> {OUT.relative_to(ROOT)}")
    for c in cases:
        print(f"  {c['cid']:22s} host {c['host']:5d}  {c['len']:6,} ch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
