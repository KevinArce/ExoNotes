"""Question-design gate for ExoNotes (PLAN.md §6 Step 2.5).

Every case below is a REAL comment taken verbatim from `analysis_set`, sampled across the
true length distribution (p50 = 30 chars). Hand-written prose was the flaw in the previous
round (research/04) and is deliberately absent here.

For each question in PLAN.md §5 the set carries its clear positive, its clear negative, and
its nearest confusable -- the case a sloppy question gets wrong.

Run:  .venv/bin/python scripts/025_question_gate.py
Idempotent: yes. Responses are cached on sha256(model + version + state + questions) under
data/cache/, so re-running costs nothing. Bump QUESTION_SET_VERSION to force a real re-test.
"""
import hashlib
import http.client
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache" / "gate"
OUTDIR = ROOT / "research" / "data"

MODEL = "jev-latest"

# Decision thresholds for the gate. A Noul between these is a coin flip and fails:
# a near-0.5 column is noise in the feature matrix, which is what this gate exists to stop.
YES_MIN = 0.70
NO_MAX = 0.30

for line in (ROOT / ".env").read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ[k.strip()] = v.strip().strip('"').strip("'")

KEY = os.environ.get("TYPESAFE_API_KEY", "")
if not KEY:
    raise SystemExit("no TYPESAFE_API_KEY found")


sys.path.insert(0, str(ROOT / "src"))
from exonotes.questions import (  # noqa: E402
    QUESTION_SET_VERSION, QUESTIONS, TIER_LABEL_ECHO, TIER_PREDICTIVE)



Y, N = "Y", "N"

