# 05 — Project proposals

> Thirteen projects, ranked roughly by value per unit effort. **Every one that touches the
> registered claims is written to be pre-registered on its own** (append-only, as §11 of
> [`PREREGISTRATION.md`](../../PREREGISTRATION.md)). None of them edits a past criterion.
> Model costs use the measured `jev-1.13.0` rate ($0.042 / Mtok; a full TESS corpus pass was
> ~$0.24). Labels follow [`03`](./03_literature_and_prior_art.md).

## At a glance

| # | project | field | label | complexity | model cost | best fit |
| :-- | :--- | :--- | :--- | :--- | :--- | :--- |
| **P1** | Prospective prediction registry for open TESS candidates | astro × stats | **Genuine** | low–med (long wall-clock) | < $1 per scoring | **publication**, master's core |
| **P2** | ExoNotes-Gold: annotated benchmark + featurizer-agnostic replication | AI/ML × astro | **Genuine** (dataset) | medium | ~$1 + local GPU | **dataset paper**, master's, open source |
| **P3** | Text beyond pixels: notes on top of ExoMiner++ | astro × ML | **Genuine** | medium | $0–1 | publication, master's |
| **P4** | Notes → physics: follow-up constraints into TRICERATOPS | astro | Incremental | med–high | ~$0 | master's, publication |
| **P5** | Why TESS and not Kepler: the label-mechanism test | astro × metascience | **Genuine** | medium | ~$1 (K2) | **publication** |
| **P6** | The value of a follow-up observation | astro × stats | **Genuine** | med–high | $0 | master's thesis |
| **P7** | When notes and catalogue disagree: stellar classification | stellar astro | Incr. → genuine | low–med | $0 | RNAAS, portfolio |
| **P8** | LeakLens: a leakage-audit toolkit for text features | data science | Incremental (tool) | medium | $0 | **open source + JOSS** |
| **P9** | The ExoNotes design on GCN Circulars | transients × AI | **Genuine** | medium | ~$1–3 | publication, master's |
| **P10** | Drift observatory for science featurizers | AI metascience | Incremental | low | ~$1 / year | portfolio, workshop |
| **P11** | Quantum-classifier benchmark on a registered real dataset | quantum ML | Established (negative expected) | medium | $0 | portfolio / course |
| **P12** | TFOP collaboration network and consensus dynamics | complex systems | Speculative → incr. | medium | $0 | portfolio, SoS paper |
| **P13** | Lockboxed autoresearch: question discovery with an honest holdout | AI/ML | Incr. → genuine | medium | < $5 | publication, master's |

---

## P1 — ExoNotes-Prospective: a pre-registered prediction registry for open TESS candidates

> **Registered on 2026-09-23 as [`PREREGISTRATION.md`](../../PREREGISTRATION.md) §11.14, A-45.
> Where this sketch and A-45 differ, A-45 governs.** Two differences: the interim looks are
> descriptive only, so no α-spending boundary is needed. ExoMiner++ is not a registered arm.

- **Research question.** Do the frozen r6 features predict TFOPWG dispositions **assigned after
  the predictions were published** better than B, B+meta, B+TFIDF and, where available,
  ExoMiner++?
- **Motivation.** It is the only design that removes three problems at once: topic selection on
  outcome (W2), survivorship in the temporal split (W7), and text written after the verdict (E8).
  It is also the only honest test of the word "anticipate".
- **Background.** Every result so far is retrospective. About 5,300 TOIs are PC or APC
  (`toi_snapshot`: PC 4,819, APC 485). The open-candidate backlog is the operational problem
  (ExoNet cites >7,800 PCs and <720 confirmed).
- **Hypothesis.** H1: prospective D − B excludes zero and exceeds a prospective MDE, registered
  once the expected number of resolutions is known. H1b: D − B+meta > 0. H0 is publishable too.
- **Data.** ExoFOP TOI table and observer notes for every open TIC, **frozen at T₀** (only notes
  with `Lastmod` ≤ T₀). NEA `toi`. Monthly snapshots afterwards, which also give disposition
  dates at monthly resolution (none exist today).
- **Tools.** The existing pipeline (`etta`, Jev, CatBoost), a Zenodo deposit for the timestamped
  predictions and their SHA-256, and a small cron job for snapshots.
- **Method.** (1) Snapshot at T₀. (2) Train every arm on all TOIs labelled at T₀. (3) Predict
  every open TOI. (4) **Publish predictions, hashes and the analysis plan before any
  resolution.** (5) Evaluate at T₀+6, +12 and +18 months on newly resolved TOIs only.
