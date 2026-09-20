"""Frozen question set for ExoNotes — the single source of truth.

`PREREGISTRATION.md` quotes this file. The Step 2.5 gate imports it, so the questions that
were tested and the questions that are pre-registered cannot drift apart.

QUESTION_SET_VERSION is part of the Jev cache key (PLAN.md §6 Step 3). Bump it on ANY edit
to QUESTIONS — an edit that does not bump it will silently serve stale cached answers.

-------------------------------------------------------------------------------------------
r5/r6 — rewritten for the `download_obsnotes` corpus. PREREGISTRATION.md §2 required this:
the r4 set was verified on the TOI `Comments` field and *does not transfer*.

r6 is r5 plus five scoped repairs and one deletion, all driven by r5's measured failures
(WORKLOG 2026-09-20T19:41Z): the imaging exclusion was cancelling its own positive on
standalone imaging notes; `NEB` was never expanded; "rules out an eclipsing binary" was
missing from the planet-side cues; and two multi-hop inferences ("ruled out → rejected",
"RV companion → a star was seen") are now named and forbidden per §2.4 rule 3.
`reports_on_target_detection` was restored per §2.3, tested, and deleted on the evidence.

Why the r4 questions could not simply be re-run (WORKLOG 2026-09-20T19:14Z, full-corpus
prevalence measured on all 1,482 rows):

    reports_offset_eclipsing_binary   4.0% of rows, |AUC| 0.537
    mentions_spectroscopic_binary     4.7%          |AUC| 0.540
    describes_transit_morphology      3.2%          |AUC| 0.513
    mentions_instrumental_artifact    1.6%          |AUC| 0.504   <- 23 rows of 1,482
    asserts_ephemeris_problem        12.4%          |AUC| 0.534

`Comments` was TFOP vetting shorthand ("TFOP FP; retired as NEB"). Observer notes are
reconnaissance-spectroscopy and speckle-imaging reports. The NEB/BEB vetting vocabulary the
r4 set was built around is almost absent; the content that IS here is different.

The r5 questions target the judgments this corpus actually contains, chosen by measured
prevalence and directional AUC, and written so that none of them can be answered from who
wrote the note, how many notes there are, or how long they are — the A-7 `B+meta` arm
reaches 0.6817 AUC on that metadata alone, so a question that merely detects "a speckle
imager reported here" adds nothing.
-------------------------------------------------------------------------------------------
"""

QUESTION_SET_VERSION = "2026-09-20.r6"

# Corpus cues these questions are written against, verified verbatim in the corpus text:
#   imaging clean      "No secondary sources were detected." / "No companions detected within 4.0\""
#   imaging detection  "Gaia DR2 says that there is a nearby companion at 1.4 arcsec separation"
#                      "Possible nearby companion = Yes (1.67\" companion (Keck/NIRC2 ...))"
#   RV -> planet       "It does rule out a brown dwarf." / "implies a hot Jupiter companion"
#   RV -> non-planet   "This system is an eclipsing binary." / "A planetary companion is ruled out"
#   host evolved       "reveals a late F evolved star" / "an early G subgiant"
#   host dwarf         "reveals a G dwarf" / "an early K dwarf with almost no rotation"
#   closure            "No more TRES recon spectra are needed."
#
# HEADER BLOCKS ARE A TRAP. Most rows open with a machine-written block such as
#   "T0418987806, 00:26:04.69 63:19:09.80, V=9.8, PM=13.0, J-K=0.22, Period=0.9 TOI-1584,Rp=24.9
#    2019-12-30 TRES, pha=63.85, RV=-19.683, Teff=6250+/-125, log(g)=2.00+/-0.25, ..."
# `RV=` there is an ABSOLUTE radial velocity, not a variation, and `log(g)` is a number the
# model must not compare (PLAN.md §1: Jev never judges whether two values are near each
# other). Every question below names that trap explicitly, per §2.4 rule 3.