# ---------------------------------------------------------------------------
# Cases. Every `text` is verbatim from analysis_set; `toi` and `y` are its real values.
# `expect` asserts only what the TEXT SAYS. Questions not listed are inspected by eye.
# Score expectations are (lo, hi) bounds on the returned score.
# ---------------------------------------------------------------------------
CASES = [
    dict(cid="C01", toi="624.01", y=1, role="bare designation (leakage channel)",
         text="HAT-P-70 b",
         expect={"contains_object_designation": Y, "indicates_confirmed_planet": N,
                 "indicates_retired_or_rejected": N, "reports_offset_eclipsing_binary": N,
                 "describes_transit_morphology": N, "evidence_depth": (0, 1.0)}),
    dict(cid="C02", toi="154.01", y=0, role="pure label echo, no object named",
         text="TFOP FP",
         expect={"indicates_retired_or_rejected": Y, "contains_object_designation": N,
                 "indicates_confirmed_planet": N, "reports_offset_eclipsing_binary": N,
                 "mentions_spectroscopic_binary": N}),
    dict(cid="C03", toi="2492.01", y=0, role="most common comment in corpus (308 rows); provenance only",
         text="found in faint-star QLP search",
         expect={"contains_object_designation": N, "indicates_retired_or_rejected": N,
                 "describes_transit_morphology": N, "mentions_instrumental_artifact": N,
                 "reports_stellar_companion_or_blend": N, "evidence_depth": (0, 1.6)}),
    dict(cid="C04", toi="1752.02", y=1, role="terse fragment named in the handoff",
         text="low SNR; potential multi",
         expect={"mentions_instrumental_artifact": N, "describes_transit_morphology": N,
                 "contains_object_designation": N, "indicates_retired_or_rejected": N,
                 "author_certainty": (0, 2.2)}),
    dict(cid="C05", toi="2215.01", y=1, role="crowded field = blend positive",
         text="variable host; crowded field; L1 candidate",
         expect={"reports_stellar_companion_or_blend": Y, "reports_offset_eclipsing_binary": N,
                 "mentions_spectroscopic_binary": N, "indicates_retired_or_rejected": N}),
    dict(cid="C06", toi="3357.01", y=0, role="CONFUSABLE: tool failure is not an instrumental attribution",
         text="centroid plot failed",
         expect={"mentions_instrumental_artifact": N, "reports_stellar_companion_or_blend": N,
                 "indicates_retired_or_rejected": N, "describes_transit_morphology": N,
                 "evidence_depth": (0, 1.6)}),
    dict(cid="C07", toi="849.01", y=1, role="terse morphology positive",
         text="flat-bottomed",
         expect={"describes_transit_morphology": Y, "reports_offset_eclipsing_binary": N,
                 "contains_object_designation": N, "indicates_retired_or_rejected": N}),
    dict(cid="C08", toi="1513.01", y=0, role="CONFUSABLE: depth-aperture = blend, not morphology, not artifact",
         text="Slight depth-aperture correlation",
         expect={"reports_stellar_companion_or_blend": Y, "mentions_instrumental_artifact": N,
                 "describes_transit_morphology": N, "indicates_retired_or_rejected": N}),
    dict(cid="C09", toi="591.01", y=0, role="CONFUSABLE: EB on the target itself; problem stated but no retirement",
         text="8.5 day signal is EB",
         expect={"reports_offset_eclipsing_binary": N, "indicates_retired_or_rejected": N,
                 "mentions_spectroscopic_binary": N, "reports_stellar_companion_or_blend": N}),
    dict(cid="C10", toi="217.01", y=0, role="2nd most common comment (46 rows); NEB + retirement",
         text="TFOP FP; retired as NEB",
         expect={"reports_offset_eclipsing_binary": Y, "indicates_retired_or_rejected": Y,
                 "mentions_spectroscopic_binary": N, "contains_object_designation": N,
                 "describes_transit_morphology": N}),
    dict(cid="C11", toi="276.01", y=0, role="terse SB positive; CONFUSABLE for offset EB",
         text="TFOP FP/SB1",
         expect={"mentions_spectroscopic_binary": Y, "indicates_retired_or_rejected": Y,
                 "reports_offset_eclipsing_binary": N, "contains_object_designation": N}),
    dict(cid="C12", toi="1799.01", y=1, role="artifact positive, hedged",
         text="low SNR; possible instrument or systematic",
         expect={"mentions_instrumental_artifact": Y, "indicates_retired_or_rejected": N,
                 "describes_transit_morphology": N, "author_certainty": (0, 2.2)}),
    dict(cid="C13", toi="262.01", y=1, role="CONFUSABLE: confirmation stated with no designation",
         text="validated planet",
         expect={"indicates_confirmed_planet": Y, "contains_object_designation": N,
                 "indicates_retired_or_rejected": N, "describes_transit_morphology": N}),
    dict(cid="C14", toi="815.02", y=1, role="ephemeris problem positive, hedged",
         text="real period likely shorter than max period of ~734.4987 d",
         expect={"asserts_ephemeris_problem": Y, "indicates_retired_or_rejected": N,
                 "reports_offset_eclipsing_binary": N}),
    dict(cid="C15", toi="1052.01", y=1, role="CONFUSABLE: period mentioned, no problem asserted",
         text="Low priority; similar epoch and period from sector 1",
         expect={"asserts_ephemeris_problem": N, "indicates_retired_or_rejected": N,
                 "reports_stellar_companion_or_blend": N, "describes_transit_morphology": N}),
    dict(cid="C16", toi="397.01", y=0, role="companion + NEB + retirement + bare TIC",
         text="close companion star 219379014; TFOP FP; retired as NEB",
         expect={"reports_stellar_companion_or_blend": Y, "reports_offset_eclipsing_binary": Y,
                 "indicates_retired_or_rejected": Y, "contains_object_designation": Y,
                 "mentions_spectroscopic_binary": N}),
    dict(cid="C17", toi="1990.01", y=0, role="CONFUSABLE: EB retired on target, crowded field, secondary",
         text="Crowded field; secondary; synchronized; TFOP FP; retired as EB",
         expect={"describes_transit_morphology": Y, "reports_stellar_companion_or_blend": Y,
                 "indicates_retired_or_rejected": Y, "reports_offset_eclipsing_binary": N,
                 "mentions_spectroscopic_binary": N}),
    dict(cid="C18", toi="5540.01", y=0, role="multi-fact: 2x period + odd-even + NEB + retirement",
         text="possibly too large for period; short period; significant odd-even at 2x previous period (0.55 d); retired as TFOP FP/NEB",
         expect={"asserts_ephemeris_problem": Y, "describes_transit_morphology": Y,
                 "reports_offset_eclipsing_binary": Y, "indicates_retired_or_rejected": Y,
                 "mentions_spectroscopic_binary": N}),
    dict(cid="C19", toi="729.01", y=0, role="artifact positive (asteroid) with a data product referenced",
         text="likely asteroid based on difference image in s9; no additional events; retired as TFOP FA",
         expect={"mentions_instrumental_artifact": Y, "indicates_retired_or_rejected": Y,
                 "reports_offset_eclipsing_binary": N, "evidence_depth": (1.5, 4.0)}),
    dict(cid="C20", toi="128.01", y=1, role="confirmation + designation + paper",
         text="TOI-128.01; validated planet from Hord et al 2024; Rp underestimated",
         expect={"indicates_confirmed_planet": Y, "contains_object_designation": Y,
                 "indicates_retired_or_rejected": N, "reports_offset_eclipsing_binary": N}),
    dict(cid="C21", toi="261.01", y=1, role="CONFUSABLE: 'active TFOP PC' is a status, not a rejection",
         text="TOI 261.01; active TFOP PC; validated planet in S Giacalone 2020",
         expect={"indicates_confirmed_planet": Y, "contains_object_designation": Y,
                 "indicates_retired_or_rejected": N, "mentions_instrumental_artifact": N}),
    dict(cid="C22", toi="4135.01", y=0, role="CONFUSABLE: hedged NEB, no retirement stated, depth-aperture",
         text="found in faint-star QLP search; significant centroid offset and depth aperture correlation; likely NEB",
         expect={"reports_offset_eclipsing_binary": Y, "reports_stellar_companion_or_blend": Y,
                 "mentions_instrumental_artifact": N, "indicates_retired_or_rejected": N,
                 "author_certainty": (0, 2.6)}),
    dict(cid="C23", toi="953.01", y=0, role="SB positive via RV; CONFUSABLE: 'WASP-South' is a survey, not a planet",
         text="SB1 from WASP-South SB1 RV variation=30 km/s",
         expect={"mentions_spectroscopic_binary": Y, "contains_object_designation": N,
                 "reports_offset_eclipsing_binary": N, "indicates_retired_or_rejected": N}),
]