- **Experimental design.** The primary comparison is D vs B, with a paired bootstrap over TIC.
  The secondary ones are D vs B+meta, D vs B+TFIDF, and D vs B+ExoMiner++ where TCE-matched.
  Three interim looks share α through an O'Brien–Fleming boundary. Resolutions are also reported
  **by time-to-resolution**, and never-resolved TOIs are treated as censored (links to P6).
- **Expected results.** A smaller gain than the retrospective +0.043: open TOIs have thinner
  and less decisive notes. The first resolutions are the fast, easy ones, so the gain may
  **shrink as the checkpoints go on**. That trajectory is itself a finding.
- **Success.** The registration published before the first resolution. A primary interval
  reported at every checkpoint. Either sign reported.
- **Limitations.** Months of waiting. TFOP decisions may use the same information, so the
  predictions are not independent of the process. Resolved-early TOIs are still a selected
  subset. ExoFOP may change its schema mid-study.
- **Extensions.** An open forecasting ledger where others register predictions (N7).
  Reliability weights for occurrence rates (RQ16). A follow-up prioritisation pilot with a TFOP
  sub-group.
- **Complexity.** Low–medium technically. The main cost is discipline and wall-clock time.
- **Prerequisites.** This repository, pre-registration practice, and basic survival analysis.
- **Fit.** **The strongest publication candidate**: an RNAAS note for the registration, then a
  full paper at the result. A natural master's-thesis core, with P6 as its second chapter.

---

## P2 — ExoNotes-Gold: an annotated benchmark and a featurizer-agnostic replication

- **Research question.** (a) How accurate is each featurized question against expert labels?
  (b) Does the TESS ΔAUC depend on the featurizer?
- **Motivation.** W3 (a single proprietary, drifting featurizer), W4 (no ground truth), A5
  (world knowledge) and A7 (stability is not validity) share one remedy.
- **Background.** PPI and DSL (Angelopoulos 2023; Egami 2023) turn a small gold set into valid
  corrected estimates. Grinsztajn et al. show embeddings are strong baselines. GCN-Circular
  extraction shows open models can read astronomical reports.
- **Objective.** A public gold set, plus a replication table of G2, G5 and B+meta across
  featurizers.
- **Data.** 300–500 TESS observer-note texts, stratified by length, topic cue and label
  (labels hidden from annotators), plus 150 Kepler CFOP texts. **Check redistribution with ExoFOP
  first.** If the text cannot be shared, release IDs and labels, with a fetch script.
- **Tools.** Argilla or Label Studio. Open-weights instruction models served locally (vLLM,
  llama.cpp or Ollama; 7B–70B class). A DeBERTa-MNLI zero-shot classifier. Sentence-transformer
  and astroBERT embeddings. `ppi_py` and `dsl`.
- **Method.** (1) Two domain-literate annotators per text, adjudication, and Cohen's κ per
  question. (2) Every featurizer answers the seven questions: probabilities from the LLMs and
  NLI, a linear probe on embeddings (fit in-fold), and the regex proxies from A-23. (3) Per
  question: AUC and accuracy against gold, and ECE with Wilson intervals. (4) Full-corpus
  features from each featurizer, then the registered G2, G5, B+meta and B+TFIDF arms. (5) PPI
  estimates of feature prevalence by class.
- **Design.** Pre-register the featurizer list, the prompts (the r6 wording, unchanged) and the
  primary test: *D_featurizer − B+TFIDF on the G5 arm, for each featurizer.*
- **Expected results.** Phrase-like questions (imaging no-companion, closure) near ceiling for
  every featurizer. The spectroscopic-verdict questions separate the featurizers. **If strong
  open models reproduce the ΔAUC, the finding is about the text.**
- **Success.** κ ≥ 0.7 on at least 5 of 7 questions. A replication table with ≥ 3 featurizers.
  The feature matrices published.
- **Limitations.** 30–40 annotator-hours, and annotators need the vocabulary (NEB, SB2, SPC). A
  300-row gold set limits calibration resolution. Local 70B models need a GPU.
- **Extensions.** An LLM-extraction benchmark (N10). Distilling a small offline featurizer
  (RQ30). Featurizer disagreement as uncertainty (RQ28). A gold-set seed for P9.
- **Complexity.** Medium. **Prerequisites:** NLP tooling, annotation methodology, exoplanet
  follow-up vocabulary.
