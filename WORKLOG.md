# ExoNotes Work Log

Append-only. Format and rules: `PLAN.md` §0.5. **Never edit or delete a past entry** — corrections
go in a new entry. Resumption procedure is in §0.5; read the tail of this file first.

---

## [2026-09-19T15:56Z] SESSION START — Claude Opus 5
**Scope:** Research Jev for astrophysics; verify prior dossier; plan an MVP.
**State at start:** `research/01_*`, `research/02_*`, `task.md`. No code, no API key.
---

## [2026-09-19T16:07Z] RESEARCH — DONE
**Doing:** Verified `research/01_*` and `research/02_*` against live TypeSafe docs and independent
third-party evaluations.
**Result:** Core specs confirmed (`jev-1.13.0`, $0.042/MTok in / free out, 64k/32k tokens,
`POST /v1/systemone`, text-only, RLCD). **Ten claims did not survive verification** — most
seriously: calibration is NOT near-zero ECE out of distribution (independent measurement: ECE
0.107 vs 0.024 noise floor, refit T=2.74, with Choice/Score and Noul miscalibrating in OPPOSITE
directions), and `confidence` is a distribution-shape statistic, not P(correct).
**Artifacts:** `research/03_jev_astrophysics_evidence_based_assessment.md` (§1.4 itemizes all ten).
**Decision:** The prior dossier's flagship `TESS-RoboVetter` is the WEAKEST proposal — it competes
against ExoMiner (R@P0.99=0.936), ExoMiner++, LEO-Vetter, TRICERATOPS, all of which ingest flux and
pixel data Jev physically cannot read. Reprioritized to `ExoNotes` (semantic featurization of
free text), where no competing model exists.
**Jev spend:** $0.00 (no API key at this point)
**Next:** Write the MVP plan.
---

## [2026-09-19T16:26Z] PROJECT RENAME — DONE
**Doing:** `/Users/<user>/Projects/Jev` → `/Users/<user>/Projects/ExoNotes` (user request).
**Result:** Renamed. Converted absolute `file:///…/Jev/…` links in `research/README.md` to relative
paths so they survive future renames.
**Side effect handled:** Claude memory is keyed by project path — copied
`~/.claude/projects/-Users-<user>-Projects-Jev/memory/` → `-Users-<user>-Projects-ExoNotes/memory/`,
preserving the "always load the typesafe-ai skill" instruction. Old dir left in place, harmless.
**Note (not caused by this session):** `task.md` was moved to `~/.Trash` at 16:33 by a Finder/IDE
action (`rm` does not use the Trash). Left in place; README reference removed. Restore with
`mv ~/.Trash/task.md /Users/<user>/Projects/ExoNotes/`.
**Next:** MVP plan.
---

## [2026-09-19T16:26Z] PLAN — DONE
**Artifacts:** `PLAN.md` (§0–§10), `README.md`.
**Key design decision:** Jev is the FEATURIZER, gradient boosting is the PREDICTOR,
cross-validation is the arbiter. This absorbs the OOD miscalibration found above — a
systematically overconfident probability is still a monotone, informative feature.
**Key risk identified:** ExoFOP comments may be edited AFTER disposition is assigned, making
label-echo rather than prediction. A temporal split does not fix this. Mitigation: two question
tiers (`TIER_PREDICTIVE` / `TIER_LABEL_ECHO`), headline result uses predictive tier only. See
`PLAN.md` §2.
**Next:** Await API key.
---

## [2026-09-19T16:37Z] ENV SETUP — DONE
**Doing:** User added an API key to `.env`.
**Problem found:** Variable was named `JEV-API-KEY`. Hyphens are not legal in shell environment
variable names, and the SDK reads `TYPESAFE_API_KEY` — nothing would have picked it up.
**Result:** Renamed the variable in place; value untouched and never printed. Added `.gitignore`
(excludes `.env`, `data/`) and `.env.example`.
**Next:** Smoke-test the key.
---

## [2026-09-19T16:38Z] SMOKE TEST 1 — DONE
**Doing:** 7 draft questions (5 Noul, 2 Score) × 4 hand-written ExoFOP-style comments, one request
per comment, all questions batched.
**Command:** `python3 scripts/00_smoke_test.py`
**Idempotent:** yes
**Result — key works**, `jev-1.13.0`. **3 of 7 questions defective:**
  - `names_alternate_eclipse_source`: 0.370 on a comment explicitly reporting an NEB (should be
    high). Caught the surface fact, failed the one-step inference. Documented multi-hop weakness.
  - `reports_nearby_eclipsing_binary`: 0.710 on "possible EB" with no nearby source — conflated
    "EB mentioned" with "nearby EB reported".
  - `expresses_doubt_about_ephemeris`: 0.780 on "period is likely correct" — literal reading of
    hedging language, backwards for the science.
**Also measured:** 603–645 input tokens/call → ~$0.19 for 7,000 rows (cost model CONFIRMED).
Latency 550–1520ms vs advertised 70–500ms (cold sequential calls, not a careful benchmark).
Two-decimal probability quantization reproduced.
**Artifacts:** `research/data/smoke_2026-09-19.json`, `research/04_first_live_measurements.md`
**Jev spend this step:** ~$0.0001 · **running total:** ~$0.0001
**Next:** Revise the three defective questions and RE-TEST.
---

## [2026-09-19T16:40Z] SMOKE TEST 2 (verification) — DONE
**Doing:** Re-tested the three revised questions on the same four cases.
**Idempotent:** yes
**Result — 2 of 3 repaired:**
  - `reports_offset_eclipsing_binary`: 0.710 → **0.070** on the confusable; held at 0.870 / 0.070
    on positive / negative. FIXED.
  - `asserts_ephemeris_problem`: 0.780 → **0.050**; held at 0.890 on the true positive. FIXED.
  - `names_alternate_eclipse_source`: 0.370 → 0.590. Still a coin flip. NOT fixed.
**What did the work:** adding an explicit negative case ("answer no if…") to the instructions
repaired both fixable questions.
**Decision:** DROPPED `names_alternate_eclipse_source` rather than rewording a third time —
`reports_offset_eclipsing_binary` already captures the same fact with clean separation, and a
second question about one fact would add a near-0.5 noise column. Generalized into a plan rule:
when a question needs inference, deletion often beats rewording.
**Artifacts:** `research/data/smoke_revised_2026-09-19.json`, `research/04_*` §4.1–4.2
**Jev spend this step:** ~$0.0001 · **running total:** ~$0.0002
**Next:** Propagate into PLAN.md.
---

## [2026-09-19T16:46Z] PLAN UPDATE — DONE
**Result:** `PLAN.md` §5 now carries the verified question set (10 predictive + 3 label-echo);
added Step 2.5 (question-design gate, mandatory); async client now REQUIRED not optional; cost
figures replaced with measured values; two new question-writing rules.
**Added §0.5** — this work-logging and resumption protocol.
**Artifacts:** `PLAN.md`, `HANDOFF_PROMPT.md`, `WORKLOG.md`
**Next:** **STEP 1 — `scripts/01_ingest.py`** (PLAN.md §6). No Jev spend in Step 1 or Step 2.
---

## [2026-09-19T16:47Z] SESSION END — Claude Opus 5
**Completed:** Research verification, project rename, MVP plan, API key setup, two smoke-test
rounds, question set verified and reduced to 13.
**Not started:** Any pipeline code. `data/exonotes.duckdb` does not exist yet.
**Jev spend this session:** ~$0.0002
**Resume at:** STEP 1 (ingest). Use `HANDOFF_PROMPT.md`.
---

## [2026-09-19T22:55Z] SESSION START — Claude Opus 5
**Scope (assigned):** PLAN.md §6 Step 1 (ingest) and Step 2 (baselines A/B/C). STOP after Step 2.
Do NOT proceed to Step 2.5 or Step 3. Expected Jev spend: **$0.00** — neither step calls the API.
**State at start:** Last entry `SESSION END` (16:47Z), no orphan `STARTED`. `data/` does not exist.
No `src/`, no `pyproject.toml`. Only `scripts/00_smoke_test.py` exists.
**Read:** PLAN.md §0.5, §1, §2, §3, §5, §6, §7; research/04 (full); research/03 §1–§2.
---

## [2026-09-19T22:55Z] RESUMED — STEP 1 (ingest)
**Picking up at:** `Next:` field of the 16:46Z PLAN UPDATE entry — "STEP 1 — scripts/01_ingest.py".
Confirmed nothing from Step 1 was started: no `data/exonotes.duckdb`, no `scripts/01_ingest.py`.
No work to redo, no paid calls to avoid.
---

## [2026-09-19T22:56Z] STEP 1.0 ENV — STARTED
**Doing:** Establish the Python environment for Steps 1–2. PLAN.md §4 warns CatBoost may lack
Python 3.14 wheels; if so, fall back to a `uv` venv on 3.12 rather than fighting it.
**Command:** version/availability probes only, no installs yet.
**Idempotent:** yes — read-only probe.
---

## [2026-09-19T22:59Z] STEP 1.0 ENV — DONE
**Result:** `uv venv --python 3.14 .venv` + install of catboost, duckdb, pandas, pyarrow,
scikit-learn, scipy, matplotlib, etta, requests, python-dotenv. All import cleanly.
Versions: python **3.14.7** · catboost **1.2.10** · duckdb **1.5.5** · pandas **3.0.6** ·
sklearn **1.9.1** · etta **0.1.1**.
**DEVIATION FROM PLAN (§4):** the plan predicted CatBoost would lack Python 3.14 wheels and
instructed a fallback to a 3.12 `uv` venv. **That prediction was wrong** — catboost 1.2.10
installed and imported on 3.14.7 with no build step. **No 3.12 fallback was needed; this project
runs on 3.14.** Recording so the next session does not re-litigate the interpreter choice.
**Note:** pandas resolved to **3.0.6** (major version, not 2.x). Copy-on-write and the string
dtype are defaults there; code written for pandas 2 idioms may warn. Watch for it.
**Side finding (relevant to §2 timestamps):** `etta` exposes more than `download_toi` —
notably **`download_obsnotes`**, plus `download_tag_imaging` / `download_tag_spect` /
`download_tag_tseries`, `download_user_tags`, `download_imaging`, `download_spect`,
`download_tseries`, `download_nearbytarget`, `download_stellarcomp`. `download_obsnotes` is a
candidate second free-text corpus and a candidate source of dated records. Will investigate in
STEP 1.5 rather than assuming.
**Jev spend this step:** $0.00 · **running total:** ~$0.0002
**Next:** STEP 1.1 — pull the ExoFOP TOI table, checksum it, inspect the schema.
---

## [2026-09-19T23:00Z] STEP 1.1 EXOFOP PULL — STARTED
**Doing:** `etta.download_toi()` → raw ExoFOP-TESS TOI table. Save raw bytes to
`data/raw/exofop_toi_<date>.csv`, record SHA256 + retrieval timestamp, inspect schema
(PLAN.md §3.1 claims 57 columns incl. a free-text `Comments` column — to be verified).
**Command:** `.venv/bin/python scripts/_probe_exofop.py` (scratch probe, not a pipeline script)
**Idempotent:** yes — re-download overwrites the same dated path; checksum recorded either way.
**Network:** yes. **Jev calls:** none.
---

