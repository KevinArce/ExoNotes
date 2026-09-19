# Jev for Astrophysics: An Evidence-Based Assessment

> **Scope:** Critical re-examination of TypeSafe AI's Jev (`jev-1.13.0`) as a component of computational astrophysics workflows, with emphasis on exoplanet discovery and characterization.
> **Date:** 2026-09-19
> **Status:** Supersedes claims in `01_jev_fundamentals_and_ecosystem.md` and `02_astrophysics_and_scientific_discovery.md` where they conflict. Corrections are itemized in §1.4.
> **Method note:** No `TYPESAFE_API_KEY` was available in this environment and no astronomy libraries are installed, so **nothing here is backed by live API measurement**. Every quantitative claim is sourced to vendor documentation or to independent third-party evaluations, and labelled accordingly.

---

## 1. What Jev Actually Is (Verified)

### 1.1 Confirmed specifications

Verified against `docs.typesafe.ai` on 2026-09-19:

| Property | Verified value | Source |
| :--- | :--- | :--- |
| Model ID | `jev-1.13.0`; aliases `jev-latest`, `jev-preview` | `models.md` |
| Endpoint | `POST https://api.typesafe.ai/v1/systemone` | `api.md` |
| Input price | $0.042 / MTok ($42 per billion tokens) | `models.md` |
| Output price | Free | `models.md` |
| Total context | 64,000 tokens per request | `models.md` |
| State limit | 32,000 tokens for `state` + longest single question | `models.md` |
| Rate limit | 250,000 tokens/sec, 1,200 requests/min (dynamic) | `models.md` |
| Input modality | **Text only** — string, JSON object, or array of text. No image/audio/video | `models.md` |
| Latency | 70ms–500ms end-to-end | TypeSafe blog |
| Training | RLCD — "Reinforcement Learning for Calibrated Decisions" | TypeSafe blog |
| Decoding | "Parallel sampler… generates all outputs in a single query" | TypeSafe blog |
| Founder | Diogo Almeida, ex-OpenAI (instruction-following / InstructGPT lineage) | TypeSafe blog |

**Primitives** (`primitives.md`, `api.md`, `sdk/python/api/types/responses.md`):

- `Noul` → `{noul: float}`. Probability of yes. **No confidence field.**
- `Choice` → `{choice: str, probabilities: dict, confidence: float}`. Requires `criteria` map.
- `Score` → `{score: float, legend: dict, probabilities: dict[int,float], confidence: float}`. Requires ordered array of ≥2 level descriptions.