- **Fit.** **Dataset or benchmark paper** (for example NeurIPS Datasets & Benchmarks, or RAS
  Techniques & Instruments), a master's project, and a lasting open-source asset.

---

## P3 — Text beyond pixels: do follow-up notes add to ExoMiner++?

- **Research question.** Out of sample, do note-derived features improve disposition prediction
  over a pixel-level vetter's score?
- **Motivation.** `PLAN.md` §8.5 called this "the interesting long-term question". ExoMiner++
  now publishes TESS scores, so it no longer needs a CNN to be trained.
- **Background.** ExoMiner++: 7,330 PCs matching 1,868 TOIs, with confidence scores. **It learns
  from TESS labels, so its scores on labelled TOIs are probably in-sample.** Read its data
  section for the label source and freeze date before designing anything.
- **Hypothesis.** Text adds most for false positives that pixels cannot see (on-target
  spectroscopic binaries, evolved hosts) and least for NEBs, whose centroid shifts pixels do
  see.
- **Data.** The ExoMiner++ TESS catalog (TCE-level, matched to TOIs by TIC and period), ExoFOP
  notes, and NEA `toi`.
- **Method.** B_vet = B + ExoMiner++ score, and D_vet = B_vet + the seven features. **Evaluate
  only on TOIs dispositioned after ExoMiner++'s label freeze**, or on its published CV scores if
  it has them. Add N1's FP-subtype labels for the stratified analysis.
- **Design.** Registered. D_vet vs B_vet is primary. D_vet vs B_vet+meta is the content test.
- **Expected results.** A positive increment smaller than +0.043, concentrated in the
  spectroscopy family.
- **Success.** A registered interval on an out-of-sample set. A stratified table by FP type.
- **Limitations.** Only 2-min targets. TCE–TOI matching errors. The out-of-sample n may be small
  (a few hundred), so compute the MDE first. TRICERATOPS FPPs exist for only a subset.
- **Extensions.** The same with LEO-Vetter and TESS-ExoClass outputs. A late-fusion model if the
  increment is large.
- **Complexity.** Medium. **Prerequisites:** TESS data products, TCE/TOI bookkeeping.
- **Fit.** Publication (AJ or RNAAS), master's chapter.

---

## P4 — Notes → physics: follow-up constraints into TRICERATOPS

- **Research question.** Can ExoFOP follow-up information be converted automatically into
  TRICERATOPS inputs, and how much does that change FPP and NFPP and the number of candidates
  that clear validation thresholds? The information is structured contrast curves plus
  companion statements in the notes.
- **Motivation.** It converts a *linguistic* signal into a *physical* probability, the direction
  `research/03` §2.2 argued for.
- **Background.** TRICERATOPS marginalises over EB, NEB and background scenarios and accepts
  contrast curves. The validation thresholds are FPP < 0.015 and NFPP < 10⁻³.
- **Objective.** A reproducible pipeline and a measured FPP shift.
- **Data.** ExoFOP imaging uploads (contrast-curve files through `download_imaging` listings),
  notes, TESS light curves (`lightkurve`) and TRICERATOPS.
- **Method.** For about 200 PCs that have imaging, run TRICERATOPS three ways: (a) no curve,
  (b) the ExoFOP curve, (c) a constraint derived from text alone. The featurizer only
  **locates** the sentence stating a detection limit. **Code parses and compares every number**,
  per `PLAN.md` §1.
- **Expected results.** (b) cuts NFPP for many TOIs. (c) approximates (b) where curves are
  missing, and over-constrains where notes are vague.
- **Success.** Agreement between (b) and (c). A count of threshold crossings. **No validation
  claim without full vetting**: this project measures FPP shifts, it does not validate planets.
- **Limitations.** Minutes of CPU per TOI (fine on a workstation). Heterogeneous file formats.
  Easy to over-claim.
- **Extensions.** Use P2's gold set to audit the extraction. Feed Gaia DR3 companions in as
  well.
- **Complexity.** Medium–high (domain-heavy). **Prerequisites:** transit photometry and
  high-resolution imaging basics.
- **Fit.** Master's thesis. Publication (AJ) if the text-only arm (c) holds up.

---

## P5 — Why TESS and not Kepler: the label-mechanism test

- **Research question.** Does the text predict disposition beyond follow-up volume only when the
  **label is produced through the follow-up the text records**?
- **Motivation.** The Kepler content test failed. E6, E7 and E9 suggest a mechanism: the TESS
  content signal sits in recon-spectroscopy conclusions, CFOP has little of that content, and
  Kepler confirmations are mostly statistical (`rv_flag` 0.05 vs 0.76). That mechanism was
  fitted after the result, so it needs its own test.