## [2026-09-19T23:05Z] STEP 1.1 EXOFOP PULL — DONE
**Result:** `etta.download_toi()` worked with no authentication. 22.6 s, 3,806,771 bytes.
**Artifact:** `data/raw/exofop_toi_2026-09-19.csv`
**sha256:** `0e6734b6a38afbb32051a4a6609faf94efc1e3353a603aa05005a5cb1e38b4be`
**retrieved_utc:** `2026-09-19T22:57:10.807680+00:00`
**Shape: 8,148 rows x 63 columns.** *(DEVIATION: PLAN.md §3.1 says "57 columns" and "~7,000+
rows". Actual is 63 columns / 8,148 rows. Harmless, but the plan's column count was stale.)*
**`Comments` column confirmed present** (index 62).
**Also present and NOT anticipated by the plan:** `Date TOI Alerted (UTC)`, `Date TOI Updated
(UTC)`, `Date Modified` — see STEP 1.5 for what these actually timestamp.
**Jev spend this step:** $0.00 · **running total:** ~$0.0002
**Next:** STEP 1.2 — corpus census.
---

## [2026-09-19T23:06Z] STEP 1.2 CORPUS CENSUS — DONE
**Idempotent:** yes (read-only over the saved CSV).
**Comments are present, but SHORT:**
- non-empty `Comments`: **7,801 / 8,148 (95.7%)** — the plan's worry that "most comments are
  empty" is **not** borne out. Emptiness is not the problem.
- length: **median 30 chars**, mean 41.4, p10 11, p90 81, max 352. These are terse fragments,
  not prose. The hand-written smoke-test cases in `research/04` (100–200 chars, multi-clause)
  are **longer and richer than the median real comment.** Question behaviour verified on those
  cases has NOT been verified on a 30-character fragment.
**Label mapping (PLAN.md §3.3) applied to `TFOPWG Disposition`:**
- positives CP 813 + KP 607 = **1,420**
- negatives FP 1,311 + FA 99 = **1,410**
- **labelled total 2,830 · class balance 50.2% positive — essentially balanced**
- excluded PC 4,819 + APC 485 + blank 14 = 5,318
- labelled **and** non-empty comment: **2,725** · unique TIC ID among them: **2,577**
**DEVIATION — corpus is 2.6x smaller than the plan assumed.** PLAN.md sizes the study at
"~7,000 rows" throughout (§3.1, §6 Step 3 cost model). The labelled, commented corpus is
**2,725 rows**. Consequences: (a) Jev cost falls to ~**$0.07** for the full 13-question set,
not $0.185; (b) statistical power is materially lower — a ΔAUC bootstrap CI on 2,725 rows
grouped into 2,577 host stars is wider than the plan assumed when it set gate G2.
**Good news:** the balance is 50/50, so AUC is well-behaved and no class rebalancing is needed.
---

## [2026-09-19T23:08Z] STEP 1.2b LEAKAGE AUDIT — DONE (**MAJOR FINDING**)
**Doing:** Unplanned check. The comment samples looked structurally suspicious on sight, so I
measured the §2 label-echo threat directly instead of deferring it to Step 4.
**Idempotent:** yes (read-only).
**The §2 primary validity threat is not hypothetical — it is the dominant structure of the corpus.**
Measured over the 2,725 labelled rows with comments:

| Marker in comment text | n | P(y=1 \| marker) |
| :--- | ---: | ---: |
| bare planet designation (e.g. `WASP-68 b`, `Kepler-718 b`) | 679 | **0.999** |
| contains `retir*` (e.g. "retired as NEB") | 488 | **0.006** |
| contains `TFOP FP` | 502 | **0.000** |
| contains `validat*` / `confirmed planet` / `published` | 21 | 0.905 |
| **any of the above** | **1,304 (47.9%)** | — |

**Read that carefully: 47.9% of the labelled corpus carries a marker that is very nearly
deterministic of the label.** Positives are frequently *nothing but a planet designation* — a
comment that reads `WASP-68 b` in full. A planet only has a name because it was confirmed, so
that string IS the label. Negatives carry `retired as NEB` / `TFOP FP` — the disposition itself,
written into the prose after the fact.
**Consequences, in order of importance:**
1. **`references_other_object` is currently in `TIER_PREDICTIVE` (PLAN.md §5) and it must not
   be.** It is defined as "does the note cross-reference another TOI, a known planet, or a
   duplicate designation?" — which is precisely the 679-row / P=0.999 planet-name pattern. As
   written, the plan puts the single strongest leakage channel inside the tier reserved for the
   headline result. **This would have produced a spectacular and entirely false positive result.**
   Flagging for the question-design gate (Step 2.5) — NOT fixing it now, question design is the
   next session's gate and PLAN.md §5 is a pre-registered artifact.
2. Baseline C (TF-IDF) will score very high. That is **expected and is not evidence for the
   hypothesis** — it is this leakage being read off n-grams. Interpret C accordingly.
3. The honest corpus is the **1,421 rows carrying no strong leakage marker**, where
   P(y=1) = 0.481 — still balanced, but the usable N for a clean predictive claim is ~1,400,
   not 7,000. This is the number the power of the whole study rests on.
**Recommendation for the next session (do not act on it here):** a leakage-stripped analysis —
regex-remove designation-only and `retired`/`TFOP FP` text, then re-run — deserves to be a
pre-registered arm in `PREREGISTRATION.md`, not a post-hoc robustness check.
**Jev spend this step:** $0.00 · **running total:** ~$0.0002
**Next:** STEP 1.3 — NASA Exoplanet Archive TAP queries.
---

## [2026-09-19T23:09Z] STEP 1.3 TAP — STARTED
**Doing:** NASA Exoplanet Archive TAP sync queries: `toi` (TFOPWG dispositions, cross-check
against ExoFOP) and `pscomppars` (numeric covariates). Discover schema first, do not assume it.
**Endpoint:** `https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=<ADQL>&format=csv`
**Idempotent:** yes — pure GET, results written to dated files under `data/raw/`.
**Network:** yes. **Jev calls:** none.
---

## [2026-09-19T23:13Z] STEP 1.3 TAP — DONE (**PLAN DEFECT FOUND — pscomppars must not be used**)
**Result:** Both TAP queries succeeded, no auth, plain GET.
**Artifacts:**
- `data/raw/nea_toi_2026-09-19.csv` — 8,148 rows ·
  sha256 `8e90ae4b0795eef5b4c0ea3c4ac3d890dd3ed56d78ae4dfeb5cdc61da727c4d1`
- `data/raw/nea_pscomppars_2026-09-19.csv` — 6,366 rows, 4,482 unique TIC ·
  sha256 `139485ed433fbfb2ae01d21ca9d27e311e3981f6bd72bb376f9119fbb97d7329`
- `toi` schema is 90 columns; `pscomppars` is 399.
**Source agreement:** NEA `toi` returns **8,148** rows — exactly matching today's ExoFOP pull.
Labelled counts differ trivially (NEA 2,826 vs ExoFOP 2,830), i.e. 4 rows of sync drift, which
is the weekly-drift effect PLAN.md §3.2 anticipated. Snapshots taken same day as instructed.

### The defect
**PLAN.md §3.2 instructs using `pscomppars` for "numeric covariates". Doing that would have
destroyed the study.** `pscomppars` is the composite-parameters table for **confirmed/published
planets only**. Membership in it is therefore almost the label:

| | y=0 (FP/FA) | y=1 (CP/KP) |
| :--- | ---: | ---: |
| **in pscomppars** | 6 | 1,307 |
| **not in pscomppars** | 1,404 | 113 |

**P(y=1 \| in pscomppars) = 0.995 · P(y=1 \| not in) = 0.074.**
Any feature set derived from `pscomppars` leaks the label through **missingness alone** — a
model would score near-perfect AUC by learning "this row has a radius value" and would contain
zero astrophysics. Worse, it would make **gate G2 unpassable**: baseline B would sit at ~0.99
AUC and no text feature could ever beat it, so the project would report a false negative and
stop. Either way the answer would be an artifact.
**DEVIATION — resolved as follows:** `pscomppars` is **dropped from the feature path entirely.**
Numeric covariates come from the **`toi` table itself**, which carries them for every row
regardless of disposition. Note this is not really a conflict inside the plan: PLAN.md §6 Step 2
already names exactly the right columns ("period, depth, duration, planet radius, Tmag, stellar
Teff/radius/logg") — all of which live in `toi`. It is **§3.2's choice of source table** that is
wrong, not §6's choice of columns. The raw `pscomppars` file is kept on disk for provenance and
is **not** joined into any model input.
**Residual, much milder issue — recorded, not fixed:** within `toi`, non-null coverage is itself
mildly class-dependent (`st_logg` 0.829 for y=0 vs 0.991 for y=1; `pl_rade` 0.906 vs 0.993).
CatBoost consumes NaN natively, so this is a weak leakage channel, not a fatal one — but a
missingness-indicator ablation belongs in `PREREGISTRATION.md`. Flagging, not acting.
**Jev spend this step:** $0.00 · **running total:** ~$0.0002
**Next:** STEP 1.5 — comment-timestamp investigation (PLAN.md §2.1).
---

## [2026-09-19T23:14Z] STEP 1.5 COMMENT-TIMESTAMP INVESTIGATION — STARTED
**Doing:** PLAN.md §2.1 — determine whether ExoFOP exposes a timestamp or edit history for the
`Comments` FIELD specifically (as opposed to the row). This decides whether the primary validity
threat can be controlled by restricting to comments predating disposition, or only mitigated by
the question-tier scheme. A negative finding is to be recorded as explicitly as a positive one.
**Probes:** (a) date columns in ExoFOP TOI table; (b) `toi_created`/`rowupdate`/`release_date`
in NEA `toi`; (c) `etta.download_obsnotes` on sample TICs; (d) etta's PHP endpoint surface.
**Idempotent:** yes — read-only probes.
---

## [2026-09-19T23:20Z] STEP 1.5 COMMENT-TIMESTAMP INVESTIGATION — DONE (**answer: partially YES**)
**Idempotent:** yes. **Network:** 32 GETs. **Jev spend:** $0.00 · **running total:** ~$0.0002

### Finding 1 — the `Comments` field itself has NO timestamp. (negative finding, recorded as required)
The three ExoFOP date columns are **row-level, not field-level**:
`Date TOI Alerted (UTC)` (TOI announcement), `Date TOI Updated (UTC)`, `Date Modified`
(504 unique values, 5,709 rows sharing a single bulk value of `2025-07-31 12:59:22`).
NEA `toi` adds `toi_created`, `rowupdate`, `release_date` — also row-level.
**Nothing in `etta`'s PHP surface exposes an edit history for the `Comments` field**; the eleven
wrapped endpoints are `download_toi`, `download_nearbytarget`, `download_imaging`,
`download_tag_imaging`, `download_spect`, `download_tag_spect`, `download_tseries`,
`download_tag_tseries`, `download_obsnotes`, `download_user_tags`, `download_stellarcomp`.
None is a revision log. **There is also no disposition-assignment timestamp anywhere** — so even
in principle the TOI `Comments` text cannot be aligned to "as it stood when the label was set."

### Finding 2 — `download_obsnotes` IS a timestamped, authored corpus (**the plan did not know about this**)
Schema: `ID · TIC ID · Username · Groupname · TAG ID · Lastmod · notes`.
Measured on 30 labelled TICs (15 per class):
- **30 / 30 had at least one note** — coverage looks essentially complete.
- median **3** notes per TIC (mean 4.2, max 26); median **2,384 characters** of text per TIC
  versus **30 characters** in the TOI `Comments` field — roughly **80x more text**.
- `Lastmod` spans **2009-08-08 → 2026-08-25** and is genuinely spread across years (latest-note
  year: 2020:9, 2021:5, 2022:4, 2023:3, 2024:2, 2025:4, 2026:3). This is real temporal
  information, not a single bulk stamp.
- Notes are per-author (`Username`) and per-group (`Groupname`, e.g. `tfopwg`), so observer
  notes can be separated from the TFOP working-group summary that carries the disposition.

### Finding 3 — three caveats that limit what Finding 2 buys
1. **`Lastmod` is last-modified, not created.** A note written in 2019 and edited in 2026 reads
   as 2026, and the 2019 text is unrecoverable. A visible **bulk-migration cluster at
   `2020-09-18 12:0x:xx`** (many TICs, same minute) is a clear instance — for those notes
   `Lastmod` is an import artifact, not an authoring date.
2. **Note count is itself label-correlated** — median 5 notes for CP/KP vs 2 for FP/FA. Any
   feature derived from note volume is a leakage channel and must be handled, not ingested.
3. **21 / 30 TICs carry HTML markup** inside `notes` (`<!DOCTYPE html>`, inline `<span
   style=...>`). Requires stripping before any text use.

### What this means for the study design (the user asked for this specifically)
**The primary validity threat of PLAN.md §2 can be partially controlled, which is better than
the plan assumed — but via a different corpus than the plan is built on.** Concretely:
- For the **TOI `Comments` corpus the MVP currently uses: no temporal control is possible.**
  The `TIER_PREDICTIVE` / `TIER_LABEL_ECHO` split remains the *only* available mitigation, which
  raises the stakes on getting that split right — see the 23:08Z entry, where
  `references_other_object` is shown to be mis-tiered.
- For the **obsnotes corpus: a conservative temporal filter is possible** ("keep only notes with
  `Lastmod` before cutoff T"), which is a genuine, if imperfect, control — imperfect because of
  caveat 1.
**Recommendation to the next session (NOT acted on here — out of scope):** obsnotes look like a
materially better corpus for this study than the TOI `Comments` field: ~80x more text, per-note
timestamps, and author attribution. Cost to acquire is the blocker — **3.24 s/TIC measured, so
~2.3 hours sequential for 2,577 TICs** (one HTTP GET each, parallelizable, no API cost). This is
a corpus-selection decision that belongs with the §7 pre-registration, not with me.
**Next:** STEP 1.6 — write `scripts/01_ingest.py` and materialize DuckDB.
---

## [2026-09-19T23:21Z] STEP 1.6 WRITE 01_ingest.py — STARTED
**Doing:** Materialize the pipeline script and build `data/exonotes.duckdb`.
**Command:** `.venv/bin/python scripts/01_ingest.py`
**Idempotent:** **yes** — reuses the dated raw files under `data/raw/` if present and re-verifies
their SHA256; only re-downloads when passed `--refresh` or when a file is missing. DuckDB tables
are dropped and recreated each run (`CREATE OR REPLACE`), so a partial run leaves no debris.
**Deviation carried in:** numeric covariates come from NEA `toi`, NOT `pscomppars` (see 23:13Z).
---

## [2026-09-19T23:26Z] STEP 1.6 WRITE 01_ingest.py — DONE — **STEP 1 COMPLETE**
**Artifacts:** `scripts/01_ingest.py`, `data/exonotes.duckdb`
**Tables:** `toi_snapshot` (8,148 rows, all TOIs incl. unresolved), `analysis_set` (the modelling
set), `ingest_provenance` (per-source sha256 + bytes + snapshot date + `used_as_features` flag),
`ingest_stats` (every count below, so the next session need not recompute them).
**Idempotency VERIFIED:** re-ran the script; identical SHA256s, zero network I/O on the second
run (raw files cached by snapshot date and re-verified), tables rebuilt via `CREATE OR REPLACE`.

| quantity | value |
| :--- | ---: |
| ExoFOP rows / NEA `toi` rows / joined | 8,148 / 8,148 / **8,148** (clean 1:1 on TOI id) |
| labelled (CP/KP/FP/FA) | **2,826** |
| — positive (CP+KP) | 1,425 |
| — negative (FP+FA) | 1,401 |
| excluded (PC/APC/blank) | 5,322 |
| **dropped: empty/whitespace comment** | **105** (3.7% of labelled) |
| **analysis set (labelled + non-empty comment)** | **2,721** |
| unique TIC ID in analysis set (grouping key) | **2,573** |
| median comment length | **30 chars** |

**On the plan's worry about empty comments:** only **105** labelled rows were dropped for an
empty comment — **3.7%**. Emptiness is NOT the limiting factor the plan feared. The corpus is
limited by something else entirely: **labels** (only 2,826 of 8,148 TOIs are resolved) and
**comment brevity** (median 30 characters).
**Label source:** NEA `toi.tfopwg_disp`, per PLAN.md §6 Step 1.2. **6 labelled rows disagree with
the ExoFOP disposition** and are flagged in `toi_snapshot.label_source_agrees` — four are sign
flips (ExoFOP `FP` -> NEA `CP`: TOIs 4462.01, 4759.01, 5240.01, 5467.01). Kept, not dropped;
a 6-row sensitivity check is a cheap robustness item for the next session.
**Jev spend this step:** $0.00 · **running total:** ~$0.0002
**Next:** STEP 2 — `scripts/02_baselines.py`, baselines A/B/C under GroupKFold on TIC ID.
---

## [2026-09-19T23:27Z] STEP 2 BASELINES — STARTED
**Doing:** Baselines A (prior), B (numeric-only CatBoost), C (TF-IDF + logistic regression),
all under the §7 S1 regime: `GroupKFold` on **TIC ID**, 5 folds x 3 repeats. Metrics: AUC + Brier.
**Command:** `.venv/bin/python scripts/02_baselines.py`
**Idempotent:** **yes** — reads `analysis_set` from DuckDB, fixed seeds (repeat r uses seed
`RANDOM_STATE + r`), writes results via `CREATE OR REPLACE TABLE baseline_results`. No network,
no Jev calls.
**Note:** sklearn has no repeated GroupKFold, so repeats are done by shuffling the group->fold
assignment under a per-repeat seed. Recording this because it is an implementation choice the
plan does not specify.
**Prediction on record (before running):** baseline C will score high because of the 47.9%
leakage measured at 23:08Z, and that will NOT be evidence for the hypothesis.
---

## [2026-09-19T23:33Z] STEP 2 BASELINES — DONE — **GATE G1 PASSES**
**Artifacts:** `scripts/02_baselines.py`; DuckDB tables `baseline_results` (per-fold, 45 rows)
and `baseline_summary`.
**Idempotent:** yes — fixed seeds, no network, `CREATE OR REPLACE`. Deterministic on re-run.
**Setup:** 2,721 rows · 2,573 TIC groups · base rate 0.5031 · GroupKFold(5) x 3 repeats = 15 folds.

| model | AUC (mean ± sd) | Brier (mean ± sd) |
| :--- | ---: | ---: |
| **C — TF-IDF** | **0.9691 ± 0.0064** | **0.0703 ± 0.0052** |
| **B — numeric CatBoost** | **0.9154 ± 0.0130** | **0.1136 ± 0.0079** |
| **A — prior** | **0.5000 ± 0.0000** | **0.2501 ± 0.0002** |

### GATE G1 — **PASS.** B beats A on both metrics (AUC 0.9154 vs 0.5000; Brier 0.1136 vs 0.2501).
The pipeline is not broken. A sits at exactly 0.5000 AUC / 0.2501 Brier, which is the correct
degenerate answer for a constant predictor on a 50/50 corpus and is itself a sanity check.

### Diagnostics (unplanned; run because the headline numbers needed interpreting)
**Baseline C is reading planet names — leakage, exactly as predicted at 23:08Z.**
Its strongest positive-pushing terms are survey catalogue prefixes:
`toi, wasp, k2, kepler, hat, hats, hd, multi, kelt, ngts, gj, qatar, corot, lhs`.
Strongest negative-pushing terms: `tfop, fp, eb, neb, retired, retired as, tfop fp, secondary,
centroid, offset`. **A planet has a name only because it was confirmed**, so "wasp" IS the label.
**C's 0.9691 must not be read as evidence that comment text carries predictive information.**
**Baseline B is sound.** CatBoost importances are spread over genuine physical quantities
(`pl_rade` 16.2, `pl_orbper` 16.1, `st_logg` 15.5, `pl_trandurh` 12.4, `pl_trandep` 12.1,
`st_teff` 10.3, `st_tmag` 10.0, `st_rad` 7.4) rather than concentrated in one column. The
missingness-leak flagged at 23:13Z was quantified: **a model on missingness indicators ALONE
scores AUC 0.5869** — non-trivial, so it should be ablated in Step 4, but far from B's 0.9154.
B is mostly real astrophysics (an EB implies an absurd planet radius), not an artifact.
**Leakage-stripped preview** (regex-removed designation-only and `retired`/`TFOP FP` rows →
1,417 rows, 1,312 TIC, base rate 0.485), GroupKFold(5):
- B numeric: **AUC 0.9037** / Brier 0.1254 — barely moves. The numeric baseline is robust.
- C TF-IDF: **AUC 0.8965** / Brier 0.1285 — falls 0.073 but stays high, so either residual
  leakage survives my crude regex (`likely EB`, `centroid offset`, `secondary` are
  observational *and* near-deterministic of FP) or there is genuine lexical signal. **This
  measurement cannot distinguish those two, and neither can any test in Step 2.**
**The headroom problem, stated plainly:** baseline B is at **0.9154** (0.9037 leakage-stripped).
For gate G2, Jev features must beat that with a bootstrap CI excluding zero, on **2,573 host
star groups** — or ~1,312 once leakage markers are stripped. The plan set G2 assuming ~7,000
rows and did not anticipate a numeric baseline this strong. **G2 is a harder target than the
plan assumed, on less data than the plan assumed.** Not a reason to stop; a reason to size the
expectation honestly before spending.
**Jev spend this step:** $0.00 · **running total:** ~$0.0002 (unchanged — no API calls made)
**Next:** STOP per session scope. Next session: PLAN.md Step 2.5 (question-design gate) and
`PREREGISTRATION.md`. See the SESSION END entry for the carry-forward list.
---

## [2026-09-19T23:35Z] SESSION END — Claude Opus 5
**Completed:** PLAN.md §6 **Step 1 (ingest)** and **Step 2 (baselines)**. Stopped at the assigned
boundary. Step 2.5 and Step 3 NOT started, as instructed.
**Artifacts created:** `.venv/` (py3.14), `scripts/01_ingest.py`, `scripts/02_baselines.py`,
`data/raw/{exofop_toi,nea_toi,nea_pscomppars}_2026-09-19.csv`, `data/exonotes.duckdb`
(tables: `toi_snapshot`, `analysis_set`, `ingest_provenance`, `ingest_stats`,
`baseline_results`, `baseline_summary`).
**Headline numbers:** analysis set **2,721 rows / 2,573 TIC / 50.3% positive / median comment
30 chars / 105 empty comments dropped**. **G1 PASS** — A 0.5000, B **0.9154**, C 0.9691 AUC.
**Jev spend this session: $0.00** (Steps 1–2 make no API calls, as scoped) ·
**project running total: ~$0.0002**

### Carry-forward for the next session — five plan defects found, in priority order
1. **`references_other_object` is mis-tiered.** It sits in `TIER_PREDICTIVE` (PLAN.md §5) but
   captures the planet-name pattern that predicts the label at **P=0.999** over 679 rows. Left
   in place deliberately — §5 is pre-registration material and re-tiering it is a Step 2.5
   decision, not a unilateral one. **Fix before any Jev spend.**
2. **`pscomppars` must stay out of the feature path** (PLAN.md §3.2 is wrong). Already handled
   in `01_ingest.py`; do not reintroduce it. See 23:13Z.
3. **Corpus is 2,721 rows, not ~7,000.** Update the §6 Step 3 cost model (~$0.07, not $0.185)
   and re-examine whether gate G2's bootstrap CI is achievable at this N.
4. **Comment timestamps: none for the `Comments` field; `download_obsnotes` has them.**
   Decide whether to switch corpus — ~80x more text, per-note `Lastmod`, author attribution,
   ~2.3 h to pull. See 23:20Z for the three caveats. This belongs in `PREREGISTRATION.md`.
5. **Questions were verified on 100–200-char hand-written cases; the median real comment is 30
   chars.** Step 2.5's ~20-case set must be drawn from REAL comments in `analysis_set`, not
   hand-written ones, or the gate tests the wrong distribution.

**Resume at:** PLAN.md §6 **Step 2.5** (question-design gate) then §7 `PREREGISTRATION.md`.
Read this entry plus 23:08Z, 23:13Z and 23:20Z before designing questions.
---

## [2026-09-19T23:40Z] SESSION REOPENED — Claude Opus 5
**Reason:** User request after the 23:35Z SESSION END. Two tasks:
(a) fix the five plan defects found this session, in `PLAN.md` and `HANDOFF_PROMPT.md`;
(b) prepare the project for **public release on GitHub**, and factor that into the handoff.
**Scope guard unchanged:** still NO Jev API calls. Steps 2.5 and 3 remain the next session's work.
---

## [2026-09-19T23:40Z] STEP 6.1 SECRET AUDIT — STARTED
**Doing:** Before anything git-related, verify the TypeSafe API key does not appear in any file
that would be committed. The repo is not yet under version control, so there is no history to
scrub — this is the one moment when a clean start is free.
**Idempotent:** yes — read-only audit.
**Method:** read the key value into a shell variable and grep for it WITHOUT echoing it; print
only file names and match counts. The key is never written to stdout, to a file, or to this log.
---

## [2026-09-19T23:42Z] STEP 6.1 SECRET AUDIT — DONE
**Result:** **Clean.** The `TYPESAFE_API_KEY` value (108 chars) appears in **no file other than
`.env`**. `.env.example` contains the bare variable name with no value. No key-like strings in
`research/` or `scripts/`. Existing `.gitignore` already excludes `.env`, `.env.*`, `data/`,
`.venv/`, `__pycache__/`, `*.pyc`, `.DS_Store`.
**Method note:** key read into a shell variable and used only as a `grep -F` pattern; never
echoed, never written. Only filenames were printed.
**Why this matters now:** the project is **not yet a git repository**, so there is no history to
scrub. The initial commit can start clean — this is the one moment when that is free.
**Next:** PLAN.md defect fixes.
---

## [2026-09-19T23:42Z] STEP 6.2 PLAN.md REVISION — DONE
**Doing:** Fix the defects found this session and add a public-release section.
**Idempotent:** n/a (document edit). Applied via an assertion-checked patch script — every
anchor asserted to match exactly once, so a stale anchor fails loudly instead of silently
corrupting the file. All 24 replacements verified.
**Changes:**
- **§0 / §3.1 / §3.3** — corpus facts replaced with measured values (2,721 analysis rows,
  2,573 TIC, 63 columns, 8,148 TOIs, 50.3% positive, median 30-char comment, 105 empty dropped).
- **§2.0 NEW** — the leakage table (47.9% of labelled rows carry a near-deterministic marker),
  with the TF-IDF term evidence. The validity threat is now documented as measured, not feared.
- **§2.1 NEW** — comment-timestamp negative finding recorded in full.
- **§2.2 NEW** — `download_obsnotes` documented as a timestamped alternative corpus, with its
  three caveats and its 2.3 h acquisition cost, flagged as a human pre-registration decision.
- **§3.2** — **`pscomppars` now carries a ⛔ box** with the 0.995/0.074 table and an explicit
  statement that the earlier instruction was wrong.
- **§4** — environment resolved: Python 3.14 confirmed, CatBoost 3.14 wheels exist, versions
  pinned. Repo layout gains LICENSE / CITATION.cff / CONTRIBUTING.md / PROVENANCE.md /
  requirements.txt.
- **§5** — **`references_other_object` MOVED from `TIER_PREDICTIVE` to `TIER_LABEL_ECHO`**, with
  the P=0.999 justification inline. Added a box warning that the question set was verified on
  100–200-char hand-written text while the median real comment is 30 chars.
- **§6** — Steps 1 and 2 marked ✅ DONE with their measured results inline; Step 2.5 now requires
  cases drawn from REAL comments (with the SQL to sample them); Step 3 cost revised $0.185 →
  **~$0.072** (7 questions) / ~$0.15 (13); runtime 2 h → ~45 min.
- **§7** — **S2 temporal split rewritten.** As originally specified it was *not implementable*:
  it keyed on a disposition timestamp that does not exist. Now uses `date_toi_alerted` as an
  explicitly weaker proxy, with three measured cutoff options and a warning about the base-rate
  shift (0.50 overall → ~0.63 in the recent slice). G1 marked passed; G2 annotated with the
  headroom problem; **G5 (leakage-stripped arm) and G6 (missingness ablation) added** as new
  gates with a matching decision rule.
- **§9** — definition of done extended with G5/G6 and the release checklist.
- **§11 NEW — Public release on GitHub.** Secrets policy, what is/is not published, honesty
  requirements, licensing (MIT code / CC BY 4.0 text), the ExoFOP + NASA Exoplanet Archive
  acknowledgements both archives require, a pre-publication checklist, and a recommendation on
  timing.
- Tail renumbered; the orphaned §12 merged back into §10.
**SIXTH DEFECT FOUND during this pass** (beyond the five in the 23:35Z list): **§7's S2 temporal
split was unimplementable as written** — it required a disposition timestamp that §2.1 proves
does not exist. Fixed in place.
**Jev spend:** $0.00 · **running total:** ~$0.0002
**Next:** publication scaffolding (LICENSE, requirements.txt, PROVENANCE.md, README, git init).
---

## [2026-09-19T23:44Z] STEP 6.3 PUBLICATION SCAFFOLDING — STARTED
**Doing:** LICENSE (MIT), requirements.txt (pinned from the live venv), CITATION.cff,
CONTRIBUTING.md, PROVENANCE.md, hardened .gitignore, rewritten README.md, `git init` + initial
commit. **NOT pushing to GitHub** — creating a public remote is the user's call and needs their
account; I stop at a local commit.
**Idempotent:** mostly — file writes overwrite; `git init` is safe to re-run. The commit is not
(re-running creates a second commit); check `git log` before repeating.
---

## [2026-09-19T23:50Z] STEP 6.3 PUBLICATION SCAFFOLDING — DONE
**Artifacts:** `LICENSE` (MIT), `requirements.txt` (pinned from the live venv), `CITATION.cff`,
`CONTRIBUTING.md`, `PROVENANCE.md` (now emitted by `01_ingest.py`, so it cannot drift),
hardened `.gitignore`, rewritten `README.md`, rewritten `HANDOFF_PROMPT.md`.
**`.gitignore` bug caught and fixed:** the pattern `data/` matched **`research/data/`** as well
as the root `data/`, silently excluding `smoke_2026-09-19.json` and
`smoke_revised_2026-09-19.json` — our own measurement artifacts, which `research/04` links to.
Changed to `/data/` (root-anchored). Both files are now tracked. **A public repo would have
shipped with dead links to its only first-party measurements.**
**`01_ingest.py` extended** to write `PROVENANCE.md` on every run. Re-ran: still idempotent,
identical checksums.
**Git:** `git init` + staged. **Safety verified before committing:** `.env` not tracked;
`data/` tracked files = 0; `.venv` tracked files = 0; the key string appears in no tracked file.
**Jev spend:** $0.00 · **running total:** ~$0.0002

### ⚠️ OPEN ITEM FOR THE USER — local path in this log, append-only rule respected
`git grep` found `/Users/<user>/...` in **`WORKLOG.md` lines 31 and 39** (the 16:26Z PROJECT
RENAME entry). Publishing would expose the macOS short username `<user>`.
**I did not edit those lines.** PLAN.md §0.5 non-negotiable #2 is "append only — never edit or
delete a past entry", and silently rewriting history to tidy a public repo is exactly the kind
of edit that rule exists to prevent. This is the user's call. Options:
- **(a) Leave it.** The GitHub account name will be public anyway; "<user>" reveals nothing more.
- **(b) Redact before the first push**, and record the redaction in a NEW worklog entry so the
  change is itself logged. Only clean while there is no published history.
No other tracked file contains a local path.
**Next:** initial commit (local only — NOT pushing; creating a public remote is the user's call).
---

## [2026-09-19T23:56Z] STEP 6.4 PRE-PUBLICATION CHECKLIST — PARTIAL
**Idempotent:** yes (checks are read-only; the banner edit below is a one-time content fix).
**PLAN.md §11.6 results on the committed tree:**

| # | check | result |
| ---: | :--- | :--- |
| 1 | key absent from git history | **PASS** |
| 2 | `.env` not tracked | **PASS** |
| 3 | `data/` not tracked (0 files) | **PASS** |
| 4 | LICENSE / CITATION.cff / CONTRIBUTING.md / PROVENANCE.md / requirements.txt present | **PASS** |
| 5 | README states the headline question is still open | **PASS** |
| 6 | README carries ExoFOP + NASA Exoplanet Archive acknowledgements | **PASS** |
| 7 | `research/01–02` marked superseded | **FIXED — see below** |
| 8 | no local paths outside `WORKLOG.md` | **PASS** |
| 9 | `CITATION.cff` repository URL | **PENDING** — `REPLACE_ME` until a remote exists |
| 10 | clean-clone reproduction | **NOT VERIFIED — see 6.5** |

**Item 7 was a real defect, not a grep artifact.** `research/01_*` and `research/02_*` had **no
supersession banner in the files themselves** and opened by describing themselves as
"Authoritative analysis" and "A Rigorous Technical Assessment". The warnings existed only in
`research/README.md` and in document `03`. On a public repo, anyone arriving at those files
directly — a search engine, a deep link, GitHub code search — would have read superseded,
partly-wrong material presented as authoritative, with no signal at all.
**Fixed:** added a prominent `⚠️ SUPERSEDED — DO NOT BUILD FROM THIS DOCUMENT` banner to the top
of both, naming the three most consequential errors and pointing to `03` §1.4. The H1 is kept
above the banner so GitHub still renders a sensible title.
---

## [2026-09-19T23:57Z] STEP 6.5 CLEAN-CLONE REPRODUCTION — **BLOCKED / IN PROGRESS**
**Doing:** `git clone` to a scratch dir, fresh `uv venv --python 3.14`, install from
`requirements.txt`, then `01_ingest.py` → verify the snapshot regenerates and G1 reproduces.
**Idempotent:** yes — scratch clone, `rm -rf`'d and recreated each attempt. Touches nothing in
the project.
**Status:** clone OK (`.env` correctly absent, `data/` correctly absent), venv + install OK.
**`01_ingest.py` then hung on the ExoFOP download for 8+ minutes with `data/raw/` still empty**
(the same call took **22.6 s** at 22:57Z). Process confirmed alive, not crashed.
**FINDING — `etta.download_toi()` takes no timeout argument.** A hung ExoFOP request is
therefore indistinguishable from a slow one, and `01_ingest.py` inherits that: it can block
forever with no output and no error. Probable cause here is ExoFOP throttling after four pulls
from this host today, but **the robustness defect is real regardless of today's cause** and it
lands on the *first* thing a new contributor runs.
**Recommended fix (NOT applied — it is a code change beyond this session's remit, and the next
session should decide):** bypass `etta.download_toi()` for the bulk table and fetch
`https://exofop.ipac.caltech.edu/tess/download_toi.php?output=csv` with
`requests.get(..., timeout=(10, 300))` plus a bounded retry, keeping `etta` for the per-TIC
endpoints. Add it to PLAN.md §6 Step 1 and the release checklist.
**Consequence for publication:** checklist item 10 is **NOT verified**. Do not claim
reproducibility until a clean clone completes end to end. Everything else is verified.
---

## [2026-09-20T00:02Z] STEP 6.5 CLEAN-CLONE REPRODUCTION — **FAILED (external cause, diagnosed)**
**Result:** Aborted after ~30 min. `data/raw/` never received a byte.
**Root cause CONFIRMED by direct probe**, not inferred:
```
curl --max-time 20 "https://exofop.ipac.caltech.edu/tess/download_toi.php?output=csv"
curl: (28) Operation timed out after 20004 ms with 0 bytes received
http=000  connect=0.419s  total=20.004s  size=0
```
**TCP connects in 0.42 s, then the server sends zero bytes.** ExoFOP is accepting the connection
and withholding the response — server-side throttling, almost certainly because this host pulled
the full TOI table four times today (22:57Z, plus three `01_ingest.py` runs). The same call
succeeded in **22.6 s** at 22:57Z.
**This is not a defect in our code, but it exposes one.** `etta.download_toi()` accepts no
timeout argument, so a withheld response hangs the process **indefinitely, silently, with no
output and no error** — and it does so on the very first command a new contributor runs. A
public repo whose quickstart can hang forever with no diagnostic is a bad first impression at
best and a bug report at worst.
**Two items handed to the next session (neither applied here — both are code/plan changes past
this session's remit):**
1. Add an explicit timeout + bounded retry with backoff to the ExoFOP fetch, and print a clear
   "ExoFOP is throttling, retry later" message on timeout. Suggested: fetch the bulk CSV via
   `requests.get(..., timeout=(10, 300))` directly and keep `etta` for per-TIC endpoints.
2. **Re-run the clean-clone test once ExoFOP has cooled off**, before publishing. Checklist
   item 10 remains **UNVERIFIED** and must not be claimed as passing.
**Note on the existing snapshot:** unaffected. `data/exonotes.duckdb` and the three raw CSVs in
the project are intact and checksum-verified; `01_ingest.py` is cached-by-date, so re-running it
in the project does no network I/O. Only a *fresh* clone needs the download.
**Jev spend:** $0.00 · **running total:** ~$0.0002
**Next:** report to user. Publication is prepared but NOT pushed — creating the public remote is
the user's call.
---

## [2026-09-20T00:03Z] SESSION END — Claude Opus 5
**Completed this block:** PLAN.md revised (six defects fixed, §11 public-release section added),
`HANDOFF_PROMPT.md` rewritten for the new state, full publication scaffolding, local git repo
with two commits, pre-publication checklist 9/10 with one item blocked externally.
**NOT done, deliberately:** no GitHub remote created, no push. Publishing is the user's call.
**Jev spend this session: $0.00** · **project running total: ~$0.0002**
**Two open items needing the user:**
1. `WORKLOG.md` lines 31/39 contain `/Users/<user>/...`. Append-only rule respected — not edited.
   Leave it, or redact before first push and log the redaction.
2. Clean-clone reproduction unverified (ExoFOP throttling). Re-test before publishing.
**Resume at:** `HANDOFF_PROMPT.md` — Step 2.5 question gate, `PREREGISTRATION.md`, publication.
---

## [2026-09-20T00:12Z] HANDOFF TASK 3 REFRESH — DONE
**Trigger:** User published the repo to https://github.com/KevinArce/ExoNotes between sessions,
which made part of `HANDOFF_PROMPT.md` stale — TASK 3 still instructed the next session NOT to
create the remote and to fill in the `CITATION.cff` URL. Both were already done by the user.
**Verified on the pushed history (all PASS):** API key absent from `git log -p --all`; `.env`
not tracked; `data/` 0 files tracked; `CITATION.cff` now carries the real repository URL.
**Changed:** TASK 3 rewritten to state the repo is already public and to carry the two items
that actually remain — (1) checklist item 10, clean-clone reproduction, still UNVERIFIED, with
the exact commands and the pass criterion (G1 reproduces at B ~0.9154 vs A 0.5000); (2) the
unfixed `etta.download_toi()` timeout bug, with the concrete fix. Also restates the WORKLOG
local-path item as the user's decision, with the instruction that any redaction be recorded in
a NEW entry rather than an amendment.
**Idempotent:** n/a (document edit, assertion-checked anchor).
**Jev spend:** $0.00 · **running total:** ~$0.0002
**Not pushed** — commit is local. The user pushes.
---

## [2026-09-20T00:00Z] SESSION START — Claude Opus 5
**Resuming from:** last entry `[2026-09-20T00:12Z] HANDOFF TASK 3 REFRESH — DONE`. No orphan
`STARTED` entry, so nothing was interrupted. Picking up `HANDOFF_PROMPT.md` TASKS 1–3.
**Clock note:** this machine's `date -u` currently reads **2026-09-20T00:00Z**, i.e. *earlier* than the
three preceding entries (00:02Z–00:12Z on 2026-09-20). The preceding session's stamps run a few
minutes ahead of this host's clock. Recorded rather than corrected — §0.5 non-negotiable #2 is
append-only, and a log whose timestamps are silently "fixed" is worth less than one that says
where its clock came from. Timestamps below are this host's real `date -u`.
**Scope this session (from HANDOFF_PROMPT.md):**
1. TASK 1 — PLAN.md §6 Step 2.5 question-design gate on cases drawn from REAL comments.
2. TASK 2 — write `PREREGISTRATION.md`, then STOP. Step 3 belongs to the next session.
3. TASK 3 — publication prep: clean-clone reproduction (checklist item 10) + the
   `etta.download_toi()` timeout robustness bug.
**Budget:** ~$0.01, Task 1 only. **Jev spend to date:** ~$0.0002.
---

## [2026-09-20T00:01Z] TASK 3 / ITEM 10 PRE-CHECK — ExoFOP STILL THROTTLING
**Doing:** probe ExoFOP before committing ~20 min to a clean-clone run, so a known-dead endpoint
does not burn the session's time budget twice.
**Idempotent:** yes (read-only `curl`, `--max-time 25`).
**Result — unchanged from 2026-09-20T00:02Z:**
```
http=000  connect=0.403s  total=25.005s  size=0
```
**TCP still connects in 0.40 s and the server still sends zero bytes.** The cool-off the handoff
hoped for has **not** happened. Checklist item 10 stays **UNVERIFIED**; the repo must still not
be described as reproduction-verified.
**Deviation from HANDOFF_PROMPT.md:** it says "Re-run it now that ExoFOP has cooled off." That
premise is false as of this timestamp. I will re-probe periodically through the session and run
the clone test the moment it answers; the timeout fix (the other half of TASK 3) does not depend
on ExoFOP being up and proceeds regardless.
**Jev spend:** $0.00 · **running total:** ~$0.0002
**Next:** TASK 1 — build the Step 2.5 case set from real comments.
---
## [2026-09-20T00:04Z] TASK 1 / STEP 2.5 QUESTION GATE — STARTED
**Doing:** build `scripts/025_question_gate.py` — ~23 cases drawn verbatim from `analysis_set`,
covering each §5 question's clear positive, clear negative and nearest confusable. Run, inspect
every answer by eye, revise, re-test.
**Idempotent:** **yes** — responses are cached content-addressed on
`sha256(model + QUESTION_SET_VERSION + state + questions)` under `data/cache/` (gitignored), so a
re-run costs $0.00 and returns byte-identical answers. Bumping `QUESTION_SET_VERSION` invalidates
the cache by design, which is what makes round 2 a real re-test rather than a replay.
**Corpus reconnaissance done first (read-only DuckDB, $0.00) — three findings that change the
question set BEFORE any spend:**

| § 5 question | corpus support | note |
| :--- | ---: | :--- |
| `reports_on_target_detection` | **11 rows (0.40%)**, ~2 genuine | most matches are *requests* ("SG1 check if it is on target") or non-recoveries |
| `indicates_followup_complete` | **2 rows (0.07%)**, **0 genuine** | neither states follow-up is finished |
| `reports_stellar_companion_or_blend` | 27 (1.0%) | sparse but real |
| `mentions_spectroscopic_binary` | 38 (1.4%) | sparse but real, clean `SB1`/`SB2` tokens |
| `mentions_instrumental_artifact` | 32 (1.2%) | sparse but real |

Both dead questions were re-checked with a deliberately **over-broad** regex (`on.?target|cleared|
recovered|lco|muscat|sg1|sg2|trappist|…` and `no further|complete|closed|finished|done|final|…`)
to make sure this was not a regex artifact. It is not.
**Length distribution confirmed** (p10=9, p25=11, **p50=30**, p75=54, p90=89, p99=163, max=336) —
and the 1–15-char bucket is **891 rows at 89% positive**, which is the bare-designation leakage
channel of §2.0 showing up as a length effect.
**Jev spend:** $0.00 · **running total:** ~$0.0002
---
## [2026-09-20T00:08Z] TASK 1 / GATE ROUND 1 — DONE (13 FAILURES, as predicted)
**Artifacts:** `scripts/025_question_gate.py` (v `2026-09-20.r2`),
`research/data/gate_2026-09-20.r2_2026-09-19.json` (all 23 raw responses).
**Result: 90/103 assertions passed · 13 FAILED · 23 calls · 38,013 input tokens · $0.00160.**

### The headline failure — §5's warning box was right, and worse than it said
`reports_offset_eclipsing_binary` **failed on 5 of 23 cases**, and it is the question
`research/04` §4.1 certified as *verified* at 0.870 / 0.070 / 0.070.

| case | real comment | want | got |
| :--- | :--- | :--- | ---: |
| C18 | `…; retired as TFOP FP/NEB` | Y | **0.26** |
| C10 | `TFOP FP; retired as NEB` (46 rows) | Y | **0.54** |
| C16 | `close companion star 219379014; TFOP FP; retired as NEB` | Y | **0.57** |
| C17 | `Crowded field; secondary; synchronized; TFOP FP; retired as EB` | N | **0.53** |
| C11 | `TFOP FP/SB1` | N | **0.35** |

**Diagnosis:** 04 verified this question on `"NEB detected at 1.2 arcmin NE"` — prose that
*spells the offset out*. Real comments never do; they write the bare acronym `NEB`. The
instruction listed `NEB` as a cue but led with "at a position offset from the target star", so on
text that states a **classification** and no offset, the model hedges at ~0.5. **A question can
pass a hand-written verification at 0.87/0.07 and still be a coin flip on the corpus it will
actually run against.** This is the single most valuable result of the session and it is exactly
the failure PLAN.md §5's box predicted.

### A domain error of mine, caught by the same run
I had listed **`SEB`** as an *offset*-EB cue. It is not: in TFOP nomenclature `NEB` = **nearby** EB
and `BEB` = **background** EB (both offset), whereas `SEB1`/`SEB2` = **spectroscopic eclipsing
binary** — on-target, and properly a cue for `mentions_spectroscopic_binary`. Moved. C11's 0.35
is partly my error leaking into the question, not the model's.

### The other 8 failures, by cause
- **Literal-token mismatch.** The corpus writes `depth aperture correlation` *unhyphenated*; my
  instruction said `depth-aperture`. C22 blend 0.62 (want Y) and artifact 0.52 (want N) both
  trace to the exclusion clause not binding on the unhyphenated spelling.
- **A negative clause fighting its own positive.** `mentions_instrumental_artifact` said "answer
  no if the text only reports low SNR". C12 is `low SNR; possible instrument or systematic` —
  both at once, so the clauses cancelled: **0.69**, one hundredth under the bar.
- **`depth` is not morphology.** C08 `Slight depth-aperture correlation` scored 0.70 on
  `describes_transit_morphology` (want N). The word `depth` alone carried it.
- **Stating what a signal *is* read as rejecting it.** C09 `8.5 day signal is EB` →
  `indicates_retired_or_rejected` 0.42 (want N) and `reports_stellar_companion_or_blend` 0.53
  (want N — an on-target EB is two stars, but not another star *in the aperture*).
- **Provenance counted as evidence.** C03 `found in faint-star QLP search` — **the single most
  common comment in the corpus, 308 rows** — scored `evidence_depth` **1.86**, i.e. as much
  described evidence as a real follow-up observation. My rubric's level 2 said "one observation or
  data product referenced" and a QLP search *is* a data product, so the model was right and **my
  rubric was wrong.** Left unfixed, `evidence_depth` would have been partly a "came from QLP"
  detector across 11% of the corpus.
**Idempotent:** yes — all 23 responses cached under `data/cache/gate/`; re-running round 1 is $0.00.
**Jev spend this step:** $0.00160 · **running total:** ~$0.0018
**Next:** revise to `r3` and RE-TEST (version bump invalidates the cache, so round 2 is a real
re-test, not a replay).
---
## [2026-09-20T00:11Z] TASK 1 / GATE ROUND 2 (r3) — DONE (13 -> 6 failures) + ONE NEW DEFECT FOUND
**Artifact:** `research/data/gate_2026-09-20.r3_2026-09-19.json` · **97/103 assertions passed**
· 23 calls · 44,430 input tokens · **$0.00187**.

### `reports_offset_eclipsing_binary` — REPAIRED, and the repair is the session's main result

| case | comment | r2 | **r3** |
| :--- | :--- | ---: | ---: |
| C18 | `…; retired as TFOP FP/NEB` | 0.26 | **0.92** |
| C10 | `TFOP FP; retired as NEB` | 0.54 | **0.95** |
| C16 | `close companion star …; retired as NEB` | 0.57 | **0.94** |
| C22 | `…; likely NEB` | 0.86 | **0.97** |
| C17 | `…; retired as EB` (on target) | 0.53 | **0.13** |
| C11 | `TFOP FP/SB1` | 0.35 | **0.08** |
| C09 | `8.5 day signal is EB` | 0.19 | **0.06** |

Positives now **0.92–0.97**, negatives **0.03–0.17**. What did the work was *not* more precision
about the geometry — it was **expanding the acronym in the instruction** (`NEB (nearby eclipsing
binary)`, `BEB (background eclipsing binary)`) and stating that the bare acronym counts **on its
own, with no separation, direction, or star name required**, then naming the excluded acronyms
(`EB`, `SB1`, `SB2`, `SEB1`, `SEB2`) explicitly. The corpus speaks in abbreviations; the question
has to as well.

`evidence_depth` rubric fix also landed: C03 `found in faint-star QLP search` **1.86 -> 1.01**, so
the 308-row provenance boilerplate no longer reads as described evidence.

### ⚠️ NEW DEFECT — `mentions_instrumental_artifact` is a partial LABEL-ECHO detector
The six-failure list hid this, because it shows up on cases where I asserted nothing. Full column:

| case | comment | r3 |
| :--- | :--- | ---: |
| C02 | `TFOP FP` | **0.65** |
| C10 | `TFOP FP; retired as NEB` | **0.62** |
| C11 | `TFOP FP/SB1` | **0.60** |
| C09 | `8.5 day signal is EB` | **0.55** |
| C22 | `…centroid offset and depth aperture correlation; likely NEB` | **0.53** |
| C16 | `close companion star …; TFOP FP; retired as NEB` | **0.46** |
| C17 | `Crowded field; secondary; …; retired as EB` | **0.44** |

**7 of 23 cases land in the 0.30–0.70 mid-band, and every one of them carries a TFOP disposition
token.** The bare string `TFOP FP` — which names no instrument, no systematic, no solar-system
object, nothing — scores **0.65**. Meanwhile the genuine positives are clean (C12 0.94, C19 0.95)
and the genuine negatives are clean (C03 0.06, C06 0.06, C08 0.06).

**Diagnosis:** the model is not answering the question asked. It is inferring
*false positive -> the signal was not real -> therefore it was an artifact*. That is the documented
multi-hop failure mode, and it is the **worst possible place** for it: `TFOP FP` / `retired` tokens
appear in **47.9% of the labelled corpus** (§2.0), so this `TIER_PREDICTIVE` feature would carry a
diffuse echo of the label into the headline result — the exact contamination §2 exists to prevent.
Genuine corpus support for the question is only **32 rows (1.2%)**.

### Pre-committed decision rule for round 3 — recorded BEFORE the run, not after
Round 3 bundles literal-cue fixes for C01/C09/C17/C02 (all of which are over-broad cues I
introduced, not inference). `mentions_instrumental_artifact` additionally gets **one** anti-inference
clause stating that a disposition is not an instrumental cause. **The rule, fixed now:**

> **If case C02 (`TFOP FP`) does not fall to ≤ 0.30 in r4, `mentions_instrumental_artifact` is
> DELETED, not reworded again.** PLAN.md §5: *if a question needs inference, delete it rather than
> reword it a third time* — and 1.2% corpus support does not justify a fourth attempt.

**Idempotent:** yes (r3 responses cached).
**Jev spend this step:** $0.00187 · **running total:** ~$0.0037
---
## [2026-09-20T00:15Z] TASK 1 / GATE ROUND 3 (r4) — DONE · **GATE PASSED 101/103**
**Artifact:** `research/data/gate_2026-09-20.r4_2026-09-19.json` · 10 new calls (13 served from
cache after the crash below) · 20,959 input tokens · **$0.00088**.

### The pre-committed rule was met — `mentions_instrumental_artifact` SURVIVES
> Rule recorded at 00:11Z, before the run: *C02 (`TFOP FP`) must reach ≤ 0.30 or the question is
> deleted.*

**C02 `TFOP FP`: 0.65 -> 0.07.** Mid-band (0.30–0.70) cases **7/23 -> 3/23**. The label-token
contamination is gone from the cases that carry it: C10 0.62->0.12, C16 0.46->0.24, C17 0.44->0.23.
The fix was one clause naming the inference and forbidding it outright — *"A disposition is not an
instrumental cause: 'TFOP FP', 'FP', 'FA' and 'retired' say that the candidate was rejected, not
that an instrument produced the signal."* Telling the model **what not to infer** worked where
describing the positive case better had not.

### All five other targeted repairs landed
| case | question | r3 | **r4** | want |
| :--- | :--- | ---: | ---: | :--- |
| C01 `HAT-P-70 b` | `reports_offset_eclipsing_binary` | 0.34 | **0.08** | N |
| C09 `8.5 day signal is EB` | `reports_stellar_companion_or_blend` | 0.41 | **0.05** | N |
| C09 | `indicates_retired_or_rejected` | 0.33 | **0.08** | N |
| C17 `Crowded field; secondary; …` | `describes_transit_morphology` | 0.67 | **0.86** | Y |
| C02 `TFOP FP` | `indicates_confirmed_planet` | 0.31 | **0.10** | N |

C01 is worth naming: my own r3 cue *"a named nearby TIC given as the eclipse source"* was
over-broad and made a **bare planet designation** score 0.34 for "is there an offset EB?". Bare
designations are **891 rows, 33% of the corpus**, so that regression alone would have injected a
spurious mid-value into a third of the feature matrix. It was introduced *by a fix* and caught
only because the gate re-tests every case every round, not just the ones that failed last time.

### Two residual failures — ACCEPTED, not reworded a fourth time
Both are the same case, C22 `found in faint-star QLP search; significant centroid offset and depth
aperture correlation; likely NEB`:
- `mentions_instrumental_artifact` **0.39** (want N) — down from 0.53, still mid-band.
- `indicates_retired_or_rejected` **0.31** (want N) — one hundredth over the line, and on
  reflection **my assertion is the weaker half of this disagreement**: in TFOP practice "likely
  NEB" *is* a hedged rejection, and this is a `TIER_LABEL_ECHO` question whose job is to capture
  exactly that echo. A small positive here is arguably correct behaviour, not a defect.
**Stopping is the disciplined choice.** Three rounds are already one more than PLAN.md §6 Step 2.5
budgets. Two boundary cases out of 103 assertions do not justify a fourth rewrite, and rewriting
to clear them would be fitting the questions to my own 23-case set — the precise overfitting the
pre-registration exists to prevent. Recorded as known limitations in `PREREGISTRATION.md` instead.

### Idempotence verified, not assumed
Re-ran the gate with no changes: **0 new API calls, $0.00000, identical 101/103 verdict.**

### A bug in my own gate script, found the hard way
Round 3's first attempt died mid-run on `http.client.RemoteDisconnected`. My retry loop caught
only `HTTPError`, so a connection-level failure was fatal. **Fixed** — it now retries
`URLError`, `RemoteDisconnected`, `ConnectionError` and `TimeoutError` with backoff, and raises a
clear error if retries are exhausted instead of falling through on an undefined variable. The
content-addressed cache meant the crash cost **nothing**: 13 of 23 calls were already on disk and
the re-run paid for only the missing 10. This is the §0.5 resumption property working exactly as
designed, on an unplanned failure.
**Note the shape of this bug: it is the same defect as the `etta.download_toi()` one in TASK 3** —
an unbounded or unhandled network failure on the happy path. I wrote it myself while holding a
worklog entry describing it.

### ⚠️ DEVIATION — PLAN.md §6 Step 3 cost estimate is LOW and must be revised
Measured on the final set: **min 2,077 / mean 2,088 / max 2,109 input tokens per row** for 11
questions (the 7-question smoke test measured 603–645).

`2,721 rows x 2,088 tok = 5.68M tok = ` **`$0.239`**

PLAN.md §6 Step 3 says **$0.072** (7 q) / **$0.15** (13 q). Both are low — my questions are far
longer than §5's one-line summaries because the §5 writing rules *require* spelling out cues and
the negative case, and because every Noul now carries `criteria.true`/`criteria.false`. **The
gate's own instruction to write fuller questions is what raised the price.** $0.239 is still well
inside the "$0.50 and something is wrong" tripwire, so the tripwire stands unchanged.
**Jev spend this step:** $0.00088 · **running total:** ~$0.0046 (budget for the session was ~$0.01)
**Next:** record the final set in `research/05`, then `PREREGISTRATION.md`.
---
## [2026-09-20T00:34Z] TASK 2 / PRE-REGISTRATION INPUTS VERIFIED — DONE
**Doing:** verify every number `PREREGISTRATION.md` is about to commit to. PLAN.md has been wrong
six times; nothing goes into a pre-registration on its authority alone.
**Idempotent:** yes (read-only DuckDB + pure-regex modules).
**Artifacts:** `src/exonotes/questions.py`, `src/exonotes/leakage.py`.

### ⚠️ SEVENTH PLAN DEFECT — split S2 leaks host stars across the temporal boundary
PLAN.md §7 S1 says *"Never split within a system; two planets around one star share a comment
record and a host."* **S2 does not obey its own rule.** A TIC can carry two TOIs alerted on
different dates, so it lands on both sides of the cutoff:

| cutoff | TIC straddling the split | test rows affected |
| :--- | ---: | ---: |
| 2021-07-19 | 36 | 40 |
| **2021-10-28** | **30** | **33** |
| 2022-01-25 | 31 | 33 |

33 of 681 test rows (**4.8%**) would have a same-host row in training. Not fatal, but it is
precisely the leak S1 is written to prevent, and it would inflate S2 — the split that G4's
headline claim rests on. **Resolution pre-registered:** after applying the date cutoff, drop from
**test** any row whose `tic_id` also appears in **train**. Dropping from test (not train) keeps the
temporal direction honest — a training row must never be newer than the cutoff.

### S2 cutoff table re-measured — PLAN.md §7 confirmed
| cutoff | train | test | % test | test base | train base |
| :--- | ---: | ---: | ---: | ---: | ---: |
| 2021-07-19 | 1,902 | 819 | 30.1% | 0.651 | 0.440 |
| **2021-10-28** | **2,040** | **681** | **25.0%** | **0.636** | **0.459** |
| 2022-01-25 | 2,160 | 561 | 20.6% | 0.635 | 0.469 |
Within rounding of §7's table (29.6 / 24.7 / 19.9%). `date_toi_alerted` is **100% populated**,
range 2018-09-05 → 2026-08-06. The base-rate shift §7 warns about is real and reproduced.

### ⚠️ EIGHTH DEFECT — §2.0's leakage regex was never recorded, so it cannot be reproduced
`WORKLOG.md` line 217 and PLAN.md §2.0 report "bare planet designation, n=679, P=0.999" but **no
session ever wrote down the pattern that produced 679.** The repo's headline leakage measurement
was therefore unreproducible — on a public repo, an unfalsifiable number. PLAN.md §7 already says
*"Pre-register the exact regex before running it"*; this discharges that.

**`src/exonotes/leakage.py`** now holds it, measured independently per clause:

| clause | pattern | n | P(y=1) |
| :--- | :--- | ---: | ---: |
| L1 | `(?i)retir` | 488 | 0.006 |
| L2 | `(?i)tfop\s*(?:wg)?\s*[/-]?\s*(?:fp\|fa\|cp\|kp)\b` | 543 | 0.006 |
| L3 | `(?i)\b(?:validat\w*\|confirmed planet\|published\|known planet)\b` | 21 | 0.905 |
| L4a | whole comment is a catalogue designation | 795 | **0.999** |
| L4b | short clause ending in a bare planet letter | 682 | **1.000** |

L4a/L4b reproduce §2.0's P=0.999 finding on a **larger** set (795/682 vs 679). L4b exists because
L4a missed the Bayer and white-dwarf forms — `pi Men c`, `55 Cnc e`, `DS Tuc A b`,
`WD 1856+534 b`, `nu 2 Lup b`. **Audited: L4b strips exactly 5 rows beyond L4a and all 5 are
genuine designations — zero false positives on prose.**

**Result — G5 arm: 1,269 rows · 1,222 TIC · base rate 0.431.** Stripped: 1,452 (53.4%), base 0.566.
**Deviation from PLAN.md §7**, which predicted 1,417 rows / 1,312 TIC / 0.485. Mine strips ~5.5
points more. **Over-stripping is the correct direction:** a surviving leak lets G5 pass on label
echo, which is the one thing G5 exists to detect, and it cannot be detected after the fact.
Survivors are now genuine observational fragments (`low SNR`, `V-shaped`, `flat-bottomed`).
Note the arm is **imbalanced (0.431)** where the full corpus is 0.503 — stripping removes more
positives than negatives, so G5's AUC is not directly comparable to G2's.

### Question set frozen and de-duplicated
Lifted verbatim out of the gate into `src/exonotes/questions.py` (PLAN.md §4's specified home) and
made the gate import it, so the pre-registered set and the tested set are the same bytes. **Proof
the extraction changed nothing: re-running the gate made 0 API calls** — the cache key hashes the
question JSON, so an identical hash is an identical set. 101/103, $0.00000.
**Final set: 11 questions — 8 `TIER_PREDICTIVE` + 3 `TIER_LABEL_ECHO`.**
**Jev spend:** $0.00 · **running total:** ~$0.0046
**Next:** write `PREREGISTRATION.md`.
---
## [2026-09-20T00:43Z] REDACTION + AUTHORSHIP CORRECTION — DONE (user-directed)
**This entry exists because a past entry was edited.** PLAN.md §0.5 non-negotiable #2 is
*append only — never edit or delete a past entry*. The 2026-09-19T23:50Z entry raised the local
paths as an **open item for the user**; the user has now directed the redaction. Recording it here,
in a new entry, is the condition under which that edit is legitimate: the change is logged, not
silent. **Nothing was removed except the username string itself** — no finding, measurement,
timestamp or conclusion was altered, and the surrounding text still says what it always said.

### What was edited
| file | occurrences | change |
| :--- | ---: | :--- |
| `WORKLOG.md` | 5 | the macOS home prefix + short username → `/Users/<user>` |
| `WORKLOG.md` | 2 | `-Users-arce-Projects-` → `-Users-<user>-Projects-` |
| `WORKLOG.md` | 2 | bare `` `arce` `` in the prose discussing this very issue → `` `<user>` `` |
| `HANDOFF_PROMPT.md` | 1 | same substitution → `/Users/<user>` |
PLAN.md §11.6 item 9 (`git grep -nE '/(Users|home)/[a-z]'`) now returns **nothing**. ✅

### ⚠️ A REAL DEFECT the §11.6 check could not see
`scripts/00_smoke_test.py` line 91 hard-coded
`"/private/tmp/claude-501/-Users-<user>-Projects-Jev/<session-uuid>/scratchpad/smoke_out.json"`.
The §11.6 grep only looks for `/Users/` and `/home/`, so **a `/private/tmp/…` absolute path sailed
straight through a checklist item whose stated purpose is "no absolute local paths anywhere in
tracked files."** It leaked the username *and* the project's former name *and* a dead session id,
and it is a live **bug**: the path does not exist on any other machine, so a new contributor
running the script gets the full run and then a crash on the final write. Fixed to a
repo-relative `data/smoke_out.json`; the `.env` read made CWD-independent (it assumed the repo
root); a shadowed variable renamed; and a SUPERSEDED banner added pointing at
`scripts/025_question_gate.py`. **The checklist grep should be widened** — recommended
`git grep -nE '"/(private/)?(tmp|Users|home|var)/'`, which is what found this.

### Git authorship corrected — user-directed
`git log` showed **one** commit out of six attributed to the wrong identity:
`20c11ae "Update handoff TASK 3: repo is now public"` was authored **and** committed as
`ExoNotes <arcetechnologies@gmail.com>`. The other five were already correct.
Amended to `KevinArce <iav.kevinarce@ufg.edu.sv>` (now `6b28005`).
**`git diff 20c11ae HEAD` is empty — only metadata changed, not one byte of content.**
Local and global `git config` were already correct, so this was a one-off, not a misconfiguration
that would recur.

### 🚩 BLOCKED ON THE USER — this rewrite needs a force-push and I have not done it
`20c11ae` was **already pushed** to `github.com/KevinArce/ExoNotes`. Rewriting it leaves the branch
`ahead 1, behind 1`, so publishing the correction requires:
```
git push --force-with-lease origin master
```
**I have not run it and will not without explicit confirmation.** Force-pushing rewrites public
history: anyone who cloned or forked between the push and now keeps the old commit, and open PRs
referencing it can break. The user authorised *changing the attribution*; they did not
specifically authorise a force-push, and that is the kind of outward-facing, hard-to-reverse
action that gets confirmed rather than assumed. The alternative — leave `20c11ae` published as-is
and simply use the right identity from here on — is a legitimate choice and costs nothing.
**Jev spend:** $0.00 · **running total:** ~$0.0046
---
## [2026-09-20T00:46Z] CORPUS DECISION — USER CHOSE `download_obsnotes`; RECON — STARTED
**Trigger:** user answered the §2.2 open decision: **switch to `download_obsnotes`**.
**Doing:** reproduce §2.2's measurements before `PREREGISTRATION.md` commits to them, and quantify
the `Master Disp:` leakage channel §2.2 warns about but never measured.
**Idempotent:** yes — read-only GETs, results cached to `research/data/`.
**Two findings already, before the recon proper:**
1. **My own bug, worth recording.** `etta.download_obsnotes(tic)` passes the TIC as **`tag`** —
   the signature is `(tag=None, tic=None, row_id=None, ...)`, so the first positional argument is
   *not* the TIC. That call hits `?tag=<tic>` and returns a **well-formed empty table**: 7 correct
   column headers, 0 rows, HTTP 200. I briefly believed the corpus was empty and that §2.2 was
   wrong. The correct call is `etta.download_obsnotes(tic=...)` → `?tid=<tic>`. **A silent empty
   result is the worst failure shape there is** — it looks like a measurement. Any scraper must
   assert non-empty on known-good TICs rather than trust a 200.
2. **ExoFOP is only PARTIALLY throttled.** The per-TIC endpoints answer normally (0.7–8.0 s) while
   the bulk `download_toi.php` full-table pull still returns zero bytes. So TASK 3's clean-clone
   test is blocked specifically on the **bulk** endpoint, not on ExoFOP as a whole. One per-TIC
   call did die with `RemoteDisconnected` — the same failure class as the `etta.download_toi()`
   bug, now observed on the endpoint the new corpus depends on.
---
## [2026-09-20T00:51Z] OBSNOTES RECON — DONE · §2.2 PARTLY CONFIRMED, PARTLY WRONG
**Artifacts:** `scripts/027_obsnotes_recon.py`, `research/data/obsnotes_recon_2026-09-19.json`
(30 TIC, 15 per class, seeded; 79 notes). **Idempotent:** yes — per-TIC responses cached under
`data/cache/obsnotes/`; the re-run below did 0 network calls.

| PLAN.md §2.2 claim | measured 2026-09-20 | verdict |
| :--- | :--- | :--- |
| 30/30 TIC have ≥1 note | 30/30 | ✅ |
| median 3 notes/TIC (mean 4.2, max 26) | median **2**, mean 2.6, max **10** | ⚠️ optimistic |
| median **2,384** chars/TIC | median **991** | ❌ **overstated 2.4×** |
| 70% carry HTML | 63% (19/30) | ✅ |
| note count is label-correlated (5 vs 2) | **3 (y=1) vs 2 (y=0)** | ✅ real, weaker |
| 3.24 s/TIC → ~2.3 h for 2,573 TIC | **3.21 s/TIC → 2.30 h** | ✅ exact |
| tfopwg notes "state `Master Disp:` outright" | **100% of TIC — 30/30** | ⚠️ far worse than implied |
| observer notes separable from the tfopwg summary | **yes — and it works** | ✅ **the decisive finding** |

### The leakage is total — and then it is completely removable
**Every single TIC's notes contain `Master Disp: <value>` verbatim.** Values seen: `P`, `KP`, `VP`,
`SEB`, `EB`, `NEB`, `FA` — 15 planet-side and 15 false-positive-side across a 15/15 balanced
sample. **This string is not a proxy for the label, it is the label**, and it is present in 100% of
the corpus versus 53.4% for `Comments`. Judged naively, obsnotes would be **strictly worse** than
the corpus we already have.

**But the leakage is confined to one separable channel.** Filtering `Groupname == 'tfopwg'`:
- **20/30 TIC (67%) retain ≥1 observer note**, median **2 notes** and **780 chars** — still **26×**
  the 30-char `Comments` median.
- **0 of those 20 contain any `Master Disp:` / `Phot Disp:` / `Spec Disp:` string.** The
  disposition leakage drops from 100% to **zero** on a single mechanical filter.

`Comments` has no equivalent cut: its leakage is interleaved with its content in the same field.

### A correction to my own measurement, caught before it misled the pre-registration
My first pass reported **0/30 TIC with observer notes** and I nearly wrote that down. The bug:
observer notes come back with `Groupname` = **`nan`**, and I had excluded `nan` along with
`tfopwg`. Their `Username` is a real person — `everett`, `latham`, `furlan`, `baranec`, `quinn`,
`mayo`, `gautier`, `isaacson`. **45 of 79 notes (57%) are observer notes.** Fixed: a note is a
TFOPWG summary **iff `Groupname == 'tfopwg'`**, everything else is an observer note.

### What the observer notes actually contain — and why it changes the question set
> *"WIYN speckle imaging using NESSI was taken of TIC156648452 on 2022-04-18 … No secondary
> sources were detected."*
> *"Rick Schwarz / LCO-Teid-1m0 analyzed a deep full on 20231219 in zs and cleared 6/6 neighbors
> to 2.5'."*
> *"Robo-AO i-band imaging of KOI-12 on 2012-07-17. No companions detected within 2.5"."*

**This is the follow-up narrative that `Comments` does not have.** Today's gate deleted
`reports_on_target_detection` (11 rows, ~2 genuine) and `indicates_followup_complete` (2 rows, 0
genuine) **for lack of support in `Comments`** — and the text above is precisely what both
questions were written to detect. **Both deletions must be revisited on obsnotes.**

`Lastmod` spans 2009→2026 with genuine spread (2020 n=16, 2022 n=14, 2024 n=8). §2.2's
bulk-migration cluster is visible but minor here (`2020-09-18 12:01` ×4). Some Kepler-era notes
carry their original 2011/2014 stamp with a migration preamble, so the date survived the move.

### ⚠️ CONSEQUENCE — today's gate result does NOT transfer to the new corpus
`QUESTION_SET_VERSION 2026-09-20.r4` scored 101/103 **on `Comments` text**. Switching corpora makes
that verification **inapplicable**, for exactly the reason PLAN.md §5's warning box gives: a
question verified on one text distribution says little about another. Obsnotes notes are ~26×
longer, multi-sentence, HTML-laden and written in a different register. **Step 2.5 must be re-run
against real obsnotes text before Step 3**, with both deleted questions restored as candidates.
Pre-registering otherwise would repeat the exact error this project has already made once.
**Jev spend:** $0.00 · **running total:** ~$0.0046
**Next:** `PREREGISTRATION.md`.
---
## [2026-09-20T00:57Z] TASK 2 — `PREREGISTRATION.md` WRITTEN · TASK 3 — TIMEOUT BUG FIXED
**Artifacts:** `PREREGISTRATION.md`, `research/05_question_design_gate.md`,
`src/exonotes/questions.py`, `src/exonotes/leakage.py`, `scripts/025_question_gate.py`,
`scripts/027_obsnotes_recon.py`, hardened `scripts/01_ingest.py`.
**Idempotent:** yes throughout.

### TASK 2 — what the pre-registration fixes
- **Corpus:** `download_obsnotes`, **observer notes only** (`Groupname != 'tfopwg'`), per the
  user's decision. Unit of analysis stays the **TOI** so the existing labels and baseline B remain
  comparable; text is the TIC's observer notes, HTML-stripped, `Lastmod`-ordered.
- **Projected scale recorded BEFORE the run: ~1,814 rows / ~1,715 TIC**, down from 2,721 / 2,573.
  **This makes G2 harder**, and saying so now is the point — a null cannot later be waved away as
  "too few rows".
- **S2 cutoff FIXED: `date_toi_alerted < 2021-10-28`.** Sizes will be re-measured on the new
  corpus and **reported, not re-chosen**.
- **S2a** closes the group leak (drop straddling TICs from *test*). **S2b** adds a note-level
  `Lastmod < cutoff` filter on the training side — the real temporal control that `Comments` could
  never support, with its "last-modified, not created" limitation stated.
- **G1–G6** with exact numeric criteria; G1's passed value recorded **and** required to be
  re-established on the new row set.
- **G5 regex** written out in full, with per-clause counts, plus an obsnotes-specific `L5` probe
  for `Master Disp:` that **should never fire** — if it does, the corpus filter failed and Step 3
  stops.
- **§8.1 commits to publishing a null**, and §8.2 lists what will not be done (no threshold
  tuning, no swapping the headline tier, no re-picking the cutoff after seeing a result).
- **§2 is explicitly PROVISIONAL**: the r4 set was gated on `Comments` text, so Step 2.5 must be
  re-run on observer-note text and the set re-frozen before Step 3.

### TASK 3 — `etta.download_toi()` hang: FIXED and verified against the live failure
`fetch_exofop()` now fetches the bulk CSV with `requests.get(..., timeout=(10, 300))` and a
bounded retry (4 attempts, 5/10/20 s backoff). `etta` is kept for the per-TIC endpoints.
Added a **sanity check the original lacked**: a response under 100 KB, or missing `Comments` in
its header, is rejected as truncated rather than written to disk — because a short valid-looking
CSV is exactly how a throttled pull can poison a snapshot silently.

**Verified two ways, not asserted:**
1. **Happy path** — re-ran `01_ingest.py` from cache: all three raw checksums **unchanged**,
   `analysis_set` still 2,721 / 2,573 / 0.5031, `baseline_*` tables intact.
2. **Failure path, against the genuinely throttled live endpoint** (ExoFOP is *still* withholding
   as of this timestamp — `http=000 connect=0.11s size=0` after 30 s). With the read timeout
   shortened so the test takes seconds, `fetch_exofop` **raised `SystemExit` after 38.3 s instead
   of hanging**, printed the retry notice, named throttling as the likely cause, gave three
   concrete remedies, and **wrote no partial file**. This is the bug's real trigger condition, not
   a simulation of it.

### TASK 3 / ITEM 10 — clean-clone reproduction STILL BLOCKED
Re-probed at 00:46Z and 00:55Z: bulk `download_toi.php` still returns **zero bytes** after a fast
TCP connect. Per-TIC endpoints answer normally, so this is endpoint-specific throttling, not an
outage. **Checklist item 10 remains UNVERIFIED and the repo must still not be described as
reproduction-verified.** The fix above at least converts that failure from an infinite silent hang
into a 20-minute bounded failure with an actionable message.
**Jev spend:** $0.00 · **running total:** ~$0.0046 (session budget was ~$0.01)
**Next:** commit; report to user. **Step 3 is NOT started — it belongs to the next session.**
---
## [2026-09-20T01:00Z] SESSION END — Claude Opus 5
**Completed:** TASK 1 (Step 2.5 question gate, 3 rounds, 101/103), TASK 2 (`PREREGISTRATION.md`
committed), TASK 3 (ExoFOP timeout bug fixed and verified live; redaction and authorship done).
`HANDOFF_PROMPT.md` rewritten for the corpus switch.
**Jev spend this session: $0.0044** · **project running total: ~$0.0046** (budget was ~$0.01).
**Committed:** `0f0a40d`, authored `KevinArce <iav.kevinarce@ufg.edu.sv>`. **Not pushed.**

**NOT done, deliberately:** Step 3 not started — it belongs to the next session and is now gated
behind acquiring the obsnotes corpus and re-running Step 2.5 on it.

**Plan defects found this session: two new ones (#7 S2 group leak, #8 unrecorded leakage regex),
bringing the running total to eight.** Plus one cost estimate corrected upward ($0.072/$0.15 →
$0.239 measured for 11 questions on 2,721 rows) and three of §2.2's obsnotes measurements
corrected (chars/TIC overstated 2.4×, notes/TIC optimistic, `Master Disp:` far more pervasive than
implied).

**Three open items for the user:**
1. **Force-push pending** for the authorship correction (`ahead 2, behind 1`). Not run — it
   rewrites public history and needs explicit confirmation.
2. **Clean-clone reproduction still UNVERIFIED** — ExoFOP bulk endpoint throttled all session
   (probed 4×, always `http=000 size=0`). The repo must not be called reproducible yet.
3. **The r4 question set is provisional** and must be re-gated on observer-note text before Step 3.

**Resume at:** `HANDOFF_PROMPT.md` — TASK A (pull obsnotes), then TASK B (re-gate), then TASK C.
---
