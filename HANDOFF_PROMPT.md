# ExoNotes — handoff to the next session

You are picking up the ExoNotes project. **Work from the repo, not from memory.**

---

## ⚠️ START HERE — the design changed on 2026-09-20 (audit 01)

An adversarial pre-flight review was run before TASK A and found **four defects that change the
registered design**. They are written up in
[`AUDIT_01_PREFLIGHT_REVIEW.md`](./AUDIT_01_PREFLIGHT_REVIEW.md) and registered as amendments
**A-1 … A-8** in [`PREREGISTRATION.md`](./PREREGISTRATION.md) §11.

**The two that will silently ruin the study if you skip them:**

1. **Gate G2 had no zero point.** Adding eight *pure-noise* columns to baseline B costs
   **−0.0112 AUC** (mean of 5 seeds; every seed's paired bootstrap CI excludes zero). That is
   over 4× the SE of the G2 statistic, which is 0.0026. **A reported ΔAUC of 0.000 is therefore
   not a null — it is ~+0.011 of real signal cancelling dilution.** `PREREGISTRATION.md` §8 would
   have mapped that onto *"Stop. Write the negative result."* Every D-vs-B comparison is now read against the **B+N** arm from
   [`scripts/026_noise_floor.py`](./scripts/026_noise_floor.py).
2. **Gate G5's regex is dead code on this corpus.** [`src/exonotes/leakage.py`](./src/exonotes/leakage.py)
   was written for 30-character `Comments`; two of its five clauses are anchored `^…$`. On real
   observer-note text it fires on **1 of 20 TICs**. G5 would pass trivially and §8 reads a G5 pass
   as *"the effect was not label echo."* **TASK B2 re-derives it.**

Nothing has been run on the full corpus. Every criterion is still being fixed before the result,
which is the only window in which it can be. **Do not open that window wider.**

---

## Read first, in this order

1. **[`AUDIT_01_PREFLIGHT_REVIEW.md`](./AUDIT_01_PREFLIGHT_REVIEW.md)** — all 13 findings, the two
   hypotheses that were tested and failed, and what changed as a result. **Read this first; it is
   the most recent word on every other document.**
2. **[`PREREGISTRATION.md`](./PREREGISTRATION.md)** — the binding document. §11 amendments A-1…A-8
   **override** the body text where they disagree. §2 is still provisional.
3. **`WORKLOG.md` — read the TAIL first.** Append-only; the end is current.
4. **`PLAN.md`** — §0.5 (work logging) and §1 (guardrails) before anything else. **Treat the rest
   as a hypothesis, not a specification: eight of its claims have been found wrong, and audit 01
   found four more.**
5. `research/05_question_design_gate.md` — how the question set was tested, and why that test
   **does not transfer to the new corpus**.

`research/01_*` and `research/02_*` are **SUPERSEDED**. Do not build from them.

## Mandatory working rule — step logging and resumability

Not optional, applies to everything.

Narrate every step in your visible output **and** persist it to `WORKLOG.md` as you go — not at
the end. Write a `STARTED` entry **before** each action and a matching `DONE`/`FAILED`/`BLOCKED`
entry **after** it. **Append only; never edit a past entry.** Format: `PLAN.md` §0.5.

An orphan `STARTED` with no outcome is the interruption marker.

State `Idempotent: yes/no` on every `STARTED`. Track cumulative Jev spend on every entry that
makes API calls. **Never log secrets.** The key is in `.env` (gitignored) as `TYPESAFE_API_KEY`.

**THE REPO IS PUBLIC:** https://github.com/KevinArce/ExoNotes — every commit is immediately visible.

**Git identity:** commit as `KevinArce <iav.kevinarce@ufg.edu.sv>`.

---

## The corpus (unchanged since 2026-09-20)

**Not the TOI `Comments` field.** `download_obsnotes`, observer notes only,
`Groupname != 'tfopwg'`. Rationale and measurements: `PREREGISTRATION.md` §1.

**One correction from audit 01 (A-10):** across all 79 cached notes, `Groupname` takes exactly two
values — `'tfopwg'` and **NaN**. There is no `SG1`-style groupname in the data, so the filter is
in practice `Groupname IS NULL`. It works, but assert it in TASK A rather than trusting it.

---

## State you are inheriting

- `data/exonotes.duckdb` — `toi_snapshot`, `analysis_set`, `ingest_provenance`, `ingest_stats`,
  `baseline_results`, `baseline_summary`, **`noise_floor`** (new). Built on the **`Comments`**
  corpus; still valid as the numeric/label foundation.
- **G1 PASSED** on that set: baseline B (numeric) **0.9154** AUC vs A 0.5000.
- **Baseline C (TF-IDF) 0.9691 AUC is LEAKAGE, not signal** — never cite it without that.
- **The G2 noise floor, MDE and oracle bar** — `research/data/noise_floor_2026-09-20.json`.
- `src/exonotes/questions.py` — set `2026-09-20.r4`, 8 predictive + 3 label-echo. **Provisional.**
- `src/exonotes/leakage.py` — the G5 regex. **Known inoperative on obsnotes (A-3).**
- `data/cache/` — content-addressed Jev responses and per-TIC obsnotes. **Re-runs are free.**
- Environment: Python 3.14 venv at `.venv`. **Do not rebuild it.** Run `.venv/bin/python scripts/…`.
- **Jev spend to date: ~$0.0046.**

### Plan defects already found and fixed — do not re-litigate
1. `pscomppars` removed from the feature path (predicts the label at P=0.995 vs 0.074).
2. `references_other_object` → `TIER_LABEL_ECHO`, renamed `contains_object_designation`.
3. Corpus is 2,721 rows, not ~7,000.
4. No comment timestamps exist.
5. The question set was verified on the wrong text length distribution.
6. S2 was unimplementable as written; now uses `date_toi_alerted`.
7. S2 violated S1's own no-split-within-a-host rule — fixed in `PREREGISTRATION.md` §4 S2a.
8. §2.0's leakage regex was never recorded — now `src/exonotes/leakage.py`.
9. **G2 had no dilution control** — fixed, §11 A-1.
10. **No MDE; §8.1 planned observed power** — fixed, §11 A-2.
11. **G5's regex does not fire on obsnotes** — TASK B2, §11 A-3.
12. **`toi` was being sent to Jev on every call for no reason** — removed, §11 A-4.

### Two hypotheses that were tested and FAILED — do not re-raise them
- **"Known Planets inflate baseline B."** They do not. B = 0.9128 all-in, **0.9231 with KP
  excluded**, 0.9211 KP-only. No KP-excluded arm is warranted.
- **"The cross-platform 5×10⁻⁴ AUC offset matters."** It is real but ~15× smaller than the MDE of 0.0073.
  Keep the single-platform rule; stop quoting the 10⁻³ figure as a decision threshold.

---

## Scope of the NEXT session

> **Binding order: A → A2 → B and B2 → C.** No step may start before its predecessor's `DONE`
> entry is in `WORKLOG.md`.

### TASK A — acquire the obsnotes corpus (~2.3 h, $0 Jev)

Pull observer notes for all **2,573 TIC** (`etta.download_obsnotes(tic=...)` — **note the
keyword**; the first positional arg is `tag` and silently returns an empty table). ~3.21 s/TIC.

**Build on [`scripts/027_obsnotes_recon.py`](./scripts/027_obsnotes_recon.py)** — it already caches
per-TIC under `data/cache/obsnotes/`, so the pull is resumable and a re-run is free. Parallelise
with a bounded pool; retry `RemoteDisconnected` (observed once in 10 calls).

Preconditions and assertions, all from audit 01:
- **Assert non-empty on known-good TICs** — a throttled or mis-parameterised call returns a
  well-formed empty table, not an error.
- **Assert the `Groupname` domain** is `{'tfopwg', NULL}` (A-10). If any other value appears, the
  corpus definition in §1.1 no longer describes what is being selected — **stop and report**.
- **Write `null`, not bare `NaN`** (A-11). 20 of the 30 existing cache files are not valid
  RFC-8259 JSON. Use `json.dumps(..., allow_nan=False)` after coercing, and re-serialise the 30.
- Persist to DuckDB, strip HTML, record checksums in `PROVENANCE.md`.
- **Report the realised base rate and coverage**, and P(has note | y=1) vs P(has note | y=0). The
  recon estimate is 0.80 vs 0.53 on n=30 (A-7). It is **not** grounds to change any criterion.

### TASK A2 — re-establish G1 and re-measure the noise floor on the real row set ($0 Jev)

1. **G1 on the obsnotes row set.** Criterion, pre-registered: **B ≥ 0.85 AUC and B > A by a
   bootstrap 95% CI excluding zero.** A different row set is a different pipeline.
2. **Re-run [`scripts/026_noise_floor.py`](./scripts/026_noise_floor.py) on the realised rows.**
   The dilution penalty and the MDE are both functions of *n*, and the ~1,715-TIC projection is
   20/30 extrapolated — the true interval is roughly 1,200–2,140 TIC (A-12). Pass `--k` equal to
   the final Jev feature count once TASK B has frozen it.
3. **Also report B's AUC on excluded vs included rows** (A-7). If B is materially weaker on the
   included subset, D is being compared on easier ground and the write-up must say so.

### TASK B — re-run Step 2.5 on observer-note text (~$0.01)

Same method as [`scripts/025_question_gate.py`](./scripts/025_question_gate.py): ~20–25 cases drawn
**verbatim** from real observer notes, across the true length distribution, each question's
positive / negative / nearest confusable, every answer inspected by eye.

**Changes from last time, all binding:**
- **Blind the cases (A-9).** Sample programmatically across the length distribution and **withhold
  the labels until every answer has been inspected**, then attach them. The r4 cases carried
  `y=` and were hand-picked by someone who could see it.
- **Pin the model (A-5).** `MODEL = "jev-1.13.0"`, not `"jev-latest"`. Assert
  `response["model"] == MODEL` before persisting. `jev-latest` sits inside the cache key, so a
  version bump silently mixes two models in one feature matrix.
- **Drop `toi` from the state (A-4).** The registered state is now `{"notes": ...}`. No question
  reads `toi`, and it hands the model a catalogue designation that G5 structurally cannot strip.
- **Check each candidate against the oracle bar (A-2).** A feature needs roughly **0.65 univariate
  AUC** against the label before G2 can see it (a feature at 0.59 is invisible). A question that cannot plausibly clear that is not
  worth a column.
- **Restore the two deleted questions as candidates** — `reports_on_target_detection` and
  `indicates_followup_complete` (`PREREGISTRATION.md` §2.3). They were deleted for absence of
  support in `Comments`, not for being bad questions.
- **Re-freeze with a new `QUESTION_SET_VERSION` and record it in `PREREGISTRATION.md` §11.**

Apply the §2.4 writing rules literally, including the one added last session:
**when the model keeps making an inference, name that inference and forbid it explicitly.**
That is what fixed `mentions_instrumental_artifact` after two rounds of better positive
descriptions had failed.

### TASK B2 — re-derive the G5 clause set on observer-note text ($0 Jev, no Jev calls)

`src/exonotes/leakage.py` fires on **1 of 20** cached observer-note TICs. `L1`, `L2`, `L4a` and
`L4b` are all **0/20**. The arm would be ~95% identical to the full arm.

The leak is real, it just has a different shape: `NEB`/`BEB`/`cleared`/`retired`/`false positive`
are all 0/20 — the `Groupname` filter genuinely works — but **`TOI-\d+` fires 13/20**, and one
note opens *"Extracted KOI12 observing note from ExoFOP-Kepler."*

Derive the new clauses on the **full pulled corpus**, measure n and P(y=1) per clause exactly as
§5 does, audit the marginal rows by eye, and **register the result in §11 before TASK C**.
Keep `L5_explicit_disposition` as the tripwire: **if L5 fires on any row, the corpus filter has
failed and Step 3 stops** — that is a pipeline bug, not a finding.

### TASK C — Step 3, the full run (~$0.18)

Only after A, A2, B and B2. `PLAN.md` §6 Step 3. Async client, bounded semaphore, one request per
row, all questions per request, content-addressed cache, persist **full raw response JSON**.

- **Tripwire: if projected cost exceeds ~$0.50, stop and check the state size.**
- Then evaluate G2–G6 **against the B+N and B+meta reference arms**, with ΔAUC aggregated as
  §11 A-6 registers it: pool OOF within a repeat, score each repeat, average the repeats;
  bootstrap resamples TIC groups and uses **the same resample for both models**.

---

## 🚩 OPEN ITEMS FOR THE USER

**There are none. Both previous items are closed and verified.** Start at TASK A.

1. ~~Force-push to correct commit attribution~~ — **CLOSED 2026-09-20T01:14Z, verified again
   after the audit-01 push.** All 13 commits on `origin/master` are authored *and* committed by
   `KevinArce <iav.kevinarce@ufg.edu.sv>`; `git log --format='%an <%ae>' | sort -u` returns
   exactly one identity. `20c11ae` is **not an ancestor of `origin/master`** and survives only as
   a dangling local reflog object. Ordinary `git push` works — the branch is not diverged.
   *(The previous handoff listed this as pending after it had already been done, and audit 01's
   first draft repeated the error. Verify before carrying an open item forward.)*
   **Standing caveat:** GitHub still serves unreachable commits by direct SHA for some time. The
   attribution is off the branch, not cryptographically erased.

2. ~~Clean-clone reproduction~~ — **CLOSED 2026-09-20**. `PLAN.md` §11.6 is 10/10 and the check
   re-runs weekly. Note what it does **not** cover: it reruns ingest and baselines only and makes
   **no API calls**, so it says nothing about Step 3's reproducibility (A-5).

---

## Environment notes

- `.venv` exists (Python 3.14.7, catboost 1.2.10, duckdb 1.5.5, pandas 3.0.6, etta 0.1.1).
- `typesafe-sdk` is **not** installed. `scripts/025_question_gate.py` uses raw `urllib` with a
  hardened retry and works without it.
- Live TypeSafe docs: https://docs.typesafe.ai/llms.txt (append `.md` to any page path).
  Noul supports a structured `criteria: {true, false}` — use it; §2.4 requires the negative case
  be stated and that is the documented field for it.
- This project's memory directs that the `typesafe-ai` skill be loaded for work here.
- **Run model-vs-model comparisons on one platform.** macos/arm64 and linux/x64 differ by 5×10⁻⁴
  on identical inputs. It is ~15× below the MDE, so it is a hygiene rule, not a decision rule.