- **Hypothesis (H5).** The content gain (D+meta − B+meta) is larger for positives confirmed
  dynamically (RV or TTV mass) than for statistically validated positives, within each mission.
  K2 falls between TESS and Kepler.
- **Data.** NEA `pscomppars` (`rv_flag`, `ttv_flag`, and `pl_bmassprov`, where a mass from a
  mass–radius relation marks no dynamical mass), the existing TESS and Kepler matrices, and
  **ExoFOP-K2 notes** (a new, third corpus).
- **Method.** Stratify positives by confirmation route; false positives are shared across
  strata. Compare within-route content gains. K2 is an out-of-sample test of the predicted
  ordering.
- **Design.** **This is where D+meta on Kepler finally gets registered**, which
  `RESULTS_KEPLER.md` §4 says must happen first. Confirmation route correlates with host
  brightness (RV needs bright stars), so stratify on Tmag and report route-by-brightness cells.
- **Expected results.** If H5 holds, it gives a general rule for when text helps, tested again
  in P9 (N5). If it fails, the Kepler negative is about corpus content, which is also informative.
- **Success.** A pre-registered interaction test with its interval. The K2 ordering stated in
  advance and checked.
- **Limitations.** Small strata (statistically validated TESS CPs may number in the tens).
  Route metadata errors in the archive. A confound with brightness.
- **Extensions.** Clinical and transient analogues (P9). A methods paper on "label-generating
  process" as a design variable.
- **Complexity.** Medium. **Prerequisites:** planet confirmation and validation practice.
- **Fit.** **Publication.** With the leakage findings, this is the paper with the clearest story.

---

## P6 — The value of a follow-up observation

- **Research question.** Which follow-up types (recon spectroscopy, high-resolution imaging, SG1
  photometry, PRV) most accelerate resolution per unit telescope time, and for which kinds of
  candidate?
- **Motivation.** It turns ExoNotes from "can we predict the verdict" into "which observation
  should be taken next", which is the question TFOP actually faces (W10).
- **Background.** Bayesian experimental design and value-of-information theory are established.
  Their use on the TFOP record was not found.
- **Data.** ExoFOP structured observation tables (dated, with facility), notes, alert dates, and
  disposition dates. **Disposition dates do not exist in any archive.** They come from P1's
  monthly snapshots going forward, and from the upper-bound TFOPWG-note proxy (E8) for the past.
- **Method.** Survival models (Cox with time-varying covariates, random survival forests) for
  the hazard of resolution after each observation type. The **information gain per
  observation** is measured as the change in entropy of D's predicted P(planet) before and after
  it. A cost model uses rough hours per observation type.
- **Design.** Descriptive and hypothesis-generating. Follow-up is chosen *because* of a
  candidate's promise (confounding by indication), so causal language is off limits unless
  inverse-probability weighting is registered and its assumptions are stated.
- **Expected results.** Recon spectroscopy resolves on-target EB and SB false positives fast.
  Imaging rarely resolves a candidate alone but conditions later steps. Large effects by host
  brightness.
- **Success.** Hazard ratios with intervals by observation type. A cost-weighted ranking that a
  TFOP coordinator finds plausible, and ideally reviews.
- **Limitations.** Observational data. Coarse disposition dates. `Lastmod` edits.
- **Extensions.** A scheduling simulator (`astroplan` plus the learned hazards). Joint work with
  P12.
- **Complexity.** Medium–high (statistics). **Prerequisites:** survival analysis, causal
  inference basics.
- **Fit.** Master's thesis. PASP paper. Directly useful to TFOP.

---

## P7 — When the notes and the catalogue disagree: text-mined stellar classification

- **Research question.** How often do follow-up spectroscopists' descriptions contradict
  catalogue stellar parameters? Which side is right? And what does that do to planet radii and
  disposition prediction?
- **Motivation.** E10: 148 of 357 hosts described as evolved have dwarf-like TIC log g. I7 says
  part of the text signal may be the text correcting the catalogue.
- **Data.** Feature `host_star_described_as_evolved`, TIC v8, Gaia DR3 astrophysical parameters
  (GSP-Phot log g, FLAME radius), ExoFOP-uploaded spectroscopic parameters, and TOI `pl_rade`.
- **Method.** (1) Build the contradiction set. (2) Adjudicate **in code** against Gaia and
  spectroscopic values. (3) Estimate radius corrections (R_p scales with R⋆). (4) The I7 test:
  add Gaia log g and radius to B and measure how much D's gain shrinks.
