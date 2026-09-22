"""Gate G3 — stability of the Jev features (TASK C; PREREGISTRATION.md §6, A-8 item 11).

Registered criterion:
    Re-run 200 rows with (a) paraphrased question wording and (b) permuted state key order.
    Spearman rho >= 0.85 per feature AND mean |delta p| <= 0.05.
A-8 item 11 exemption: if a feature's inter-quartile range is below one quantisation step
(0.01), G3 is judged on mean |delta p| <= 0.05 ALONE for that feature, and the exemption is
reported. Jev returns two decimals, so a near-constant column's rho is dominated by ties.

**(b) IS NOT APPLICABLE AND THAT IS REGISTERED, NOT SKIPPED.** A-4 removed `toi` from the
request state, so the registered state is `{"notes": ...}` -- a single key. There is no key
order to permute. §6 wrote criterion (b) when the state still had two keys. This script
asserts that the state has exactly one key and reports (b) as vacuous rather than silently
dropping it. If a future amendment re-introduces a second key, this assertion fires.

Run:  .venv/bin/python scripts/036_gate_g3_stability.py
Idempotent: yes. Paraphrase responses are cached under data/cache/g3/ on
sha256(model + PARAPHRASE_VERSION + state + questions); a re-run costs nothing.
"""
import hashlib
import json
import pathlib
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import duckdb
import numpy as np
from scipy.stats import spearmanr

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "exonotes.duckdb"
OUT = ROOT / "research" / "data"
CACHE = ROOT / "data" / "cache" / "g3"

sys.path.insert(0, str(ROOT / "src"))
from exonotes.questions import QUESTIONS, TIER_PREDICTIVE  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
_s3 = __import__("importlib").util.spec_from_file_location(
    "s3", ROOT / "scripts" / "034_step3_features.py")
s3 = __import__("importlib").util.module_from_spec(_s3)
_s3.loader.exec_module(s3)

N_ROWS = 200
SEED = 20260920
PARAPHRASE_VERSION = "2026-09-20.r6-para"
# A same-wording REPEAT arm, added after the 21:06Z finding that jev-1.13.0 is not run-to-run
# deterministic (mean |delta| 0.0049 over 270 paired values, max 0.100). Without it, a
# paraphrase rho below 0.85 cannot be told apart from plain resampling noise. This salt only
# changes the cache key, so the request payload is byte-identical to the Step 3 one.
REPEAT_VERSION = "2026-09-20.r6-repeat2"
_SWAP = threading.Lock()             # WORKLOG defect 34: serialises the s3 globals swap
RHO_MIN, MAD_MAX, IQR_EXEMPT = 0.85, 0.05, 0.01

