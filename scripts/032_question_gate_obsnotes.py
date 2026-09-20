"""Question-design gate on OBSERVER-NOTE text (TASK B; PLAN.md §6 Step 2.5; PREREGISTRATION §2).

The r4 gate ran on the TOI `Comments` field and does not transfer: observer notes are ~26x
longer, differently written, and built from reconnaissance-spectroscopy and speckle-imaging
reports rather than TFOP vetting shorthand. PREREGISTRATION.md §2 makes re-running this a
binding precondition of Step 3.

Differences from `scripts/025_question_gate.py`, each required by a registered amendment:
  A-4  state is {"notes": ...} -- `toi` is NOT sent
  A-5  MODEL is pinned to "jev-1.13.0" and response["model"] is asserted before persisting
  --   cases are label-blinded: they come from scripts/031_gate_cases_obsnotes.py, which
       emits no `y`, and EXPECT below was written from the text alone

Run:  .venv/bin/python scripts/032_question_gate_obsnotes.py
Idempotent: yes. Responses cached on sha256(model + version + state + questions) under
data/cache/gate_obsnotes/, so re-running costs nothing. Bump QUESTION_SET_VERSION to re-test.
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
CACHE = ROOT / "data" / "cache" / "gate_obsnotes"
OUTDIR = ROOT / "research" / "data"
CASES_PATH = OUTDIR / "gate_cases_obsnotes_2026-09-20.json"

# A-5: pinned. "jev-latest" sits inside the cache key, so an alias move would serve
# old-model hits beside new-model misses under an identical key.
MODEL = "jev-1.13.0"

# PREREGISTRATION §2.4 rule 6. A Noul between these is a coin flip and FAILS; a near-0.5
# column is noise in the feature matrix, which is what this gate exists to stop.
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
# Expectations. Written from the TEXT ONLY, with `y` withheld -- the case file carries no
# label and `--unblind` was not run until after every answer below was inspected.
# `expect` asserts only what the text SAYS. Questions not listed are inspected by eye.
# Score expectations are (lo, hi) bounds.
# ---------------------------------------------------------------------------
IMG_NO = "imaging_reports_no_companion"
IMG_YES = "imaging_reports_companion_present"
SP_NOT = "spectroscopy_indicates_nonplanetary_companion"
SP_PL = "spectroscopy_consistent_with_planet"
EVO = "host_star_described_as_evolved"
DONE = "followup_reported_concluded"
ONTGT = "reports_on_target_detection"
RETIRED = "indicates_retired_or_rejected"
CONF = "indicates_confirmed_planet"
DESIG = "contains_object_designation"

EXPECT = {
    # --- speckle boilerplate, RUN-TOGETHER form ("832nmNo secondary sources were detected")
    "B01": {IMG_NO: Y, IMG_YES: N, SP_NOT: N, SP_PL: N, EVO: N, DONE: N, ONTGT: N,
            RETIRED: N, CONF: N},
    "B02": {IMG_NO: Y, IMG_YES: N, SP_NOT: N, SP_PL: N, EVO: N, DONE: N, ONTGT: N,
            RETIRED: N, CONF: N},
    # --- ephemeris doubt, no designation, no imaging, hedged alternative
    "B03": {IMG_NO: N, IMG_YES: N, SP_NOT: N, SP_PL: N, EVO: N, DONE: N, ONTGT: N,
            RETIRED: N, CONF: N, DESIG: N},
    # --- TRES recon, evolved host, closure stated
    "B04": {EVO: Y, DONE: Y, SP_NOT: N, SP_PL: N, IMG_NO: N, IMG_YES: N, DESIG: Y,
            RETIRED: N, CONF: N, ONTGT: N},
    "B05": {EVO: Y, DONE: Y, SP_NOT: N, SP_PL: N, IMG_NO: N, IMG_YES: N, DESIG: Y,
            RETIRED: N, CONF: N},
    # --- CONFUSABLE: "SG1 reports that this is K2-133" is a designation, NOT a confirmation
    "B06": {EVO: N, DONE: Y, DESIG: Y, CONF: N, IMG_NO: N, IMG_YES: N, SP_NOT: N,
            RETIRED: N},
    # --- clean speckle (with spaces), K dwarf, closure
    "B07": {IMG_NO: Y, IMG_YES: N, EVO: N, DONE: Y, SP_NOT: N, SP_PL: N, DESIG: Y,
            RETIRED: N, CONF: N},
    # --- CONFUSABLE: "giant extrasolar planets" -- giant describes the PLANET, not the host
    "B08": {CONF: Y, IMG_NO: Y, IMG_YES: N, EVO: N, SP_PL: Y, SP_NOT: N, DESIG: Y,
            RETIRED: N, DONE: N},
    # --- CONFUSABLE: "out of phase with the photometric ephemeris" is not a binary
    "B09": {EVO: N, IMG_NO: Y, IMG_YES: N, DONE: Y, SP_NOT: N, SP_PL: N, DESIG: Y,
            RETIRED: N, CONF: N},
    "B10": {EVO: N, IMG_NO: Y, IMG_YES: N, DONE: Y, SP_NOT: N, SP_PL: N, DESIG: Y,
            RETIRED: N, CONF: N},
    # --- CONFUSABLE: "rules out the unlikely possibility that this was an eccentric EB"
    "B11": {IMG_NO: Y, IMG_YES: N, SP_NOT: N, SP_PL: Y, EVO: N, DONE: Y, DESIG: Y,
            RETIRED: N, CONF: N},
    # --- CONFUSABLE: "Is the orbit good enough to publish?" is a question, not a publication
    "B12": {SP_PL: Y, SP_NOT: N, EVO: Y, IMG_NO: Y, IMG_YES: N, CONF: N, DESIG: Y,
            RETIRED: N},
    # --- CONTEXT-ROT tests: 17.8k / 10.9k / 12.1k chars of multi-year KOI history
    "B13": {CONF: Y, IMG_NO: Y, DESIG: Y, RETIRED: N},
    "B14": {IMG_YES: Y, IMG_NO: N, DESIG: Y, RETIRED: N},
    "B15": {IMG_YES: Y, IMG_NO: N, DESIG: Y, RETIRED: N},
    # --- NEB retired: eclipse on a nearby star
    "B16": {IMG_YES: Y, IMG_NO: N, RETIRED: Y, SP_NOT: Y, EVO: N, DONE: N, DESIG: Y,
            CONF: N},
    # --- SB1 + "This system is an eclipsing binary" + hedged evolved
    "B17": {SP_NOT: Y, SP_PL: N, EVO: Y, DONE: Y, IMG_NO: N, IMG_YES: N, DESIG: Y,
            RETIRED: N, CONF: N},
    # --- clean speckle, with spaces (the control for B01/B02/B27)
    "B18": {IMG_NO: Y, IMG_YES: N, SP_NOT: N, SP_PL: N, EVO: N, DONE: N, DESIG: Y,
            RETIRED: N, CONF: N},
    # --- genuine companion at 1.4 arcsec + an NEB reported
    "B19": {IMG_YES: Y, IMG_NO: N, EVO: Y, DONE: Y, SP_NOT: Y, SP_PL: N, DESIG: Y,
            CONF: N},
    # --- "It does rule out a brown dwarf" + "cooler but evolved"
    "B20": {SP_PL: Y, SP_NOT: N, EVO: Y, DONE: Y, IMG_NO: N, IMG_YES: N, DESIG: Y,
            RETIRED: N, CONF: N},
    # --- "implies a hot Jupiter companion", K dwarf, clean speckle
    "B21": {SP_PL: Y, SP_NOT: N, EVO: N, IMG_NO: Y, IMG_YES: N, DONE: Y, DESIG: Y,
            RETIRED: N, CONF: N},
    # --- "A planetary companion is ruled out"
    "B22": {SP_NOT: Y, SP_PL: N, EVO: Y, DONE: Y, DESIG: Y, IMG_NO: N, IMG_YES: N,
            RETIRED: N, CONF: N},
    "B23": {EVO: N, IMG_NO: Y, IMG_YES: N, DONE: Y, SP_NOT: N, SP_PL: N, DESIG: Y,
            RETIRED: N, CONF: N},
    # --- CONFUSABLE: "wouldn't surprise me to find that this is a false positive" is
    #     speculation, not a classification
    "B24": {IMG_NO: Y, IMG_YES: N, RETIRED: N, DESIG: Y, CONF: N, "author_certainty": (0, 2.5)},
    # --- "WASP-29 published by Hellier et al. 2010"
    "B25": {CONF: Y, DESIG: Y, IMG_NO: N, IMG_YES: N, EVO: N, DONE: N, SP_NOT: N,
            RETIRED: N},
    # --- CONFUSABLE: double-lined binary raised and REJECTED; log(g)=2.00 must be ignored
    "B26": {SP_NOT: N, SP_PL: N, EVO: N, DONE: Y, IMG_NO: N, IMG_YES: N, RETIRED: N,
            CONF: N},
    # --- run-together negation + "consistent with a companion of about one Jupiter mass"
    "B27": {SP_PL: Y, SP_NOT: N, EVO: N, IMG_NO: Y, IMG_YES: N, DONE: Y, DESIG: Y,
            RETIRED: N, CONF: N},
}


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
    transient = (urllib.error.URLError, http.client.RemoteDisconnected,
                 ConnectionError, TimeoutError)
    last = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
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

    # A-5: assert the pinned model actually answered, BEFORE the response is persisted.
    got = out.get("model")
    if got != MODEL:
        raise SystemExit(
            f"MODEL MISMATCH: pinned {MODEL!r} but response says {got!r}. "
            "Not caching -- the literal sits inside the cache key (A-5). STOPPING.")
    hit.write_text(json.dumps(out, indent=2))
    return out, (time.time() - t0) * 1000, False


def verdict(ans, want):
    if ans["type"] == "noul":
        v = ans["noul"]
        return (v >= YES_MIN, f"{v:.2f}") if want == Y else (v <= NO_MAX, f"{v:.2f}")
    v = ans["score"]
    lo, hi = want
    return lo <= v <= hi, f"{v:.2f}"


def main():
    cases = json.loads(CASES_PATH.read_text())["cases"]
    assert all("y" not in c for c in cases), "case file must be label-blinded"

    raw, fails, mid, n_new, tok = {}, [], [], 0, 0
    print(f"question set {QUESTION_SET_VERSION} · {len(QUESTIONS)} questions "
          f"({len(TIER_PREDICTIVE)} predictive + {len(TIER_LABEL_ECHO)} label-echo) "
          f"· {len(cases)} blinded cases · model {MODEL}\n")

    for c in cases:
        state = {"notes": c["text"]}          # A-4: no `toi`
        out, ms, cached = call(state, QUESTIONS)
        raw[c["cid"]] = {"case": c, "state": state, "response": out}
        if not cached:
            n_new += 1
            tok += out["usage"]["input_tokens"]
        mark = "cache" if cached else f"{ms:.0f}ms"
        exp = EXPECT.get(c["cid"], {})
        print(f"=== {c['cid']}  [{c['stratum']}]  TOI {c['toi']}  {c['len']} ch  [{mark}]")
        for qid, ans in out["answers"].items():
            want = exp.get(qid)
            shown = (f"noul={ans['noul']:.2f}" if ans["type"] == "noul"
                     else f"score={ans['score']:.2f} conf={ans['confidence']:.2f}")
            if ans["type"] == "noul" and NO_MAX < ans["noul"] < YES_MIN:
                mid.append((c["cid"], qid, ans["noul"]))
            if want is None:
                print(f"      .    {qid:46s} {shown}")
                continue
            ok, _ = verdict(ans, want)
            if not ok:
                fails.append((c["cid"], qid, want, shown, c["stratum"]))
            print(f"      {'ok ' if ok else 'FAIL'} {qid:46s} {shown}   want={want}")
        print()

    path = OUTDIR / f"gate_obsnotes_{QUESTION_SET_VERSION}_{time.strftime('%Y-%m-%d')}.json"
    path.write_text(json.dumps(raw, indent=2))

    n_assert = sum(len(EXPECT.get(c["cid"], {})) for c in cases)
    print("=" * 84)
    print(f"{n_assert - len(fails)}/{n_assert} assertions passed · {len(fails)} FAILED")
    print(f"mid-band nouls (0.30 < p < 0.70), asserted or not: {len(mid)}")
    print(f"new API calls: {n_new} · input tokens: {tok:,} · cost: ${tok / 1e6 * 0.042:.5f}")
    print(f"raw -> {path.relative_to(ROOT)}")
    if fails:
        print("\n--- FAILURES ---")
        for cid, qid, want, got, stratum in fails:
            print(f"  {cid} [{stratum}] {qid:46s} want={want} got={got}")
    if mid:
        print("\n--- MID-BAND (a near-0.5 column is noise in the matrix) ---")
        for cid, qid, v in mid:
            print(f"  {cid} {qid:46s} {v:.2f}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
