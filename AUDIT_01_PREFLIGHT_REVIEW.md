# Audit 01 — adversarial pre-flight review

> **Taken on 2026-09-20, before TASK A**, at the project owner's request: interrogate every
> architectural decision, statistical assumption and methodology choice, and find the blind spots
> while they are still cheap to fix.
> **Cost:** $0 — no model API calls anywhere in this audit.
> **Outcome:** 4 findings that change the registered design (amended into
> [`PREREGISTRATION.md`](./PREREGISTRATION.md) §11), 5 that change how a step is run, 4 recorded
> for the write-up. Two of the auditor's own hypotheses were tested and **failed**; both are
> recorded below, because a review that only reports its hits is not a review.

---

## Why this exists

The previous session closed the pre-publication checklist at 10/10 and handed over three
unresolved risks. Everything downstream of here spends money and, more importantly, spends the
one thing a pre-registered study cannot get back: **the right to decide the criteria before
seeing the result.** `PLAN.md` has already been wrong eight times. This audit assumes it is
wrong a ninth.

Every claim below was checked against the repo or measured. Where a measurement contradicted the
reviewer's hypothesis, the contradiction is what is reported.

---

## Severity 1 — these change the registered design

### A1. Gate G2 has no zero point: adding *any* eight columns costs ~0.011 AUC

**The finding.** [`PREREGISTRATION.md`](./PREREGISTRATION.md) §6 defines G2 as "model D beats
model B on ΔAUC, paired group bootstrap CI excluding zero." It never asks what ΔAUC an
*uninformative* feature set produces. At the projected obsnotes scale, the answer is not zero.

Measured by [`scripts/026_noise_floor.py`](./scripts/026_noise_floor.py) — 1,811 rows, 1,715 TIC
groups, base rate 0.491, `TIER_PREDICTIVE`-sized `k = 8` columns of pure Gaussian noise, five
seeds, S1 as registered. Artifact: `research/data/noise_floor_2026-09-20.json`.

**B (numeric only, 8 features) = 0.9044 AUC.** Adding eight columns of nothing:

| noise seed | AUC | ΔAUC vs B | paired 95% CI |
| ---: | ---: | ---: | :--- |
| 0 | 0.8934 | −0.0110 | [−0.0160, −0.0061] |
| 1 | 0.8919 | −0.0125 | [−0.0177, −0.0073] |
| 2 | 0.8921 | −0.0123 | [−0.0177, −0.0070] |
| 3 | 0.8954 | −0.0090 | [−0.0143, −0.0038] |
| 4 | 0.8930 | −0.0114 | [−0.0164, −0.0065] |
| **mean** | **0.8932** | **−0.0112** | **all five exclude zero** |

Eight worthless columns produce a statistically clean *negative* result on the exact statistic G2
uses, on every seed.

**Why it is not a tuning artifact.** The reviewer's first assumption was that the fixed 500
iterations were to blame. Probed across five configurations × three noise seeds (single-repeat
CV, so these are indicative rather than the registered arm):

| configuration | dilution penalty |
| :--- | ---: |
| `iterations=500 depth=4` — **as registered** | −0.0114 |
| `iterations=200 depth=4` | −0.0100 |
| `iterations=2000` + early stopping | **−0.0132** |
| `iterations=500 depth=6` | −0.0120 |
| `iterations=500 l2_leaf_reg=30` | −0.0108 |

Early stopping makes it *worse*. This is structural at n ≈ 1,800, not a hyperparameter choice.

**Why it is blocking.** The penalty is **over four times the bootstrap SE** of ΔAUC (0.0026). So:

- a reported **ΔAUC ≈ 0.000 is not a null** — it is ~+0.011 of genuine signal cancelling dilution;
- a reported **ΔAUC ≈ +0.007 with a CI excluding zero** understates the true effect by ~0.011.

§8's decision table maps ΔAUC ≈ 0 onto *"Stop. Write the negative result."* As written, the study
can publish a null that its own model configuration manufactured — and §8.1 commits to publishing
that null with the same care as a positive result. That is the failure mode this audit exists to
catch.

**Resolution — registered in §11 as amendment A-1.** A fourth arm, **B+N**: B plus *k* Gaussian
columns, *k* = the final Jev feature count, averaged over ≥5 seeds. ΔAUC(D−B) is reported against
ΔAUC(B+N−B) as its zero point, and §8's decision table reads against that reference. Costs $0.

---

### A2. Power was never computed, and §8.1 plans to compute it the one way that carries no information

