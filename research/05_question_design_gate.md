# The Question-Design Gate — 23 Real Comments, Three Rounds

> **Date:** 2026-09-20 · **Model:** `jev-latest` · **Cost:** $0.0044 (56 calls across 3 rounds)
> **Script:** [`scripts/025_question_gate.py`](../scripts/025_question_gate.py)
> **Frozen set:** [`src/exonotes/questions.py`](../src/exonotes/questions.py) · `2026-09-20.r4`
> **Raw:** [`data/gate_2026-09-20.r2_2026-09-19.json`](./data/gate_2026-09-20.r2_2026-09-19.json) ·
> [`r3`](./data/gate_2026-09-20.r3_2026-09-19.json) · [`r4`](./data/gate_2026-09-20.r4_2026-09-19.json)
>
> This is a first-party measurement. Documents 01–03 are sourced to vendor docs and third-party
> evaluation; this, [`04`](./04_first_live_measurements.md) and `WORKLOG.md` are not.

---

## 1. Why this round existed

[`04`](./04_first_live_measurements.md) tested seven questions against **four hand-written
comments of 100–200 characters** and certified two of them repaired. `PLAN.md` §5 then carried a
warning box: the median *real* ExoFOP comment is **30 characters**, so 04 had verified the
questions on a distribution the corpus does not contain.

**The warning was correct, and the failure was worse than it predicted.**

All 23 cases here are drawn **verbatim** from `analysis_set`, sampled across the true length
distribution (p10 = 9, p50 = 30, p90 = 89, max = 336), including the terse fragments that dominate
the corpus. Every one was verified to exist in the database before it was used, and each case
carries its real TOI id and label.

---

## 2. The headline: a "verified" question was a coin flip

`reports_offset_eclipsing_binary` was certified in 04 §4.1 at **0.870 / 0.070 / 0.070**. On real
text it failed **5 of 23 cases**:

| case | real comment | want | r2 | **r4** |
| :--- | :--- | :---: | ---: | ---: |
| C18 | `…; retired as TFOP FP/NEB` | Y | **0.26** | **0.92** |
| C10 | `TFOP FP; retired as NEB` *(46 rows)* | Y | **0.54** | **0.95** |
| C16 | `close companion star 219379014; TFOP FP; retired as NEB` | Y | **0.57** | **0.94** |
| C22 | `…centroid offset and depth aperture correlation; likely NEB` | Y | 0.86 | **0.97** |
| C17 | `Crowded field; secondary; synchronized; TFOP FP; retired as EB` | N | **0.53** | **0.13** |
| C11 | `TFOP FP/SB1` | N | **0.35** | **0.08** |
| C09 | `8.5 day signal is EB` | N | 0.19 | **0.06** |

**Why it failed.** 04 verified it on `"NEB detected at 1.2 arcmin NE"` — prose that *spells the
offset out*. Real comments never do; they write the bare acronym. The instruction listed `NEB` as
a cue but **led with the geometry** ("at a position offset from the target star"), so on text that
states a *classification* and no geometry, the model hedged at ~0.5.

**What fixed it** was not more precision about the geometry. It was **expanding the acronym inside
the instruction** — `NEB (nearby eclipsing binary)`, `BEB (background eclipsing binary)` — and
stating that the bare acronym counts **on its own, with no separation, direction, or star name
required**, then naming the excluded acronyms (`EB`, `SB1`, `SB2`, `SEB1`, `SEB2`) explicitly.

> **The corpus speaks in abbreviations. The question has to as well.**

**A question can pass a hand-written verification at 0.87/0.07 and still be a coin flip on the
corpus it will actually run against.** That is the transferable result of this document.

---

## 3. A label-echo detector hiding in the predictive tier

Round 2 passed 97/103, and the six-item failure list **hid the most serious defect**, because it
appeared on cases where nothing had been asserted. The full `mentions_instrumental_artifact`
column:

| comment | r3 | **r4** |
| :--- | ---: | ---: |
| `TFOP FP` | **0.65** | **0.07** |
| `TFOP FP; retired as NEB` | **0.62** | 0.12 |
| `TFOP FP/SB1` | **0.60** | 0.34 |
| `8.5 day signal is EB` | **0.55** | 0.42 |
| `close companion star …; TFOP FP; retired as NEB` | **0.46** | 0.24 |
| `Crowded field; …; retired as EB` | **0.44** | 0.23 |
| *(genuine positives)* `low SNR; possible instrument or systematic` | 0.94 | 0.94 |
| *(genuine positives)* `likely asteroid based on difference image in s9` | 0.95 | 0.94 |

**7 of 23 cases sat in the 0.30–0.70 mid-band, and every one carried a TFOP disposition token.**
The bare string `TFOP FP` — which names no instrument, no systematic, no solar-system object —
scored **0.65**.

The model was not answering the question. It was inferring
*false positive → the signal was not real → therefore it was an artifact.* That is the documented
multi-hop failure mode, in the worst possible place: `TFOP FP`/`retired` tokens appear in **47.9%
of the labelled corpus**, so a `TIER_PREDICTIVE` feature would have carried a diffuse echo of the
label straight into the headline result.

**The fix was to name the inference and forbid it:**

> *"A disposition is not an instrumental cause: 'TFOP FP', 'FP', 'FA' and 'retired' say that the
> candidate was rejected, not that an instrument produced the signal."*

`TFOP FP` **0.65 → 0.07**. Mid-band cases **7/23 → 3/23**.

Two rounds of describing the *positive* case more carefully had not moved it. **Telling the model
what not to infer did.** This is a rule 04 did not have and §5 now carries.

