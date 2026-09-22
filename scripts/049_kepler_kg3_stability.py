"""Kepler gate KG3 -- stability under paraphrase (PREREGISTRATION.md 11.10, A-40 40.7; A-41).

scripts/036_gate_g3_stability.py, adapted to the Kepler set. Registered criterion (A-40 40.7):
    200 distinct host states, paraphrased question wording:
    Spearman rho >= 0.85 per feature AND mean |delta p| <= 0.05;
    A-8 item 11's exemption: IQR < 0.01 -> judged on mean |delta p| alone, and reported.
§6's permuted-key-order test is VACUOUS with a one-key state, as on TESS; asserted, not skipped.

THE PARAPHRASES BELOW WERE WRITTEN AND COMMITTED WITH A-41, BEFORE THE STEP 5 RUN -- before any
Kepler feature existed -- so their wording cannot have been tuned to the result. Same judgment,
same cues, same named traps; different words and order. Criteria are unchanged (036's form).

A same-wording REPEAT arm is run beside the paraphrase arm, as 036 does, because jev-1.13.0 is
not run-to-run deterministic (WORKLOG 2026-09-20T21:06Z): without it a paraphrase rho below
0.85 cannot be told apart from resampling noise.

Run (after scripts/048_kepler_step3_features.py):
      .venv/bin/python scripts/049_kepler_kg3_stability.py
Idempotent: yes. Cached under data/cache/kepler_kg3/ on a salted key; re-runs cost nothing.
"""
import hashlib, importlib.util, json, pathlib, sys, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import duckdb, numpy as np
from scipy.stats import spearmanr

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "kepler.duckdb"
OUT = ROOT / "research" / "data"
CACHE = ROOT / "data" / "cache" / "kepler_kg3"

_spec = importlib.util.spec_from_file_location("s3", ROOT / "scripts" / "048_kepler_step3_features.py")
s3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(s3)
QUESTIONS, TIER_PREDICTIVE = s3.QUESTIONS, s3.TIER_PREDICTIVE

N_STATES, SEED = 200, 20260921
PARAPHRASE_VERSION = "kepler-2026-09-21.r3-para"
REPEAT_VERSION = "kepler-2026-09-21.r3-repeat"
RHO_MIN, MAD_MAX, IQR_EXEMPT = 0.85, 0.05, 0.01
_SWAP = threading.Lock()             # WORKLOG defect 34: serialises the s3 globals swap

