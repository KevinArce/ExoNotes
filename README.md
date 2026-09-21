# ExoNotes

<p align="center">
  <img src="assets/exonotes_banner.jpg" alt="ExoNotes Banner" width="100%">
</p>

<p align="center">
  <a href="https://github.com/KevinArce/ExoNotes/actions/workflows/reproduce.yml">
    <img src="https://github.com/KevinArce/ExoNotes/actions/workflows/reproduce.yml/badge.svg"
         alt="clean-clone reproduction">
  </a>
  <a href="https://github.com/KevinArce/ExoNotes/actions/workflows/gates.yml">
    <img src="https://github.com/KevinArce/ExoNotes/actions/workflows/gates.yml/badge.svg"
         alt="full-pipeline gate check">
  </a>
  <a href="https://orcid.org/0000-0003-3453-6551">
    <img src="https://img.shields.io/badge/ORCID-0000--0003--3453--6551-A6CE39?logo=orcid&logoColor=white"
         alt="ORCID">
  </a>
  <!-- DOI badge goes here on the first Zenodo release. -->
</p>

**Do the free-text notes astronomers write on TESS Objects of Interest carry
disposition-relevant information that the numeric catalogue columns do not?**

That is the whole question. It is falsifiable, it is cheap to test, and **a null result is a
valid and useful outcome** — so this repository is built to report one honestly if that is what
the data says.

**Method.** Convert ExoFOP observer notes into numeric semantic features with a System One model
(Jev, TypeSafe AI), then measure whether those features improve held-out prediction of TFOPWG
disposition over a numeric-only baseline. (The study began on the `Comments` field and moved off
it — that field restates the label in nearly half its rows; see below.) The model is the **featurizer**, gradient boosting is
the **predictor**, grouped cross-validation by host star is the **arbiter**. The model's own
probabilities are never thresholded into a decision — its calibration degrades ~4.4× out of
distribution, and astrophysics is maximally out of distribution for it.

---

## Status — answered, and all six gates pass

**[`RESULTS.md`](./RESULTS.md) is the write-up. The short version:**

> **ΔAUC(D − B) = +0.0432, 95% CI [+0.0324, +0.0547]** — model D (numeric covariates + semantic
> features) over baseline B (numeric only), under grouped cross-validation by host star,
> `TIER_PREDICTIVE` questions only, paired bootstrap over TIC groups.
> **5.3× the minimum effect the study was pre-registered to detect (+0.0082).**