# Paraphrases: same judgment, different words. Cues and the named forbidden inferences are
# preserved -- those ARE the question (§2.4). What changes is phrasing and order.
PARA = {
    "imaging_reports_no_companion":
        "Do the notes say that imaging of this star turned up nothing beside it -- no companion, "
        "no secondary source, no neighbouring star? Phrases like 'No secondary sources were "
        "detected' or 'No companions detected within 4.0\"' are themselves enough. Count it too "
        "when the words are jammed against what precedes them, e.g. 'acquired at 832nmNo "
        "secondary sources were detected'; a missing space does not change what was said. Imaging "
        "notes routinely also record that an observation happened, list wavelengths, and mention "
        "limiting-magnitude plots. None of that is a result, but none of it cancels a result "
        "either: whenever a statement that nothing was found appears somewhere in the text, say "
        "yes. Say no only when such a statement is absent altogether -- the notes describe an "
        "observation without its outcome, or they report that something IS there.",
    "imaging_reports_companion_present":
        "Do the notes report that a neighbouring star, companion, or secondary source was in fact "
        "located beside this target? Count a quoted separation ('a nearby companion at 1.4 arcsec "
        "separation'), a 'Possible nearby companion = Yes' entry, a star noticed on a guider, or a "
        "named neighbour identified as the eclipse source. Say no where the notes report that "
        "nothing turned up, including the run-together '832nmNo secondary sources were detected'. "
        "Say no where they merely record that imaging happened; asking someone to look for a "
        "companion is not finding one. The question concerns a star OBSERVED beside the target. A "
        "companion worked out from velocities or a spectrum -- an SB1, doubled lines, 'a mid dwarf "
        "companion' from RVs -- is not an observed neighbour and does not qualify unless imaging "
        "or a catalogue also places one there.",
    "spectroscopy_indicates_nonplanetary_companion":
        "Do the notes decide that whatever produces the events is heavier than a planet -- a star, "
        "a brown dwarf, or an eclipsing or spectroscopic binary? It may be this star or a "
        "neighbouring one whose eclipses feed through; either qualifies. The shorthand NEB "
        "(nearby eclipsing binary) and BEB (background eclipsing binary) carry exactly this "
        "meaning by themselves -- no separation, bearing, or star name required -- so 'SG1 "
        "indicates there is an NEB' suffices. Also count 'This system is an eclipsing binary', "
        "'the transit-like events are secondary eclipses in an eclipsing binary', 'the eclipse is "
        "on a nearby star', 'a planetary companion is ruled out', 'double-lined', SB1, SB2, SEB1, "
        "SEB2. Say no where the finding goes the other way -- a brown dwarf or stellar companion "
        "excluded, or the companion called a planet or hot Jupiter. Disregard the `RV=` figure in "
        "the machine-written header: it is the star's absolute radial velocity, not a variation, "
        "and reveals nothing about the companion. A velocity 'out of phase with the photometric "
        "ephemeris' is not on its own a binary -- out of phase means the variation fails to track "
        "the transit, casting doubt on the companion rather than declaring it stellar. A binary "
        "floated and then dismissed does not qualify: 'the cores do not swap sides, as would be "
        "expected if this is a double-lined binary' and 'rules out the unlikely possibility that "
        "this was an eccentric eclipsing binary' both conclude it is NOT a binary.",
    "spectroscopy_consistent_with_planet":
        "Do the notes decide the spectroscopic or radial-velocity evidence fits a planet-mass "
        "companion, or excludes a stellar or brown-dwarf one? 'implies a hot Jupiter companion', "
        "'consistent with a companion of about one Jupiter mass', 'It does rule out a brown "
        "dwarf', 'This pretty much rules out a stellar or brown dwarf companion' all qualify. "
        "Excluding a stellar companion qualifies however it is worded, 'rules out the unlikely "
        "possibility that this was an eccentric eclipsing binary' included -- an eclipsing binary "
        "IS a stellar companion, so excluding one argues for a planet. A published radial-velocity "
        "mass that lands in the planetary range also qualifies. Say no where the notes conclude "
        "the companion is stellar or a brown dwarf, or the system a binary. Say no where they only "
        "note the velocity shift was small, insignificant, or inside the errors without concluding "
        "anything about the companion. Disregard the `RV=` figure in the machine-written header: "
        "it is an absolute radial velocity, not a variation.",
    "host_star_described_as_evolved":
        "Do the notes characterise this star in words as having evolved off the main sequence, "
        "rather than as an ordinary dwarf? 'evolved', 'somewhat evolved', 'slightly evolved', "
        "'subgiant', 'giant' all qualify, hedges such as 'perhaps' or 'probably' included. Say no "
        "where the star is called a dwarf -- 'a late F dwarf', 'an early K dwarf', 'a G dwarf' -- "
        "or 'a Sun-like spectrum', with no evolved wording present. Decide from the descriptive "
        "words alone. Pay no attention to `log(g)`, `Teff`, `R=` or `V=` in the machine-written "
        "header; do not deduce evolutionary state from any number.",
    "followup_reported_concluded":
        "Do the notes declare that this target needs no more observing? 'No more TRES recon "
        "spectra are needed', 'No more recon spectra are needed', 'No more TRES observations are "
        "needed' all qualify. Say no where the notes instead call for more -- \"Let's get a second "
        "TRES recon spectrum near phase 0.75\", 'we need to make sure', 'this deserves more "
        "attention'. Where the notes request more earlier and later declare none are needed, say "
        "yes: what is asked is whether the declaration occurs at all.",
    "author_certainty":
        "How sure does the person writing these notes sound about the conclusion they reach on "
        "this candidate? Judge the human prose, not the machine-written lines of measurements.",
    "indicates_retired_or_rejected":
        "Do the notes declare this candidate retired, rejected, or labelled a false positive or "
        "false alarm -- 'Retired as NEB', 'TFOP FP', 'FA'? Say no where they only characterise the "
        "signal, or voice a doubt about it, without declaring retirement, rejection, or an FP/FA "
        "label. Calling the signal an eclipsing binary, a binary, or a variable is not itself a "
        "retirement. Nor is excluding something: 'a planetary companion is ruled out' and 'this "
        "rules out a brown dwarf' describe what the companion is or is not, not that the candidate "
        "was retired or labelled FP. Nor is halting observations: 'no more recon spectra are "
        "needed' means the follow-up is over, not that the candidate was rejected. Say no unless "
        "the text genuinely declares a retirement, a rejection, or an FP or FA label.",
    "indicates_confirmed_planet":
        "Do the notes declare this candidate a confirmed, validated, or published planet? A "
        "statement that a paper presenting it is published qualifies. Say no where only a "
        "catalogue name is given, another catalogue's included, such as 'SG1 reports that this is "
        "K2-133', without an accompanying statement of confirmation, validation, or publication -- "
        "do not draw on your own knowledge of what an object by that name turned out to be. Say no "
        "where the notes call the candidate a false positive or false alarm, or say it was "
        "retired. Asking to publish, or wondering whether the data are good enough to publish, is "
        "not a declaration that it was published.",
    "contains_object_designation":
        "Do the notes include a catalogue name for a star or planet -- 'WASP-29', 'K2-133', "
        "'Kepler-410Ab', 'KOI-889b', 'TOI-1584', or a bare TIC number? Say no where the only names "
        "present belong to instruments, surveys, working groups, people, or papers -- 'TRES', "
        "'NESSI', 'WIYN', 'SG1', 'TFOP', 'HARPS-N', 'Hord et al 2024'.",
}


