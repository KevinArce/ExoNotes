"""P1 — score the registry at a checkpoint (PREREGISTRATION.md §11.14, A-45). $0, no model call.

    --checkpoint 6m | 12m | 18m | 24m
        The dates are fixed by A-45 45.7, and the script refuses to run before its date. 6m and
        12m are descriptive only. 18m is the confirmatory checkpoint. 24m exists only if 18m came
        back underpowered.
    --smoke signal | null
        Runs the whole machinery on a SYNTHETIC outcome drawn over the dry-run predictions
        (052 --dry-run), to prove it before any real outcome exists. `signal` draws the outcome
        from p_D, so D should win. `null` draws it at the base rate, so nothing should win.

Evaluation set (A-45 45.5): predicted TOIs that were PC/APC in 052's at-prediction snapshot and
are CP/KP (y=1) or FP/FA (y=0) in NEA `toi` at the checkpoint. Nothing else is scored.

Comparisons (A-45 45.4), each ΔAUC with a paired bootstrap of 10,000 resamples over TIC groups
(`026`'s code, imported unchanged):
    primary     D − B
    secondary   Dmeta − Bmeta (content beyond volume) · D − BTFIDF (structure beyond words) ·
                D − Bmeta (continuity with the retrospective study)
    sensitivity (a) drop TOIs whose TIC carried a labelled TOI at T0 · (b) drop rows whose frozen
                text fires a leakage clause (OBSNOTES_PATTERNS + K10-style survey names)
The reading is computed here, by A-45 45.8's table. It is not read off by hand.
"""
import argparse
import datetime
import hashlib
import importlib.util
import io
import json
import pathlib
import subprocess
import sys
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
RDATA = ROOT / "research" / "data"
PRAW = ROOT / "data" / "prospective" / "raw"
DRY = ROOT / "data" / "prospective" / "dryrun"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

CHECKPOINTS = {"6m": "2027-03-23", "12m": "2027-09-23", "18m": "2028-03-23", "24m": "2028-09-23"}
CONFIRMATORY = {"18m", "24m"}
N_MIN = 200            # A-45 45.8: where the retrospective +0.0432 is detectable at 80% power
N_BOOT = 10_000
PUBLISH_WINDOW_H = 24  # A-45 45.1: predictions pushed within 24 h of the 052 run

_s = importlib.util.spec_from_file_location("nf", ROOT / "scripts" / "026_noise_floor.py")
nf = importlib.util.module_from_spec(_s)
_s.loader.exec_module(nf)

COMPARISONS = [("primary", "D", "B"), ("content", "Dmeta", "Bmeta"),
               ("structure", "D", "BTFIDF"), ("continuity", "D", "Bmeta")]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True,
                          text=True).stdout


def load_predictions(smoke: bool) -> tuple[pd.DataFrame, dict, dict]:
    base = DRY if smoke else RDATA
    csv_p, meta_p = base / "prospective_predictions_t0.csv", base / "prospective_predictions_t0.json"
    meta = json.loads(meta_p.read_text())
    digest = hashlib.sha256(csv_p.read_bytes()).hexdigest()
    if digest != meta["predictions_sha256"]:
        raise SystemExit(f"REFUSING: predictions sha256 {digest[:16]} != recorded "
                         f"{meta['predictions_sha256'][:16]}. The file changed after publication.")
    audit = {"predictions_sha256": digest}
    if not smoke:
        git("fetch", "--quiet", "origin")
        rel = str(csv_p.relative_to(ROOT))
        first = git("log", "origin/master", "--diff-filter=A", "--format=%H %cI", "--", rel).split()
        if not first:
            raise SystemExit(f"REFUSING: {rel} is not on origin/master, so it was never published.")
        sha, t_pub = first[-2], first[-1]
        pub = datetime.datetime.fromisoformat(t_pub)
        made = datetime.datetime.fromisoformat(meta["predicted_utc"].replace("Z", "+00:00"))
        audit |= {"published_commit": sha, "t_pub": t_pub,
                  "hours_from_prediction_to_publication": round((pub - made).total_seconds() / 3600, 2)}
        audit["publication_window_met"] = audit["hours_from_prediction_to_publication"] <= PUBLISH_WINDOW_H
    return pd.read_csv(csv_p), meta, audit


