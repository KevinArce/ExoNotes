# 06 — Critical reassessment and research roadmap

> **Written 2026-09-23, after both registered studies** (TESS, positive; Kepler transfer,
> negative). **It changes no registered criterion or verdict, and it is not a
> pre-registration.** Its new numbers come from unregistered, exploratory checks run at **$0 of
> model spend**, read-only on the local databases, plus two public NASA Exoplanet Archive reads.
> Treat them as hypothesis generators. Every one that matters comes with a proposal for how to
> register it properly.

**The question this document asks is not only "is ExoNotes right?" but "how much more can be
done with it?"**

---

## Reading order

| file | what it answers |
| :--- | :--- |
| [`01_critical_assessment.md`](./01_critical_assessment.md) | Which claims the evidence carries, the assumptions (stated and hidden), 14 weaknesses each with a remedy, alternative interpretations, and what would falsify the result |
| [`02_exploratory_checks.md`](./02_exploratory_checks.md) | The ten exploratory measurements (E1–E10) behind the critique, with the code that produced them |
| [`03_literature_and_prior_art.md`](./03_literature_and_prior_art.md) | What already exists, and whether each idea is established, incremental, a genuine opportunity or speculative |
| [`04_research_questions.md`](./04_research_questions.md) | An honest map of disciplinary links, 50 research questions, and ten non-obvious ideas |
| [`05_project_proposals.md`](./05_project_proposals.md) | Thirteen full project proposals (question, data, method, design, success criteria, limitations, fit) |
| [`06_ecosystem_and_roadmap.md`](./06_ecosystem_and_roadmap.md) | How the projects feed each other, the phases and kill criteria, and **the ten-part roadmap** |

Evidence tags used throughout: **[R]** registered result in this repository · **[M]** measured
here, exploratory · **[L]** literature · **[A]** argument without measurement.

---

## The short version

**1. The headline is sturdier than the repository claims.** [M] The TESS gain survives:

- a stronger catalogue baseline that adds multiplicity, sectors, distance and insolation
  (+0.0432 → **+0.0354**);
- removing pre-TESS known planets (**+0.0342**);
- stripping a residual planet-name channel the TESS clause set misses (**+0.0383**).

By two loose proxies, most observer text predates the disposition.

**2. One public claim is not supported.** [M] The README says *"bag-of-words does not reach
it"*, based on a TF-IDF model that saw **text only**. With the catalogue columns underneath it,
bag-of-words reaches **80%** of the headline gain and **62%** of the leakage-stripped gain.
Structured judgments add a real but modest **+0.009 to +0.017** beyond it.

**3. "Content beyond volume" rests on three features.** [M]

- The imaging features add nothing beyond note count, length and authorship.
- The margin comes from the recon-spectroscopy and evolved-host features, which are almost
  uncorrelated with volume.
- On Kepler those features are rare, and the rest are strongly volume-correlated (ρ up to 0.73).
- Kepler's confirmations rarely run through RV follow-up (`rv_flag` 0.05 vs 0.76 on TESS).

Together these give a **testable mechanism for the Kepler failure**, fitted after the fact and
labelled that way.

**4. Question topics were chosen with outcome information.** [R] The r5/r6 topics were ranked by
crude-cue AUC on the full labelled corpus. A-41 acknowledges this, but `RESULTS.md` §10 does not
list it. The bias is probably small and has never been measured. The one study that chose topics
label-free (Kepler) failed. The clean fix is prospective.

**5. The largest gaps:**

- no external replication;
- a single proprietary featurizer that drifts;
- no gold labels for what the features say;
- no prospective test;
- no comparison with ExoFOP's *own* structured follow-up tables, which the archive-design
  claim needs.

**6. The text sometimes contradicts the catalogue.** [M] About 40% of hosts that a
spectroscopist described as evolved (148 of 357) have dwarf-like TIC log g. Part of the "text
signal" may be the text *correcting* the catalogue. That is an astrophysics result waiting to be
checked against Gaia DR3.

**7. Quantum: no forced connections.** The only defensible quantum projects are:

- a registered QML benchmark on this data, where a negative result is expected;
- carrying the "noisy black-box instrument" methodology over to device characterisation.

Both are labelled portfolio-grade.

---

## Recommended next steps (all are the owner's call)

> **Status, 2026-09-23.** Row 1 is **done**: the claim is corrected in the README, `RESULTS.md`
> §4.3, `CITATION.cff` and `.zenodo.json`; the limitation is in `RESULTS.md` §10; both are
> recorded in `PREREGISTRATION.md` §11.13, A-44. Row 3 is **registered**: the T₀ snapshot is
> frozen, `scripts/051`–`053` are in place, and the registration is `PREREGISTRATION.md` §11.14,
> A-45. The paid prediction run comes next, in the order A-45 §45.1 fixes.

| priority | action | cost |
| :--- | :--- | :--- |
| now | Reword the README and `RESULTS.md` §4.3 bag-of-words claim (W1). List the topic-selection limitation (W2). Label the two "4.4×" figures (W13) | $0 |
| now | Ask ExoFOP whether the **numeric feature matrices** can be published (W3). This makes every gate exactly reproducible by anyone, with no API key | $0 |
| month 1 | **Freeze and register P1**, the prospective prediction registry. TOIs that resolve before T₀ can never be prospective evidence | < $1 |
| months 1–3 | **P2**: a gold-labelled set of 300–500 notes, plus open-weights and NLI featurizers, to answer "is it the text or is it Jev?" | ~30–40 annotator-hours |
| months 1–3 | **P7**: notes vs catalogue stellar parameters, adjudicated with Gaia DR3 | $0 |
| months 3–9 | **P5**: the label-mechanism test with K2 as a third corpus. **This is where D+meta on Kepler finally gets registered** | ~$1 |

Everything else is in [`06_ecosystem_and_roadmap.md`](./06_ecosystem_and_roadmap.md).

---

## What this reassessment did not do

- It made **no** model API calls and **no** registered analysis. It changed no file under
  `data/`, `scripts/` or `src/`, and did not edit `PREREGISTRATION.md`, `RESULTS*.md` or the
  README.
- It did not run a D+meta arm on **Kepler**. The handoff says that needs a registration first,
  and P5 is that registration.
- It did not validate any literature claim beyond the abstract-level searches recorded in
  [`03`](./03_literature_and_prior_art.md). Check sources before citing them in a paper.