TIER_PREDICTIVE = {
    "imaging_reports_no_companion": {
        "type": "noul",
        # Highest-prevalence content signal in the corpus: 28.5% of rows, |AUC| 0.643.
        # ExoFOP's raw HTML glues this sentence to the preceding token on 129 rows, as
        # "...acquired at 832nmNo secondary sources were detected." The negation is still
        # there and still governs; the criteria say so, because jev-1.13 reads literally.
        "instructions": (
            "Does `notes` state that imaging of this target found no companion, no secondary "
            "source, and no nearby star? The sentences 'No secondary sources were detected' and "
            "'No companions detected within 4.0\"' say exactly this and count on their own. "
            "Answer yes even when the sentence is run together with the words before it, as in "
            "'acquired at 832nmNo secondary sources were detected' - that is the same statement "
            "with a missing space, and it is still a statement that nothing was found. "
            "Most imaging notes also say that the imaging was taken, name the wavelengths, and "
            "offer plots or tables of the limiting magnitude. Those sentences are not findings, "
            "but they do not count against one either: if a statement that nothing was found "
            "appears anywhere in the text, answer yes, however much surrounding material only "
            "describes the observation. Answer no only when no such statement appears at all - "
            "when the text says imaging was taken or requested and never reports the result, or "
            "when a nearby star, companion, or secondary source is reported as present."),
        "criteria": {
            "true": {
                "what": "Imaging is reported to have found nothing: no secondary source, no companion, no nearby star",
                "examples": ["No secondary sources were detected.",
                             "No companions detected within 4.0\"",
                             "acquired at 832nmNo secondary sources were detected.",
                             "No companion detected within 4 arcsec"]},
            "false": {
                "what": "No imaging result is reported, or imaging found something",
                "examples": ["WIYN speckle imaging using NESSI was taken of TIC22233480 on 2022-04-21.",
                             "there is a nearby companion at 1.4 arcsec separation",
                             "Possible nearby companion = Yes (1.67\" companion)"]},
        },
    },
    "imaging_reports_companion_present": {
        "type": "noul",
        # Asked as its own proposition rather than as the negation of the question above.
        # jev-1.13's jaggedness page is explicit that P(noul) and 1 - P(not noul) are not
        # interchangeable, so the opposite direction is asked, not inferred.
        "instructions": (
            "Does `notes` state that a companion star, a nearby star, or a secondary source was "
            "actually found near this target? A stated angular separation such as 'a nearby "
            "companion at 1.4 arcsec separation', a report of 'Possible nearby companion = Yes', "
            "a star seen on a guider, or a named nearby star given as the source of the eclipse "
            "all count. Answer no if the text reports that nothing was found, including when the "
            "sentence is run together with the words before it as in '832nmNo secondary sources "
            "were detected'. Answer no if the text only says that imaging was taken. A request to "
            "look for a companion is not a finding that one is there. This question is about a "
            "star that was SEEN next to the target. A companion inferred from radial velocities "
            "or from a spectrum - an SB1, a double-lined spectrum, or 'a mid dwarf companion' "
            "deduced from velocities - is not a star seen near the target, and does not count "
            "unless imaging or a catalogue also reports one there."),
        "criteria": {
            "true": {
                "what": "A companion, nearby star, or secondary source is reported as actually present",
                "examples": ["Gaia DR2 says that there is a nearby companion at 1.4 arcsec separation and 5 magnitudes fainter",
                             "Possible nearby companion = Yes (1.67\" companion (Keck/NIRC2))",
                             "we saw, on the HIRES guider, a star about 3 mag fainter located 1.3 \" away",
                             "star at 31\" is an EB"]},
            "false": {
                "what": "Nothing was found, or no imaging result is reported at all",
                "examples": ["No secondary sources were detected.",
                             "acquired at 832nmNo secondary sources were detected.",
                             "let's check for a stellar companion in an eclipsing binary"]},
        },
    },
    "spectroscopy_indicates_nonplanetary_companion": {
        "type": "noul",
        # 11.7% of rows, |AUC| 0.586, and the direction is what carries it: the crude
        # "RV variation" token alone is 0.540 because it pools both conclusions together.
        "instructions": (
            "Does `notes` conclude that the companion causing the events is too massive to be a "
            "planet - that it is a star, a brown dwarf, or an eclipsing or spectroscopic binary? "
            "The binary may be the target itself or a nearby star whose eclipses are the source "
            "of the events; both count. The abbreviations NEB (nearby eclipsing binary) and BEB "
            "(background eclipsing binary) mean exactly this and count on their own, with no "
            "separation, direction, or star name needed - 'SG1 indicates there is an NEB' is "
            "enough. Statements such as 'This system is an eclipsing binary', "
            "'the transit-like events are secondary eclipses in an eclipsing binary', 'the "
            "eclipse is on a nearby star', 'a planetary companion is ruled out', 'double-lined', "
            "SB1, SB2, SEB1 and SEB2 all count. Answer no when the "
            "conclusion runs the other way - when a brown dwarf or stellar companion is ruled "
            "out, or the companion is called a planet or a hot Jupiter. Do not use the `RV=` "
            "value in the machine-written header line: that is the star's absolute radial "
            "velocity, not a variation, and it says nothing about the companion. Do not treat a "
            "velocity that is 'out of phase with the photometric ephemeris' as a binary on its "
            "own - out of phase means the variation does not track the transit, which is a "
            "reason to doubt the companion, not a statement that it is stellar. A binary that is "
            "raised as a possibility and then rejected does not count: 'the cores do not swap "
            "sides, as would be expected if this is a double-lined binary' and 'rules out the "
            "unlikely possibility that this was an eccentric eclipsing binary' are both "
            "conclusions that it is NOT a binary."),
        "criteria": {
            "true": {
                "what": "The text concludes the companion is stellar, a brown dwarf, or that the system is a binary",
                "examples": ["This system is an eclipsing binary.",
                             "a mid dwarf companion ... the transit-like events are secondary eclipses",
                             "A planetary companion is ruled out",
                             "this is a double-lined binary"]},
            "false": {
                "what": "No such conclusion, or the opposite one",
                "examples": ["It does rule out a brown dwarf.",
                             "implies a hot Jupiter companion",
                             "This pretty much rules out a stellar or brown dwarf companion",
                             "The two TRES observations yield a velocity offset of 20 m/s."]},
        },
    },
    "spectroscopy_consistent_with_planet": {
        "type": "noul",
        "instructions": (
            "Does `notes` conclude that the spectroscopic or radial-velocity evidence is "
            "consistent with a planet-mass companion, or that it rules out a stellar or "
            "brown-dwarf companion? Statements such as 'implies a hot Jupiter companion', "
            "'consistent with a companion of about one Jupiter mass', 'it does rule out a brown "
            "dwarf', and 'this pretty much rules out a stellar or brown dwarf companion' all "
            "count. Ruling out a stellar companion counts however it is phrased, including "
            "'rules out the unlikely possibility that this was an eccentric eclipsing binary' - "
            "an eclipsing binary is a stellar companion, so excluding one is evidence for a "
            "planet. A published mass measurement from radial velocities that establishes a "
            "planetary mass also counts. Answer no if the text concludes the companion is "
            "stellar or a brown dwarf, or "
            "that the system is a binary. Answer no if the text reports only that the velocity "
            "shift was small, insignificant, or within the errors and draws no conclusion about "
            "what the companion is. Do not use the `RV=` value in the machine-written header "
            "line: that is the star's absolute radial velocity, not a variation."),
        "criteria": {
            "true": {
                "what": "The spectroscopic conclusion supports a planet-mass companion, or excludes a stellar or brown-dwarf one",
                "examples": ["implies a hot Jupiter companion",
                             "consistent with a companion of about one Jupiter mass",
                             "It does rule out a brown dwarf.",
                             "This pretty much rules out a stellar or brown dwarf companion in this system."]},
            "false": {
                "what": "No such conclusion, a bare small-shift report, or the opposite conclusion",
                "examples": ["The two TRES observations yield a velocity offset of 20 m/s.",
                             "a small velocity shift that is probably not significant",
                             "This system is an eclipsing binary."]},
        },
    },
    "host_star_described_as_evolved": {
        "type": "noul",
        # 24.6% of rows, |AUC| 0.590, and astrophysically load-bearing: an evolved host makes
        # the inferred companion radius larger, which is how a candidate becomes a false
        # positive. Deliberately keyed to the WORDS, never to log(g) -- PLAN.md §1 forbids
        # Jev judging numeric values, and log(g) sits in every header block.
        "instructions": (
            "Does `notes` describe this target star as evolved rather than as an ordinary "
            "main-sequence dwarf? The words 'evolved', 'somewhat evolved', 'slightly evolved', "
            "'subgiant' and 'giant' count, including when hedged with 'perhaps' or 'probably'. "
            "Answer no when the star is called a dwarf, for example 'a late F dwarf', 'an early K "
            "dwarf', 'a G dwarf', or 'a Sun-like spectrum', and no such evolved description "
            "appears. Judge this only from the words used to describe the star. Ignore the "
            "`log(g)`, `Teff`, `R=` and `V=` numbers in the machine-written header line - do not "
            "work out from any number whether the star is evolved."),
        "criteria": {
            "true": {
                "what": "The star is described in words as evolved, a subgiant, or a giant",
                "examples": ["The first TRES observation reveals a late F evolved star.",
                             "reveals an early G subgiant",
                             "an early F star that is somewhat evolved",
                             "it shows this star is not an M dwarf, but a giant"]},
            "false": {
                "what": "The star is described as a dwarf or Sun-like, or its type is not described at all",
                "examples": ["The first TRES observation reveals a G dwarf.",
                             "reveals an early K dwarf with almost no rotation",
                             "reveals a good-looking Sun-like spectrum"]},
        },
    },
    "followup_reported_concluded": {
        "type": "noul",
        # 55.3% of rows, |AUC| 0.613 -- but this sentence lives inside the TRES boilerplate,
        # so it is the candidate most at risk of being absorbed by B+meta's author one-hot.
        # Kept for the gate so the risk is measured rather than assumed. See WORKLOG 19:14Z.
        "instructions": (
            "Does `notes` state that no further observations of this target are needed? "
            "Sentences such as 'No more TRES recon spectra are needed', 'No more recon spectra "
            "are needed' and 'No more TRES observations are needed' count. Answer no if the text "
            "instead asks for further observations, for example \"Let's get a second TRES recon "
            "spectrum near phase 0.75\", 'we need to make sure', or 'this deserves more "
            "attention'. If the text both asks for more observations earlier and states that no "
            "more are needed later, answer yes, because the question is whether that statement "
            "appears at all."),
        "criteria": {
            "true": "The text states that no further observations are needed",
            "false": "The text asks for further observations, or says nothing about whether more are needed",
        },
    },
    "author_certainty": {
        "type": "score",
        "instructions": (
            "How certain is the author of `notes` about the conclusion they state about this "
            "candidate? Judge the human commentary, not the machine-written header lines of "
            "measurements."),
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
    "indicates_retired_or_rejected": {
        "type": "noul",
        "instructions": (
            "Does `notes` state that this candidate has been retired, rejected, or classified as "
            "a false positive or false alarm - for example 'Retired as NEB', 'TFOP FP', 'FA'? "
            "Answer no if the text only says what the signal is, or only describes a problem with "
            "it, without stating that it was retired, rejected, or classified FP or FA. "
            "Identifying the signal as an eclipsing binary, a binary, or a variable is not by "
            "itself a retirement. Ruling something out is not a retirement either: 'a planetary "
            "companion is ruled out' and 'this rules out a brown dwarf' say what the companion "
            "is or is not, not that the candidate was retired or classified FP. Stopping "
            "observations is not a retirement: 'no more recon spectra are needed' says the "
            "follow-up is finished, not that the candidate was rejected. Answer no unless the "
            "text actually states a retirement, a rejection, or an FP or FA classification."),
        "criteria": {
            "true": "A retirement, rejection, or false-positive/false-alarm classification is stated",
            "false": "Only a description of the signal or a doubt about it; no retirement, rejection, FP or FA stated",
        },
    },
    "indicates_confirmed_planet": {
        "type": "noul",
        "instructions": (
            "Does `notes` state that this candidate is a confirmed, validated, or published "
            "planet? A statement that a paper presenting it has been published counts. Answer no "
            "if the text gives only a catalogue designation, including one from another "
            "catalogue such as 'SG1 reports that this is K2-133', without also stating that it "
            "was confirmed, validated, or published - do not use your own knowledge of whether "
            "an object with that name turned out to be a planet. Answer no if the text states "
            "the candidate is a false positive, a false alarm, or was retired. A request to "
            "publish, or a question about whether the data are good enough to publish, is not a "
            "statement that it was published."),
        "criteria": {
            "true": "The text states the candidate is confirmed, validated, or published",
            "false": "No such statement; a bare designation, or a question about publishing, does not count",
        },
    },
    "contains_object_designation": {
        "type": "noul",
        "instructions": (
            "Does `notes` contain a catalogue designation for a planet or a star - for example "
            "'WASP-29', 'K2-133', 'Kepler-410Ab', 'KOI-889b', 'TOI-1584', or a bare TIC number? "
            "Answer no if the text names only instruments, surveys, working groups, people, or "
            "publications - for example 'TRES', 'NESSI', 'WIYN', 'SG1', 'TFOP', 'HARPS-N', "
            "'Hord et al 2024'."),
        "criteria": {
            "true": "A planet or star catalogue designation appears",
            "false": "Only instruments, surveys, groups, people, or papers are named",
        },
    },
}

QUESTIONS = {**TIER_PREDICTIVE, **TIER_LABEL_ECHO}

# Questions carried in r4 and NOT carried into r5, with the measured reason. Recorded here
# because PREREGISTRATION.md §2.1 lists them and a reader of that section needs to find the
# reason next to the artifact. Registered in §11.3.
RETIRED_ON_OBSNOTES = {
    "reports_offset_eclipsing_binary":   "NEB/BEB subject matter on 4.0% of rows, |AUC| 0.537",
    "reports_stellar_companion_or_blend": "superseded by the two directional imaging questions",
    "mentions_spectroscopic_binary":     "4.7% of rows, |AUC| 0.540; folded into spectroscopy_indicates_nonplanetary_companion",
    "asserts_ephemeris_problem":         "12.4% of rows, |AUC| 0.534, and confusable with 'out of phase with the ephemeris'",
    "mentions_instrumental_artifact":    "23 rows of 1,482 (1.6%), |AUC| 0.504",
    "describes_transit_morphology":      "3.2% of rows, |AUC| 0.513",
    "evidence_depth":                    "A-7 proxy concern, now measured: metadata alone reaches 0.6817 AUC",
    "indicates_followup_complete":       "restored under the name followup_reported_concluded",
    "reports_on_target_detection":       "restored per §2.3 and TESTED in r5: 1.4% of rows, and across "
                                         "all 27 gate cases it never returned a clear positive (range "
                                         "0.03-0.64, four cases mid-band). Deleted under §2.4 rule 6.",
}
