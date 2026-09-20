"""Gate G5 — the leakage-stripped arm (PLAN.md §2.0, §7; PREREGISTRATION.md §5, §11.4).

G5 re-fits model D on the rows whose text does NOT restate the label, so that a D-beats-B
result cannot be explained by the model reading the answer out of the prose.

**The regex is the pre-registered artifact.** PLAN.md §7 requires it be fixed in writing
before the arm is run. §2.0 reported counts from a regex that was never recorded, so it
could not be reproduced; this module is that regex, written down and measured.

TWO CLAUSE SETS LIVE HERE, because the project changed corpora:

  COMMENTS_PATTERNS  — the original set, derived and measured on the TOI `Comments` field
                       (2,721 rows). Kept for provenance; PREREGISTRATION.md §5 quotes its
                       numbers. NOT used for the obsnotes study.
  OBSNOTES_PATTERNS  — the registered set for the `download_obsnotes` corpus (1,482 rows),
                       derived in TASK B2 and registered as PREREGISTRATION.md §11.4.

A-3 required this re-derivation, and the reason is measured: run on observer-note text, the
`Comments` set is nearly inoperative — L2, L4b and L5 fire on **zero** rows, L4a on one, L1
on 17. Only L3 does real work. It strips 8.0% of the corpus where the obsnotes set strips
24.8%, and it misses every one of the three channels that actually carry the label here.
"""
import re

# Catalogue prefixes observed in the `Comments` corpus. Every one sits at P(y=1) >= 0.995
# when it opens a short single-clause comment.
CATALOGUE_PREFIX = (
    r"TOI|WASP|HATS|HAT-P|HAT|Kepler|K2|KOI|EPIC|HD|HIP|HR|GJ|Gliese|TYC|LHS|LTT|LP|"
    r"KELT|NGTS|CoRoT|XO|TrES|TRES|Qatar|Gaia|TRAPPIST|Wendelstein|OGLE2?-TR|MASCARA|"
    r"KPS|WTS|WD|NN|AU|DS|V|L|G"
)

# --------------------------------------------------------------------------------------
# The original `Comments` set. Measured on analysis_set (2,721 rows), PREREGISTRATION §5:
# stripped 1,452 rows (53.4%) at base 0.566; G5 arm 1,269 rows / 1,222 TIC at base 0.431.
# --------------------------------------------------------------------------------------
COMMENTS_PATTERNS = {
    "L1_retired": re.compile(r"(?i)retir"),
    "L2_tfop_disposition": re.compile(r"(?i)tfop\s*(?:wg)?\s*[/-]?\s*(?:fp|fa|cp|kp)\b"),
    "L3_confirmed": re.compile(r"(?i)\b(?:validat\w*|confirmed planet|published|known planet)\b"),
    "L4a_designation_catalogue": re.compile(
        r"(?i)^(?:" + CATALOGUE_PREFIX + r")[\s-]?\d+(?:-\d+)?[a-z]?(?:\s*[A-Z])?(?:\s*[b-h])?\s*(?:/.*)?$"),
    "L4b_designation_planet_letter": re.compile(r"^[^;,.]{1,22}\s[b-h]$"),
}