def disposition_at(checkpoint: str, smoke: bool) -> tuple[pd.DataFrame, str]:
    path = (DRY if smoke else PRAW) / f"nea_toi_{checkpoint}.csv"
    if not path.exists():
        q = urllib.parse.urlencode({"query": "select toi, tfopwg_disp from toi", "format": "csv"})
        with urllib.request.urlopen(f"{TAP}?{q}", timeout=600) as r:
            txt = r.read().decode()
        if "tfopwg_disp" not in txt.splitlines()[0]:
            raise SystemExit(f"TAP did not return the toi table: {txt[:200]}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(txt)
    d = pd.read_csv(path)
    d["toi"] = pd.to_numeric(d.toi, errors="coerce")
    return d, hashlib.sha256(path.read_bytes()).hexdigest()


def compare(ev: pd.DataFrame, x: str, base: str) -> dict:
    y, g = ev.y.to_numpy(), ev.tic_id.to_numpy()
    PX, PB = ev[f"p_{x}"].to_numpy()[None, :], ev[f"p_{base}"].to_numpy()[None, :]
    lo, hi, se = nf.paired_group_bootstrap(PB, PX, y, g, N_BOOT)
    a_x, a_b = nf.score(PX, y), nf.score(PB, y)
    return {"arm": x, "vs": base, "auc_arm": a_x, "auc_vs": a_b, "dauc": a_x - a_b,
            "ci_lo": lo, "ci_hi": hi, "se": se, "mde80": nf.Z80 * se,
            "brier_arm": float(np.mean((ev[f"p_{x}"] - y) ** 2)),
            "brier_vs": float(np.mean((ev[f"p_{base}"] - y) ** 2))}


def evaluate(ev: pd.DataFrame) -> dict:
    out = {"n": len(ev), "tic": int(ev.tic_id.nunique()), "base_rate": float(ev.y.mean())}
    if len(ev) < 10 or ev.y.nunique() < 2:
        out["note"] = "too few resolved TOIs, or only one class: no comparison computed"
        return out
    out["comparisons"] = {name: compare(ev, x, b) for name, x, b in COMPARISONS}
    return out


def reading(checkpoint: str, res: dict) -> str:
    """A-45 45.8's table."""
    if checkpoint not in CONFIRMATORY:
        return "INTERIM: descriptive only, no test is read at this checkpoint (A-45 45.7)"
    n = res["n"]
    if n < N_MIN:
        return ("UNDERPOWERED at 18m: n < 200. Extend once to 24m (A-45 45.8)" if checkpoint == "18m"
                else "INCONCLUSIVE: still n < 200 at the final checkpoint. Report estimates, claim nothing")
    p = res["comparisons"]["primary"]
    if p["ci_lo"] > 0:
        head = "CONFIRMED PROSPECTIVELY: D beats B"
    elif p["ci_hi"] < 0:
        head = "REVERSED: D is worse than B prospectively"
    else:
        head = "NOT CONFIRMED PROSPECTIVELY: D vs B includes zero"
    c = res["comparisons"]["content"]
    tail = ("content beyond volume confirmed (Dmeta − Bmeta excludes zero, above it)"
            if c["ci_lo"] > 0 else "content beyond volume NOT confirmed (Dmeta − Bmeta)")
    return f"{head}; {tail}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--checkpoint", choices=list(CHECKPOINTS), default="18m")
    ap.add_argument("--smoke", choices=["signal", "null"])
    a = ap.parse_args()
    smoke = a.smoke is not None
    cp = a.checkpoint

    if not smoke:
        today = datetime.datetime.now(datetime.UTC).date().isoformat()
        if today < CHECKPOINTS[cp]:
            raise SystemExit(f"REFUSING: checkpoint {cp} is {CHECKPOINTS[cp]}; today is {today} (A-45 45.7).")
        if cp == "24m":
            prior = RDATA / "prospective_eval_18m.json"
            if not prior.exists() or json.loads(prior.read_text())["overall"]["n"] >= N_MIN:
                raise SystemExit("REFUSING: 24m runs only if 18m was run and came back underpowered.")

    pred, meta, audit = load_predictions(smoke)
    pred = pred[pred.open_at_prediction].copy()
    if smoke:
        rng = np.random.default_rng(20260923)
        pick = rng.choice(len(pred), size=min(300, len(pred)), replace=False)
        ev = pred.iloc[np.sort(pick)].copy()
        p = ev.p_D.to_numpy() if a.smoke == "signal" else np.full(len(ev), 0.45)
        ev["y"] = (rng.uniform(size=len(ev)) < p).astype(int)
        disp_sha = "synthetic"
    else:
        disp, disp_sha = disposition_at(cp, smoke)
        now = pred.toi.map(disp.set_index("toi").tfopwg_disp)
        ev = pred[now.isin(["CP", "KP", "FP", "FA"])].copy()
        ev["y"] = now[ev.index].isin(["CP", "KP"]).astype(int)
        ev["disp_at_checkpoint"] = now[ev.index]

    res = {
        "registration": "PREREGISTRATION.md §11.14 (A-45)",
        "checkpoint": cp, "checkpoint_date": CHECKPOINTS[cp],
        "smoke": a.smoke, "run_utc": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
        "audit": audit, "nea_toi_at_checkpoint_sha256": disp_sha,
        "open_at_prediction": int(len(pred)),
        "overall": evaluate(ev),
        "sensitivity": {
            "no_shared_tic": evaluate(ev[~ev.tic_has_labelled_toi.astype(bool)]),
            "no_leak_clause": evaluate(ev[~ev.leak_clause.astype(bool)]),
        },
    }
    res["reading"] = reading(cp, res["overall"]) if "comparisons" in res["overall"] else \
        ("INCONCLUSIVE: " + res["overall"]["note"])
    if not smoke and not audit.get("publication_window_met", True):
        res["reading"] += (" | FLAG: the predictions were published more than 24 h after they were "
                           "made (A-45 45.1). Reported, not excluded.")

    target = DRY if smoke else RDATA
    out_p = target / f"prospective_eval_{cp}{'_smoke_' + a.smoke if smoke else ''}.json"
    out_p.write_text(json.dumps(res, indent=2, default=float) + "\n")

    o = res["overall"]
    print(f"checkpoint {cp} ({CHECKPOINTS[cp]}){'  SMOKE: ' + a.smoke if smoke else ''}")
    print(f"open at prediction {res['open_at_prediction']:,} · resolved and scored n={o['n']} "
          f"({o['tic']} TIC, base {o['base_rate']:.3f})")
    for name, c in o.get("comparisons", {}).items():
        print(f"  {name:<11} {c['arm']:>6} − {c['vs']:<6} {c['dauc']:+.4f} "
              f"[{c['ci_lo']:+.4f}, {c['ci_hi']:+.4f}]  MDE {c['mde80']:.4f}")
    for k, s in res["sensitivity"].items():
        c = s.get("comparisons", {}).get("primary")
        if c:
            print(f"  sensitivity {k:<15} n={s['n']:<4} D − B {c['dauc']:+.4f} [{c['ci_lo']:+.4f}, {c['ci_hi']:+.4f}]")
    print(f"READING: {res['reading']}")
    print(f"wrote {out_p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
