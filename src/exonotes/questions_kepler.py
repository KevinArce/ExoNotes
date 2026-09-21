"""Frozen question set for the Kepler transfer test (PREREGISTRATION.md section 11.10) -- the
single source of truth for the CFOP corpus.

A NEW module under a NEW version string, never an edit to `questions.py`: `2026-09-20.r6` is
frozen for the TESS study (A-40 40.11), and QUESTION_SET_VERSION sits inside the Jev cache key,
so reusing it would let Kepler and TESS answers collide.

-------------------------------------------------------------------------------------------
How this set was chosen -- WITHOUT any Kepler label (WORKLOG 2026-09-21, step 4a).

TESS chose topics partly by each crude cue's |AUC| against the label on its own corpus (r5
docstring, A-19, A-23): selection on the evaluation data. Here the topics come from TESS's
evidence -- the judgments that carried signal on a DIFFERENT corpus -- and are kept or retired
on LABEL-FREE prevalence in CFOP, against a 5%-of-rows floor (TESS retired everything at
<= 4.7%). Subject-matter prevalence, over-broad regex, all 4,720 corpus rows, no `y` read:

    imaging: nothing found             62.8%   kept   imaging_reports_no_companion
    imaging: companion found           48.2%   kept   imaging_reports_companion_present
    spectroscopy: non-planetary         7.1%   kept   spectroscopy_indicates_nonplanetary_companion
    spectroscopy: no binary signature  14.0%   NEW    spectroscopy_reports_no_binary_signature
    recon finished / escalated          9.4%   kept   recon_reported_concluded (r6's closure, widened)
    evolved-host wording                2.2%   RETIRED -- below the floor (24.6% on TESS)

`spectroscopy_consistent_with_planet` is not carried: on CFOP the positive reconnaissance
result is "no significant velocity variation" / "Looks good", which r6 deliberately answers NO
to ("reports only that the velocity shift was small ... and draws no conclusion"). The Kepler
recon community states the pass that way, so it is asked for directly, as its own question.

Deliberately NOT read by any predictive question: the `Possible <x> = Yes/No` structured
fields where they carry a disposition or a catalogue lookup -- `Possible false positive = ...`
and `Possible eclipsing binary = Yes (Kepler Eclipsing Binary Catalog ...)`. TESS's L7 names
these the Kepler/K2 analogue of `Master Disp:` (A-24); they belong to the label-echo tier.
`Possible nearby companion = Yes (...)` IS read, by the companion question: it reports an
imaging observation, not a disposition. (G5's registered L7 strips all of them regardless.)
-------------------------------------------------------------------------------------------
"""

QUESTION_SET_VERSION = "kepler-2026-09-21.r3"

# Corpus cues these questions are written against, verified verbatim in CFOP text:
#   imaging clean     "Robo-AO LP600-imaging of KOI-5952 on 2014-08-31 No companions detected within 4.0\""
#                     "No secondary sources were detected." (WIYN / Gemini speckle)
#                     "No companions were detected on the field of view." (ARIES AO)
#                     "No companions visible from 2\" to 5\" away from the star" (Lick 1-m)
#   imaging detection "Possible nearby companion = Yes (2.00\", 4.09\" companion (UKIRT))"
#                     "Nearby stars detected in Robo-AO LP600-imaging of KOI-2848 Separation: 2.30\""
#                     "The source is found to be double with the fainter, second source ..."
#                     "There is a companion 6-7\" away to the SE."
#   no-result imaging "A HIRES guider snap is avaible in .pdf and .fits formats"
#   spec -> binary    "CCF clearly double-peaked => SB2", "This looks like a double-lined ... spectrum"
#                     "There is a large velocity variation (~20 km/s)"
#   spec -> clean     "there is no significant velocity variation", "Looks good.",
#                     "the correlation peak is clean and strong"
#   recon closed      "No more recon is needed.", "It's time for more precise velocities."
#
# HEADER BLOCKS ARE THE SAME TRAP AS ON TESS. Recon notes open with a machine-written line:
#   "K01848.01, 19:06:50.57 43:02:36.42, V=13.6, ... 2012-04-04 MCDONALD, pha=21.20, RV=20.702,
#    Teff=5750+/-125, log(g)=4.00+/-0.25, Vrot=8.0+/-2.0, [m/H]=0.00+/-0.25, ccf=0.747"
#   "2010-08-06 LICK, phase=28.69, Teff=4750, log(g)=4.5, Vrot=4, Vrad=-26.250, ccfPeak=0.952"
# `RV=` / `Vrad=` is the ABSOLUTE radial velocity of the star, and `ccf=` / `ccfPeak=` is a
# number the model must not compare (PLAN.md section 1). Every spectroscopy question names this.

