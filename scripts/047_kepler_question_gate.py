"""Question-design gate for the Kepler set on CFOP text (A-40 40.11 item 1; the 032 procedure).

Identical in mechanism to scripts/032_question_gate_obsnotes.py -- only the question module,
the case file and the cache directory differ:
  A-4  state is {"notes": ...}; no KOI or TIC identifier is sent
  A-5  MODEL pinned to "jev-1.13.0"; response["model"] asserted before anything is cached
  --   cases come from scripts/046_kepler_gate_cases.py, which emits no label, and EXPECT below
       was written from the case text alone, before any answer was seen
  6    section 2.4 rule 6 bands: Noul >= 0.70 for an asserted yes, <= 0.30 for an asserted no;
       anything between is a FAILURE

Two cells are deliberately NOT asserted, because the text only implies the answer and section
2.4 rule 1 says questions ask what the text says:
  S5_verylong_2 / no_binary_signature -- the only "looks good" is about light-curve modelling
  T05 / no_binary_signature -- "if there were a stellar companion, we would have seen the
       velocity variation" is an inference, not a report

Run:  .venv/bin/python scripts/047_kepler_question_gate.py            # the 30 main cases
      .venv/bin/python scripts/047_kepler_question_gate.py --holdout  # the 15 disjoint cases
      .venv/bin/python scripts/047_kepler_question_gate.py --holdout2 # the freeze decision

HOLDOUT2_EXPECT decides whether r3 freezes, under the rule fixed in WORKLOG before any r3 answer
existed: >= 95% of asserted cells pass AND no predictive question fails on more than one case;
a predictive question that still fails is DELETED, not reworded (section 2.4 rule 4).

The holdout exists because r1 -> r2 was repaired on the main cases. HOLDOUT_EXPECT was written
from the holdout texts after r2 was frozen and BEFORE r2 was run on them; three further cells are
deliberately unasserted there (H_S4_long_1 / recon: "This KOI is dead" never says recon is
finished; H_S5_verylong_1 / no_binary_signature: the text concludes both ways).
Idempotent: yes. Responses cached on sha256(model + version + state + questions) under
data/cache/gate_kepler/, so a re-run costs nothing. Bump QUESTION_SET_VERSION to re-test.
"""
import argparse, hashlib, http.client, json, os, pathlib, sys, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache" / "gate_kepler"
OUTDIR = ROOT / "research" / "data"
CASES_PATH = OUTDIR / "gate_cases_kepler_2026-09-21.json"
HOLDOUT_PATH = OUTDIR / "gate_cases_kepler_holdout_2026-09-21.json"
HOLDOUT2_PATH = OUTDIR / "gate_cases_kepler_holdout2_2026-09-21.json"
MODEL = "jev-1.13.0"
YES_MIN, NO_MAX = 0.70, 0.30
PRICE_PER_M_INPUT = 0.042

_envfile = ROOT / ".env"
if _envfile.exists():
    for line in _envfile.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip('"').strip("'")
KEY = os.environ.get("TYPESAFE_API_KEY", "")
if not KEY:
    raise SystemExit("no TYPESAFE_API_KEY found")

sys.path.insert(0, str(ROOT / "src"))
from exonotes.questions_kepler import (  # noqa: E402
    QUESTION_SET_VERSION, QUESTIONS, TIER_LABEL_ECHO, TIER_PREDICTIVE)

NO, CP = "imaging_reports_no_companion", "imaging_reports_companion_present"
NP, CL = "spectroscopy_indicates_nonplanetary_companion", "spectroscopy_reports_no_binary_signature"
DN, FP, CF = "recon_reported_concluded", "indicates_false_positive_or_retired", "indicates_confirmed_planet"
Y, N = "yes", "no"


def row(no, cp, np_, cl, dn, fp, cf):
    return {q: v for q, v in zip((NO, CP, NP, CL, DN, FP, CF), (no, cp, np_, cl, dn, fp, cf))
            if v is not None}


