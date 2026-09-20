"""Frozen question set for ExoNotes — the single source of truth.

`PREREGISTRATION.md` quotes this file. `scripts/025_question_gate.py` imports it, so the
questions that were tested and the questions that are pre-registered cannot drift apart.

QUESTION_SET_VERSION is part of the Jev cache key (PLAN.md §6 Step 3). Bump it on ANY edit
to QUESTIONS — an edit that does not bump it will silently serve stale cached answers.

Gate result for 2026-09-20.r4: 101/103 assertions passed on 23 real comments.
See research/05_question_gate.md and WORKLOG.md 2026-09-20T00:15Z.
"""

QUESTION_SET_VERSION = "2026-09-20.r4"

TIER_PREDICTIVE = {
    "reports_offset_eclipsing_binary": {
        "type": "noul",
        # r2 wording (from research/04) was a COIN FLIP on real terse text: it led with the
        # geometry ("at a position offset"), but real comments write only the acronym.
        # r3 leads with the classification and expands the acronyms. See WORKLOG 00:08Z.
        "instructions": (
            "Does `comment` place the eclipsing binary on a star other than the target? The "
            "abbreviations NEB (nearby eclipsing binary) and BEB (background eclipsing binary) mean "
            "exactly this and count on their own - no separation, direction, or star name is needed. "
            "A contaminating star, a named nearby TIC given as the eclipse source, or a stated angular "
            "separation also count. Answer no for a bare EB with no N or B prefix, for SB1, SB2, SEB1 "
            "or SEB2, and for a crowded field on its own - none of those place the eclipse on another "
            "star. Answer no if the text gives only a planet or star designation and says nothing "
            "about an eclipsing binary."),
        "criteria": {
            "true": "The eclipse is placed on a star other than the target, including by the bare abbreviation NEB or BEB",
            "false": "No eclipsing binary, or one attributed to the target itself (bare EB, SB1, SB2, SEB1, SEB2)"},
    },
    "reports_stellar_companion_or_blend": {
        "type": "noul",
        "instructions": (
            "Does `comment` state that a second star is present in or near the photometric aperture - "
            "described as a companion star, a blend, a diluted or contaminated signal, a crowded field, "
            "two stars in the same pixel, a named nearby TIC, or a depth-aperture correlation (written "
            "with or without the hyphen, e.g. 'depth aperture correlation')? Answer no if the text "
            "gives only the signal's position, such as a centroid offset with no second star named, or "
            "only states that the target itself is a binary. An eclipsing binary reported without "
            "naming or locating a second star in the aperture does not count."),
        "criteria": {
            "true": "A second star is stated to be in or near the aperture, or a depth-aperture correlation is reported",
            "false": "No second star; a centroid offset alone, or the target itself being a binary, does not count"},
    },
    "mentions_spectroscopic_binary": {
        "type": "noul",
        "instructions": (
            "Does `comment` report spectroscopic or radial-velocity evidence of a binary - written as "
            "SB1, SB2, SEB1, SEB2, a double-lined spectrum, or a large radial-velocity variation? "
            "Answer no if the text reports only a photometric eclipsing binary (EB, NEB, BEB) with no "
            "spectroscopic or radial-velocity evidence."),
        "criteria": {
            "true": "Spectroscopic or radial-velocity binary evidence is stated, including the bare abbreviations SB1, SB2, SEB1, SEB2",
            "false": "Photometry only; an eclipsing binary reported without spectroscopy or radial velocities does not count"},
    },
    "asserts_ephemeris_problem": {
        "type": "noul",
        # Wording verified in research/04 §4.1 (0.890 / 0.050). Kept verbatim.
        "instructions": (
            "Does `comment` assert a specific problem with the orbital period or epoch - that it is wrong, "
            "aliased, a harmonic or multiple of the true value, or requires revision? Answer no if the text "
            "affirms the ephemeris, even with hedging such as 'likely' or 'probably'."),
        "criteria": {
            "true": "A specific defect in the period or epoch is asserted",
            "false": "The period or epoch is not mentioned, or is mentioned without asserting a defect"},
    },
    "mentions_instrumental_artifact": {
        "type": "noul",
        "instructions": (
            "Does `comment` attribute the signal, or part of it, to an instrumental, data-processing, or "
            "solar-system cause - described as a systematic, an artifact, scattered light, a momentum "
            "dump, a data gap, or an asteroid crossing the aperture? A hedged attribution such as "
            "'possible systematic' still counts. Answer no when no such cause is named: weak signal on "
            "its own (low SNR, low MES), a depth-aperture correlation, a centroid offset, or a plotting "
            "or processing tool that failed are not attributions to an instrumental cause. A disposition "
            "is not an instrumental cause: 'TFOP FP', 'FP', 'FA' and 'retired' say that the candidate "
            "was rejected, not that an instrument produced the signal. Answer no unless an instrumental, "
            "processing, or solar-system cause is actually named in the text."),
        "criteria": {
            "true": "An instrumental, processing, or solar-system cause is named for the signal, hedged or not",
            "false": "No such cause named; weak signal, a depth-aperture correlation, a centroid offset, or a failed tool alone do not count"},
    },
    "describes_transit_morphology": {
        "type": "noul",
        "instructions": (
            "Does `comment` describe the shape, depth behaviour, or duration of the event itself - "
            "described as V-shaped, flat-bottomed, an odd-even depth difference, a secondary eclipse "
            "(the bare word 'secondary' counts), a duration too long or too short for the period, or a "
            "depth too deep or too shallow? Answer "
            "no if the text only reports the signal's strength or position, or only gives a disposition "
            "or false-positive category such as FP, EB, NEB or SB1, or only reports a depth-aperture "
            "correlation - that describes how the measured depth changes with the photometry aperture, "
            "not the shape of the event."),
        "criteria": {
            "true": "The event's own shape, depth behaviour, or duration is described",
            "false": "Only strength, position, a disposition category, or a depth-aperture correlation is given"},
    },
    "author_certainty": {
        "type": "score",
        "instructions": "How certain is the author of `comment` about the conclusion they state?",
        "criteria": [
            "Purely speculative: raises a possibility with no supporting observation",
            "Tentative: hedged language such as 'possible', 'potential', 'may be'; conclusion not settled",
            "Qualified: a conclusion stated together with explicit caveats",
            "Confident: a clear conclusion supported by a described observation",
            "Definitive: stated as settled fact, case closed"],
    },
    "evidence_depth": {
        "type": "score",
        "instructions": "How much observational evidence does `comment` actually describe?",
        "criteria": [
            "No observation described at all",
            "A remark, a label, or a statement of where the candidate was found, with no observation of it described",
            "One observation of the candidate referenced",
            "Several observations of the candidate referenced",
            "Multiple independent facilities or techniques described"],
    },
}

