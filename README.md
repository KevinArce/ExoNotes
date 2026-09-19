# ExoNotes

**Do the free-text comments astronomers write on TESS Objects of Interest carry
disposition-relevant information that the numeric catalogue columns do not?**

That is the whole question. It is falsifiable, it is cheap to test, and **a null result is a
valid and useful outcome** — so this repository is built to report one honestly if that is what
the data says.

**Method.** Convert ExoFOP `Comments` into numeric semantic features with a System One model
(Jev, TypeSafe AI), then measure whether those features improve held-out prediction of TFOPWG
disposition over a numeric-only baseline. The model is the **featurizer**, gradient boosting is
the **predictor**, grouped cross-validation by host star is the **arbiter**. The model's own
probabilities are never thresholded into a decision — its calibration degrades ~4.4× out of
distribution, and astrophysics is maximally out of distribution for it.

---

## Status — the headline question is still open

| | |
| :--- | :--- |
| ✅ Data foundation | 2,721 labelled TOIs across 2,573 host stars, 50.3% positive |
| ✅ Gate G1 (pipeline sanity) | **Passed.** Numeric baseline 0.9154 AUC vs 0.5000 prior |
| ⬜ Gate G2/G4/G5/G6 | **Not yet run.** No semantic features have been computed |
| 💸 Spend to date | **~$0.0002** |

**Nothing in this repository yet answers the headline question.** Baselines exist; the semantic
features do not.

## Two findings that are already useful

Both are things anyone pointing a language model at archive text will hit, so they are stated
here rather than buried in the log.

### 1. Nearly half the ExoFOP comment corpus restates the label

Measured over 2,725 labelled rows with comments:

| Marker in comment text | n | P(confirmed planet \| marker) |
| :--- | ---: | ---: |
| bare planet designation (`WASP-68 b`, `Kepler-718 b`) | 679 | **0.999** |
| contains `retir*` ("retired as NEB") | 488 | **0.006** |
| contains `TFOP FP` | 502 | **0.000** |
| **any of the above** | **1,304 (47.9%)** | — |

A planet has a name only because it was confirmed, so a comment reading `WASP-68 b` **is** the
label written in prose. A TF-IDF baseline on this text scores **0.969 AUC** — and its strongest
positive terms are survey prefixes (`wasp, k2, kepler, hat, kelt, ngts`). **That number is
leakage, not signal, and must never be cited as evidence for the hypothesis.**

There is also **no timestamp on the `Comments` field** — not in ExoFOP, not in the NASA
Exoplanet Archive, and no revision log in any `etta` endpoint — so post-hoc edits cannot be
filtered out. ([`PLAN.md`](./PLAN.md) §2.)

### 2. `pscomppars` cannot be used as a covariate source

The NASA Exoplanet Archive's `pscomppars` table contains **confirmed planets only**. Membership
in it predicts the label at **P=0.995 vs 0.074** — so a model built on it leaks the label through
*missingness alone*, scores ~0.99 AUC, and contains no astrophysics. An earlier version of this
plan specified it as the covariate source; that was wrong. Covariates come from the `toi` table.
([`PLAN.md`](./PLAN.md) §3.2.)

---

## Repository guide

| File | What it is |
| :--- | :--- |
| **[PLAN.md](./PLAN.md)** | The build plan, the guardrails, and the pre-registered gates. §0.5 is the work-logging protocol; §2 is the validity threat; §11 covers public release. |
| **[WORKLOG.md](./WORKLOG.md)** | Append-only record of every step, including every failure and every place the plan turned out to be wrong. **The most honest file here.** |
| **[PROVENANCE.md](./PROVENANCE.md)** | SHA256 of each raw source. `data/` is not committed. |
| [HANDOFF_PROMPT.md](./HANDOFF_PROMPT.md) | Pasteable prompt for the next working session. |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | How to reproduce, and the two rules that keep this auditable. |
| [research/03_*](./research/03_jev_astrophysics_evidence_based_assessment.md) | Why this project, and why it is deliberately **not** a transit vetter. |
| [research/04_*](./research/04_first_live_measurements.md) | First live model calls. Found 3 of 7 draft questions defective. |

⚠️ `research/01_*` and `research/02_*` are **superseded** where they conflict with `03_*`, which
itemizes ten corrections in §1.4. They are kept because the correction history is part of the
record — not because they are reliable.

**What is measured vs. what is sourced:** `research/01–03` are sourced to vendor documentation
and third-party evaluation and contain **no measurement of our own**. Only
[`research/04`](./research/04_first_live_measurements.md) and [`WORKLOG.md`](./WORKLOG.md) report
our own calls.

## Reproducing

```bash
uv venv --python 3.14 .venv
uv pip install -r requirements.txt
.venv/bin/python scripts/01_ingest.py      # ~25 s
.venv/bin/python scripts/02_baselines.py   # ~2 min, reproduces gate G1
```

No API key required — neither step makes a model API call. See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Acknowledgements

> This research has made use of the **Exoplanet Follow-up Observation Program (ExoFOP)** website,
> which is operated by the California Institute of Technology under contract with the National
> Aeronautics and Space Administration under the Exoplanet Exploration Program.
>
> This research has made use of the **NASA Exoplanet Archive**, which is operated by the
> California Institute of Technology under contract with the National Aeronautics and Space
> Administration under the Exoplanet Exploration Program.

TOI table access uses [`etta`](https://pypi.org/project/etta/) (MIT).

## Licence

Code is **MIT** ([LICENSE](./LICENSE)). Prose and figures are **CC BY 4.0**. No archival data is
redistributed here.