`SystemOneResponse` exposes `answers` (all answers keyed by question name) plus convenience accessors `nouls`, `choices`, `scores`, and `request_id`. *(The prior dossier's use of `response.answers["x"].choice` is valid.)*

### 1.2 The operating principle that matters for science

The architectural claim — parallel single-pass evaluation rather than autoregressive decoding — has one consequence that genuinely matters for scientific workloads, and it is not speed.

It is that **adding questions to a request is nearly free**. The official `parallel_questions` cookbook measured 13 questions (8 Noul, 2 Choice, 3 Score) against a ~54,000-character document: one batched call cost $0.000497 versus $0.006090 for 13 separate calls — **12.2× cheaper, 10.0× faster** — with *no measured quality degradation*, because "each question is scored on its own against the document."

For science this means the marginal cost of asking *one more diagnostic question* about an object approaches zero. That inverts the usual economics of hypothesis testing over a corpus: you can afford to ask twenty speculative questions of every object in a catalogue and throw away nineteen. §4 and §5 build on this; it is the single property that justifies Jev's presence in an astrophysics pipeline at all.

### 1.3 Documented limitations that are disqualifying for most astronomy

From `model-jaggedness/jev-1.13.md`, verbatim:

- **Math:** "Jev is not a calculator. We strongly recommend implementing any mathematical logic in code."
- **Counting:** "does not count reliably."
- **Numeric representation:** "cannot reliably judge whether two values are near each other."
- **Dates:** "reads dates as text, not as ordered quantities. Asking which of two dates comes first, how far apart they are… is unreliable."
- **Large state:** "Accuracy falls as the state grows with content unrelated to the decision."
- **Structural invariants:** no guarantee that complementary questions are mathematically consistent.
- **Generation:** "is not trained to generate text."
- **Adversarial content:** state is not treated as hostile by default.

Read together, these rule out most of what an astronomer does. Photometry, period search, orbital fitting, ephemeris propagation, significance testing, and unit conversion are all either arithmetic, ordering, or counting. **Jev cannot do any of them and should never be asked to.**

The numeric-proximity limitation is the sharpest constraint and the least obvious. A question of the form *"is this centroid offset small enough to rule out a background blend?"* asks the model to compare two numbers. That is a documented failure mode, and it is a Python `if` statement.

### 1.4 Corrections to the existing project dossier

The prior documents in this directory overstate the case in ways that would produce a scientifically unsound system. Itemized:

| # | Prior claim | Correction | Evidence |
| :-- | :--- | :--- | :--- |
| 1 | "ECE ≈ 0"; calibration gives "mathematically defensible acceptance thresholds" | **False out of distribution.** Independent study: in-domain ECE 0.024–0.032, but on a synthetic task the model cannot have seen, ECE = **0.107** against a noise floor of 0.024 (4.4× floor), refit temperature **2.74** | [jev-ood-calibration](https://github.com/scienthoon/jev-ood-calibration) |
| 2 | Policy gates on `confidence > 0.90` | **Category error.** Docs: *"Confidence is not probability. It measures distribution shape (certainty), not the likelihood that a specific answer is correct."* The OOD study explicitly *"advise[s] against thresholding on Jev's separate `confidence` field."* Gate on `probabilities[label]` instead | `confidence.md`; jev-ood-calibration |
| 3 | Miscalibration can be fixed with one global threshold | **No.** Error signs are *opposite by primitive*: Choice overconfident (T=3.29), Score overconfident (T=3.40), Noul **under**confident (T=0.66). *"Whether a fixed threshold is safe depends on the question type, not just on the task"* | jev-ood-calibration |
| 4 | Prototype asks Jev `"Is centroid_offset_arcsec sufficiently small (< 1.0 arcsec)?"` | Direct violation of documented numeric-proximity weakness. Must be computed in code | `model-jaggedness/jev-1.13.md` |
| 5 | "A single Jev request evaluates all 50 candidates in parallel" (RV-Followup-Prioritizer) | **Contradicted.** Packing 40 items into one state degraded Spearman ρ from **0.932 → 0.579** and pushed inversion rate past its gate (0.171 vs 0.15). Batch size 1 restored performance. Parallel *questions over one state* is supported; parallel *items in one state* is not | [jev-orderby-bench](https://github.com/yodablocks/jev-orderby-bench) |
| 6 | Rank targets by Jev probability | Probabilities are **quantized to two decimals**, producing large ties (53 rows at 0.99 in one run). `ORDER BY prob DESC LIMIT 20` silently returns an arbitrary subset | jev-orderby-bench |
| 7 | `TESS-RoboVetter` ranked as flagship project | **Weakest proposal in the set.** It puts a text-only model in direct competition with ExoMiner (recall-at-precision-0.99 = **0.936**), ExoMiner++ (7,330 TESS PCs), TRICERATOPS, LEO-Vetter, and TESS-ExoClass — all of which see the actual flux and pixel data Jev cannot ingest. See §2.2 | [ExoMiner](https://arxiv.org/pdf/2111.10009) |
| 8 | "Zero schema hallucination" implies reliability | The community *Start Here* guide warns directly: schema-valid output "doesn't guarantee correctness" | [awesome-jev](https://github.com/cobanov/awesome-jev) |
| 9 | Choice supports "up to 255 options" | Not documented anywhere in `api.md` or `primitives.md`. Treat as unverified | — |
| 10 | LSST delivers "10 million alerts per night" today | Rubin issued first alerts **2026-02-25**, currently ~**800,000/night**, ramping toward ~7M | [Rubin Observatory](https://rubinobservatory.org/news/first-alerts) |

Correction #1 deserves emphasis. **Astrophysics is maximally out-of-distribution for this model.** The one independent measurement of Jev on data it cannot have seen found calibration degrading by a factor of ~4.4 and overconfidence requiring a temperature of ~3 to correct. Any astronomy deployment must measure and refit its own calibration on labelled astronomical data before any probability is used in a decision. This is not a formality; it is the difference between a usable instrument and a random number generator with a decimal point.

### 1.5 Additional third-party findings

The [jev-behavior-study](https://github.com/RINNECODER/jev-behavior-study) (11,621 requests, Sept 16–17 2026) documented **position sensitivity**: an arithmetic task scored 95/108 when the answer appeared first in the state versus 62/108 when it appeared last, and "dispersed middle-position facts failed at larger sizes." For astronomy this means the ordering of fields in a state object is a free parameter that affects results and must be held fixed and version-controlled.

[jev-orderby-bench](https://github.com/yodablocks/jev-orderby-bench) also found that on a *harder* graded-relevance probe (Amazon ESCI), Jev "does not pass a gate it cleared comfortably on topic membership" — four of six conditions failed. **Coarse categorical distinctions hold up; fine graded ordinal distinctions do not.** This is directly relevant: "rank these 200 candidates by scientific priority" is a graded-relevance task of exactly the failing kind.

### 1.6 Existing scientific or data-intensive use

There is **no published example of Jev being used for a natural-science workload.** The ecosystem (per `awesome-jev`) is code agents, browser control, log triage, RAG reranking, trading bots, and games. The closest analogues are:

- **`autoresearch_feature_discovery`** (official cookbook) — the most scientifically interesting artifact in the entire ecosystem. See §4.1.
- **`duckdb-jev` / `pg-jev` / `jevql` / `jev-curate`** — semantic predicates inside SQL and over Parquet/JSONL. Directly reusable for catalogue work.
- **`citation_check`** — verifying claims against source text. Directly reusable for literature cross-checking.
- **`jev-tree`** — hierarchical Choice over large taxonomies. Relevant to classification schemes.

**Verdict on §1:** Jev is a fast, cheap, type-safe semantic judgment layer over *text*. It is not a scientific instrument, has never been used as one, and its calibration guarantees weaken substantially outside its training distribution. Everything below is constrained by those three facts.

---

## 2. Where Jev Fits in Astrophysics — and Where It Does Not

### 2.1 The decisive constraint: Jev cannot see a light curve

TESS and Kepler photometry is a numeric time series. Gaia astrometry is numeric. Radial velocities are numeric. Spectra are numeric. Images are pixels.

Jev accepts **text only**, has a 32,000-token state budget, cannot count, and cannot compare numbers for proximity. A 20,000-point light curve cannot be put into its state in any form it can reason over. Serializing flux values as text would consume the entire budget and land squarely in the documented "large state" and "counting" failure modes.

Therefore: **Jev's role in astronomy is never to look at the data.** It can only ever operate on *descriptions* of data produced by classical code, or on text that was text to begin with.

This single constraint eliminates the majority of the application list in the task brief. Transit detection, light-curve analysis, RV fitting, stellar classification from photometry, variability characterization, and simulation are all numeric-array problems. `astropy`, `lightkurve`, `wotan`, `batman`, `exoplanet`, `juliet`, `rebound`, and `scipy` do these correctly. There is no argument for Jev anywhere in that list.

### 2.2 Transit vetting: the trap

This is the most tempting application and, on the evidence, the worst.

The vetting problem looks like a classification problem over qualitative diagnostics — U-shape vs V-shape, odd/even depth agreement, centroid offset, secondary eclipse. That framing makes it look like a natural `Choice` question. But:

1. **The field already solved it with better tools.** ExoMiner's multi-branch CNN explicitly "mimics the process by which domain experts vet transit signals," ingesting centroid motion, odd-even flux asymmetry, and secondary-eclipse diagnostics *as time series and pixel data*, achieving R@P0.99 = 0.936 and validating 301 new Kepler planets. ExoMiner++ transferred this to TESS and catalogued 7,330 planet candidates. LEO-Vetter does automated flux- and pixel-level vetting. TESS-ExoClass provides an open detection filter and ranker.
2. **TRICERATOPS gives a physically grounded answer, not a semantic one.** It computes a Bayesian false-positive probability by marginalizing over transiting-planet, EB, nearby-EB, and secondary-transiting-planet scenarios using actual nearby-star contamination from the real field. Validation thresholds are FPP < 0.015 and NFPP < 10⁻³. That is a calibrated physical probability. A Jev `Noul` is a calibrated *linguistic* probability about a description — and, per §1.4, one whose calibration is unverified in this domain.
3. **Jev would receive a lossy summary of what those models see directly.** Every diagnostic must first be reduced to a scalar by classical code. Once you have the scalars, a gradient-boosted tree trained on the ~9,500 labelled KOIs plus the Kepler Certified False Positive Table will beat a zero-shot text model, and will be calibratable on held-out data.

**Conclusion:** do not build a Jev robovetter to compete with ExoMiner. If Jev appears anywhere near vetting, it should be *upstream as a cost gate* (deciding which candidates justify an expensive TRICERATOPS/MCMC run) or *downstream on the free text* (see §2.3) — never as the classifier.

### 2.3 Where Jev has a real, uncontested advantage

Jev wins exactly where the following three conditions hold simultaneously:

1. The input **is genuinely text**, not a serialized array.
2. **No labelled training set exists**, so a supervised model cannot be trained.
3. The judgment is **coarse and categorical**, not fine-grained ordinal or numeric.

Astronomy has more of this than it realizes, and it is systematically under-exploited because it has never been machine-readable in a useful way:

| Text corpus | Scale | Why no ML model exists | Jev fit |
| :--- | :--- | :--- | :--- |
| **ExoFOP-TESS `Comments` field** | ~7,000+ TOI rows, free-form observer notes | Unstructured, idiosyncratic, never labelled. `etta.download_toi()` returns it as a dataframe column | **Strong** |
| **TFOP observation notes & upload descriptions** | Tens of thousands of entries | Heterogeneous, multi-author, no schema | **Strong** |
| **ADS / arXiv astro-ph abstracts** | ~10⁵–10⁶ relevant | Retrieval exists; *semantic claim-level judgment* does not | **Strong** |
| **TESS DV report text** | One per TCE, ~10⁵ | PDF prose + diagnostic tables | **Moderate** (needs extraction) |
| **Catalogue provenance / reference strings** | Every row in `ps` | Bibcode + free-text method descriptions | **Strong** |
| **KOI / CFP disposition rationale text** | ~9,500 KOIs | Human-written justifications | **Strong** |

This is the honest answer to "where does Jev provide meaningful advantage in astrophysics": **in the natural-language connective tissue around the numerical science — the notes, comments, abstracts, dispositions, and provenance records that no one has ever been able to query semantically at scale.**

### 2.4 The allocation table (corrected)

```
┌─────────────────────────────────────────────┬────────────────────────────────────────────┐
│ NEVER JEV — use established code            │ CANDIDATE FOR JEV — text, unlabelled,      │
│                                             │ coarse, cheap to verify                     │
├─────────────────────────────────────────────┼────────────────────────────────────────────┤
│ ✗ BLS / TLS / Lomb-Scargle period search    │ ✓ Triaging free-text observer comments     │
│ ✗ Detrending (wotan, PDCSAP)                │ ✓ ADS abstract relevance to a target       │
│ ✗ Transit model fitting (batman, exoplanet) │ ✓ Claim-vs-catalogue contradiction checks  │
│ ✗ MCMC / nested sampling / BIC              │ ✓ Extracting which diagnostic a note cites │
│ ✗ FPP computation (TRICERATOPS)             │ ✓ Routing: does this deserve an MCMC run?  │
│ ✗ Any threshold comparison on a number      │ ✓ Coarse typing of heterogeneous metadata  │
│ ✗ Ephemeris / date / airmass arithmetic     │ ✓ Feature proposal→judgment loops (§4.1)   │
│ ✗ Centroid / difference-image analysis      │ ✓ De-duplicating cross-catalogue entities  │
│ ✗ N-body integration (rebound)              │ ✓ Flagging notes that contradict a flag    │
│ ✗ Ranking by fine-grained science priority  │ ✓ Binary "is this worth a human minute?"   │
└─────────────────────────────────────────────┴────────────────────────────────────────────┘
```

Note the last row on each side. **Binary triage: yes. Fine-grained priority ranking: no** — that is the ESCI graded-relevance failure mode from §1.5, compounded by two-decimal probability quantization.

---

## 3. Real Astronomical Data

### 3.1 Datasets assessed for Jev suitability

**NASA Exoplanet Archive (TAP)** — `https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=...&format=csv`
Tables: `ps` (planetary systems, one row per published parameter set), `pscomppars` (composite, one row per planet), `toi` (TESS candidates), `cumulative` (KOIs), `k2pandc`, `stellarhosts`. ADQL; CSV/JSON/VOTable output. Discoverable via `TAP_SCHEMA.tables`.
Scale: ~6,366 confirmed planets (2026); ~9,500 KOIs; ~7,000+ TOIs. Tens of MB — trivially fits on a laptop.
**Jev suitability: numeric columns NO, provenance/reference/comment columns YES.** The `ps` table's multi-row-per-planet structure (conflicting published values with different bibcodes) is exactly the kind of heterogeneous reconciliation problem where a semantic judgment over *reference text* adds something a join cannot.

**ExoFOP-TESS** — via `etta` (MIT-licensed Python wrapper over ExoFOP PHP endpoints). `etta.download_toi()` returns a 57-column dataframe **including the free-text `Comments` column** (e.g. "period is likely correct", "TOI-125 b").
**Jev suitability: HIGHEST of any dataset examined.** This is unlabelled natural-language annotation attached to structured rows, at a scale where manual reading is infeasible but semantic querying is valuable. No competing model exists.

**MAST (TESS / Kepler)** — `astroquery.mast`, `lightkurve`. FITS light curves (`TIME`, `PDCSAP_FLUX`, `MOM_CENTR1/2`, `QUALITY`), target pixel files, and **DV reports (PDF prose + diagnostic tables)**.
Scale: hundreds of TB of pixels; light curves ~0.5–5 MB each.
**Jev suitability: flux arrays NO. DV report *text* MODERATE** (requires PDF extraction first).

**Gaia DR3** — `astroquery.gaia`, TAP/ADQL. ~1.806 billion sources; 585M five-parameter + 800M six-parameter astrometric solutions; `ruwe`, `astrometric_excess_noise`; NSS catalogue of ~813,000 sources with orbital/SB1/SB2/eclipsing/acceleration solutions.
**Jev suitability: LOW for the catalogue itself.** RUWE > 1.4 as a binarity indicator is a numeric threshold — that is a `WHERE` clause, not an AI judgment. Gaia is essential *ground truth* for the projects below, but Jev should not touch its numbers.

**SDSS (SkyServer / CASJobs)**, **ESA archives**, **Rubin/LSST brokers (ALeRCE, Fink, Lasair, ANTARES, AMPEL, Babamul, Pitt-Google)** — Rubin began alerting 2026-02-25 at ~800k alerts/night, ramping toward ~7M.
**Jev suitability for alert streams: LOW-to-MODERATE and economically marginal.** At 7M alerts/night with a ~500-token state each, that is 3.5B tokens/night ≈ $147/night — affordable — but the *classification* is numeric/image-based (that is what the brokers' ML already does), and 7M/night exceeds the 1,200 req/min rate limit by ~4×. Jev could plausibly sit on a *broker's filtered output* (hundreds/night) applying semantic policy to text metadata. It cannot sit on the raw stream.

**NASA ADS** — `ads` Python package, token-authenticated, ~5,000 requests/day default.
**Jev suitability: HIGH.** Abstracts are text; relevance judgment is coarse and categorical; `citation_check` is a proven Jev pattern.

### 3.2 Preprocessing requirements, by pattern

| Pattern | Required preprocessing |
| :--- | :--- |
| Free-text triage (ExoFOP, ADS) | Minimal. Strip HTML, truncate to budget, fix field order |
| Catalogue reconciliation | Cross-match in code (`astropy.coordinates.match_coordinates_sky`), compute all deltas in code, present *only* the text/provenance to Jev |
| Diagnostic arbitration | Full classical pipeline first (detrend → BLS → fit → diagnostics), then **render scalars as qualitative statements in code**, never as raw numbers |
| Feature discovery | Assemble a text corpus + a numeric target column from catalogue joins |

The third row is the key engineering discipline of this entire report. **Code computes the number *and* the comparison; the state contains the verdict in words.** Instead of `{"centroid_offset_arcsec": 0.32}`, send `{"centroid": "offset consistent with target star at 0.4σ; no significant shift"}`. This moves the numeric comparison out of a documented failure mode and into a deterministic `if`, while leaving Jev the genuinely semantic task of weighing several such verdicts together.

---

## 4. Exoplanet Research Projects

Five proposals, ordered by how well they exploit Jev's actual advantages rather than by superficial appeal. Project 1 is the one worth building.

---

### Project 1: `ExoNotes` — Semantic Feature Discovery over Follow-Up Text

**Scientific question**
Do the free-text comments that astronomers write on TESS Objects of Interest contain predictive information about eventual disposition (confirmed planet / false positive / retired) that is *not* already present in the archive's numeric columns? If so, what are the latent discriminants that humans are encoding in prose but nobody has ever extracted?

**Why Jev?**
This is the direct astronomical transfer of the official `autoresearch_feature_discovery` cookbook, which is the only scientifically validated Jev workflow in existence. That cookbook converted free-form wine tasting notes into numeric features via a propose → answer → fit → feedback loop: a reasoning LLM proposes up to 18 semantic questions, Jev answers them across the whole corpus, probability distributions become numeric columns (a Score becomes *two* columns — expected level and its spread), CatBoost fits, feature importances and worst-predicted rows feed back into the next proposal round. Measured: RMSE 3.09 (mean baseline) → 2.47 (word counts) → 2.15 (direct score question) → **1.77** after five rounds and 38 questions.

Every ingredient transfers: free text in, numeric target out, no labelled training set, and the economics only work because marginal questions are nearly free (12.2× batching saving). Crucially, **Jev is not the predictor here — CatBoost is.** Jev is a *featurizer*, and every feature it produces is independently validated by whether it improves held-out error. That structure makes miscalibration (§1.4) largely harmless: a systematically overconfident probability is still a monotone, informative feature, and the downstream model learns its own mapping.

**Data**
- ExoFOP-TESS TOI table via `etta.download_toi()` — 57 columns including free-text `Comments`.
- NASA Exoplanet Archive `toi` table (TAP) for TFOPWG disposition labels (CP/KP/FP/FA/PC).
- Archive `cumulative` (KOI) + Kepler Certified False Positive Table (KSCI-19093) as an independent held-out corpus with rationale text.
- `pscomppars` for numeric covariates used as the *baseline* model.

**Workflow**
1. Pull TOI rows; join ExoFOP comments to archive dispositions on TOI ID. Freeze a snapshot with a checksum.
2. Split by *host star*, not by row, to prevent leakage between planets in the same system.
3. Fit baseline A: numeric columns only (period, depth, duration, Rp, Tmag, stellar params) → gradient-boosted classifier. Fit baseline B: TF-IDF over comments.
4. Run the autoresearch loop for 5 rounds. A reasoning model proposes Noul/Score questions over comment text ("does this note report a ground-based seeing-limited detection on target?", "does the note express doubt about the ephemeris?", "does it mention a nearby star as the eclipse source?"). Jev answers all questions for all rows in **one request per row, many questions per request**.
5. Encode probabilities as features; refit; feed importances and worst-predicted rows back to the proposer.
6. Evaluate on the held-out Kepler CFP corpus — a genuinely different mission, different text conventions, different era.

**Expected output**
- A reproducible feature table: ~40 semantic questions × ~7,000 TOIs, with probabilities and encoded columns, stored in DuckDB/Parquet.
- A ranked list of which *semantic* features carry information beyond the numeric baseline.
- ΔAUC / ΔBrier of (numeric + semantic) versus numeric-only, with bootstrap CIs.
- A human-readable list of the highest-importance questions — which is itself the scientific finding.

**Scientific value**
If semantic features from comments add signal beyond numeric columns, that is direct evidence that the follow-up community encodes decision-relevant information in prose that never reaches the structured catalogue — an actionable finding for archive schema design and for TFOP workflow. If they add nothing, that is a clean negative result and cheap to obtain. **Either outcome is publishable and useful.** That asymmetry is why this project ranks first.

**Technical complexity:** Medium
**Feasibility today:** **Buildable now, end to end.** `etta` + archive TAP + `typesafe-sdk` + CatBoost. Estimated ~$5–20 in Jev calls for the full 5-round loop over 7,000 rows. No blocked dependency.

---

### Project 2: `CatalogContradiction` — Literature-vs-Archive Consistency Auditing

**Scientific question**
Where do the stellar and planetary parameters asserted in the literature disagree with what the NASA Exoplanet Archive records, and which disagreements are substantive (genuinely conflicting measurements) versus artefactual (different conventions, aliases, or parameter definitions)?

**Why Jev?**
The numeric disagreement is trivially computed in code. The hard, irreducibly semantic part is deciding **whether two statements are talking about the same quantity** — is this paper's "stellar radius" the same as the archive's `st_rad`, or an isochrone-derived value under a different metallicity prior? Is this a measurement or a propagated assumption? That is entity-and-claim alignment over text, which maps onto two proven Jev cookbooks (`citation_check`, `entity_alignment`) and requires no arithmetic.

**Data**
- NASA Exoplanet Archive `ps` table (multi-row per planet, each row with a `reference` bibcode) — the disagreements are already in there by construction.
- NASA ADS API for abstracts and, where open-access, full text.
- Gaia DR3 for an independent astrometric check on host-star parameters.

**Workflow**
1. For each planet in `ps` with ≥2 published parameter sets, compute all pairwise numeric discrepancies **in code**, in units of the quoted uncertainties.
2. Keep only pairs exceeding a code-computed significance threshold. This is where most rows are eliminated — cheaply, deterministically.
3. For surviving pairs, fetch both abstracts via ADS.
4. Jev, one request per pair, many questions: `same_quantity` (Noul), `measurement_vs_assumed` (Choice), `method` (Choice: spectroscopic / isochrone / asteroseismic / photometric / SED / other), `supersedes_prior` (Noul), `flags_disagreement_explicitly` (Noul).
5. Code partitions into: benign (convention mismatch), superseded (later work explicitly supersedes), and **genuinely unresolved**.
6. Human review of the unresolved set only.

**Expected output**
A ranked table of unresolved parameter conflicts in the confirmed-planet catalogue, each with the discrepancy magnitude (from code), the semantic classification (from Jev), and links to both sources.

**Scientific value**
Planet radii and densities inherit stellar-parameter errors multiplicatively. A systematic audit of where the catalogue carries unresolved conflicts directly affects population-level results such as the radius valley. This is tedious, unglamorous, and currently done by hand one system at a time.

**Technical complexity:** Medium
**Feasibility today:** **Buildable now.** Main friction is ADS rate limits (~5,000/day) and open-access full-text coverage. Abstract-only is sufficient for an MVP.

---

### Project 3: `TriageGate` — Cost Routing for Expensive Validation

**Scientific question**
Given finite compute and telescope time, which of the ~7,000 open TOIs justify a full TRICERATOPS FPP computation, an MCMC fit, or a night of high-resolution spectroscopy?

**Why Jev?**
Not as a classifier — as a **cost gate**. TRICERATOPS requires querying nearby stars and marginalizing over scenarios; MCMC fits take CPU-hours; spectroscopy takes nights. A 100ms, $0.00005 judgment over a candidate's *textual dossier* (comments, prior observation notes, existing disposition rationale) that halves the number of expensive runs pays for itself by roughly seven orders of magnitude, **provided its false-negative rate is measured and the gate is tuned to be recall-heavy.**

The correct question is not "is this a planet?" — that is ExoMiner's and TRICERATOPS' job. It is "**does the existing text record already contain a decisive reason not to spend on this?**" — e.g. a comment noting a known nearby EB, a prior retirement, a duplicate of another TOI, a known systematic. That is text comprehension, and no model is trained on it.

**Data**
ExoFOP comments + observation notes; archive `toi` dispositions; prior TFOP upload descriptions.

**Workflow**
1. Assemble a textual dossier per candidate (code, deterministic field order).
2. Jev: `already_retired_in_text` (Noul), `duplicate_of_known_object` (Noul), `text_names_alternate_eclipse_source` (Noul), `text_reports_completed_followup` (Noul).
3. Code applies a recall-heavy policy: run the expensive analysis **unless** an exclusion fires above a threshold fitted on held-out labelled data.
4. Log every gated-out candidate for audit. Periodically run the expensive pipeline on a random sample of gated-out candidates to measure the false-negative rate directly.

**Expected output**
A routing decision per candidate plus a permanent audit log; a measured compute-saving fraction and a measured false-negative rate with confidence intervals.

**Scientific value**
Indirect but real: more expensive analyses run on candidates that deserve them. The random-sample audit makes the loss quantifiable rather than assumed — which is the property that makes this scientifically acceptable at all.

**Technical complexity:** Low
**Feasibility today:** **Buildable now.** The random-audit design is essential and non-optional.

---

### Project 4: `SystemNarrative` — Cross-Archive Anomaly Surfacing

**Scientific question**
Which planetary systems have *descriptive* records that are mutually inconsistent across archives — a system described as single-starred in one source and as a visual binary in another, a planet with a disputed period alias, a host with conflicting evolutionary-stage descriptions?

**Why Jev?**
Cross-matching by coordinates is a solved code problem. What is not solved is that the *same object* is described in incompatible prose across ExoFOP, the archive, SIMBAD object types, and the literature. Detecting "these two descriptions cannot both be true" is semantic contradiction detection over short text — coarse, categorical, and unlabelled.

**Data**
Archive `ps`/`stellarhosts`; ExoFOP comments; Gaia DR3 NSS catalogue (~813,000 sources, as *ground truth* for the binarity question); SIMBAD object types via `astroquery.simbad`.

**Workflow**
1. Cross-match in code; assemble per-object text bundles from all sources.
2. Jev: `descriptions_mutually_consistent` (Noul), `conflict_type` (Choice: multiplicity / evolutionary-stage / period-alias / identity / none), `conflict_is_substantive` (Noul).
3. **Cross-check every flagged multiplicity conflict against the Gaia NSS catalogue and RUWE in code.** Gaia adjudicates; Jev only surfaces candidates for adjudication.
4. Rank by whether Gaia confirms the conflict.

**Expected output**
A list of systems whose archival descriptions conflict, each annotated with whether independent Gaia astrometry supports one side.

**Scientific value**
Unrecognized stellar multiplicity dilutes transit depths and biases planet radii downward. This finds cases where *someone already knew* about a companion but the information never propagated into the parameter chain. Gaia-adjudicated, so the output is verifiable rather than suggestive.

**Technical complexity:** Medium
**Feasibility today:** **Buildable now**, though the yield is genuinely uncertain — this may surface mostly known cases. Worth a bounded pilot on a few hundred systems before committing.

---

### Project 5: `ObsQueue` — Follow-Up Shortlisting (deliberately narrow)

**Scientific question**
Which candidates should a ground-based spectrograph observe tonight?

**Why Jev? — Mostly, it should not.**
This is included as a **worked negative example**, because the prior dossier proposed it as a Jev ranking task and the evidence says that fails. Airmass, Moon separation, ephemeris uncertainty propagation, and exposure-time calculation are arithmetic and date reasoning — both documented failure modes. Ranking 50 candidates in one request is the exact configuration that degraded Spearman ρ from 0.932 to 0.579. Two-decimal probability quantization makes `ORDER BY` return arbitrary subsets of ties.

**The defensible residue:** `astroplan` computes observability and produces the ranked schedule. Jev answers one narrow binary question per target, one request each: *"does the free-text record indicate this target's follow-up is already complete or that it has been retired?"* — a text-comprehension veto, not a ranking.

**Data:** Archive `toi` ephemerides; ExoFOP notes; observatory site parameters.
**Workflow:** `astroplan` constraints → code-ranked schedule → Jev veto pass on text → final list.
**Expected output:** A nightly target list with a text-derived exclusion log.
**Scientific value:** Modest — avoids wasted nights on already-retired targets.
**Technical complexity:** Low
**Feasibility today:** Buildable, but **the scheduling must be `astroplan`, not Jev.**

---

## 5. Jev in a Computational Scientific Discovery System

The task brief proposes a ten-step discovery loop. Assessed honestly, step by step:

| # | Step | Who does it | Assessment |
| :-- | :--- | :--- | :--- |
| 1 | Continuously ingest observations | **Classical** (`astroquery`, `lightkurve`, broker clients) | Jev has no role. It cannot read FITS. |
| 2 | Detect interesting/anomalous phenomena | **Classical + specialized ML** (BLS/TLS, GP, isolation forests, ExoMiner) | Jev has no role in numeric anomaly detection. It *can* flag anomalies described in text. |
| 3 | Formulate possible explanations | **Reasoning LLM** proposes; **Jev** binds to typed hypothesis classes | Genuine Jev role, but as a *typing layer* over an LLM's generation — Jev cannot generate hypotheses, it is "not trained to generate text." |
| 4 | Retrieve relevant knowledge | **Vector/ADS retrieval** fetches; **Jev** reranks and verifies | **Strongest Jev role in the loop.** Proven pattern (`rerank_typesafe`, `citation_check`). |
| 5 | Run statistics/simulations | **Classical** (`emcee`, `dynesty`, `batman`, `rebound`) | Zero Jev role. |
| 6 | Compare competing hypotheses | **Classical** (BIC/AIC, Bayes factors, nested sampling evidence) | **Zero Jev role, contra the prior dossier.** Model comparison is a computed quantity. Asking Jev which residual "favours planet vs EB" substitutes a linguistic judgment for a likelihood ratio. Do not do this. |
| 7 | Determine discriminating observations | **Classical** (information gain, ETC) + **Jev** for text-based exclusions | Mostly classical. Expected-information-gain is computable. |
| 8 | Generate new research questions | **Reasoning LLM** proposes; **Jev** answers them at corpus scale; **classical ML** validates | **This is the autoresearch loop of §4.1 — the one genuinely novel capability.** |
| 9 | Maintain persistent context | **Database** (DuckDB/Postgres) | Jev is stateless. Persistence is the application's job entirely. The prior dossier's framing of Jev as providing "persistent scientific context" is wrong — it has no memory between calls. |
| 10 | Produce a reviewable research trail | **Database + templating**; **Jev** for typed tags | Jev cannot write the report. It can populate typed fields in one. |

**Honest summary:** of ten steps, Jev has a *primary* role in exactly one (step 4, retrieval judgment), a *co-starring* role in two (steps 3 and 8, always paired with a generative model and a validator), and no role at all in six. Step 9 is a category error in the original framing.

This is not a "System One discovery engine." It is a conventional scientific pipeline with a fast semantic judgment layer bolted onto its text-handling seams. That is a modest but real contribution — and describing it accurately is what makes it buildable.

### 5.1 The one architecture worth building

```
                  ┌──────────────────────────────────────────┐
                  │  REASONING LLM (Claude/GPT)              │
                  │  proposes candidate semantic questions    │
                  │  reads: worst-predicted rows + importances│
                  └───────────────┬──────────────────────────┘
                                  │  N questions
                                  ▼
 ┌─────────────┐   text    ┌──────────────┐  probabilities  ┌──────────────────┐
 │ TEXT CORPUS │──────────►│     JEV      │────────────────►│  FEATURE MATRIX  │
 │ ExoFOP      │  1 req    │  N questions │  Score → 2 cols │  (numeric)       │
 │ ADS         │  per row  │  1 forward   │  Noul  → 1 col  │                  │
 │ DV text     │           │  pass        │                 │                  │
 └─────────────┘           └──────────────┘                 └────────┬─────────┘
                                                                     │
 ┌─────────────┐                                                     ▼
 │ CATALOGUES  │  numeric covariates + labels          ┌──────────────────────────┐
 │ NExScI TAP  │──────────────────────────────────────►│ CLASSICAL ML / STATS     │
 │ Gaia DR3    │                                       │ CatBoost, CV, bootstrap  │
 └─────────────┘                                       │ ΔAUC vs numeric baseline │
                                                       └────────┬─────────────────┘
                                                                │ importances,
                                                                │ worst rows
                                                                └──► back to LLM

 EVERY Jev-derived feature must justify itself by improving held-out error,
 or it is dropped. Miscalibration is absorbed by the downstream model.
```

The property that makes this architecture scientifically defensible: **Jev's output is never a conclusion.** It is a feature, and features are falsified by cross-validation. The §1.4 calibration problem — fatal if you threshold on a Jev probability to decide a planet is real — is largely neutralized when the probability is one column among sixty feeding a model that is itself evaluated on held-out data.

---

## 6. Concrete Prototype: `ExoNotes`

### 6.1 Architecture

```
  ExoFOP-TESS (etta)          NASA Exoplanet Archive TAP
  Comments, obs notes         toi / pscomppars / cumulative
          │                              │
          └──────────┬───────────────────┘
                     ▼
       ┌─────────────────────────────┐
       │ INGEST (Python)             │   snapshot + SHA256 checksum
       │ join on TOI/TIC             │   host-star grouping for splits
       │ deterministic field order   │   → DuckDB
       └──────────┬──────────────────┘
                  │
      ┌───────────┴────────────┐
      ▼                        ▼
 ┌──────────────┐      ┌────────────────────────────┐
 │ BASELINE A   │      │ AUTORESEARCH LOOP (5 rounds)│
 │ numeric only │      │  LLM proposes ≤18 questions │
 │ BASELINE B   │      │  Jev answers (1 req/row)    │
 │ TF-IDF text  │      │  encode → CatBoost → refit  │
 └──────┬───────┘      └────────────┬───────────────┘
        │                           │
        └───────────┬───────────────┘
                    ▼
         ┌──────────────────────────┐
         │ EVALUATION               │
         │ group-split CV (by host) │
         │ ΔAUC, ΔBrier, bootstrap  │
         │ held-out: Kepler CFP     │
         │ reliability diagrams     │
         └──────────┬───────────────┘
                    ▼
         ┌──────────────────────────┐
         │ DuckDB + Parquet + plots │
         │ every request/response   │
         │ cached by content hash   │
         └──────────────────────────┘
```

### 6.2 Jev's role — explicit boundaries

**Jev does:**
- Answer Noul and Score questions about free-text comments, one request per TOI, many questions per request.
- Return probability distributions that become numeric feature columns.
- Nothing else.

**Jev does not:**
- See any light curve, flux value, or pixel.
- Compute, compare, or threshold any number.
- Parse any date or compute any interval.
- Decide any disposition.
- Rank candidates.
- Produce any text that reaches a human.

Every numeric operation, including every threshold comparison, happens in Python. Where a numeric fact is needed for a semantic judgment, **code renders it as a qualitative phrase first**.

### 6.3 Complementary classical methods

- `astropy` / `astroquery` — coordinates, cross-matching, TAP queries.
- CatBoost or LightGBM — the actual predictor. Gradient boosting, not Jev.
- `sklearn` `GroupKFold` — splits by host star to prevent system-level leakage.
- `scipy.stats.bootstrap` — confidence intervals on ΔAUC.
- `sklearn.calibration.calibration_curve` + custom ECE — reliability diagrams for Jev's raw probabilities *and* the final model's.
- Baselines: mean, TF-IDF + logistic regression, numeric-only GBM. **No Jev feature is accepted unless it beats all three.**

### 6.4 Storage

- **DuckDB** single file — TOI snapshots, question definitions (versioned), raw Jev responses, encoded features, model runs, metrics.
- **Content-addressed response cache** — SHA256 of `(model, state, questions)` → response JSON. Makes reruns free and results exactly reproducible.
- **Parquet exports** for the feature matrix.
- Scale: ~7,000 rows × ~40 questions × ~200 bytes ≈ 60 MB raw. Trivial.
- Every run records `jev-1.13.0` as the model string and pins the question set version — model updates must invalidate the cache.

### 6.5 Visualization

- Reliability diagram for each Jev question against eventual disposition — **the single most important plot in the project**, because it directly measures the §1.4 OOD calibration question on astronomical data.
- Feature importance ranked by question, summed across encoding columns.
- ΔAUC per round with bootstrap CIs.
- Per-question probability histograms — to detect the two-decimal quantization and ties problem empirically.
- Confusion analysis on the worst-predicted TOIs, which feeds the proposer.

### 6.6 Evaluation methodology

1. **Group-split cross-validation by host star**, 5-fold, 3 repeats. Never split within a system.
2. **Temporal held-out split** — train on TOIs dispositioned before a cutoff date, test after. This is the realistic deployment condition.
3. **Cross-mission held-out** — evaluate on Kepler CFP rationale text. Different mission, different conventions, a genuine distribution shift test.
4. **Primary metric:** ΔAUC and ΔBrier of (numeric + semantic) over numeric-only, with bootstrap 95% CIs. A gain whose CI crosses zero is not a gain.
5. **Ablation:** drop all Jev features and refit; drop each question individually.
6. **Calibration audit:** ECE of each raw Jev probability against outcomes, with a permutation noise floor, reported per primitive type — because §1.4 showed Choice/Score and Noul miscalibrate in *opposite* directions.
7. **Stability audit:** re-run a 200-row sample with paraphrased question wording and with permuted state field order. The `jev-behavior-study` position-sensitivity finding makes this mandatory. Report Jaccard/rank agreement. **If paraphrasing materially changes features, the result is not scientific.**

### 6.7 Scientific validation

The claim under test is narrow and falsifiable: *free-text follow-up comments contain disposition-relevant information beyond the numeric catalogue columns.*

It is validated only if all of the following hold:
- ΔAUC over the numeric-only baseline is positive with a bootstrap CI excluding zero, **on the temporal held-out split**.
- The gain survives on the cross-mission Kepler corpus.
- The paraphrase/order-permutation stability audit shows agreement above a pre-registered threshold.
- Top-importance questions are inspectable and astrophysically sensible to a human reader.

It is **refuted** if the gain vanishes on temporal or cross-mission splits — which would mean the model learned annotation conventions rather than physics. That is a real and likely failure mode, and detecting it is the point of having three splits.

**Pre-register the thresholds before running.** Otherwise the loop's five rounds of feedback on model errors is an efficient machine for overfitting a dev set.

### 6.8 MVP scope (~1 week)

1. Ingest ExoFOP TOI + archive dispositions → DuckDB. Snapshot and checksum.
2. Numeric-only and TF-IDF baselines with group-split CV.
3. **One** hand-written round of ~12 Jev questions — no LLM proposer yet.
4. ΔAUC with bootstrap CI + reliability diagram per question.
5. Go/no-go: if round one shows no gain over baselines, stop. The cookbook found most of the gain arrives in round one (1.87 of the eventual 1.77); rounds 2–5 contributed 0.10. **If there is no signal in round one, five more rounds will not create it.**

### 6.9 Future extensions

- Add the LLM proposer loop (rounds 2–5) if and only if the MVP clears its gate.
- Extend the corpus to ADS abstracts per host star.
- Extend to DV report text (needs PDF extraction).
- Feed validated semantic features into ExoMiner-style models as auxiliary inputs — the genuinely interesting long-term question is whether text features add anything *on top of* a pixel-level CNN.
- Apply the identical loop to a different target variable: not disposition, but *time-to-disposition*, which would identify what makes a candidate slow to resolve.

---

## 7. Thinking Like an Astrophysicist: The Four-Way Distinction

The task brief asks for a clean separation. Here it is.

**Established astrophysical techniques** — mature, physics-grounded, should never be replaced:
BLS/TLS period search; wotan/PDCSAP detrending; `batman`/`exoplanet` transit modelling; MCMC and nested sampling; difference-image centroid analysis; odd-even and secondary-eclipse tests; ghost diagnostics; statistical bootstrap false-alarm estimation; TRICERATOPS/VESPA Bayesian FPP (with Morton et al. 2023 recommending migration from VESPA to TRICERATOPS); Gaia RUWE and NSS solutions for binarity; `astroplan` scheduling; `rebound` N-body integration.

**Existing machine-learning approaches** — already strong, already deployed, Jev does not compete:
ExoMiner (R@P0.99 = 0.936, 301 validated Kepler planets); ExoMiner++ (7,330 TESS PCs via transfer learning); AstroNet; ExoNet (multimodal, phase-folded curves + stellar params + attention fusion); WATSON-Net; LEO-Vetter; TESS-ExoClass; broker ML at ALeRCE/Fink/Lasair. **All of these see the actual data. Jev cannot.**

**Potential applications of Jev** — defensible, buildable, with the boundaries of §2.3:
Semantic featurization of follow-up comment text (§4.1); literature-vs-archive claim consistency auditing (§4.2); recall-heavy cost gating with measured false-negative rates (§4.3); cross-archive descriptive contradiction surfacing with Gaia adjudication (§4.4); ADS abstract relevance reranking; text-based vetoes in scheduling (§4.5).

**Highly experimental** — interesting, unproven, do not build yet:
Jev as a typing layer over LLM-generated hypotheses (step 3 of §5); continuous monitoring daemons over broker output; any use of Jev probabilities directly in a scientific inference chain rather than as features; using Score for fine-grained scientific priority ranking (evidence says this fails).

### 7.1 Against the brief's own criteria

The brief asks where Jev enables workflows that are difficult manually, too complex to coordinate, too dynamic for batch pipelines, benefit from persistent state, find overlooked correlations, or help explore large archives. Scored honestly:

| Criterion | Verdict |
| :--- | :--- |
| Difficult to perform manually | **Yes, genuinely.** Reading 7,000 free-text comments and extracting 40 consistent judgments from each is ~280,000 human judgments. This is the real win. |
| Too computationally complex to coordinate | **No.** Coordination is an orchestration problem, solved by Airflow/Prefect/Snakemake. Jev adds nothing. |
| Too dynamic for batch pipelines | **Weak.** Astronomy is overwhelmingly batch. Rubin alerting is genuinely streaming, but its classification is numeric/image-based and 7M/night exceeds Jev's rate limit ~4×. |
| Benefits from persistent state | **No — Jev is stateless.** Persistence belongs to the database. This criterion is a misconception about the model. |
| Discovers overlooked correlations | **Yes, with a caveat.** The autoresearch loop genuinely surfaces non-obvious features — but *only over text*, and only validated by a downstream model. |
| Explores large archives | **Partially.** Excellent over the *text* columns of large archives. Useless over the numeric ones, which is most of them. |

Two of six are real. That is a narrower result than the brief anticipates, and it is the honest one.

---

# Most Promising Astrophysics Opportunities

Ranked by expected scientific return per unit of engineering risk.

### 1. Semantic featurization of astronomical free text — `ExoNotes` (§4.1, §6)

**Why this one deserves experimentation above all others.** It is the only proposal where Jev does something no existing tool does, on data no existing model is trained on, inside an architecture that makes its known weaknesses harmless.

ExoFOP's `Comments` column is a genuinely unexploited scientific corpus: thousands of expert annotations, written by the people closest to each candidate, machine-inaccessible until now because extracting consistent structure from free prose at scale required either an army of readers or a model too slow and expensive to run 280,000 times. Jev's 12.2× batching economics and 70–500ms latency make it affordable for the first time.

Critically, the workflow is **already validated in a different domain with measured results** (RMSE 3.09 → 1.77), and its structure — Jev as featurizer, gradient boosting as predictor, cross-validation as arbiter — means every Jev output is falsified or accepted by held-out error rather than trusted. The §1.4 out-of-distribution calibration problem, which is disqualifying for direct decision-making, is absorbed.

And it has a **clean negative result**. If text adds nothing beyond the numeric catalogue, that answers a real question about archive design cheaply, in about a week, for under $20.

### 2. Literature-vs-archive claim auditing — `CatalogContradiction` (§4.2)

Stellar parameter errors propagate multiplicatively into planet radii and densities, and thence into population-level results like the radius valley. The archive's `ps` table already contains the conflicts by construction — multiple published parameter sets per planet, with different bibcodes. What has never been feasible is deciding *at scale* whether a numeric disagreement is substantive or a convention artefact, because that requires reading both papers.

This maps precisely onto two proven Jev patterns (`citation_check`, `entity_alignment`), requires no arithmetic from the model (code computes every discrepancy first and eliminates most pairs before Jev sees anything), and produces output that a human can verify one row at a time.

### 3. Recall-heavy cost gating with measured loss — `TriageGate` (§4.3)

The least glamorous and the most likely to be adopted. A seven-order-of-magnitude cost ratio between a Jev call and an MCMC run means even a mediocre gate pays for itself, *provided* the false-negative rate is measured rather than assumed.

The design feature that makes this scientifically acceptable is the **random-sample audit**: periodically running the expensive pipeline on candidates the gate rejected, which converts an unknown risk into a measured number with a confidence interval. Any Jev deployment in a scientific pipeline should carry this property, and this project exists partly to demonstrate the pattern.

### 4. ADS abstract triage as infrastructure (component of §4.2, §4.4)

Not a standalone project but a reusable component. Reranking and relevance-judging retrieved abstracts is the single Jev capability with the strongest published evidence behind it and the clearest role in §5's step 4. Build it once as a library; every other project uses it.

### What I would not fund

A Jev transit vetter (§2.2). The field has ExoMiner, ExoMiner++, ExoNet, WATSON-Net, LEO-Vetter, TESS-ExoClass, and TRICERATOPS — all operating on data Jev physically cannot ingest. A text-only model receiving a lossy scalar summary will lose, and a gradient-boosted tree on the same scalars, trained on ~9,500 labelled KOIs, will beat it while being calibratable. The prior dossier ranked this first; the evidence puts it last.

---

# Verdict

> **Could Jev become a useful component of a new generation of computational astrophysics tools that continuously explore astronomical data and help researchers discover interesting exoplanets, anomalies, relationships, or scientific hypotheses?**

**A qualified yes, but for almost none of the reasons the question implies — and the qualifications are severe enough to change what gets built.**

**Not as an analyzer of astronomical data.** Jev is text-only, cannot count, cannot compare numbers for proximity, and cannot read a date as an ordered quantity. Light curves, spectra, astrometry, images, and time series are closed to it. The established numerical stack is correct and should not be touched, and where machine learning has already been applied — ExoMiner and its successors — those models see data Jev cannot and outperform anything Jev could offer.

**Not as a source of calibrated scientific probabilities.** The one independent test on data the model could not have seen found calibration degrading ~4.4× above the noise floor, with overconfidence requiring a temperature near 3 — and with Choice/Score and Noul miscalibrating in opposite directions, so no single correction works. Astronomy is further out of distribution than that test's synthetic tickets. A Jev probability is not a false-positive probability and must never be reported as one.

**Not as a persistent reasoner.** Jev is stateless. Persistence, provenance, and the research trail belong entirely to the database and application code.

**Yes, as a semantic featurizer over the text that astronomy has always had and never been able to query.** ExoFOP comments, TFOP notes, disposition rationales, catalogue provenance strings, ADS abstracts — hundreds of thousands of expert judgments encoded in prose, structurally invisible to every numerical pipeline ever built. The combination of near-free marginal questions, 70–500ms latency, and typed output makes systematic extraction from this corpus economically feasible for the first time, and the `autoresearch_feature_discovery` result demonstrates the pattern works well enough to beat strong baselines in a domain where it was actually measured.

The decisive architectural point is this: **Jev's output must be a feature, never a conclusion.** Inside a propose → answer → fit → validate loop, where every semantic judgment is falsified or accepted by held-out error, Jev's miscalibration and brittleness become tolerable engineering noise. Used directly — thresholding a Noul to decide a planet is real — the same weaknesses are disqualifying. The difference between a useful instrument and a liability is entirely architectural, not a property of the model.

So the realistic version of the ambition is smaller and more defensible than "a new generation of computational astrophysics tools." It is: **a semantic bridge between astronomy's numerical pipelines and its textual record.** That bridge does not currently exist, it would be genuinely new, it is buildable in about a week for under $20, and it fails cheaply and informatively if the hypothesis is wrong.

That is worth building. The transit vetter is not.

---

## Sources

**TypeSafe (vendor, verified 2026-09-19):** [models](https://docs.typesafe.ai/models.md) · [system-one](https://docs.typesafe.ai/concepts/system-one.md) · [jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md) · [HTTP API](https://docs.typesafe.ai/api.md) · [confidence](https://docs.typesafe.ai/confidence.md) · [Python SDK](https://docs.typesafe.ai/sdk/python.md) · [responses](https://docs.typesafe.ai/sdk/python/api/types/responses.md) · [state](https://docs.typesafe.ai/concepts/state.md) · [autoresearch feature discovery](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery.md) · [parallel questions](https://docs.typesafe.ai/cookbooks/parallel_questions.md) · [launch blog](https://typesafe.ai/blog/introducing-system-one-models-and-jev)

**Independent evaluations:** [jev-ood-calibration](https://github.com/scienthoon/jev-ood-calibration) · [jev-orderby-bench](https://github.com/yodablocks/jev-orderby-bench) · [jev-behavior-study](https://github.com/RINNECODER/jev-behavior-study) · [jev-benchmarks](https://github.com/AbdelStark/jev-benchmarks) · [awesome-jev](https://github.com/cobanov/awesome-jev) · [Latent Space coverage](https://www.latent.space/p/ainews-jev-a-system-one-model-that)

**Astronomy:** [ExoMiner](https://arxiv.org/pdf/2111.10009) · [ExoNet](https://arxiv.org/abs/2604.15560) · [WATSON-Net](https://arxiv.org/pdf/2511.08768) · [LEO-Vetter](https://arxiv.org/pdf/2509.10619) · [TRICERATOPS](https://iopscience.iop.org/article/10.3847/1538-3881/abc6af) · [TESS-ExoClass](https://github.com/christopherburke/TESS-ExoClass) · [NASA Exoplanet Archive TAP](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html) · [Kepler CFP Table](https://exoplanetarchive.ipac.caltech.edu/docs/KSCI-19093-003.pdf) · [etta / ExoFOP](https://etta.readthedocs.io/en/latest/index.html) · [Rubin first alerts](https://rubinobservatory.org/news/first-alerts) · [Gaia DR3](https://gaia.aip.de/cms/data/gdr3/) · [ADS API](https://ads.readthedocs.io/) · [LLM instability in scientific decision-making](https://arxiv.org/pdf/2603.15840)
