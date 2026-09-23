# 01 — Critical assessment: what is established, what is assumed, what is missing

> Written 2026-09-23, after both registered studies (TESS v1.0.0 and v1.1.0; Kepler v1.1.0).
> **It revises no registered criterion or verdict.** Numbers tagged **[R]** are registered
> results from this repository. **[M]** marks this reassessment's unregistered exploratory
> measurements, detailed in [`02_exploratory_checks.md`](./02_exploratory_checks.md). **[L]**
> marks literature, in [`03`](./03_literature_and_prior_art.md). **[A]** marks argument without
> measurement.

---

## 0. What deserves to be kept exactly as it is

The critique below is only possible because the project made it possible. These practices are
rare in astronomy software, and they are the reason the weaknesses can be found at all:

- **Pre-registration with an append-only amendment log** that labels which amendments came
  after results. The falsified prior (A-23) and the negative Kepler reading were published,
  not buried.
- **A zero point for ΔAUC** (the B+N dilution floor, A-1), a **registered MDE** instead of
  post-hoc power (A-2), and a **volume control** (B+meta, A-7). Most published "text adds
  signal" claims in any field have none of the three.
- **Leakage treated as the primary threat.** The `Comments` echo (47.9%) and the `pscomppars`
  membership leak (P = 0.995 vs 0.074) are **the most portable findings in the repository**
  [R].
- **A verifier that is proven able to fail** (17 mutations), and **CI that demands a paid run**.
- **Corrections that moved the headline down** (A-38, A-43), recorded where they apply.

Nothing below argues against these. Several proposals exist to make them reusable (P8 in
[`05`](./05_project_proposals.md)).

---

## 1. The claim ladder: which conclusions the evidence carries

| # | Claim, as the repository states or implies it | Evidence | Verdict |
| :-- | :--- | :--- | :--- |
| **C1** | ExoFOP-TESS observer notes carry disposition signal beyond the 8 numeric TOI columns | G2 +0.0432 [+0.0324, +0.0547], all six gates pass, two cold re-runs (+0.0451, +0.0460) [R]. It survives a stronger catalogue baseline (+0.0354, E3), removing KP (+0.0342, E4) and a residual name channel (+0.0383, E5) [M] | **Strongly supported** for this corpus, snapshot and featurizer |
| **C2** | …beyond *how much* follow-up happened | D − B+meta +0.0220 [+0.0126, +0.0321] [R]. D+meta − B+meta +0.0277 [+0.0186, +0.0369] [M, unregistered]. **But the whole margin is carried by 3 of 7 features.** The imaging features add +0.0009 [−0.0077, +0.0089] beyond meta (E6) | **Supported, narrowly, through one mechanism**: recon-spectroscopy conclusions |
| **C3** | *"Whatever the signal is, bag-of-words does not reach it"* (README) | Baseline C is **text-only**. Stacked TF-IDF on top of B reaches **+0.0345 (80%)** of the gain, and **+0.0244 (62%)** on the leakage-stripped arm. Jev's increment over it is +0.0088 [+0.0004, +0.0174] full / +0.0147 [+0.0042, +0.0246] G5 (E2) [M] | **Not supported as stated.** Supported as *"structured judgments add a modest increment beyond bag-of-words"* |
| **C4** | The model *"reads the follow-up evidence trail and anticipates expert consensus"* | By two loose proxies, most observer text predates the label: ≥ 4.6% of notes post-date an upper-bound disposition time, and 8.1% of CP notes post-date the discovery year (E8) [M]. S2 +0.1296 [R]. **No prospective test** | **Partially supported.** "Reads the trail" holds; "anticipates" has not been tested prospectively |
| **C5** | The information *"never reaches the structured catalogue"* (`research/03` §4.1; README: the numeric columns *"contain none of that"*) | Only the `toi` table was tested. ExoFOP's structured imaging, spectroscopy, time-series and stellar-companion tables (`etta.download_imaging`, `download_spect`, `download_tseries`, `download_stellarcomp`; `PLAN.md` §2.1) were never tried as baselines | **Open.** It is true of the TOI table and untested for ExoFOP as a whole |
| **C6** | The TESS result should be read as specific to ExoFOP-TESS | Kepler: D − B+meta −0.0023 [−0.0041, −0.0004]; KG3 fails [R] | **Supported.** E7 and E9 suggest a mechanism [M] |
| **C7** | Reproducible | Exact from the cache, approximate from a cold start, verified in CI. **No external replication.** The model is proprietary and not bit-stable | **Supported internally; the largest open gap is external** |
| **C8** | `Comments` restates the label; `pscomppars` leaks through membership | Measured directly [R] | **Strongly supported, and the most portable result** |

