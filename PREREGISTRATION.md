# ExoNotes — Pre-registration

> **Status:** committed **2026-09-20**, before any Jev run over any full corpus.
> **Registered by:** KevinArce · **Repository:** https://github.com/KevinArce/ExoNotes
> **Binds:** `PLAN.md` §7. This document fixes the criteria *before* results are seen.
> **Amendments:** this file is append-only below §11. Any change after the first full-corpus run
> must be recorded there with a timestamp and a reason, and the original text left intact.

---

## 0. The question this study asks

**Does free-text human annotation in an exoplanet archive carry predictive signal about a
candidate's eventual disposition, beyond what the numeric columns already say?**

Operationally: does adding Jev-derived features from ExoFOP observing notes improve a
CatBoost model over the same model trained on numeric covariates alone?

**The honest prior is that it does not.** Baseline B (numeric only) already scores **0.9154 AUC**,
leaving roughly 0.08 of headroom, and the corpus has ~1,700 independent host stars. This study is
designed to be *capable of returning a null*, and §9 commits to publishing that null.

---

## 1. Corpus — `download_obsnotes`, observer notes only

**Decision made by the project owner on 2026-09-20**, after the measurements in
`WORKLOG.md` 00:51Z and `PLAN.md` §2.2. The alternative — the TOI `Comments` field — is
**rejected** and the reasons are recorded here so the choice cannot be re-litigated after a result.

### 1.1 Definition

| | |
| :--- | :--- |
| **Source** | ExoFOP-TESS `download_obsnotes.php?tid=<TIC>`, via `etta.download_obsnotes(tic=...)` |
| **Unit of analysis** | one **TOI** row of `analysis_set` (label is per-TOI; notes are per-TIC) |
| **Text** | all notes for that TOI's TIC with **`Groupname != 'tfopwg'`**, HTML-stripped, whitespace-collapsed, concatenated in ascending `Lastmod` order |
| **Inclusion** | the TOI is labelled (§1.3) **and** its TIC has ≥ 1 observer note |
| **Exclusion** | TICs with no observer note (~33%, measured on 30 TIC) |

### 1.2 The `Groupname != 'tfopwg'` filter is the entire reason for this corpus

Measured on 30 TIC (15 per class), `research/data/obsnotes_recon_2026-09-19.json`:

- **`Master Disp: <value>` appears in 100% of TICs** (30/30). It is not a proxy for the label —
  it *is* the label, written out. Unfiltered, obsnotes is **strictly worse** than `Comments`
  (100% leakage vs 53.4%).
- Dropping `Groupname == 'tfopwg'` leaves **20/30 TIC (67%)** with a median of **2 notes** and
  **780 characters**, and **0 of those 20 contain any `Master Disp:` / `Phot Disp:` / `Spec Disp:`
  string**.

The disposition leakage goes from total to zero on one mechanical filter. `Comments` offers no
equivalent cut: there, annotation and observation are interleaved in a single field.

### 1.3 Label (unchanged from `PLAN.md` §3.3)

`CP`/`KP` → **1**. `FP`/`FA` → **0**. `PC`/`APC`/blank → **excluded**.
Source: NASA Exoplanet Archive `toi.tfopwg_disp`.

### 1.4 Projected scale, and the power cost of this choice — stated before the result

| | projected |
| :--- | ---: |
| TOI rows | **~1,814** (from 2,721) |
| unique TIC (CV groups) | **~1,715** (from 2,573) |
| median text per row | **~780 chars** (vs 30 in `Comments`) |
| acquisition | **~2.3 h** sequential, 2,573 TIC × 3.21 s, $0 API |
| Step 3 Jev cost | **~$0.18** at 11 questions |

**This corpus is ~33% smaller than `Comments` and it makes G2 harder, not easier.** Fewer groups
and the same ~0.08 of headroom above baseline B. That is accepted deliberately: a smaller corpus
of genuine observational prose is a better test of the hypothesis than a larger corpus of
disposition echoes. **The reduction is recorded here so that a null result cannot later be
explained away as "too few rows" — we knew.**

**The base rate of the observer-note subset is not yet known** and will not be known until the
full pull. Note count already correlates with the label (median 3 for y=1 vs 2 for y=0), so the
67% coverage is **probably not label-neutral**. The realised base rate will be reported as
measured, and it is **not** grounds to change any criterion below.

---

## 2. Question set — **PROVISIONAL, and why**

The current set is `QUESTION_SET_VERSION = "2026-09-20.r4"`, frozen in
[`src/exonotes/questions.py`](src/exonotes/questions.py), which scored **101/103 assertions on 23
real comments** in the Step 2.5 gate (`scripts/025_question_gate.py`, `research/05`).

> ### ⚠️ That gate was run on `Comments` text, and therefore does not transfer
> The 23 cases were drawn from the TOI `Comments` field: median 30 characters, terse fragments.
> Observer notes are **~26× longer**, multi-sentence, HTML-derived and written in a different
> register. `PLAN.md` §5 already records what happens when a question is verified on the wrong
> text distribution — it cost us `reports_offset_eclipsing_binary`, which passed at 0.870/0.070 on
> hand-written prose and was a **coin flip (0.26–0.57)** on real corpus text.
>
> **Binding requirement: Step 2.5 is re-run against real observer-note text, and the question set
> re-frozen with a new `QUESTION_SET_VERSION`, before Step 3 makes a single full-corpus call.**
> The set below is the *starting point* for that round, not the registered final set. §11 records
> the re-frozen version when it exists.
>
> **✅ DISCHARGED 2026-09-20. The re-frozen set is `2026-09-20.r6`, registered in §11.3 (A-18),
> and it supersedes the §2.1 and §2.2 tables below.** Six of the eight questions in §2.1 were
> retired on measured corpus prevalence (A-19); the set is now 7 predictive + 3 label-echo.
> Read §11.3 before §2.1.

### 2.1 `TIER_PREDICTIVE` — observational content (the headline result uses **only** these)

| ID | Type | Judgment |
| :--- | :--- | :--- |
| `reports_offset_eclipsing_binary` | Noul | An eclipsing binary placed on a star other than the target (`NEB`, `BEB`, contaminating star, stated separation). Bare `EB`/`SB1`/`SB2`/`SEB1`/`SEB2` → no. |
| `reports_stellar_companion_or_blend` | Noul | A second star in or near the aperture: companion, blend, dilution, crowded field, depth-aperture correlation. |
| `mentions_spectroscopic_binary` | Noul | Spectroscopic/RV binary evidence: `SB1`, `SB2`, `SEB1`, `SEB2`, double-lined, large RV variation. |
| `asserts_ephemeris_problem` | Noul | A **specific** defect in period or epoch. Affirming the ephemeris, even hedged, → no. |
| `mentions_instrumental_artifact` | Noul | Signal attributed to an instrumental/processing/solar-system cause. **A disposition is explicitly not such a cause.** |
| `describes_transit_morphology` | Noul | The event's own shape, depth behaviour, or duration. |
| `author_certainty` | Score 0–4 | Speculative → tentative → qualified → confident → definitive. |
| `evidence_depth` | Score 0–4 | None → remark/provenance → one observation → several → multiple independent facilities. |

### 2.2 `TIER_LABEL_ECHO` — may restate the disposition (**never** in the headline)

| ID | Type | Judgment |
| :--- | :--- | :--- |
| `indicates_retired_or_rejected` | Noul | States retirement/rejection/FP/FA. Describing a problem alone → no. |
| `indicates_confirmed_planet` | Noul | States confirmed/validated/published. A bare designation alone → no. |
| `contains_object_designation` | Noul | A planet or star catalogue designation. Instruments, surveys, groups, people, papers → no. |

Renamed from `references_other_object`: a bare *self*-designation is not "another" object, but it
**is** the P=0.999 leakage channel of §2.0, and the ID should say what it measures.

### 2.3 Two questions deleted on `Comments` — **to be reconsidered on obsnotes**

| ID | why deleted | status |
| :--- | :--- | :--- |
| `reports_on_target_detection` | 11/2,721 `Comments` rows matched, ~2 genuine | **restore as a candidate** |
| `indicates_followup_complete` | 2/2,721 matched, **0** genuine | **restore as a candidate** |

Both were deleted for **absence of support in `Comments`**, not for being bad questions. Observer
notes contain exactly this content — *"cleared 6/6 neighbors to 2.5'"*, *"No secondary sources
were detected"*, *"detected an on-time ~8 ppt transit"*. Re-test both in the re-run of §2.

### 2.4 Question-writing rules that bind the re-run

1. Ask what the text **says**, never what it **implies**.
2. Spell out any decisive qualifier with concrete cues, and **state the negative case explicitly**.
3. Name the inference to be avoided when the model keeps making it. *(This is what repaired
   `mentions_instrumental_artifact`: "a disposition is not an instrumental cause" moved `TFOP FP`
   from 0.65 to 0.07 where three rounds of describing the positive case better had not.)*
4. If a question needs inference, **delete it rather than reword it a third time**.
5. No arithmetic, counting, date ordering, or numeric comparison.
6. Pass/fail bands: Noul **≥ 0.70** for an asserted yes, **≤ 0.30** for an asserted no. Anything
   between is a **failure**, not a partial credit — a near-0.5 column is noise in the matrix.

---

## 3. Models

| | definition |
| :--- | :--- |
| **A** | prior only (predict the training base rate) |
| **B** | CatBoost on numeric covariates from NEA `toi` |
| **C** | TF-IDF + logistic regression on the raw text — **reported as a leakage upper bound, never as evidence** |
| **D** | CatBoost on numeric + `TIER_PREDICTIVE` Jev features — **the headline model** |
| **E** | CatBoost on numeric + all Jev features (both tiers) — reported as a contaminated upper bound |

`pscomppars` is **never** joined into any feature path (`PLAN.md` §3.2: P(y=1 | in) = 0.995).

State sent to Jev, fixed key order, nothing else:

```python
state = {"toi": str(row.toi), "notes": observer_notes_text}
```

---

## 4. Splits

### S1 — grouped cross-validation
`GroupKFold` on **TIC ID**, 5 folds × 3 repeats. Two planets around one star share a host and a
note record and must never straddle a fold.

### S2 — temporal
**Cutoff: `date_toi_alerted` < `2021-10-28` → train; ≥ → test. Fixed now, before any result.**

Chosen from the three measured options in `PLAN.md` §7 as the middle one: it leaves the largest
test set that still keeps ~75% of the data in training. Measured on the `Comments` analysis set:

| cutoff | train | test | % test | test base | train base |
| :--- | ---: | ---: | ---: | ---: | ---: |
| 2021-07-19 | 1,902 | 819 | 30.1% | 0.651 | 0.440 |
| **2021-10-28** | **2,040** | **681** | **25.0%** | **0.636** | **0.459** |
| 2022-01-25 | 2,160 | 561 | 20.6% | 0.635 | 0.469 |

**These sizes will differ on the obsnotes corpus.** They will be **re-measured and reported**, not
re-chosen. The date is fixed; the resulting split is whatever it is.

**Base-rate shift is expected and is the point:** 0.503 overall versus ~0.636 in the recent slice.
An S2 AUC is therefore **not** directly comparable to an S1 AUC, and neither is quoted as if it
were.

#### S2a — group leak, closed
**Defect found 2026-09-20** (`WORKLOG.md` 00:34Z): S1 forbids splitting within a host, and **S2 as
written in `PLAN.md` §7 violated that rule** — a TIC with two TOIs alerted on different dates lands
on both sides. At the 2021-10-28 cutoff, **30 TIC straddle the split, affecting 33 of 681 test
rows (4.8%)**.

**Resolution, pre-registered:** after applying the date cutoff, **drop from *test*** any row whose
`tic_id` also appears in train. Dropping from test, not train, keeps the temporal direction
honest — no training row may be newer than the cutoff.

#### S2b — note-level temporal filter (the payoff of this corpus)
For the S2 **training** side only, include a note **iff its `Lastmod` < the cutoff**. This
approximates the text as it stood when the candidate was young, which the `Comments` field made
impossible (§2.1: it has no field-level timestamp at all).

**Honest limitation:** `Lastmod` is *last-modified*, not *created*. A 2019 note edited in 2023 is
**dropped** by a 2021 cutoff. Dropping is the **safe** direction — it removes text that may
contain post-hoc knowledge — but it means S2b tests on *less* text, not on *older* text, and it
will be described that way in `RESULTS.md`.

---

## 5. Gate G5 — the leakage-stripped arm, exact regex

`PLAN.md` §7 requires the regex be fixed before the arm is run. `PLAN.md` §2.0's own headline
measurement was produced by a regex **that was never written down**, so it could not be
reproduced. This closes that.

**Authoritative implementation: [`src/exonotes/leakage.py`](src/exonotes/leakage.py).** If this
document and that file ever disagree, the file is the artifact that ran.

```python
CATALOGUE_PREFIX = (
    r"TOI|WASP|HATS|HAT-P|HAT|Kepler|K2|KOI|EPIC|HD|HIP|HR|GJ|Gliese|TYC|LHS|LTT|LP|"
    r"KELT|NGTS|CoRoT|XO|TrES|TRES|Qatar|Gaia|TRAPPIST|Wendelstein|OGLE2?-TR|MASCARA|"
    r"KPS|WTS|WD|NN|AU|DS|V|L|G")

L1_retired                    = r"(?i)retir"
L2_tfop_disposition           = r"(?i)tfop\s*(?:wg)?\s*[/-]?\s*(?:fp|fa|cp|kp)\b"
L3_confirmed                  = r"(?i)\b(?:validat\w*|confirmed planet|published|known planet)\b"
L4a_designation_catalogue     = r"(?i)^(?:CATALOGUE_PREFIX)[\s-]?\d+(?:-\d+)?[a-z]?(?:\s*[A-Z])?(?:\s*[b-h])?\s*(?:/.*)?$"
L4b_designation_planet_letter = r"^[^;,.]{1,22}\s[b-h]$"
```

A row is **excluded from the G5 arm** if any clause matches. Measured on the 2,721-row `Comments`
analysis set:

| clause | n | P(y=1) |
| :--- | ---: | ---: |
| L1 `retir` | 488 | 0.006 |
| L2 TFOP disposition | 543 | 0.006 |
| L3 confirmed/validated/published | 21 | 0.905 |
| L4a catalogue designation | 795 | **0.999** |
| L4b bare planet letter | 682 | **1.000** |
| **any** | **1,452 (53.4%)** | 0.566 |
| **G5 arm** | **1,269 rows · 1,222 TIC** | **0.431** |

L4b exists because L4a misses Bayer and white-dwarf forms (`pi Men c`, `55 Cnc e`, `DS Tuc A b`,
`WD 1856+534 b`). **Audited: L4b strips exactly 5 rows beyond L4a, all genuine designations, zero
false positives on prose.**

**Deviation from `PLAN.md` §7**, which predicted 1,417 rows / 1,312 TIC / 0.485. This strips ~5.5
points more. **Over-stripping is the correct direction:** a surviving leak lets G5 pass on label
echo, which is the one thing G5 exists to detect, and it cannot be detected after the fact.

### 5.1 Additional clause for the obsnotes corpus
```python
L5_explicit_disposition = r"(?i)\b(?:master|phot|spec)\s*disp\s*:"
```
Applied as belt-and-braces. It should never fire, because `Groupname != 'tfopwg'` already removes
every note containing it (**0/20 TIC in the recon sample**). **If L5 fires on any row, the corpus
filter has failed and Step 3 stops** — that is a pipeline bug, not a finding.

### 5.2 Note on the G5 arm's base rate
The arm runs at **0.431** where the full corpus is 0.503: stripping removes more positives than
negatives. **A G5 AUC is therefore not directly comparable to a G2 AUC**, and will not be
presented as if it were.

---

## 6. Gates — exact criteria, fixed now

| Gate | Criterion | Status |
| :--- | :--- | :--- |
| **G1** | Baseline B beats baseline A on AUC under S1. | ✅ **PASSED 2026-09-19 on the `Comments` set: B 0.9154 AUC / 0.1136 Brier vs A 0.5000 / 0.2501.** **Must be re-established on the obsnotes row set before Step 3** — a different row set is a different pipeline. Criterion for the re-run: **B ≥ 0.85 AUC and B > A by a bootstrap 95% CI excluding zero.** |
| **G2** | Model **D** beats Model **B** on **ΔAUC**, under **S1**, with a **bootstrap 95% CI (10,000 resamples, resampled over TIC groups) excluding zero**. | pending |
| **G3** | **Stability.** Re-run 200 rows with (a) paraphrased question wording and (b) permuted state key order. **Spearman ρ ≥ 0.85 per feature and mean \|Δp\| ≤ 0.05.** | pending |
| **G4** | The G2 gain survives on **`TIER_PREDICTIVE` only**, under **split S2**, CI excluding zero. | pending |
| **G5** | The G2 gain survives on the **leakage-stripped arm** of §5, CI excluding zero. | pending |
| **G6** | **Missingness ablation.** Re-fit B and D with explicit missingness indicators; the D−B gain must survive. Numeric missingness is label-correlated (`st_logg` non-null 0.829 for y=0 vs 0.991 for y=1; a missingness-only model scores **AUC 0.5869**). | pending |

