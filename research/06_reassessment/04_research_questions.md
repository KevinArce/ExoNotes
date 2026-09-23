# 04 — New directions and research questions

> Each question says **why it follows from this project**, what kind of work it is, and a label
> from [`03`](./03_literature_and_prior_art.md): **Established · Incremental · Genuine
> opportunity · Speculative**. Questions developed into full proposals point to their project
> (P1–P13) in [`05`](./05_project_proposals.md).

---

## 1. Where the project connects to other disciplines, and where it does not

This reassessment was asked to consider many fields without forcing connections. This table
rates each connection **before** any question is proposed, so the weak ones stay visibly weak.

| field | strength | the actual link |
| :--- | :--- | :--- |
| Exoplanet science | **Strong** | Same corpus, same labels. Vetting, validation, occurrence rates, stellar parameters |
| Time-domain astronomy / transients | **Strong** | GCN Circulars, TNS AstroNotes and ATels are expert free text attached to structured alerts. It is the same problem, with precise timestamps |
| AI / ML | **Strong** | Featurizer comparison, gold sets, lockboxed feature discovery, drift |
| Statistics | **Strong** | Conditional-importance inference, CV intervals, measurement error, survival |
| Data science / open science | **Strong** | Leakage audits, reproducibility kits, prediction registries |
| Stellar astrophysics | **Moderate** | Text vs TIC stellar classification (E10). Binarity from imaging text vs Gaia |
| Gravitational waves | **Moderate** | Detector logbooks (aLOG) and GW-counterpart circulars. A method transfer, not a physics one |
| Information theory | **Moderate** | Conditional mutual information and value of information as the natural units of "text adds signal" |
| Complex systems / science of science | **Moderate** | The TFOP collaboration network and consensus dynamics |
| Particle / accelerator physics | **Moderate (operations only)** | eLogbooks. Blind-analysis culture. **No link to the physics analyses themselves** |
| Scientific visualisation | **Moderate** | Evidence-trail timelines. Reliability diagrams per question |
| Computational physics / simulation | **Weak–moderate** | Simulation-based robustness (A-33 generalised). FPP forward models (TRICERATOPS) |
| Black holes | **Weak** | Only through transient text (TDE classification reports) |
| Cosmology, dark matter, dark energy | **Weak** | Methodological only: blinding and pre-registration. No data link worth a project |
| Quantum computing | **Weak** | Benchmarking discipline; characterising noisy black-box devices. **No scientific advantage expected** |
| Quantum mechanics / many-body physics | **None found** | No defensible link to this project's data or methods. Nothing is proposed |
| HPC | **Weak** | The corpora are small (MB). Only large open-model sweeps or ADS full-text work would need it |

---

## 2. Research questions

### A. Is the current claim true? (validity)

- **RQ1 — Does the TESS content gain hold prospectively?** Score the TOIs dispositioned *after*
  the 2026-09-19 snapshot with the frozen r6 questions.
  *Follows from:* W2 (topic selection) and W7 (survivorship). A prospective test removes both.
  *Type:* data analysis, pre-registered. **Genuine opportunity → P1.**
- **RQ2 — Is the gain about the text or about Jev?** Swap in an open-weights instruction model,
  an NLI zero-shot classifier, sentence embeddings and regex proxies.
  *Follows from:* W3 and A13. *Type:* computational experiment. **Genuine (as a dataset) → P2.**
- **RQ3 — Do structured judgments beat bag-of-words and embeddings on top of B, under
  registration?** *Follows from:* E2 (80% and 62%). *Type:* registered arm. **Incremental.**
- **RQ4 — How much optimistic bias did full-corpus topic selection introduce?** Re-run the
  A-19/A-23 selection on crude cues *within* training folds.
  *Follows from:* W2. *Type:* simulation, $0. **Incremental.**
- **RQ5 — Does the text beat ExoFOP's own structured follow-up tables?**
  *Follows from:* C5 and W5. It decides whether the archive-design implication is real.
  *Type:* data analysis, $0. **Genuine opportunity.**
- **RQ6 — Does Jev use world knowledge?** Mask every designation and re-score.
  *Follows from:* A5, and `contains_object_designation` averaging 0.929. *Type:* experiment,
  ~$0.24. **Incremental.**
- **RQ7 — What is each question's accuracy against human labels, and does a PPI- or
  DSL-corrected ΔAUC differ?** *Follows from:* `RESULTS.md` §9.2. *Type:* annotation +
  statistics. **Incremental → P2.**
