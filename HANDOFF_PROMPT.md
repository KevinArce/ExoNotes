# ExoNotes — handoff to the next session

You are picking up the ExoNotes project. **Work from the repo, not from memory.**

---

## ⚠️ START HERE — the TESS study is DONE, published and citable. Do not redo it.

All six gates pass, `RESULTS.md` is written, CI covers the gates and has passed a cold run, and
**v1.0.0 is archived on Zenodo with a DOI**.

> **ΔAUC(D − B) = +0.0432, 95% CI [+0.0324, +0.0547]**, under S1, `TIER_PREDICTIVE` only,
> paired bootstrap over TIC groups. **5.3× the registered MDE of +0.0082.**

| gate | result | verdict |
| :--- | :--- | :--- |
| **G1** | B = 0.9051 ≥ 0.85, CI excludes 0 | ✅ PASS |
| **G2** | ΔAUC **+0.0432** [+0.0324, +0.0547] | ✅ PASS |
| **G3** | 7/7 `TIER_PREDICTIVE` stable under paraphrase | ✅ PASS |
| **G4** | S2+S2a+S2b temporal **+0.1296** [+0.0948, +0.1670] | ✅ PASS |
| **G5** | leakage-stripped **+0.0391** [+0.0268, +0.0519] | ✅ PASS |
| **G6** | missingness ablation **+0.0425** [+0.0314, +0.0540] | ✅ PASS |

**Concept DOI: `10.5281/zenodo.22866246`** (always newest — cite this).
Version DOI for v1.0.0: `10.5281/zenodo.22866247`.
**Jev spend to date: ~$0.674.** Working tree clean, everything pushed.

---

## ⚠️ THREE NUMBERS YOU MIGHT MISREMEMBER. ALL THREE ARE TRAPS.

1. **The headline is +0.0432, not +0.0440.** A concurrency defect in `034_step3_features.py`
   made the original matrix irreproducible from its own cache. Fixed with a per-key lock; every
   arm re-run; **every S1 shift ≤0.0010, no verdict moved.** §11.8 A-38.
2. **The headline is +0.0432, not +0.0451.** The first cold CI run landed at **+0.0451** — that
   is **~28 hours of model drift, not a better result.** §8a and A-39a. **Do not adopt it.** It
   moves in the flattering direction, which is exactly why it is refused.
3. **Cite the CONCEPT DOI `…22866246`, not `…22866247`.** `zenodo.org/badge/latestdoi/` hands
   you the *version* DOI; using it pins every future citation to v1.0.0 forever.

**Matrix checksum:** `sha256(jev_features_obsnotes)[:16] = d7b5be5675778f44`.
**If a rebuild does not produce this, stop and find out why.** The recipe:

```python
sha256(duckdb.connect("data/exonotes.duckdb", read_only=True)
       .execute("select * from jev_features_obsnotes").fetchdf()
       .to_csv(index=False).encode()).hexdigest()[:16]   # -> d7b5be5675778f44
```

**Row order is part of the checksum** — re-sorting by `['tic_id','toi']` gives
`d952de67733cbfa8` on identical data.

---

## Read first, in this order

1. **[`RESULTS.md`](./RESULTS.md)** — §1, then §8/§8a (reproducibility) and §9 (what was not done).
2. **`WORKLOG.md` — read the TAIL first.** Append-only.
3. **[`PREREGISTRATION.md`](./PREREGISTRATION.md) §11.9 (A-39, A-39a)**, then §11.8 → §11.1.
   **Later sections supersede earlier ones. §11.1–§11.4 were written BEFORE any full-corpus
   model call; §11.5–§11.9 AFTER the result**, each saying so in its heading.
4. **`PLAN.md` §0.5 (work logging) and §1 (guardrails)** before anything else.

`research/01_*` and `research/02_*` are **SUPERSEDED**. `research/05_*` describes the
`Comments`-era gate and **does not transfer**.

## Mandatory working rules

Narrate every step in your visible output **and** persist it to `WORKLOG.md` as you go — not at
the end. `STARTED` before each action, `DONE`/`FAILED`/`BLOCKED` after. **Append only; never
edit a past entry** — corrections go in a *new* entry. Format: `PLAN.md` §0.5.