**G2 is expected to be hard and that expectation is recorded before the run:** B sits at 0.9154
(0.9037 leakage-stripped), leaving ~0.08 of headroom, over ~1,715 groups. This is **not** a reason
to lower the bar. It is a reason to expect a null and to have said so first.

---

## 7. What counts as the headline result

**One number:** ΔAUC of **D − B** under **S1**, using **`TIER_PREDICTIVE` questions only**, with
its bootstrap 95% CI.

Reported alongside it, always, never instead of it:
- the **E − B** full-set gain, explicitly labelled leakage-contaminated;
- **baseline C**, explicitly labelled as leakage (0.9691 AUC on `Comments` — its top
  positive-pushing terms are catalogue prefixes and its top negative terms are `tfop`, `fp`,
  `retired`);
- the G5 arm result;
- the S2 result, with its base-rate shift stated.

---

## 8. Decision rule

| outcome | action |
| :--- | :--- |
| **All gates pass** | Report the positive result with all five caveats of §7. Proceed to `PLAN.md` §8 extensions. |
| **G1 fails** | Pipeline bug. Fix and rerun. Not a finding. |
| **G2 fails** | **Stop.** Write the negative result. **Do not add question rounds hoping for signal.** |
| **G3 fails** | **Report the instability as the finding.** That the features move under paraphrase is a real, publishable result about using this class of model in science. |
| **G4 fails** | The gain does not generalise to newer candidates, or lives only in the label-echo tier. **Negative result.** |
| **G5 fails** | **The effect was label echo.** Report as a negative result *and* as a finding about archive text: the signal was the annotation, not the observation. |
| **G6 fails** | The gain tracks missingness, not text. **Negative result.** |

### 8.1 A null result gets written up and published

**This is the part that makes the rest of the document mean anything.**

If ΔAUC is indistinguishable from zero, `RESULTS.md` is written and published with the same care
as a positive result would have been, stating plainly that **free-text ExoFOP observing notes add
no measurable predictive signal beyond the numeric columns**, with the confidence interval, the
power the study actually had, and every gate outcome.

A null here is genuinely informative: it would say that the numeric covariates already contain
what the notes contain, which is worth knowing before anyone else spends money pointing a language
model at an astronomical archive.

**No result changes this document.** Criteria are not revised after seeing data. If something here
turns out to be unimplementable — as `PLAN.md` §7's S2 split did, twice — the defect and its fix
are recorded in §11 and in `WORKLOG.md`, dated, with the original text left standing.

### 8.2 Things that will **not** be done
- No threshold tuning to make a gate pass.
- No swapping the headline from D to E, or from `TIER_PREDICTIVE` to the full set.
- No re-picking the S2 cutoff after seeing an S2 result.
- No dropping G3, G5 or G6 because they are inconvenient.
- No quoting baseline C's AUC without its leakage explanation.

---

## 9. Definition of done

1. `01_ingest.py` regenerates the snapshot from scratch, checksums recorded in `PROVENANCE.md`.
2. Observer notes pulled for all 2,573 TIC, cached, checksummed.
3. Step 2.5 re-run on obsnotes text; question set re-frozen with a new `QUESTION_SET_VERSION`.
4. G1 re-established on the obsnotes row set.
5. Step 3 run; every raw Jev response persisted, content-addressed.
6. G2–G6 evaluated exactly as written above.
7. `RESULTS.md` written — **whatever the answer is** — with reliability diagrams and CIs.
8. `WORKLOG.md` complete and append-only throughout.

---

## 10. Known limitations, recorded before the result

1. **`Lastmod` is last-modified, not created.** S2b drops edited notes rather than recovering
   their earlier text. No temporal control here is perfect.
2. **Note count correlates with the label** (median 3 for y=1 vs 2 for y=0). **No feature derived
   from note count, note length, or number of authors may enter any model.** Text content only.
3. **~33% of TICs have no observer note** and are excluded. The exclusion is probably not
   label-neutral. The realised base rate will be reported.
4. **Two questions in the r4 set carry known residual failures** on the `Comments` gate, both on
   one case (`found in faint-star QLP search; significant centroid offset and depth aperture
   correlation; likely NEB`): `mentions_instrumental_artifact` 0.39 where ≤0.30 was asserted, and
   `indicates_retired_or_rejected` 0.31 where ≤0.30 was asserted. Accepted rather than reworded a
   fourth time, to avoid fitting the questions to a 23-case set.
5. **Jev probabilities are quantised to two decimals**, producing tie groups. Harmless for
   features; it forecloses ranking without an explicit tiebreak.
6. **Jev calibration degrades out of distribution** (ECE 0.107 vs 0.024 floor). Jev output is used
   **only** as a feature into a validated model, never as a decision threshold, and `confidence`
   is never thresholded on.
7. **HTML stripping is lossy.** ~63% of notes carry markup; tables and links become plain text and
   some structure is lost.

---

## 11. Amendments

*(Append only. Each entry: date, what changed, why, and what it was before.)*

- **2026-09-20 — registered.** Initial commit of this document. No full-corpus Jev run has been
  made. Cumulative Jev spend to date: **~$0.0046**, all of it on the 23-case question-design gate.
- **PENDING — question set re-freeze.** §2 is provisional until Step 2.5 is re-run on observer-note
  text. The new `QUESTION_SET_VERSION` and its gate result will be recorded here **before** Step 3.

---

## 11.1 Amendments from audit 01 — 2026-09-20, before any full-corpus run

> All eight entries below were registered **before** TASK A, before the obsnotes corpus was
> pulled, and before a single full-corpus Jev call. No result has been seen. Every measurement
> cited is on the existing `Comments` `analysis_set`, on the 30-TIC recon sample, or on synthetic
> noise. Full reasoning: [`AUDIT_01_PREFLIGHT_REVIEW.md`](AUDIT_01_PREFLIGHT_REVIEW.md).
>
> **Where these amendments and the body text above disagree, these govern.**

### A-1 — Gate G2 gains a dilution control arm, **B+N**

**What changed.** A fourth arm is added and §6's G2 is read against it.

> **B+N** — baseline B plus *k* columns of i.i.d. `N(0, 1)` noise, where *k* is the final count of
> `TIER_PREDICTIVE` features, averaged over **5 noise seeds**. It is fitted, scored and
> bootstrapped exactly as D is.
>
> **ΔAUC(D − B) is reported against ΔAUC(B+N − B) as its zero point**, and both appear in
> `RESULTS.md` whenever either does.

**Why.** G2 as written had no zero point. Measured by
[`scripts/026_noise_floor.py`](scripts/026_noise_floor.py) at the projected obsnotes scale
(1,811 rows, 1,715 TIC, base 0.491), adding eight *known-worthless* columns to B costs:

| | |
| :--- | ---: |
| B (numeric only) | **0.9044** AUC |
| B + 8 pure-noise columns (mean of 5 seeds) | **0.8932** AUC |
| **dilution floor ΔAUC** | **−0.0112** |

Every one of the five seeds produced a paired bootstrap CI **excluding zero**. The penalty is
over 4× the SE of the G2 statistic (0.0026), and it is not a hyperparameter artifact: across five
CatBoost configurations it ranged −0.0100 to −0.0132, and **early stopping made it worse**.

Consequently a reported **ΔAUC ≈ 0.000 is not a null** — it is roughly +0.011 of genuine signal
cancelling dilution — and §8's decision table would have mapped that onto *"Stop. Write the
negative result."*

**What it was before.** §6: *"Model D beats Model B on ΔAUC … with a bootstrap 95% CI excluding
zero."* No reference arm. §8: ΔAUC ≈ 0 → G2 fails → publish the null.

**§8 decision table, as amended.** G2 passes when ΔAUC(D−B) exceeds ΔAUC(B+N−B) with a paired
bootstrap 95% CI on the difference excluding zero. If ΔAUC(D−B) lands between the dilution floor
and zero, that is **recorded and reported as an inconclusive result**, not as a null — the study
cannot distinguish it from dilution, and saying so is the honest outcome.

### A-2 — A minimum detectable effect is registered now; §8.1's observed power is withdrawn

**What changed.** The MDE below is fixed before the run. §8.1's commitment to report *"the power
the study actually had"* is **withdrawn and replaced** by: report the **registered MDE** and where
the observed CI fell relative to it.

| quantity, at the projected scale | value |
| :--- | ---: |
| SE of ΔAUC (paired, resampled over TIC groups) | **0.0026** |
| **MDE at 80% power, two-sided 95%** | **+0.0073** |
| net of the A-1 dilution floor, true signal required | **0.0186** |
| **univariate AUC a single Jev feature must reach to be visible** | **≈ 0.65** |

**Why.** Power computed after the fact from the observed effect is a monotone function of the
p-value and adds nothing to a CI that is already being reported. §9's promise to publish an
informative null is only meaningful against an effect size fixed in advance.

The 0.65 figure comes from a graded oracle (`scripts/026_noise_floor.py`): a synthetic text
feature with univariate AUC 0.592 is **invisible** to G2 (CI [−0.0019, +0.0053]); one at 0.653 is
detectable (CI [+0.0030, +0.0154]). **This is the bar the TASK B question set must be written
against.**

**What it was before.** No power calculation existed anywhere in the project. §8.1 planned to
report observed power.

**Re-measurement is required, not optional.** The dilution floor and the MDE are both functions of
*n*, and the ~1,715-TIC projection is 20/30 extrapolated (see A-8). `scripts/026_noise_floor.py`
is **re-run on the realised obsnotes row set** before Step 3, with `--k` set to the final feature
count, and the result recorded here.

### A-3 — §5's G5 clause set is re-derived on observer-note text before Step 3

**What changed.** §5's regex is **provisional on this corpus**, exactly as §2's question set is.
It is re-derived on the full pulled obsnotes corpus, measured per clause with n and P(y=1) as §5
does, audited by eye on the marginal rows, and **registered here before Step 3 makes a single
full-corpus call.**

**Why.** [`src/exonotes/leakage.py`](src/exonotes/leakage.py) was written for 30-character
`Comments` text and two of its five clauses are anchored `^…$`. Run against the 20 cached TICs
that survive the corpus filter:

| clause | fires |
| :--- | :--- |
| `L1_retired` | **0 / 20** |
| `L2_tfop_disposition` | **0 / 20** |
| `L3_confirmed` | 1 / 20 |
| `L4a_designation_catalogue` | **0 / 20** |
| `L4b_designation_planet_letter` | **0 / 20** |
| **any clause** | **1 / 20** |

The G5 arm would be ~95% identical to the full arm. **G5 would pass trivially**, and §8 reads a
G5 pass as *"the effect was not label echo"* — the one conclusion G5 exists to license.

The leak is real, with a different shape: `NEB`, `BEB`, `cleared`, `retired` and `false positive`
are all 0/20, so the `Groupname` filter genuinely works — but `TOI-\d+` fires **13/20**, and one
cached note opens *"Extracted KOI12 observing note from ExoFOP-Kepler."*

**What it was before.** §5 presented the clause set as fixed and measured, with §5.1 adding only
`L5_explicit_disposition`. `L5` remains the tripwire: **if it fires on any row, the corpus filter
has failed and Step 3 stops.**

### A-4 — `toi` is removed from the request state

**What changed.** §3's registered state becomes:

```python
state = {"notes": observer_notes_text}
```

**Why.** No question in `src/exonotes/questions.py` reads `toi`; all eleven are phrased *"Does
`comment` …"*. Meanwhile §5's entire apparatus excludes rows **whose text** carries a catalogue
designation — `L4a` at P(y=1) = 0.999, the strongest leakage channel in the corpus — while every
row's state was handing the model a catalogue designation **in a field the regex never reads**.
G5 cannot strip a channel that does not live in the text it strips.

**What it was before.** §3: `state = {"toi": str(row.toi), "notes": observer_notes_text}`, and
`scripts/025_question_gate.py` sending `{"toi": "TOI-624.01", "comment": ...}`.

### A-5 — The model is pinned; `jev-latest` is not reproducible

**What changed.** `MODEL = "jev-1.13.0"`. Every response's `model` field is asserted equal to it
before the response is persisted. The pinned version is part of this registration.

**Why.** `scripts/025_question_gate.py` used `MODEL = "jev-latest"`, and that literal string sits
inside the cache key `sha256(MODEL + QUESTION_SET_VERSION + state + questions)`. A version bump
would make cache hits serve old-model answers and cache misses new-model answers **under an
identical key**, silently mixing two models in one feature matrix. The cached responses already
record the resolved version (`"model": "jev-1.13.0"`); it simply was not used. The CI reproduction
does not cover this — it makes no API calls.

**What it was before.** `"jev-latest"`, unpinned, unasserted.

### A-6 — How ΔAUC aggregates across the S1 repeats, and that the bootstrap is paired

**What changed.** Registered, for every D-vs-B comparison including G2, G4, G5 and G6:

> **Pool out-of-fold predictions within a repeat; score each repeat; average the three repeat
> AUCs.** The bootstrap resamples **TIC groups** with replacement and recomputes that same
> average, using **the same resample for both models**.

**Why.** §6 specified "ΔAUC under S1, 10,000 resamples over TIC groups" but S1 is 5 folds × 3
repeats, and a mean of 15 per-fold AUCs, a single pooled AUC, and a mean of 3 per-repeat AUCs give
different intervals. Pairing is not optional: D and B share every numeric column, so an unpaired
bootstrap inflates the CI by the between-model covariance. Reference implementation:
`paired_group_bootstrap` in [`scripts/026_noise_floor.py`](scripts/026_noise_floor.py).

**What it was before.** Undefined. `scripts/02_baselines.py` averages 15 per-fold AUCs and reports
a `std` across folds, which is not a standard error.

### A-7 — A metadata control baseline, **B+meta**, is added

**What changed.** A fifth arm, reported alongside the headline:

> **B+meta** — baseline B plus **note count**, **total characters**, and an **author one-hot**.
> Zero API calls. **If D does not beat B+meta, the result is about how much follow-up a candidate
> received, not about what the prose says**, and `RESULTS.md` says so in those words.

Also reported: **B's AUC on the included versus excluded rows**, and the realised
P(has observer note | y = 1) vs P(has observer note | y = 0).

**Why.** §10.2 bans any feature derived from note count, length or author count — correctly, since
note count correlates with the label. But `evidence_depth` scores *"none → a remark → one
observation → several → multiple independent facilities"*, which is close to monotone in note
count and text length. The direct feature was banned and a semantic proxy for it was kept.

Separately, the exclusion is not merely a base-rate shift but a **collider**: follow-up effort
sits downstream of both the numeric properties and the disposition. The recon measures
P(note | y=1) = **0.80** vs P(note | y=0) = **0.53** (n=30), implying a subset base rate of ~0.60.
Conditioning on it can attenuate B and inflate the apparent text gain.

**What it was before.** §10.2 banned the direct features; no control arm existed, and §1.4 noted
only that the exclusion was "probably not label-neutral."

### A-8 — Three recorded limitations, added to §10

9. **The corpus-size projection is a point estimate from n = 30.** "~1,814 rows / ~1,715 TIC" is
   20/30 extrapolated linearly; the binomial interval is roughly **1,200–2,140 TIC**. Since the
   A-1 floor and the A-2 MDE are both functions of *n*, the low end materially changes the
   study's power. Both are re-measured on the realised row set (A-2).
10. **`Groupname != 'tfopwg'` is in practice `Groupname IS NULL`.** Across all 79 cached notes the
    field takes exactly two values: `'tfopwg'` (34) and NaN (45). There is no `SG1`-style
    groupname in the data. The filter works and selects genuine observer prose, but §1.1 describes
    a selection semantics the data does not have, and nothing asserts it. TASK A asserts the
    `Groupname` domain and stops if a third value appears.
11. **G3's Spearman criterion is undefined on low-variance features.** Jev returns two decimals
    (§10.5) and several nouls will sit near 0 or near 1 on nearly every row, so ρ is dominated by
    quantisation ties and can fail spuriously while `mean |Δp|` passes comfortably. Registered
    rule: **if a feature's inter-quartile range is below one quantisation step (0.01), G3 is
    judged on `mean |Δp| ≤ 0.05` alone for that feature, and the exemption is reported.**

### Recorded as tested-and-rejected — not amendments, but binding on future sessions

- **"Known Planets inflate baseline B."** Tested, false. B = 0.9128 on the full set, **0.9231 with
  `KP` excluded** (n=2,120, base 0.362), 0.9211 on KP-only positives. B is slightly *better*
  without them. **No KP-excluded arm is warranted**, and §0's pessimism about G2 is better founded
  than §0 itself argues.
- **The cross-platform 5×10⁻⁴ AUC offset.** Real, but the MDE is 0.0073 — roughly fifteen times
  larger. The single-platform rule for model-vs-model comparisons is kept as hygiene; the "ΔAUC
  below 10⁻³ is noise" figure is **retired as a decision rule**, because quoting it beside a ΔAUC
  invites a reader to think 2×10⁻³ means something.

---

## 11.2 Amendments from TASK A / TASK A2 — 2026-09-20, before any full-corpus Jev run

> Registered **after** the corpus was acquired and the baselines re-measured, and **before**
> TASK B writes a question or TASK C makes a single full-corpus call. No Jev feature has been
> computed on this corpus and no D-vs-B comparison has been seen. Cumulative Jev spend is
> unchanged at **~$0.0046**. Full detail: `WORKLOG.md` 2026-09-20T18:14Z and 18:34Z.
>
> **Where these and §11.1 or the body text disagree, these govern.**