TIER_LABEL_ECHO = {
    "indicates_retired_or_rejected": {
        "type": "noul",
        "instructions": (
            "Does `comment` state that this candidate has been retired, rejected, or classified as a "
            "false positive or false alarm - for example 'retired as NEB', 'TFOP FP', 'FA'? Answer no "
            "if the text only says what the signal is, or only describes a problem with it, without "
            "stating that it was retired, rejected, or classified FP or FA. Identifying the signal as "
            "an eclipsing binary, a binary, or a variable is not by itself a retirement."),
        "criteria": {
            "true": "A retirement, rejection, or false-positive/false-alarm classification is stated",
            "false": "Only a description of the signal or a doubt about it; no retirement, rejection, FP or FA stated"},
    },
    "indicates_confirmed_planet": {
        "type": "noul",
        "instructions": (
            "Does `comment` state that this candidate is a confirmed, validated, or published planet? "
            "Answer no if the text gives only a catalogue designation such as 'WASP-68 b' or 'K2-115 b' "
            "without stating that it was confirmed, validated, or published, and answer no if the text "
            "states the candidate is a false positive, a false alarm, or was retired."),
        "criteria": {
            "true": "The text states the candidate is confirmed, validated, or published",
            "false": "No such statement; a bare planet designation on its own does not count"},
    },
    "contains_object_designation": {
        "type": "noul",
        # Renamed from `references_other_object`. See WORKLOG: a bare self-designation is not
        # "another" object, but it IS the leakage channel measured in PLAN.md §2.0.
        "instructions": (
            "Does `comment` contain a catalogue designation for a planet or a star - for example "
            "'WASP-68 b', 'K2-115 b', 'Kepler-96 b', 'TOI-836 c', or a bare TIC number? Answer no if "
            "the text names only instruments, surveys, working groups, people, or publications - for "
            "example 'QLP search', 'SG1', 'TFOP', 'WASP-South', 'LCO', 'Hord et al 2024'."),
        "criteria": {
            "true": "A planet or star catalogue designation appears",
            "false": "Only instruments, surveys, groups, people, or papers are named"},
    },
}
QUESTIONS = {**TIER_PREDICTIVE, **TIER_LABEL_ECHO}