- **RQ8 — Do nested-CV or cross-fitted intervals change any verdict?** *Follows from:* W8.
  *Type:* statistics, $0. **Incremental.**

### B. What does the text actually know? (mechanism)

- **RQ9 — Is the "beyond volume" signal entirely the TRES reconnaissance team's conclusions?**
  Stratify by author and team. *Follows from:* E6 (the spectroscopy family carries it) and E7
  (it is volume-independent). *Type:* data analysis. **Incremental.**
- **RQ10 — Is part of the text signal really the correction of wrong TIC stellar parameters?**
  Add Gaia DR3 FLAME / GSP-Phot log g and radius to B and see whether D's gain shrinks.
  *Follows from:* E10 (148 of 357 "evolved" hosts are catalogued as dwarfs) and I7.
  **Genuine → P7.**
- **RQ11 — Does the text gain depend on the confirmation route?** Compare RV-confirmed and
  statistically validated TESS planets. *Follows from:* E9 (rv_flag 0.76 TESS vs 0.05 Kepler).
  **Genuine → P5.**
- **RQ12 — Why did Kepler fail: the corpus content or the label mechanism?** K2, with
  ExoFOP-K2 notes and a mixed confirmation route, is the natural third corpus.
  *Follows from:* E7 and E9 together. **Genuine → P5.**
- **RQ13 — Does text add information on top of a pixel-level vetter?** Use ExoMiner++ scores on
  TOIs dispositioned after its training labels were frozen. *Follows from:* `PLAN.md` §8.5.
  **Genuine → P3.**
- **RQ14 — How much information sits in the excluded TFOPWG-account notes (SG1 photometry)
  after every disposition token is stripped?** *Follows from:* W12. *Type:* registered arm,
  high leakage risk. **Incremental.**
- **RQ15 — Is the text more informative for some false-positive types than others?**
  *Follows from:* the NEB, SB2 and evolved-host content of the features. See N1 for a label
  source. **Genuine.**

### C. Exoplanet astrophysics

- **RQ16 — Can calibrated P(planet) for open TOIs serve as reliability weights in TESS
  occurrence-rate work?** *Follows from:* D's sharpness (Brier 0.121 → 0.089) and Bryson et
  al. 2020. *Caveat:* the training labels come from resolved TOIs, so the weights inherit their
  selection. **Speculative → a P1 extension.**
- **RQ17 — How often do follow-up spectra contradict the TIC's evolutionary stage, and how much
  does that bias planet radii?** *Follows from:* E10. **Genuine → P7.**
- **RQ18 — Can imaging companions reported in the notes be validated against Gaia DR3 (RUWE,
  resolved pairs) and turned into dilution-correction flags?** *Follows from:*
  `imaging_reports_companion_present`. **Incremental.**
- **RQ19 — Which follow-up type shortens time-to-disposition most per telescope-hour?**
  *Follows from:* the notes' timestamps plus ExoFOP's observation tables. **Genuine → P6.**
- **RQ20 — Do planets whose notes report a nearby companion differ systematically in catalogued
  radius (uncorrected dilution), and does that matter for the radius valley?** *Follows from:*
  RQ18. **Speculative.**
- **RQ21 — Which dispositions does the model most confidently disagree with, and on audit, how
  many are mislabels or overturns?** *Follows from:* D's out-of-fold predictions (recomputable
  at $0 with `035`'s code) and the 4 FP→CP flips in `PLAN.md` §3.3. *Type:* audit list, $0.
  **Genuine, small, high value.**
- **RQ22 — Do Planet Hunters TESS notes predict CTOI → TOI promotion?** *Follows from:* the same
  design on community candidates. *Data access to check first.* **Genuine / speculative.**
- **RQ23 — What makes a candidate slow to resolve?** Use time-to-disposition as the target
  (`research/03` §6.9). **Genuine → P6.**

### D. AI and machine learning

- **RQ24 — How much does an automatic question-proposer loop gain on a true lockbox, compared
  with its development-set gain?** *Follows from:* `PLAN.md` §8.1, never run, and W2.
  **Genuine (methodology) → P13.**
- **RQ25 — Do small open models match Jev on these seven questions, measured against gold
  labels and ΔAUC?** **→ P2.**