### 3.1 The decision rule was fixed before the run
Because this would have been the question's third wording, and `PLAN.md` §5 says *delete rather
than reword a third time*, a rule was committed to `WORKLOG.md` **before** round 3 executed:

> *If case C02 (`TFOP FP`) does not fall to ≤ 0.30 in r4, the question is deleted, not reworded.*

It reached 0.07. The question survives on a criterion set in advance, not on a judgment made after
seeing the number.

---

## 4. Two questions deleted for absence of corpus support

Before spending anything, the corpus was searched for each question's subject matter. Two had
essentially none:

| question | rows matching a **deliberately over-broad** regex | genuine |
| :--- | ---: | ---: |
| `reports_on_target_detection` | 11 / 2,721 (0.40%) | **~2** |
| `indicates_followup_complete` | 2 / 2,721 (0.07%) | **0** |

Most `on-target` matches are *requests* (`SG1 check if it is on target`) or non-recoveries, not
detections. Neither `followup_complete` match states that follow-up finished.

A feature that is constant across 99.6% of rows costs tokens on every call and contributes
nothing. **Both deleted** — a different reason from §5's "needs inference" rule, same remedy.

> **These deletions are corpus-specific and have since been reopened.** The project has switched
> to `download_obsnotes`, whose observer notes contain exactly this content (*"cleared 6/6
> neighbors to 2.5'"*, *"No secondary sources were detected"*). Both are restored as candidates in
> [`PREREGISTRATION.md`](../PREREGISTRATION.md) §2.3.

---

## 5. Smaller findings worth keeping

**A fix introduced a regression, caught only because every case is re-tested every round.**
An r3 cue — *"a named nearby TIC given as the eclipse source"* — was over-broad, and made the bare
designation `HAT-P-70 b` score **0.34** for "is there an offset eclipsing binary?". Bare
designations are **891 rows, 33% of the corpus**. Fixed in r4 to **0.08**.

**Provenance was being counted as evidence.** `found in faint-star QLP search` — the single most
common comment in the corpus, **308 rows** — scored `evidence_depth` **1.86**, as much described
evidence as a real follow-up observation. The rubric's level 2 read *"one observation or data
product referenced"*, and a QLP search **is** a data product, so the model was right and the
**rubric was wrong**. Level 1 was rewritten to absorb provenance explicitly: **1.86 → 1.01**.

**A domain error of ours, surfaced by a failing case.** `SEB` had been listed as an *offset*-EB
cue. It is not: `NEB` = nearby and `BEB` = background (both offset), while `SEB1`/`SEB2` =
**spectroscopic** eclipsing binary, on-target. Moved to `mentions_spectroscopic_binary`.

**Literal token matching matters.** The corpus writes `depth aperture correlation` *unhyphenated*;
the instruction said `depth-aperture`, and the exclusion clause silently failed to bind.

**A negative clause can cancel its own positive.** `mentions_instrumental_artifact` said *"answer
no if the text only reports low SNR"*. The case `low SNR; possible instrument or systematic` has
both, and landed at **0.69** — one hundredth under the bar.

---

## 6. Result

**101 of 103 assertions pass** at `QUESTION_SET_VERSION = 2026-09-20.r4`.

| round | version | assertions passed | new calls | cost |
| :--- | :--- | ---: | ---: | ---: |
| 1 | `r2` | 90/103 | 23 | $0.00160 |
| 2 | `r3` | 97/103 | 23 | $0.00187 |
| 3 | `r4` | **101/103** | 10 *(13 from cache)* | $0.00088 |

**Both residual failures are the same case** — `found in faint-star QLP search; significant
centroid offset and depth aperture correlation; likely NEB`:
`mentions_instrumental_artifact` **0.39** (≤0.30 asserted) and `indicates_retired_or_rejected`
**0.31** (≤0.30 asserted). On reflection the second is the weaker half of the disagreement: in TFOP
practice *"likely NEB"* **is** a hedged rejection, and that is a `TIER_LABEL_ECHO` question whose
job is to capture exactly that echo.

**Accepted rather than reworded a fourth time.** Two boundary cases out of 103 do not justify
another rewrite, and rewriting to clear them would be fitting the questions to this 23-case set —
the overfitting the pre-registration exists to prevent.

### Operational notes
- **Per-row cost is up, not down.** 11 questions cost **2,077–2,109 input tokens per row**, against
  603–645 for 04's seven. `PLAN.md` §6's $0.072/$0.15 estimates are **low**; the measured
  projection is **$0.239** for 2,721 rows. The §5 writing rules — spell out cues, state the
  negative case, add `criteria.true`/`criteria.false` — are what raised the price, and they are
  what made the questions work.
- **Caching earned its keep unplanned.** Round 3 died mid-run on `http.client.RemoteDisconnected`
  (the retry loop caught only `HTTPError`). Because responses are content-addressed, 13 of 23 calls
  were already on disk and the re-run paid for 10. Re-running the finished gate costs **$0.00000**
  and returns an identical verdict.

---

## 7. What this does **not** establish

23 comments, no model fit, no ground truth beyond our own reading of each case. This tests
**question design**, not scientific validity. Nothing here addresses calibration, and the headline
question — *does note text add signal beyond the numeric columns?* — remains **completely open**.

**And this gate does not transfer.** It was run on the TOI `Comments` field. The project has since
switched to `download_obsnotes`, whose text is ~26× longer and differently written. Re-running
Step 2.5 on real observer-note text is a **binding precondition** of
[`PREREGISTRATION.md`](../PREREGISTRATION.md) §2 — because the lesson of §2 above is precisely
that a question verified on the wrong distribution tells you very little.