# Written from the case text alone (WORKLOG, step 4b). None = deliberately not asserted.
EXPECT = {
    # --- Robo-AO clean, nothing else
    "S1_short_1":    row(Y, N, N, N, N, N, N),
    "S1_short_2":    row(Y, N, N, N, N, N, N),
    "S1_short_3":    row(Y, N, N, N, N, N, N),
    "S2_median_3":   row(Y, N, N, N, N, N, N),
    # --- Robo-AO clean AND a UKIRT companion flag: both imaging questions yes
    "S2_median_1":   row(Y, Y, N, N, N, N, N),
    "T01_roboao_clean": row(Y, Y, N, N, N, N, N),
    # --- companion only
    "S2_median_2":   row(N, Y, N, N, N, N, N),
    "T04_companion_flag": row(N, Y, N, N, N, N, N),
    # --- light-curve EB conclusion ("clear stellar eclipsing binary") + UKIRT companion
    "S3_typical_1":  row(N, Y, Y, N, N, N, N),
    # --- four stars on the guide camera; "Possible false positive = No" must NOT fire FP
    "S3_typical_2":  row(N, Y, N, N, N, N, N),
    # --- "Looks good but ... Let's try for phase 0.75"; KEBC flag must NOT fire NP
    "S3_typical_3":  row(Y, Y, N, Y, N, N, N),
    # --- weak, noisy spectrum with no verdict; imaging clean
    "S4_long_1":     row(Y, N, N, N, N, N, N),
    # --- "consistent with no variation. It's time for more precise velocities. No more recon"
    "S4_long_2":     row(Y, Y, N, Y, Y, N, N),
    # --- "clearly a K-dwarf" is not a verdict on variation; "Kepler-167e" is a bare designation
    "S4_long_3":     row(Y, Y, N, N, N, N, N),
    # --- recon closed, "RVs show no evidence of a binary", "has been validated"
    "S5_verylong_1": row(Y, Y, N, Y, Y, N, Y),
    # --- companions everywhere, no nothing-found statement; "has been confirmed ... Kepler-410"
    "S5_verylong_2": row(N, Y, N, None, N, N, Y),
    # --- everything clean, recon closed, no confirmation statement
    "S5_verylong_3": row(Y, N, N, Y, Y, N, N),
    # --- "Looks OK. Let's get another observation"; close double / triple in imaging
    "T03_nearby_stars": row(N, Y, N, Y, N, N, N),
    # --- recon closed by inference; speckle double + Robo-AO secondary + WIYN clean
    "T05_speckle_double": row(Y, Y, N, None, Y, N, N),
    # --- "no velocity variation. It's time for more precise velocities"; star 10" south
    "T06_guider_only": row(Y, Y, N, Y, Y, N, N),
    # --- KEBC flag + "a nice double-lined orbital solution"
    "T07_sb2_double": row(N, N, Y, N, N, N, N),
    # --- "large velocity variation (~20 km/s)"; faint star ~4" south seen on the slit
    "T08_large_var": row(Y, Y, Y, N, N, N, N),
    # --- "no significant velocity variation, and now no more recon is needed"
    "T09_no_var":    row(Y, Y, N, Y, Y, N, N),
    # --- "Looks good. Let's go for opposite quadrature" -- no closure statement
    "T10_looks_good": row(Y, N, N, Y, N, N, N),
    "T11_recon_done": row(Y, N, N, Y, Y, N, N),
    "T12_precise_rv": row(Y, N, N, Y, Y, N, N),
    # --- KEBC flag alone: every question no
    "T13_kebc_flag": row(N, N, N, N, N, N, N),
    # --- "look good ... ~300 m/s variation which indicates a ~6.8Mjupiter planet"; the only
    # SB2 is INSIDE "Possible false positive = Yes (...)", which the module's pre-run design rule
    # says no predictive question reads. NP was asserted "yes" in r1 -- a cell that contradicted
    # that rule; corrected to "no" AFTER seeing r1's 0.21, disclosed in WORKLOG step 4b.
    "T14_fp_yes":    row(Y, Y, N, Y, N, Y, N),
    # --- "Possible false positive = No (disposition updated)" alone
    "T15_fp_no":     row(N, N, N, N, N, N, N),
    # --- "presumably validation would be possible" is not a validation
    "T16_published": row(Y, Y, N, N, N, N, N),
}