- **RQ26 — Does paraphrase stability (G3's ρ) predict a question's accuracy against gold?** If
  it does, G3 becomes a cheap validity proxy. If it does not, G3 measures only reliability.
  *Follows from:* A7. **Genuine (small).**
- **RQ27 — Does averaging k repeated identical calls improve the features?** It turns the ~0.005
  nondeterminism into a denoising knob and costs k× (still cents). *Follows from:* the G3
  repeat arm. **Incremental.**
- **RQ28 — Is disagreement between featurizers a useful uncertainty signal?** Are rows where
  featurizers disagree predicted worse? **Incremental.**
- **RQ29 — How are Noul and Score calibrated on astronomical text against gold?** This is the
  measurement `research/03` §6.5 called "the most important plot". **Incremental → P2.**
- **RQ30 — Can a small local model distilled from Jev's outputs reproduce the features
  offline?** It would remove the vendor dependence. **Incremental.**
- **RQ31 — Does a question set designed on one corpus transfer without redesign, when the
  holdout discipline is kept?** *Follows from:* the Kepler gate's holdouts (A-41 41.1).
  **Incremental.**
- **RQ32 — How do science-grade featurizers drift over months?** **Incremental → P10.**

### E. Statistics and information theory

- **RQ33 — How many bits does the follow-up record carry beyond the catalogue?** Estimate the
  conditional mutual information I(Y; T | X) with bounds, and compare TESS and Kepler in
  bits instead of ΔAUC. *Follows from:* ΔAUC being an awkward unit near the ceiling.
  **Incremental.**
- **RQ34 — Is the dilution floor general?** How does ΔAUC(B+N − B) scale with n, k, the learner
  and the base AUC? Would most published "adding X helps" astro-ML results survive it?
  *Follows from:* A-1. **Genuine (a methods note).**
- **RQ35 — What is the decision value?** Net-benefit curves, and precision at fixed planet
  recall. *Follows from:* W10. **Incremental.**
- **RQ36 — Treat the featurizer as a noisy instrument (errors in variables). How much is ΔAUC
  attenuated by the measured ~0.005 noise?** *Follows from:* A-33's simulation, inverted.
  **Incremental.**
- **RQ37 — Survival models with unresolved TOIs as censored observations.** *Follows from:* W7.
  **Incremental → P6.**

### F. Transfer to other sciences (the design, not the data)

- **RQ38 — GCN Circulars.** Does early circular text (the first 24 h) predict whether a GRB
  receives a spectroscopic redshift, beyond the numeric Swift and Fermi properties?
  *Follows from:* the ExoNotes design plus precise circular timestamps, which ExoFOP lacks.
  **Genuine → P9.**
- **RQ39 — TNS reports.** Do discovery and classification comments predict the spectroscopic
  class beyond broker light-curve features? Label echo will be severe, so the ExoNotes leakage
  machinery is the point. **Genuine (with care).**
- **RQ40 — LIGO aLOG.** Do logbook entries predict data-quality vetoes or glitch rates beyond
  auxiliary-channel numerics? *Needs DetChar collaborators.* **Speculative / genuine.**
- **RQ41 — Accelerator eLogs.** Does shift-log text predict downtime beyond machine-state
  numerics? *Needs a facility partner* (see the eLog RAG work in [`03`](./03_literature_and_prior_art.md)).
  **Genuine.**
- **RQ42 — Zooniverse Talk (Gravity Spy, Planet Hunters).** Does volunteer discussion text
  predict expert classification beyond vote fractions? **Genuine / speculative.**
- **RQ43 — Visual-inspection comments in spectroscopic surveys.** Do they predict redshift
  failures beyond pipeline flags? *Whether such comments are public is unverified.*
  **Speculative.**

### G. Quantum computing (honestly weak)

- **RQ44 — Does any QML model match CatBoost on the ExoNotes matrix under the same registered
  protocol?** Expected answer: no (Bowles et al. 2024). **Established → P11**, as a
  benchmarking exercise only.
- **RQ45 — Can ExoNotes' noisy-instrument toolkit characterise run-to-run drift of cloud quantum
  processors on a fixed benchmark over weeks?** The toolkit is repeat arms, paraphrase-style
  perturbation arms, noise propagation to a headline, and mutation-tested verifiers.
  *Follows from:* a methodological overlap only. QCVV is its own mature field.
  **Incremental / speculative.**
- **RQ46 — Does the wording of published quantum-advantage claims predict a later classical
  rebuttal?** This is a science-of-science claims ledger. The sample is small (tens of claims),
  so it is a curated literature database, not ML. **Speculative.**
- *Not proposed:* quantum-annealing question selection (classically trivial at k ≤ 40), QNLP on
  notes (toy-scale), and anything touching quantum simulation or many-body physics (no link).

### H. Complex systems and science of science

- **RQ47 — Does the structure of the TFOP collaboration network (who observes which candidate,
  and when) predict time-to-disposition?** **Speculative → incremental → P12.**
- **RQ48 — Do later notes echo earlier notes' conclusions (herding)?** **Speculative.**
- **RQ49 — What text precedes a disposition flip (FP → CP)?** **Genuine (small n).**
- **RQ50 — What did pre-registration catch here?** Catalogue every defect, falsified prior and
  corrected number as evidence for the practice in astronomy. **Incremental (metascience note).**

---

## 3. Opportunities in astrophysics and quantum physics, summarised

**Astrophysics:** the defensible ones, in order of value per unit effort:

1. Prospective prediction for open TOIs (RQ1, P1).
2. Text on top of pixel vetters (RQ13, P3).
3. Stellar-parameter contradictions (RQ10/RQ17, P7).
4. The label-mechanism explanation of the Kepler failure (RQ11/RQ12, P5).
5. Value of follow-up information (RQ19/RQ23, P6).
6. Transfer to transient text: GCN and TNS (RQ38/RQ39, P9).

Gravitational waves come in through detector logbooks (RQ40), not through any astrophysical
signal. Black holes, dark matter, dark energy and cosmological simulations have **no data link
worth building**. The only transferable thing is the blinding and pre-registration practice
(RQ50), and cosmology already practises blinding.

**Quantum:** the honest verdict is that **nothing here produces quantum-physics results.** The
defensible options are (a) a rigorous QML benchmark with an expected negative result (P11), and
(b) moving the *noisy-black-box methodology* to device characterisation (RQ45). Both are
portfolio-grade. Neither is a research programme. A "quantum + astrophysics" project built on
this corpus would be a forced connection, and **this document recommends against it**.

**AI + astrophysics** is where the real combined value lies: P1, P2, P3, P9 and P13.

---

## 4. Non-obvious but defensible ideas

Each is labelled. None is established science.

- **N1 — Turn the project's biggest trap into a label source.** The `Comments` field restates
  the disposition, and often the **false-positive type**: `retired as NEB`, `SB1`, `EB`. It was
  rightly banned as a *feature*. As a *label* for FP subtype it is nearly free, large (hundreds
  of rows) and cleanly separated from the observer-note text. It would enable RQ15 (which FP
  types the text detects) without new annotation. **Genuine; the labels need an audit.**
- **N2 — The disagreement list as a product.** D's high-confidence out-of-fold predictions that
  contradict TFOPWG form a short, rankable audit list for TFOP. It costs $0 today. Some entries
  will be mislabels, and each confirmed one is a concrete contribution. **Genuine.**
- **N3 — Notes as a stellar-catalogue error detector** (E10, P7). The spectroscopist's words
  disagree with TIC log g for about 40% of "evolved" hosts. **Genuine.**
- **N4 — Featurizer noise as an ambiguity index.** Rows where identical repeated calls disagree
  most are the ambiguous notes. Does ambiguity predict slow or contested dispositions? The G3
  repeat arm already has 200 rows. **Speculative, and free to check.**
- **N5 — A cross-domain meta-hypothesis.** *Text adds predictive information beyond volume only
  when the label is produced through the process the text records.* TESS (RV-driven labels)
  passed and Kepler (validation-driven labels) failed. GCN and TNS corpora can test it again
  (P5 + P9). **Genuine and falsifiable.**
- **N6 — The dilution floor as a reviewer's checklist item.** Most astro-ML papers that add a
  feature group report ΔAUC with no zero point. A short note that measures the floor across
  public benchmarks (RQ34) could change practice. **Genuine (methods).**
- **N7 — An open forecasting ledger for exoplanet dispositions.** Anyone registers
  hash-committed predictions for open TOIs: humans, ExoMiner++, ExoNotes, TRICERATOPS FPPs. The
  ledger scores them as TFOPWG resolves the candidates. It is P1 generalised into community
  infrastructure. **Genuine; uptake is speculative.**
- **N8 — Kepler as a natural control.** Its labels mostly do not run through the notes, so
  Kepler estimates how much "text signal" is process echo. That makes the Kepler negative an
  asset. **Genuine.**
- **N9 — Text against pixels as a two-way audit.** SG1 "on target" statements can be checked
  against TESS difference-image centroids. Disagreement flags errors in either. **Incremental.**
- **N10 — ExoFOP as an extraction benchmark for LLMs.** Abbreviation-dense, header-polluted
  (`832nmNo secondary sources`), expert text whose answers are unambiguous to a specialist. It is
  a realistic stress test far from web text (part of P2). **Genuine as a benchmark.**
