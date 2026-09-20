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