**The finding.** §8.1 commits to reporting "the power the study actually had." Power computed
after the fact, from the observed effect, is a deterministic monotone function of the p-value. It
adds exactly nothing to a confidence interval that is already being reported. A null published
with an observed-power number is a null with a decorative statistic attached.

What §9's promise actually requires is a **minimum detectable effect fixed in advance**.

**Measured**, from the same paired group bootstrap:

| quantity | value |
| :--- | ---: |
| SE of ΔAUC (paired, resampled over TIC groups) | **0.0026** |
| MDE at 80% power, two-sided 95% | **+0.0073** |
| net of the A1 dilution floor, true signal required | **0.0186** |

Expressed in terms the question set can be checked against — a graded oracle text feature that
agrees with the truth with probability *q*:

| feature's own univariate AUC | ΔAUC | paired 95% CI | G2 detects it? |
| ---: | ---: | :--- | :--- |
| 0.553 | +0.0024 | [−0.0009, +0.0058] | no |
| 0.592 | +0.0017 | [−0.0019, +0.0053] | no |
| **0.653** | +0.0090 | [+0.0030, +0.0154] | **yes** |
| 0.695 | +0.0156 | [+0.0081, +0.0231] | yes |
| 0.753 | +0.0242 | [+0.0155, +0.0332] | yes |
| 0.808 | +0.0398 | [+0.0297, +0.0508] | yes |

**A single Jev feature must reach roughly 0.65 univariate AUC against the disposition before G2
can see it**, and a feature at 0.59 is invisible. That is a demanding bar for six noul questions
about eclipse geometry, and it is the number TASK B's question set should be checked against *as
it is being written*, not after.

**Resolution — §11 amendment A-2.** MDE and the oracle bar are registered before the run.
§8.1's "power we had" is replaced by "the MDE we registered, and where the observed CI fell
relative to it."

---

### A3. Gate G5's regex is inoperative on the corpus it will actually run against

**The finding.** [`src/exonotes/leakage.py`](./src/exonotes/leakage.py) was built for the
`Comments` field: median 30 characters. Two of its five clauses are anchored `^…$` against the
whole string. Run against the 20 cached TICs that survive the corpus filter:

| clause | fires on observer-note text |
| :--- | :--- |
| `L1_retired` | **0 / 20** |
| `L2_tfop_disposition` | **0 / 20** |
| `L3_confirmed` | 1 / 20 |
| `L4a_designation_catalogue` | **0 / 20** |
| `L4b_designation_planet_letter` | **0 / 20** |
| **any clause** | **1 / 20** |

The G5 arm would be ~95% identical to the full arm. **G5 would pass trivially and detect
nothing** — and §8 reads a G5 pass as *"the effect was not label echo,"* which is the single
conclusion G5 exists to license.

**The leak is real; it just has a different shape here.** `NEB`, `BEB`, `cleared`, `retired`,
`false positive` all fire 0/20 on observer prose — the `Groupname` filter genuinely works. But
`TOI-\d+` fires **13/20**, and one cached note opens *"Extracted KOI12 observing note from
ExoFOP-Kepler"* — a Kepler Object of Interest designation, which is the §2.0 P=0.999 channel in a
form no anchored clause can see.

**`HANDOFF_PROMPT.md` TASK A/B/C said nothing about this.** The question set was correctly
identified as non-transferable; the leakage regex it is paired with was not.

**Resolution — §11 amendment A-3.** G5's clause set is re-derived on real observer-note text and
re-registered, on the same schedule and with the same discipline as the question set: before
Step 3 makes a single full-corpus call.

---

### A4. Every request hands Jev a label-correlated designation in a field G5 structurally cannot strip

**The finding.** §3 fixes the request state as:

```python
state = {"toi": str(row.toi), "notes": observer_notes_text}
```

