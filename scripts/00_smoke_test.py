"""Original 4-case smoke test (2026-09-19). SUPERSEDED by scripts/025_question_gate.py,
which runs 23 cases drawn from real corpus comments. Kept as the record of the first
live measurements written up in research/04.

Extend CASES to ~20: for EACH question, its clear positive, its clear negative,
and its nearest confusable. Inspect every answer by eye before the full corpus run.
Question set below is the VERIFIED version - see research/04_first_live_measurements.md.
"""
import json, os, urllib.request, pathlib, time

# load .env without printing secrets
for line in (pathlib.Path(__file__).resolve().parent.parent / ".env").read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ[k.strip()] = v.strip().strip('"').strip("'")

KEY = os.environ.get("TYPESAFE_API_KEY", "")
if not KEY:
    raise SystemExit("no TYPESAFE_API_KEY found")

QUESTIONS = {
    # NOTE: `names_alternate_eclipse_source` was DROPPED as redundant - see research/04 section 4.2.
    "reports_offset_eclipsing_binary": {"type": "noul", "instructions":
        "Does `comment` report an eclipsing binary at a position offset from the target star - described as "
        "nearby, background, NEB, a contaminating star, or at a stated angular separation? "
        "Answer no if an eclipsing binary is proposed for the target star itself."},
    "reports_on_target_detection": {"type": "noul", "instructions":
        "Does `comment` report a follow-up detection confirmed to be on the target star?"},
    "asserts_ephemeris_problem": {"type": "noul", "instructions":
        "Does `comment` assert a specific problem with the orbital period or epoch - that it is wrong, aliased, "
        "a harmonic or multiple of the true value, or requires revision? Answer no if the text affirms the "
        "ephemeris, even with hedging such as 'likely' or 'probably'."},
    "references_other_object": {"type": "noul", "instructions":
        "Does `comment` cross-reference another TOI, a known planet designation, or a duplicate identifier?"},
    "author_certainty": {"type": "score", "instructions":
        "How certain is the author of `comment` about the conclusion they state?",
        "criteria": [
            "Purely speculative: raises a possibility with no supporting observation",
            "Tentative: hedged language, conclusion not settled",
            "Qualified: a conclusion stated together with explicit caveats",
            "Confident: a clear conclusion supported by a described observation",
            "Definitive: stated as settled fact, case closed"]},
    "evidence_depth": {"type": "score", "instructions":
        "How much observational evidence does `comment` actually describe?",
        "criteria": [
            "No observation described at all",
            "A remark or opinion with no data referenced",
            "One follow-up observation referenced",
            "Several follow-up observations referenced",
            "Multiple independent facilities or techniques described"]},
}

CASES = [
    ("A_neb_retired",
     "SG1 observed 2023-04-12 in Rc. NEB detected at 1.2 arcmin NE, depth consistent with TESS signal. Target star clear. Retired as NEB."),
    ("B_doubt_vshape",
     "V-shaped event, possible EB. Period may be 2x the reported value. Needs RV follow-up before further photometry."),
    ("C_on_target_pub",
     "Confirmed on-target by LCO 1m in zs. Depth consistent with TESS. Published as TOI-1234 b in Smith et al. 2024."),
    ("D_empty_ish",
     "period is likely correct"),
]

def call(state, questions):
    body = json.dumps({"model": "jev-latest", "state": state, "questions": questions}).encode()
    req = urllib.request.Request(
        "https://api.typesafe.ai/v1/systemone", data=body,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.loads(r.read())
    return out, (time.time() - t0) * 1000

results = {}
for name, text in CASES:
    state = {"toi": "TOI-0000.01", "comment": text}   # fixed key order
    try:
        out, ms = call(state, QUESTIONS)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} on {name}: {e.read().decode()[:400]}")
        raise SystemExit(1)
    results[name] = out
    print(f"\n=== {name}  ({ms:.0f} ms, model={out['model']}, in={out['usage']['input_tokens']}, out={out['usage']['output_tokens']}) ===")
    print(f"    {text[:95]}")
    for qid, a in out["answers"].items():
        if a["type"] == "noul":
            print(f"    {qid:35s} noul={a['noul']:.3f}")
        else:
            print(f"    {qid:35s} score={a['score']:.3f} conf={a['confidence']:.3f} p={ {k: round(v,3) for k,v in a['probabilities'].items()} }")

outfile = pathlib.Path(__file__).resolve().parent.parent / "data" / "smoke_out.json"
outfile.parent.mkdir(parents=True, exist_ok=True)
outfile.write_text(json.dumps(results, indent=2))
print("\nraw responses saved")