# --------------------------------------------------------------------------------------
# The registered obsnotes set. Measured on analysis_set_obsnotes (1,482 rows, base 0.5378)
# on 2026-09-20; every count is in PREREGISTRATION.md §11.4 and WORKLOG.md 2026-09-20T20:2xZ.
#
#   clause                              n     %     P(y=1)   marginal (this clause alone)
#   L1_retired                         17   1.1%    0.235    10
#   L2_tfop_disposition                 0     -        -      0   (belt-and-braces)
#   L3_confirmed                      101   6.8%    0.891    19
#   L4a_designation_catalogue           1   0.1%    1.000     0   (belt-and-braces)
#   L4b_designation_planet_letter       0     -        -      0   (belt-and-braces)
#   L5_explicit_disposition             0     -        -      0   TRIPWIRE
#   L6_archive_provenance             231  15.6%    0.948    82
#   L7_structured_disposition_field   136   9.2%    0.941     0
#   L8_status_line                     97   6.5%    0.866    53
#   L9_disposition_transition          11   0.7%    0.364     4
#   -------------------------------------------------------------------------------
#   ANY (stripped)                    368  24.8%    0.875
#   G5 ARM                           1114  75.2%    0.426    (1,043 TIC)
# --------------------------------------------------------------------------------------
OBSNOTES_PATTERNS = {
    # -- disposition echo: the text restates the TFOP verdict -------------------------
    # "Retired as an NEB", "Retired as a False Alarm (FA)", "retired from SG1".
    # NOTE: unlike on `Comments` (P(y=1)=0.006) this fires in BOTH label directions here
    # -- "VPC -> VPC+ (and retired from SG1)" is a positive-direction transition.
    # Audited: 10 marginal rows, all genuine retirements.
    "L1_retired": re.compile(r"(?i)retir"),
    # Fires on 0 obsnotes rows. Kept so the clause set still covers a TFOP token if one
    # ever appears in an observer note.
    "L2_tfop_disposition": re.compile(r"(?i)tfop\s*(?:wg)?\s*[/-]?\s*(?:fp|fa|cp|kp)\b"),
    # "Status: WASP-29 published by Hellier et al. 2010", "validated planet".
    # Audited: 19 marginal rows. Over-strips a few future-tense cases ("Data will be
    # published in Lillo-Box et al. (2014) in prep") -- the safe direction per §5.
    "L3_confirmed": re.compile(r"(?i)\b(?:validat\w*|confirmed planet|published|known planet)\b"),
    "L4a_designation_catalogue": re.compile(
        r"(?i)^(?:" + CATALOGUE_PREFIX + r")[\s-]?\d+(?:-\d+)?[a-z]?(?:\s*[A-Z])?(?:\s*[b-h])?\s*(?:/.*)?$"),
    "L4b_designation_planet_letter": re.compile(r"^[^;,.]{1,22}\s[b-h]$"),
    # -- TRIPWIRE. Must fire on ZERO rows. If it fires, the Groupname corpus filter has
    # failed and Step 3 STOPS: that is a pipeline bug, not a finding (§5.1, A-13).
    "L5_explicit_disposition": re.compile(r"(?i)\b(?:master|phot|spec)\s*disp\s*:"),
    # -- archive provenance: not a disposition statement, but near-deterministic --------
    # "Extracted KOI178 observing note from ExoFOP-Kepler on 2020-11-02".
    # 231 rows at P(y=1)=0.948 -- the largest near-deterministic channel in this corpus.
    # Audited: the 82 marginal rows carry NO disposition statement at all; they are
    # stripped purely because the provenance string predicts the label. See §11.4 for
    # why that still belongs in G5, and for the without-L6 sensitivity arm.
    "L6_archive_provenance": re.compile(r"(?i)ExoFOP-Kepler|ExoFOP-K2|\bKOI[\s-]?\d|\bEPIC\s?\d"),
    # -- structured disposition fields carried in the Kepler/K2 extracts ---------------
    # "Possible planetary candidate = Yes" (69 rows, P=0.957), "Possible false positive
    # = Yes". This is the Kepler/K2 analogue of L5's "Master Disp:". Fully subsumed by
    # L6 today (0 marginal rows); kept because it is the explicit-disposition clause and
    # must not depend on the provenance string staying the same.
    "L7_structured_disposition_field": re.compile(r"(?i)Possible\s+[a-z ]+=\s*(?:Yes|No)"),
    # -- the DACE/CORALIE summary line -------------------------------------------------
    # "Status: Solved by ESPRESSO-GTO (Sozzetti et al. 2021)", "Status: WASP-72, Gillon
    # et al. 2013". Audited: 53 marginal rows, MIXED -- most carry the verdict, but a few
    # carry only an observation ("Status: No significant RV variation ..., SB2 ruled
    # out"). Over-strips those, which §5 names as the correct direction.
    "L8_status_line": re.compile(r"(?i)\bStatus:\s"),
    # -- explicit disposition transitions ----------------------------------------------
    # "PC => NEB", "VPC -> VPC+", "PC->CPC". Audited: all 4 marginal rows genuine.
    "L9_disposition_transition": re.compile(
        r"(?i)\b(?:A?PC|VPC|CP|KP|FP|FA|CPC)\s*(?:->|=>|→)\s*"
        r"(?:A?PC|VPC|CP|KP|FP|FA|CPC|NEB|BEB|EB)\b"),
}

# The clause whose firing means the pipeline is broken, not that a leak was found.
TRIPWIRE = "L5_explicit_disposition"

# Not leakage, and deliberately LEFT IN the G5 arm: these are observational findings, which
# are exactly what model D is supposed to be using. Recorded so the choice is visible.
#   NEB / BEB                34 rows, P(y=1)=0.059  -- an observation that a nearby star eclipses
#   "is an eclipsing binary" 17 rows, P(y=1)=0.059  -- a spectroscopic conclusion
#   "false positive"         31 rows, P(y=1)=0.613  -- ABOVE the 0.5378 base rate. Audit 01
#       read this phrase as a label marker; at full scale it is mostly speculation
#       ("I wouldn't be surprised if this is a false positive"), not a disposition.


def leakage_markers(text: str, patterns: dict | None = None) -> list[str]:
    """Names of every leakage clause that fires on this text. Empty list == clean."""
    s = (text or "").strip()
    return [name for name, rx in (patterns or OBSNOTES_PATTERNS).items() if rx.search(s)]


def is_leaky(text: str, patterns: dict | None = None) -> bool:
    """True if the text carries a label marker and is excluded from the G5 arm."""
    return bool(leakage_markers(text, patterns))


# Backwards compatibility: the Comments-era call site passed a comment and expected the
# Comments clause set.
LEAKAGE_PATTERNS = COMMENTS_PATTERNS
