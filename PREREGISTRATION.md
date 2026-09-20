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
