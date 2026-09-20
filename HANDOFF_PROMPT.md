# ExoNotes — handoff to the next session

You are picking up the ExoNotes project. **Work from the repo, not from memory.**

---

## ⏱️ DO THIS FIRST — [`SIDEQUEST_01_CI_REPRODUCTION.md`](./SIDEQUEST_01_CI_REPRODUCTION.md)

A one-shot task that comes **before** the main sequence below. Everything is built and locally
verified; all that remains is to run it:

> **Actions → reproduce → Run workflow** on `master`, then read the summary.

It closes `PLAN.md` §11.6 **item 10** (clean-clone reproduction), the last open item on the
pre-publication checklist, which ExoFOP throttling has blocked for two sessions. ~10–15 min,
$0, no API calls. Log the outcome in `WORKLOG.md`, then come back here and start TASK A.

**Until it goes green, do not describe this repository as reproduction-verified.**

---

## Read first, in this order

1. **`WORKLOG.md` — read the TAIL first.** It is append-only; the end is current. The entries
   from `2026-09-20T00:00Z` onward are this session and contain everything below in full detail.
2. **`PREREGISTRATION.md`** — **committed 2026-09-20. This is now the binding document.**
   §2 is *provisional* and §11 lists what must be recorded before Step 3.
3. **`PLAN.md`** — §0.5 (work logging) and §1 (guardrails) before anything else. **Treat the rest
   as a hypothesis, not a specification: eight of its claims have now been found wrong.**
4. `research/05_question_design_gate.md` — how the question set was tested, and why that test
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

**Git identity:** commit as `KevinArce <iav.kevinarce@ufg.edu.sv>`. Both local and global config
are already correct. One earlier commit was mis-attributed to `ExoNotes
<arcetechnologies@gmail.com>` and has been amended.

---

## ⚠️ THE BIG CHANGE THIS SESSION — the corpus switched

**The project no longer uses the TOI `Comments` field.** The owner decided on 2026-09-20 to
switch to **`download_obsnotes`, observer notes only** (`Groupname != 'tfopwg'`).

**Why**, measured on 30 TIC (`research/data/obsnotes_recon_2026-09-19.json`):
- `Master Disp: <value>` — **the label, written out verbatim** — appears in **100%** of TICs.
  Unfiltered, obsnotes is *strictly worse* than `Comments` (100% leakage vs 53.4%).
- Dropping `Groupname == 'tfopwg'` leaves **67% of TICs** with a median **780 characters** of real
  observer prose and **zero** residual `*Disp:` strings. The leakage goes from total to nil on one
  mechanical filter. `Comments` has no equivalent cut.

**Consequences you must not skip:**
1. **The Step 2.5 gate does NOT transfer.** `QUESTION_SET_VERSION = 2026-09-20.r4` scored 101/103
   **on `Comments` text** (30-char fragments). Observer notes are ~26× longer and differently
   written. **Re-run Step 2.5 on real observer-note text and re-freeze the set with a new version
   before Step 3.** Skipping this repeats the exact mistake that already cost this project once.