**The one-line summary:** the headline (C1) is sturdier than the repository claims. The
*interpretation* (C3, C4, C5) is looser than the repository claims.

---

## 2. Assumptions, stated and implicit

| # | Assumption | Status | How to test or replace it |
| :-- | :--- | :--- | :--- |
| A1 | TFOPWG disposition is a meaningful target | Holds, but it is a **human consensus that the notes help produce**. 39% of positives are pre-TESS KP (E1) | Report CP-only (E4: +0.0342). Consider *time-to-disposition* as a second target (P6) |
| A2 | Eight TOI columns represent "the numeric catalogue" | **Weak.** Multiplicity alone sits at P(y=1) 0.926 vs 0.481; a stronger B takes 18% of the gain (E3) | Register a strong B: multiplicity, sectors, distance, Gaia DR3 RUWE, and the ExoFOP structured tables (W5) |
| A3 | `Groupname IS NULL` separates observation from disposition | **Partly.** TFOPWG-account notes also carry SG1 photometry and Keck/HIRES spectroscopy text (seen in `obsnotes_raw`). The corpus drops the most decisive NEB evidence wholesale | Scope statement now. A registered "TFOPWG notes with disposition lines stripped" arm later (W12) |
| A4 | The clause sets strip label echo | Holds in effect. There is a 17-row survey-name residual at P = 0.941 that the TESS set does not catch (E5) | Add a `K10`-style clause to the TESS set by the same rule |
| A5 | Jev answers from the text, not from world knowledge (for example, that `WASP-72` is a planet) | **Untested.** `contains_object_designation` averages 0.929, so designations are almost everywhere | Mask every designation with a placeholder and re-score (~$0.24). Compare features and ΔAUC (W3) |
| A6 | The features mean what their names say | Tested on 27 gate cases (219/221) only. **There is no per-question accuracy on a representative sample** (`RESULTS.md` §9 item 2) | A gold-labelled sample of 300–500 notes (P2) |
| A7 | Paraphrase stability (G3) supports validity | G3 measures **reliability, not validity**. A stable feature can be stably wrong | Gold labels (P2), and agreement across featurizers (P2) |
| A8 | The paired group bootstrap captures the uncertainty | It resamples *test groups* and holds the fits fixed. CV-based intervals are known to under-cover (Bates, Hastie & Tibshirani 2023) [L]. The seed spread in G4 already shows missing variance | Nested CV or cross-fitted inference (Williamson et al. 2021 `vimp`) for any comparison near zero (W8) |
| A9 | `Lastmod` approximates when a note was written | Acknowledged (`RESULTS.md` §10.1). Edits are invisible | Only a prospective design removes it (P1) |
| A10 | The ~33% of TICs without notes do not bias the comparison | Measured and bounded: ratio 1.149, and B is *harder* on included rows [R] | — |
| A11 | **Question topics were chosen without outcome information** | **Violated for TESS.** r5/r6 topics were *"chosen by measured prevalence and directional AUC"* on all 1,482 labelled rows (`questions.py`; A-19, A-23). A-41 acknowledges this. `RESULTS.md` §10 does not list it | Prospective or lockbox holdout (P1). Meanwhile, list it as a limitation (W2) |
| A12 | The unit is a TOI | The features are **host-level**, so all TOIs on a star share them. Mixed-label hosts get identical text features | Report the mixed-label host count. Consider per-TOI extraction where notes name the TOI |
| A13 | The featurizer is a stable instrument | **Not bit-stable** (~0.005 per feature) and **vendor-controlled**. `jev-1.13.0` can be retired | Publish the numeric feature matrix. Replicate with open-weights models (W3, P2) |
| A14 | AUC is the right figure of merit | B already sits at 0.90. ΔAUC near the ceiling says little about *utility* (telescope nights saved, planets not lost) | Decision curves and precision at fixed planet recall (W10) |