- **Expected results.** A catalogue of TIC misclassifications (mostly subgiants called dwarfs),
  some text errors, and a measurable share of the D gain explained.
- **Success.** An adjudicated table with its error analysis. The I7 ΔAUC shrinkage measured.
- **Limitations.** Gaia parameters have their own systematics (binarity, extinction). n in the
  hundreds.
- **Extensions.** The same for companions reported in text vs Gaia RUWE and resolved pairs
  (RQ18).
- **Complexity.** Low–medium. **Prerequisites:** stellar parameters, Gaia archive queries.
- **Fit.** An RNAAS note, a portfolio project, a master's chapter. **The cheapest real
  astrophysics result in this document.**

---

## P8 — LeakLens: a leakage-audit toolkit for text features in scientific ML

- **Objective.** Package ExoNotes' discipline as a reusable library: (1) label-echo tiers and
  clause-set registries with per-clause P(y | clause) and marginal counts; (2) the dilution floor
  (B+N) and the oracle MDE; (3) the volume control (B+meta, D+meta); (4) stacked bag-of-words and
  embedding comparators (W1); (5) paraphrase and repeat arms for any featurizer; (6) drift
  propagation (A-33); (7) a mutation-tested gate verifier; (8) a model-info-sheet generator
  (Kapoor & Narayanan).
- **Motivation.** These tools solved real problems here and exist nowhere as a package.
- **Data.** ExoNotes as the worked example (the published matrix, W3), plus one public
  non-astronomy text-and-tabular dataset (for example from the STRABLE benchmark) to prove
  generality.
- **Tools.** Python with a scikit-learn-style API, CatBoost or LightGBM, pytest with mutation
  tests, and documentation.
- **Success.** One call reproduces ExoNotes' gates from the matrix. It works on a second
  dataset. A JOSS paper.
- **Limitations.** Maintenance. The line between a general and an ExoNotes-specific clause set.
- **Complexity.** Medium (software engineering). **Prerequisites:** packaging, testing.
- **Fit.** **Open-source project plus a JOSS publication**, and a strong portfolio piece.

---

## P9 — The ExoNotes design on GCN Circulars

- **Research question.** Does the text of the earliest GCN Circulars about a GRB (for example
  the first 24 h) predict whether it will get a spectroscopic redshift, beyond structured prompt
  and afterglow properties?
- **Motivation.** It tests the design, and N5, on a second science. **Circulars have exact
  timestamps**, so the temporal control that ExoFOP could not have is clean here.
- **Background.** 40,500 circulars. LLM topic classification and zero-shot redshift extraction
  already exist (arXiv:2511.14858). The predictive, leakage-controlled question does not.
- **Hypothesis.** Volume (the number of circulars and responding teams) will be strongly
  predictive, because bright afterglows draw telescopes. By N5, redshift acquisition runs
  through the follow-up the circulars describe, so content should add beyond volume.
- **Data.** The GCN Circulars archive (public), Swift BAT, XRT and UVOT properties, observability
  (sky position, Moon, Galactic extinction), and redshift labels (published GRB redshift tables,
  or the extraction from the LLM paper, audited).
- **Leakage design.** Use only circulars posted **before** the first redshift report. A
  label-echo tier ("absorption lines", "z =", "redshift"). Volume controls (B+meta, D+meta). A
  question set designed label-blind with two disjoint holdouts (the Kepler gate discipline).
- **Method.** Port the pipeline, register, score, gate.
- **Expected results.** A large volume effect. The content effect is the open question.
- **Success.** A registered result either way. The N5 prediction checked.
- **Limitations.** Defining B carefully (some structure lives inside the circulars themselves).
  Observability confounds. Redshift label completeness.
- **Alternatives, same design.** TNS classification reports (RQ39, severe echo), LIGO aLOG with
  DetChar (RQ40), accelerator eLogs with a facility partner (RQ41).
- **Complexity.** Medium. **Prerequisites:** GRB follow-up basics, the ExoNotes pipeline.
- **Fit.** Publication (ApJS or RASTI), master's thesis. **The best interdisciplinary portfolio
  piece.**

---

## P10 — Drift observatory for science featurizers

- **Research question.** How much do API-hosted models used as scientific instruments drift over
  months, and does the drift ever move a registered verdict?