### A-13 — The realised corpus, reported as measured

§1.4 projected ~1,814 rows / ~1,715 TIC. **Realised:**

| quantity | projected §1.4 | **realised** |
| :--- | ---: | ---: |
| TOI rows | ~1,814 | **1,482** |
| unique TIC (CV groups) | ~1,715 | **1,388** |
| base rate | not known in advance | **0.5378** |
| row coverage of `analysis_set` | ~0.67 | **0.545** |
| median characters per row | ~780 | **870** |

TIC count is **19.1% below** the projection and sits near the **low end of A-8's 1,200–2,140
binomial interval**. A-8's caveat was correct and is now load-bearing. §1.4's commitment stands:
this is **recorded before the result so that a null cannot later be explained away as "too few
rows" — we knew, and we knew the number.**

**A-10 holds.** `Groupname` takes exactly two values across all 6,855 notes: `'tfopwg'` (2,892)
and NULL (3,963). No third value. The filter is `Groupname IS NULL` in practice.

**§1.2 holds at full scale.** **0 of 1,482 rows** contain `Master Disp:` / `Phot Disp:` /
`Spec Disp:`. The recon measured 0/20; the `Groupname` filter removes the disposition channel
completely.

### A-14 — Gate G1 re-established on the obsnotes row set: **PASS**

A different row set is a different pipeline, so G1 was re-run against the registered criterion
(**B ≥ 0.85 AUC and B > A by a paired bootstrap 95% CI excluding zero**), using the A-6
aggregation and paired bootstrap.

| arm | n | TIC | base | A | B | B−A 95% CI |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| **CORPUS (obsnotes)** | 1,482 | 1,388 | 0.5378 | 0.4840 | **0.9051** | **[+0.3977, +0.4441]** |

`scripts/030_gate_g1_obsnotes.py`. Note that `scripts/02_baselines.py` tests only
`mean(B) > mean(A)` with a std across folds, which is not the registered criterion; G1 on this
corpus is established by the script above, not by that one.

### A-15 — The A-1 dilution floor and A-2 MDE, re-measured at the realised n

This supersedes A-2's table for every downstream decision. Required by A-2, not optional.

| quantity | registered at 1,715 TIC | **realised at 1,388 TIC** |
| :--- | ---: | ---: |
| B | 0.9044 | **0.9051** |
| **dilution floor ΔAUC(B+N − B)** | −0.0112 | **−0.0115** |
| **bootstrap SE of ΔAUC** | 0.0026 | **0.0030** |
| **MDE, 80% power, two-sided 95%** | +0.0073 | **+0.0084** |
| true signal required, net of the floor | 0.0186 | **0.0199** |
| **univariate AUC one Jev feature must reach** | ≈ 0.65 | **≈ 0.68** |

The floor is a property of model capacity and barely moved. **The SE grew 15% with the smaller
corpus, and the detection bar moved with it:** the graded-oracle arm at feature AUC **0.659 is
no longer detectable** (paired CI [−0.0009, +0.0121]), where it was at the projected scale.
**A question that would have cleared the old 0.65 bar no longer clears — TASK B is written
against 0.68.**

`--k 8` is **provisional**. A-2 requires this be re-run with `--k` equal to the final Jev
feature count once TASK B freezes the question set, and the result recorded here.

### A-16 — The selection effect is real but ~⅓ as strong as the recon estimated

**P(has observer note | y=1) = 0.5822** vs **P(has observer note | y=0) = 0.5067**, ratio
**1.149**. The recon measured 0.80 vs 0.53 (ratio 1.51) on n=30.

**A-7's read-across, measured:** B scores **0.9051 on the included rows vs 0.9197 on the
excluded rows (−0.0146)**. The included subset is marginally *harder* ground for B, so model D
is **not** being flattered by an easier comparison set. Per §1.4 and A-7 this is **reported,
not acted on**; no criterion changes. The **B+meta** arm registered in A-7 is still required at
TASK C.

### A-17 — Corpus text is entity-decoded; `src/exonotes/leakage.py` is unchanged

The registered text transform in §1.1 ("HTML-stripped, whitespace-collapsed") is extended to
**HTML-stripped, entity-decoded, whitespace-collapsed**. Measured cause: `&nbsp;` occurs 5,746
times across **1,061 of 1,482 rows (71.6%)**, and one note ends on an unterminated `<a
target="_blank"` that a `<[^>]+>` strip cannot match. Without this, Jev would have read raw
entity text on most of the corpus. Implementation and the load-bearing ordering constraint:
`plain()` in `scripts/028_obsnotes_pull.py`. The row set is **unchanged** at 1,482 / 1,388.

**Not amended here:** §5's clause set and `src/exonotes/leakage.py`. A-3 assigns that to TASK B2,
which must derive it on this corpus with the §5 eye-audit and register the result **before**
Step 3. Full-corpus probe rates are recorded in `WORKLOG.md` 18:34Z as a starting point only —
notably `TOI-\d+` fires on 68.4% of rows at P(y=1)=0.431, close to the 0.5378 base rate, while
`ExoFOP-Kepler` fires on 7.3% at **P(y=1)=0.954**. Audit 01's 20-TIC shapes do not survive
contact with the full corpus and **must not be carried forward unmeasured**.

---

## 11.3 Amendments from TASK B — 2026-09-20, before any full-corpus Jev run

> Registered **after** the Step 2.5 gate was re-run on real observer-note text and **before**
> TASK C makes a single full-corpus call. The only Jev calls made on this corpus are the 54
> gate calls recorded here; **no feature has been computed on the corpus, no D-vs-B comparison
> has been seen, and no G2–G6 number exists.** Cumulative Jev spend is **~$0.0144**.
> Full detail: `WORKLOG.md` 2026-09-20T19:14Z, 19:41Z and 19:58Z.
>
> **Where these and §11.2, §11.1 or the body text disagree, these govern.**

### A-18 — The question set is re-frozen at `2026-09-20.r6`

This discharges §2's binding precondition. `QUESTION_SET_VERSION = "2026-09-20.r6"`, frozen in
[`src/exonotes/questions.py`](src/exonotes/questions.py), **10 questions = 7 `TIER_PREDICTIVE`
+ 3 `TIER_LABEL_ECHO`**. §2.1 and §2.2's tables are **superseded** by this list.

| tier | ID | type |
| :--- | :--- | :--- |
| predictive | `imaging_reports_no_companion` | Noul |
| predictive | `imaging_reports_companion_present` | Noul |
| predictive | `spectroscopy_indicates_nonplanetary_companion` | Noul |
| predictive | `spectroscopy_consistent_with_planet` | Noul |
| predictive | `host_star_described_as_evolved` | Noul |
| predictive | `followup_reported_concluded` | Noul |
| predictive | `author_certainty` | Score 0–4 |
| label-echo | `indicates_retired_or_rejected` | Noul |
| label-echo | `indicates_confirmed_planet` | Noul |
| label-echo | `contains_object_designation` | Noul |

**Gate result: 219/221 assertions on 27 label-blinded real observer notes, 3 mid-band nouls**
(`scripts/032_question_gate_obsnotes.py`, raw in
`research/data/gate_obsnotes_2026-09-20.r6_2026-09-20.json`). Two rounds were run: r5 scored
212/221 with 12 mid-band, and five scoped repairs produced r6. **No question reached a third
wording**, so §2.4 rule 4 was not triggered. The two residual failures — B13
`indicates_confirmed_planet` 0.56 and B10 `spectroscopy_consistent_with_planet` 0.35 — are
**accepted, not reworked**, on the r4 precedent: rewriting to clear two boundary cases out of
221 would fit the questions to a 27-case set.

**The r6 decision rule was fixed in `WORKLOG.md` at 19:41Z, before the r6 call was made**, and
all five cases it named passed (B01 0.80, B02 0.77, B18 0.86, B19 0.84, B22 0.07).

### A-19 — Six r4 questions are retired on measured prevalence, and §2.3's two are resolved

Measured on all 1,482 rows before any question was written (`WORKLOG.md` 19:14Z). For a binary
feature, `AUC = 0.5 + (P(fires|y=1) − P(fires|y=0))/2` exactly.

| r4 question | subject matter in corpus | \|AUC\| | disposition |
| :--- | ---: | ---: | :--- |
| `mentions_instrumental_artifact` | **23 rows (1.6%)** | 0.504 | retired |
| `describes_transit_morphology` | 47 rows (3.2%) | 0.513 | retired |
| `reports_offset_eclipsing_binary` | 60 rows (4.0%) | 0.537 | retired; NEB/BEB folded into the spectroscopy question |
| `mentions_spectroscopic_binary` | 70 rows (4.7%) | 0.540 | retired; folded into `spectroscopy_indicates_nonplanetary_companion` |
| `asserts_ephemeris_problem` | 184 rows (12.4%) | 0.534 | retired |
| `reports_stellar_companion_or_blend` | 471 rows (31.8%) | 0.528 | superseded by the two **directional** imaging questions |
| `evidence_depth` | — | — | retired; see A-23 |

The `Comments` corpus was TFOP vetting shorthand; observer notes are reconnaissance-spectroscopy
and speckle-imaging reports, and the NEB/BEB vocabulary the r4 set was built around is nearly
absent. §2.3's two restored candidates are resolved: **`indicates_followup_complete` is revived**
as `followup_reported_concluded` (0.07% of `Comments` rows → **55.3%** here), and
**`reports_on_target_detection` is deleted** — restored as §2.3 required, tested, and across all
27 gate cases it never returned a clear positive (range 0.03–0.64, four cases mid-band). It is
deleted on measurement, not on assumption.

### A-20 — The A-1 floor and A-2 MDE, re-measured at the frozen k = 7

A-15 required this re-run once TASK B froze the feature count; `--k 8` there was provisional.
`scripts/026_noise_floor.py --table analysis_set_obsnotes --groups 0 --k 7`.

| quantity | A-15 (provisional k=8) | **registered (k=7)** |
| :--- | ---: | ---: |
| B | 0.9051 | **0.9051** |
| dilution floor ΔAUC(B+N − B) | −0.0115 | **−0.0105** |
| bootstrap SE of ΔAUC | 0.0030 | **0.0029** |
| **MDE, 80% power, two-sided 95%** | +0.0084 | **+0.0082** |
| true signal required, net of the floor | 0.0199 | **0.0187** |
| **univariate AUC one Jev feature must reach** | ≈ 0.68 | **≈ 0.68** |

Dropping one column bought back 0.0010 of dilution. **The detection bar is unchanged:** the
graded oracle is undetectable at feature AUC 0.659 (CI [−0.0009, +0.0121]) and detectable at
0.675 (CI [+0.0067, +0.0225]). These k=7 numbers are the registered ones;
`research/data/noise_floor_analysis_set_obsnotes_2026-09-20.json` and
`duckdb::noise_floor_obsnotes` now hold them, and A-15's k=8 values remain on the record here
and in `WORKLOG.md` 18:34Z.

### A-21 — TASK C's cost, re-projected from measured tokens; no truncation

§6's projection assumed ~780 characters per row. Fitted on the 27 gate calls:

> **`input_tokens = 0.4177 × chars + 3376`** (max residual 1,235 tokens over 27 calls)

which is **2.39 characters per token** — far denser than the usual ~4, because the text is
dominated by machine-written headers full of numbers and identifiers. Applied to the realised
corpus (1,482 rows, 1,898,624 chars):

| | |
| :--- | ---: |
| projected input tokens | **5,796,037** |
| **projected TASK C cost** | **$0.2434** |
| §6 tripwire | $0.50 — **does not fire** |

**No truncation is applied.** The longest row is 41,268 chars ≈ 20,613 tokens of state; the
limits are 64k per request and 32k for state plus the longest single question, so it fits with
room to spare. The 20 rows over 10k chars are 1.3% of the corpus and 3.9% of the tokens, so
truncating them would save ~$0.01 while silently changing what those rows say. The handoff's
"truncate or the tripwire will fire" was a cost worry; measured, it is unfounded.

### A-22 — The gate was label-blinded, and the handoff's "A-9" does not exist