---

## 3. Weaknesses, each with a concrete remedy

Ordered by how much each one could change what the repository claims.

### W1 — The bag-of-words comparison was single-modality · affects C3 · **high**

**What.** C (TF-IDF + logistic, text only) is compared against B (numeric only), and the
README reads the gap as *"bag-of-words does not reach it."* The right comparison is
B+bag-of-words against D.
**Evidence.** E2: B+TFIDF reaches 80% of the full-arm gain and 62% of the leakage-stripped gain.
**Why it matters.** It is the README's *"what is genuinely non-obvious"* sentence, and it is
already quoted in search-engine summaries of the Zenodo record.
**Remedy.** (1) Reword the README and `RESULTS.md` §4.3 now. The C-below-B fact stays true as a
*leakage* check (the label is not readable from the raw text alone). It is not a
*semantic-advantage* claim. (2) In any future registration, add **B+TFIDF (stacked)** and
**B+embedding** (for example a sentence-transformer or astroBERT embedding, reduced in-fold) as
reference arms. Make **D − B+TFIDF** the registered test of "structure beats words". $0.

### W2 — Question topics were selected with outcome information · affects C1–C3 · **high**

**What.** The topics were ranked by crude-cue |AUC| on the full labelled corpus before any split
(A-19, A-23). That is feature selection outside the CV loop, a textbook leakage type (Kapoor &
Narayanan 2023, "feature selection on training and test set") [L]. The *gate cases* were
label-blinded (A-22); the *topics* were not.
**How large.** Probably small. The crude cues were weak (0.51–0.64), and the pool they were
chosen from was modest (A-19 lists what was retired). But nobody has measured it. It is the same order as
Jev's increment over bag-of-words (W1), and **the one study that chose topics label-free, Kepler,
failed its content test**. That is confounded with the corpus (E7, E9), but it is not reassuring.
**Remedy.** (1) Add it to `RESULTS.md` §10 as a limitation. (2) The clean fix is **a prospective
holdout** (P1): TOIs dispositioned after the 2026-09-19 snapshot, scored with the frozen r6
questions, are out-of-sample for topic selection *and* for time. (3) A cheaper partial bound: run
the A-19/A-23 selection procedure on crude cues *inside each training fold*, and measure how
often it picks the same topics and how much the cue AUCs shrink out-of-fold.

### W3 — One proprietary, drifting featurizer · affects C7 and generality · **high**

**What.** Every content feature comes from `jev-1.13.0`. It cannot be pinned below its version
string, varies by ~0.005 per feature between identical calls [R], and could be retired. The
raw cache (1,382 responses) is not published, so exact reproduction depends on this one machine.
**Remedy.**
(1) **Publish the numeric feature matrices** (`jev_features_obsnotes` and `kepler_jev_features`:
TOI or KOI id plus floats, no note text) as a Zenodo dataset. Every gate can then be recomputed
exactly by anyone, with no API key. Confirm with ExoFOP that derived numbers are fine to publish
(W11).
(2) **Featurizer-agnostic replication** (P2): the same seven questions answered by an
open-weights instruction model, by an NLI zero-shot classifier and by embeddings plus a linear
probe. If the ΔAUC survives across featurizers, the finding is about the *text*. If it does not,
it is about *Jev*.
(3) **World-knowledge probe** (A5): re-score with every designation masked.