and [`scripts/025_question_gate.py:231`](./scripts/025_question_gate.py#L231) already sends
`{"toi": "TOI-624.01", "comment": ...}`.

**No question in [`src/exonotes/questions.py`](./src/exonotes/questions.py) reads `toi`.** Every
one of the eleven is phrased "Does `comment` …". The field buys nothing and costs input tokens on
every one of ~1,814 rows.

What it does do is defeat G5. §5's entire apparatus excludes rows **whose text** carries a
catalogue designation — `L4a` is documented at P(y=1) = 0.999, the strongest leakage channel in
the corpus. Meanwhile **every row's state carries a catalogue designation in a field the regex
never reads.** The G5 arm cannot strip a channel that does not live in the text it strips.

`contains_object_designation` is in `TIER_LABEL_ECHO` precisely because designations predict the
label almost deterministically. Supplying one on every call, for free, to a model whose answers
become features, is not a defensible default.

**Resolution — §11 amendment A-4.** `toi` is removed from the state. The registered state becomes
`{"notes": observer_notes_text}`. If the owner prefers to keep it, G3 must add a third
perturbation — *state with `toi` removed* — alongside paraphrase and key permutation.

---

## Severity 2 — these change how a step is run

### A5. `jev-latest` is a moving target sitting inside the cache key

[`scripts/025_question_gate.py:36`](./scripts/025_question_gate.py#L36) sets `MODEL =
"jev-latest"`, and the cache key is `sha256(MODEL + QUESTION_SET_VERSION + state + questions)`.

The cached responses record the *resolved* version — every one in `data/cache/gate/` carries
`"model": "jev-1.13.0"`. So the information exists; it just is not used.

If TypeSafe ships 1.14 mid-run, or between the run and a reproduction, **cache hits serve 1.13
answers and cache misses get 1.14, under an identical key.** The feature matrix silently mixes two
models. The CI reproduction does not catch this: it reruns ingest and baselines only, and makes no
API calls at all — so the repo's "reproduction-verified" badge says nothing about Step 3.

**Fix before TASK B:** pin `MODEL = "jev-1.13.0"`, and assert `response["model"] == MODEL` before
persisting. Record the pinned version in §11.

### A6. How ΔAUC aggregates across the three S1 repeats was never defined

§6 specifies "ΔAUC under S1, bootstrap 95% CI, 10,000 resamples over TIC groups." S1 is 5 folds ×
**3 repeats**. Whether ΔAUC is a mean of 15 per-fold AUCs, a single AUC over pooled predictions,
or a mean of 3 per-repeat AUCs is undefined — and the three give different CIs.
[`scripts/02_baselines.py`](./scripts/02_baselines.py) averages 15 per-fold AUCs and reports a
`std` across them, which is not a standard error of anything.

`scripts/026_noise_floor.py` fixes a convention and §11 registers it: **pool out-of-fold
predictions within a repeat, score each repeat, average the repeat AUCs.** The bootstrap resamples
TIC groups and recomputes that same average, **using the same resample for both models**. Pairing
is not optional — D and B share every numeric column, so an unpaired bootstrap inflates the CI by
the between-model covariance.

### A7. The selection effect is measured, directional, and understated

§1.4 says the ~33% exclusion is "probably not label-neutral." The project's own recon file
already measures it:

| | |
| :--- | ---: |
| P(has observer note \| y=1) | **0.80** (12/15) |
| P(has observer note \| y=0) | **0.53** (8/15) |
| implied subset base rate at corpus base 0.503 | **≈ 0.60** |

n = 30, so the interval is wide — but this is the best estimate available and it is directional.
More than a base-rate shift, it is a **collider**: follow-up effort sits downstream of both the
numeric properties and the eventual disposition. Conditioning on it can attenuate B and inflate
the apparent text gain on the selected subset relative to the population.

**Report, don't fix:** alongside the realised base rate, report B's AUC on included versus
excluded rows. If B is materially weaker on the included subset, the D−B comparison is running on
easier ground for D and the write-up must say so.

### A8. `evidence_depth` is a semantic proxy for the feature §10.2 bans

§10.2: *"No feature derived from note count, note length, or number of authors may enter any
model. Text content only."* Correct, and motivated — note count correlates with the label (median
3 for y=1 vs 2 for y=0).

But `evidence_depth` is a 0–4 score over *"none → a remark → one observation → several → multiple
independent facilities."* That is close to monotone in note count and text length. The direct
feature was banned and a semantic proxy for it was kept.

**Fix:** register a control baseline **B+meta** — numerics + note count + total characters +
author one-hot. All of it derivable with zero API calls. If D does not beat B+meta, the result is
about *how much follow-up a candidate received*, not about what the prose says — which is a
finding, but a different one from the one §0 asks about.

### A9. The question-design gate can see the labels

Every case in [`scripts/025_question_gate.py`](./scripts/025_question_gate.py) carries its real
`y=`, and the 23 cases were hand-picked by someone who could see it. The `expect` fields assert
only what the text says, and that discipline is visible and real — but **case selection** was
label-aware, which is feature design informed by the outcome.

**Fix for TASK B:** sample the 20–25 obsnotes cases programmatically across the length
distribution, withhold labels until every answer has been inspected by eye, then attach them.
Cheap, and it removes the objection rather than arguing about it.

---

## Severity 3 — recorded for the write-up

### A10. `Groupname != 'tfopwg'` is really `Groupname IS NULL`

Across all 79 cached notes there are exactly two values: `'tfopwg'` (34) and **NaN** (45). There
is no `SG1`-style groupname in the data. The filter works, and
[`scripts/027_obsnotes_recon.py`](./scripts/027_obsnotes_recon.py) documents the behaviour in a
comment — but §1.1 describes a selection semantics the data does not have, and the mechanism is
fragile: if ExoFOP ever populates `Groupname`, or `etta` changes its parse, the corpus changes
silently and nothing asserts otherwise. One honest sentence in §1.1, and an assertion in TASK A.

### A11. The cached corpus artifacts are not valid JSON

20 of 30 files in `data/cache/obsnotes/` contain bare `NaN` tokens — accepted by Python's `json`
and by `jq`, rejected by `JSON.parse` and by any RFC-8259-strict parser. For a public archival
artifact backing a pre-registered study, write `null`. One-line fix in the TASK A writer.

### A12. The corpus-size projection is a point estimate from n = 30

"~1,814 rows / ~1,715 TIC" is 20/30 extrapolated linearly. The binomial interval on 20/30 is
roughly [47%, 83%], i.e. **1,200–2,140 TIC**. Since the A1 dilution penalty and the A2 MDE are
both functions of n, the low end of that range materially changes the study's power. Re-run
`scripts/026_noise_floor.py` on the **realised** row set after TASK A, before TASK C.

### A13. G3's Spearman criterion will misbehave on low-variance features

G3 requires ρ ≥ 0.85 per feature. Jev returns two decimals (§10.5), and several nouls will sit
near 0 or near 1 for almost every row. A feature that is correctly and stably near-zero
everywhere has almost no rank variance, so ρ is dominated by quantisation ties and can fail
spuriously while `mean |Δp|` passes comfortably. Pre-specify the degenerate case: if a feature's
IQR is below one quantisation step, G3 is judged on `mean |Δp|` alone, and that is recorded.

---

## Hypotheses the reviewer tested and had to abandon

These are recorded because the alternative is a review that looks more accurate than it was.

### N1. "Known Planets inflate baseline B." — **Wrong.**

601 of 1,369 positives (44%) are `KP`: pre-TESS discoveries, systematically bright, large and
short-period. The hypothesis was that B's 0.9154 is substantially "this object was already
famous," and that excluding KP would open headroom for D. Measured:

| arm | n | base | B AUC |
| :--- | ---: | ---: | ---: |
| all (CP+KP vs FP+FA) — as registered | 2,721 | 0.503 | **0.9128** |
| **KP excluded** (CP vs FP+FA) | 2,120 | 0.362 | **0.9231** |
| KP-only positives (CP excluded) | 1,953 | 0.308 | **0.9211** |

B is *not* leaning on the known planets — it is slightly better without them. The numeric columns
genuinely separate false positives from real planets in every stratification. **The project's
pessimism about G2 is better founded than its own document argues**, and no KP-excluded arm is
warranted.

### N2. "The cross-platform nondeterminism finding is load-bearing." — **It is a distraction.**

The previous session established a systematic 5×10⁻⁴ AUC offset between macos/arm64 and
linux/x64, and derived the guidance *"treat any claimed ΔAUC below ~10⁻³ as noise."* Both are
correct. But the bootstrap SE of the headline statistic is **0.0026** and the MDE is **0.0073** —
so the registered decision threshold is roughly **fifteen times larger** than the platform effect.
Two CI runs went into characterising an error term that ranks somewhere around sixth. Keep the
single-platform rule (it is free); retire the 10⁻³ figure as a decision rule, because quoting it
next to a ΔAUC invites a reader to think 2×10⁻³ means something.

---

## What changed as a result

| artifact | change |
| :--- | :--- |
| [`PREREGISTRATION.md`](./PREREGISTRATION.md) §11 | amendments **A-1 … A-7** registered, append-only, before any full-corpus run |
| [`scripts/026_noise_floor.py`](./scripts/026_noise_floor.py) | **new** — the B+N dilution arm, the MDE, the oracle bar, and the ΔAUC aggregation convention |
| [`HANDOFF_PROMPT.md`](./HANDOFF_PROMPT.md) | rewritten around these findings; TASK A gains preconditions, TASK B gains blinding and the oracle bar, a new TASK B0 covers G5 |
| `WORKLOG.md` | this audit, appended |

**Nothing in this audit was learned from data that the pre-registration forbids looking at.** No
full-corpus Jev run has been made; every measurement above is on the existing `Comments`
`analysis_set`, on the 30-TIC recon sample, or on synthetic noise. The criteria are still being
fixed before the result, which is the only window in which they can be.
