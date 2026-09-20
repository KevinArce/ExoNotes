"""Derive and measure the G5 clause set on observer-note text (TASK B2; A-3; §5, §11.4).

`src/exonotes/leakage.py`'s `OBSNOTES_PATTERNS` is the pre-registered artifact; this script
is the measurement that stands behind it. It reports, per clause, n and P(y=1) exactly as
§5 does, plus the MARGINAL count (rows that clause strips alone), which is what the §5 eye
audit is performed on.

It also enforces the §5.1 tripwire: L5 must fire on ZERO rows, because the Groupname corpus
filter is supposed to have removed every note carrying an explicit disposition field. If L5
fires, that is a pipeline bug, not a finding, and Step 3 must stop.

Run:  .venv/bin/python scripts/033_leakage_obsnotes.py
      .venv/bin/python scripts/033_leakage_obsnotes.py --audit L6_archive_provenance
Idempotent: yes. Read-only against the corpus; CREATE OR REPLACE on its own output tables.
"""
import argparse
import json
import pathlib
import sys

import duckdb

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "exonotes.duckdb"
OUT = ROOT / "research" / "data" / "leakage_obsnotes_2026-09-20.json"

sys.path.insert(0, str(ROOT / "src"))
from exonotes.leakage import OBSNOTES_PATTERNS, TRIPWIRE  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", help="print the marginal rows for one clause, for the eye audit")
    ap.add_argument("--n", type=int, default=15)
    args = ap.parse_args()

    con = duckdb.connect(str(DB), read_only=bool(args.audit))
    rows = con.execute(
        "select cast(toi as varchar), tic_id, notes, y from analysis_set_obsnotes"
    ).fetchall()
    n_all = len(rows)
    base = sum(r[3] for r in rows) / n_all

    fired = {name: [r for r in rows if rx.search((r[2] or "").strip())]
             for name, rx in OBSNOTES_PATTERNS.items()}

    if args.audit:
        name = args.audit
        if name not in OBSNOTES_PATTERNS:
            raise SystemExit(f"unknown clause {name!r}; have {list(OBSNOTES_PATTERNS)}")
        rx = OBSNOTES_PATTERNS[name]
        others = [v for k, v in OBSNOTES_PATTERNS.items() if k != name]
        only = [r for r in fired[name]
                if not any(o.search((r[2] or "").strip()) for o in others)]
        print(f"{name}: {len(fired[name])} fire, {len(only)} MARGINAL (this clause alone)\n")
        for toi, tic, text, y in only[:args.n]:
            m = rx.search(text.strip())
            ctx = text[max(0, m.start() - 90):m.end() + 90].strip()
            print(f"  TOI {toi:10s} y={y}  ...{ctx}...")
        return 0

    # --- §5.1 tripwire, checked before anything else is reported ----------------------
    if fired[TRIPWIRE]:
        bad = fired[TRIPWIRE]
        print(f"!!! TRIPWIRE {TRIPWIRE} FIRED ON {len(bad)} ROWS !!!", file=sys.stderr)
        for toi, tic, text, y in bad[:5]:
            print(f"    TOI {toi} TIC {tic}", file=sys.stderr)
        raise SystemExit(
            "The Groupname corpus filter has failed: an explicit disposition field reached "
            "the observer-note corpus. This is a PIPELINE BUG, not a finding. Step 3 STOPS "
            "(PREREGISTRATION.md §5.1).")

    print(f"corpus n={n_all}  base={base:.4f}\n")
    print(f'{"clause":34s} {"n":>6s} {"%":>6s} {"P(y=1)":>8s} {"marginal":>9s}')
    print("-" * 70)
    per_clause = {}
    for name, hits in fired.items():
        n = len(hits)
        p = (sum(h[3] for h in hits) / n) if n else None
        others = [v for k, v in OBSNOTES_PATTERNS.items() if k != name]
        only = [r for r in hits if not any(o.search((r[2] or "").strip()) for o in others)]
        per_clause[name] = {"n": n, "pct": 100 * n / n_all, "p_y1": p, "marginal": len(only)}
        ps = f"{p:8.3f}" if p is not None else f'{"-":>8s}'
        print(f"{name:34s} {n:6d} {100 * n / n_all:5.1f}% {ps} {len(only):9d}")

    stripped = [r for r in rows
                if any(rx.search((r[2] or "").strip()) for rx in OBSNOTES_PATTERNS.values())]
    arm = [r for r in rows
           if not any(rx.search((r[2] or "").strip()) for rx in OBSNOTES_PATTERNS.values())]
    arm_tic = len(set(r[1] for r in arm))
    print("-" * 70)
    print(f'{"ANY (stripped)":34s} {len(stripped):6d} {100 * len(stripped) / n_all:5.1f}% '
          f'{sum(r[3] for r in stripped) / len(stripped):8.3f}')
    print(f'{"G5 ARM (survivors)":34s} {len(arm):6d} {100 * len(arm) / n_all:5.1f}% '
          f'{sum(r[3] for r in arm) / len(arm):8.3f}   {arm_tic} TIC')

    # Sensitivity: L6 strips on provenance rather than on a disposition statement, so the
    # arm is reported both ways. §11.4 registers the WITH-L6 arm as the G5 arm.
    no6 = {k: v for k, v in OBSNOTES_PATTERNS.items() if k != "L6_archive_provenance"}
    arm6 = [r for r in rows if not any(rx.search((r[2] or "").strip()) for rx in no6.values())]
    print(f'{"  sensitivity: arm without L6":34s} {len(arm6):6d} '
          f'{100 * len(arm6) / n_all:5.1f}% {sum(r[3] for r in arm6) / len(arm6):8.3f}   '
          f'{len(set(r[1] for r in arm6))} TIC')

    result = {
        "corpus": {"n": n_all, "base_rate": base},
        "clauses": per_clause,
        "stripped": {"n": len(stripped),
                     "p_y1": sum(r[3] for r in stripped) / len(stripped)},
        "g5_arm": {"n": len(arm), "tic": arm_tic,
                   "base_rate": sum(r[3] for r in arm) / len(arm)},
        "g5_arm_without_L6": {"n": len(arm6), "tic": len(set(r[1] for r in arm6)),
                              "base_rate": sum(r[3] for r in arm6) / len(arm6)},
        "tripwire": {"clause": TRIPWIRE, "fired": 0},
    }
    OUT.write_text(json.dumps(result, indent=2))

    con.execute("create or replace table leakage_obsnotes as select * from (values " +
                ",".join(f"('{k}',{v['n']},{v['p_y1'] if v['p_y1'] is not None else 'NULL'},"
                         f"{v['marginal']})" for k, v in per_clause.items()) +
                ") as t(clause, n, p_y1, marginal)")
    con.execute(
        "create or replace table g5_arm_obsnotes as "
        "select tic_id, toi, y from analysis_set_obsnotes where tic_id in " +
        "(" + ",".join(str(r[1]) for r in arm) + ")")
    con.close()
    print(f"\nraw -> {OUT.relative_to(ROOT)}  ·  duckdb::leakage_obsnotes, ::g5_arm_obsnotes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
