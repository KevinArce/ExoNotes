# ExoNotes — MVP Build Plan

> **Handoff document.** Written to be picked up cold by a fresh Claude Code session with no prior
> context. Everything needed to build the MVP is in this file or in `research/`.
>
> **If `WORKLOG.md` exists, read it first** and resume per §0.5. Do not restart work that is
> already logged as `DONE`.
>
> **Read `research/03_jev_astrophysics_evidence_based_assessment.md` before writing code**, then
> **`research/04_first_live_measurements.md`** — a live smoke test on 2026-09-19 found that
> **3 of 7 draft questions were defective**. §5 below already incorporates the fixes.
> Documents `01_` and `02_` in that directory contain superseded claims — §1.4 of document 03
> itemizes ten corrections. Do not build from 01 or 02.

---

## 0. One-paragraph brief

ExoNotes tests a single falsifiable scientific claim: **the free-text comments astronomers write
on TESS Objects of Interest contain disposition-relevant information that is not already present
in the numeric catalogue columns.** We test it by using Jev (TypeSafe AI's System One model) to
convert its free-text comment fields into numeric semantic features, then measuring whether
those features improve held-out prediction of TFOPWG disposition over a numeric-only baseline.
**Measured corpus (2026-09-19): 2,721 labelled rows across 2,573 host stars**, not the ~7,000
this plan originally assumed.
Jev is the *featurizer*. Gradient boosting is the *predictor*. Cross-validation is the arbiter.

**If the MVP shows no gain over baselines, stop and write up the negative result.** That outcome
is cheap, fast, and genuinely informative about archive design. Do not extend the loop hoping
signal appears.

---

## 0.5 Work logging and resumption protocol — **applies to every session**

Sessions end unexpectedly: context exhaustion, network failure, a crashed tool, a closed laptop.
This project must survive that without losing work or repeating paid API calls. The mechanism is
an append-only journal at **`WORKLOG.md`** in the project root.

### The rule

**Narrate every step you take in your visible output, and persist it to `WORKLOG.md` as you go.**
Not at the end of the session — as each step happens. A log written at the end is exactly the log
you do not have when the session dies.

### Entry format

Write a `STARTED` entry **before** an action, and a matching `DONE` / `FAILED` / `BLOCKED` entry
**after** it. Two entries per step. Append only.

```markdown
## [2026-09-19T16:45Z] STEP 1.3 — STARTED
**Doing:** TAP query for `toi` dispositions → DuckDB table `toi_disposition`
**Command:** `python scripts/01_ingest.py --stage disposition`
**Idempotent:** yes — safe to re-run from scratch
---
## [2026-09-19T16:47Z] STEP 1.3 — DONE
**Result:** 7,412 rows. 4,881 labelled (CP/KP=1,203; FP/FA=3,678). 2,531 excluded (PC/APC).
**Artifacts:** `data/exonotes.duckdb::toi_disposition` (sha256 a3f9…)
**Jev spend this step:** $0.00 · **running total:** $0.0002
**Next:** STEP 1.4 — join ExoFOP comments on TOI ID
---
```

### Non-negotiables

1. **`STARTED` before, outcome after.** An orphan `STARTED` with no matching outcome is the
   interruption marker — it is how the next session knows exactly where things stopped.
2. **Append only. Never edit or delete a past entry.** Corrections go in a *new* entry that says
   what was wrong. The log is a record, not a document.
3. **Always state `Idempotent: yes/no`** on a `STARTED` entry, and if no, say what to check before
   re-running. This is what makes resumption safe.
4. **Record every deviation from `PLAN.md`** as its own entry, with the reason. If the plan turns
   out to be wrong, the log is where that is discovered.
5. **Track cumulative Jev spend** on every entry that makes API calls. Cost is a gate (§6 Step 3);
   an unnoticed 10× overrun means something is misconfigured.
6. **Log failures in full** — the error, not a summary of it. A `FAILED` entry with the actual
   traceback is worth more than a successful one.
7. **Mark session boundaries** with a `SESSION START` / `SESSION END` entry naming the model and
   date.
8. **Never log secrets.** No API keys, no `.env` contents, no `Authorization` headers. If a command
   would echo one, redact before writing.

### Resumption procedure — the first thing any session does

1. Read `WORKLOG.md` (the tail is enough; the file is append-only so the end is current).
2. Find the last entry.
   - Ends in `DONE` → start the step named in its `Next:` field.
   - Ends in `STARTED` with no outcome → **that step was interrupted.** Read its `Idempotent:`
     field. If yes, re-run it. If no, inspect the named artifacts first, then decide.
   - Ends in `FAILED` / `BLOCKED` → read the recorded error and address it before continuing.
3. Append a `SESSION START` entry and a `RESUMED` entry naming the step being picked up.
4. Continue.

### Why this works here specifically

Jev responses are cached content-addressed on
`sha256(model + question_set_version + state + questions)` (§6 Step 3). **Re-running an
interrupted judging step costs nothing and returns byte-identical results** — cache hits skip the
API entirely. Combined with idempotent scripts, resumption is cheap by construction. Preserve that
property: every script in `scripts/` must be safe to re-run from scratch.

---

## 1. Non-negotiable guardrails

These come from verified documentation and independent evaluation. Violating them produces a
system that looks fine and is scientifically worthless. Full sourcing in `research/03_*.md` §1.

### About Jev itself

| Rule | Why |
| :--- | :--- |
| **Jev never sees a number it must compare.** Code computes the value *and* the comparison, then puts a qualitative phrase in the state. | Docs: Jev "cannot reliably judge whether two values are near each other." |
| **Jev never counts anything.** | Docs: "does not count reliably." |
| **Jev never parses or orders a date.** | Docs: "reads dates as text, not as ordered quantities." |
| **Never threshold on `confidence`.** Use `probabilities[label]` or the `noul` value. | `confidence` is a distribution-shape statistic, not P(answer correct). An independent study explicitly advises against thresholding on it. |
| **One request per row. Many questions per request.** Never pack multiple TOIs into one state. | Packing 40 items into one state dropped Spearman ρ from 0.932 → 0.579 in independent testing. Many questions over *one* state is the supported pattern (12.2× cheaper, no measured quality loss). |
| **Field order in the state object is fixed and version-controlled.** | Documented position sensitivity: an arithmetic task scored 95/108 when the answer appeared first vs 62/108 when last. |
| **Jev output is a feature, never a conclusion.** | Jev's calibration degrades ~4.4× out of distribution (ECE 0.107 vs 0.024 floor, refit T=2.74), and Choice/Score vs Noul miscalibrate in *opposite* directions. As a feature feeding a validated model, this is tolerable. As a decision threshold, it is disqualifying. |
| Jev is **text-only** and **stateless**. | No FITS, no arrays, no images. No memory between calls — persistence is DuckDB's job. |

### About the science

- **Do not replace any established astrophysical algorithm with Jev.** No period search, no
  detrending, no transit fitting, no FPP computation, no ephemeris arithmetic. The MVP does not
  touch light curves at all.
- **Do not build a transit vetter.** That competes against ExoMiner (recall-at-precision-0.99 =
  0.936), ExoMiner++, LEO-Vetter and TRICERATOPS, all of which ingest flux and pixel data Jev
  physically cannot read. See `research/03_*.md` §2.2.

---

## 2. The primary validity threat — read this before designing anything

**ExoFOP comments may be edited *after* a disposition is assigned.** If an observer writes
"retired as NEB" into the Comments field after the TFOPWG marks the TOI a false positive, then a
question like *"does this note indicate the candidate was rejected?"* is not predicting the label
— it is reading the label back out of prose. The model would score beautifully and mean nothing.

This is the single most likely way for this project to produce a false positive result, and a
temporal split does **not** fix it, because the comment text snapshot is current regardless of
when the disposition was set.

### 2.0 This is no longer hypothetical — it was measured on 2026-09-19

Over the 2,725 labelled rows with comments:

| Marker in comment text | n | P(y=1 \| marker) |
| :--- | ---: | ---: |
| bare planet designation (`WASP-68 b`, `Kepler-718 b`) | 679 | **0.999** |
| contains `retir*` ("retired as NEB") | 488 | **0.006** |
| contains `TFOP FP` | 502 | **0.000** |
| contains `validat*` / `confirmed planet` / `published` | 21 | 0.905 |
| **any of the above** | **1,304 (47.9%)** | — |

**Nearly half the labelled corpus carries a near-deterministic label marker.** Positives are
frequently *nothing but a planet designation* — the entire comment reads `WASP-68 b`. A planet
has a name only because it was confirmed, so that string **is** the label.

Confirmed independently by baseline C (§6 Step 2): its strongest positive-pushing TF-IDF terms
are survey catalogue prefixes — `toi, wasp, k2, kepler, hat, hats, hd, kelt, ngts, gj, qatar,
corot, lhs` — and its strongest negative terms are `tfop, fp, eb, neb, retired, retired as`.
**Baseline C scores AUC 0.969 and that number is almost entirely leakage. Do not cite it as
evidence for the hypothesis.**

**Required handling — build this in from the start, not as an afterthought:**

1. ~~**Investigate first.**~~ **DONE 2026-09-19 — see §2.1 and §2.2 for the answer.**
2. **Split the question set into two tiers** (see §5): `TIER_PREDICTIVE` (observational content)
   and `TIER_LABEL_ECHO` (statements that may restate the disposition). **The planet-name channel
   above is why `references_other_object` was moved to the label-echo tier — see §5.**
3. **Report two numbers, always.** The headline result is ΔAUC using `TIER_PREDICTIVE` **only**.
   The full-set number is reported alongside as an upper bound, clearly labelled as
   leakage-contaminated.
4. **Gate G4 in §7 makes the predictive-tier gain the pass/fail criterion.** A gain that exists
   only in the full set is a negative result, not a positive one.
5. **Run the leakage-stripped arm (§7).** Regex-remove designation-only comments and
   `retired`/`TFOP FP` text and re-fit. Pre-register it as an arm, not a post-hoc check.

### 2.1 Comment timestamps — investigated 2026-09-19, answer: **no, not for `Comments`**

**Negative finding, recorded as required.** The `Comments` field has no field-level timestamp:

- ExoFOP's `Date TOI Alerted (UTC)`, `Date TOI Updated (UTC)`, `Date Modified` are **row-level**
  (`Date Modified` has 504 distinct values, 5,709 rows sharing one bulk stamp of
  `2025-07-31 12:59:22`). NEA `toi` adds `toi_created`, `rowupdate`, `release_date` — also
  row-level.
- **No `etta` endpoint is a revision log.** The eleven wrappers are `download_toi`,
  `download_nearbytarget`, `download_imaging`, `download_tag_imaging`, `download_spect`,
  `download_tag_spect`, `download_tseries`, `download_tag_tseries`, `download_obsnotes`,
  `download_user_tags`, `download_stellarcomp`.
- **There is no disposition-assignment timestamp either**, so even in principle the text cannot
  be aligned to "as it stood when the label was set."

**Consequence: for the TOI `Comments` corpus, no temporal control is possible.** The two-tier
question split is the *only* available mitigation, which raises the stakes on getting it right.

### 2.2 `download_obsnotes` — a timestamped alternative corpus the plan did not know about

Schema: `ID · TIC ID · Username · Groupname · TAG ID · Lastmod · notes`. Measured on 30 labelled
TICs (15 per class):

- **30 / 30 had ≥1 note.** Median 3 notes per TIC (mean 4.2, max 26).
- Median **2,384 characters** of text per TIC vs **30** in `Comments` — roughly **80× more text.**
- `Lastmod` spans 2009→2026 and is genuinely spread across years — real temporal information.
- Per-author (`Username`) and per-group (`Groupname`, e.g. `tfopwg`), so observer notes can be
  separated from the TFOP summary that carries the disposition.

**Three caveats that limit what this buys:**

1. `Lastmod` is **last-modified, not created**. A 2019 note edited in 2026 reads as 2026 and the
   2019 text is unrecoverable. A bulk-migration cluster at `2020-09-18 12:0x:xx` is a clear case.
2. **Note count is label-correlated** (median 5 for CP/KP vs 2 for FP/FA). Any note-volume
   feature is a leakage channel.
3. **70% of TICs carry HTML markup** inside `notes` and need stripping.

**Cost to acquire: 3.24 s/TIC measured → ~2.3 h sequential for 2,573 TICs.** One GET each,
parallelizable, no API cost.

**This is an open corpus-selection decision and belongs in `PREREGISTRATION.md`, decided by a
human.** It is a genuine trade: ~80× more text with partial temporal control, against 2.3 h of
scraping and a worse leakage profile in the `tfopwg` notes (they state `Master Disp:` outright).

---

## 3. Data sources

### 3.1 ExoFOP-TESS — the corpus (the thing being tested)

- Package: `etta` (MIT, `pip install etta`). Python wrapper over ExoFOP-TESS PHP endpoints.
- Call: `etta.download_toi()` → dataframe, **63 columns** (measured; an earlier draft said 57),
  **including the free-text `Comments` column** (real examples: "period is likely correct",
  "TOI-125 b").
- Also carries `Date TOI Alerted (UTC)`, `Date TOI Updated (UTC)`, `Date Modified` — all
  **row-level**, none of them a timestamp for the `Comments` field. See §2.1.
- No authentication known to be required for the TOI table; verify on first run.
- Scale (measured 2026-09-19): **8,148 rows**, 3.8 MB, ~23 s to download. No authentication
  required — confirmed, not assumed.
- **`etta` exposes ten other endpoints**, one of which matters: `download_obsnotes` (see §2.2).

### 3.2 NASA Exoplanet Archive — the labels and numeric covariates

- TAP endpoint: `https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=<ADQL>&format=csv`
- ADQL; spaces URL-encoded as `+`. Discover schema via `TAP_SCHEMA.tables` / `TAP_SCHEMA.columns`.
- Tables needed:
  - `toi` — TESS Project Candidates. Carries the TFOPWG disposition **and every numeric
    covariate the models use.** 90 columns. This is the only table in the feature path.
  - `pscomppars` — pulled for provenance only. **NEVER used as a feature source. See the box.**

> ### ⛔ `pscomppars` MUST NOT be joined into model input
>
> `pscomppars` is the composite-parameters table for **confirmed/published planets only**.
> Membership in it is very nearly the label. Measured 2026-09-19 over the 2,830 labelled rows:
>
> | | y=0 (FP/FA) | y=1 (CP/KP) |
> | :--- | ---: | ---: |
> | in `pscomppars` | 6 | 1,307 |
> | not in `pscomppars` | 1,404 | 113 |
>
> **P(y=1 | in) = 0.995 · P(y=1 | not in) = 0.074.**
>
> Any feature derived from it leaks the label through **missingness alone**. Worse, it would
> push baseline B to ~0.99 AUC and make **gate G2 unpassable**, so the project would report a
> false negative and stop. An earlier version of this plan specified `pscomppars` as the
> covariate source; that was **wrong** and `scripts/01_ingest.py` deliberately does not do it.
> The correct covariates were always in `toi`.
- Note: the archive's TOI list syncs from ExoFOP roughly weekly, so the two sources can drift.
  Snapshot both on the same day and record the date.

### 3.3 Label definition

Binary target from TFOPWG disposition:

| Disposition | Target |
| :--- | :--- |
| `CP` (confirmed planet), `KP` (known planet) | **1** |
| `FP` (false positive), `FA` (false alarm) | **0** |
| `PC` (planet candidate), `APC` (ambiguous), blank | **excluded** — unresolved, not a label |

**Measured 2026-09-19** (label source: NEA `toi.tfopwg_disp`):

| | count |
| :--- | ---: |
| CP 813 + KP 607 → **y=1** | **1,425** |
| FP 1,311 + FA 99 → **y=0** | **1,401** |
| labelled total | **2,826** |
| excluded (PC 4,819 + APC 485 + blank 14) | 5,318 |
| dropped: empty comment | 105 (3.7%) |
| **analysis set** (labelled ∧ non-empty comment) | **2,721** |
| unique TIC ID in analysis set | **2,573** |
| median comment length | **30 characters** |

**The corpus is balanced (50.3% positive)** — no stratification or reweighting needed, and AUC
is well behaved. Six labelled rows disagree between ExoFOP and NEA and are flagged in
`toi_snapshot.label_source_agrees`; four are FP→CP sign flips.

### 3.4 Out of MVP scope

Kepler CFP cross-mission validation, ADS abstracts, DV report text, and the LLM proposer loop are
all **future extensions**. Do not build them in the MVP.

---

## 4. Repository layout

```
ExoNotes/
├── PLAN.md                       # this file
├── README.md                     # short: what this is, how to run
├── PREREGISTRATION.md            # ← write BEFORE running anything (§7)
├── LICENSE                       # MIT (code) — see §11
├── CITATION.cff                  # how to cite this work
├── CONTRIBUTING.md               # how to reproduce and contribute
├── PROVENANCE.md                 # committed source checksums (data/ is gitignored) — §11
├── requirements.txt              # pinned, for reproducibility
├── pyproject.toml
├── .env.example                  # TYPESAFE_API_KEY=
├── .gitignore                    # data/, .env
├── research/                     # existing dossier — read 03 first
├── src/exonotes/
│   ├── __init__.py
│   ├── config.py                 # paths, model id, thresholds, seeds
│   ├── ingest.py                 # ExoFOP + TAP → DuckDB, with checksums
│   ├── questions.py              # VERSIONED question set, two tiers
│   ├── judge.py                  # Jev client + content-addressed cache
│   ├── features.py               # answers → numeric matrix
│   ├── baselines.py              # mean / TF-IDF / numeric-only GBM
│   ├── evaluate.py               # group CV, temporal split, bootstrap, ECE
│   └── plots.py                  # reliability diagrams, importances
├── scripts/
│   ├── 01_ingest.py
│   ├── 02_baselines.py
│   ├── 03_judge.py
│   ├── 04_evaluate.py
│   └── 05_report.py
├── data/                         # gitignored
│   ├── exonotes.duckdb
│   ├── cache/                    # content-addressed Jev responses
│   └── figures/
└── tests/
```

### Dependencies

```toml
# pyproject.toml [project] dependencies
"typesafe-sdk",      # Jev
"etta",              # ExoFOP-TESS access
"astropy",           # coordinates, table handling
"astroquery",        # TAP convenience (optional; raw HTTP also fine)
"duckdb",
"pandas", "pyarrow",
"scikit-learn",      # GroupKFold, TF-IDF, calibration_curve, metrics
"catboost",          # or lightgbm
"scipy",             # bootstrap
"matplotlib",
"python-dotenv",
```

**RESOLVED 2026-09-19 — the environment is Python 3.14, no fallback needed.** This plan
predicted CatBoost would lack 3.14 wheels; **that prediction was wrong.** Verified working set:

```
python 3.14.7 · catboost 1.2.10 · duckdb 1.5.5 · pandas 3.0.6
scikit-learn 1.9.1 · scipy 1.18.1 · etta 0.1.1
```

Reproduce with `uv venv --python 3.14 .venv && uv pip install -r requirements.txt`.
Note `pandas` resolves to **3.x**, where copy-on-write and the string dtype are defaults —
pandas-2 idioms may warn. Do not re-litigate the interpreter choice.

---

## 5. The question set (`src/exonotes/questions.py`)

**MVP uses `Noul` and `Score` only.** No `Choice`. This mirrors the validated
`autoresearch_feature_discovery` recipe (presence questions → Noul, intensity questions → Score)
and avoids one primitive's worth of calibration surface.

The set is a versioned constant. Bump `QUESTION_SET_VERSION` on any edit — it is part of the
cache key, so an edit must invalidate cached responses.

### TIER_PREDICTIVE — observational content (the headline result uses only these)

| ID | Type | Judgment |
| :--- | :--- | :--- |
| `reports_offset_eclipsing_binary` | Noul | Does the note report an eclipsing binary **at a position offset from the target** — nearby, background, NEB, contaminating star, or at a stated separation? **Answer no if an EB is proposed for the target star itself.** *(Revised and verified: 0.870 / 0.070 / 0.070 — see 04 §4.1. Replaces a dropped `names_alternate_eclipse_source` question, 04 §4.2.)* |
| `reports_stellar_companion_or_blend` | Noul | Does the note describe a stellar companion, blend, or contaminating source? |
| `mentions_spectroscopic_binary` | Noul | Does the note describe spectroscopic binary signatures (SB1/SB2, large RV variation)? |
| `reports_on_target_detection` | Noul | Does the note report a follow-up detection confirmed to be on the target star? |
| `asserts_ephemeris_problem` | Noul | Does the note assert a **specific problem** with the period or epoch — wrong, aliased, a harmonic/multiple, or needing revision? **Answer no if the text affirms the ephemeris, even hedged ("likely", "probably").** *(Revised and verified: 0.890 vs 0.050 — see 04 §4.1.)* |
| `mentions_instrumental_artifact` | Noul | Does the note attribute the signal to an instrumental or systematic artifact? |
| `describes_transit_morphology` | Noul | Does the note comment on the shape or depth behaviour of the event itself? |
| `author_certainty` | Score | 0: purely speculative · 1: tentative, hedged · 2: qualified with caveats · 3: confident · 4: stated as settled fact |
| `evidence_depth` | Score | 0: no observation described · 1: a single note with no data · 2: one follow-up observation referenced · 3: multiple observations referenced · 4: multiple independent facilities or techniques described |

### TIER_LABEL_ECHO — may restate the disposition (reported separately, never in the headline)

| ID | Type | Judgment |
| :--- | :--- | :--- |
| `indicates_retired_or_rejected` | Noul | Does the note state the candidate has been retired, rejected, or dismissed? |
| `indicates_followup_complete` | Noul | Does the note state that follow-up is finished or the case is closed? |
| `indicates_confirmed_planet` | Noul | Does the note state the candidate is a confirmed or published planet? |
| `references_other_object` | Noul | Does the note cross-reference another TOI, a known planet, or a duplicate designation? **⚠️ MOVED HERE FROM `TIER_PREDICTIVE` on 2026-09-19.** It captures the planet-name channel measured at §2.0: 679 comments are a bare designation and predict the label at **P=0.999**. Leaving it in the predictive tier would have produced a spectacular and entirely false positive result. |

> ### ⚠️ These questions were verified on the wrong text distribution
>
> The §5 question set was validated in `research/04` against **four hand-written comments of
> 100–200 characters**, multi-clause and information-rich. The **median real comment is 30
> characters** (p90 = 81). Verified behaviour on a rich paragraph says little about behaviour on
> the fragment `low SNR; potential multi`.
>
> **Step 2.5 must draw its cases from real comments in `analysis_set`, sampled across the actual
> length distribution — not hand-written ones.** This is the single most likely way for the
> question set to be silently wrong.

### Question-writing rules

- **Ask what the text *says*, never what it *implies*.** Multi-hop inference is a documented
  failure mode and was the first thing to break in live testing (04 §3.1). Extract facts with Jev;
  draw conclusions in Python.
- **If a question turns on one qualifier** (*nearby*, *on-target*), spell that qualifier out with
  concrete cues **and state the negative case explicitly** ("answer no if…"). A bare adjective gets
  ignored. Adding the negative case is what repaired both fixable questions (04 §4.1).
- **If a question needs inference, delete it rather than reword it** — provided another question
  captures the underlying fact. Two questions about one fact is worse than one that works (04 §4.2).
- Each question asks **one** narrow judgment. No conjunctions, no double negatives.
- `Score` levels describe **concrete situations** and stand on their own — never "low/medium/high".
- Instructions reference the state field by backticked path, e.g. `` `comment.text` ``.
- No question may require arithmetic, counting, date ordering, or numeric comparison.

---

## 6. Build order

Each step is independently runnable and writes its output to DuckDB. Do not skip ahead.

### Step 1 — `scripts/01_ingest.py` · ✅ **DONE 2026-09-19**

> Built and verified idempotent (re-run performs zero network I/O and reproduces identical
> SHA256s). Outputs `data/exonotes.duckdb` with tables `toi_snapshot`, `analysis_set`,
> `ingest_provenance`, `ingest_stats`. Results are in §3.3 and `WORKLOG.md` 23:26Z.
> **Deviation carried in: covariates come from `toi`, not `pscomppars` — see the box in §3.2.**

1. `etta.download_toi()` → raw ExoFOP dataframe. Save raw to `data/` with a SHA256 checksum and
   the retrieval timestamp.
2. TAP query the `toi` table for dispositions **and numeric covariates**. `pscomppars` is
   pulled for provenance only and **must not enter the feature path** (§3.2).
3. Join on TOI ID. Keep TIC ID — **it is the grouping key for all splits.**
4. Apply the label mapping from §3.3; drop unresolved.
5. Drop rows with empty/whitespace-only `Comments` — **and record how many.** If most comments are
   empty, the corpus is smaller than assumed and that changes the power calculation. Report it.
6. Investigate comment timestamps per §2.1 and record the finding in `PREREGISTRATION.md`.
7. Write `toi_snapshot` table to DuckDB with the checksum and date as columns.

**Report before continuing:** row count, class balance, non-empty comment count, median comment
length, and whether timestamps were found.

### Step 2 — `scripts/02_baselines.py` · ✅ **DONE 2026-09-19 · GATE G1 PASSED**

> Measured under S1 (GroupKFold(5) × 3 repeats on TIC ID, 2,721 rows / 2,573 groups):
>
> | model | AUC | Brier |
> | :--- | ---: | ---: |
> | C — TF-IDF | 0.9691 ± 0.0064 | 0.0703 |
> | **B — numeric CatBoost** | **0.9154 ± 0.0130** | **0.1136** |
> | A — prior | 0.5000 ± 0.0000 | 0.2501 |
>
> **G1 PASS** (B beats A on both metrics). Diagnostics: B's importance is spread across genuine
> physical quantities (`pl_rade` 16.2, `pl_orbper` 16.1, `st_logg` 15.5, …) and a
> missingness-indicators-only model scores just **0.5869**, so B is mostly real astrophysics.
> **C's 0.9691 is leakage** — see §2.0.
>
> **Leakage-stripped preview** (1,417 rows / 1,312 TIC): B **0.9037**, C **0.8965**.

Three baselines, all evaluated with the same splits as the final model (§7):

- **A — Prior:** predict the base rate. Establishes the floor.
- **B — Numeric only:** CatBoost on catalogue columns (period, depth, duration, planet radius,
  Tmag, stellar Teff/radius/logg). **This is the baseline that matters** — the claim is that text
  adds something *beyond* it.
- **C — TF-IDF:** logistic regression on comment text. Establishes that any gain is from *semantic*
  features, not just from the presence of words.

### Step 2.5 — question-design gate (**do not skip**)

Before spending anything on the full corpus, assemble ~20 cases covering, for **each** question:
its clear positive, its clear negative, and its **nearest confusable** (the case a sloppy question
would get wrong). Run them, inspect every answer by eye, and fix the questions that fail.

> **⚠️ CHANGED 2026-09-19 — draw the cases from REAL comments, not hand-written ones.**
> Sample them from `analysis_set` in DuckDB, stratified across the true length distribution
> (median 30 chars, p90 81), and include several of the terse fragments that dominate the
> corpus. The previous round used 100–200-char hand-written prose that is **longer and richer
> than the median real comment**, so it tested the questions on a distribution the corpus does
> not contain. Hand-written cases may supplement the real ones; they may not replace them.
>
> Start from this query:
> ```sql
> SELECT toi, tic_id, y, comment_len, comment FROM analysis_set
> WHERE comment_len BETWEEN 8 AND 40 ORDER BY random() LIMIT 30;
> ```

`scripts/00_smoke_test.py` is the working template — extend it. The 2026-09-19 run found **3 of 7
questions defective on four cases**; rewording repaired two, and the third was dropped as
redundant (04 §3–4). Budget two rounds: draft → test → revise → **re-test**. Cost is cents; the
alternative is a silently corrupted feature matrix.

### Step 3 — `scripts/03_judge.py`

1. Build the state per row. **Fixed key order, always:**
   ```python
   state = {
       "toi": str(row.toi),                     # identifier first
       "comment": row.comments.strip(),         # the material being judged
   }
   ```
   Keep it minimal. Documented failure mode: "accuracy falls as the state grows with content
   unrelated to the decision." Do **not** pad the state with numeric columns — they are the
   baseline's job, and Jev cannot use them anyway.
2. Cache key: `sha256(model_id + QUESTION_SET_VERSION + canonical_json(state) + canonical_json(questions))`.
   Cache hit → skip the call. This makes reruns free and results byte-reproducible.
3. One `system_one()` call per row, all questions in that one call.
4. Concurrency: `AsyncTypeSafeClient` with a bounded semaphore (start at 8). **Required, not
   optional** — measured latency on 2026-09-19 was 550–1520ms per call (above the advertised
   70–500ms; cold sequential calls, so not a careful benchmark). At ~1s sequential, 2,721 rows
   is ~45 minutes. Rate limit is 1,200 req/min; stay well under. SDK handles 429 retries with backoff.
5. Persist the **full raw response JSON** — every `probabilities` dict, not just the argmax. The
   distributions are the features.

**Cost estimate — measured, and revised down.** The 2026-09-19 smoke test used 603–645 input
tokens for a short comment + 7 questions. **The corpus is 2,721 rows, not 7,000** (§3.3), and
real comments are shorter than the smoke-test cases:

`2,721 × ~630 tok ≈ 1.7M input tokens ≈ **$0.072**` for 7 questions; the full 13-question set
roughly doubles it to **~$0.15**. Output is free.

**If a run is heading past ~$0.50, stop and check the state size — something is wrong.**

Note the question definitions outweigh the comment text ~14:1, so **cost scales with the question
set, not the corpus.** If projected cost exceeds a few dollars, something is wrong — check the
state size first.

### Step 4 — `scripts/04_evaluate.py`

**Encoding rules** (from the validated cookbook):

- `Noul` → **1 column**: the `noul` probability directly.
- `Score` → **2 columns**: expected level `E = Σ i·p_i`, and spread `sqrt(Σ p_i (i − E)²)`.
  The spread column is not decoration — it carries the model's uncertainty as a usable signal.

Then:
1. Fit model D = numeric + `TIER_PREDICTIVE` features.
2. Fit model E = numeric + all features (including `TIER_LABEL_ECHO`).
3. Evaluate D and E against baselines A/B/C under both split regimes (§7).
4. Compute ΔAUC and ΔBrier vs baseline B with bootstrap 95% CIs (`scipy.stats.bootstrap`,
   resampling **by host star**, not by row).
5. Per-question calibration audit: ECE of each raw Jev probability against the outcome, with a
   permutation noise floor. **Report Noul and Score separately** — they miscalibrate in opposite
   directions, so a pooled number hides the problem.
6. Stability audit (§7 G3).

### Step 5 — `scripts/05_report.py`

Figures into `data/figures/`:
- Reliability diagram per question, with the permutation noise floor drawn in. **This is the most
  important plot in the project** — it is the first measurement of Jev's calibration on
  astronomical data that anyone has made.
- Feature importance by question, summed across encoding columns.
- ΔAUC with CIs: model D and E vs baselines A/B/C, both splits, one chart.
- Probability histogram per question — to see the documented two-decimal quantization and any
  degenerate pile-up at 0.0/1.0 empirically.

---

## 7. Pre-registration — write `PREREGISTRATION.md` and commit it BEFORE Step 3

The build loop reads model errors and can be iterated. That is an efficient machine for
overfitting. Fix the criteria in writing first, commit them, and do not edit them after seeing
results.

### Splits (both required)

- **S1 — Grouped CV:** `GroupKFold` on **TIC ID**, 5 folds × 3 repeats. Never split within a
  system; two planets around one star share a comment record and a host.
- **S2 — Temporal:** ⚠️ **REVISED 2026-09-19 — as originally written this split was not
  implementable.** It said "train on TOIs *dispositioned* before a cutoff", but **there is no
  disposition-assignment timestamp in any source** (§2.1). The nearest usable proxy is
  **`date_toi_alerted`** (ExoFOP `Date TOI Alerted (UTC)`, 100% coverage, range 2018-09-05 →
  2026-08-06): train on TOIs *alerted* before a cutoff, test after.

  **This is a weaker claim than the plan intended** and must be described honestly in
  `RESULTS.md`: it tests generalization to *newer candidates*, not to *future dispositions*.

  Candidate cutoffs, measured — **pick one and record it in `PREREGISTRATION.md` before looking
  at any result:**

  | cutoff | % in test | test base rate |
  | :--- | ---: | ---: |
  | 2021-07-19 | 29.6% | 0.651 |
  | **2021-10-28** | **24.7%** | **0.634** |
  | 2022-01-25 | 19.9% | 0.633 |

  **Note the base-rate shift:** the corpus is 50.3% positive overall but the recent slice runs
  ~0.63. S2 therefore carries genuine distribution shift — which is the point, but it means an
  S2 AUC is not directly comparable to an S1 AUC.

### Gates

| Gate | Criterion |
| :--- | :--- |
| **G1** | ✅ **PASSED 2026-09-19.** B **0.9154** AUC / 0.1136 Brier vs A 0.5000 / 0.2501. Pipeline is sound. |
| **G2** | Model D (numeric + predictive tier) beats Model B on **ΔAUC with a bootstrap 95% CI excluding zero**, under split S1. ⚠️ **Harder than this plan assumed:** B sits at **0.9154** (0.9037 leakage-stripped), leaving ~0.08 of headroom, and there are **2,573 groups, not ~7,000**. Both shrink the detectable effect. This is not a reason to lower the bar — it is a reason to expect a null and to size that expectation before spending. |
| **G3** | **Stability.** Re-run 200 rows with (a) paraphrased question wording and (b) permuted state key order. Rank agreement (Spearman) on each feature ≥ 0.85 and mean \|Δp\| ≤ 0.05. *If paraphrasing materially moves the features, the result is not scientific and G2 does not count.* |
| **G4** | **The headline gain survives on the predictive tier alone, under split S2.** A gain present only in Model E (with label-echo questions) or only under S1 is a **negative** result. |
| **G5** | ⚠️ **NEW 2026-09-19 — leakage-stripped arm.** The gain must survive on the subset with designation-only and `retired`/`TFOP FP` comments removed (**1,417 rows / 1,312 TIC**, base rate 0.485). Given §2.0, a gain that evaporates here was a gain from reading the label. **Pre-register the exact regex before running it.** |
| **G6** | ⚠️ **NEW 2026-09-19 — missingness ablation.** Numeric-column missingness is mildly label-correlated (`st_logg` non-null 0.829 for y=0 vs 0.991 for y=1) and a missingness-only model scores **AUC 0.5869**. Re-fit B and D with explicit missingness indicators and confirm the *Jev* gain is not tracking the same channel. |

### Decision rule

- **All four gates pass** → proceed to the extensions in §8.
- **G1 fails** → pipeline bug. Fix, rerun.
- **G3 fails** → report the instability as the finding. It is a real and publishable result about
  using this class of model in science.
- **G5 fails** → the effect was label echo. Report it as a negative result **and** as a finding
  about archive text: the signal was the annotation, not the observation.
- **G2 or G4 fails** → **stop.** Write the negative result. Do not add rounds hoping for signal:
  the source cookbook found most of its gain in round one (1.87 of an eventual 1.77), with four
  further rounds contributing 0.10. If round one is flat, more rounds will not rescue it.

---

## 8. Future extensions (not MVP — only after all four gates pass)

1. **LLM proposer loop.** Rounds 2–5: a reasoning model reads worst-predicted rows and feature
   importances, proposes new questions. Revisions tested by refit and rejected if dev error rises.
2. **Cross-mission validation** on the Kepler Certified False Positive Table (KSCI-19093) rationale
   text — different mission, different era, different conventions. The real distribution-shift test.
3. **ADS abstract corpus** per host star, via the `ads` package (~5,000 req/day).
4. **DV report text** from MAST (needs PDF extraction).
5. **The interesting long-term question:** do text features add anything *on top of* a pixel-level
   CNN like ExoMiner? That is the experiment that would tell you whether this is a real channel of
   information or a proxy for something the pixels already contain.

---

## 9. Definition of done for the MVP

- [ ] `01_ingest.py` reproduces the snapshot from checksums; row/class/comment counts reported.
- [ ] Comment-timestamp investigation recorded in `PREREGISTRATION.md`.
- [ ] `PREREGISTRATION.md` committed **before** the first Jev call.
- [ ] Baselines A, B, C evaluated under both splits.
- [ ] ~14 questions answered for every row, raw responses cached and persisted.
- [ ] Total Jev spend recorded (expected < $1).
- [ ] ΔAUC/ΔBrier with bootstrap CIs, for tiers predictive and full, under S1 and S2.
- [ ] Per-question reliability diagrams with noise floor, Noul and Score reported separately.
- [ ] Stability audit results.
- [ ] A short `RESULTS.md` stating plainly which gates passed and what the answer is — **including
      if the answer is no.**
- [ ] **G5 (leakage-stripped) and G6 (missingness) reported alongside G2/G4.**
- [ ] **Public-release checklist in §11 completed** before the repo is made public.

---

## 10. Context for a fresh session

- **Jev docs:** start at `https://docs.typesafe.ai/llms.txt`. Mintlify serves Markdown by appending
  `.md` to any page path. Load the `typesafe:typesafe-ai` skill if available — this project's
  memory directs that it be used for all work here.
- **Key doc pages:** `models.md`, `primitives.md`, `confidence.md`,
  `model-jaggedness/jev-1.13.md`, `sdk/python.md`,
  `cookbooks/autoresearch_feature_discovery.md` (the pattern this project adapts),
  `cookbooks/parallel_questions.md`.
- **Verified specs:** model `jev-1.13.0` · `POST https://api.typesafe.ai/v1/systemone` ·
  $0.042/MTok input, output free · 64k total / 32k state tokens · 250k tok/s, 1,200 req/min ·
  text only · 70–500ms.
- **SDK shape:**
  ```python
  from typesafe_sdk import AsyncTypeSafeClient, Noul, Score
  async with AsyncTypeSafeClient() as client:
      r = await client.system_one(state={...}, questions={"id": Noul(instructions="...")})
  r.answers["id"].noul          # float 0–1
  r.scores["sid"].score         # expected level
  r.scores["sid"].probabilities # dict[int, float] ← the features live here
  ```
- **API key is present** in `.env` as `TYPESAFE_API_KEY` (gitignored; `.env.example` shows the
  shape). Verified working against `jev-1.13.0` on 2026-09-19.
- **Documents 01–03 contain no live measurement** — they are sourced to vendor docs and
  third-party evaluation only. `research/04_first_live_measurements.md` and `WORKLOG.md` are the
  only records backed by our own measurements.
- **Environment:** `uv venv --python 3.14 .venv` — see §4, already resolved and verified.

---

## 11. Public release on GitHub

This project is intended to be **published as a public repository.** That is a good fit for the
work — the negative-result design, the pre-registration and the append-only `WORKLOG.md` are
exactly what makes a small study credible, and none of it is proprietary. It also raises the bar:
a public repo is read by people who did not watch it being built.

### 11.1 Secrets — the non-negotiable part

- The API key lives **only** in `.env`, which is gitignored. `.env.example` carries the variable
  name and no value.
- **Audited 2026-09-19:** the key string appears in no file other than `.env`. At that point the
  project was **not yet a git repository**, so there is no history to scrub — the initial commit
  starts clean. Preserve that.
- **Never** commit `data/` (raw snapshots, DuckDB, the Jev response cache). It is gitignored.
- If a key is ever committed: **rotate it first**, then rewrite history. Rotation first, always —
  a public commit is scraped within minutes.

### 11.2 What gets published, and what does not

| Published | Not published |
| :--- | :--- |
| `PLAN.md`, `WORKLOG.md`, `PREREGISTRATION.md`, `RESULTS.md` | `.env` |
| `research/01–04` | `data/` (raw CSVs, DuckDB, cache, figures) |
| `scripts/`, `src/`, `tests/` | `.venv/` |
| `PROVENANCE.md` (checksums of the raw pulls) | — |

**`data/` stays gitignored, but reproducibility must not depend on it.** Every raw source is
re-downloadable and checksummed, so `01_ingest.py` regenerates the snapshot and a third party
can verify they got the same bytes. `PROVENANCE.md` is the committed record of those checksums.
Note the sources **drift** (ExoFOP updates continuously; NEA syncs weekly), so a later pull will
*not* match — that is expected and is exactly why the checksums and the snapshot date are
recorded rather than the data.

### 11.3 Honesty requirements specific to going public

These matter more once strangers are reading:

1. **State the negative findings in the README, not only in the log.** The `pscomppars` trap and
   the 47.9% label-echo rate (§2.0) are the most useful things this project has produced so far.
   Anyone else pointing an LLM at ExoFOP text will hit both.
2. **Never present baseline C's 0.969 AUC without the leakage explanation.** Out of context it
   reads as a strong result. It is not one.
3. **Keep `research/01–02` published but clearly marked superseded.** Deleting them would hide
   the correction history, which is part of the record. `research/README.md` and `03` §1.4
   already carry the warnings — verify they survive into the public version.
4. **Label what was measured vs. what was assumed.** `research/01–03` are sourced to vendor docs
   and third-party evaluation; only `research/04` and `WORKLOG.md` are our own measurements.
5. **Credit the data sources properly** — ExoFOP-TESS, the NASA Exoplanet Archive, and `etta`.
   See §11.5.

### 11.4 Licensing

- **Code:** MIT. Simple, permissive, standard for this kind of work.
- **Text and figures:** CC BY 4.0, stated in the README.
- **Data:** not redistributed, so no licence is needed — but acknowledgements are (§11.5).

### 11.5 Required acknowledgements

Both archives request citation. Put this in the README:

> This research has made use of the **Exoplanet Follow-up Observation Program (ExoFOP)** website,
> which is operated by the California Institute of Technology under contract with NASA under the
> Exoplanet Exploration Program. This research has made use of the **NASA Exoplanet Archive**,
> which is operated by Caltech under contract with NASA under the Exoplanet Exploration Program.
> TOI data access uses **`etta`** (MIT).

### 11.6 Pre-publication checklist

Run this immediately before making the repo public:

- [ ] `git log -p | grep -i` for the key — must be empty. **Rotate the key if not.**
- [ ] `.env` is not tracked: `git ls-files --error-unmatch .env` must fail.
- [ ] `data/` is not tracked: `git ls-files data/ | wc -l` must be `0`.
- [ ] `LICENSE`, `CITATION.cff`, `CONTRIBUTING.md`, `PROVENANCE.md`, `requirements.txt` present.
- [ ] README states current status honestly, including that the headline question is still open.
- [ ] README carries the §11.5 acknowledgements.
- [ ] `research/01–02` are marked superseded.
- [ ] A clean clone reproduces: `uv venv --python 3.14 .venv`, install, `01_ingest.py`,
      `02_baselines.py` — and G1 passes.
- [ ] No absolute local paths (a home directory, a username) anywhere in tracked files:
      `git grep -nE '/(Users|home)/[a-z]'` must return nothing.

### 11.7 When to publish

**Publishing now is reasonable and arguably better than waiting.** The repo currently contains a
verified data foundation, a passing G1, two genuinely useful negative findings, and an explicitly
open headline question. A repo that says "here is the question, here is the honest baseline, the
answer is not in yet" is more credible than one that appears only once the result is favourable —
and pre-registration only means something if it is published *before* the result.

The alternative — waiting for `RESULTS.md` — risks looking like the pre-registration was written
after the fact, which is the exact failure mode §7 exists to prevent.