State `Idempotent: yes/no` on every `STARTED`. Track cumulative Jev spend on every entry that
makes API calls. **Never log secrets.** Key is in `.env` (gitignored) as `TYPESAFE_API_KEY`.

**Verify a fix by checking its output, not by checking that it ran.** `0 calls, $0.00` is not
evidence that nothing changed. This repo has been bitten by that three times.

**THE REPO IS PUBLIC.** Commit as `KevinArce <iav.kevinarce@ufg.edu.sv>`.
**Ask before pushing.**

---

# THE NEXT TASK — Kepler cross-mission validation

**This is the single highest-value thing left.** Everything so far rests on one corpus, one
mission, one epoch, checked by nobody outside this repository. A second corpus is the one thing
that changes that. `PLAN.md` §8 item 2.

## ⚠️ §8 item 2 is NOT ready to run as written. It was scouted 2026-09-21 — read this first.

Three checks against the live archive. **All three change the task, and skipping them will burn
a session.**

### 1. The target field is right, but the access path is unresolved

`fpwg_comment` in the Kepler Certified False Positive table is documented as a **"Free text
field with FPWG comments"** — genuinely the right target.
[Column docs](https://exoplanetarchive.ipac.caltech.edu/docs/API_fpwg_columns.html).

| route tried | result |
| :--- | :--- |
| TAP `select … from fpwg` | **absent from `TAP_SCHEMA.tables`**; archive TAP docs confirm fpwg is not served |
| legacy API `table=fpwg` | **"not a valid table"** — same for `keplerfpwg`, `fpwgtable`, `koifpwg` |
| legacy API in general | **alive** — `table=cumulative` returned 95 KB, so the API is not dead |

**Task 0 is resolving this**: the interactive web-UI download, archive support, or a table name
not yet found. **If the table cannot be obtained, STOP and reconsider the corpus.**

### 2. `koi_comment` is a trap. Do not substitute it.

It is in TAP, it is easy to get, and it is **not prose** — it is `---`-delimited flag codes:

```
K00966.01  FALSE POSITIVE  MOD_SEC_DV---MOD_SEC_ALT---HAS_SEC_TCE
K00965.01  FALSE POSITIVE  DEEP_V_SHAPED---HAS_SEC_TCE---CENT_RESOLVED_OFFSET---EPHEM_MATCH
```

- **It is an enumerable categorical field.** One-hot encoding captures it *completely*, so
  bag-of-words is **exact** — and the study's central comparison (structured judgments beat
  TF-IDF) becomes untestable.
- **Those codes ARE the vetting rationale** — the Robovetter's stated reasons for the
  disposition. This is the `Comments`-field leakage again, only more direct.

**Register `koi_comment` as an excluded source in the pre-registration**, so the temptation is
settled in writing before the easy path presents itself.

### 3. There may be no positive class — this is a design question, not a detail

`fpwg_disp_status` ∈ *certified FP · certified FA · not examined · pending · possible planet*.
**A table of certified false positives has no positives.** The label must come from a join, and
the corpus becomes "KOIs the FPWG examined" — **heavily FP-skewed and selected on the outcome.**

Several defensible corpus definitions exist. **Pick and register one before seeing base rates.**

## The sequence — do not reorder it

| # | step | model calls |
| ---: | :--- | :--- |
| 0 | **Resolve table access.** If impossible, stop and reconsider — do not drift to `koi_comment`. | 0 |
| 1 | **Ingest and characterise:** n, base rate, how many rows have non-empty `fpwg_comment`, median length. **Read 30 rows by hand before writing a single question** — a "free text field" can still be terse codes in practice. | 0 |
| 2 | **Measure the noise floor and MDE**, as `026_noise_floor.py` did. **The MDE depends on n and cannot be known in advance.** | 0 |
| 3 | **PRE-REGISTER as §11.10 / A-40. Commit and push BEFORE the first Kepler model call.** Corpus definition, label, excluded sources (naming `koi_comment`), gates, MDE, and **what counts as the effect failing to transfer.** | 0 |
| 4 | **Design questions against Kepler text.** `2026-09-20.r6` was written for TESS prose about speckle imaging and RV follow-up — **do not assume it transfers.** Run a question-design gate as TASK B did. | ~$0.06 |
| 5 | **Then spend.** Step 3 equivalent, ~$0.25. | ~$0.25 |