# Written from the holdout texts alone, after r2 was frozen, before r2 saw them.
HOLDOUT_EXPECT = {
    "H_S1_short_1":      row(Y, N, N, N, N, N, N),
    # --- "likely a background eclipsing binary": hedged BEB
    "H_S1_short_2":      row(N, N, Y, N, N, N, N),
    # --- recon spectrum logged with no verdict
    "H_S2_median_1":     row(Y, N, N, N, N, N, N),
    "H_S2_median_2":     row(Y, Y, N, N, N, N, N),
    # --- "Recon: single lined"; "Let's get the opposite quadrature"
    "H_S3_typical_1":    row(Y, Y, N, Y, N, N, N),
    "H_S3_typical_2":    row(Y, Y, N, N, N, N, N),
    # --- "Obvious BGEB ... nearby source is producing the transit signal"; "This KOI is dead"
    "H_S4_long_1":       row(Y, Y, Y, N, None, Y, N),
    # --- "Looks good." then doubts about two stars -- the verdict still appears
    "H_S4_long_2":       row(Y, Y, N, Y, N, N, N),
    # --- final conclusion: "a small star eclipsing the target"; "doesn't warrant more recon"
    "H_S5_verylong_1":   row(Y, Y, Y, None, Y, N, N),
    # --- "no RV variation above errors ... No evidence of double lines or SB2"; "Kepler-5" bare
    "H_S5_verylong_2":   row(Y, Y, N, Y, Y, N, N),
    # --- "Keck AO <0.1\" binary" is an IMAGING companion: nonplanetary must stay no
    "H_T04_companion_flag": row(Y, Y, N, N, N, N, N),
    "H_T07_sb2_double":  row(N, N, Y, N, N, N, N),
    # --- KEBC flag + "large velocity variations": the r1 failure mode on unseen text
    "H_T08_large_var":   row(N, N, Y, N, N, N, N),
    "H_T09_no_var":      row(Y, Y, N, Y, Y, N, N),
    "H_T10_looks_good":  row(Y, N, N, Y, N, N, N),
}