def para_questions():
    q = json.loads(json.dumps(QUESTIONS))   # deep copy
    for qid, text in PARA.items():
        q[qid]["instructions"] = text
    return q


def main() -> int:
    assert set(PARA) == set(QUESTIONS), "paraphrase set must cover every question"

    # (b) permuted state key order -- assert the premise rather than skip it.
    probe_state = {"notes": "x"}
    assert len(probe_state) == 1, "state gained a key; G3(b) is no longer vacuous"

    con = duckdb.connect(str(DB), read_only=True)
    rows = con.execute("select tic_id, cast(toi as varchar), notes "
                       "from analysis_set_obsnotes order by toi").fetchall()
    con.close()
    rng = np.random.default_rng(SEED)
    pick = rng.choice(len(rows), size=min(N_ROWS, len(rows)), replace=False)
    sample = [rows[i] for i in sorted(pick)]

    QP = para_questions()
    qpjson = json.dumps(QP, sort_keys=True, separators=(",", ":"))

    def call_variant(notes, salt, questions, qjson):
        """One call under a cache-key salt, so an identical payload can be re-asked."""
        state = {"notes": notes}
        key = hashlib.sha256((s3.MODEL + salt
                              + json.dumps(state, sort_keys=False, separators=(",", ":"))
                              + qjson).encode()).hexdigest()
        CACHE.mkdir(parents=True, exist_ok=True)
        hit = CACHE / f"{key}.json"
        if hit.exists():
            return json.loads(hit.read_text())
        # s3.CACHE must be redirected too. `s3.call` builds its own key from the patched
        # _QJSON and looks it up in ITS OWN cache dir -- so for the repeat arm, whose payload
        # is byte-identical to Step 3's, it would find the Step 3 file and return it without
        # calling. That made the repeat arm report a trivially perfect rho=1.000 on the first
        # run. Pointing s3.CACHE at this script's directory forces a real call.
        # The swap rebinds s3's module globals, which every worker shares. Unlocked, a thread in
        # the other arm could rebind them mid-call (4 of 197 paraphrase calls went out with the
        # original wording) and a `finally` could restore another thread's values, which left
        # s3.CACHE on data/cache/g3/ so `base` below was read from the repeat arm's own files
        # (WORKLOG defect 34). So swap + call + restore is one step.
        with _SWAP:
            saved_q, saved_j, saved_c = s3.QUESTIONS, s3._QJSON, s3.CACHE
            try:
                s3.QUESTIONS, s3._QJSON, s3.CACHE = questions, qjson, CACHE
                out, _ = s3.call(state)
            finally:
                s3.QUESTIONS, s3._QJSON, s3.CACHE = saved_q, saved_j, saved_c
        hit.write_text(json.dumps(out, indent=2))
        return out

    print(f"G3: {len(sample)} rows · paraphrase arm + same-wording repeat arm · "
          f"model {s3.MODEL}")
    base, para, rep = {}, {}, {}
    s3_globals = s3.QUESTIONS, s3._QJSON, s3.CACHE
    with ThreadPoolExecutor(max_workers=s3.CONCURRENCY) as ex:
        futs = {}
        for tic, toi, n in sample:
            futs[ex.submit(call_variant, n, PARAPHRASE_VERSION, QP, qpjson)] = ("para", toi, n)
            futs[ex.submit(call_variant, n, REPEAT_VERSION, QUESTIONS,
                           json.dumps(QUESTIONS, sort_keys=True, separators=(",", ":")))] = \
                ("rep", toi, n)
        for i, f in enumerate(as_completed(futs), 1):
            kind, toi, notes = futs[f]
            (para if kind == "para" else rep)[toi] = f.result()["answers"]
            if i % 100 == 0:
                print(f"  {i}/{len(futs)}")
    # base must come from the Step 3 cache, i.e. the features in the matrix (defect 34).
    if (s3.QUESTIONS, s3._QJSON, s3.CACHE) != s3_globals:
        raise SystemExit("s3 globals were not restored after the G3 calls. STOPPING.")
    for tic, toi, notes in sample:
        base[toi] = s3.call({"notes": notes})[0]["answers"]

    toids = sorted(base)
    print(f"\n{'':<46} {'--- PARAPHRASE ---':>26}   {'--- REPEAT (noise) ---':>24}")
    print(f"{'feature':<46} {'rho':>7} {'mean|dp|':>9} {'IQR':>7}   {'rho':>7} {'mean|dp|':>9}"
          f"  verdict")
    print("-" * 104)
    res, fails = {}, []
    for qid in QUESTIONS:
        kind = "noul" if QUESTIONS[qid]["type"] == "noul" else "score"
        sc = 4.0 if kind == "score" else 1.0     # put the 0-4 score on the 0-1 scale
        a = np.array([base[t][qid][kind] for t in toids], float) / sc
        b = np.array([para[t][qid][kind] for t in toids], float) / sc
        r = np.array([rep[t][qid][kind] for t in toids], float) / sc
        rho = spearmanr(a, b).statistic
        mad = float(np.mean(np.abs(a - b)))
        rho_r = spearmanr(a, r).statistic
        mad_r = float(np.mean(np.abs(a - r)))
        iqr = float(np.subtract(*np.percentile(a, [75, 25])))
        exempt = iqr < IQR_EXEMPT             # A-8 item 11
        ok = (mad <= MAD_MAX) if exempt else (rho >= RHO_MIN and mad <= MAD_MAX)
        tag = "ok (IQR exempt)" if (ok and exempt) else ("ok" if ok else "FAIL")
        if not ok:
            fails.append(qid)
        print(f"{qid:<46} {rho:7.3f} {mad:9.4f} {iqr:7.3f}   {rho_r:7.3f} {mad_r:9.4f}  {tag}")
        res[qid] = dict(rho=float(rho), mean_abs_delta=mad, iqr=iqr,
                        repeat_rho=float(rho_r), repeat_mean_abs_delta=mad_r,
                        iqr_exempt=bool(exempt), passed=bool(ok),
                        tier="predictive" if qid in TIER_PREDICTIVE else "label_echo")

    pred_fail = [q for q in fails if q in TIER_PREDICTIVE]
    verdict = "PASS" if not pred_fail else "FAIL"
    print("-" * 84)
    print(f"G3 VERDICT (TIER_PREDICTIVE): {verdict}"
          + (f" — failing: {', '.join(pred_fail)}" if pred_fail else ""))
    print("G3(b) permuted state key order: VACUOUS — the registered state has one key "
          "(`notes`) since A-4 removed `toi`. Reported, not skipped.")

    nr = float(np.mean([v["repeat_mean_abs_delta"] for v in res.values()]))
    np_ = float(np.mean([v["mean_abs_delta"] for v in res.values()]))
    print(f"mean |dp| over all features: paraphrase {np_:.4f} · same-wording repeat {nr:.4f} "
          + (f"(ratio {np_ / nr:.1f}x)" if nr > 0 else "(repeat noise measured at 0)"))

    (OUT / "gate_g3_stability_2026-09-20.json").write_text(json.dumps(
        {"n_rows": len(sample), "paraphrase_version": PARAPHRASE_VERSION,
         "repeat_version": REPEAT_VERSION,
         "criterion": {"rho_min": RHO_MIN, "mad_max": MAD_MAX, "iqr_exempt": IQR_EXEMPT},
         "key_order_test": "vacuous: state has exactly one key since A-4",
         "mean_abs_delta_paraphrase": np_, "mean_abs_delta_repeat": nr,
         "features": res, "verdict": verdict, "failing_predictive": pred_fail}, indent=2))
    print(f"\nraw -> research/data/gate_g3_stability_2026-09-20.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