| | |
| :--- | :--- |
| ✅ Corpus | **1,482 labelled TOIs across 1,388 host stars**, 53.8% positive — ExoFOP observer notes (`Groupname IS NULL`), not the TFOP working-group `Comments` field |
| ✅ G1 pipeline sanity | Numeric baseline **0.9051** AUC vs 0.4840 prior |
| ✅ G2 headline · G3 stability · G4 temporal · G5 leakage-stripped · G6 missingness | **All pass.** [Every interval](./RESULTS.md#2-every-gate-with-its-interval) |
| ⚠️ The pre-registered prior | **Falsified.** A null was predicted in advance and did not happen — [why](./RESULTS.md#5-the-pre-registered-prior-was-wrong) |
| 💸 Spend to date | **~$0.674** (study ~$0.3539 · first CI gate run ~$0.32) |

**The caveats travel with the number.** A cold-cache re-run lands *near* +0.0432, not on it —
**measured at +0.0451** on a clean runner 28 hours later, which is drift, [not a new
headline](./RESULTS.md#8a-the-cold-cache-reproduction-measured);
two label-echo features fail the stability gate; the study's own pre-registered prior predicted
a null and was falsified. All of it is in [`RESULTS.md`](./RESULTS.md), not buried.

### What this is, and what it is not

**The label is a human judgment.** TFOPWG disposition is assigned by the TESS Follow-up
Observing Program, and the observer notes are the *evidence record that same community produced
on the way to it* — speckle imaging results, radial-velocity follow-up, seeing conditions. The
numeric TOI columns are transit-derived and contain none of that.

So this measures whether a model can **read the follow-up evidence trail and anticipate expert
consensus**. It is **not** a planet detector, it is not a transit vetter, and it does not show
the model found physics that people missed.

**What is genuinely non-obvious is the comparison, not the gain:** TF-IDF on the *same text*
scores **0.8766 — below** the numeric baseline's 0.9044, while structured semantic judgments
over that same text add **+0.0432**. Whatever the signal is, bag-of-words does not reach it.

## Two findings that are already useful

Both are things anyone pointing a language model at archive text will hit, so they are stated
here rather than buried in the log.

### 1. Nearly half the ExoFOP `Comments` corpus restates the label

**This is why the study moved to observer notes.** Measured over 2,725 labelled rows of the
`Comments` field — the corpus this project started on and then abandoned:

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
| **[RESULTS.md](./RESULTS.md)** | **The answer**, with reliability diagrams, every confidence interval, the falsified prior, and what was not done. |
| **[PREREGISTRATION.md](./PREREGISTRATION.md)** | The criteria, fixed before the run. §11 is the append-only amendment log. **§11.1–§11.4 were written before any full-corpus model call; §11.5–§11.9 were written after the result and each says so in its own heading.** Later sections supersede earlier ones. |
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
.venv/bin/python scripts/01_ingest.py             # ~25 s
.venv/bin/python scripts/02_baselines.py          # ~2 min, reproduces gate G1
.venv/bin/python scripts/029_verify_reproduction.py   # asserts G1 actually reproduced
.venv/bin/python scripts/026_noise_floor.py       # ~2 min, gate G2's noise floor and MDE
```

No API key required — none of these steps makes a model API call.
See [CONTRIBUTING.md](./CONTRIBUTING.md).

### Reproducing the headline result (needs an API key, ~$0.24)

```bash
.venv/bin/python scripts/028_obsnotes_pull.py         # ~6 min, $0 — the corpus
.venv/bin/python scripts/034_step3_features.py        # ~7 min, ~$0.24 cold / $0.00 warm
.venv/bin/python scripts/035_gates_g2_g6.py           # ~15 min, $0 — G2, G4, G5, G6
.venv/bin/python scripts/036_gate_g3_stability.py     # ~2 min, ~$0.06 — G3
.venv/bin/python scripts/037_reliability.py           # ~1 min, $0 — the RESULTS.md figures
.venv/bin/python scripts/038_drift_sensitivity.py     # ~1 min, $0 — the drift arm
.venv/bin/python scripts/039_gate_g4_s2b.py           # ~1 min, ~$0.03 — G4 with S2b
.venv/bin/python scripts/040_verify_gates.py          # $0 — asserts all six gates still hold
```

> **⚠️ A cold-cache re-run lands near the published number, not exactly on it.** `jev-1.13.0`
> is effectively deterministic within a session (mean |Δ| **0.0001** between calls minutes
> apart) but drifts slightly over longer gaps (**0.0049** at ~1 hour), measured on
> byte-identical requests. `data/` is gitignored, so the 1,382 cached responses are not in this
> repository: from that cache the pipeline is exact, without it only approximate. No gate
> verdict is at risk — measured, not argued: perturbing the features by the drift moves ΔAUC by
> sd 0.0010, and G2 still passes at **ten times** the measured drift. Details:
> [`PROVENANCE.md`](./PROVENANCE.md) and `PREREGISTRATION.md` §11.5 (A-31).

**This is checked automatically, by two workflows that do different jobs.**

[`reproduce.yml`](.github/workflows/reproduce.yml) — the badge above — runs ingest and baselines
on a clean clone, on a fresh GitHub runner, weekly and on every change to `scripts/`, `src/` or
`requirements.txt`. It makes **no API calls** and asserts that baseline B still beats the prior
by a wide margin.

[`gates.yml`](.github/workflows/gates.yml) goes the rest of the way: it rebuilds the corpus,
re-scores it through Jev and asserts **all six gates** with
[`040_verify_gates.py`](scripts/040_verify_gates.py). It **spends real money** — ~$0.33 per run,
cold every time, because `data/` is gitignored and a runner starts empty — so it runs on manual
dispatch and a monthly schedule, never on push. It also **demands that the run actually paid**:
a cold-cache run reporting zero API calls has tested nothing, and would otherwise report six
green gates. The verifier itself is mutation-tested by
[`041_test_verify_gates.py`](scripts/041_test_verify_gates.py), which breaks one gate at a time
and checks all 15 breakages are caught — it runs *before* the paid steps. Registered as
`PREREGISTRATION.md` §11.9 (A-39).

**Neither asserts that the numbers match exactly, and neither should**: ExoFOP updates
continuously and the NASA Exoplanet Archive syncs weekly, so a later pull genuinely differs.
What must survive is the finding, not the bytes — the committed checksums in
[PROVENANCE.md](./PROVENANCE.md) are what pin the exact snapshot. `gates.yml` therefore checks
each gate's **registered criterion** and reports every point estimate with its delta from
publication; a delta larger than model drift alone explains raises a **notice for a human**, not
a red build. Turning normal archive drift into a failing badge is how a badge gets ignored.

**A green badge is not independent replication.** Both workflows run this pipeline, written by
its author, against the same archive. Nobody outside this repository has checked the result —
that is the study's largest open gap and CI does not close it.

If ExoFOP is throttling or down, the run fails with a message saying so explicitly, so an
upstream outage is never mistaken for a broken repository.

## Acknowledgements

> This research has made use of the **Exoplanet Follow-up Observation Program (ExoFOP)** website,
> which is operated by the California Institute of Technology under contract with the National
> Aeronautics and Space Administration under the Exoplanet Exploration Program.
>
> This research has made use of the **NASA Exoplanet Archive**, which is operated by the
> California Institute of Technology under contract with the National Aeronautics and Space
> Administration under the Exoplanet Exploration Program.

TOI table access uses [`etta`](https://pypi.org/project/etta/) (MIT).

## How to cite

**Kevin Javier Arce Alfaro** ([ORCID 0000-0003-3453-6551](https://orcid.org/0000-0003-3453-6551)),
independent researcher.

Machine-readable metadata is in [`CITATION.cff`](./CITATION.cff) — GitHub's *"Cite this
repository"* button renders it in APA and BibTeX.

<!-- DOI-PLACEHOLDER: replace on the first Zenodo release. Use the CONCEPT DOI (the one that
     always resolves to the newest version), not the per-version DOI. Update CITATION.cff
     (`doi:`) and .zenodo.json in the same commit so the three never diverge. -->
> A DOI will appear here once the first release is archived on Zenodo.

Please also cite the archives this work depends on — see
[Acknowledgements](#acknowledgements) above.

## Licence

Code is **MIT** ([LICENSE](./LICENSE)). Prose and figures are **CC BY 4.0**.

**No archival data is redistributed here, with one stated exception.** `data/` is gitignored, so
neither the corpus nor the 1,382 cached model responses are in this repository. The exception is
[`research/data/gate_cases_obsnotes_2026-09-20.json`](research/data/gate_cases_obsnotes_2026-09-20.json),
which carries the **27 verbatim ExoFOP observing notes** of the hand-labelled question-design
gate — they are quoted because the gate cannot be audited without the text that was judged.
ExoFOP is credited under [Acknowledgements](#acknowledgements) above.