### W4 — No ground truth for what the features say · affects A6, A7 · **high**

**What.** 27 gate cases are the only human-checked answers. `PLAN.md` §9 asked for per-question
reliability diagrams, and `RESULTS.md` §9.2 correctly says they could not be made without labels.
**Remedy.** Annotate a stratified sample of **300–500 observer notes** on the seven predictive
questions. Use two annotators with domain knowledge, report Cohen's κ, and stay blind to
disposition. That set enables per-question accuracy and calibration, and PPI or DSL
bias-corrected estimates (Angelopoulos et al. 2023; Egami et al. 2023) [L]. It makes the
featurizer comparison in W3 possible, and it becomes a **public benchmark** (P2). About 30–40
annotator-hours.

### W5 — The baseline is the TOI table, not the archive · affects C5 · **medium–high**

**What.** The archive-design implication, that prose carries what the schema drops, requires a
baseline that includes ExoFOP's **own structured follow-up tables**. The strongest content
features (the spectroscopic verdict and evolved host) may partly exist there already: stellar
parameters from spectra, companion detections, and whether imaging was done.
**Remedy.** A registered **B+ExoFOP-structured** arm: counts and flags from `download_imaging`,
`download_spect`, `download_stellarcomp` and `download_tseries`, restricted to observations dated
before the TESS alert cutoff where needed. If D still beats it, C5 becomes a real finding
worth sending to ExoFOP. If it does not, the finding becomes *"the structured follow-up tables
are underused"*. That is also useful, and cheaper to act on. $0, using `etta` endpoints
already wrapped.

### W6 — "Content beyond volume" rests on three features · affects C2 · **medium**

**What.** E6: the imaging family adds nothing beyond B+meta. The spectroscopy and evolved-host
family carries the margin (+0.0130). Closure and certainty do *worse* than meta. The registered
comparison, D vs B+meta, compares two different feature sets. The logical test of "content adds
beyond volume" is D+meta vs B+meta (E6: +0.0277, unregistered).
**Remedy.** Report the family decomposition in any write-up. Future registrations should use
**D+meta vs B+meta** as the content test, alongside D vs B+meta. Add a **volume-matched** analysis:
stratify or match on note count, characters and authors, then test D − B within strata.

### W7 — The temporal split is conditioned on resolution · affects C4 · **medium**

**What.** S2's test set is TOIs alerted after 2021-10-28 *and dispositioned by September 2026*.
TOIs that resolve quickly tend to have decisive notes, such as an SB2 in the first recon spectrum.
This survivorship inflates text gains on recent TOIs, and it may help explain why S2's gain
(+0.1296) is three times S1's. It does not invalidate G4. It limits what G4 can mean.
**Remedy.** The prospective design (P1) tests exactly this. In the meantime, a survival framing
(P6) treats unresolved TOIs as censored instead of dropping them.

### W8 — The inference does not cover fitting variance · affects marginal comparisons · **medium**