**Row 3 is the one that matters.** It will feel like a follow-up arm rather than a new study,
which is exactly when pre-registration gets skipped — and it is the habit the entire credibility
of this project rests on.

## Both outcomes are publishable. Decide the reading in advance.

| outcome | what it means |
| :--- | :--- |
| effect **survives** | the finding is about follow-up prose in general → a full paper becomes reasonable |
| effect **vanishes** | it was TESS/ExoFOP-specific → a **real negative result**, and the framing becomes "beware: this does not transfer" |

**Register that table before running.** Deciding after seeing the number is the one thing that
would undo what makes this project worth anything.

**Cost is not the constraint here. Corpus definition and question design are.**

---

## State you are inheriting

- `data/exonotes.duckdb` — `toi_snapshot`, `analysis_set`, `analysis_set_obsnotes` (**the
  corpus**, 1,482 rows / 1,388 TIC / base 0.5378), `obsnotes_raw`, `obsnotes_text`,
  `obsnotes_coverage`, `gate_g1_obsnotes`, `noise_floor_obsnotes`, `leakage_obsnotes`,
  `g5_arm_obsnotes`, `jev_features_obsnotes` (1,482 × 10, checksum above),
  `jev_features_obsnotes_s2b`.
- `data/cache/step3/` — **exactly 1,382 responses**. `data/cache/g3/` the G3 arms.
  `data/cache/s2b/` **203**. **Re-runs are free.** `data/` is gitignored.
- `src/exonotes/questions.py` — **`2026-09-20.r6`**, 7 predictive + 3 label-echo. **FROZEN** for
  the TESS study; bumping it invalidates the cache and costs ~$0.24. **A Kepler question set
  should be a NEW version string, not an edit to this one.**
- `src/exonotes/leakage.py` — `OBSNOTES_PATTERNS` (10 clauses) is registered;
  `COMMENTS_PATTERNS` is provenance only.
- Environment: Python 3.14 venv at `.venv`. **Do not rebuild it.** Run `.venv/bin/python scripts/…`.

### CI — it costs money