- **Method.** Freeze a probe set (the G3 200-row sample, the 27 gate cases, and P2's gold set).
  Run the same-wording repeat arm monthly (`gates.yml` already runs monthly). Keep SPC charts
  (CUSUM or EWMA) of mean |Δp| and ρ, test for silent updates (arXiv:2504.12335), and propagate
  to ΔAUC with A-33. **Add one locally pinned open-weights model as a zero-drift control.**
- **Cost.** ~$0.06 per month per API model.
- **Success.** A year of drift series. Any silent change detected and dated.
- **Complexity.** Low. **Fit.** Portfolio, a workshop paper, lasting infrastructure.

---

## P11 — Quantum-classifier benchmark on a pre-registered real dataset

> **Label: established, negative result expected.** Included because quantum projects were in
> this reassessment's scope, and because this is the *defensible* form of one. It will not produce physics.

- **Research question.** Under ExoNotes' registered protocol (grouped CV, paired bootstrap,
  dilution floor), does any QML model match CatBoost or logistic regression on the 15-feature
  matrix?
- **Background.** Bowles, Ahmed & Schuld 2024: across 160 datasets, classical models win and
  removing entanglement often does not hurt.
- **Data.** The published ExoNotes matrix (W3): 1,482 rows × (8 numeric + 7 text) features.
- **Tools.** PennyLane (the Bowles et al. benchmark code), Qiskit simulators (≤ 15 qubits). No
  hardware is needed.
- **Method.** Pre-register the models (quantum kernel SVM, variational classifier, data
  re-uploading), **equal tuning budgets** for classical and quantum, and "de-quantised" controls
  (entanglement removed, and a classical kernel with the same feature map). Report grouped-CV AUC
  and wall-clock cost.
- **Expected results.** QML at or below classical.
- **Success.** A clean, reproducible negative, and a teaching artifact on benchmarking
  discipline.
- **Limitations.** No advantage is expected. Simulators only. Small data.
- **Complexity.** Medium. **Prerequisites:** QML basics, PennyLane.
- **Fit.** Portfolio or course project. A publication only as benchmarking methodology.

---

## P12 — The TFOP collaboration network and the dynamics of consensus

> **Label: speculative → incremental.**

- **Research question.** How is follow-up effort distributed across teams? Does the position of
  a candidate's observers in the collaboration network relate to how fast and how decisively it
  resolves? Do later notes echo earlier conclusions?
- **Data.** Observer notes (author, `Lastmod`, TIC), structured observation tables (observer,
  facility), and dispositions.
- **Method.** A bipartite observers × targets network, and a temporal network. Community
  detection. Embedding similarity over time to look for herding. Survival models shared with P6.
- **Ethics.** Analyse at team or facility level and **never rank individuals**. Check ExoFOP's
  terms before publishing author-level statistics.
- **Expected results.** Heavy-tailed effort, with a few teams carrying most of the informative
  text (E6 already hints at this). Descriptive insight for TFOP coordination.
- **Complexity.** Medium. **Fit.** Portfolio. A science-of-science paper if P6's dates exist.

---

## P13 — Lockboxed autoresearch: automated question discovery with an honest holdout

- **Research question.** When an LLM proposes new questions from worst-predicted rows and
  feature importances (`PLAN.md` §8.1), how much of its development-set gain survives on a
  lockbox? How does the optimism grow with the number of rounds?
- **Motivation.** It is the original `research/03` vision, and it was never run. It also
  answers, for LLM-driven feature discovery in general, a question CAAFE and LLM-FE do not
  control for.
- **Design.** Split by TIC into **dev (60%) and lockbox (40%)**. The lockbox is scored exactly
  once, at the end. Each round runs propose → Jev → grouped CV on dev only. **A label-permuted
  control** (the proposer sees shuffled labels) measures how much "gain" a proposer can
  manufacture from noise. Register the proposer prompt verbatim.
- **Tools.** A reasoning model as proposer, Jev as answerer (a 10-question round over the corpus
  is ~$0.2–0.3), and the existing CV machinery.
- **Expected results.** Development gains inflate over rounds. The lockbox gain is smaller. The
  permuted control shows non-zero development "gain", which directly estimates the optimism.
- **Success.** A lockbox interval for the discovered set against r6. An optimism curve over
  rounds.
- **Limitations.** A lockbox of ~550 TICs is noisy (compute its MDE first). There is a lot of
  freedom in the proposer prompt, which is why it is registered.
- **Complexity.** Medium. **Prerequisites:** LLM APIs, CV methodology.
- **Fit.** Publication (an ML methods workshop, or a data-science venue), a master's project.
