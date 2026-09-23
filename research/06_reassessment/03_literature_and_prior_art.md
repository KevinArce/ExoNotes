# 03 — Prior art: what already exists, and what that makes each idea

> Searched 2026-09-23. **A search is not proof of absence.** "No prior work found" below means
> the searches run for this document found none. It does not mean none exists. Where a citation
> comes from memory rather than a search, it is a standard reference (for example Lissauer et
> al. 2012), and its link goes to the canonical record. Check before citing in a paper.

**Classification used here and in [`05`](./05_project_proposals.md):**

| label | meaning |
| :--- | :--- |
| **Established** | Done and published. Repeating it here would be practice or tooling, not research |
| **Incremental** | A known method applied to a new corpus or setting. Publishable as a short note or a solid thesis chapter |
| **Genuine opportunity** | A question that existing work makes possible but that the searches found no one answering |
| **Speculative** | Defensible in principle, weak or untested in practice. Label it as such wherever it appears |

---

## 1. LLMs as featurizers for tabular prediction — *established in ML*

| work | what it established |
| :--- | :--- |
| CAAFE — Hollmann, Müller & Hutter 2023 ([arXiv:2305.03403](https://arxiv.org/abs/2305.03403)) | An LLM proposes features from a dataset description. ROC AUC 0.79 → 0.82 across 14 datasets |
| FeatLLM — Han et al. 2024 ([arXiv:2404.09491](https://arxiv.org/abs/2404.09491)) | LLM-extracted rules as features for few-shot tabular learning |
| LLM-FE ([OpenReview](https://openreview.net/pdf?id=JhJPJtau8B)); FeRG-LLM ([arXiv:2503.23371](https://arxiv.org/abs/2503.23371)) | Evolutionary and reasoning-driven LLM feature engineering |
| LATTEArena ([arXiv:2606.09004](https://arxiv.org/html/2606.09004)) | A benchmark and taxonomy of 15 LLM feature-engineering methods |
| Grinsztajn, Oyallon & Varoquaux 2023 ([arXiv:2312.09634](https://arxiv.org/abs/2312.09634)); STRABLE ([arXiv:2605.12292](https://arxiv.org/html/2605.12292)) | How to vectorise string columns. Large LLM encoders help mainly on free-text-heavy tables, and simple embeddings are strong baselines |
| TypeSafe `autoresearch_feature_discovery` cookbook ([docs](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery.md)) | The pattern ExoNotes adapted: questions → probabilities → gradient boosting |

**What this makes ExoNotes.** The *method* (LLM judgments as features for a GBM) is
**established**. What the ML literature does not usually do is the *discipline*: a registered
MDE, a dilution floor, a volume control, label-echo tiers and leakage-stripped arms. That is
ExoNotes' methodological contribution. The strongest evidence against a novelty claim is
Grinsztajn et al.'s finding that **embeddings are strong baselines**. It matches E2, where
bag-of-words on top of B reaches most of the gain, and it is why an embedding arm belongs in any
future registration.

---

## 2. Valid statistics from LLM-produced variables — *established; directly applicable*

| work | relevance |
| :--- | :--- |
| Prediction-powered inference — Angelopoulos et al. 2023, *Science* ([arXiv:2301.09633](https://arxiv.org/abs/2301.09633)) | Combines many model-labelled rows with a few human-labelled ones for valid confidence intervals |
| Design-based supervised learning — Egami et al. 2023 ([arXiv:2306.04746](https://arxiv.org/abs/2306.04746)); `dsl` ([site](https://naokiegami.com/dsl/)) | The same goal for downstream regressions using LLM annotations |
| Multi-perspective LLM annotations ([arXiv:2603.21404](https://arxiv.org/html/2603.21404)); debiasing benchmark ([EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1000.pdf)) | Recent evaluations of these corrections |

**What this makes ExoNotes.** Applying PPI or DSL to the Jev features is **incremental**, but it
is exactly what W4's gold set enables. It is the principled answer to *"we cannot plot
per-question reliability because nothing is labelled"* (`RESULTS.md` §9.2).

---

## 3. Leakage and reproducibility in ML-based science — *established framework*

| work | relevance |
| :--- | :--- |
| Kapoor & Narayanan 2023, *Patterns* ([paper](https://www.cell.com/patterns/fulltext/S2666-3899(23)00159-9)) | Eight leakage types across 17 fields and 294 papers. Proposes "model info sheets" |
| "Which leakage types matter?" ([arXiv:2604.04199](https://arxiv.org/pdf/2604.04199)) | Quantifies leakage types across 2,047 benchmark datasets |

**Mapping ExoNotes onto the taxonomy:** the `Comments` echo and `pscomppars` membership are
*illegitimate features* (a proxy for the outcome). Topic selection on full-corpus |AUC| (W2) is
*feature selection on training and test data*. Post-disposition text is *temporal leakage*. The
host-level feature sharing handled by GroupKFold is *non-independence*. **ExoNotes is an
unusually well-documented astronomy case study for this literature**, and writing it up in
those terms is **incremental but useful** (P8).

---

## 4. The clinical-notes analogue — *established in medicine, rare in astronomy*

Clinical NLP has spent a decade on the ExoNotes question: *do free-text notes add to structured
records, and how do outcomes leak into notes?*

| work | parallel |
| :--- | :--- |
| van Aken et al. 2021, admission-note outcome prediction ([arXiv:2102.04110](https://arxiv.org/abs/2102.04110)) | Keeps only sections knowable at admission. **The same idea as S2b**, done by section instead of by timestamp |
| Notes + structured EHR for mental-health crisis prediction ([PMC10694623](https://pmc.ncbi.nlm.nih.gov/articles/PMC10694623/)) | Text + structured beats either alone. The same design as D vs B |
| Label leakage in clinical text ([arXiv:2602.15852](https://arxiv.org/pdf/2602.15852)) | *"the patient has passed away"* is to mortality what `retired as NEB` is to disposition |

**What this makes ExoNotes.** Importing clinical practice (note-section filtering, time-of-
prediction cut-offs, notes written after the outcome) is **incremental** and should be cited in
any write-up. It shows that the design choices here are standard in a neighbouring field, which
strengthens them.

---

## 5. Inference for "does feature set X add beyond Y?" — *established statistics*

| work | relevance |
| :--- | :--- |
| Williamson, Gilbert, Simon & Carone, *JASA* ([arXiv:2004.03683](https://arxiv.org/abs/2004.03683)); `vimp` / `vimpy` ([docs](https://bdwilliamson.github.io/vimp/)) | **ExoNotes' ΔAUC is this framework's AUC-based variable importance.** It gives cross-fitted, valid CIs and a test of zero importance |
| Bates, Hastie & Tibshirani 2023, *JASA* ([arXiv:2104.00673](https://arxiv.org/abs/2104.00673)); `nestedcv` ([GitHub](https://github.com/stephenbates19/nestedcv)) | Naive CV intervals under-cover by a factor of 2–3. Nested CV fixes it |
| Nadeau & Bengio 2003, *Machine Learning* 52:239 | Corrected resampled t-test for comparing learners |
| Lei et al. 2018, *JASA* (LOCO); Candès et al. 2018, *JRSS-B* (model-X knockoffs / CRT) | Conditional-independence tests of "text ⟂ label given numerics" |

**What this makes ExoNotes.** Adopting any of these is **incremental** and cheap. It matters
only for marginal comparisons (W8), which is where every future question lives (D vs
B+TFIDF, D+meta vs B+meta).

---

## 6. Drift and nondeterminism of API models — *established; ExoNotes adds a clean measurement*

| work | relevance |
| :--- | :--- |
| Atil et al. 2024, *Non-determinism of "deterministic" LLM settings* ([arXiv:2408.04667](https://arxiv.org/abs/2408.04667)) | Temperature-0 outputs vary across runs on five models |
| Chen, Zaharia & Zou, *How is ChatGPT's behavior changing over time?* ([arXiv:2307.09009](https://arxiv.org/abs/2307.09009)) | The "same" model changes substantially within months |
| Thinking Machines Lab 2025, *Defeating nondeterminism in LLM inference* ([blog](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)) | The cause is batch-variant kernels, and it can be fixed on the serving side |
| *You've Changed: detecting modification of black-box LLMs* ([arXiv:2504.12335](https://arxiv.org/abs/2504.12335)) | Statistical tests for silent model updates |

**What this makes ExoNotes.** The drift arm (A-33), the same-wording repeat arm and the
"measured noise floor ≥ 0.001" CI check are a **small, clean contribution**: a science pipeline
that *budgets* for featurizer noise and propagates it to the headline (sd 0.0010). A
longitudinal version (P10) is **incremental**.

---

## 7. Exoplanet vetting and validation — *established; the text channel is absent*

| work | relevance |
| :--- | :--- |
| ExoMiner — Valizadegan et al. 2022, *ApJ* ([arXiv:2111.10009](https://arxiv.org/abs/2111.10009)) | Kepler vetting CNN. 301 validated planets |
| **ExoMiner++ on TESS** — ([arXiv:2502.09790](https://arxiv.org/abs/2502.09790); [AJ](https://iopscience.iop.org/article/10.3847/1538-3881/ae03a4)) | A 2-min TESS vetting catalog: 7,330 PCs matching 1,868 TOIs, with scores. It learns from TESS labels (the abstract refers to their being "noisier and more ambiguous") with transfer from Kepler, **so its scores on labelled TOIs are probably in-sample. Check its data section before using them** |
| ExoNet ([arXiv:2604.15560](https://arxiv.org/abs/2604.15560)) | Multimodal (light curves + stellar parameters), calibrated. Test AUC 0.9549 on TESS |
| LEO-Vetter ([arXiv:2509.10619](https://arxiv.org/pdf/2509.10619)); TESS Triple-9 ([arXiv:2303.00624](https://arxiv.org/abs/2303.00624)); NotPlaNET ([arXiv:2405.18278](https://arxiv.org/abs/2405.18278)) | Automated and uniform vetting catalogs |
| TRICERATOPS — Giacalone et al. 2021, *AJ* 161:24 ([paper](https://iopscience.iop.org/article/10.3847/1538-3881/abc6af)) | Bayesian FPP. **Accepts high-resolution imaging contrast curves as input** |
| Guerrero et al. 2021, *ApJS* 254:39 (the TOI catalog) | How TOIs and TFOPWG dispositions are produced |
| NASA Exoplanet Archive + ExoFOP data paper ([arXiv:2506.03299](https://arxiv.org/abs/2506.03299)); *Understanding ExoFOP and TFOP TOI dispositions* ([Zenodo 13117992](https://zenodo.org/records/13117992)) | The authoritative description of the label process. **Read before P5** |
| Lissauer et al. 2012, *ApJ* 750:112 | The multiplicity boost (E3's multiplicity column) |
| Rowe et al. 2014, *ApJ* 784:45; Morton et al. 2016, *ApJ* 822:86 | Statistical validation of most Kepler planets (E9's label-mechanism contrast) |
| Bryson et al. 2020, *AJ* 159:279 | Reliability-weighted occurrence rates (a use for calibrated P(planet), P1 extension) |

**What this makes ExoNotes.** Nothing in this list uses follow-up **text**, and the searches
found no other study that uses ExoFOP notes as predictive features (only this repository came
up). **"Does text add to a pixel-level vetter?" is a genuine opportunity** (P3), and it is now
cheap because ExoMiner++ publishes scores. Automating TRICERATOPS's imaging inputs from ExoFOP is
**incremental** (P4).

---

## 8. Language models on astronomical text — *established for retrieval and extraction; rare for prediction*

| work | what it does |
| :--- | :--- |
| astroBERT — Grezes et al. ([arXiv:2112.00590](https://arxiv.org/abs/2112.00590)) | A BERT trained on ADS, used for NER and retrieval |
| AstroLLaMA — Nguyen et al. 2023 ([arXiv:2309.06126](https://arxiv.org/abs/2309.06126)) | LLaMA-2 fine-tuned on astro-ph abstracts |
| pathfinder — Iyer et al. 2024, *ApJS* ([arXiv:2408.01556](https://arxiv.org/abs/2408.01556)) | Semantic literature search and RAG over ADS |
| **LLM analysis of GCN Circulars** — ([arXiv:2511.14858](https://arxiv.org/abs/2511.14858); [ApJS](https://iopscience.iop.org/article/10.3847/1538-4365/ae2e9c)) | 40,500 circulars. Topic classification by waveband and messenger; zero-shot GRB redshift extraction with Mistral |
| Language models for multimessenger astronomy — *Galaxies* 2023 ([doi](https://doi.org/10.3390/galaxies11030063)) | Zero- and few-shot extraction from ATels and GCNs |
| ALeRCE text-to-SQL ([A&A 2026](https://www.aanda.org/articles/aa/full_html/2026/07/aa58221-25/aa58221-25.html)); AstroReview ([arXiv:2512.24754](https://arxiv.org/abs/2512.24754)) | LLM interfaces to broker databases, and to telescope proposal review |
| HeyLIGO ([arXiv:1710.05350](https://arxiv.org/abs/1710.05350)) | TF-IDF and word2vec retrieval over LIGO, Virgo and GEO **electronic logbooks** |
| Accelerator eLogs: RAG over logbooks ([arXiv:2406.12881](https://arxiv.org/abs/2406.12881)); eLog status review ([arXiv:2506.12949](https://arxiv.org/abs/2506.12949)); GAIA assistant ([arXiv:2405.01359](https://arxiv.org/abs/2405.01359)) | LLMs over particle-accelerator logbooks (DESY, BESSY, Fermilab, SLAC, CERN …) |

**What this makes ExoNotes.** The **extraction** step is established for astronomical text. The
**evaluation design**, *"does the extracted text add predictive information beyond the structured
data, under leakage controls?"*, is what these works mostly do not do. Porting that design to
GCN Circulars, TNS AstroNotes or LIGO logbooks is a **genuine opportunity** (P9). Those corpora
have precise timestamps, which ExoFOP lacks.

---

## 9. Forecasting expert outcomes from text — *established in other sciences*

BrainBench — Luo et al. 2024, *Nature Human Behaviour*
([paper](https://www.nature.com/articles/s41562-024-02046-9)): LLMs beat neuroscientists at
predicting which of two abstracts reports the real result. **ExoNotes' "anticipate expert
consensus" framing belongs to this family.** P1 (prospective) is what would make ExoNotes a
forecasting study rather than a retrospective one.

---

## 10. Blinding and pre-registration in the physical sciences — *established, unevenly adopted*

Blind analysis is standard in particle physics (Klein & Roodman 2005, *Annu. Rev. Nucl. Part.
Sci.* 55:141) and in weak-lensing cosmology (e.g. Muir et al. 2020, *MNRAS* 494:4454). Formal
pre-registration of an ML analysis in observational astronomy is rare. The searches found no
astronomy-specific practice literature on it. **An RNAAS or PASP-style note, "what pre-registration
caught in an astronomy ML study", is incremental and useful**, and the WORKLOG supplies the
evidence (every defect and every falsified prior).

---

## 11. Quantum machine learning — *established negative expectation*

| work | relevance |
| :--- | :--- |
| Bowles, Ahmed & Schuld 2024 ([arXiv:2403.07059](https://arxiv.org/abs/2403.07059)) | 12 QML models on 160 datasets: **out-of-the-box classical models win**, and removing entanglement often does not hurt |
| Mücke et al. 2023, *Quantum Machine Intelligence* 5 (QUBO feature selection); follow-ups on quantum-annealing feature selection ([ESANN 2025](https://www.esann.org/sites/default/files/proceedings/2025/ES2025-162.pdf)) | Mutual-information QUBO for subset selection. Solvable classically at ExoNotes' scale |
| lambeq / QNLP — Kartsaklis et al. 2021 ([arXiv:2110.04236](https://arxiv.org/abs/2110.04236)) | Compositional quantum NLP. Demonstrated on toy-sized corpora |

**What this makes ExoNotes.** Running quantum classifiers on a 7-feature, 1,482-row table is
**established practice with an expected negative result**. Its only defensible value is as a
**rigorously controlled benchmark** (P11). Treat any claim of "quantum advantage" on this data as
a red flag.

---

## 12. Novelty ledger

| idea (where) | label | nearest prior work |
| :--- | :--- | :--- |
| LLM judgments as GBM features | Established | CAAFE, FeatLLM, TypeSafe cookbook |
| The same, pre-registered with a dilution floor, MDE and volume control, on astronomy text | Incremental → **genuine as methodology** | Kapoor & Narayanan (diagnosis); clinical NLP (design) |
| `Comments` label echo and `pscomppars` membership leak | **Genuine (a finding)**, already made | — (report to ExoFOP) |
| Prospective prediction registry for open TOIs (P1) | **Genuine opportunity** | BrainBench (forecasting); no exoplanet analogue found |
| Gold-labelled follow-up-note benchmark + featurizer-agnostic replication (P2) | **Genuine opportunity** (as a dataset) | GCN extraction work; PPI and DSL |
| Text on top of ExoMiner++ / TRICERATOPS (P3) | **Genuine opportunity** | `PLAN.md` §8.5; ExoMiner++ catalog |
| Note-derived constraints into TRICERATOPS (P4) | Incremental | TRICERATOPS contrast curves |
| Label-mechanism test, TESS vs Kepler (P5) | **Genuine opportunity** | Rowe 2014 / Morton 2016 (why Kepler labels differ) |
| Value of information per follow-up type (P6) | **Genuine opportunity** | Bayesian experimental design (general) |
| Text-vs-TIC stellar-classification contradictions (P7) | Incremental → genuine | `research/03` Project 4 (proposed, never run) |
| Leakage-audit toolkit for text features (P8) | Incremental (tool) | Model info sheets (Kapoor & Narayanan) |
| ExoNotes design on GCN, TNS or LIGO logbooks (P9) | **Genuine opportunity** | GCN LLM (extraction only); HeyLIGO (retrieval only) |
| Longitudinal drift monitor for science featurizers (P10) | Incremental | Chen et al.; Atil et al. |
| QML benchmark on the ExoNotes matrix (P11) | Established (negative expected) | Bowles et al. 2024 |
| TFOP collaboration network and consensus dynamics (P12) | Speculative → incremental | Science-of-science (general) |
| Lockboxed autoresearch question-proposer loop (P13) | Incremental → genuine | CAAFE, LLM-FE (no lockbox discipline) |