`.github/workflows/gates.yml` runs the full pipeline cold and asserts all six gates
(`040_verify_gates.py`, mutation-tested by `041_test_verify_gates.py`). §11.9 A-39.
**~$0.33 per run, cold every time**, dispatch + **monthly cron** — no `push` trigger, on purpose.
First run: [35547134433](https://github.com/KevinArce/ExoNotes/actions/runs/35547134433),
success, 10.9 min, 12/12.

**It asserts registered criteria, not the published numbers**, because corpus drift is unbounded.
A shift beyond 5× the A-33 sd raises a **NOTICE, not a failure**. **Do not "tighten" this into
equality** — that turns normal archive drift into a red badge, which is how badges get ignored.

### Release checklist — three files can silently diverge

1. **`CITATION.cff`** — bump `version` and `date-released`. **These go stale.**
2. **`README.md`** — badge needs no change; it uses the **concept** DOI.
3. **`.zenodo.json`** — only if authorship, licence or description changed. It deliberately
   omits `version`/`publication_date` so Zenodo reads the git tag. **Zenodo ignores
   `CITATION.cff` when `.zenodo.json` exists and does not merge them.**

### Defects found and fixed — do not re-litigate

1–16: see `WORKLOG.md` (pscomppars removed; corpus 2,721 rows; S2 group leak; G2 dilution
control; MDE; G5 regex; `toi` dropped from state; model pinned; `etta` unusable for the bulk
pull; zero-byte body is a throttle, not "no notes"; `pd.read_csv(delimiter='|')` mis-parses
pipes **silently**; HTML entities never decoded).
17. **The `Comments`-derived G5 clauses are inoperative on obsnotes** — `L2`, `L4b`, `L5` fire on
    **0** rows. Replaced by `L6`/`L7`/`L8`. §11.4.
18. **Six of eight r4 predictive questions had almost no support here.** §11.3 A-19.
19. **`jev-1.13.0` drifts over time** — mean |Δ| 0.0001 minutes apart, 0.0049 an hour apart.
    Quantified end-to-end (A-33): moves ΔAUC by sd 0.0010; **G2 survives 10×**. Confirmed against
    a real cold run at ~28 h (A-39a).
20. **A too-good-to-be-true number caught a bug** — ρ = 1.000 because `s3.CACHE` was not patched
    and no call was made.
21. **The Step 3 cache race** — per-key lock. §11.8 A-38. **Verified under real CI concurrency:
    1,382 calls for 1,382 states, 0 failed.**
22. **Two values of B (0.9051 vs 0.9044) are input row order** — 0.0008 AUC, ~10× below the MDE.
23. **§10 item 2's note-count medians were measured on the `Comments` set.** A-34.
24. **Two result JSONs were silently overwritten by cached re-runs.** Cost fields are now
    `*_this_run` plus a `paid_run` block.
25. **`CITATION.cff` described the ABANDONED corpus** for three sessions after the result, with
    no author and no numbers. Fixed 2026-09-21.
26. **`README.md` claimed "§11.5 is the only section written after the result"** — five sections
    are. The error **understated** how much was post-result, i.e. it flattered the study.

### Hypotheses tested and FAILED — do not re-raise

- **"Known Planets inflate baseline B."** They do not (0.9231 KP-excluded vs 0.9128 all-in).
- **"The cross-platform 5×10⁻⁴ AUC offset matters."** ~12× below the MDE.
- **"The run-together `832nmNo secondary sources` text flips the imaging judgment."** It does not.
- **"`false positive` is a label marker."** Fires at P(y=1)=**0.613**, *above* the 0.5378 base
  rate. Not stripped. A-26.
- **"S2b will collapse the G4 gain."** It does not — G4 rises to +0.1296. A-37.

---

## Environment notes

- `.venv` exists (Python 3.14.7, catboost 1.2.10, duckdb 1.5.5, pandas 3.0.6, matplotlib 3.11.2,
  etta 0.1.1).
- `typesafe-sdk`, `aiohttp` and `httpx` are **not** installed — scripts use raw `urllib` with a
  `ThreadPoolExecutor`. **`requirements.txt` is part of the reproduction contract; do not add
  dependencies mid-study.** Validators (pyyaml, cffconvert) go in a scratch venv.
- Live TypeSafe docs: https://docs.typesafe.ai/llms.txt (append `.md` to any page path).
  **Read `model-jaggedness/jev-1.13` before writing any new question.**
- **Run model-vs-model comparisons on one platform.** macos/arm64 and linux/x64 differ by 5×10⁻⁴.
- Rebuilding the TESS pipeline from a clean clone: `028_obsnotes_pull.py` (~6 min, $0) →
  `034_step3_features.py` (~7 min, ~$0.24) → `035_gates_g2_g6.py` (~2 min, $0) →
  `036_gate_g3_stability.py` (~2 min, ~$0.06) → `037_reliability.py` (~1 min, $0) →
  `038_drift_sensitivity.py` (~2 min, $0) → `039_gate_g4_s2b.py` (~1 min, ~$0.03) →
  `040_verify_gates.py` (instant, $0; add `--require-paid` on a cold cache).
  `041_test_verify_gates.py` mutation-tests the verifier, also $0.

---

## If you would rather not do the Kepler work

It is the highest-value step, but it is not the only one. Each of these is real:

- **Nothing external has checked this.** Someone else running the pipeline closes the gap that
  CI cannot. A green badge is this pipeline checking itself.
- **An RNAAS note on the leakage finding alone** — `Comments` restates the label in 47.9% of
  2,725 rows; `pscomppars` leaks at P=0.995 vs 0.074. Needs no further validation and is
  immediately useful to anyone doing ML on these catalogues.
- **Contact ExoFOP** with that same finding, now that a DOI exists.
- **The S2 arm is noisier than its interval suggests** — ~±0.005 seed noise, one fit.
  Repeated-fit aggregation would tighten it. Not registered; would be a new arm.
- **Per-question reliability diagrams** need more hand-labelled cases than the 27 that exist.
  A-36.