TIER_PREDICTIVE = {
    "imaging_reports_no_companion": {
        "type": "noul",
        "instructions": (
            "Does `notes` state that imaging of this target found no companion, no secondary "
            "source, and no nearby star, at least over some range of separations? Sentences such "
            "as 'No companions detected within 4.0\"', 'No secondary sources were detected', 'No "
            "companions were detected on the field of view' and 'No companions visible from 2\" "
            "to 5\" away from the star' say exactly this and count on their own. So do 'WIYN "
            "speckle image reveals a single star' and 'KOI 273 is a single star as observed "
            "within a box of size 2.76 x 2.76 arcsec': a single star means nothing else was "
            "found. Answer yes even "
            "when the text also reports a companion somewhere else, for example 'No companions "
            "visible from 2\" to 5\" away ... There is a companion 6-7\" away': the statement "
            "that nothing was found over one range still appears. Most imaging notes also name "
            "the telescope, the filter, the field of view, the seeing, or offer plots and FITS "
            "files; those sentences are not findings and do not count against one. Answer no "
            "when no such statement appears at all - when the text only says an image was taken "
            "or is available, as in 'A HIRES guider snap is avaible in .pdf and .fits formats', "
            "or when the only imaging result reported is a companion or nearby star."),
        "criteria": {
            "true": {
                "what": "Imaging is reported to have found nothing - no companion, secondary source, or nearby star - over at least some range",
                "examples": ["Robo-AO LP600-imaging of KOI-5952 on 2014-08-31 No companions detected within 4.0\"",
                             "No secondary sources were detected.",
                             "No companions were detected on the field of view.",
                             "No companions visible from 2\" to 5\" away from the star down to 19th magnitude."]},
            "false": {
                "what": "No imaging result is reported, or the only result is that something was found",
                "examples": ["A HIRES guider snap is avaible in .pdf and .fits formats",
                             "Possible nearby companion = Yes (2.00\", 4.09\" companion (UKIRT))",
                             "Nearby stars detected in Robo-AO LP600-imaging of KOI-2848 Separation: 2.30\""]},
        },
    },
    "imaging_reports_companion_present": {
        "type": "noul",
        # Asked as its own proposition, not as the negation of the question above: jev-1.13's
        # jaggedness page says P(noul) and 1 - P(not noul) are not interchangeable.
        "instructions": (
            "Does `notes` state that a companion star, a nearby star, or a second source was "
            "actually seen near this target - in an image, on a guide camera, or on a slit "
            "viewer? A report of 'Possible nearby companion = Yes' with a separation, 'Nearby "
            "stars detected' with a separation, 'The source is found to be double', 'There is a "
            "companion 6-7\" away', 'Equally bright star 10\" to the South' and 'Faint star ~4\" "
            "to south is well off slit' all count, whatever the separation. Notes on one target "
            "often come from several observers and can disagree: one reports 'No companions "
            "detected within 4.0\"' while another reports 'Possible nearby companion = Yes (3.39\" "
            "companion (UKIRT))'. A report that nothing was found does not cancel a report that "
            "a star was seen; if any report of a seen star appears, answer yes. Answer no if the "
            "text reports only that nothing was found. Answer no if "
            "the text only says an image was taken or is available, or only gives plots, contour "
            "maps or limiting magnitudes without saying a star was found. This question is about "
            "a star that was SEEN next to the target. A companion inferred from a spectrum or "
            "from radial velocities - a double-lined spectrum, an SB1 or SB2, a large velocity "
            "variation - is not a star seen near the target and does not count. A listing in the "
            "Kepler Eclipsing Binary Catalog is not an imaging detection and does not count."),
        "criteria": {
            "true": {
                "what": "Imaging reports a companion, nearby star, or second source as actually present",
                "examples": ["Possible nearby companion = Yes (2.00\", 4.09\" companion (UKIRT))",
                             "Nearby stars detected in Robo-AO LP600-imaging of KOI-2848 Separation: 2.30\"",
                             "The source is found to be double with the fainter, second source",
                             "Equally bright star 10\" to the South.",
                             "Faint star ~4\" to south is well off slit."]},
            "false": {
                "what": "Nothing was found, no imaging result is given, or the companion is inferred only from spectra",
                "examples": ["No companions detected within 4.0\"",
                             "A HIRES guider snap is avaible in .pdf and .fits formats",
                             "CCF clearly double-peaked => SB2",
                             "Possible eclipsing binary = Yes (Kepler Eclipsing Binary Catalog v2)"]},
        },
    },
    "spectroscopy_indicates_nonplanetary_companion": {
        "type": "noul",
        # r6's scope is kept: evidence-agnostic (r6 counts NEB/BEB and "This system is an
        # eclipsing binary"). An observer's light-curve conclusion -- "alternating eclipses
        # (odd and even) are of different depths, so this one is a clear stellar eclipsing
        # binary" -- counts here as it would on TESS. What is excluded is the catalogue
        # listing, which is a lookup, not a conclusion drawn from these observations.
        "instructions": (
            "Does `notes` conclude that the signal is caused by a stellar or brown-dwarf "
            "companion rather than a planet - that the target is an eclipsing or spectroscopic "
            "binary, or that its companion is too massive to be a planet? A double-lined or "
            "double-peaked spectrum, an SB1 or SB2, a second set of lines, a large velocity "
            "variation between observations, eclipses of alternating depth showing a stellar "
            "eclipsing binary, or a nearby or background eclipsing binary (NEB, BEB or BGEB) "
            "named as the source all count, as does a centroid or difference-image conclusion "
            "that the transit signal comes from another star - 'Difference image shows that "
            "nearby source is producing the transit signal', 'Current transit signal is from "
            "background star', 'Obvious BGEB at col=468; row=135'. Statements such as 'CCF clearly double-peaked => SB2', 'a nice double-lined "
            "orbital solution', 'There is a large velocity variation (~20 km/s)', 'this one is a "
            "clear stellar eclipsing binary' count, including when hedged with 'possibly', "
            "'looks like' or 'these are just initial musings' and followed by a request for "
            "another observation to be sure. Answer no when the conclusion runs the other way - "
            "no significant "
            "velocity variation, a single set of lines, 'Looks good', 'our RVs show no evidence "
            "of a binary' - or when a binary is raised and then rejected. Answer no for a "
            "listing in a catalogue such as 'Possible eclipsing binary = Yes (Kepler Eclipsing "
            "Binary Catalog)' when that listing is the only evidence: a catalogue listing is not "
            "a conclusion drawn from these observations. The listing does not cancel a "
            "conclusion stated elsewhere in the text - if the text also reports a double-lined "
            "orbital solution or a large velocity variation, answer yes. Ignore any field that "
            "reads 'Possible false positive = Yes (...)' or 'Possible false positive = No (...)', "
            "including what is written inside its parentheses: that field is a disposition "
            "record, not a conclusion drawn here. Answer no for a companion star seen only in "
            "imaging: a nearby star "
            "is not by itself a conclusion that it causes the signal. Do not use the numbers in "
            "the machine-written header line: `RV=` and `Vrad=` are the star's absolute radial "
            "velocity, not a variation, and `ccf=` or `ccfPeak=` is a number that says nothing "
            "about a second star on its own."),
        "criteria": {
            "true": {
                "what": "The text concludes, even tentatively, that a stellar or brown-dwarf companion or a binary causes the signal",
                "examples": ["2013-08-20 MCDONALD CCF clearly double-peaked => SB2",
                             "We have 13 TRES observations and a nice double-lined orbital solution.",
                             "There is a large velocity variation (~20 km/s).",
                             "alternating eclipses (odd and even) are of different depths, so this one is a clear stellar eclipsing binary"]},
            "false": {
                "what": "No such conclusion, the opposite conclusion, a catalogue listing, or a companion seen only in imaging",
                "examples": ["there is no significant velocity variation",
                             "Looks good. Let's get an observation at phase 0.75",
                             "Possible eclipsing binary = Yes (Kepler Eclipsing Binary Catalog v2)",
                             "McDonald 2.7m R=60K recon spectrum obtained."]},
        },
    },
    "spectroscopy_reports_no_binary_signature": {
        "type": "noul",
        # NEW for Kepler. The positive reconnaissance result on CFOP is stated as the ABSENCE
        # of a binary signature, which r6's spectroscopy_consistent_with_planet answers NO to.
        "instructions": (
            "Does `notes` report that reconnaissance spectra of this target look clean - no "
            "significant velocity variation between observations, a single set of lines, a clean "
            "or strong correlation peak, or a plain verdict such as 'Looks good'? The terse forms "
            "'Recon: single lined', 'single-lined' and 'Looks OK' count. If such a verdict "
            "appears anywhere in the text, answer yes, even when later sentences raise other "
            "doubts - about which star was observed, or about the ephemeris - that are not a "
            "double-lined spectrum or a large velocity variation. Statements such "
            "as 'there is no significant velocity variation', 'there's no velocity variation. "
            "It's time for more precise velocities', 'the correlation peak is clean and strong' "
            "and 'Looks good' all count, including when the author also asks for one more "
            "spectrum at another phase. A small velocity variation that the author describes as "
            "consistent with a planet also counts, because it is a statement that no stellar "
            "binary was seen: 'The single order velocities show variation consistent with a "
            "planetary companion' and 'There is ~300m/s velocity variation which indicates a "
            "~6.8Mjupiter planet' count. Ignore any field that reads 'Possible false positive = "
            "Yes (...)' or 'Possible false positive = No (...)', including what is written inside "
            "its parentheses. Answer no if the text reports a double-lined or "
            "double-peaked spectrum, an SB1 or SB2, or a large velocity variation. Answer no if "
            "the text only says that a spectrum was obtained, at what phase, with what "
            "instrument, or with what signal-to-noise, and gives no verdict on it. Do not use the "
            "numbers in the machine-written header line - `RV=`, `Vrad=`, `ccf=`, `ccfPeak=`, "
            "`Vrot=` - to decide: judge only the words the author wrote about the spectra."),
        "criteria": {
            "true": {
                "what": "The author reports the spectra as clean: no significant velocity variation, single-lined, or 'looks good'",
                "examples": ["The phase coverage is good and there is no significant velocity variation",
                             "The phase coverage is good and there's no velocity variation. It's time for more precise velocities.",
                             "The rotation is a bit rapid, but the correlation peak is clean and strong.",
                             "Looks good. Let's get an observation at phase 0.75",
                             "The single order velocities show variation consistent with a planetary companion."]},
            "false": {
                "what": "A binary signature is reported, or a spectrum is only logged with no verdict",
                "examples": ["CCF clearly double-peaked => SB2",
                             "There is a large velocity variation (~20 km/s).",
                             "2013-05-26 TRES, pha=441.75, SNRe=28.5",
                             "McDonald 2.7m R=60K recon spectrum obtained."]},
        },
    },
    "recon_reported_concluded": {
        "type": "noul",
        # r6's followup_reported_concluded, widened to the Kepler form of the same verdict:
        # the recon community closed a target by sending it on to precise velocities.
        "instructions": (
            "Does `notes` state that reconnaissance of this target is finished - that no more "
            "recon spectra or observations are needed, or that it is time to move on to precise "
            "radial velocities? Sentences such as 'No more recon is needed', 'For now, no more "
            "recon is needed', 'It's time for more precise velocities', 'I don't think this "
            "warrants more recon right now' and 'This candidate needs no further Keck-HIRES "
            "spectra' count, including when a word is misspelled, as in 'needs nor further'. "
            "Answer no if "
            "the text asks for more reconnaissance, for example \"Let's get another observation "
            "at opposite quadrature\", \"Let's fill out the phase coverage\" or 'We'll have to "
            "take a closer look at this one', and never states that recon is finished. If the "
            "text asks for more observations in one place and states that recon is finished in "
            "another, answer yes, because the question is whether that statement appears at all. "
            "Answer no if the text only logs that a spectrum or image was taken."),
        "criteria": {
            "true": "The text states that reconnaissance is finished, or that the target should move on to precise radial velocities",
            "false": "The text asks for more reconnaissance, only logs an observation, or says nothing about whether recon is finished",
        },
    },
    "author_certainty": {
        "type": "score",
        "instructions": (
            "How certain is the author of `notes` about the conclusion they state about this "
            "target? Judge the words the author wrote, not the machine-written header lines of "
            "measurements, and not sentences that only describe the instrument, the field of "
            "view, or where the files are."),
        "criteria": [
            "Purely speculative: raises a possibility with no supporting observation",
            "Tentative: hedged language such as 'possible', 'perhaps', 'may be'; the conclusion is not settled",
            "Qualified: a conclusion stated together with explicit caveats or a request for more data",
            "Confident: a clear conclusion supported by a described observation",
            "Definitive: stated as settled fact, case closed",
        ],
    },
}