# Written from the holdout-2 texts alone, after r3 was frozen, before r3 saw them.
HOLDOUT2_EXPECT = {
    "H2_S1_short_1":     row(Y, N, N, N, N, N, N),
    "H2_S1_short_2":     row(Y, N, N, N, N, N, N),
    "H2_S2_median_1":    row(Y, N, N, N, N, N, N),
    "H2_S2_median_2":    row(Y, N, N, N, N, N, N),
    # --- KEBC flag + UKIRT + Robo-AO clean: the catalogue alone must NOT fire nonplanetary
    "H2_S3_typical_1":   row(Y, Y, N, N, N, N, N),
    # --- KEBC + "Possible false positive = Yes (Possible SB2 ...)": the FP field is ignored by NP
    "H2_S3_typical_2":   row(N, Y, N, N, N, Y, N),
    # --- "the spectra are so nice" is quality, not binarity -> CL unasserted
    "H2_S4_long_1":      row(N, Y, N, None, N, N, N),
    # --- hedged throughout ("wouldn't surprise me ... false positive"): NP/CL/recon unasserted
    "H2_S4_long_2":      row(Y, N, None, None, None, N, N),
    # --- Kepler-22b: "no evidence of the lines of a secondary star"; "Published as Kepler 22b"
    "H2_S5_verylong_1":  row(Y, Y, N, Y, Y, N, Y),
    # --- Kepler-4: "Recon looks OK"; "Ready for HIRES" needs domain knowledge -> recon unasserted
    "H2_S5_verylong_2":  row(Y, N, N, Y, None, N, N),
    "H2_T04_companion_flag": row(N, Y, N, N, N, N, N),
    # --- "The spectrum is double-lined, but the weak secondary may by sky contamination"
    "H2_T07_sb2_double": row(N, N, Y, N, N, N, N),
    # --- "small velocity variation is within the errors ... no more recon is needed"; KEBC flag
    "H2_T08_large_var":  row(Y, Y, N, Y, Y, N, N),
    "H2_T09_no_var":     row(Y, Y, N, Y, Y, N, N),
    "H2_T10_looks_good": row(Y, N, N, Y, N, N, N),
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
    req = urllib.request.Request(
        "https://api.typesafe.ai/v1/systemone", data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    t0 = time.time()
    transient = (urllib.error.URLError, http.client.RemoteDisconnected, ConnectionError, TimeoutError)
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
    if out.get("model") != MODEL:
        raise SystemExit(f"MODEL MISMATCH: pinned {MODEL!r} but response says {out.get('model')!r}. "
                         "Not caching (A-5). STOPPING.")
    hit.write_text(json.dumps(out, indent=2))
    return out, (time.time() - t0) * 1000, False


def verdict(ans, want):
    v = ans["noul"]
    return v >= YES_MIN if want == Y else v <= NO_MAX


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--holdout", action="store_true", help="run the disjoint holdout cases")
    ap.add_argument("--holdout2", action="store_true", help="run the second holdout (freeze decision)")
    a = ap.parse_args()
    expect, cpath, tag = ((HOLDOUT2_EXPECT, HOLDOUT2_PATH, "gate_kepler_holdout2") if a.holdout2 else
                          (HOLDOUT_EXPECT, HOLDOUT_PATH, "gate_kepler_holdout") if a.holdout else
                          (EXPECT, CASES_PATH, "gate_kepler"))
    cases = json.loads(cpath.read_text())["cases"]
    assert all("y" not in c for c in cases), "case file must be label-blinded"
    assert set(expect) == {c["cid"] for c in cases}, "EXPECT and the case file disagree on cids"

    raw, fails, mid, n_new, tok = {}, [], [], 0, 0
    print(f"question set {QUESTION_SET_VERSION} · {len(QUESTIONS)} questions "
          f"({len(TIER_PREDICTIVE)} predictive + {len(TIER_LABEL_ECHO)} label-echo) "
          f"· {len(cases)} blinded cases · model {MODEL}\n")
    for c in cases:
        state = {"notes": c["text"]}
        out, ms, cached = call(state, QUESTIONS)
        raw[c["cid"]] = {"case": c, "state": state, "response": out}
        if not cached:
            n_new += 1
            tok += out["usage"]["input_tokens"]
        exp = expect[c["cid"]]
        print(f"=== {c['cid']}  host {c['host']}  {c['len']:,} ch  [{'cache' if cached else f'{ms:.0f}ms'}]")
        for qid, ans in out["answers"].items():
            want = exp.get(qid)
            shown = (f"noul={ans['noul']:.2f}" if ans["type"] == "noul"
                     else f"score={ans['score']:.2f} conf={ans['confidence']:.2f}")
            if ans["type"] == "noul" and NO_MAX < ans["noul"] < YES_MIN:
                mid.append((c["cid"], qid, ans["noul"]))
            if want is None:
                print(f"      .    {qid:46s} {shown}")
                continue
            ok = verdict(ans, want)
            if not ok:
                fails.append((c["cid"], qid, want, shown))
            print(f"      {'ok ' if ok else 'FAIL'} {qid:46s} {shown}   want={want}")
        print()

    path = OUTDIR / f"{tag}_{QUESTION_SET_VERSION}_{time.strftime('%Y-%m-%d')}.json"
    path.write_text(json.dumps(raw, indent=2))
    n_assert = sum(len(v) for v in expect.values())
    print("=" * 84)
    print(f"{n_assert - len(fails)}/{n_assert} assertions passed · {len(fails)} FAILED")
    print(f"mid-band nouls (0.30 < p < 0.70), asserted or not: {len(mid)}")
    print(f"new API calls: {n_new} · input tokens: {tok:,} · cost: ${tok / 1e6 * PRICE_PER_M_INPUT:.5f}")
    print(f"raw -> {path.relative_to(ROOT)}")
    if fails:
        print("\n--- FAILURES ---")
        for cid, qid, want, got in fails:
            print(f"  {cid:20s} {qid:46s} want={want} got={got}")
    if mid:
        print("\n--- MID-BAND ---")
        for cid, qid, v in mid:
            print(f"  {cid:20s} {qid:46s} {v:.2f}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