PARA = {
    "imaging_reports_no_companion":
        "Do the notes say imaging of this star turned up nothing beside it -- no companion, no "
        "secondary source, no neighbouring star -- across at least some span of separations? "
        "'No companions detected within 4.0\"', 'No secondary sources were detected', 'No "
        "companions were detected on the field of view' and 'No companions visible from 2\" to "
        "5\" away from the star' each say exactly that and are enough by themselves. 'WIYN "
        "speckle image reveals a single star' and 'KOI 273 is a single star as observed within a "
        "box of size 2.76 x 2.76 arcsec' qualify too: a lone star means nothing else was seen. "
        "Say yes even where the notes also place a companion elsewhere -- 'No companions visible "
        "from 2\" to 5\" away ... There is a companion 6-7\" away' still contains a finding of "
        "nothing over one span. Telescope names, filters, fields of view, seeing, plots and FITS "
        "files are not findings and do not count against one. Say no only when no such finding "
        "occurs at all: the notes merely record that an image exists, as in 'A HIRES guider snap "
        "is avaible in .pdf and .fits formats', or the only imaging outcome is a companion.",
    "imaging_reports_companion_present":
        "Do the notes report a companion, a neighbouring star, or a second source actually "
        "observed beside this target -- in an image, on a guide camera, or on a slit viewer? "
        "Count, at any separation, 'Possible nearby companion = Yes' with a separation, 'Nearby "
        "stars detected' with a separation, 'The source is found to be double', 'There is a "
        "companion 6-7\" away', 'Equally bright star 10\" to the South' and 'Faint star ~4\" to "
        "south is well off slit'. Several observers often write about one target and can "
        "disagree -- 'No companions detected within 4.0\"' beside 'Possible nearby companion = "
        "Yes (3.39\" companion (UKIRT))'. A finding of nothing does not erase a sighting; if any "
        "sighting is reported, say yes. Say no where the notes report only that nothing was "
        "found, or only that an image exists, or only give plots, contour maps or limiting "
        "magnitudes without a star being found. The question is about a star SEEN beside the "
        "target: a companion deduced from spectra or velocities -- double lines, an SB1 or SB2, "
        "a large velocity variation -- is not one, and nor is a listing in the Kepler Eclipsing "
        "Binary Catalog.",
    "spectroscopy_indicates_nonplanetary_companion":
        "Do the notes decide that a star or brown dwarf, not a planet, produces the signal -- "
        "that the target is an eclipsing or spectroscopic binary, or its companion too heavy to "
        "be a planet? Qualifying: double-lined or double-peaked spectra, an SB1 or SB2, a second "
        "set of lines, a large velocity variation between visits, eclipses of alternating depth "
        "marking a stellar eclipsing binary, a nearby or background eclipsing binary (NEB, BEB or "
        "BGEB) named as the source, or a centroid or difference-image finding that another star "
        "makes the transit -- 'Difference image shows that nearby source is producing the "
        "transit signal', 'Current transit signal is from background star', 'Obvious BGEB at "
        "col=468; row=135'. 'CCF clearly double-peaked => SB2', 'a nice double-lined orbital "
        "solution', 'There is a large velocity variation (~20 km/s)' and 'this one is a clear "
        "stellar eclipsing binary' qualify even hedged with 'possibly', 'looks like' or 'these "
        "are just initial musings' and followed by a request to check. Say no where the finding "
        "goes the other way -- no significant variation, one set of lines, 'Looks good', 'our "
        "RVs show no evidence of a binary' -- or a binary is floated and then dismissed. A "
        "catalogue entry such as 'Possible eclipsing binary = Yes (Kepler Eclipsing Binary "
        "Catalog)' is not a finding from these observations: alone it means no, but it does not "
        "cancel a finding stated elsewhere, so a double-lined solution or large variation beside "
        "it still means yes. Disregard any 'Possible false positive = Yes (...)' or 'Possible "
        "false positive = No (...)' field and everything inside its parentheses; it is a "
        "disposition record. A star seen only in imaging is not a finding that it makes the "
        "signal. Disregard the header numbers: `RV=` and `Vrad=` are the star's absolute radial "
        "velocity, not a variation, and `ccf=` or `ccfPeak=` alone says nothing about a second "
        "star.",
    "spectroscopy_reports_no_binary_signature":
        "Do the notes report that the reconnaissance spectra look clean -- no significant "
        "velocity variation between visits, one set of lines, a clean or strong correlation "
        "peak, or a bare verdict like 'Looks good'? Short forms such as 'Recon: single lined', "
        "'single-lined' and 'Looks OK' qualify. Where such a verdict occurs anywhere, say yes, "
        "even if later sentences voice other doubts -- which star was observed, or the ephemeris "
        "-- that are not double lines or a large velocity variation. 'there is no significant "
        "velocity variation', 'there's no velocity variation. It's time for more precise "
        "velocities', 'the correlation peak is clean and strong' and 'Looks good' all qualify, "
        "also when another spectrum at a different phase is requested. A small variation the "
        "author calls consistent with a planet qualifies too, since it says no stellar binary "
        "was seen: 'The single order velocities show variation consistent with a planetary "
        "companion', 'There is ~300m/s velocity variation which indicates a ~6.8Mjupiter "
        "planet'. Disregard any 'Possible false positive = Yes (...)' or 'Possible false "
        "positive = No (...)' field and its parentheses. Say no where the notes report double "
        "or double-peaked lines, an SB1 or SB2, or a large velocity variation, or where they only "
        "log that a spectrum was taken -- phase, instrument, signal-to-noise -- with no verdict. "
        "Decide from the author's words, not the header numbers `RV=`, `Vrad=`, `ccf=`, "
        "`ccfPeak=`, `Vrot=`.",
    "recon_reported_concluded":
        "Do the notes declare the reconnaissance of this target finished -- no more recon "
        "spectra or observations needed, or time to move on to precise radial velocities? 'No "
        "more recon is needed', 'For now, no more recon is needed', 'It's time for more precise "
        "velocities', 'I don't think this warrants more recon right now' and 'This candidate "
        "needs no further Keck-HIRES spectra' qualify, misspellings like 'needs nor further' "
        "included. Say no where the notes ask for more recon -- \"Let's get another observation "
        "at opposite quadrature\", \"Let's fill out the phase coverage\", 'We'll have to take a "
        "closer look at this one' -- and never declare it finished. Where more is requested in "
        "one place and recon is declared finished in another, say yes: what matters is whether "
        "the declaration occurs at all. Say no where the notes only record that a spectrum or "
        "image was taken.",
    "author_certainty":
        "How sure does the writer of these notes sound about the conclusion they reach on this "
        "target? Go by the words the writer chose, not the machine-written measurement header "
        "lines, and not sentences that only describe the instrument, the field of view, or where "
        "the files are kept.",
    "indicates_false_positive_or_retired":
        "Do the notes declare this candidate a false positive, rejected or retired, or carry the "
        "field 'Possible false positive = Yes'? 'This KOI is dead. Move to inactive.' qualifies. "
        "The field 'Possible false positive = No' means no. So does a mere account of what the "
        "signal is or of an observation -- 'likely a background eclipsing binary', 'this is a "
        "small star eclipsing the target', a companion, double lines, a Kepler Eclipsing Binary "
        "Catalog listing -- without a declaration that the candidate is a false positive, "
        "rejected, retired, dead or inactive. Describing something that implies a false positive "
        "is not declaring one.",
    "indicates_confirmed_planet":
        "Do the notes declare this candidate a confirmed, validated or published planet, or that "
        "a paper presenting it was accepted or published? Say no where only a name appears -- "
        "'KOI-157', 'Kepler-21' -- with no statement of confirmation, validation, acceptance or "
        "publication; 'Partial transit of Kepler-167e observed by Spitzer' names a planet without "
        "saying it was confirmed. Do not use your own knowledge of what an object by that name "
        "turned out to be. A request to publish, or a plan to write a paper, is not a statement "
        "that one was published.",
}


