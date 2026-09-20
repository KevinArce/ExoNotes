"""Gate G5 — the leakage-stripped arm (PLAN.md §2.0, §7).

PLAN.md §2.0 measured that ~48% of the labelled corpus carries a near-deterministic label
marker: a bare planet designation predicts y=1 at P=0.999, `retired` predicts y=0 at
P=0.006, `TFOP FP` at P=0.000. G5 re-fits on the rows that survive stripping those markers.

**The regex is the pre-registered artifact.** PLAN.md §7 requires it be fixed in writing
before the arm is run. §2.0 reported counts from a regex that was never recorded, so it
could not be reproduced; this module is that regex, written down and measured.

Measured on `analysis_set` (2,721 rows) on 2026-09-20 — see PREREGISTRATION.md §5:

    stripped   1,452 rows (53.4%)   base rate 0.566
    G5 arm     1,269 rows            1,222 TIC   base rate 0.431

This strips MORE than §2.0's unrecorded regex (which left 1,417 rows). Over-stripping is the
safe direction for G5: a surviving leak would let the gate pass on label echo, which is the
exact failure G5 exists to detect. Under-stripping cannot be detected after the fact.
"""
import re

# Catalogue prefixes observed in the corpus. Every one of these sits at P(y=1) >= 0.995
# (TOI 0.995, all others 1.000) when it opens a short single-clause comment.
CATALOGUE_PREFIX = (
    r"TOI|WASP|HATS|HAT-P|HAT|Kepler|K2|KOI|EPIC|HD|HIP|HR|GJ|Gliese|TYC|LHS|LTT|LP|"
    r"KELT|NGTS|CoRoT|XO|TrES|TRES|Qatar|Gaia|TRAPPIST|Wendelstein|OGLE2?-TR|MASCARA|"
    r"KPS|WTS|WD|NN|AU|DS|V|L|G"
)

LEAKAGE_PATTERNS = {
    # L1 -- "retired as NEB", "retired as TFOP FP/SB1".      n=488,  P(y=1)=0.006
    "L1_retired": re.compile(r"(?i)retir"),
    # L2 -- an explicit TFOP disposition token.              n=543,  P(y=1)=0.006
    "L2_tfop_disposition": re.compile(r"(?i)tfop\s*(?:wg)?\s*[/-]?\s*(?:fp|fa|cp|kp)\b"),
    # L3 -- an explicit statement of confirmation.           n=21,   P(y=1)=0.905
    "L3_confirmed": re.compile(r"(?i)\b(?:validat\w*|confirmed planet|published|known planet)\b"),
    # L4a -- the whole comment is a catalogue designation.   n=795,  P(y=1)=0.999
    "L4a_designation_catalogue": re.compile(
        r"(?i)^(?:" + CATALOGUE_PREFIX + r")[\s-]?\d+(?:-\d+)?[a-z]?(?:\s*[A-Z])?(?:\s*[b-h])?\s*(?:/.*)?$"),
    # L4b -- a short single clause ending in a bare planet letter, which catches the Bayer
    # and white-dwarf forms L4a misses ("pi Men c", "55 Cnc e", "DS Tuc A b", "WD 1856+534 b").
    # Audited: strips exactly 5 rows beyond L4a, all genuine designations, no false positives.
    "L4b_designation_planet_letter": re.compile(r"^[^;,.]{1,22}\s[b-h]$"),
}


def leakage_markers(comment: str) -> list[str]:
    """Names of every leakage clause that fires on this comment. Empty list == clean."""
    s = (comment or "").strip()
    return [name for name, rx in LEAKAGE_PATTERNS.items() if rx.search(s)]


def is_leaky(comment: str) -> bool:
    """True if the comment carries a label marker and is excluded from the G5 arm."""
    return bool(leakage_markers(comment))