**What.** The bootstrap resamples test groups with the fitted predictions held fixed. The G4
seed study shows fit variance of ±0.005 on a single split [R]. For G2, with a lower bound of
+0.032, this cannot matter. For comparisons whose lower bound sits near zero (E2's +0.0004, or
Kepler's −0.0004 upper bound), it can.
**Remedy.** For any future comparison expected to be marginal, register nested CV (Bates,
Hastie & Tibshirani 2023) or cross-fitted variable-importance inference (Williamson et al. 2021,
AUC measure) [L]. Both are ready-made, and `vimpy` exists for Python.

### W9 — KP positives are included · affects the interpretation of C1 · **low (tested)**

E4 shows the gain survives without KP (+0.0342). **Remedy:** report it beside the headline.
KP rows are the easiest positives and the least interesting ones.

### W10 — Utility is unmeasured · affects the science case · **medium**

**What.** Going from AUC 0.90 to 0.95 sounds large. The operational question for TFOP is
different: *how many follow-up hours or FP-resolution steps could a ranking save, at what cost
in lost planets?*
**Remedy.** Decision-curve analysis, and **precision at 95% or 99% planet recall** for B and D.
Add a cost model with a rough price per follow-up type (recon spectrum, speckle image, SG1 light
curve). $0 on existing predictions. Also compare against what TFOP actually does. The notes
exist only because TFOP already ran the follow-up, so the deployable use is on **open**
candidates (P1), not closed ones.

### W11 — No external replication · affects C7 · **high, and acknowledged**

**Remedy.** (1) Publish a **replication kit**: the frozen snapshot checksums (done), the numeric
feature matrices (W3), a one-command gate recomputation, and a plain statement of what an
independent replicator should vary (featurizer, baseline, corpus date). (2) Ask one or two
exoplanet groups, or an ML-reproducibility venue (for example the ML Reproducibility Challenge),
to attempt it. (3) Write the RNAAS note (`HANDOFF_PROMPT.md` item 3) so the work is findable by
people who can replicate it.

### W12 — The corpus excludes TFOPWG-account notes wholesale · affects scope · **medium**

**What.** `Groupname IS NULL` removes every TFOPWG-account note, and those carry `Master Disp:`.
They also carry the **SG1 ground-based photometry summaries** (*"confirmed a 3 ppt transit on
target in a 6'' aperture"*) and some spectroscopy. On-target versus off-target detection is the
single most decisive NEB discriminant, and it is outside the corpus.
**Remedy.** A separately registered arm on TFOPWG notes with **every disposition line and token
stripped**, using the strictest clause set (L1–L9, SG1 statuses such as `VPC`, `CPC` and
`cleared`). Expect heavy residual leakage, which is why it needs its own registration. Its value
is to measure how much of the follow-up record's information sits in the channel the study
excluded.

### W13 — Two small presentation issues

- The README states *"its calibration degrades ~4.4× out of distribution"* as fact. That figure
  is a **third-party measurement on a synthetic task** (`research/03` §1.4 labels it so). The
  README should label it the same way.
- **"4.4×" appears twice with unrelated meanings**: the third-party calibration ratio, and G3's
  paraphrase-to-repeat noise ratio. Readers will conflate them. Spell out both where they appear.

### W14 — The question set mixes observations with decisions

`followup_reported_concluded` (*"No more TRES recon spectra are needed"*) and `author_certainty`
record **the observers' own decisions**, not observations. That puts them close to label echo,
because the recon team stops once it has concluded. E6 shows this family does *worse* than meta.
**Remedy.** In future sets, split the predictive tier into **observation** questions (imaging
results, spectroscopic verdicts, stellar class) and **process** questions (closure, certainty).
Register the headline on observation questions only.

---

## 4. Alternative interpretations of the TESS result

| # | Interpretation | Evidence for | Evidence against | Test |
| :-- | :--- | :--- | :--- | :--- |
| I1 | **Evidence-trail reading** (the intended one): the prose records follow-up results that the catalogue lacks | G2, G5, B+meta [R]; spectroscopy features carry it and are volume-independent (E6, E7) [M] | — | Gold labels (P2), prospective test (P1) |
| I2 | **Process proxy**: the signal is *who* followed up and *when they stopped* | Imaging and closure features are absorbed by meta (E6) | The spectroscopy family beats meta | Volume-matched and author-stratified D − B (W6) |
| I3 | **Residual label echo** | 17-row name channel (E5) | Stripping it changes nothing (+0.0383) | Add a K10-style clause (A4) |
| I4 | **Selection on outcome in question design** | Topics chosen by full-corpus \|AUC\| (W2) | Crude cues were weak; the gates were blinded | Prospective holdout (P1) |
| I5 | **Survivorship**: resolved TOIs have decisive notes | Plausible; S2's gain is 3× S1's [R] | Affects B too | P1, P6 |
| I6 | **World knowledge**: Jev recognises named planets | Designations appear in most rows | Label-echo questions forbid it, and G5 strips most names | Designation masking (A5) |
| I7 | **Catalogue-error correction**: the text supplies a better stellar classification than the TIC | 148 of 357 "evolved" hosts have dwarf-like TIC log g (E10) [M] | — | Add Gaia DR3 or spectroscopic log g to B. If D's gain shrinks, I7 is a real mechanism (P7) |

**I7 deserves attention.** If it holds, part of the "text signal" is really *the catalogue's
stellar parameters being wrong*, and the text is correcting them. That is a finding about the
TIC as much as about notes, and it is testable with public data.

---

## 5. What would reproduce, validate or falsify the findings

| level | question | concrete step | falsified if |
| :--- | :--- | :--- | :--- |
| **Reproduce exactly** | Same numbers from the same inputs? | Publish the feature matrices (W3) and recompute the gates | Any gate number differs beyond row-order effects (0.0008) |
| **Reproduce approximately** | Same verdicts from a cold start? | Already done twice in CI [R] | A gate verdict flips |
| **Replicate independently** | Does another team, with another featurizer, get the gain? | P2 plus the replication kit (W11) | Open-weights and NLI featurizers give D − B+TFIDF ≤ 0 on the G5 arm |
| **Validate prospectively** | Does it predict dispositions not yet made? | P1: frozen predictions for open TOIs, checked as TFOPWG resolves them | Prospective D − B ≤ MDE, or D − B+meta ≤ 0 |
| **Generalise** | Other follow-up corpora? | K2, CTOIs (Planet Hunters), and non-exoplanet corpora (P9) | A pattern of "volume only" readings where the label is not produced by the follow-up |
| **Explain** | Why TESS but not Kepler? | P5, the label-mechanism test | The content gain on TESS does not depend on the confirmation route |

---

## 6. Hidden biases and constraints

- **Selection into the corpus is outcome-related.** P(note | y=1) / P(note | y=0) = 1.149 [R].
  Notes exist only where someone decided to follow up.
- **Survivorship in the label.** Only resolved TOIs are labelled, and resolution speed is
  plausibly related to how decisive the text is (W7).
- **Concentration of authorship.** A handful of observers and teams (the TRES recon team, the
  speckle imagers) write most of the informative text. The finding may be *"these two teams'
  conclusions are predictive"*. That is valuable, but it is narrower than "observer notes".
- **Time-period and language.** English-language notes from 2019 to 2026 TFOP conventions. The
  Kepler contrast shows that conventions matter.
- **One author, one analysis pipeline.** No second analyst has chosen the arms. A many-analysts
  design (several teams, one question, independent choices) is the strongest available check
  for a single-author study.
- **Vendor dependence** of the featurizer (W3), and of the drift characterisation itself.
- **The pre-registration cuts both ways.** It rightly forbids fishing, but it also froze a
  design (8 columns, C text-only, no gold set) whose weak points are now visible. The remedy is
  new registrations, not edits (every proposal in [`05`](./05_project_proposals.md) is written
  that way).

---

## 7. The questions nobody has asked yet

1. **Does the text help where it would actually be used, on open candidates, before follow-up
   finishes?** Everything so far is retrospective (P1).
2. **What is a note worth?** Which follow-up type moves a candidate toward resolution most per
   telescope-hour (P6)?
3. **When the model and TFOPWG disagree, who is right?** High-confidence D predictions that
   contradict the disposition are candidates for mislabels, or for real overturns (the 4 FP→CP
   label flips between ExoFOP and NEA in `PLAN.md` §3.3 are a start).
4. **Is the text correcting the catalogue** (I7, P7)?
5. **Does text add to a pixel-level vetter** (`PLAN.md` §8.5, never done)? ExoMiner++ now
   publishes TESS scores, so this can be tested without running a CNN (P3).
6. **Is Jev necessary?** Two of the seven "semantic" questions reduce to phrase detection. How
   far do open models, NLI, embeddings and regex get (P2)?
7. **Why Kepler failed.** A mechanism exists in E7 and E9 and has not been tested (P5).
