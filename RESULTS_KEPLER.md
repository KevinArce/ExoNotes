# ExoNotes — Kepler transfer test: Results

**Does the TESS result — structured reading of follow-up observers' notes adds signal beyond the
catalogue columns — hold on a second mission, era and observer community?**

**No. On Kepler it transfers only as follow-up volume: the content claim does not transfer.**

The Jev features beat the covariates by **+0.0234 [+0.0186, +0.0282]**, 12× the registered
minimum detectable effect, and that gain survives leakage stripping, missingness indicators and
the temporal split. But a control that makes **no model call at all**, one that knows only how
much follow-up a KOI received (note count, characters, authors), beats them:
**D − B+meta = −0.0023 [−0.0041, −0.0004]**. On TESS, D beat that control by +0.0220. That
comparison is the one that carries the claim, and it does not reproduce. **Separately, the
paraphrase-stability gate KG3 fails:** three of the six features rank the notes differently when
the question is reworded.

This is the second study in this repository, registered in
[`PREREGISTRATION.md`](./PREREGISTRATION.md) **§11.10 (A-40, A-41)** and pushed (`b14a97e`,
2026-09-21T03:24Z) **before any full-corpus Kepler model call**. Every comparison, split, clause set,
threshold and the reading table below was fixed then. The reading is computed by
[`scripts/050_kepler_gates.py`](scripts/050_kepler_gates.py), not read off by hand. The TESS result is
[`RESULTS.md`](./RESULTS.md). This study changes none of its verdicts, though a defect found on
the way affects some of its G3 numbers ([§6](#6-what-happened-during-the-run-disclosed)).

---

## 1. The reading, as registered

A-40 40.9 says **TRANSFERS** only if **all four** criteria hold:

| criterion (A-40 40.9) | result | |
| :--- | :--- | :--- |
| 1. KG2 excludes zero **and** its point estimate ≥ the MDE (+0.0019) | +0.0234 [+0.0186, +0.0282] | ✅ |
| **2. D beats B+meta**, paired CI excluding zero | **−0.0023 [−0.0041, −0.0004]** | ❌ **fails, and on the wrong side of zero** |
| 3. KG5 passes (with-`L7` arm) | +0.0198 [+0.0092, +0.0315] | ✅ |
| 4. KG6 passes | +0.0241 [+0.0194, +0.0290] | ✅ |

The row of the table that applies, **written before the run**:

> **KG2 holds, D does not beat B+meta → Transfers only as follow-up volume.** On Kepler the prose
> adds nothing beyond how much follow-up a KOI received. Since TESS D *did* beat B+meta, **the
> content claim does not transfer.** Negative for the claim that matters.

Criterion 2 doesn't just fall short of significance. D is **significantly worse** than B+meta.

KG3 is not one of the four criteria. 40.9 gives it its own row: **"KG3 fails: the instability is
the finding."** It fails here ([below](#kg3-per-feature)). That is a second negative next to
the first. It doesn't cause the first and doesn't soften it.

---

## 2. Every gate, with its interval

n = 4,720 KOIs · 3,843 `kepid` groups · base rate 0.5750 · GroupKFold(5) × 3 repeats · paired
bootstrap, 10,000 resamples over `kepid`, the same machinery as TESS (`026`, imported unchanged).

| gate | criterion (A-40 40.7) | result | verdict |
| :--- | :--- | :--- | :--- |
| **KG1** | B ≥ 0.85, CI above 0.5 | B **0.9582** (measured pre-Jev; reproduced) | ✅ |
| **KG2** | D − B, S1, `TIER_PREDICTIVE` only, CI excludes 0 | **+0.0234** [+0.0186, +0.0282] · B 0.9582 → D 0.9816 | ✅ |
| **KG3** | ρ ≥ 0.85 and mean \|Δp\| ≤ 0.05 per feature under paraphrase | **3 of 6** `TIER_PREDICTIVE` miss ρ (0.841, 0.828, 0.651); all pass \|Δp\| | ❌ **FAIL** |
| **KG4** | D − B under S2, CI excludes 0 | **+0.0348** [+0.0206, +0.0496] · B 0.9363 → D 0.9712 | ✅ |
| **KG5** | D − B on the `KEPLER_PATTERNS`-stripped arm, **with `L7`** | **+0.0198** [+0.0092, +0.0315] · n 2,036 · base 0.811 | ✅ |
| **KG6** | D − B with explicit missingness indicators | **+0.0241** [+0.0194, +0.0290] | ✅ |

Reference arms, with the pre-run values they reproduce:

| arm | result | pre-run (A-40 / A-41) |
| :--- | :--- | :--- |
| **B+meta** (A-7: note count, characters, authors, top-8 author one-hot) | **+0.0257** [+0.0208, +0.0306] · AUC **0.9839** | +0.0257 · 0.9839 |
| **D − B+meta** | **−0.0023** [−0.0041, −0.0004] | — (TESS: +0.0220 [+0.0126, +0.0321]) |
| B+N, k = 6 noise columns (dilution) | −0.0043 [−0.0058, −0.0029] | −0.0036 (mean of 5 seeds) |
| E − B, all 8 questions (label-echo tier included; never the headline) | +0.0245 [+0.0196, +0.0295] | — |
| C, TF-IDF + logistic on the text (never evidence) | AUC **0.9429**, below B | 0.9429 |
| KG5 sensitivity, **without `L7`** | +0.0234 [+0.0186, +0.0284] · n 4,402 · base 0.557 | — |

**KG5 does not flip between its two arms** (A-40 40.6 registered that a flip would be reported as
one).

### KG3, per feature

200 hosts (seed 20260921), every question reworded (the eight paraphrases were committed with
A-41, before any Kepler feature existed) and re-asked, beside a same-wording repeat arm that
measures resampling noise. Compared with the Step 5 features that went into D.
[`research/data/kepler_kg3_stability.json`](research/data/kepler_kg3_stability.json).

| feature | tier | ρ | mean \|Δp\| | IQR | repeat ρ | repeat \|Δp\| | verdict |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `imaging_reports_no_companion` | predictive | 0.925 | 0.0102 | 0.950 | 0.983 | 0.0013 | ✅ |
| `imaging_reports_companion_present` | predictive | 0.943 | 0.0105 | 0.890 | 0.968 | 0.0033 | ✅ |
| `spectroscopy_indicates_nonplanetary_companion` | predictive | **0.841** | 0.0178 | 0.020 | 0.924 | 0.0048 | ❌ ρ |
| `spectroscopy_reports_no_binary_signature` | predictive | **0.828** | 0.0224 | 0.040 | 0.910 | 0.0037 | ❌ ρ |
| `recon_reported_concluded` | predictive | **0.651** | 0.0103 | 0.010 | 0.934 | 0.0016 | ❌ ρ |
| `author_certainty` | predictive | 0.969 | 0.0149 | 0.510 | 0.979 | 0.0053 | ✅ |
| `indicates_false_positive_or_retired` | label-echo | 0.732 | 0.0072 | 0.010 | 0.780 | 0.0032 | ❌ ρ |
| `indicates_confirmed_planet` | label-echo | 0.857 | 0.0075 | 0.030 | 0.928 | 0.0054 | ✅ |

- **All three predictive failures are on ρ alone.** Every mean |Δp| is under 0.023, less than half
  the bar. The three are near-constant columns (IQR 0.010–0.040), where a small shift reorders
  many near-tied values.
- **It isn't resampling noise.** Asked again in the *same* words, the same three columns keep
  ρ 0.91–0.93. The drop comes from the rewording.
- **The IQR exemption isn't applied.** A-8 item 11 exempts a column whose IQR is *below* one
  quantisation step (0.01). `recon_reported_concluded`'s IQR is exactly 0.01, which is the edge
  TESS met and did not relax ([`RESULTS.md`](./RESULTS.md) §6). Relaxing it would not change the
  verdict, because the other two failures have IQR 0.020 and 0.040.
- `spectroscopy_reports_no_binary_signature` was named the **least robust** question before
  the run (A-41 41.1). It is one of the three.
- The key-order half of the test is vacuous with a one-key state, as on TESS. `049` asserts that
  and reports it, rather than skipping it.

---

## 3. Three things known before the result, and stated beside it

These were written down in A-40 / A-41 before any feature existed, and they belong next to the
number:

1. **"A null is a live outcome" (A-40 40.10), and criterion 2 was the hard part.** B = 0.9582 and
   B+meta = 0.9839 leave 0.016 of AUC headroom. In `050`'s pre-run smoke test, a synthetic column
   that agreed with the label **95% of the time** beat B+meta by only **+0.0078** (A-41 41.6).
   Criterion 2 was demanding on this corpus. That makes the result less surprising. It doesn't
   make it less negative. The registered criterion is what it is, and D lands *below* B+meta,
   not just short of it.
2. **KG5's registered arm is not comparable to TESS's G5.** On TESS, `L7` stripped rows at
   P(y=1) = 0.941 (positive-label echo). On Kepler it strips **53% of rows at 0.362**, the opposite
   direction, so the headline KG5 arm is 2,036 rows at base **0.811**. The **without-`L7`** arm
   (4,402 rows, base 0.557) is the representative one. Both pass here.
3. **S2's test set is 84% false positives** (base 0.158, train 0.714). Later-identified KOIs are
   overwhelmingly false positives, a far larger shift than TESS's. **An S2 AUC is not an S1
   AUC**, and KG4's +0.0348 is not a bigger effect than KG2's.

---

## 4. What this establishes, and what it does not

**Established, under the registered rule:**

- **The features carry signal about the Kepler disposition.** +0.0234 over the covariates, 12.3×
  the MDE. It survives leakage stripping in both arms, missingness indicators, and a temporal split.
  By share of headroom captured, (D − B)/(1 − B), it is **0.560** against TESS's 0.455. That is
  a description, and A-40 40.9 bars it from being a criterion.
- **That signal is not more than the follow-up volume already gives.** Three counts and an
  author one-hot, with no model call, reach 0.9839. The Jev features reach 0.9816. On TESS the
  order was reversed (B+meta 0.9256, D 0.9476).
- **So the claim this project cares about, that structured reading of the *content* adds
  something that *how much was written* does not, has held on one corpus and not on a second.**
  The TESS result should be read as specific to ExoFOP-TESS observer notes until something else
  replicates it.

**Not established:**

- **That the Kepler features carry *no* information beyond volume.** The registered comparison is
  D against B+meta, as on TESS. A model with *both* (D + meta against B+meta) was **not
  registered, and has not been run.** Running it now, after seeing this result, would be the
  forking path the registration exists to close. It is a reasonable question for a future,
  separately registered test.
- **That the TESS result is wrong.** This is a different corpus (heavily templated imaging reports,
  less spectroscopic prose; A-40 40.10) and a different label process. A failure to transfer
  limits the TESS claim's generality. It doesn't reverse it.
- **That the negative comes from the model misreading the notes.** The question set passed a
  label-blinded design gate with two disjoint holdouts (A-41 41.1). KG3 then showed that three
  of the six features depend on wording. That weakens any claim about what those three
  features *mean*, and 40.9 counts it as a finding in its own right. It was never tested as an
  explanation of criterion 2, and it isn't offered as one.

**Context recorded before the result (A-40 40.1, 40.12), not an explanation fitted after it:**
follow-up volume differs sharply by class on this corpus. Median characters are 115 vs 370 and
median authors 1 vs 3 (y=0 vs y=1). Post-disposition follow-up cannot be filtered on Kepler (no
per-KOI disposition date, so TESS's S2b has no analogue), which means confirmed KOIs' later
follow-up enters every arm. A-40 40.12 named D vs B+meta as the registered defence against
exactly that. These facts are consistent with the result. They weren't tested as causes of it.

---

## 5. Kepler beside TESS

| | TESS ([`RESULTS.md`](./RESULTS.md)) | Kepler (this document) |
| :--- | ---: | ---: |
| corpus | ExoFOP-TESS observer notes | Kepler CFOP observer notes (migrated into ExoFOP) |
| n / groups / base | 1,482 / 1,388 TIC / 0.5378 | 4,720 / 3,843 `kepid` / 0.5750 |
| questions (`TIER_PREDICTIVE`) | `2026-09-20.r6`, k = 7 | `kepler-2026-09-21.r3`, k = 6 |
| B | 0.9051 | 0.9582 |
| MDE (80%) | +0.0082 | +0.0019 |
| **D − B (headline)** | **+0.0432** [+0.0324, +0.0547] | **+0.0234** [+0.0186, +0.0282] |
| B+meta − B | +0.0212 | +0.0257 |
| **D − B+meta** | **+0.0220** [+0.0126, +0.0321] ✅ | **−0.0023** [−0.0041, −0.0004] ❌ |
| C (TF-IDF) vs B | 0.8766 < 0.9044 | 0.9429 < 0.9582 |
| leakage-stripped | +0.0391 | +0.0198 (with `L7`) · +0.0234 (without) |
| missingness | +0.0425 | +0.0241 |
| temporal split | +0.1296 (S2 + S2a + S2b) | +0.0348 (S2 + S2a; S2b not applicable) |
| paraphrase stability | 7/7 `TIER_PREDICTIVE` pass | **3/6 fail ρ** — KG3 fails |
| **reading** | **all gates pass** | **transfers only as follow-up volume; KG3 fails** |

---

## 6. What happened during the run, disclosed

- **3,192 model calls, not 3,843.** A-41 41.5 projected cost over "3,843 distinct host states".
  That counts hosts. 802 hosts share byte-identical note text with another (277 carry only the
  line `Possible eclipsing binary = Yes (Kepler Eclipsing Binary Catalog v2 …`), and identical text
  is one state and one call. **$0.5263** against the $0.6265 projection. No feature changes: every
  KOI gets its host's answers either way.
- **A concurrency defect in the KG3 script was found and fixed before KG3's first call**
  (WORKLOG defect 34). `049` swapped shared module globals from eight threads, so a call could go
  out under the other arm's wording, and its baseline could be read from the wrong cache. The fix
  is a lock plus an assertion. No paraphrase, sample, seed or criterion changed (verified against
  `b14a97e` by AST comparison), and the run was verified by output: every repeat-arm response has
  exactly Step 5's token count and every paraphrase-arm response a single constant offset
  (Δ 0 on 200 / 200 and −253 on 200 / 200).
- **The same defect exists in TESS's G3 script (`036`), and it did fire there.** It doesn't
  change any TESS gate verdict. It does change numbers in [`RESULTS.md`](./RESULTS.md) §6, which
  are **not yet corrected**. See [`WORKLOG.md`](./WORKLOG.md) (2026-09-22, defect 34) and
  [`PREREGISTRATION.md`](./PREREGISTRATION.md) §11.11.

---

## 7. Cost

| step | calls | spend |
| :--- | ---: | ---: |
| question-design gate (A-41 41.1) | 165 | $0.0239 |
| Step 5, the feature matrix (`048`) | 3,192 | $0.5263 |
| KG3 (`049`) | 362 | $0.0569 |
| **Kepler total** | **3,719** | **$0.6071** |

---

## 8. Reproducing

```bash
.venv/bin/python scripts/043_kepler_corpus.py --stage fetch   # the label: TAP `cumulative` snapshot, $0
.venv/bin/python scripts/045_kepler_cfop_corpus.py        # the corpus: ExoFOP bulk notes + that label, $0
.venv/bin/python scripts/044_kepler_step2.py --corpus cfop --k 6   # baselines, dilution floor, MDE, $0
.venv/bin/python scripts/048_kepler_step3_features.py     # the Jev feature matrix, ~$0.53 cold
.venv/bin/python scripts/050_kepler_gates.py              # KG2, KG4, KG5, KG6 and the 40.9 reading, $0
.venv/bin/python scripts/049_kepler_kg3_stability.py      # KG3, ~$0.06 cold
```

Kepler lives in its own database, `data/kepler.duckdb`. TESS's `data/exonotes.duckdb` is never
opened for write. `data/` is not committed. The ExoFOP dump and the cumulative table are
live sources, so a rebuild on a later day can differ, and the checksums say whether it did:

| artifact | sha256[:16] |
| :--- | :--- |
| `kepler_cfop_corpus` (to_csv) | `f3c30d2daf460095` |
| `kepler_jev_features` (to_csv) | `647a73578551b2b4` |
| ExoFOP obsnotes bulk dump, 2026-09-21T02:44Z | `475fc5dcafd43574` |
| TAP `cumulative` snapshot, 2026-09-21T02:23Z | `962947427b3038a3` |

Raw numbers:

| table | file |
| :--- | :--- |
| KG2, KG4, KG5, KG6, every reference arm, the computed reading | `research/data/kepler_gates.json` |
| KG3 | `research/data/kepler_kg3_stability.json` |
| the registered MDE (k = 6) | `research/data/kepler_cfop_step2_k6_2026-09-20.json` |
| the paid run (write-once) | `research/data/kepler_step3_paid_run.json` |
| the `KEPLER_PATTERNS` audit | `research/data/kepler_g5_audit_2026-09-21.json` |
| the question-design gate | `research/data/gate_kepler_*_kepler-2026-09-21.r3_*.json` |

Jev (`jev-1.13.0`) cannot be pinned below the version string, and it isn't bit-stable over
time (TESS: [`RESULTS.md`](./RESULTS.md) §8), so a cold re-run of `048` will land *near* these
numbers rather than on them.

---

## Acknowledgements

> This research has made use of the **Exoplanet Follow-up Observation Program (ExoFOP)** website,
> which is operated by the California Institute of Technology under contract with the National
> Aeronautics and Space Administration under the Exoplanet Exploration Program.
>
> This research has made use of the **NASA Exoplanet Archive**, which is operated by the
> California Institute of Technology under contract with the National Aeronautics and Space
> Administration under the Exoplanet Exploration Program.
>
> This paper includes data collected by the **Kepler** mission. Funding for the Kepler mission is
> provided by the NASA Science Mission Directorate.

The observer notes were written by the Kepler Community Follow-up Observing Program's observers;
this study reads their work and could not exist without it.