def call(state, questions):
    """POST one state with all questions. Cached content-addressed; cache hits cost nothing."""
    payload = {"model": MODEL, "state": state, "questions": questions}
    key = hashlib.sha256(
        (MODEL + QUESTION_SET_VERSION
         + json.dumps(state, sort_keys=False, separators=(",", ":"))
         + json.dumps(questions, sort_keys=True, separators=(",", ":"))).encode()).hexdigest()
    CACHE.mkdir(parents=True, exist_ok=True)
    hit = CACHE / f"{key}.json"
    if hit.exists():
        return json.loads(hit.read_text()), 0.0, True
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.typesafe.ai/v1/systemone", data=body,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    t0 = time.time()
    # Retry connection-level failures too, not just HTTP status codes. A bare
    # `except HTTPError` misses RemoteDisconnected / URLError / socket timeouts,
    # which is how round 3 of this gate died mid-run on 2026-09-20.
    transient = (urllib.error.URLError, http.client.RemoteDisconnected,
                 ConnectionError, TimeoutError)
    last = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                out = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            sys.stderr.write(f"HTTP {e.code}: {e.read().decode()[:400]}\n")
            raise
        except transient as e:
            last = e
            if attempt < 4:
                sys.stderr.write(f"  transient {type(e).__name__}, retry {attempt + 1}/4\n")
                time.sleep(2 ** attempt)
                continue
            raise
    else:
        raise RuntimeError(f"exhausted retries: {last!r}")
    hit.write_text(json.dumps(out, indent=2))
    return out, (time.time() - t0) * 1000, False


def verdict(qid, ans, want):
    """Return (ok, rendered) for one asserted answer."""
    if ans["type"] == "noul":
        v = ans["noul"]
        if want == Y:
            return v >= YES_MIN, f"{v:.2f}"
        return v <= NO_MAX, f"{v:.2f}"
    v = ans["score"]
    lo, hi = want
    return lo <= v <= hi, f"{v:.2f}"


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    raw, fails, n_new, tok = {}, [], 0, 0
    print(f"question set {QUESTION_SET_VERSION} · {len(QUESTIONS)} questions · {len(CASES)} real cases\n")

    for c in CASES:
        state = {"toi": f"TOI-{c['toi']}", "comment": c["text"]}  # fixed key order, as Step 3
        out, ms, cached = call(state, QUESTIONS)
        raw[c["cid"]] = {"case": c, "state": state, "response": out}
        if not cached:
            n_new += 1
            tok += out["usage"]["input_tokens"]
        mark = "cache" if cached else f"{ms:.0f}ms"
        print(f"=== {c['cid']}  y={c['y']}  [{len(c['text'])} ch, {mark}]  {c['role']}")
        print(f"    {c['text']}")
        for qid, ans in out["answers"].items():
            want = c["expect"].get(qid)
            if ans["type"] == "noul":
                shown = f"noul={ans['noul']:.2f}"
            else:
                shown = f"score={ans['score']:.2f} conf={ans['confidence']:.2f}"
            if want is None:
                print(f"      .    {qid:36s} {shown}")
                continue
            ok, _ = verdict(qid, ans, want)
            if not ok:
                fails.append((c["cid"], qid, want, shown, c["text"], c["role"]))
            print(f"      {'ok ' if ok else 'FAIL'} {qid:36s} {shown}   want={want}")
        print()

    stamp = time.strftime("%Y-%m-%d")
    path = OUTDIR / f"gate_{QUESTION_SET_VERSION}_{stamp}.json"
    path.write_text(json.dumps(raw, indent=2))

    n_assert = sum(len(c["expect"]) for c in CASES)
    print("=" * 78)
    print(f"{n_assert - len(fails)}/{n_assert} assertions passed · {len(fails)} FAILED")
    print(f"new API calls: {n_new} · input tokens: {tok:,} · cost: ${tok / 1e6 * 0.042:.5f}")
    print(f"raw -> {path.relative_to(ROOT)}")
    if fails:
        print("\n--- FAILURES ---")
        for cid, qid, want, got, text, role in fails:
            print(f"  {cid} {qid:36s} want={want} got={got}")
            print(f"      {text[:96]}")
            print(f"      role: {role}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