2. **Two deleted questions must be reconsidered.** `reports_on_target_detection` and
   `indicates_followup_complete` were deleted for having no support in `Comments`. Observer notes
   are full of exactly that content ("cleared 6/6 neighbors to 2.5'", "No secondary sources were
   detected"). See `PREREGISTRATION.md` §2.3.
3. **G1 must be re-established** on the new row set (~1,814 rows / ~1,715 TIC, down from
   2,721 / 2,573). A different row set is a different pipeline.
4. **The base rate of the observer-note subset is unknown** until the full pull, and is probably
   not label-neutral. Report it as measured; it is not grounds to change any criterion.

---

## State you are inheriting

- `data/exonotes.duckdb` — `toi_snapshot`, `analysis_set`, `ingest_provenance`, `ingest_stats`,
  `baseline_results`, `baseline_summary`. Built on the **`Comments`** corpus; still valid as the
  numeric/label foundation.
- **G1 PASSED** on that set: baseline B (numeric) **0.9154** AUC vs A 0.5000.
- Baseline C (TF-IDF) 0.9691 AUC is **LEAKAGE, not signal** — never cite it without that.
- `src/exonotes/questions.py` — frozen set `2026-09-20.r4`, 8 predictive + 3 label-echo.
- `src/exonotes/leakage.py` — the G5 regex, measured per clause.
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
7. **NEW:** S2 violated S1's own no-split-within-a-host rule — 30 TIC straddle the cutoff.
   Fixed in `PREREGISTRATION.md` §4 S2a.
8. **NEW:** §2.0's leakage regex was never recorded, so the repo's headline leakage measurement
   was unreproducible. Now `src/exonotes/leakage.py`.

---

## Scope of the NEXT session

### TASK A — acquire the obsnotes corpus (~2.3 h, no Jev spend)
Pull observer notes for all **2,573 TIC** (`etta.download_obsnotes(tic=...)` — note the keyword;
the first positional arg is `tag` and silently returns an empty table). ~3.21 s/TIC.
**Build on `scripts/027_obsnotes_recon.py`** — it already caches per-TIC under
`data/cache/obsnotes/`, so the pull is resumable and a re-run is free. Parallelise with a bounded
pool; retry `RemoteDisconnected` (observed once in 10 calls). **Assert non-empty on known-good
TICs — a throttled or mis-parameterised call returns a well-formed empty table, not an error.**
Persist to DuckDB, strip HTML, record checksums in `PROVENANCE.md`.

### TASK B — re-run Step 2.5 on observer-note text (~$0.01)
Same method as `scripts/025_question_gate.py`: ~20–25 cases drawn **verbatim** from real observer
notes, across the true length distribution, each question's positive / negative / nearest
confusable, every answer inspected by eye. Restore the two deleted questions as candidates.
Re-freeze with a new `QUESTION_SET_VERSION` and **record it in `PREREGISTRATION.md` §11.**

Apply the §5 writing rules literally, plus the one this session added:
**when the model keeps making an inference, name that inference and forbid it explicitly.**
That is what fixed `mentions_instrumental_artifact` after two rounds of better positive
descriptions had failed.

### TASK C — Step 3, the full run (~$0.18)
Only after A and B. `PLAN.md` §6 Step 3. Async client, bounded semaphore, one request per row,
all questions per request, content-addressed cache, persist **full raw response JSON**.
**Tripwire: if projected cost exceeds ~$0.50, stop and check the state size.**

---

## 🚩 OPEN ITEMS FOR THE USER — do not decide these alone

1. **A force-push is pending and has NOT been run.** Commit `20c11ae` was mis-attributed and has
   been amended to `6b28005`. It was already pushed, so the branch is `ahead 2, behind 1` and
   publishing the correction needs:
   ```
   git push --force-with-lease origin master
   ```
   This rewrites public history. **Ask before running it.** Leaving the old commit published and
   simply using the right identity from here on is a legitimate alternative.

2. **Clean-clone reproduction (checklist item 10) is STILL UNVERIFIED — but it is now
   actionable.** See **[`SIDEQUEST_01_CI_REPRODUCTION.md`](./SIDEQUEST_01_CI_REPRODUCTION.md)**:
   a CI workflow now runs the check from a GitHub runner, whose IP is not the one ExoFOP is
   throttling. Run it before anything else. ExoFOP has been throttling the **bulk**
   `download_toi.php` endpoint from this host continuously since 2026-09-19 — probed five times,
   always `http=000, connect≈0.4 s, size=0`. Per-TIC endpoints answer normally, so this is
   endpoint-specific, not an outage.
   **Do not describe the repo as reproducible until this passes:**
   ```
   git clone https://github.com/KevinArce/ExoNotes /tmp/cc && cd /tmp/cc
   uv venv --python 3.14 .venv && VIRTUAL_ENV=.venv uv pip install -r requirements.txt
   .venv/bin/python scripts/01_ingest.py && .venv/bin/python scripts/02_baselines.py
   ```
   Passes when G1 reproduces (B ~0.9154 AUC vs A 0.5000). **Re-probe first** — one `curl` saves
   20 minutes:
   ```
   curl --max-time 30 -o /dev/null -w '%{http_code} %{size_download}\n' \
     'https://exofop.ipac.caltech.edu/tess/download_toi.php?output=csv'
   ```
   `01_ingest.py` now fails in a bounded way with an actionable message instead of hanging
   forever, so the test is at least safe to attempt.

---

## Environment notes

- `.venv` exists (Python 3.14.7, catboost 1.2.10, duckdb 1.5.5, pandas 3.0.6, etta 0.1.1).
- `typesafe-sdk` is **not** installed. `scripts/025_question_gate.py` uses raw `urllib` with a
  hardened retry and works without it.
- Live TypeSafe docs: https://docs.typesafe.ai/llms.txt (append `.md` to any page path).
  Noul supports a structured `criteria: {true, false}` — use it; §5 requires the negative case be
  stated and that is the documented field for it.
- This project's memory directs that the `typesafe-ai` skill be loaded for work here.