TIER_LABEL_ECHO = {
    "indicates_false_positive_or_retired": {
        "type": "noul",
        "instructions": (
            "Does `notes` state that this candidate is a false positive, has been rejected or "
            "retired, or carry the field 'Possible false positive = Yes'? 'This KOI is dead. Move "
            "to inactive.' counts. Answer no for the field 'Possible false positive = No'. Answer "
            "no if the text only describes what the signal is or an observation - 'likely a "
            "background eclipsing binary', 'this is a small star eclipsing the target', a "
            "companion, a double-lined spectrum, a listing in the Kepler Eclipsing Binary Catalog "
            "- without stating that the candidate is a false positive, rejected, retired, dead or "
            "inactive. A description that implies a false positive is not a statement that it "
            "is one."),
        "criteria": {
            "true": "A false-positive classification, a rejection, a retirement, or 'Possible false positive = Yes' is stated",
            "false": "No such statement; 'Possible false positive = No', or only a description of an observation",
        },
    },
    "indicates_confirmed_planet": {
        "type": "noul",
        "instructions": (
            "Does `notes` state that this candidate is a confirmed, validated, or published "
            "planet, or that a paper presenting it has been accepted or published? Answer no if "
            "the text gives only a designation such as 'KOI-157' or 'Kepler-21' without also "
            "stating that the planet was confirmed, validated, accepted or published - 'Partial "
            "transit of Kepler-167e observed by Spitzer' names a planet but does not state that "
            "it was confirmed - and do not use "
            "your own knowledge of whether an object with that name is a planet. A request to "
            "publish, or a plan to write a paper, is not a statement that one was published."),
        "criteria": {
            "true": "The text states the candidate is confirmed, validated, accepted, or published",
            "false": "No such statement; a bare designation or a plan to publish does not count",
        },
    },
}

QUESTIONS = {**TIER_PREDICTIVE, **TIER_LABEL_ECHO}

# r6 questions NOT carried into the Kepler set, with the label-free reason.
NOT_CARRIED_FROM_R6 = {
    "host_star_described_as_evolved":      "subject matter on 2.2% of CFOP rows, below the 5% floor (24.6% on TESS)",
    "spectroscopy_consistent_with_planet": "replaced by spectroscopy_reports_no_binary_signature: CFOP states the recon "
                                           "pass as an absence of variation, which r6's wording answers NO to",
    "followup_reported_concluded":         "carried as recon_reported_concluded, widened to 'time for precise velocities'",
    "indicates_retired_or_rejected":       "carried as indicates_false_positive_or_retired, with the CFOP field form",
    "contains_object_designation":         "near-universal on CFOP -- notes name their KOI -- so it cannot discriminate",
}