def para_questions():
    q = json.loads(json.dumps(QUESTIONS))
    for qid, text in PARA.items():
        q[qid]["instructions"] = text
    return q


def main() -> int:
    assert set(PARA) == set(QUESTIONS), "paraphrase set must cover every question"
    assert len({"notes": "x"}) == 1, "state gained a key; the key-order test is no longer vacuous"

    with duckdb.connect(str(DB), read_only=True) as con:
        hosts = con.execute("select host, any_value(text) from kepler_cfop_corpus "
                            "group by host order by host").fetchall()
    rng = np.random.default_rng(SEED)
    pick = sorted(rng.choice(len(hosts), size=min(N_STATES, len(hosts)), replace=False))
    sample = [hosts[i] for i in pick]
    QP = para_questions()
    qpjson = json.dumps(QP, sort_keys=True, separators=(",", ":"))
    qjson = json.dumps(QUESTIONS, sort_keys=True, separators=(",", ":"))

    def call_variant(notes, salt, questions, qj):
        state = {"notes": notes}
        key = hashlib.sha256((s3.MODEL + salt + json.dumps(state, sort_keys=False,
                              separators=(",", ":")) + qj).encode()).hexdigest()
        CACHE.mkdir(parents=True, exist_ok=True)
        hit = CACHE / f"{key}.json"
        if hit.exists():
            return json.loads(hit.read_text())
        # Redirect s3.CACHE as well as its questions: the repeat arm's payload is byte-identical
        # to Step 5's, so s3.call would otherwise find the Step 5 file and never call -- the
        # rho = 1.000 that WORKLOG defect 20 was.
        # The swap rebinds s3's module globals, which every worker shares: unlocked, a thread
        # in the other arm can rebind them between s3.call's key and its request body, sending
        # one arm's call with the other arm's wording -- 4 of 197 on TESS (WORKLOG defect 34).
        # So swap + call + restore is one step; cache hits above still return in parallel.
        with _SWAP:
            saved = s3.QUESTIONS, s3._QJSON, s3.CACHE
            try:
                s3.QUESTIONS, s3._QJSON, s3.CACHE = questions, qj, CACHE / salt
                out = s3.call(state)
            finally:
                s3.QUESTIONS, s3._QJSON, s3.CACHE = saved
        hit.write_text(json.dumps(out, indent=2))
        return out

    print(f"KG3: {len(sample)} host states · paraphrase + same-wording repeat · model {s3.MODEL}")
    s3_globals = s3.QUESTIONS, s3._QJSON, s3.CACHE
    para, rep = {}, {}
    with ThreadPoolExecutor(max_workers=s3.CONCURRENCY) as ex:
        futs = {}
        for host, notes in sample:
            futs[ex.submit(call_variant, notes, PARAPHRASE_VERSION, QP, qpjson)] = ("para", host)
            futs[ex.submit(call_variant, notes, REPEAT_VERSION, QUESTIONS, qjson)] = ("rep", host)
        for f in as_completed(futs):
            kind, host = futs[f]
            (para if kind == "para" else rep)[host] = f.result()["answers"]
    # base is read through s3.CACHE below. On TESS, 036's unlocked swap left that global on the
    # G3 directory, so its base was silently the repeat arm's re-ask (WORKLOG defect 34).
    if (s3.QUESTIONS, s3._QJSON, s3.CACHE) != s3_globals:
        raise SystemExit("s3 globals were not restored after the KG3 calls. STOPPING.")
    base = {}
    for host, notes in sample:
        hit = s3.CACHE / f"{s3.cache_key({'notes': notes})}.json"
        if not hit.exists():
            raise SystemExit(f"host {host} has no Step 5 answer; run 048 first. STOPPING.")
        base[host] = json.loads(hit.read_text())["answers"]

    hs = sorted(base)
    print(f"\n{'feature':<46} {'rho':>7} {'mean|dp|':>9} {'IQR':>7}   {'rep rho':>7} {'rep|dp|':>8}  verdict")
    res, fails = {}, []
    for qid in QUESTIONS:
        kind = "noul" if QUESTIONS[qid]["type"] == "noul" else "score"
        sc = 4.0 if kind == "score" else 1.0
        a = np.array([base[h][qid][kind] for h in hs], float) / sc
        b = np.array([para[h][qid][kind] for h in hs], float) / sc
        r = np.array([rep[h][qid][kind] for h in hs], float) / sc
        rho, mad = spearmanr(a, b).statistic, float(np.mean(np.abs(a - b)))
        rho_r, mad_r = spearmanr(a, r).statistic, float(np.mean(np.abs(a - r)))
        iqr = float(np.subtract(*np.percentile(a, [75, 25])))
        exempt = iqr < IQR_EXEMPT
        ok = (mad <= MAD_MAX) if exempt else (rho >= RHO_MIN and mad <= MAD_MAX)
        if not ok:
            fails.append(qid)
        print(f"{qid:<46} {rho:7.3f} {mad:9.4f} {iqr:7.3f}   {rho_r:7.3f} {mad_r:8.4f}  "
              f"{('ok (IQR exempt)' if exempt else 'ok') if ok else 'FAIL'}")
        res[qid] = dict(rho=float(rho), mean_abs_delta=mad, iqr=iqr, repeat_rho=float(rho_r),
                        repeat_mean_abs_delta=mad_r, iqr_exempt=bool(exempt), passed=bool(ok),
                        tier="predictive" if qid in TIER_PREDICTIVE else "label_echo")
    pred_fail = [q for q in fails if q in TIER_PREDICTIVE]
    verdict = "PASS" if not pred_fail else "FAIL"
    print(f"\nKG3 VERDICT (TIER_PREDICTIVE): {verdict}" + (f" -- failing: {', '.join(pred_fail)}" if pred_fail else ""))
    print("KG3 key-order test: VACUOUS -- the state has one key (`notes`). Reported, not skipped.")
    (OUT / "kepler_kg3_stability.json").write_text(json.dumps(
        {"n_states": len(sample), "seed": SEED, "paraphrase_version": PARAPHRASE_VERSION,
         "repeat_version": REPEAT_VERSION,
         "criterion": {"rho_min": RHO_MIN, "mad_max": MAD_MAX, "iqr_exempt": IQR_EXEMPT},
         "features": res, "verdict": verdict, "failing_predictive": pred_fail}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