`HANDOFF_PROMPT.md` cites "**Blind the cases (A-9)**", but §11.1 runs A-1…A-8 and §11.2 runs
A-13…A-17; **there is no A-9 in this registration.** The requirement is real — it is recorded in
`AUDIT_01_PREFLIGHT_REVIEW.md` and `WORKLOG.md` ("Question-gate cases must be label-blinded in
TASK B; the r4 cases carried `y=`") — and it is registered here under a number that exists.

**How it was discharged.** `scripts/031_gate_cases_obsnotes.py` selects cases programmatically
— 15 by length stratum, 12 by over-broad topic regex, fixed seed 20260920 — and emits a case
file that **contains no `y`**. Expectations were written from the text alone. `--unblind` was run
**once**, after every answer in both rounds had been inspected, and **no wording changed after
it**. The 27 cases are 16 positive / 11 negative. **Reported, not acted on**; 27 rows cannot
estimate an AUC, and selecting questions by their correlation with `y` is the overfitting this
document exists to prevent.

### A-23 — Metadata alone reaches 0.6817 AUC, so **B+meta is the arm to beat**, and a null is likely

A-7 added **B+meta** on the *suspicion* that `evidence_depth` was a semantic proxy for note
count. That suspicion is now measured, and it is far stronger than when it was registered.
A model built **only** from note metadata — no text content whatsoever — scores:

| metadata-only feature | \|AUC\| |
| :--- | ---: |
| `n_authors` | 0.609 |
| notes by `latham` (TRES recon) | 0.599 |
| notes by `everett` (speckle) | 0.586 |
| `n_notes_obs` | 0.571 |
| `n_chars` | 0.504 |
| **all six, grouped 5-fold OOF** | **0.6817** |

**0.6817 is the same ≈0.68 that A-20 says a single Jev feature must reach to be visible at all.**
Registered consequences, fixed now:

1. **`evidence_depth` is retired** (A-19). Scoring *"none → a remark → one observation → several
   → multiple independent facilities"* is close to monotone in note count, which §10.2 bans as a
   direct feature. Keeping the semantic proxy while banning the direct feature is not defensible
   now that the metadata arm is measured.
2. Every r6 question is written so its judgment is **not recoverable from who wrote the note,
   how many notes there are, or how long they are.**
3. **The honest prior, recorded before the result:** the best *content* signal measurable in this
   corpus by regex is **0.643** (imaging reports nothing found, 28.5% of rows), followed by
   evolved host **0.590** and a non-planetary spectroscopic conclusion **0.586**. **Not one
   content probe clears 0.68.** Jev can beat a crude token where the judgment is semantic, and
   the r6 questions are built exactly on those three signals — but **G2 failing is a live and
   expected outcome, and §8.1 already commits to publishing a null.** This paragraph exists so
   that a null cannot later be presented as a surprise, and so that a pass cannot be presented
   as though it had been the obvious expectation.

---

## 11.4 Amendments from TASK B2 — 2026-09-20, before any full-corpus Jev run

> The G5 clause set, re-derived on observer-note text as **A-3** requires, registered
> **before** Step 3. $0 of Jev spend; this is a regex measurement. Cumulative Jev spend is
> unchanged at **~$0.0144**. Detail: `WORKLOG.md` 2026-09-20T20:2xZ.
>
> **Where these and §11.3, §11.2, §11.1 or the body text disagree, these govern.**

### A-24 — §5's clause set is replaced for this corpus; the `Comments` set is inoperative here

A-3 said §5's regexes had to be re-derived on observer-note text. Run as-is on the obsnotes
corpus they are **nearly inert**:

| `Comments` clause | fires on obsnotes | P(y=1) |
| :--- | ---: | ---: |
| `L2_tfop_disposition` | **0** | — |
| `L4b_designation_planet_letter` | **0** | — |
| `L4a_designation_catalogue` | 1 | 1.000 |
| `L1_retired` | 17 | 0.235 |
| `L3_confirmed` | 101 | 0.891 |
| **any** | **118 (8.0%)** | 0.797 |

L4a and L4b are anchored to a comment that **is** a designation; an observer note never is.
`retired`/`TFOP FP` are the SG-shorthand of the `Comments` field and barely appear here.

**The registered set is `OBSNOTES_PATTERNS` in [`src/exonotes/leakage.py`](src/exonotes/leakage.py)**,
measured on all 1,482 rows (base 0.5378). "Marginal" is the number of rows that clause strips
**alone**, and is what the §5 eye audit was performed on.

| clause | n | % | P(y=1) | marginal |
| :--- | ---: | ---: | ---: | ---: |
| `L1_retired` | 17 | 1.1% | 0.235 | 10 |
| `L2_tfop_disposition` | 0 | — | — | 0 |
| `L3_confirmed` | 101 | 6.8% | 0.891 | 19 |
| `L4a_designation_catalogue` | 1 | 0.1% | 1.000 | 0 |
| `L4b_designation_planet_letter` | 0 | — | — | 0 |
| **`L5_explicit_disposition`** | **0** | — | — | 0 |
| **`L6_archive_provenance`** *(new)* | **231** | **15.6%** | **0.948** | 82 |
| **`L7_structured_disposition_field`** *(new)* | 136 | 9.2% | 0.941 | 0 |
| **`L8_status_line`** *(new)* | 97 | 6.5% | 0.866 | 53 |
| **`L9_disposition_transition`** *(new)* | 11 | 0.7% | 0.364 | 4 |
| **any (stripped)** | **368** | **24.8%** | **0.875** | |
| **G5 ARM** | **1,114 rows · 1,043 TIC** | **75.2%** | **0.426** | |

Three channels the `Comments` set had no clause for:
- **`L6`** — `Extracted KOI178 observing note from ExoFOP-Kepler on 2020-11-02`. 231 rows at
  **P(y=1) = 0.948**, the largest near-deterministic channel in this corpus.
- **`L7`** — the Kepler/K2 extracts carry structured fields: `Possible planetary candidate =
  Yes` (69 rows, P = 0.957), `Possible false positive = Yes`. This is the Kepler/K2 analogue
  of L5's `Master Disp:`.
- **`L8`** — the DACE/CORALIE notes carry a summary line: `Status: Solved by ESPRESSO-GTO
  (Sozzetti et al. 2021)`, `Status: WASP-72, Gillon et al. 2013`. 97 rows at P = 0.866.

**Eye audit, per §5.** `L1` (10 marginal): all genuine retirements. `L9` (4): all genuine
transitions (`PC => NEB`, `PC -> VPC`). `L3` (19): genuine, with a few future-tense
over-strips (*"Data will be published in Lillo-Box et al. (2014) in prep"*). **`L8` (53): mixed
— most carry the verdict, but some carry only an observation** (*"Status: No significant RV
variation …, SB2 ruled out"*), so L8 over-strips. Over-stripping is the direction §5 names as
correct, and it is recorded here rather than hidden.

**`L1_retired` behaves differently here than on `Comments`.** There it sat at P(y=1) = 0.006;
here it is **0.235**, because observer notes record positive-direction transitions too —
*"VPC -> VPC+ (and retired from SG1)"*. It is still a disposition echo and still stripped; it
is simply not a one-directional marker on this corpus.

### A-25 — `L6` strips on provenance, not on a disposition statement; the sensitivity arm is registered too

This is the one judgment call in the set, and it is recorded rather than buried. The 82 rows
`L6` strips alone **contain no disposition statement at all** — they read *"Extracted KOI178
observing note from ExoFOP-Kepler on 2020-11-02 Lick Recon: …"* and then ordinary imaging or
spectroscopy. So `L6` is not "label echo" in §2.0's sense: the text does not restate the
verdict. It is stripped because the **provenance string alone predicts the label at 0.948**, so
a model can score it without reading a single observation — which is the effect G5 exists to
rule out, whatever the form. §5's standing rule decides it: *"Over-stripping is the correct
direction: a surviving leak lets G5 pass on label echo, which is the one thing G5 exists to
detect, and it cannot be detected after the fact."*

**Both arms are registered now, before any result is seen:**

| arm | rows | TIC | base rate |
| :--- | ---: | ---: | ---: |
| **G5 (registered, with `L6`)** | **1,114** | **1,043** | **0.426** |
| sensitivity (without `L6`) | 1,196 | 1,122 | 0.463 |

The headline G5 number is the **with-`L6`** arm. The without-`L6` arm is reported alongside it,
and **a G5 verdict that flips between the two will be reported as such**, not resolved after the
fact by picking the arm that gives the better answer.

### A-26 — Three phrases that are NOT stripped, and why

Deliberately left in the G5 arm, because they are observational findings — exactly what model D
is supposed to be reading:

| phrase | n | P(y=1) | why it stays |
| :--- | ---: | ---: | :--- |
| `NEB` / `BEB` | 34 | 0.059 | an observation that a nearby star is the eclipsing source |
| `is an eclipsing binary` | 17 | 0.059 | a spectroscopic conclusion about the companion |
| `false positive` | 31 | **0.613** | **above** the 0.5378 base rate |

**`false positive` is the one audit 01 got wrong, and it is now measured at full scale.** The
phrase fires at P(y=1) = 0.613 — *above* base rate — because in observer notes it is usually
speculation (*"I wouldn't be surprised if this is a false positive"*) rather than a
disposition. Stripping it would remove more positives than negatives and would not remove a
leak. It stays.

### A-27 — The §5.1 tripwire holds: `L5` fires on 0 of 1,482 rows

`L5_explicit_disposition` (`(?i)\b(?:master|phot|spec)\s*disp\s*:`) fires on **zero** rows, so
the `Groupname` filter is removing the disposition channel completely, as §1.2 and A-13 both
record. **The tripwire is enforced in code:** `scripts/033_leakage_obsnotes.py` raises and
refuses to write its output if `L5` ever fires, with the message that this is a pipeline bug
and not a finding. Step 3 stops if it does.

---

## 11.5 TASK C results — 2026-09-20. **This section is written AFTER the result.**

> Everything above §11.5 was registered **before** any full-corpus Jev feature existed.
> This section records what happened. It changes **no criterion**; §11.3 and §11.4 fixed the
> question set, the clause set, the MDE and the arms, and all of it was committed and pushed
> (`4198379`) before `scripts/034_step3_features.py` made its first call.
> Cumulative Jev spend: **~$0.3201**.

### A-28 — All five gates pass. G2 ΔAUC = **+0.0440** [+0.0332, +0.0554]

n = 1,482 · TIC = 1,388 · base 0.5378 · S1 GroupKFold(5)×3 · paired bootstrap 10,000 over TIC
groups, A-6 aggregation. **B = 0.9044.**

| arm / gate | AUC | ΔAUC vs B | 95% CI | verdict |
| :--- | ---: | ---: | :--- | :--- |
| B+N — A-1 dilution floor | 0.8971 | −0.0073 | [−0.0133, −0.0014] | as registered |
| B+meta — A-7 control | 0.9256 | +0.0212 | [+0.0132, +0.0293] | metadata *does* add |
| **D — headline (G2)** | **0.9483** | **+0.0440** | **[+0.0332, +0.0554]** | **PASS** |
| **D vs B+meta** | 0.9483 | **+0.0228** | [+0.0133, +0.0329] | **survives A-23** |
| E — contaminated upper bound | 0.9523 | +0.0479 | [+0.0367, +0.0596] | reported, never headline |
| **G5 — registered, with L6** | 0.9323 | **+0.0394** | [+0.0272, +0.0523] | **PASS** (n=1,114, base 0.426) |
| **G5 — sensitivity, without L6** | 0.9341 | **+0.0421** | [+0.0303, +0.0547] | **does not flip** (n=1,196, base 0.463) |
| **G6 — missingness ablation** | 0.9472 | **+0.0425** | [+0.0316, +0.0540] | **PASS** |
| **G4 — S2 temporal** | 0.9136 | **+0.0927** | [+0.0608, +0.1264] | **PASS** (train 1,070 / test 390) |
| **G3 — stability** | — | — | — | **PASS**, 7/7 predictive |
| C — TF-IDF on raw text | **0.8766** | — | — | **below B** |

**The headline, as §7 defines it: ΔAUC(D − B) = +0.0440, 95% CI [+0.0332, +0.0554].** That is
**5.4×** the registered MDE of +0.0082 (A-20) and the CI clears the dilution floor of −0.0105
with a wide margin.

**G4's S2 split, as measured (§4 fixed the date, not the sizes):** train 1,070 / test 390
(26.3%), **22 test rows dropped by the S2a group-leak fix**, train base 0.4888 vs test base
0.6487. The base-rate shift is expected and **an S2 AUC is not comparable to an S1 AUC**.
**S2b (the note-level `Lastmod` filter) was NOT applied** — it requires recomputing every
training row's features on time-filtered text, a second full-corpus run. G4 is therefore the
S2 + S2a result, and that limitation is stated here rather than left implicit.

### A-29 — A-23's registered prior was WRONG, and the reason is specific

A-23 recorded, before the run, that no content probe cleared 0.68 and that **a null was the
expected outcome**. Four of the seven predictive features clear it:

| feature | regex proxy \|AUC\| (A-23) | **Jev \|AUC\|** | gain |
| :--- | ---: | ---: | ---: |
| `spectroscopy_indicates_nonplanetary_companion` | 0.586 | **0.748** | **+0.162** |
| `spectroscopy_consistent_with_planet` | 0.509 | **0.705** | **+0.196** |
| `host_star_described_as_evolved` | 0.590 | **0.696** | +0.106 |
| `imaging_reports_no_companion` | 0.643 | **0.687** | +0.044 |
| `followup_reported_concluded` | 0.613 | 0.648 | +0.035 |
| `imaging_reports_companion_present` | 0.528 | 0.637 | +0.109 |
| `author_certainty` | — | 0.578 | — |

**The error was in the estimator, not in the reasoning.** A-23 bounded the achievable signal
with regex proxies and explicitly flagged that a regex is a loose proxy for a judgment. That
caveat was right and larger than allowed for: **the semantic judgment beats the token by
0.10–0.20 AUC on the two spectroscopic questions.** A pre-registered prior was falsified in
public by the measurement it was written to constrain. Recorded here in full rather than
quietly dropped.

### A-30 — Why this is not the leakage signature, stated with the numbers

Three independent checks, each registered in advance:

1. **It survives the metadata control.** A-23's named worry was that the signal is really
   *which follow-up group wrote a note*. B+meta does reach 0.9256 — **metadata alone adds
   +0.0212** — and **D still beats B+meta by +0.0228, CI [+0.0133, +0.0329]**.
2. **It survives leakage stripping in both arms**, and **the verdict does not flip** between
   them, which A-25 committed to reporting either way.
3. **Baseline C = 0.8766, BELOW B = 0.9044.** On `Comments`, C was 0.9691 and was pure label
   echo. Here, raw text alone is *weaker than the numeric columns* — there is no readable label
   lying in the prose — yet structured judgments over that same text add +0.0440. **Whatever D
   is using, TF-IDF cannot find it.** That is the opposite of a leakage signature.

**What this does not establish.** That the gain is *astrophysically* meaningful, that it
generalises beyond TESS/ExoFOP observer notes, or that these features would help a vetter that
already ingests pixels and flux. §7's headline is one number on one corpus.

### A-31 — Reproducibility is weaker than `PLAN.md` §0.5 claims, and the exact claim is corrected

§0.5 says re-running a judging step "returns byte-identical results". **True only from a warm
cache.** Two identical requests — same pinned model, same state, same questions, verified by a
shared cache key — return:

| gap between the two calls | mean \|Δ\| | Spearman ρ |
| :--- | ---: | ---: |
| **minutes** (G3 repeat arm, 200 rows × 10 features) | **0.0001** | 0.996 – 1.000 |
| **~1 hour** (r6 gate vs Step 3, 27 cases × 10 features) | **0.0049** | — |

Within a session Jev is effectively deterministic; over about an hour it drifts slightly,
consistent with server-side variation rather than per-request sampling. **Consequences:**
- **A clean clone re-running Step 3 from a cold cache will not reproduce +0.0440 exactly.**
  `data/` is gitignored, so `data/cache/step3/` (1,382 responses) is **not** in the repository.
  The published numbers are reproducible *from that cache*, and approximately — not exactly —
  without it. `PROVENANCE.md` and `README.md` must say this in these terms.
- **No gate verdict is at risk.** The closest any CI comes to zero is G5's +0.0272, orders of
  magnitude beyond what a 0.005 feature perturbation could move.
- G3 is strengthened, not weakened: the paraphrase effect (0.0242) is **412×** the
  within-session noise floor, so G3 measures wording sensitivity rather than jitter.

### A-32 — G3's two failures are label-echo, and the threshold was NOT relaxed to clear them

`contains_object_designation` (ρ 0.814, mean |Δp| **0.0626** — fails both halves) and
`indicates_retired_or_rejected` (ρ 0.812, mean |Δp| 0.0096 — fails ρ only) do not meet the
registered criterion. Both are `TIER_LABEL_ECHO` and **never enter the headline** (§7).

**Both have IQR exactly 0.010**, so A-8 item 11's exemption — *"inter-quartile range below one
quantisation step (0.01)"* — misses on a strict reading of *below*. Changing `<` to `<=` after
seeing the numbers would turn both failures into passes. **That change has not been made.** The
criterion stands as registered and the failures are recorded as failures.

**G3(b), the permuted state key order, is vacuous:** A-4 reduced the state to the single key
`notes`, so there is no order to permute. §6 was written when the state had two keys.
`scripts/036_gate_g3_stability.py` asserts the state has exactly one key, so the test stops
being vacuous automatically if a future amendment adds one.

---

## 11.6 TASK D — the write-up. **This section is written AFTER the result.**

> `RESULTS.md` discharges §9 item 7, the last open item in the definition of done. Writing it
> required three measurements that did not exist, each of which turned a claim already in this
> document into a result or corrected it. No criterion changes. **No API calls were made:
> cumulative Jev spend is unchanged at ~$0.3201.**

### A-33 — A-31's "no gate verdict is at risk" is now measured, not argued

A-31 and `PROVENANCE.md` assert that the `jev-1.13.0` time drift cannot move a verdict, on the
argument that G5's +0.0272 lower bound is *"orders of magnitude beyond what a 0.005 feature
perturbation could move."* **That was an estimate.** The gates were never re-run from a cold
cache, so the map from a feature perturbation to a ΔAUC perturbation was never established.

`scripts/038_drift_sensitivity.py` establishes it with zero API calls: perturb all seven
`TIER_PREDICTIVE` columns by Gaussian noise scaled to the measured drift, clip to each
feature's range, re-quantise to the two decimals Jev returns (§10.5), re-fit D, recompute G2.

| simulated drift | realised mean \|Δ\| | draws | ΔAUC mean ± sd | worst draw | worst draw's 95% CI | G2 |
| :--- | ---: | ---: | :--- | ---: | :--- | :--- |
| **1× measured** (0.0049) | 0.0042 | 20 | **+0.0444 ± 0.0010** | +0.0417 | [+0.0308, +0.0530] | **PASS** |
| **10× measured** (0.0490) | 0.0385 | 10 | +0.0402 ± 0.0015 | +0.0384 | [+0.0280, +0.0495] | **PASS** |

The unperturbed reference reproduces the gate run exactly at +0.0440. **At the measured drift
the worst of 20 draws shifts ΔAUC by −0.0023, about a quarter of the MDE; at ten times the
measured drift G2 still passes.** A-31's conclusion stands and is now a measurement.

**What this arm is not, stated because it bounds the claim.** It is **not** a cold-cache
re-run — real server-side drift is whatever the serving fleet does and may be correlated
across rows or concentrated on hard cases, where this perturbs every row independently. It is
**not** a registered gate. And the realised perturbation lands ~14% below target at 1×, because
re-quantising to 0.01 rounds small perturbations back to zero, so the 1× arm is marginally
*weaker* than the drift it simulates. The 10× arm exists to cover that gap rather than to argue
it away.

### A-34 — §10 item 2's note-count medians do not describe this corpus; the measured values

§10 item 2 records *"note count correlates with the label (median 3 for y=1 vs 2 for y=0)"*.
That was measured on the `Comments` analysis set. **On the obsnotes corpus the medians are
equal**, and the effect lives in the tail:

| metadata feature | median y=1 vs y=0 | mean y=1 vs y=0 | univariate \|AUC\| |
| :--- | :--- | :--- | ---: |
| note count | **2 vs 2** | 3.44 vs 2.15 | 0.571 |
| number of authors | 1 vs 1 | 1.99 vs 1.26 | **0.609** |
| note length (chars) | 863 vs 879 | 1,527 vs 995 | 0.504 |

**The direction of the registered limitation holds and its prohibition is unaffected** — no
feature derived from note count, note length or number of authors enters any model, and the
B+meta control arm exists precisely to price them. But the medians quoted in §10 are not this
corpus's medians, and **number of authors is the stronger channel, not note count**. This is
what B+meta's +0.0212 is made of. Corrected here rather than left to be discovered by a reader
who runs the query.

### A-35 — The two values of baseline B in this repository are input row order

`scripts/030_gate_g1_obsnotes.py` reports **B = 0.9051**; `scripts/035_gates_g2_g6.py` reports
**B = 0.9044**, on the same 1,482 rows, same folds, same seed, same CatBoost configuration.
The only difference is that 035 reads the rows `order by a.toi` for the feature join.
`scripts/037_reliability.py` fits both orderings and **reproduces both numbers exactly**:
**CatBoost is sensitive to input row order, worth 0.0008 AUC here** — ~10× below the MDE.

No verdict moves, and no pairing is broken: every ΔAUC in this study is computed against the B
fitted on its own arm's row ordering and row set. **0.9051 is G1's B; 0.9044 is G2's.** Recorded
so the discrepancy is explained rather than noticed.

### A-36 — Two items of §9 and `PLAN.md` §9 that `RESULTS.md` reports as NOT done

1. **Per-question reliability diagrams (`PLAN.md` §9) were not produced.** There is no ground
   truth to plot them against: the per-question judgments are not independently labelled, and
   the only hand-labelled set is the **27-case** question-design gate — far too few for
   calibration bins. The gate's 219/221 assertions are an accuracy check, not a reliability
   diagram. Plotting the judgments against the *disposition* label instead would measure
   something else entirely and is not done. §9 item 7's "reliability diagrams" are delivered
   for **baselines B and D**, which is what that item asks for.
2. **S2b remains unapplied**, as A-28 already records. `RESULTS.md` §9 restates it rather than
   letting the write-up imply G4 is the registered split.

---

## 11.7 TASK E — S2b applied. **This section is written AFTER the result.**

> **This section supersedes A-36 item 2** (*"S2b remains unapplied"*), written earlier in the
> same session, and the A-28 sentence it rests on. Per §11's append-only rule neither is
> edited: they stood when written, and this is the entry that changes them.

### A-37 — §4's S2b is applied; G4 is now the registered split, and it PASSES

A-28 reported G4 as the **S2 + S2a** result and said so explicitly rather than leaving it
implicit: S2b — *"for the S2 **training** side only, include a note iff its `Lastmod` < the
cutoff"* — needed every changed training row's features recomputed on time-filtered text.
**That has now been done.** `scripts/039_gate_g4_s2b.py`, **203 new calls · 804,981 input
tokens · $0.0338** (cumulative Jev spend **~$0.3539**).

**2,865 of 3,963 observer notes (72.3%) survive the cutoff.** `Lastmod` is non-null on all
6,855 notes, so §4's undated-note branch does not arise on this corpus.

| arm | train | B | D | ΔAUC | 95% CI | |
| :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| G4 — S2 + S2a, as A-28 reported it | 1,070 | 0.8209 | 0.9136 | +0.0927 | [+0.0608, +0.1264] | reproduced exactly |
| **G4 — S2 + S2a + S2b, REGISTERED** | 884 | 0.8039 | **0.9250** | **+0.1211** | **[+0.0869, +0.1578]** | **PASS** |
| G4c — same 884 rows, unfiltered text | 884 | 0.8039 | 0.9115 | +0.1076 | [+0.0755, +0.1423] | **not a gate** |

Test side unchanged at **390 rows, base 0.6487**; train base 0.4888 → **0.4514**.

**Four decisions, fixed before the run** (`WORKLOG.md` 21:58Z, written before the first call):
1. **A row whose S2b text is empty leaves the training set.** §1.1 requires ≥1 observer note of
   non-zero length; 186 training rows no longer qualify, so training goes 1,070 → 884.
2. **B and D both train on those 884 rows.** Otherwise ΔAUC conflates the text filter with a
   sample-size change. **G4c prices that confound** and is reported for exactly that reason.
3. **The test side is untouched**, so G4 and G4b are directly comparable. Shrinking train can
   only shrink the train-TIC set, so S2a's fix stays valid on a fixed test set; re-running S2a
   would only add test rows back. Holding it fixed is the conservative direction.
4. **New responses cache to `data/cache/s2b/`, never to `data/cache/step3/`**, which
   `PROVENANCE.md` commits to at exactly 1,382 files. Verified after the run: **step3 1,382 ·
   s2b 203.** This is `WORKLOG.md` 21:31Z defect 1 inverted — there `s3.CACHE` was *not* patched
   and paraphrase responses leaked into `step3/`; here it is patched deliberately.

**The two effects separate cleanly, which is why G4c exists:**
- **Dropping the 186 rows** (G4 → G4c): B falls **−0.0170**, D falls **−0.0021**. ΔAUC rises
  because the numeric baseline suffers more from the smaller training set than the
  text-enriched model does — **not** because D improved.
- **The text filter itself** (G4c → G4): B identical, so the whole move is D, 0.9115 → 0.9250.

**That second step was tested directly and it is MARGINAL.** The two CIs overlap heavily, so
+0.0135 cannot be read off them. Paired bootstrap on the same 390 test rows — B identical in
both arms, so the difference in ΔAUC *is* D(S2b) − D(full) — gives **+0.0135, 95% CI
[+0.0006, +0.0269]**. It excludes zero, but barely, and **no section registered this comparison
in advance.**

**The claim that survives is the weaker one: training D on time-filtered text does not degrade
it.** The stronger reading — that older-only training text actively helps — is suggestive and
**is not established here**, and is recorded that way rather than as a finding.

**What S2b still does not control**, unchanged from §10 item 1: `Lastmod` is last-modified, not
created, so **S2b tests on *less* text, not on *older* text.** Dropping is the safe direction.

---

## 11.8 TASK D/E follow-up — a concurrency defect changed the published numbers. **Written AFTER the result.**

### A-38 — The Step 3 cache race made the feature matrix irreproducible; every number is restated

**The headline is +0.0432 [+0.0324, +0.0547], not the +0.0440 first registered in A-28.**

**Cause.** `scripts/034_step3_features.py` checked the cache at the top of `call()` and wrote at
the bottom, so two workers on the same state both missed and both called — **1,462 calls for
1,382 distinct states**. The ~$0.013 of waste was already on the record. What was not:

> For each of the **80 duplicated states**, `results[(tic, toi)]` kept **whichever response that
> row's own future returned**, while the cache file kept the **last** write. Those are two
> different responses, differing by the within-session drift A-31 measured at mean |Δ| ≈ 0.0001.
> **The persisted matrix was therefore a mixture of in-memory and on-disk responses, and was not
> reproducible from its own cache.**

**How it surfaced.** A per-key lock was added and Step 3 re-run **warm — 0 calls, $0.0000 — to
prove the change was harmless**, then the rebuilt matrix was checksummed against the stored one:
`c58de4de…` → `d7b5be56…`. A zero-call re-run changed the matrix. Re-run again: stable at
`d7b5be56…`. The lock removes the cause — one caller per state means the in-memory response and
the cache file are the same object by construction.

**Every arm was re-run on the cache-consistent matrix. No verdict moves.**

| arm | A-28 / A-37 as published | **cache-consistent** | shift |
| :--- | ---: | ---: | ---: |
| **G2 — headline** | +0.0440 | **+0.0432** [+0.0324, +0.0547] | **−0.0008** |
| D − B+meta | +0.0228 | +0.0220 [+0.0126, +0.0321] | −0.0008 |
| E − B | +0.0479 | +0.0482 [+0.0370, +0.0600] | +0.0003 |
| G5 registered (L6) | +0.0394 | +0.0391 [+0.0268, +0.0519] | −0.0003 |
| G5 sensitivity (no L6) | +0.0421 | +0.0426 [+0.0308, +0.0552] | +0.0005 |
| G6 | +0.0425 | +0.0425 [+0.0314, +0.0540] | −0.0000 |
| G4 — S2 + S2a | +0.0927 | +0.0936 [+0.0622, +0.1268] | +0.0010 |
| **G4 — S2 + S2a + S2b** | +0.1211 | **+0.1296** [+0.0948, +0.1670] | +0.0085 |
| B+N · B+meta · baseline C | — | unchanged | 0.0000 |

**Every S1 shift is ≤ 0.0010 — under one eighth of the MDE — and matches the A-33 drift arm's
sd of 0.0010, which is a useful check on that arm.** G2 is **5.3×** the MDE, not 5.4×.

**A-29 is unaffected in substance.** Re-measured univariate |AUC|: 0.749, 0.705, 0.695, 0.683,
0.648, 0.636, 0.579. **Four of seven still clear the ≈0.68 bar**, so A-23's prior is still
falsified and for the same reason.

**A-37's S2b numbers moved by +0.0085, eight times the S1 shift, and that has its own cause.**
**S2 is one train/test split and one CatBoost fit per arm**, where S1 averages 5 folds × 3
repeats. The paired bootstrap resamples *test groups*, not the fit. Measured over 10 CatBoost
seeds: G4 (S2+S2a) **+0.0954 ± 0.0044**, G4 (+S2b) **+0.1286 ± 0.0047**, G4c **+0.1091 ±
0.0050**. **An S2 ΔAUC carries ~±0.005 of seed noise, roughly 5× the S1 figure**, and S2 arms
closer than ~0.01 should not be separated on the point estimate alone.

**A-37's "marginal" finding is upgraded, and the upgrade is stated as such.** The S2b text
effect was +0.0135 [+0.0006, +0.0269] on the contaminated matrix; on the corrected one it is
**+0.0246 [+0.0115, +0.0383]**, and G4's worst seed (+0.1210) still clears G4c's best
(+0.1179). **It remains a post-hoc comparison that no section registered in advance**, and it
is still not a gate.

**The correction moves the headline down.** Recorded in full rather than as a footnote: a study
that publishes a falsified prior does not get to quietly round its own headline in its favour.

---

## 11.9 Post-study infrastructure — CI now covers the gates. **Written AFTER the result; changes no number.**

### A-39 — The gates run in CI against a live API key, and the assertions are criteria, not equalities

**`RESULTS.md` §9 item 5 recorded that CI did not cover the gates and "cannot without either an
API key in CI or the response cache committed — both are real decisions with real trade-offs,
neither has been made." The decision has now been made: an API key, in a GitHub Actions
secret.** `.github/workflows/gates.yml` runs the full pipeline from a cold cache and
`scripts/040_verify_gates.py` asserts every gate.

**This amendment changes no published number.** It adds infrastructure and records why it takes
the shape it does.

**Why the alternative was not merely a preference.** Committing the response cache could not
have worked on its own. `cache_key()` hashes `MODEL + QUESTION_SET_VERSION + state + questions`,
and the state is `{"notes": <raw ExoFOP text>}` read live from `analysis_set_obsnotes`. **A cache
hit therefore requires the note text to be byte-identical.** ExoFOP gains observing notes
continuously — the reason `029_verify_reproduction.py` has always asserted tolerances rather
than equality — so a committed cache would drift into misses and CI would silently begin paying
anyway. Making it work would have required freezing and committing **1.9 MB of ExoFOP note
text**, which collides with `README.md`'s statement that no archival data is redistributed here.
A third option — committing only derived numbers (the feature matrix and numeric columns, no
prose), which covers G2/G4/G5/G6 exactly for $0 but reaches neither G3 nor baseline C — was
offered and declined in favour of full coverage.

**What the choice costs, registered rather than discovered later.** ~$0.33 per cold run
(Step 3 ~$0.24 · G3 ~$0.06 · S2b ~$0.03); CI becomes dependent on a paid third-party API's
availability; and the workflow is deliberately **not** on `push`, because a paid job on push
turns a five-commit afternoon into $1.65.

**The assertions are registered criteria, not equalities, and this is a commitment.** A cold CI
run differs from publication in two independent ways, and only one is small:

| source | size | bounded? |
| :--- | :--- | :--- |
| **model drift** (A-31 → A-33) | ΔAUC sd **0.0010**; G2 survives 10× | yes, measured |
| **corpus drift** — ExoFOP is a living archive | **unbounded**; CI re-pulls different rows, different text, some changed dispositions | **no** |

Demanding +0.0432 exactly would therefore turn normal archive drift into a red build. The
verifier asserts what the study committed to in §6 — each gate's criterion — and **reports**
point estimates with their delta from publication. A delta beyond 5× the A-33 sd raises a
**NOTICE, not a failure**, because corpus drift can legitimately produce one and the correct
response is for a person to look, not for a badge to go red.

**One thing is demanded exactly: that the run actually paid.** On a runner the cache is cold by
construction (`data/` is gitignored), so Step 3 **must** make calls. `--require-paid` fails a
run reporting zero new calls, and the cost preflight aborts on a `$0.00` projection. Without
those, a pipeline that quietly did nothing would report six green gates — which is **defect 20**
(a G3 arm scoring ρ = 1.000 because it never made a call) and **defect 24** (a cached re-run
overwriting the record of the run that paid) in a new costume.

**The verifier is proven able to fail.** `scripts/041_test_verify_gates.py` breaks one claim at
a time — G2's CI crossing zero, G2 positive but under the MDE, G4/G5/G6 collapsing, G3 losing a
`TIER_PREDICTIVE` feature, B falling under 0.85, the A-1 dilution floor flipping positive, prose
ceasing to beat metadata, the corpus halving, a zero-call run, absent inputs — **15 mutations,
all caught.** It runs in CI **before** the paid steps, since there is nothing to learn from
paying to feed a check that cannot fail. This is `PLAN.md` §0.5's rule applied to the verifier
itself: **verify by checking the output, not by checking that it ran.**

**One earlier statement is superseded, and is left standing rather than rewritten.** A-5 (model
pinning) says "The CI reproduction does not cover this — it makes no API calls." That was true
of `reproduce.yml` and is **no longer true of the pipeline as a whole**: `gates.yml` runs Step 3
against the pinned `jev-1.13.0`, so a model-pin regression would now surface in CI. A-5 is a
record of what was registered when, so it keeps its original text; **§11.9 supersedes it**, on
the same append-only convention §11 states and §11.7 already used to supersede A-36 item 2
(later section wins: §11.9 > §11.8 > … > body text).

**What CI still does not establish.** It is one more run of *this* pipeline by *this* author.
It does not address the gap `RESULTS.md` §9 and the handoff both name as the highest-value one:
**nothing external has checked this.** A green badge is not independent replication and is not
offered as one.

### A-39a — The first run: all six gates pass from a cold cache, and the drift arm's prediction holds

**`gates.yml` ran for the first time on 2026-09-21
([35547134433](https://github.com/KevinArce/ExoNotes/actions/runs/35547134433)): `success`,
10.9 minutes, 1,382 new Jev calls, ~$0.32, 12/12 criteria, no notice raised.** Full table in
`RESULTS.md` §8a.

**This is the first true cold-cache end-to-end reproduction in the project's history**, and it
converts §8's central caveat from a prediction into a measurement. G2 came in at **+0.0451**
against the published **+0.0432**.

**The run separates three effects that had never been separated.** The corpus did not drift at
all — 1,482 / 1,388 / 0.5378, with both **numeric-only** arms (G1's B, baseline C) reproducing
to four decimals — so the movement cannot be attributed to ExoFOP. G2's B moved 0.0002 and uses
no Jev feature, which is the documented macos/arm64 vs linux/x64 offset. Everything remaining —
0.0009 to 0.0031, on every arm containing a Jev feature — is **model drift over ~28 hours**.

**A-33 is confirmed against reality.** It simulated the 1-hour drift and predicted ΔAUC sd
0.0010; at ~28 hours the observed shift is +0.0019, about 2× that, and far inside the 10× band
where G2 still passed. A robustness arm built for a question nobody had yet posed answered it
correctly when it was finally posed.

**The headline remains +0.0432 and this amendment does not change it.** The cold run landed
**higher**, which is the direction that flatters the study, and is exactly why it is being
refused as a re-measurement: §11.8 recorded a correction that moved the headline *down* by
0.0008 and declined to round it away. **+0.0451 is drift at 28 hours, not a better result.**
A reproduction check asks whether a finding survives; it does not restate it.

**Three operational facts, none of which local testing could have established.** The pinned
`requirements.txt` installs clean on linux/x64 Python 3.14.7. A cold ExoFOP pull of 2,573 TIC
completes in ~2.5 minutes from a GitHub IP with zero failures — the throttling that forced the
`reproduce` workflow into existence did not recur. And **the A-38 per-key lock holds under real
concurrency on different hardware: 1,382 calls for 1,382 distinct states, none failed**, where
the defective version made 1,462 for the same 1,382.

**Two registered failures reproduced as failures**, which is the correct outcome: G3's
`indicates_retired_or_rejected` (ρ 0.806) and `contains_object_designation` (ρ 0.801) both still
fail, and A-8 item 11's threshold was not relaxed to clear them (A-32).

**Unchanged by any of this:** nothing external has checked the result. A green badge is this
pipeline checking itself on borrowed hardware.

---

## 11.10 Kepler cross-mission validation. **Written 2026-09-21, BEFORE any Kepler model call.**

This section registers a **second, separate study** — `PLAN.md` §8 item 2 — and changes **no**
TESS number. §0–§11.9 stand as written for TESS. Where a Kepler rule differs from its TESS
counterpart, the difference and its reason are stated here. Every number below was measured with
**zero model calls**; the Kepler question set does not yet exist.

### A-40 — The Kepler transfer test: corpus, label, arms, gates, MDE, and what counts as failing to transfer

#### 40.0 How the corpus was arrived at — including one that was withdrawn

`PLAN.md` §8 named the **Kepler Certified False Positive table** (`fpwg_comment`). It was
obtained (not served by TAP or the legacy API; replayed through the archive viewer's own download
path, `scripts/042_kepler_fpwg_pull.py`), a corpus was **defined and fixed in `WORKLOG.md` before
any label was joined** — commented KOIs, y from cumulative `koi_disposition` — and its zero-cost
baselines were measured (`scripts/043`, `044 --corpus fpwg`):

| FPWG corpus, n = 1,993, base 0.0672 | AUC / ΔAUC |
| :--- | :--- |
| B (8 covariates) | 0.9084 |
| **C — TF-IDF on the comment ALONE** | **0.9662 — above every covariate** |
| B + one-hot FPWG verdict (diagnostic ceiling) | **+0.0740** over B — 5× that corpus's MDE of +0.0141 |
| FPWG verdict vs the join label | agree on **1,956 of 1,993 rows (98.1%)** |

**It is withdrawn as the transfer test and will not be run.** `fpwg_comment` is written by the
FPWG *about its own certification* — the Kepler analogue of the `tfopwg` notes that §1.2 excluded
from TESS, not of the observer notes it kept — and the numbers show the consequence: a transfer
test on it **could not come out negative.** Any D that reads those comments clears the MDE.

**The replacement was found by checking, not assumed.** ExoFOP's `cfop.php` now redirects to the
unified ExoFOP, and the **Kepler Community Follow-up Observing Program's observer notes were
migrated into the same `download_obsnotes.php` dump the TESS study uses**, each prefixed
`Extracted KOI<n> observing note from ExoFOP-Kepler on 2020-11-02`. That is the like-for-like
corpus: follow-up observers' notes, with the disposition made elsewhere.

**Forking-paths disclosure, stated plainly.** The switch was made **after seeing the FPWG
corpus's baselines** — not after seeing any *outcome*: no Jev call has been made on either
corpus. The reason is a measured validity property (text alone beats the covariates; the verdict
ceiling is 5× the MDE), not an effect size, and both decisions were the project owner's, recorded
in `WORKLOG.md` with the rejected alternatives. The CFOP definition below copies §1.1/§1.3,
leaving almost no free choices, and **was fixed in `WORKLOG.md` before any CFOP label was
joined.** A reader who discounts the result for the switch has the whole record to do it with.

#### 40.1 Corpus — CFOP observer notes

| | |
| :--- | :--- |
| **Source** | ExoFOP `download_obsnotes.php?output=pipe`, bulk; parsed by `028`'s `parse_pipe` and cleaned by `028`'s `plain`, **imported unchanged** (`scripts/045_kepler_cfop_corpus.py`) |
| **Notes in scope** | cleaned text begins with `Extracted KOI<n> observing note from ExoFOP-Kepler on <date>`. **Out of scope:** K2 notes, unprefixed notes, and every TESS-era note on the same star |
| **`Groupname`** | must be empty on every in-scope note — **asserted; a non-empty value stops the build** (A-10's role) |
| **Text** | the host's in-scope notes, **prefix stripped**, joined by one space in ascending `Lastmod`, ties by note `ID` (§1.1's order) |
| **Unit** | one KOI (`kepoi_name`); per-host notes are attached to **every** KOI of that host, as §1.1 attached per-TIC notes to every TOI |
| **Inclusion** | labelled (40.2) **and** ≥ 1 non-empty in-scope note |
| **Groups** | `kepid` (host star). Every KOI host maps to exactly one TIC and one `kepid` — asserted |
| **Power floor** | minority class < 100 → **stop, no model call** (fixed before n was known) |

**Realised, measured before any model call:**

| | CFOP | TESS (A-13) |
| :--- | ---: | ---: |
| in-scope notes / hosts / authors | 14,980 / 4,977 / 66 | — |
| **n** | **4,720** | 1,482 |
| y = 1 / y = 0 | 2,714 / 2,006 | — |
| **base rate** | **0.5750** | 0.5378 |
| groups | 3,843 `kepid`; 586 multi-KOI; max 7 | 1,388 TIC |
| median chars / notes / authors, y=0 vs y=1 | 115 vs 370 · 2 vs 3 · **1 vs 3** | — |

**Parse verified two independent ways over the same bytes:** `parse_pipe` and a record-anchored
regex agree on **33,132 records, the same IDs, and identical note text on all 33,132.**

**Checksums** — `kepler_cfop_corpus` sha256(to_csv)[:16] **`f3c30d2daf460095`**; obsnotes bulk
dump (2026-09-21T02:44Z) **`475fc5dcafd43574`**; cumulative snapshot (02:23Z)
**`962947427b3038a3`**. All in `data/kepler.duckdb` / `data/kepler/`, **a separate database from
TESS** — `data/exonotes.duckdb` is never opened for write (matrix checksum re-verified
`d7b5be5675778f44` after the Kepler pulls).

#### 40.2 Label

Cumulative KOI table, `koi_disposition`: **CONFIRMED → 1, FALSE POSITIVE → 0**; CANDIDATE and NOT
DISPOSITIONED excluded (1,514 CANDIDATE KOIs with notes are out), as §1.3 excluded PC/APC. Per
the archive's column documentation, **CONFIRMED is taken from the Confirmed Planet table (the
literature)** and **FALSE POSITIVE from `koi_pdisposition`, the Kepler pipeline's disposition** —
so the disposition is made **by neither the notes' authors nor from the notes themselves**, the
§1 structure.

#### 40.3 Excluded sources — named, so the easy path is closed in writing

**`koi_comment` is excluded** from the text, from every baseline and from every feature. The
archive documents it as *"a description of the reason why an object's disposition has been given
as false positive"*, and it is `---`-delimited Robovetter codes (`MOD_SEC_DV---HAS_SEC_TCE`), so:
(i) it **is** the vetting rationale — `Comments`-field leakage, more direct; and (ii) it is an
enumerable categorical, so one-hot is exact and "structured judgments vs bag-of-words" becomes
untestable. It is in TAP and easy to get; that is why it is named here.

Also excluded, and **never pulled** by `043`/`045`: `koi_disposition` itself (label only),
`koi_pdisposition`, `koi_score`, `koi_disp_prov`, every `koi_fpflag_*`; and **every `fpwg_*`
field, `fpwg_comment` included** — the corpora are not mixed.

#### 40.4 Models

| | definition |
| :--- | :--- |
| **A** | prior only |
| **B** | CatBoost (`026`'s `CB`, unchanged) on `koi_period, koi_depth, koi_duration, koi_prad, koi_kepmag, koi_steff, koi_srad, koi_slogg` — TESS B, column for column |
| **B+meta** | B + note count, total characters, author count, top-8 author one-hot — **A-7 exactly** |
| **B+N** | B + k pure-noise columns — the A-1 dilution floor |
| **C** | TF-IDF + logistic on the text — reported, **never evidence** |
| **D** | B + Kepler `TIER_PREDICTIVE` Jev features — **the headline model** |
| **E** | B + all Kepler Jev features — reported as contaminated |

**State:** `{"notes": cfop_text}` — A-4's form; no KOI or TIC identifier. **Model:** `jev-1.13.0`,
the TESS pin (A-5), asserted per response; drift is A-33's, and is not re-litigated here. Note
count, length and author count **never enter D** (§10.2, A-7) — only B+meta.

#### 40.5 Splits

- **S1:** `GroupKFold` on `kepid`, 5 folds × 3 repeats, seed 20260919, A-6 aggregation, paired
  bootstrap 10,000 over `kepid` — `026`'s machinery imported unchanged.
- **S2 (temporal):** KOI numbers are assigned in order of identification, so the **KOI host
  number is Kepler's "alerted later"**. **Test = rows with host number ≥ 3865**, the 75th
  percentile of host number over corpus rows — the rule mirrors §4's 25.0% test share; the
  number is what the rule gives, and the realised split will be **reported, not re-chosen.**
- **S2a** holds by construction: the split is on the host, which cannot straddle.
- **S2b is not applicable and is not improvised:** it needs a date cutoff, and a host-number
  split has none. Recorded as a difference from TESS, not a gap to be filled after the result.

#### 40.6 The G5 clause set for Kepler — registered by rule now, audited in A-41

`KEPLER_PATTERNS` = **`OBSNOTES_PATTERNS` (A-24) with `L6` removed, plus one clause:**

- **`L6_archive_provenance` is removed.** It exists because, on TESS, *being a Kepler/K2 star*
  predicted the label at 0.948 (A-25). **On CFOP every row has that provenance**, so it cannot
  discriminate — and its `\bKOI[\s-]?\d` alternative would strip nearly every row, because the
  notes name their target (*"Robo-AO imaging of KOI-4774"*).
- **`K10_kepler_designation` = `\bKepler-\d+` is added.** A `Kepler-N` system name exists only
  once a planet in the system is confirmed or validated — `L4a`'s role, un-anchored because an
  observer note is never *just* a designation (A-24).
- **`L7_structured_disposition_field` is kept unchanged** — it is the Kepler/K2 analogue of
  `Master Disp:` (A-24: `Possible planetary candidate = Yes`, P = 0.957 on TESS). On CFOP it also
  fires on `Possible nearby companion = Yes (…)`, which is an **observation**; **it still
  strips**, per §5's rule that over-stripping is the correct direction.
- **`L5` stays the tripwire:** it must fire on zero rows, or the build stops.

**Two arms, both registered now, as A-25 did for `L6`:** the headline G5 is **with `L7`**; a
**without-`L7`** sensitivity arm is reported beside it; **a verdict that flips between them is
reported as such.** A-41 measures every clause's count, P(y=1) and marginal rows, with an eye
audit. **A-41 may ADD clauses, never remove one** — the only direction that cannot manufacture a
pass.

#### 40.7 Gates — exact criteria, fixed now

| gate | criterion | status |
| :--- | :--- | :--- |
| **KG1** | B ≥ 0.85 AUC under S1, group-bootstrap CI above 0.5 | ✅ **PASS, measured pre-Jev: 0.9582 [0.9524, 0.9638]** |
| **KG2** | **D − B**, S1, `TIER_PREDICTIVE` only, paired bootstrap 10,000 over `kepid`: **CI excludes zero** | pending |
| **KG3** | 200 rows, paraphrased question wording: **Spearman ρ ≥ 0.85 per feature and mean \|Δp\| ≤ 0.05**. §6's key-order permutation is vacuous with a one-key state (as on TESS) and is not run | pending |
| **KG4** | D − B under **S2**, CI excludes zero | pending |
| **KG5** | D − B on the **with-`L7`** `KEPLER_PATTERNS`-stripped arm, CI excludes zero | pending |
| **KG6** | D − B survives explicit missingness indicators on B and D, CI excludes zero | pending |

#### 40.8 Minimum detectable effect — measured, and k-dependent by rule

`scripts/044_kepler_step2.py --corpus cfop`, k = 7 × 5 seeds, zero model calls:

| | CFOP | TESS |
| :--- | ---: | ---: |
| B | 0.9582 | 0.9051 |
| **B+meta** | **0.9839 (+0.0257 [+0.0208, +0.0306])** | +0.0212 |
| C (TF-IDF, text only) | **0.9429 — below B** | 0.8766 — below B |
| dilution floor (B+N) | −0.0044 | ≈ −0.011 |
| bootstrap SE of ΔAUC | 0.0007 | — |
| **MDE (80%)** | **+0.0021** | **+0.0082** |
| single-feature AUC bar (oracle) | ≳ 0.66 | ≈ 0.68 |

**The MDE is a function of k.** A-41 re-runs `044 --corpus cfop --k <frozen k>`, and **that
output is the registered MDE** — mechanical, no discretion.

#### 40.9 What counts as the effect transferring — decided before the run

**TRANSFERS** requires **all four**:
1. **KG2 passes, and its point estimate ≥ the registered MDE.** A CI that excludes zero on an
   effect below the MDE is reported as *"detected, below the registered MDE"* — not as transfer.
2. **D beats B+meta**, paired CI excluding zero — A-7's rule. On TESS it did (+0.0220).
3. **KG5 passes** (with-`L7` arm).
4. **KG6 passes.**

| outcome | reading, fixed now |
| :--- | :--- |
| all four hold | **Transfers.** Structured reading of follow-up observers' notes adds signal beyond the covariates *and* beyond follow-up volume, on a second mission, era and observer community. A full paper becomes reasonable. |
| KG2 CI includes zero, or its point estimate < MDE | **Does not transfer.** A real negative result: the TESS effect is specific to ExoFOP-TESS, and the framing becomes *"beware: this does not transfer."* |
| KG2 holds, D does **not** beat B+meta | **Transfers only as follow-up volume.** On Kepler the prose adds nothing beyond how much follow-up a KOI received; since TESS D *did* beat B+meta, **the content claim does not transfer.** Negative for the claim that matters. |
| KG2 holds, **KG5 fails** | **Label echo on Kepler.** Negative, as §8. |
| KG2 holds, **KG6 fails** | Tracks missingness. Negative, as §8. |
| all four hold, **KG4 fails** | **Qualified transfer:** holds under S1, not for later-identified KOIs. Reported with that qualifier in the first sentence. |
| **KG3 fails** | The instability is the finding, as §8. |
| KG1 fails | Pipeline bug (it has already passed). |

**Magnitude is not a criterion.** B is higher here (0.958 vs 0.905), so headroom is 0.042 vs
0.095. **Share of headroom captured, (D − B)/(1 − B)** — TESS: 0.0432 / 0.0949 = **0.455** — is
reported as a description, never as a gate. Matching +0.0432 is not expected and not required.

#### 40.10 The honest prior, recorded before the result

**A null is a live outcome and §8.1's commitment to publish it applies unchanged.** Three
reasons, each measured:
1. **B+meta leaves 0.016 of headroom.** Follow-up volume alone is worth +0.0257 here — *more*
   than on TESS — and criterion 2 requires D to beat it.
2. **CFOP content is narrower than TESS obsnotes.** The most common openings are templated
   imaging reports — `Possible nearby companion = Yes (…)` ×2,169, Robo-AO *"No companions
   detected"* ×~2,440 — with far less of the spectroscopic prose TESS's strongest questions
   read. And **`L7` strips the flag notes from the G5 arm**, so KG5 will run on less text.
3. **C is below B**, as on TESS — so there is no easy textual shortcut to the label, which is
   what makes this a test. It also means nothing here guarantees a gain.

#### 40.11 Deferred to A-41 — which must be committed and pushed before the first paid call

1. **The Kepler question set, under a NEW version string** — never an edit to `2026-09-20.r6`,
   which stays frozen for TESS — designed against CFOP text, through a label-blinded
   question-design gate (A-22's form, ~$0.06).
2. **`KEPLER_PATTERNS` per-clause counts, P(y=1), marginal rows and eye audit** (40.6).
3. **The MDE at the frozen k** (40.8).
4. **The realised S2 sizes and base rates** (40.5).
5. **A cost projection from measured tokens** (A-21's form).

**None of these may change 40.1–40.10.** A-41 fills in what 40 leaves open; it does not revise it.

#### 40.12 Limitations recorded before the result

1. **Post-disposition follow-up cannot be filtered.** Confirmed KOIs plausibly drew follow-up
   *after* validation, and the cumulative table gives no per-KOI disposition date, so S2b's
   note-level filter has no Kepler analogue. `L3_confirmed` strips notes that *say*
   validated/confirmed/published; **D vs B+meta** is the registered defence against volume; the
   rest is a stated limitation.
2. **The two label classes come from different processes** — FALSE POSITIVE from the pipeline
   (light curves), CONFIRMED from the literature, which often used exactly this imaging (e.g.
   statistical validation). That is the §1 structure — notes feed a disposition made elsewhere —
   but it means the notes may be *inputs* to the positive label more directly than to the
   negative one.
3. **Multi-KOI hosts share one text** (586 groups) across KOIs that can carry different labels —
   as on TESS; S1 keeps them in one fold.
4. **The corpus is heavily templated**, and its migration date (2020-11-02) is a single constant
   — stripped with the prefix, so it cannot act as a feature.
5. **A corpus was withdrawn before this one was chosen** (40.0).

### A-41 — What A-40 left open, filled in before the Step 5 run: the frozen question set, the G5 audit, the MDE at k = 6, S2, cost, and the analysis code

**Written 2026-09-21, BEFORE the Step 5 run — the first full-corpus Kepler model call.** It fills
in 40.11's five items and changes **none** of 40.1–40.10. Between A-40 and this amendment the only
Kepler model calls were the question-design gate's (41.1).

**41.0 — "First paid call" in 40.11 means the Step 5 run.** 40.11 also lists a ~$0.06
question-design gate among A-41's contents; its calls necessarily come before A-41, because they
are how the question set frozen here was chosen — as TASK B's gate preceded A-18 on TESS.

#### 41.1 The question set — `kepler-2026-09-21.r3`, frozen, k = 6

[`src/exonotes/questions_kepler.py`](src/exonotes/questions_kepler.py) — a **new module under a new
version string**; `questions.py` (`2026-09-20.r6`) is untouched and stays frozen for TESS.

**Chosen without any Kepler label** — a deliberate difference from TESS, which picked topics
partly by each crude cue's |AUC| on its own evaluation corpus (A-19, A-23). Kepler topics come
from **TESS's evidence** (what carried signal on a *different* corpus) and are kept or retired on
**label-free prevalence** in CFOP against a 5%-of-rows floor (TESS retired everything ≤ 4.7%):

| question | CFOP rows | |
| :--- | ---: | :--- |
| `imaging_reports_no_companion` | 62.8% | r6, re-cued for Robo-AO / ARIES / Lick / speckle |
| `imaging_reports_companion_present` | 48.2% | r6, re-cued; guide-camera and slit-viewer sightings named |
| `spectroscopy_indicates_nonplanetary_companion` | 7.1% | r6's evidence-agnostic scope; a catalogue listing alone does **not** count |
| **`spectroscopy_reports_no_binary_signature`** | 14.0% | **new** — CFOP states the recon pass as "no significant velocity variation" / "Looks good", which r6's planet question answers **no** to by design |
| `recon_reported_concluded` | 9.4% | r6's closure, widened to "time for more precise velocities" |
| `author_certainty` | score | r6 |
| ~~`host_star_described_as_evolved`~~ | **2.2%** | **retired** (24.6% on TESS) |

Label-echo tier (never the headline): `indicates_false_positive_or_retired`,
`indicates_confirmed_planet`. **No predictive question reads the `Possible false positive = …`
or `Possible eclipsing binary = Yes (Kepler Eclipsing Binary Catalog …)` fields** — L7's
disposition analogues — while `Possible nearby companion = Yes (…)`, an imaging observation, is
read.

**The gate, and the two things it did that TESS's did not.** Label-blinded cases selected
programmatically (`scripts/046`), expectations written from text alone before any answer
(`scripts/047`), §2.4 rule 6 bands:

| round | main (30 cases) | holdout-1 (15, disjoint) | holdout-2 (15, disjoint from both) |
| :--- | :--- | :--- | :--- |
| r1 | 200/208 | — | — |
| r2 | **208/208** | **95/103** — r2 was partly fitted | — |
| r3 | 208/208 | 103/103 | **98/100 → FROZEN** |

1. **Holdouts.** r2 passed the cases it was repaired on and failed unseen text (8 mid-band
   answers on terse phrasings — "Recon: single lined", "BGEB", "reveals a single star" — and on
   hedged closures). Passing a repair set is partly a fit; TESS's gate never tested for that.
2. **The acceptance rule was fixed before any r3 answer existed:** freeze iff holdout-2 passes
   ≥ 95% of asserted cells **and** no predictive question fails on more than one case; otherwise
   delete the question (§2.4 rule 4), never reword it a fourth time. r3: **98/100, one failure
   each in two questions → frozen, nothing deleted.**

**Disclosed:** one expectation was changed **after** seeing its answer (r1, T14 / nonplanetary):
its only SB2 sat inside a `Possible false positive = Yes (…)` field, which the module's own
docstring — written before any call — says no predictive question reads. The cell contradicted
that pre-run rule and was corrected toward it. **Caveat, not explained away:**
`spectroscopy_reports_no_binary_signature` is the least robust question — mid-band on three
holdout-2 texts (one asserted, two left unasserted as ambiguous). Gate total: **165 calls,
$0.0239.**

#### 41.2 `KEPLER_PATTERNS` — audited; the registered G5 arm is a different population on Kepler

[`src/exonotes/leakage.py`](src/exonotes/leakage.py), appended; `OBSNOTES_PATTERNS` and
`COMMENTS_PATTERNS` untouched (asserted — CI imports them).
[`research/data/kepler_g5_audit_2026-09-21.json`](research/data/kepler_g5_audit_2026-09-21.json).

| clause | n | P(y=1) | marginal |
| :--- | ---: | ---: | ---: |
| L3 confirmed / validated / published | 145 | 0.924 | 21 |
| L4a catalogue designation | 110 | 0.864 | 69 |
| **L7 `Possible X = Yes/No`** | **2,516 (53.3%)** | **0.362** | 2,366 |
| L8 status line | 1 | 0.000 | 0 |
| K10 `Kepler-N` | 116 | 0.966 | 9 |
| **K11 confirmation statement** *(added)* | 67 | 0.716 | 14 |
| **K12 accepted for publication** *(added)* | 8 | 1.000 | 0 |
| **K13 dead / inactive** *(added)* | 20 | 0.100 | 1 |
| L1, L2, L4b, L9 | 0 | — | — |
| **L5 tripwire** | **0 ✓** | — | — |

| arm | rows | kepid | base | minority |
| :--- | ---: | ---: | ---: | ---: |
| **KG5 — with L7 (registered headline)** | **2,036** | 1,574 | **0.811** | 384 |
| KG5 sensitivity — without L7 | 4,402 | 3,654 | 0.557 | 1,949 |

**L7 runs in the opposite direction on Kepler.** On TESS it stripped rows at P(y=1) = 0.941 —
positive-label echo. On CFOP it strips **53% of rows at 0.362, below the 0.575 base**: the
companion / EB / false-positive flags cluster on false positives. The registered headline KG5
arm therefore **removes most FPs** and runs at base 0.811 on 43% of the corpus; **a KG5 verdict
is not comparable to TESS's G5**, and the without-L7 arm is the representative one. Nothing is
changed — both arms were registered in A-40 before this was known, and 40.6 already binds that a
verdict flipping between them is reported as such.

**Audit notes.** **L4a misfires on CFOP:** its 69 marginal rows are TRES spectrograph headers
("TRES 20/21 Jun 2010 Teff=…") — `CATALOGUE_PREFIX` carries `TRES` for the TrES survey. The rule
is add-only, so it stays; the over-strip is recorded. **Added:** K11 (narrow — "has been
confirmed", "we confirm", "Confirmed via TTV … Ming et al. 2013", "confirmed BGEBs"; the bare
verb is left, since "an observation at phase 0.75 to confirm the velocity variations" is a
plan), K12 ("Accepted in ApJ"), K13 (the FOP's "This KOI is dead. Move to inactive."). **Not
added:** "false positive" — 177 rows at 0.458, mostly speculation; A-26's precedent.

#### 41.3 The MDE at k = 6 — the registered number

`scripts/044_kepler_step2.py --corpus cfop --k 6` →
[`research/data/kepler_cfop_step2_k6_2026-09-20.json`](research/data/kepler_cfop_step2_k6_2026-09-20.json):

| | k = 7 (A-40, provisional) | **k = 6 (registered)** |
| :--- | ---: | ---: |
| dilution floor | −0.0044 | **−0.0036** |
| bootstrap SE of ΔAUC | 0.0007 | **0.0007** |
| **MDE (80%)** | +0.0021 | **+0.0019** |
| true signal needed | 0.0064 | 0.0055 |

**+0.0019 is the MDE criterion 1 of 40.9 is judged against.** `scripts/050` reads this file and
asserts k = 6.

#### 41.4 S2, realised by 40.5's rule

Test = host ≥ 3865: **train 3,539 rows / 2,700 kepid, base 0.714; test 1,181 rows / 1,143
kepid, base 0.158 (25.0%); 0 kepid straddle.** Later-identified KOIs are overwhelmingly false
positives — a far larger base-rate shift than TESS's. Reported, not re-chosen; an S2 AUC is not
an S1 AUC.

#### 41.5 Cost, projected from measured tokens

Tokens = 3621 + 0.4110 × chars, fitted on the 60 r3 gate calls (R² 0.970). Over **3,843 distinct
host states: 14.9M tokens, $0.6265.** Tripwire **$0.80**. The longest state is ~17.8k tokens
against the documented 32k limit — **no truncation.** KG3 adds ~400 calls (~$0.07).

#### 41.6 The analysis code, fixed before any Kepler feature exists

| script | role | fixed now |
| :--- | :--- | :--- |
| [`048_kepler_step3_features.py`](scripts/048_kepler_step3_features.py) | Step 5: the feature matrix | 034's machinery (A-4, A-5, A-38); refuses any question set but r3; **paid-run record write-once** |
| [`049_kepler_kg3_stability.py`](scripts/049_kepler_kg3_stability.py) | KG3 | **the eight paraphrases are written here, now** — criteria unchanged, none identical |
| [`050_kepler_gates.py`](scripts/050_kepler_gates.py) | KG2 / KG4 / KG5 / KG6 and **40.9's verdict, computed** | reads the registered MDE and asserts k = 6 |

**`050` was tested in both directions before the run** — on a scratch copy of the database,
with synthetic features in place of Jev's; `data/kepler.duckdb` and `research/data/` untouched:

| synthetic features | D − B | D − B+meta | KG5 (with L7) | KG6 | KG4 | **computed reading** |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| pure noise, k = 6 | −0.0047 | −0.0304 | −0.0095 | −0.0040 | +0.0004 (incl. 0) | **DOES NOT TRANSFER** ✓ |
| noise + one oracle column agreeing with y 95% of the time | +0.0335 | **+0.0078** | +0.0541 | +0.0339 | +0.0477 | **TRANSFERS** ✓ |

A verifier that can only say no is not proven, so both branches were exercised. **The oracle row
is also a calibration, recorded before the result: a single column that agrees with the label 95%
of the time beats B+meta by only +0.0078.** Criterion 2 is demanding on this corpus — B+meta
already reaches 0.9839 — and 40.10's statement that a null is a live outcome stands with a number
beside it.

**The sequence from here:** push this amendment → `048` (the paid run) → `050` → `049` →
`RESULTS` section for Kepler, reading the outcome through 40.9's table and nothing else.

## 11.11 Kepler — the result. **Written AFTER the result.**

Changes **no** criterion of §11.10 and **no** TESS number. The full write-up is
[`RESULTS_KEPLER.md`](RESULTS_KEPLER.md); this section records the reading, what the run did
differently from A-41's projection, and a defect found on the way.

### A-42 — The Kepler reading; 3,192 states, not 3,843; and a concurrency defect in both G3 scripts

#### 42.1 The reading, computed by `050`: **TRANSFERS ONLY AS FOLLOW-UP VOLUME**

[`research/data/kepler_gates.json`](research/data/kepler_gates.json). n 4,720 · 3,843 `kepid` ·
base 0.5750 · MDE +0.0019 (k = 6).

| A-40 40.9 criterion | result | |
| :--- | :--- | :--- |
| 1. KG2 excludes 0, point ≥ MDE | **+0.0234** [+0.0186, +0.0282] | ✅ |
| **2. D beats B+meta** | **−0.0023** [−0.0041, −0.0004] | ❌ — D is significantly *below* B+meta (0.9816 vs 0.9839) |
| 3. KG5 (with `L7`) | +0.0198 [+0.0092, +0.0315], n 2,036, base 0.811 | ✅ |
| 4. KG6 | +0.0241 [+0.0194, +0.0290] | ✅ |
| KG4 (S2) | +0.0348 [+0.0206, +0.0496], test base 0.158 | ✅ |
| KG5 without `L7` | +0.0234 [+0.0186, +0.0284], n 4,402, base 0.557 | ✅ — **no flip** |
| KG3 | 3 of 6 `TIER_PREDICTIVE` miss ρ ≥ 0.85 — `spectroscopy_indicates_nonplanetary_companion` 0.841, `spectroscopy_reports_no_binary_signature` 0.828, `recon_reported_concluded` 0.651; every mean \|Δp\| ≤ 0.0224; same-wording repeat ρ 0.91–0.93 on all three | ❌ **FAIL** |

**40.9 row 3 applies: the content claim does not transfer. 40.9's KG3 row also applies: the
instability is a finding in its own right**, reported beside the reading, not instead of it. The
IQR exemption (A-8 item 11, *below* 0.01) is not applied to `recon_reported_concluded`, whose IQR is
exactly 0.01 — TESS's precedent — and would not change the verdict (the other two failures have
IQR 0.020 and 0.040). B, B+meta, C and the dilution arm
reproduce their pre-run values (0.9582, +0.0257, 0.9429, −0.0043). No arm beyond those registered
in A-40 / A-41 was computed; in particular **D + meta vs B+meta was never registered and has not
been run.**

#### 42.2 3,192 distinct states, not 3,843

A-41 41.5 projected cost over "3,843 distinct host states". That is the host count: **3,843 hosts
carry 3,192 distinct texts** (802 hosts share byte-identical text with another; 277 carry only
`Possible eclipsing binary = Yes (Kepler Eclipsing Binary Catalog v2 …`). Identical text is one
state and one cache key, so `048` made **3,192 calls, $0.5263** (projection $0.6265). The
write-once record `research/data/kepler_step3_paid_run.json` names the host count
`distinct_states`; it is not edited. No feature is affected: every KOI carries its host's answers
either way. Matrix checksum **`647a73578551b2b4`**.

#### 42.3 Defect 34 in `049` — fixed before KG3's first call

`049` (committed with A-41) swapped `s3.QUESTIONS / s3._QJSON / s3.CACHE` — module globals shared
by every thread — from 8 workers at once, with paraphrase and repeat jobs interleaved. A thread in
one arm could send its request with the other arm's wording, and a `finally` could "restore"
another thread's values, leaving the globals pointing at the wrong cache when the baseline is read.
**Fixed before any KG3 call:** a lock around swap + call + restore, and a stop if the globals are
not restored after the threaded phase. **Unchanged, verified by AST comparison with `b14a97e`:**
all 8 paraphrases, the sample size and seed, both cache salts, and the criteria. **Verified by
output:** `usage.input_tokens` per host against Step 5 — repeat arm Δ 0 on 200 / 200, paraphrase
arm Δ −253 on 200 / 200 — so every KG3 call carried its own arm's wording; the globals-restored
check passed. KG3: 362 calls, $0.0569.

#### 42.4 The same defect in TESS's `036` — it fired; the G3 verdict holds; published numbers do not

Found by reading `049`, then checked against the TESS G3 cache at **$0, read-only**:

1. **4 of 197 TESS paraphrase-arm calls carried the original wording** (their `usage.input_tokens`
   equal Step 3's; the other 193 sit at a constant −198). The repeat arm is clean (197 / 197).
2. **The published G3 table was computed against the wrong baseline.** It reproduces exactly
   (`imaging_reports_no_companion` ρ 0.8843, |Δp| 0.0456) only when base is read from
   `data/cache/g3/` — the repeat arm's own same-session re-ask — not from `data/cache/step3/`, the
   features in the matrix. The race left `s3.CACHE` on the G3 directory when `036` read its base.
3. **Consequence:** [`RESULTS.md`](RESULTS.md) §6's repeat-arm figure (mean |Δp| 0.0001) and the
   claim that the paraphrase effect is **"412× the within-session noise"** (§6, §11) are artefacts.
   Against Step 3, same-wording noise is **0.0057**, so the paraphrase effect (0.0242) is **~4×**.
4. **The G3 verdict does not change.** Against Step 3, all 7 `TIER_PREDICTIVE` features pass on all
   200 rows (tightest: ρ 0.865, |Δp| 0.0465) and on the 196 rows without the contaminated TOIs
   (ρ 0.870, |Δp| 0.0474); the same two label-echo features fail.

**Not yet acted on, and recorded as such:** `RESULTS.md` §6 and §11 are not corrected here, `036`
is not yet fixed, and `.github/workflows/gates.yml` runs `036` cold, so every CI G3 carries the
same exposure. Those are the project owner's decisions.

## 11.12 TESS G3 and the drift table, corrected. **Written AFTER the result; changes no verdict.**

### A-43 — Defect 34 fixed in `036`; G3 recomputed against the right baseline; A-31's drift table replaced

A-42 42.4 recorded the defect and left the correction to the project owner, who approved it on
2026-09-22. This section supersedes the numbers in A-31, A-32 and §11.5's G3 table where they
differ; it changes **no** criterion and **no** gate verdict.

#### 43.1 `036` fixed, and the 4 contaminated calls re-asked

`036` gets `049`'s fix: a lock around swap + `s3.call` + restore, and a stop if the globals are not
restored before `base` is read. The 4 outer paraphrase files that carried the original wording
(identified by `usage.input_tokens` equal to Step 3's) were moved to
`data/cache/g3_defect34_quarantine/`, and `036` re-run: **4 new calls, $0.00054**. After it, all 197
paraphrase responses sit at Δ −198 tokens and all 197 repeat responses at Δ 0; `base` is read from
`data/cache/step3/`, the features in the matrix.
[`research/data/gate_g3_stability_2026-09-20.json`](research/data/gate_g3_stability_2026-09-20.json)
is rewritten in place (CI's `040` reads the newest match); the published version is in git at
`d23d32d`.

#### 43.2 G3, recomputed — every verdict unchanged

| feature | tier | ρ | mean \|Δp\| | same-wording ρ | verdict | first published |
| :--- | :--- | ---: | ---: | ---: | :--- | :--- |
| `imaging_reports_no_companion` | predictive | 0.866 | 0.0465 | 0.938 | ✅ | 0.884 / 0.0456 |
| `imaging_reports_companion_present` | predictive | 0.890 | 0.0156 | 0.931 | ✅ | 0.888 / 0.0158 |
| `spectroscopy_indicates_nonplanetary_companion` | predictive | 0.950 | 0.0208 | 0.982 | ✅ | 0.949 / 0.0196 |
| `spectroscopy_consistent_with_planet` | predictive | 0.941 | 0.0326 | 0.988 | ✅ | 0.948 / 0.0309 |
| `host_star_described_as_evolved` | predictive | 0.963 | 0.0128 | 0.976 | ✅ | 0.964 / 0.0130 |
| `followup_reported_concluded` | predictive | 0.952 | 0.0123 | 0.983 | ✅ | 0.960 / 0.0128 |
| `author_certainty` | predictive | 0.988 | 0.0147 | 0.996 | ✅ | 0.992 / 0.0135 |
| `indicates_retired_or_rejected` | label-echo | 0.808 | 0.0092 | 0.883 | ❌ ρ | 0.812 / 0.0096 |
| `indicates_confirmed_planet` | label-echo | 0.929 | 0.0193 | 0.973 | ✅ | 0.939 / 0.0189 |
| `contains_object_designation` | label-echo | 0.840 | 0.0657 | 0.915 | ❌ both | 0.814 / 0.0626 |

**G3 passes, 7/7 `TIER_PREDICTIVE`; the same two label-echo features fail, as A-32 recorded.** The
IQR exemption is still not relaxed. Paraphrase mean |Δp| **0.0250** vs same-wording **0.0056**:
the paraphrase effect is **4.4×** the noise, **not 412×** (A-31's last bullet is withdrawn). The 4
re-asked rows are two days younger than the rest; dropping them instead (196 rows) gives the same
verdicts (tightest ρ 0.870, |Δp| 0.0474).

#### 43.3 A-31's drift table, replaced

A-31's rows were *"minutes: 0.0001, ρ 0.996–1.000"* and *"~1 hour: 0.0049"*. The first was the G3
repeat arm compared with copies of itself (43.1's wrong `base`); the second gap came from log
timestamps that had been estimated. Gaps are now taken from cache-file modification times:

| comparison (byte-identical payloads) | gap | mean \|Δ\| per feature | ρ per feature |
| :--- | :--- | ---: | ---: |
| G3 repeat arm vs Step 3, 197 states × 10 | 9.1–15.3 min | **0.0056** | 0.887–0.996 |
| r6 gate vs Step 3, 27 cases × 10 | 14–21 min | **0.0050** | — |

**196 of 197 states differ** between two identical requests ~12 minutes apart. A-31's conclusion
— *"within a session Jev is effectively deterministic; over about an hour it drifts … rather than
per-request sampling"* — **is withdrawn**: identical requests differ by ~0.005 at every gap
measured, and the data cannot separate per-request sampling from server-side variation. **What
A-31 got right stands:** the pipeline is exact only from a warm cache, and no gate verdict is at
risk. A-33's drift arm simulated 0.0049, 0.88× the corrected 0.0056, and G2 passed at 10× it.
A-38's *"two different responses, ~0.0001 apart"* becomes ~0.005; its fix and +0.0432 stand.

#### 43.4 Documents corrected in the same commit

`RESULTS.md` §6 (table, noise floor, a correction note), §8 (drift table, a correction note, the
A-38 figure), §8a (the "1-hour" label), §11 (the 412× bullet); `README.md`'s cold-cache note;
`PROVENANCE.md`'s drift table and A-38 figure. Each says in place that it was corrected and why.

## 11.13 A public claim corrected, and a limitation added. **Written AFTER the result; changes no verdict.**

### A-44 — "Bag-of-words does not reach it" is withdrawn; question-topic selection is listed as a limitation

Written 2026-09-23, after v1.1.0, following the reassessment in
[`research/06_reassessment/`](research/06_reassessment/README.md). **It changes no criterion, no
gate and no registered number.** A-30 is left as written. It was true of the comparison then in
hand, and this section is append-only.

#### 44.1 The claim, and why it goes

A-30's third point, `RESULTS.md` §4.3, the README, `CITATION.cff` and `.zenodo.json` all read
C (TF-IDF + logistic, **text only**) scoring 0.8766 < B 0.9044 as *"whatever D is using,
TF-IDF cannot find it."* C never had the numeric columns under it. C < B shows that **the label
is not readable from the words alone**, and that leakage check still passes. It does not
compare bag-of-words with the structured features **on top of B**, which is the comparison the
sentence claims.

An **exploratory, unregistered** arm made that comparison. It was run with `026`'s folds,
CatBoost configuration and paired bootstrap, imported unchanged, and 2,000 resamples. It used
C's pipeline as a stacked out-of-fold column on top of B, with inner GroupKFold(5) on the
training rows only
([`research/06_reassessment/02_exploratory_checks.md`](research/06_reassessment/02_exploratory_checks.md)
E2, code included):

| arm | full S1 arm (n 1,482) | G5 arm (n 1,114) |
| :--- | :--- | :--- |
| B+TF-IDF − B | +0.0345 [+0.0237, +0.0457] | +0.0244 [+0.0146, +0.0341] |
| D − B+TF-IDF | +0.0088 [+0.0004, +0.0174] | +0.0147 [+0.0042, +0.0246] |

Bag-of-words on top of B reaches 80% of G2 and 62% of G5. The claim is replaced, in every
document that carried it, by the narrower statement the evidence supports: **the structured
judgments add a modest increment beyond bag-of-words.** That increment is itself exploratory. It
was not chosen before the result, and it is **not** a gate. A future registration that wants it
as a claim must register D − B+TF-IDF as an arm.

#### 44.2 The limitation, and why it was missing

A-19 and A-23 ranked candidate topics by the |AUC| of crude regex cues against the disposition,
**measured on all 1,482 labelled rows**, before the r5/r6 questions were written. That is
feature selection outside the CV loop. Its direction is optimistic and its size is unmeasured.
A-22 blinded the gate *cases*, not the *topics*. A-41 41.1 recorded the difference when it chose
Kepler's topics without labels. `RESULTS.md` §10 never listed it, and now does.

#### 44.3 Where it was changed

- `README.md`, *"What this is, and what it is not"*: the sentence was replaced, with a note saying so.
- `RESULTS.md` §4.3: a correction note with the table above. §10 gains the limitation.
- `CITATION.cff` abstract (validated with `cffconvert`) and `.zenodo.json` description: the
  sentence was replaced. Zenodo takes the new text only at the next release.
- `PREREGISTRATION.md` A-30 and `WORKLOG.md`: unchanged, because both are append-only.

## 11.14 Prospective validation (P1). **Written 2026-09-23, BEFORE any prospective model call. The T₀ snapshot it pins was frozen first, at $0.**

### A-45 — ExoNotes-Prospective: predictions for open TESS candidates, frozen now and scored only against dispositions assigned after they are published

Written by a working session at the owner's request, following
[`research/06_reassessment/05_project_proposals.md`](research/06_reassessment/05_project_proposals.md)
P1. **It binds only once the owner has committed it and pushed it to `origin/master`.** Until
then it is a draft, and `scripts/052_prospective_predict.py` refuses to make a paid call.

#### 45.0 Why

Every TESS number in this repository is retrospective. Three weaknesses named after the result
cannot be removed retrospectively:

- **Topic selection.** Question topics were chosen with outcome information (A-44 44.2).
- **Survivorship.** S2's test set contains only candidates that had been resolved by 2026
  (reassessment W7).
- **Post-disposition text.** Some observer text postdates the verdict. The loose proxies say
  at least 3–8% (reassessment E8).

A prospective test removes all three. It is also the only test of the word the README uses:
does reading the follow-up trail *anticipate* the consensus?

#### 45.1 Order of operations (binding)

1. **Freeze T₀.** Done: 45.2.
2. **Register.** This amendment, `research/data/prospective_freeze_manifest.json` and
   `scripts/051`–`053` are committed and pushed together. That commit is the *registration commit*.
3. **Predict.** Run `052 --registration-commit <sha>`. It refuses unless `<sha>` is an ancestor of
   `origin/master`, contains this amendment, and carries a manifest equal to the local frozen
   corpus.
4. **Publish.** `research/data/prospective_predictions_t0.csv` and `.json` are committed and
   pushed **within 24 hours** of the `052` run. The push time is **T_pub**. `053` checks the
   window and flags a violation in the reading. It does not hide it.
5. **Evaluate.** Run `053` at the checkpoints in 45.7.

**Lapse:** if step 4 has not happened by **2026-10-23**, this registration lapses. A new T₀
needs a new amendment. No step may be reordered, and no step may be repeated with changed code.

#### 45.2 The frozen T₀ snapshot

`scripts/051_prospective_freeze.py`, run 2026-09-23, $0. The TOI tables were fetched at
**01:45:37Z**. The per-TIC note pull ran **01:45:43Z → verified 02:00:31Z**, with 0 failures and
0 false empties on re-fetch. **T₀ = 2026-09-23T02:00:31Z**: all frozen text is as of a moment in
that window.

| artifact | value |
| :--- | :--- |
| `exofop_toi_T0.csv` sha256 | `7f442aa01cf19a6aa0e093e97736286347fc3e9ddb81d633d3115b6353056390` |
| `nea_toi_T0.csv` sha256 (label + covariate source) | `8e90ae4b0795eef5b4c0ea3c4ac3d890dd3ed56d78ae4dfeb5cdc61da727c4d1` |
| per-TIC note files / manifest sha256 | 7,818 / `060a830718e7609a046c299408626544833d9c130f5aac22157fc04404bf2380` |
| notes parsed (TFOPWG / observer) | 12,380 (3,677 / 8,703); the Groupname domain is asserted `{tfopwg, NULL}` |
| NEA dispositions at T₀ | PC 4,823 · APC 485 · FP 1,301 · CP 818 · KP 607 · FA 100 · blank 14 |
| **`train_t0`**: labelled at T₀, with observer text | **1,552 rows / 1,458 TIC / base 0.5361** · sha16 `a09259340a06ac63` |
| **`predict_t0`**: PC or APC at T₀, with observer text | **2,080 rows / 2,003 TIC** (of 5,308 open TOIs) · sha16 `285d1aa3cf7d199b` · 36 share a TIC with a labelled TOI |

**Checked against the published corpus:** all 1,482 rows of `analysis_set_obsnotes` are in
`train_t0`, with **identical labels and byte-identical text**. The freeze rebuilds the TESS
corpus exactly. The **70 extra rows** are labelled TOIs whose `Comments` field is empty.
`analysis_set` required a non-empty `Comments`, which was a leftover of the corpus switch and is
not applied here. This is a deliberate definitional difference, stated now.

**ExoFOP cannot re-serve T₀.** `data/prospective/` and `data/prospective.duckdb` are gitignored
and must be **backed up by the owner** before step 2. The checksums above are the public record.

#### 45.3 Corpus and label: the TESS study's definitions, unchanged

The corpus is observer notes only (`Groupname IS NULL`, §1.1, A-10), text from `028`'s
`plain()`, concatenated per TIC in ascending `Lastmod`. The label is NEA `toi.tfopwg_disp`, with
CP/KP = 1 and FP/FA = 0 (§1.3). **Text and numeric covariates are those frozen at T₀ and are
never refreshed**, for training and prediction rows alike.

#### 45.4 Featurizer, arms, comparisons

- **Featurizer:** `jev-1.13.0` (asserted on every response, A-5), question set `2026-09-20.r6`
  unchanged, state `{"notes": text}` (A-4). **Every distinct text, training and prediction, is
  scored in one session** into `data/cache/prospective/`, so the two sides share any model
  drift. The published Step 3 matrix is **not** reused, and the retrospective features are not
  claimed to be comparable.
- **Arms**, each CatBoost with `026`'s configuration, fit on all of `train_t0`, **10 seeds**
  (20260919 + i) with the predicted probabilities averaged:
  - `B`: the 8 numeric columns.
  - `Bmeta`: B + note count, characters, authors, top-8 author one-hot (top-8 fixed on
    training notes only).
  - `BTFIDF`: B + C's TF-IDF + logistic pipeline as a stacked column (inner GroupKFold(5)
    out-of-fold on training rows; for prediction rows, fit on all training rows).
  - `D`: B + the 7 `TIER_PREDICTIVE` features.
  - `Dmeta`: D + meta.
- **Primary:** ΔAUC(**D − B**) on the evaluation set, paired bootstrap, **10,000 resamples over
  TIC groups** (`026`, unchanged).
- **Secondary** (reported with intervals, read as in 45.8, never the headline):
  - **Dmeta − Bmeta**, the content test. This is the logical form of "text beyond volume"
    (reassessment W6).
  - **D − BTFIDF**, structure beyond words (A-44).
  - **D − Bmeta**, continuity with the retrospective control.
- Brier scores for every arm, descriptive.
- **No other arm will be reported as a result of this registration.**

#### 45.5 Evaluation set

These TOIs are scored:

- in `predict_t0`;
- **PC or APC in the NEA snapshot `052` takes when it runs** (`open_at_prediction`);
- **CP, KP, FP or FA in the NEA snapshot `053` takes at the checkpoint**, with CP/KP = 1.

TOIs that become blank or another value, or that leave the table, are counted and not scored.
TOIs resolved between T₀ and the `052` run are not scored (`open_at_prediction` is false).

#### 45.6 Sensitivity arms (reported beside the reading, never the reading)

**(a)** Drop TOIs whose TIC carried a labelled TOI at T₀. A sibling's label is legitimate
information in a forecast, but it inflates every arm. This is the S2a analogue.

**(b)** Drop rows whose frozen text fires `OBSNOTES_PATTERNS` or the TESS analogue of Kepler's
`K10` (reassessment E5):

```
\b(?:WASP|HAT-P|HATS|KELT|XO|TrES|Qatar|NGTS|WTS|CoRoT|K2|Kepler|MASCARA|KPS)-\d+
```

#### 45.7 Checkpoints

**6m = 2027-03-23** and **12m = 2027-09-23**: descriptive only. They cannot stop, extend or
alter the study, so no α is spent. **18m = 2028-03-23**: confirmatory. **24m = 2028-09-23**:
run only if 18m returns n < 200, and then it is final. `053` refuses to run before each date.

#### 45.8 The reading, computed by `053`

| condition at the confirmatory checkpoint | reading |
| :--- | :--- |
| n < 200 at 18m | **UNDERPOWERED**: extend once to 24m |
| n < 200 at 24m | **INCONCLUSIVE**: report estimates, claim nothing |
| n ≥ 200, primary CI lower bound > 0 | **CONFIRMED PROSPECTIVELY** |
| n ≥ 200, primary CI includes 0 | **NOT CONFIRMED PROSPECTIVELY**, a negative result, published as such |
| n ≥ 200, primary CI upper bound < 0 | **REVERSED** |
| appended to any of the above | *content beyond volume confirmed* iff Dmeta − Bmeta's CI lower bound > 0 |

**N_MIN = 200** is where the retrospective effect is detectable at 80% power. It was measured
before this registration by subsampling the TESS out-of-fold predictions (45.9).

#### 45.9 Power, cost, and the prior, stated before any prospective call

**MDE of the primary test at 80% power**, measured 2026-09-23 at $0 by subsampling n TICs from
the TESS out-of-fold B and D predictions (20 draws each, paired bootstrap SE × 2.802):

| eval n | 100 | 150 | **200** | 250 | 300 | 400 | 600 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MDE | 0.065 | 0.050 | **0.043** | 0.039 | 0.035 | 0.030 | 0.024 |

**Expected n: unknown, stated as a range.** An upper-bound proxy puts dispositions at roughly
200–350 per year across all TICs: labelled TICs whose TFOPWG `Master Disp` note was last
modified in the preceding 12 months numbered 283, and ranged 206–560 per year from 2021 to 2025.
Only the 2,080 candidates with observer text are eligible, so **the realised n at 18m could land
anywhere from about 150 to 450.**

**Cost:** `052 --dry-run` projects 3,399 distinct texts, 13,085,257 tokens, **$0.5496**. The
tripwire is **$1.50**. `053` makes no model call.

**The prior (this session's, recorded so that neither outcome can later be called obvious):**

- D − B prospectively is **positive but smaller** than the retrospective +0.0432. Open
  candidates have thinner, less decisive notes, and the first to resolve are the easy ones.
  Central guess about +0.02.
- The content test (Dmeta − Bmeta) is **more likely than not to include zero**. Its
  retrospective margin, carried by three spectroscopy features (reassessment E6), is +0.013,
  well below any achievable MDE here.
- **So the most likely registered outcome is NOT CONFIRMED, even if a real effect of about +0.02
  exists.** That is stated now, so a null is read as "not detected at this power", never as
  "absent". The report always carries the point estimate and interval.

#### 45.10 Contingencies

- **`jev-1.13.0` retired or mismatched before `052` completes:** no substitute model without a
  new amendment registered before its first call.
- **The NEA `toi` schema or `tfopwg_disp` vocabulary changes:** `053` fails loudly, and an
  amendment maps the change before any checkpoint is read.
- **The owner cannot run `052` before the lapse date:** the registration lapses (45.1).
- **A defect found after predictions are published:** fixed only in `053`, with the fix
  registered as an amendment *before* the checkpoint it affects, and reported. The published
  predictions are never regenerated.

#### 45.11 What this does not test

- **Resolution order.** Candidates that resolve early are still a selected subset.
  Checkpoint-by-checkpoint reporting shows the trajectory. It does not remove the selection.
- **Independence.** TFOP decides with much of the same information, so a confirmation shows
  that the notes *anticipate* TFOP. It does not show they beat TFOP.
- **Featurizer independence.** One featurizer. That is P2's question.
- **Scope.** Candidates without observer text (3,228 of 5,308 open TOIs) are out of scope.

#### 45.12 Frozen code (sha256 at registration)

| file | sha256 |
| :--- | :--- |
| `scripts/051_prospective_freeze.py` | `21ce8e25ac4cf075e934d505ad93b283c04e7293784b21aaeab3e2ba295f023b` |
| `scripts/052_prospective_predict.py` | `ff28a895adb986a4e40ac32be128e8cb689c22e224c771cae77a2606902eab66` |
| `scripts/053_prospective_evaluate.py` | `492051676ce5e0c74ea48b0b0ac387ba095954dfea2c90d113c2546526557e89` |
| imported, unchanged: `026` · `01_ingest` · `028` · `questions.py` · `leakage.py` | `1a685d6e…` · `080b99c5…` · `2fa25b06…` · `58ad0637…` · `9c1bebf0…` |

**Tested before registration, at $0:**

- `052 --dry-run` ran every arm on mock features (no API call).
- `053 --smoke signal` read **CONFIRMED** (D − B +0.0240 [+0.0077, +0.0417], n 300).
- `053 --smoke null` read **NOT CONFIRMED** (+0.0115 [−0.0087, +0.0320]).
- The underpowered, inconclusive and reversed branches were checked directly.
- `052` refuses a commit without A-45 and a commit that is not on `origin/master`.
- `053` refuses before its date.
