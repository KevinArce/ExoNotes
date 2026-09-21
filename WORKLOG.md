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
## [2026-09-20T01:14Z] FORCE-PUSH CONFIRMED BY USER — VERIFIED ON THE REMOTE
**Doing:** user authorised and ran `git push --force-with-lease origin master`. Verifying the
authorship correction actually landed rather than assuming it did.
**Idempotent:** yes (read-only inspection; the push itself reported `Everything up-to-date`,
i.e. the user had already run it).
**Verified on `origin/master`:**
- **All 8 commits** are authored **and** committed by `KevinArce <iav.kevinarce@ufg.edu.sv>`.
- `git log --format='%ae %ce' origin/master | sort -u` returns **exactly one address**:
  `iav.kevinarce@ufg.edu.sv`. No other identity appears anywhere on the branch.
- `20c11ae` (the `ExoNotes <arcetechnologies@gmail.com>` commit) is **no longer an ancestor of any
  remote branch**. It survives locally as a dangling object via the reflog, which is expected and
  will be garbage-collected.
**⚠️ Honest caveat — this is not a full erasure.** GitHub retains unreachable commits and will
still serve `20c11ae` to anyone who requests that SHA directly for some time. The commit is off
the branch and out of the history everyone sees; it is not cryptographically gone. Since the whole
point was the attribution, it is worth stating plainly rather than claiming the record is clean.
Nothing sensitive is in it — only a name and an email on a commit whose content was byte-identical.
**Checklist item, now closed:** git authorship ✅.
**Jev spend:** $0.00 · **running total:** ~$0.0046
---
## [2026-09-20T01:22Z] SIDE QUEST 01 — CI CLEAN-CLONE REPRODUCTION — STARTED
**Doing:** a GitHub Actions workflow that performs the §11.6 item-10 clean-clone reproduction from
GitHub's runners instead of this host, and asserts G1 reproduces. Plus a standalone verifier
script so the same check runs locally.
**Why now:** item 10 has been blocked for two sessions by ExoFOP throttling **this host**. The
per-TIC endpoints prove ExoFOP is up; the bulk endpoint is refusing *us*. A runner has a different
IP each run, so CI sidesteps the throttle entirely — and it converts item 10 from "someone
remembered to test it once" into a check that re-verifies on a schedule.
**Scope:** this is a **one-shot side quest**, taken before the established next steps (obsnotes
pull → re-gate → Step 3). It is documented separately so it does not blur into them.
**Idempotent:** yes — workflow and scripts are declarative; the verifier is read-only.
**Jev spend:** $0.00 (no API calls in this task) · **running total:** ~$0.0046
---
## [2026-09-20T01:27Z] SIDE QUEST 01 — CI CLEAN-CLONE REPRODUCTION — DONE (built, not yet run on GitHub)
**Artifacts:** `.github/workflows/reproduce.yml`, `scripts/029_verify_reproduction.py`,
`SIDEQUEST_01_CI_REPRODUCTION.md`, README badge + honest reproduction note, handoff pointer.
**Idempotent:** yes — declarative workflow; the verifier is read-only and takes `--db`.
**Jev spend:** $0.00 · **running total:** ~$0.0046

### Design decision — the assertion tolerates drift deliberately
`PLAN.md` §11.2 states the sources drift, so demanding `B == 0.9154` would turn ordinary archive
drift into a red build, and a check that cries wolf gets ignored. The verifier asserts the
**finding**: rows within ±25%, prior at chance (±0.02), **B ≥ 0.85 AUC**, and B > A on both AUC
and Brier. Baseline C is printed with its leakage warning but **never asserted on**, so nobody
lifts 0.9691 out of a CI log and mistakes it for a result. Exit 0 / 1 / 2 distinguishes
reproduced / check failed / inputs missing.

### Verified locally BEFORE it ever runs on GitHub
- Passes on the real database (**exit 0**).
- **Can fail** — against a doctored DB (`B_numeric` → 0.61, `rows_analysis` → 300) it returns
  **exit 1** naming both failures. *A check that cannot fail is theatre; this one was tested.*
- Missing DB → **exit 2**, distinct from a failed check.
- **All 7 `run:` blocks pass `bash -n`.** YAML parses with the intended triggers, defaults,
  timeout and concurrency.
- **Failure classifier tested in both directions against a REAL throttled ingest log** generated
  on this host: a throttle log matches and reports "upstream, not a code failure"; a `KeyError`
  traceback does not match and reports a genuine code failure.

### ⚠️ TWO BUGS FOUND IN MY OWN DRAFT, both fixed before commit
1. **`python … | tee log` returns *tee's* exit code.** GitHub's implicit shell is `bash -e`
   **without** `pipefail`, so a **failed verification would have been masked and the badge would
   have gone green on a broken reproduction** — the precise inverse of this task's purpose. Fixed
   by declaring `shell: bash` in the job defaults, which yields `-eo pipefail`.
2. **The draft probed ExoFOP with a separate full 3.8 MB download**, doubling our load on the
   archive that is already throttling us. Removed — `01_ingest.py` is now its own probe and its
   failure is classified afterwards. **Building a reproducibility check that worsens the problem
   it exists to work around would have been self-defeating.**

### Deliberately NOT run on every push
A full TOI pull is a real cost to a public archive, and hammering ExoFOP from CI is exactly what
got this host throttled. Triggers are `workflow_dispatch` + weekly cron + push **restricted to
`scripts/`, `src/`, `requirements.txt`**, with `concurrency.cancel-in-progress` so a burst of
commits collapses to one pull.

### Known risk, recorded in advance
`requirements.txt` pins `catboost==1.2.10`, verified on Python 3.14 **macOS/arm64**. If no Linux
3.14 wheel exists, CatBoost will attempt a source build and likely fail on `ubuntu-latest`.
**That would be a genuine finding, not a CI annoyance** — it would mean `requirements.txt` is not
portable and anyone cloning on Linux hits the same wall. This check surfacing it would be the
check doing its job.

**STILL OPEN:** item 10 is **not closed**. The workflow has been built and locally verified but
**never executed on GitHub**. Until a green run exists, the repo must not be called
reproduction-verified. Next session: **Actions → reproduce → Run workflow**, then log the outcome.
---
## [2026-09-20T01:31Z] SIDE QUEST 01 — ✅ **GREEN ON THE FIRST RUN · CHECKLIST ITEM 10 CLOSED**
**Run:** [35481446612](https://github.com/KevinArce/ExoNotes/actions/runs/35481446612), triggered
by the push (it touches `scripts/**`), **conclusion `success` in 1m32s** on `ubuntu-latest`,
Python 3.14.7.
**Idempotent:** yes. **Jev spend:** $0.00 · **running total:** ~$0.0046

```
[PASS] analysis rows within +/-25% of reference     2721 (ref 2721, band 2040-3401)
[PASS] unique TIC > 0                               2573 (ref 2573)
[PASS] A (prior) sits at chance                     AUC 0.5000 (ref 0.5000)
[PASS] B (numeric) AUC >= 0.85                      AUC 0.9149 (ref 0.9154, delta -0.0005)
[PASS] B beats A on AUC                             0.9149 > 0.5000
[PASS] B beats A on Brier                           0.1141 < 0.2501
REPRODUCTION VERIFIED - gate G1 reproduces from a clean build.
```

**`PLAN.md` §11.6 is now 10/10.** After two sessions blocked, the repo is
**reproduction-verified** — and it re-verifies weekly rather than once.
**ExoFOP answered the runner immediately while still refusing this host**, which confirms the
throttle is per-IP. The `catboost==1.2.10` / Python 3.14 Linux-wheel risk I recorded in advance
**did not materialise** — it installed from a wheel.

### ⚠️ UNEXPECTED FINDING — the −0.0005 is NOT archive drift, and it matters for G2
I built the check expecting the archives to have moved. **They had not.** Downloaded the run's
`PROVENANCE.md` artifact and diffed it: **all three raw sources are byte-identical SHA256** to the
committed checksums (`exofop_toi` 3,806,771 B, `nea_toi` 2,048,596 B, `nea_pscomppars`
1,147,680 B).

**Identical inputs, and yet B = 0.9149 on linux/x64 vs 0.9154 on macos/arm64.** The difference is
**compute nondeterminism** — floating point, threading, BLAS — not data. Within one platform the
pipeline is exactly repeatable (this host reproduces 0.9154 to four decimals on every re-run).

**Consequence for G2, recorded now rather than discovered later:** the headline test is a ΔAUC
with a bootstrap CI excluding zero, and there is now a **measured ~5×10⁻⁴ cross-platform noise
floor from arithmetic alone**. Small against the ~0.08 of headroom over baseline B, but it means
**model-vs-model comparisons must run on one platform**, and any claimed gain below ~10⁻³ is
noise. We only learned this because the same bytes ran on two architectures — a side effect of
the CI work, not something it was built to find.

**Corrected my own wording:** the verifier said "drift", which implies the data moved. It now says
"delta" and prints how to tell the two apart — different checksums mean the archive moved;
identical checksums with a non-zero delta mean compute nondeterminism.

### A second widening of §11.6
Item 9's grep (`/(Users|home)/[a-z]`) **missed** the `/private/tmp/...` path in
`00_smoke_test.py`. `PLAN.md` §11.6 now also specifies
`git grep -nE '"/(private/)?(tmp|Users|home|var)/'`.

**Updated:** `PLAN.md` §11.6 (item 10 ✅, item 9 widened), `SIDEQUEST_01_CI_REPRODUCTION.md`
(now a record, with the outcome and the nondeterminism finding),
`HANDOFF_PROMPT.md` (side quest closed, G2 noise-floor note added).
**Next:** `HANDOFF_PROMPT.md` TASK A — pull the obsnotes corpus.
---
## [2026-09-20T01:33Z] SIDE QUEST 01 — SECOND RUN ALSO GREEN; NONDETERMINISM FINDING STRENGTHENED
**Run:** [35481621813](https://github.com/KevinArce/ExoNotes/actions/runs/35481621813) —
`conclusion: success`. Triggered by the doc/verifier commit, which usefully re-validated the
edits I had just made to `029_verify_reproduction.py`.
**Idempotent:** yes. **Jev spend:** $0.00 · **running total:** ~$0.0046

**The second run reproduced `B = 0.9149` to four decimals, exactly as the first did**, on a
separate runner instance. That upgrades yesterday's claim:

| platform | runs | baseline B AUC |
| :--- | ---: | ---: |
| macos/arm64 (dev host) | 2 | **0.9154** |
| linux/x64 (GH runner) | 2 | **0.9149** |

Two independent observations per platform, **identical within each platform, differing by
5×10⁻⁴ between them**, on byte-identical inputs. So the difference is a **systematic
architecture effect, not run-to-run randomness** — which is the more useful conclusion, because a
systematic offset is something you control for by pinning the platform, whereas randomness would
have to be averaged out. The G2 guidance stands and is now better evidenced: **run
model-vs-model comparisons on a single platform; treat any claimed ΔAUC below ~10⁻³ as noise.**

**Also confirmed working as designed:** this commit touched only `WORKLOG.md`, which is **not** in
the workflow's trigger paths (`scripts/**`, `src/**`, `requirements.txt`,
`.github/workflows/reproduce.yml`), so it does **not** trigger another ExoFOP pull. The path
filter is doing its job of keeping load off a public archive.
**Next:** `HANDOFF_PROMPT.md` TASK A — pull the obsnotes corpus.
---
## [2026-09-20T16:32Z] SESSION START — Opus 5, 2026-09-20
**Doing:** adversarial pre-flight review of the whole project ahead of TASK A, at the owner's
request: interrogate every architectural decision, statistical assumption and methodology choice,
especially the three risks flagged in the previous handoff.
**Idempotent:** yes — read-only analysis, plus append-only documents.
---
## [2026-09-20T16:32Z] AUDIT 01 — STARTED
**Doing:** (1) draft the `PREREGISTRATION.md` §11 amendment for the findings that change the
registered design; (2) build the B+N noise-floor control arm as a runnable script; (3) write up
every finding; (4) rewrite `HANDOFF_PROMPT.md` around them.
**Command:** `.venv/bin/python scripts/026_noise_floor.py`
**Idempotent:** yes — no network, no API calls, fixed seeds, CREATE OR REPLACE output.
**Jev spend this step:** $0.00 · **running total:** ~$0.0046
---
## [2026-09-20T16:38Z] AUDIT 01 — DONE
**Result:** 13 findings. 4 change the registered design, 5 change how a step is run, 4 are
recorded for the write-up. 2 of the reviewer's own hypotheses were tested and **failed**; both
are recorded rather than dropped.

### The two that would have wrecked the study
1. **G2 had no zero point.** `scripts/026_noise_floor.py` (new) measures the arm G2 was missing:
   at the projected obsnotes scale (1,811 rows / 1,715 TIC / base 0.491), baseline B scores
   **0.9044**, and **B plus 8 columns of pure Gaussian noise scores 0.8932 — ΔAUC −0.0112**, with
   every one of 5 seeds producing a paired bootstrap CI that **excludes zero**. That is over 4×
   the SE of the G2 statistic (0.0026). So a reported ΔAUC of 0.000 is **not** a null; it is
   ~+0.011 of real signal cancelling dilution, and `PREREGISTRATION.md` §8 would have mapped it
   onto "Stop. Write the negative result."
   Not a tuning artifact: across 5 CatBoost configurations the penalty ran −0.0100 to −0.0132, and
   **early stopping made it worse**.
2. **G5's regex is dead code on this corpus.** `src/exonotes/leakage.py` was written for 30-char
   `Comments`; `L4a`/`L4b` are anchored `^…$`. On the 20 cached observer-note TICs, L1 **0/20**,
   L2 **0/20**, L4a **0/20**, L4b **0/20**, any clause **1/20**. The G5 arm would be ~95% identical
   to the full arm, so **G5 would pass trivially** — and §8 reads a G5 pass as "the effect was not
   label echo." The leak is real but differently shaped: `NEB`/`BEB`/`cleared`/`retired` are all
   0/20, while `TOI-\d+` fires **13/20** and one note opens "Extracted KOI12 observing note from
   ExoFOP-Kepler."

### Also registered
- **MDE fixed before the run: +0.0073** (80% power, two-sided 95%; SE 0.0026). Net of the dilution
  floor, **0.0186 of true signal** is required. A single Jev feature needs **≈0.65 univariate AUC**
  against the label to be visible at all — 0.59 is invisible. §8.1's "report the power we had" is
  **withdrawn**: observed power is a monotone function of the p-value and carries no information.
- **`toi` removed from the request state.** No question reads it, and it handed the model a
  catalogue designation — the P=0.999 channel — in a field the G5 regex never sees.
- **Model pinned to `jev-1.13.0`.** `jev-latest` sat inside the cache key, so a version bump would
  have served old-model cache hits beside new-model misses under an identical key.
- **ΔAUC aggregation defined** (pool OOF within a repeat, score each repeat, average; bootstrap
  resamples TIC groups and uses the **same** resample for both models) — it was undefined, and
  S1's 3 repeats make three different answers possible.
- **B+meta control arm added**, because `evidence_depth` is a semantic proxy for the note-count
  feature §10.2 bans. Selection effect measured at P(note|y=1) **0.80** vs P(note|y=0) **0.53**.
- Question-gate cases must be **label-blinded** in TASK B; the r4 cases carried `y=`.
- `Groupname != 'tfopwg'` is in practice `Groupname IS NULL` (only two values exist in the data).
- 20/30 obsnotes cache files contain bare `NaN` and are **not valid RFC-8259 JSON**.

### Hypotheses tested and abandoned — recorded so the review is not only its hits
- **"Known Planets inflate baseline B."** False. B = 0.9128 all-in, **0.9231 with KP excluded**
  (n=2,120, base 0.362), 0.9211 KP-only. B is slightly *better* without them. No KP arm warranted.
- **"The cross-platform 5×10⁻⁴ offset matters."** Real, but ~15× below the MDE. Keep the
  single-platform rule as hygiene; retire the 10⁻³ figure as a decision threshold.

**Artifacts:** `AUDIT_01_PREFLIGHT_REVIEW.md` (new), `scripts/026_noise_floor.py` (new),
`research/data/noise_floor_2026-09-20.json` (new), `data/exonotes.duckdb::noise_floor` (new),
`PREREGISTRATION.md` §11.1 amendments **A-1 … A-8** (append-only), `HANDOFF_PROMPT.md`
(rewritten), `README.md` (reproduce list).
**Jev spend this step:** $0.00 · **running total:** ~$0.0046
**Next:** `HANDOFF_PROMPT.md` TASK A — pull the obsnotes corpus, with the A-10/A-11 assertions.
---
## [2026-09-20T17:03Z] CORRECTION — the "pending force-push" open item was already closed
**What was wrong:** `HANDOFF_PROMPT.md` carried "a force-push is still pending and has NOT been
run" as open item 1. It had in fact been run and verified at **2026-09-20T01:14Z** (see that
entry). The previous handoff was stale on this point, and audit 01's rewrite **copied the stale
item forward without checking it** — a verification failure in a session whose whole purpose was
verifying claims.

**Trigger:** the user ran an ordinary `git push` and reported no issue, which is not what a
diverged branch does.

**Verified now, read-only:**
- `git rev-list --left-right --count origin/master...HEAD` → **0 0**. Not diverged; nothing to force.
- `git ls-remote origin master` → `9f8f78f`, identical to local `HEAD`. Audit 01 is published.
- `git log --format='%an <%ae>' | sort | uniq -c` → **13 commits, one identity**,
  `KevinArce <iav.kevinarce@ufg.edu.sv>`.
- `git merge-base --is-ancestor 20c11ae origin/master` → **false**. The mis-attributed commit is
  not in public history; it survives only as a dangling local reflog object.

**Unchanged caveat:** GitHub still serves unreachable commits by direct SHA for a time. The
attribution is off the branch, not cryptographically erased.

**Updated:** `HANDOFF_PROMPT.md` — open items section now reads "there are none", with the
verification recorded so the next session does not resurrect it a third time.
**Jev spend this step:** $0.00 · **running total:** ~$0.0046
**Next:** `HANDOFF_PROMPT.md` TASK A — pull the obsnotes corpus.
---
## [2026-09-20T17:05Z] SESSION START — Claude Opus 5
**Resumption:** last entry is the 17:03Z CORRECTION, `DONE`, `Next:` = TASK A. No orphan
`STARTED`. Nothing interrupted.
**Read before acting:** `AUDIT_01_PREFLIGHT_REVIEW.md`, `PREREGISTRATION.md` §1 + §11
(A-1…A-8), `WORKLOG.md` tail, `PLAN.md` §0.5 + §1, `scripts/027_obsnotes_recon.py`.
**State verified read-only before starting:**
- `analysis_set` = **2,721 rows / 2,573 TIC / base rate 0.5031**
- `data/cache/obsnotes/` = **30 files**, of which **10 are valid RFC-8259 JSON and 20 are not**
  (bare `NaN`) — exactly as A-11 records.
- DuckDB tables present: `analysis_set`, `baseline_results`, `baseline_summary`,
  `ingest_provenance`, `ingest_stats`, `noise_floor`, `toi_snapshot`.
**Picking up:** TASK A — acquire the obsnotes corpus for all 2,573 TIC.
**Jev spend this step:** $0.00 · **running total:** ~$0.0046
---
## [2026-09-20T17:12Z] TASK A — STARTED
**Doing:** acquire observer notes for all 2,573 TIC in `analysis_set`; persist to DuckDB;
report realised coverage and base rate. Handoff `HANDOFF_PROMPT.md` TASK A, with the A-10 /
A-11 assertions.
**Command:** `.venv/bin/python scripts/028_obsnotes_pull.py`
**Idempotent:** yes — per-TIC responses cached content-addressed under `data/cache/obsnotes/`;
a re-run does no network I/O. DuckDB writes are `CREATE OR REPLACE`.
**Jev spend this step:** $0.00 (no model calls anywhere in TASK A) · **running total:** ~$0.0046

### Pre-flight probes — three findings that change how this step is run
Probed live before writing the pull script (8 fetches total).

1. **A TIC with no notes raises `pandas.errors.EmptyDataError`; it does NOT return an empty
   table.** `TIC 1449756` → `EmptyDataError: No columns to parse from file`.
   The handoff says "a throttled or mis-parameterised call returns a well-formed empty table,
   not an error" — that is true of the *mis-parameterised* call, and the two signals are
   **distinguishable**, which the handoff did not know:

   | condition | signal |
   | :--- | :--- |
   | genuine "this TIC has no notes" | raises `EmptyDataError` |
   | mis-parameterised (positional `tag=`) | **0 rows, 7 well-formed columns** |

   Verified: `etta.download_obsnotes(156648452)` (positional → `tag`) returns 0 rows with the
   full 7-column header, while `tic=156648452` returns 3 rows.
   **Consequence:** a well-formed empty table is now treated as an **abort condition**, never
   cached. `EmptyDataError` is the genuine-empty signal and is cached without retry.

2. **`scripts/027_obsnotes_recon.py`'s `fetch()` is wrong for the full pull.** It catches bare
   `Exception` and retries 3× with backoff, so every genuinely-empty TIC — projected ~33%,
   i.e. ~850 of them — would burn 3 requests plus 3 s of sleep and then be recorded as a
   **hard failure** rather than as "no notes". Not a problem at n=30; it corrupts the coverage
   statistic at n=2,573. The new script separates the three cases.

3. **DEVIATION from the handoff, logged per §0.5 rule 4 — the bulk pull does not go through
   `etta`.** The handoff says to call `etta.download_obsnotes(tic=...)`. `etta` calls
   `pd.read_csv(url)` with **no timeout**, and `scripts/01_ingest.py` already documents that
   ExoFOP throttles *by withholding the response body* — TCP handshake completes, zero bytes
   follow, the call hangs forever with no error. Tolerable for 30 sequential calls; across
   2,573 in a thread pool it silently deadlocks the workers.
   So the pull uses `requests` with an explicit `(connect, read)` timeout against the identical
   URL `download_obsnotes.php?output=pipe&tid=<TIC>`, parsed with the same
   `pd.read_csv(..., delimiter='|')`. This is the same decision, for the same reason, that
   §01_ingest already took for the bulk TOI table. **Equivalence is verified against `etta` on
   a sample before the pull proceeds** — recorded in the DONE entry.
---
## [2026-09-20T17:34Z] TASK A — CORRECTION: my own 17:12Z pre-flight finding was BACKWARDS
**What was wrong.** The 17:12Z `STARTED` entry recorded, as finding 1, that a TIC with no notes
raises `EmptyDataError` and that a well-formed empty table is the mis-parameterised/throttle
signature. **The two are the other way round.** The handoff's original warning was right and my
"refinement" of it was wrong.

**Trigger.** The pull aborted after ~44 fetches on `TIC 14956304: 0 rows with a full 7-column
header`, which my guard treated as an abort condition. Investigating whether that was a real
throttle showed it was not.

**Measured, directly on the wire (HTTP 200 in every case):**

| TIC | bytes over 3 tries | what it is |
| :--- | :--- | :--- |
| 14956304 | `[51, 51, 51]` | **header-only, stable** — genuine "this TIC has no notes" |
| 1167538 | `[299, 299, 299]` | has notes |
| 13349647 | `[165, 165, 165]` | has notes |
| 9155187 | `[480, 0, 480]` | has notes — **and a live zero-byte throttle in the middle** |
| 1449756 | `[1195, 1195, 1195]` ×5 | has notes |

`51 bytes` is exactly `ID|TIC ID|Username|Groupname|TAG ID|Lastmod|notes\n\n`.

**The corrected mapping:**

| response | meaning | action |
| :--- | :--- | :--- |
| >= 1 data row | notes exist | cache |
| header-only (51 B, 0 rows, 7 cols) | **genuine "no notes"** | cache `[]` |
| **zero-byte body** | **throttle / transport failure** | **retry; never cache** |

`pandas.errors.EmptyDataError` is raised by the *zero-byte* case, so it is the **failure**
signal, not the no-notes signal. My 17:12Z probe saw `TIC 1449756` raise it once at 9.90 s and
concluded "no notes"; that TIC in fact returns 1,195 bytes of real notes on every one of five
subsequent tries. **One observation of a flaky endpoint was read as a semantic.**

**Damage, contained.** 3 TICs were cached as `[]` by the smoke test — `1167538`, `13349647`,
`9155187` — and **all three have notes**. `1167538` had returned 1 row in my own 17:12Z probe
and was still cached as empty minutes later. Had the full pull run to completion under the
inverted rule, every throttled response among ~2,500 fetches would have been written into the
corpus as "this TIC has no observer notes" — silently shrinking the corpus, and shrinking it
**non-randomly**, since throttling correlates with load rather than with the label only by luck.
That is precisely the failure §1.4 says must not be explainable after the fact.

**Why it aborted instead of proceeding:** the guard was wrong about *which* condition was fatal,
but having a hard stop on an unexpected response shape is what surfaced the inversion after
~44 fetches instead of after 2,503.

**Fixes now being applied:**
1. `fetch_raw`: zero-byte body -> retryable error (was: `return []`). Header-only -> `return []`
   (was: abort).
2. The 3 poisoned cache files are **deleted** so they are re-fetched.
3. Mis-parameterisation is now genuinely indistinguishable from "no notes" on the wire, so the
   **sentinel check is the only defence** and is kept: known-good TICs are re-fetched at the
   start, every 200 network fetches, and at the end.
4. `--stage verify` re-fetches every cached-empty TIC; an empty is only believed when it comes
   back header-only a second time, with sentinels passing in between. Run until it flips nothing.
5. Retries raised 4 -> 6, workers lowered 8 -> 5. The observed zero-byte rate at 8 workers was
   roughly 1 in 3 on one TIC, which is too high to leave to 4 tries.
**Jev spend this step:** $0.00 · **running total:** ~$0.0046
---
## [2026-09-20T17:52Z] TASK A — DEFECT: `pd.read_csv(delimiter='|')` mis-parses notes containing a pipe
**Found by:** the first full pull completed with `1 failed` — `TIC 70513361: ParserError:
Expected 7 fields in line 3, saw 8`. Investigating that one loud failure surfaced a second,
**silent** one.

**Cause.** A literal `|` inside note text. Two TICs of 2,573 (**0.08%**) have one. Both are
`latham` notes pasted as raw HTML e-mail, carrying Gmail thread ids of the form
`thread-f:1622534218062250498|msg-f:1622534218062250498`.

**The two failure modes are different, and the second is the dangerous one:**

| TIC | where the pipe falls | what pandas does |
| :--- | :--- | :--- |
| `70513361` | a **later** data line | column count already fixed at 7 -> `ParserError`. TIC lost, **loudly**. |
| `462715015` | the **first** data line | 9 fields vs 7 columns -> pandas infers a **2-level MultiIndex** and shifts every column left. **Silent.** |

Verified shift on `462715015`: `ID`=`'latham'`, `TIC ID`=NULL, `Username`=`'1573'`,
**`Groupname`=`'2022-09-15 11:10:57'`**, `TAG ID`=the note HTML, `Lastmod`=NULL,
**`notes`=NULL**. All 3 of that TIC's notes were corrupted; the text was moved into `TAG ID`
and the `notes` column emptied.

**What it would have done downstream.** `Groupname` became a timestamp, so the A-10 domain
assertion in the persist stage **would have fired** — and it would have reported
*"`Groupname` took a value outside {'tfopwg', NULL}; section 1.1 no longer describes what is
being selected. STOPPING."* A parser bug would have been read as a corpus-definition failure.
The assertion did its job; it just names the wrong cause. Meanwhile the `notes=NULL` rows
would have entered the observer-note arm (groupname != 'tfopwg') carrying **empty text**.

**`etta` has the identical defect** — it is the same `pd.read_csv(url, delimiter='|')` call.
Confirmed: `etta.download_obsnotes(tic=70513361)` raises the same `ParserError`. So the
handoff's prescribed acquisition path loses `70513361` outright and silently corrupts
`462715015`, and `scripts/027_obsnotes_recon.py`'s bare `except Exception` would have recorded
the former as a "hard failure" rather than as a parse defect.

**Fix.** Response parsing no longer uses pandas. `parse_pipe()` splits each line with
`split('|', 6)`; since `notes` is the **last** column it absorbs any number of literal pipes,
which is correct by construction rather than by luck. A short line (a raw newline inside a
note body) is re-attached to the previous record's `notes` instead of being padded into a junk
record the way pandas does.

**Scope check, then re-pull.** The two pandas failure modes are exhaustive — an extra-field
first line shifts (detectable: `Groupname` outside the domain, or NULL `notes`), any other
extra-field line raises. Scanning all 6,852 cached records for both signatures found exactly
these 2 TICs. The cache was nonetheless **wiped and re-pulled in full** with the new parser,
with the pandas-parsed cache kept aside, so the claim "only these 2 TICs change" is
**verified by diff rather than argued** — result in the next entry.
**Jev spend this step:** $0.00 · **running total:** ~$0.0046
---
## [2026-09-20T18:14Z] TASK A — DONE
**Result:** the observer-note corpus is acquired, asserted and persisted.

### Parser change verified by diff, not by argument
The pandas-parsed cache was kept aside and the whole corpus re-pulled with `parse_pipe`:

| | |
| :--- | ---: |
| TIC identical under both parsers | **2,571 / 2,572** |
| recovered by the new parser (was a hard `ParserError`) | 1 — `70513361` |
| silently corrupted under pandas, now correct | 1 — `462715015` |
| new cache: `Groupname` outside `{'tfopwg', NULL}` | **0** |
| new cache: records with NULL `notes` | **0** |

`462715015` before: groupnames `['2025-08-27 12:03:49', '2022-09-15 11:10:57', '2022-09-07
19:21:19']`, notes NULL on 2 of 3. After: `['tfopwg', None, None]`, no NULL notes.

### Acquisition
2,573 / 2,573 TIC fetched, **0 failures**, 5.6 min at 5 workers (~7.7 TIC/s). 6,855 notes.
10 TIC have no notes at all; all 10 re-fetched in the `verify` pass with sentinels passing
either side and came back empty a second time, so they are genuine, not throttle artifacts.

### Assertions, both from audit 01
- **A-10 `Groupname` domain holds.** Exactly two values across all 6,855 notes: `'tfopwg'`
  (2,892) and NULL (3,963). No third value. The filter is `Groupname IS NULL` in practice,
  as A-10 records, and §1.1 still describes what is being selected.
- **A-11 RFC-8259.** All 2,573 cache files are valid JSON; `null`, never bare `NaN`.

### The realised corpus — reported as measured (§1.4)
| quantity | projected §1.4 | **realised** |
| :--- | ---: | ---: |
| TOI rows | ~1,814 | **1,482** |
| unique TIC (CV groups) | ~1,715 | **1,388** |
| base rate | unknown | **0.5378** |
| median chars / row | ~780 | **896** |

**Row coverage 0.545, TIC coverage 0.539** — the recon's 67% was optimistic; the realised
figure is **54%**. TIC count is **−19.1%** against the projection and sits near the **low end
of A-8's 1,200–2,140 binomial interval**. A-8's caveat was correct and is now load-bearing:
**the A-1 dilution floor and the A-2 MDE were both measured at 1,715 TIC and are functions of
n, so both are now known to be optimistic.** TASK A2 re-measures them; nothing downstream may
use the 1,715-scale numbers.

### Selection effect — weaker than the recon estimated (A-7)
**P(has note | y=1) = 0.5822** vs **P(has note | y=0) = 0.5067**, ratio **1.149**.
The recon measured 0.80 vs 0.53 (ratio 1.51) on n=30. The collider is real but roughly a
third as strong as feared. Per §1.4 and A-7 this is **reported, not acted on** — no criterion
changes.

### Corpus integrity
**0 of 1,482 rows** contain `Master Disp:` / `Phot Disp:` / `Spec Disp:`. §1.2 measured 0/20
on the recon; it holds at full scale. The `Groupname` filter removes the disposition channel
completely. (This is not G5 — TASK B2 still owns the clause set.)

**Artifacts:** `scripts/028_obsnotes_pull.py` (new), `data/exonotes.duckdb::obsnotes_raw`,
`::obsnotes_text`, `::analysis_set_obsnotes`, `::obsnotes_coverage` (all new),
`research/data/obsnotes_corpus_2026-09-20.json` (new), `PROVENANCE.md` (obsnotes block,
manifest sha256), `data/cache/obsnotes/` 2,573 files.
**Jev spend this step:** $0.00 · **running total:** ~$0.0046
**Next:** TASK A2 — G1 on the realised row set, then re-measure the noise floor and MDE at
n = 1,482 / 1,388 TIC.
---
## [2026-09-20T18:16Z] TASK A2 — STARTED
**Doing:** (1) re-establish gate G1 on the realised obsnotes row set against the registered
criterion (B >= 0.85 AUC **and** B > A by a paired bootstrap 95% CI excluding zero);
(2) A-7's included-vs-excluded read-across; (3) re-measure the A-1 dilution floor and the A-2
MDE at the realised n, which is 19% smaller than the scale they were registered at.
**Command:** `.venv/bin/python scripts/030_gate_g1_obsnotes.py` then
`.venv/bin/python scripts/026_noise_floor.py --table analysis_set_obsnotes --groups 0 --k 8`
**Idempotent:** yes — no network, no API calls, fixed seeds, CREATE OR REPLACE output.
**Note on `--k`:** 8 is the current `TIER_PREDICTIVE` count and is **provisional**. A-2
requires this be re-run with `--k` set to the final Jev feature count once TASK B freezes the
question set. The k=8 run is the floor estimate, not the registered final one.
**Jev spend this step:** $0.00 · **running total:** ~$0.0046
---
## [2026-09-20T18:34Z] TASK A2 — DONE
**Result:** G1 re-established on the realised row set; the A-1 floor and A-2 MDE re-measured
at the true n; A-7's read-across reported.

### Gate G1 — PASS
Against the **registered** criterion, not `02_baselines.py`'s weaker one:

| arm | n | TIC | base | A | B | B−A 95% CI |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| **CORPUS (obsnotes)** | 1,482 | 1,388 | 0.5378 | 0.4840 | **0.9051** | **[+0.3977, +0.4441]** |
| full `analysis_set` | 2,721 | 2,573 | 0.5031 | 0.4847 | 0.9149 | [+0.4132, +0.4464] |
| EXCLUDED rows | 1,239 | 1,185 | 0.4617 | 0.4672 | 0.9197 | [+0.4276, +0.4764] |

**B = 0.9051 ≥ 0.85 floor, CI excludes zero → G1 PASSES** on the obsnotes row set.

### A-7 read-across — D will be compared on slightly HARDER ground
B scores **0.9051 on the included rows vs 0.9197 on the excluded** (−0.0146). The collider
runs in the *favourable* direction for honesty: the included subset is marginally harder, so
any text gain is not an artifact of D being handed easier rows. Reported, not acted on.

### The A-1 floor and A-2 MDE re-measured at n = 1,482 / 1,388 TIC
This is the re-measurement A-2 **requires**, not an optional check. The registered numbers were
taken at 1,715 TIC; the realised corpus is 19% smaller.

| quantity | registered (1,715 TIC) | **realised (1,388 TIC)** | change |
| :--- | ---: | ---: | :--- |
| B | 0.9044 | **0.9051** | ~flat |
| dilution floor ΔAUC(B+N−B) | −0.0112 | **−0.0115** | ~flat |
| bootstrap SE of ΔAUC | 0.0026 | **0.0030** | **+15%** |
| **MDE, 80% power, two-sided 95%** | +0.0073 | **+0.0084** | **+15%** |
| true signal required, net of floor | 0.0186 | **0.0199** | +7% |
| **univariate AUC bar for one Jev feature** | ~0.65 | **~0.68** | **harder** |

The dilution floor is essentially unchanged — it is a property of the model's capacity, not of
n — but **the SE grew with the smaller corpus and the detection bar moved with it.** The oracle
arm at feature AUC **0.659 is no longer detectable** (CI [−0.0009, +0.0121]); it was detectable
at the projected scale. **A question that would have cleared the old 0.65 bar no longer
clears.** `--k 8` is provisional; A-2 requires a re-run once TASK B freezes the feature count.

### Text-pipeline defects found and fixed before TASK B reads this text
Sanity-checking the persisted corpus surfaced two, neither visible on 027's 30-TIC sample:
1. **HTML entities were never decoded.** `&nbsp;` occurs **5,746 times across 1,061 of 1,482
   rows (71.6%)**. Jev would have read `&nbsp;` as literal text on most of the corpus.
2. **One unterminated tag** (`<a target="_blank"` with no closing `>`) that `<[^>]+>` cannot
   match, on TIC 164652245.
`plain()` now runs TAG_RX → FRAG_RX → `html.unescape` → collapse. **The order is load-bearing:**
running FRAG_RX first makes it consume an unquoted `href=...` and swallow the note body — that
note reduces to the empty string. FRAG_RX is restricted to real HTML tag names so it cannot eat
scientific text like `depth <1 ppt` (3 such rows verified unaffected). Entity-bearing rows
**2,029 → 0**, residual tags **1 → 0**, empty/NULL text **0**. Re-persisted; **the row set is
unchanged at 1,482 / 1,388**, so the G1 and noise-floor results above stand — both use numeric
columns only.

### Free head start for TASK B2 (measured on the full corpus, NOT registered here)
Audit 01 derived these from 20 TICs; at full scale they look different:

| probe | n (of 1,482) | P(y=1) |
| :--- | ---: | ---: |
| `TOI-\d+` | 1,013 (68.4%) | 0.431 |
| `KOI\d+` / `ExoFOP-Kepler` | 108 (7.3%) | **0.954** |
| `NEB`/`BEB` | 34 (2.3%) | **0.059** |
| `cleared` | 40 (2.7%) | 0.400 |
| `retired` | 17 (1.1%) | 0.235 |
| `false positive` | 31 (2.1%) | 0.613 |

Base rate is 0.5378. **`TOI-\d+` is the weakest of these, not the strongest** — audit 01 flagged
it on 13/20 TICs, but at full scale P(y=1)=0.431 is near base rate. The real leak is the
**Kepler-sourced** note: `ExoFOP-Kepler` at **P(y=1)=0.954 on 108 rows**. And `false positive`
at 0.613 sits *above* base rate, which is the opposite of what the phrase suggests. **TASK B2
must derive its clauses from these numbers with the §5 eye-audit — do not carry audit 01's
20-TIC shapes forward.**

**Artifacts:** `scripts/030_gate_g1_obsnotes.py` (new), `scripts/026_noise_floor.py` (`--table`),
`research/data/gate_g1_obsnotes_2026-09-20.json`,
`research/data/noise_floor_analysis_set_obsnotes_2026-09-20.json`,
`data/exonotes.duckdb::gate_g1_obsnotes`, `::noise_floor_obsnotes`.
**Jev spend this step:** $0.00 · **running total:** ~$0.0046
**Next:** register these in `PREREGISTRATION.md` §11.2, then TASK B.
---
## [2026-09-20T18:44Z] SESSION END — Claude Opus 5
**Completed:** TASK A (corpus acquisition) and TASK A2 (G1 + noise floor re-measurement), both
`DONE` above. Registered as `PREREGISTRATION.md` §11.2 amendments **A-13 … A-17**.
**Headline:** corpus is **1,482 rows / 1,388 TIC / base 0.5378** — 19% below projection. **G1
PASSES** (B = 0.9051). **The detection bar rose from ≈0.65 to ≈0.68 univariate AUC** because the
bootstrap SE grew 15% with the smaller corpus; MDE is now **+0.0084**.
**Three defects found during the work, none anticipated by audit 01:** a zero-byte body is a
throttle and not "no notes" (would have silently shrunk the corpus); `pd.read_csv(delimiter='|')`
mis-parses two TICs, one of them **silently**, via MultiIndex inference; HTML entities were never
decoded on 71.6% of rows. All three are fixed and logged at 17:34Z, 17:52Z and 18:34Z.
**Jev spend this session: $0.00 · running total: ~$0.0046.** No Jev call was made on this corpus.
**Handoff rewritten:** `HANDOFF_PROMPT.md`. **Next session starts at TASK B.**
**UNCOMMITTED:** the working tree carries all of this session's work. See the open item at the
top of `HANDOFF_PROMPT.md`; the user was asked to confirm the commit.
---
## [2026-09-20T18:52Z] COMMIT + PUSH — DONE
**Doing:** commit TASK A + A2 and publish to `origin/master`, at the user's explicit request.
**Idempotent:** n/a — a publish. Verified after the fact rather than before.

**Committed** `cfe8569` — 10 files, +1,581 / −162. `data/` and `.env` confirmed **not** staged
before committing; the 2,573 cached responses and the DuckDB tables remain local and gitignored,
so a clean clone re-pulls them (~6 min, $0).

**Pushed** `9f8f78f..cfe8569`. Two commits went up, not one: `eb4648d` (the 17:03Z open-item
correction) was already sitting unpushed from before this session, which the 17:03Z entry's
"remote and local HEAD are both 9f8f78f" no longer described by the time this session started.

**Verified after the push:**
- `git ls-remote origin master` → `cfe8569`, identical to local `HEAD`.
- `git rev-list --left-right --count origin/master...HEAD` → **0 0**. Not diverged.
- `git log origin/master --format='%an <%ae>' | sort -u` → **exactly one identity**,
  `KevinArce <iav.kevinarce@ufg.edu.sv>`. 15 commits on the branch.

**The public record now carries the A-13…A-17 registration**, which is the point: the corpus
size, the raised 0.68 detection bar and the G1 result are timestamped in public **before** TASK B
writes a question and before any full-corpus Jev call. Jev spend unchanged at **~$0.0046**.
**Next:** TASK B, per `HANDOFF_PROMPT.md`.
---
## [2026-09-20T18:58Z] SESSION START — Claude Opus 5
**Resumption:** last entry is the 18:52Z `COMMIT + PUSH — DONE`, `Next:` = TASK B. No orphan
`STARTED`. Nothing interrupted.
**Read before acting:** `WORKLOG.md` tail from 17:05Z, `PREREGISTRATION.md` §11.2 (A-13…A-17)
then §11.1 (A-1…A-8) and §2/§5, `AUDIT_01_PREFLIGHT_REVIEW.md`, `PLAN.md` §0.5 + §1,
`research/05_question_design_gate.md`, `src/exonotes/questions.py`,
`scripts/025_question_gate.py`.

**Handoff open item is already closed — no action needed.** `HANDOFF_PROMPT.md` still carries a
🚩 OPEN ITEM saying TASK A/A2 are "complete but UNCOMMITTED". They were committed at 18:52Z
(`cfe8569`) and pushed. Verified now: `git status` clean, `git log` carries `cfe8569` and
`4e4983c`. The handoff text is stale on this point; the 18:52Z entry is authoritative.

**Discrepancy recorded — `HANDOFF_PROMPT.md` cites an amendment "A-9" that does not exist.**
The handoff's TASK B constraint reads "**Blind the cases (A-9)**". `PREREGISTRATION.md` §11.1
runs A-1 … A-8 and §11.2 runs A-13 … A-17; there is no A-9 … A-12 in the registration. The
blinding requirement is real but is recorded in `WORKLOG.md` 16:—Z audit block ("Question-gate
cases must be **label-blinded** in TASK B; the r4 cases carried `y=`") and in
`AUDIT_01_PREFLIGHT_REVIEW.md`, **not** as a registered amendment. It is binding regardless of
its number, is followed here, and is registered properly in §11.3 as part of this task rather
than left as a dangling reference.

**State verified read-only before starting:**
- `analysis_set_obsnotes` = **1,482 rows / 1,388 TIC / base 0.5378**, matching A-13.
- Length distribution of `notes`, measured now: min 20 · p10 205 · p25 386 · **p50 870** ·
  p75 1,266 · p90 2,121 · **p95 3,261** · p99 11,391 · **max 41,268** · total 1,898,624 chars.
- DuckDB tables present: `analysis_set`, `analysis_set_obsnotes`, `baseline_results`,
  `baseline_summary`, `gate_g1_obsnotes`, `ingest_provenance`, `ingest_stats`, `noise_floor`,
  `noise_floor_obsnotes`, `obsnotes_coverage`, `obsnotes_raw`, `obsnotes_text`, `toi_snapshot`.

**Live TypeSafe docs read this session** (per project memory, which directs the `typesafe-ai`
skill + live docs): `concepts/state`, `primitives/noul`, `primitives/score`,
`primitives/advanced`, `api`, `models`, `model-jaggedness/jev-1.13`. Three things bind TASK B:
1. **`criteria: {true, false}` is the documented Noul field** for stating the negative case,
   which §2.4 rule 2 requires. It also accepts **structured** values (`{what, examples}`), and
   `instructions` accepts `{question, inspect, focus}`. Both are documented, not invented.
2. **Context limits:** 64k tokens per request, **32k for `state` plus the longest question**.
   The 41,268-char max row is ~10.3k tokens, so it fits — **truncation is not forced by the
   API limit.** The handoff's "truncate or the tripwire will fire" is a cost concern, not a
   hard limit, and the cost re-projection is what settles it.
3. **`jev-1.13` documents accuracy loss on large states carrying irrelevant detail** — named
   "context rot" on the jaggedness page. Our p95 row is 3,261 chars and the max is 41,268, and
   a long row is many notes concatenated across years, most of them irrelevant to any one
   question. **This is a first-class risk to TASK B and C and must be measured on long cases,
   not assumed away.** The gate case set is therefore stratified to over-sample the long tail.
**Picking up:** TASK B — re-run Step 2.5 on observer-note text.
**Jev spend this step:** $0.00 · **running total:** ~$0.0046
---
## [2026-09-20T19:02Z] TASK B — STARTED
**Doing:** re-run Step 2.5 (the question-design gate) against **real observer-note text**, as
`PREREGISTRATION.md` §2 requires as a binding precondition of Step 3, and re-freeze the set
under a new `QUESTION_SET_VERSION`.
**Method:** same as `scripts/025_question_gate.py` — ~20–25 cases drawn **verbatim** from
`analysis_set_obsnotes.notes`, each question's positive / negative / nearest confusable, every
answer inspected by eye.
**Binding constraints being applied** (handoff + §11.1/§11.2):
- Candidate features are judged against the **≈0.68** univariate-AUC bar of **A-15**, not 0.65.
- Cases are **label-blinded**: sampled programmatically across the length distribution, `y`
  withheld from the case file and from my expectations until every answer is inspected.
- **Model pinned** `MODEL = "jev-1.13.0"` (A-5), with `response["model"]` asserted before persist.
- **State is `{"notes": ...}`** (A-4). No `toi`.
- The two questions deleted on `Comments` (§2.3) are **restored as candidates**.
- Every added column costs ~**0.0115** of dilution (A-15), so a question that cannot plausibly
  clear 0.68 does not earn a column.
**Command:** `.venv/bin/python scripts/031_question_gate_obsnotes.py`
**Idempotent:** yes — responses cached content-addressed on
`sha256(MODEL + QUESTION_SET_VERSION + state + questions)` under `data/cache/gate_obsnotes/`.
A re-run costs $0. Bumping `QUESTION_SET_VERSION` is what forces a real re-test.
**Jev spend this step:** $0.00 so far · **running total:** ~$0.0046
---
## [2026-09-20T19:14Z] TASK B — PHASE 1 FINDING: the §2.1 question set has almost no support in this corpus
**What this is.** The $0 prevalence check that `research/05` §4 ran on `Comments` before spending
anything, repeated on the obsnotes corpus. It is the cheapest decision-relevant measurement
available and it changes what TASK B should write. **No Jev call was made.**

### The corpus is a different genre from `Comments`
`Comments` was TFOP vetting shorthand (`TFOP FP; retired as NEB`). Observer notes are dominated
by **reconnaissance-spectroscopy and speckle-imaging reports**: a machine-written header block
(`T0<TIC>, RA DEC, V=…, PM=…, J-K=…, Period=… TOI-…,Rp=…` then `<date> TRES, pha=…, RV=…,
Teff=…, log(g)=…, Vrot=…, ccf=…, SNRe=…`) followed by one or two human sentences that carry the
actual judgment — *"The first TRES observation reveals a late F dwarf"*, *"the velocity offset
is out of phase with the inner planet — this pretty much rules out a stellar or brown dwarf
companion"*, *"No secondary sources were detected"*, *"No more TRES recon spectra are needed."*
The header block is **repeated verbatim once per appended note**, so a long row is mostly
duplicated boilerplate. `latham` alone wrote 2,138 of the 3,963 observer notes across 1,040 TIC.

### Subject-matter prevalence and the univariate AUC ceiling
For a binary feature, `AUC = 0.5 + (P(fires|y=1) − P(fires|y=0))/2` exactly. Measured on all
1,482 rows (797 pos / 685 neg, base 0.5378), with deliberately over-broad regexes:

| subject matter | n | % | P(y=1) | AUC | \|AUC\| |
| :--- | ---: | ---: | ---: | ---: | ---: |
| TRES recon boilerplate | 954 | 64.4% | 0.433 | 0.364 | **0.636** |
| follow-up concluded ("no more … needed") | 819 | 55.3% | 0.436 | 0.387 | **0.613** |
| speckle / "no secondary sources" | 412 | 27.8% | 0.738 | 0.612 | **0.612** |
| giant / evolved host | 365 | 24.6% | 0.356 | 0.410 | 0.590 |
| KOI / ExoFOP-Kepler | 108 | 7.3% | 0.954 | 0.561 | 0.561 |
| DACE / CORALIE / HARPS | 119 | 8.0% | 0.849 | 0.550 | 0.550 |
| confirmed / validated | 105 | 7.1% | 0.867 | 0.547 | 0.547 |
| spectroscopic binary (SB1/SB2/SEB) | 70 | 4.7% | 0.114 | 0.460 | 0.540 |
| RV variation / offset | 642 | 43.3% | 0.492 | 0.460 | 0.540 |
| **offset EB (NEB/BEB)** | 60 | 4.0% | 0.083 | 0.463 | 0.537 |
| ephemeris problem | 184 | 12.4% | 0.402 | 0.466 | 0.534 |
| companion / blend | 471 | 31.8% | 0.495 | 0.472 | 0.528 |
| **transit morphology** | 47 | 3.2% | 0.340 | 0.487 | 0.513 |
| retired / rejected | 53 | 3.6% | 0.472 | 0.495 | 0.505 |
| on-target detection | 21 | 1.4% | 0.381 | 0.496 | 0.504 |
| **instrumental artifact** | 23 | 1.6% | 0.652 | 0.504 | 0.504 |

**Not one probe clears the A-15 bar of ≈0.68.** The best is 0.636.

### Five of the eight `TIER_PREDICTIVE` questions are near-dead here
`reports_offset_eclipsing_binary` (4.0% of rows), `mentions_spectroscopic_binary` (4.7%),
`describes_transit_morphology` (3.2%), `mentions_instrumental_artifact` (**1.6%**) and
`asserts_ephemeris_problem` (12.4%, AUC 0.534) have essentially no support. §2.3 deleted two
questions from the `Comments` set for exactly this — *"a feature that is constant across 99.6% of
rows costs tokens on every call and contributes nothing"* — and the same rule now applies to
these. `mentions_instrumental_artifact` at **23 rows of 1,482** is in the same position
`indicates_followup_complete` was in on `Comments`.

### The strongest signals in this corpus are PROVENANCE, not content — and B+meta already has them
The top three probes all answer *"which follow-up group wrote a note here?"*, not *"what does the
note say?"*. Measured directly, with grouped 5-fold OOF:

| metadata-only feature | AUC | \|AUC\| |
| :--- | ---: | ---: |
| `n_authors` | 0.609 | 0.609 |
| notes by `latham` (TRES recon) | 0.401 | 0.599 |
| notes by `everett` (speckle) | 0.586 | 0.586 |
| `n_notes_obs` | 0.571 | 0.571 |
| `n_chars` | 0.504 | 0.504 |
| **all six together, grouped 5-fold OOF** | | **0.6817** |

**A model with no text content at all reaches 0.6817 AUC — the same 0.68 a single Jev feature
must clear to be visible.** A-7 added the **B+meta** arm on the suspicion that `evidence_depth`
was a semantic proxy for note count; that suspicion is now **measured and much stronger than
when it was registered.** This is the decisive design constraint for TASK B:

> **A question earns a column only if its judgment is NOT recoverable from who wrote the note,
> how many notes there are, and how long they are.** A noul that effectively detects "a speckle
> imager reported here" is `n_everett` with extra steps, and will be absorbed by B+meta.

### What this does NOT mean
A regex is a tight proxy for a fixed token (`NEB`, `SB1`) and a **loose** one for a judgment
("the host is evolved, so the depth implies a stellar companion"; "the RV conclusion rules out a
stellar companion"). Jev can beat the token where the judgment is semantic and the token is not,
which is where the remaining candidates are drawn from. These ceilings bound the **subject
matter's** prevalence, not Jev's accuracy on it.
**Jev spend this step:** $0.00 · **running total:** ~$0.0046
**Next:** build the label-blinded case set, then write the r5 candidate questions against these
findings.
---
## [2026-09-20T19:41Z] TASK B — ROUND r5 RESULT: 212/221, and the failures are diagnostic
**Command:** `.venv/bin/python scripts/032_question_gate_obsnotes.py`
**Artifacts:** `scripts/031_gate_cases_obsnotes.py` (blinded sampler),
`scripts/032_question_gate_obsnotes.py`, `src/exonotes/questions.py` (`2026-09-20.r5`),
`research/data/gate_cases_obsnotes_2026-09-20.json`,
`research/data/gate_obsnotes_2026-09-20.r5_2026-09-20.json`,
`data/cache/gate_obsnotes/` (27 responses).
**Result:** **212/221 assertions passed · 9 FAILED · 12 mid-band nouls.**
**27 new API calls · 113,948 input tokens · $0.00479** · running total **~$0.0094**.
Model assertion held: every response reported `jev-1.13.0` (A-5).
Cases are label-blinded — `--unblind` has **not** been run; `y` has not been looked at.

### The glued-negation hypothesis is REFUTED
19:31Z flagged that ExoFOP's raw HTML glues the imaging negation to the previous token on 129
rows (`…acquired at 832nmNo secondary sources were detected.`) and predicted it might flip the
judgment. **It does not.** Measured on the matched pair the sampler drew on purpose:

| case | boilerplate form | length | `imaging_reports_no_companion` |
| :--- | :--- | ---: | ---: |
| B27 | **run-together** (`832nmNo`) | 1,189 | **0.71** |
| B23 | **run-together** | 1,150 | **0.78** |
| B09 | **run-together** | 1,122 | **0.77** |
| B18 | **clean, spaced** | 372 | **0.65** ← fails |
| B01 | **run-together** | 255 | **0.56** ← fails |
| B02 | **run-together** | 256 | **0.58** ← fails |

The clean short case scores **lower** than three run-together long ones. The glue is not the
variable; **length is** — and in the *opposite* direction to the context-rot risk logged at
18:58Z. The question fails on short notes that contain **nothing but** the imaging boilerplate
(0.56 / 0.58 / 0.65) and succeeds once that same boilerplate sits inside a longer note
(0.71 – 0.97 across B07, B09, B10, B11, B12, B13, B21, B23, B24, B27). **No text-normalisation
fix is warranted; A-17 needs no further amendment on this point.**

### Diagnosis: a negative clause cancelling its own positive — the SAME failure as r3
`research/05` §5 recorded it once already: `mentions_instrumental_artifact` said *"answer no if
the text only reports low SNR"*, met a case that had both, and landed at 0.69. My r5 instruction
carries two exclusions — *"answer no if the text only says that imaging was taken"* and *"saying
that a limiting magnitude or a plot is available is not a finding"* — and in a standalone
imaging note **those two clauses describe most of the text**. The finding sentence is one of four;
the other three are the things I told the model not to count. So it splits. In a longer note the
excluded material is a small fraction and the finding dominates. **The exclusion must be scoped:
it applies only when no finding is reported at all.**

### The other eight failures, each with its cause
| case | question | got | want | cause |
| :--- | :--- | ---: | :---: | :--- |
| B19 | `spectroscopy_indicates_nonplanetary_companion` | 0.09 | Y | **The instruction never expands `NEB`.** The text says only *"SG1 indicates there is an NEB"*. This is exactly `research/05` §2: *the corpus speaks in abbreviations, so the question has to as well.* |
| B11 | `spectroscopy_consistent_with_planet` | 0.38 | Y | Cues list *"rules out a brown dwarf"* but not *"rules out … an eccentric eclipsing binary"*. An EB **is** a stellar companion; the cue list has a real gap. |
| B08 | `spectroscopy_consistent_with_planet` | 0.64 | Y | Planetary nature established by published RV follow-up, phrased as a paper abstract rather than as a recon conclusion. |
| B22 | `indicates_retired_or_rejected` | 0.35 | N | Model infers *planetary companion ruled out → rejected*. A multi-hop inference to be **named and forbidden** (§2.4 rule 3). |
| B17 | `imaging_reports_companion_present` | 0.42 | N | A companion inferred from **radial velocities**, with no imaging in the note at all, is leaking into an imaging question. |
| B13 | `indicates_confirmed_planet` | 0.61 | Y | 17,836 chars; the phrase *"I thought this published planet would be a good check"* is genuinely incidental. **Accepted, not reworded** — see below. |
| B01/B02/B18 | `imaging_reports_no_companion` | 0.56/0.58/0.65 | Y | the scoped-exclusion defect above. |

### What already works, and will not be touched
- **`host_star_described_as_evolved` is the cleanest question in the set.** Positives 0.81–0.99
  (B04, B05, B12, B17, B19, B20, B22), negatives 0.03–0.08, **zero mid-band**. It passed both
  traps it was built against: B08's *"giant extrasolar planets"* (giant describes the **planet**)
  scored **0.08**, and B26's `log(g)=2.00` header was correctly ignored at **0.08**.
- **`followup_reported_concluded`**: positives 0.93–0.98, negatives 0.03–0.24, zero mid-band.
- **`spectroscopy_indicates_nonplanetary_companion`** away from B19: 0.77–0.97 positive,
  0.03–0.17 negative.

### `reports_on_target_detection` is DELETED, on the evidence it was restored to produce
§2.3 restored it as a candidate because `Comments` lacked support and obsnotes might not.
**Measured: 1.4% of rows carry the subject matter, and across all 27 cases the question never
once returned a clear positive** — its whole range is 0.03–0.64, with four cases in the mid-band
(B11 0.50, B14 0.64, B24 0.42, B17 0.36). That is the definition of a near-0.5 noise column
under §2.4 rule 6, and it would cost ~0.0115 of A-15 dilution to carry. **Deleted for the same
reason it was deleted on `Comments`, now measured on this corpus rather than assumed.**

### Decision rule fixed BEFORE r6 runs, as `research/05` §3.1 requires
r6 is the **second** wording of these five questions. §2.4 rule 4 says delete rather than reword
a third time. Committed now, before the r6 call:
> **If `imaging_reports_no_companion` does not reach ≥ 0.70 on B01, B02 and B18 in r6, the
> question is deleted, not reworded.** Same rule for `spectroscopy_indicates_nonplanetary_companion`
> on B19, and for `indicates_retired_or_rejected` on B22.
> **B13's `indicates_confirmed_planet` 0.61 is accepted as a boundary case and NOT rewritten** —
> rewriting to clear one incidental phrase inside a 17.8k-char note is fitting the question to
> this 27-case set, which is the overfitting the pre-registration exists to prevent.
**Jev spend this step:** $0.00479 · **running total:** ~$0.0094
**Next:** apply the five scoped fixes, bump to r6, re-run (cache makes unchanged questions free).
---
## [2026-09-20T19:58Z] TASK B — ROUND r6 RESULT: 219/221, all five decision-rule cases PASS
**Command:** `.venv/bin/python scripts/032_question_gate_obsnotes.py`
**Result:** **219/221 assertions passed · 2 FAILED · 3 mid-band nouls** (was 12 in r5).
**27 new API calls · 119,051 input tokens · $0.00500** · running total **~$0.0144**.
Every response reported `jev-1.13.0`; the A-5 assertion held on all 27.

### The rule fixed before r6 ran, judged on r6's numbers
| case | question | r5 | **r6** | required | verdict |
| :--- | :--- | ---: | ---: | :--- | :--- |
| B01 | `imaging_reports_no_companion` | 0.56 | **0.80** | ≥ 0.70 | **PASS** |
| B02 | `imaging_reports_no_companion` | 0.58 | **0.77** | ≥ 0.70 | **PASS** |
| B18 | `imaging_reports_no_companion` | 0.65 | **0.86** | ≥ 0.70 | **PASS** |
| B19 | `spectroscopy_indicates_nonplanetary_companion` | 0.09 | **0.84** | ≥ 0.70 | **PASS** |
| B22 | `indicates_retired_or_rejected` | 0.35 | **0.07** | ≤ 0.30 | **PASS** |

No question reaches a third wording, so §2.4 rule 4 is not triggered.

### What each repair did
1. **Scoping the imaging exclusion** ("those sentences are not findings, but they do not count
   *against* one either") lifted every standalone imaging note over the bar and also raised the
   embedded ones: B07 0.82→0.90, B09 0.77→0.88, B10 0.84→0.91, B11 0.87→0.95, B24 0.97→0.97.
   **The same repair that fixed the failures improved the cases that already passed**, which is
   what distinguishes a real fix from fitting to the failing case.
2. **Expanding `NEB`/`BEB` inside the instruction**: B19 0.09 → **0.84**. This is the third time
   this project has paid for the same lesson (`research/05` §2): **the corpus speaks in
   abbreviations, so the question has to as well.**
3. **Naming "ruled out → rejected" and forbidding it**: B22 `indicates_retired_or_rejected`
   0.35 → **0.07**. §2.4 rule 3 again, and again it worked where describing the positive better
   would not have.
4. **Naming "RV companion → a star was seen"**: B17 `imaging_reports_companion_present`
   0.42 → **0.07**, with the four genuine imaging detections unmoved (B14 0.99, B15 0.98,
   B16 0.95, B19 0.96).
5. **Adding "rules out an eclipsing binary" to the planet-side cues**: B11 0.38 → **0.81**,
   B08 0.64 → **0.83**.

### The two residual failures, accepted rather than reworded
- **B13 `indicates_confirmed_planet` 0.61 → 0.56.** Accepted in advance by the rule fixed at
  19:41Z. The phrase is *"I thought this published planet would be a good check for the RV
  analysis"*, incidental, inside 17,836 characters.
- **B10 `spectroscopy_consistent_with_planet` 0.22 → 0.35.** A **regression introduced by fix 5**
  — broadening the planet-side cues pulled up a note whose only statement is *"a small velocity
  shift that is consistent with the photometric ephemeris"*, with no companion-mass conclusion.
  Caught only because every case is re-tested every round, exactly as in `research/05` §5.
  **Accepted at 2/221 rather than reworded a third time**, per §2.4 rule 4 and the r4 precedent.
- B25 `spectroscopy_consistent_with_planet` 0.31 is unasserted but sits just above the band.

### Context rot: measured, and smaller than feared
18:58Z flagged jev-1.13's documented accuracy loss on large states. Across the three long cases
the questions mostly hold: B14 (10,945 ch) `imaging_reports_companion_present` **0.99** and
`imaging_reports_no_companion` **0.02**; B15 (12,119 ch) **0.98 / 0.21**; B13 (17,836 ch)
`imaging_reports_no_companion` **0.97**. The one soft spot is B13's incidental `published`
phrase at 0.56. **Long states are not disqualifying for this question set**, and B15's 0.21 on
`imaging_reports_no_companion` — a note that contains both a clean-imaging sentence and a
`3.36" companion` report — is the correct reading of a genuinely mixed note, not a failure.

### Unblinding — done only now, after every answer above was inspected
`scripts/031_gate_cases_obsnotes.py --unblind`. The 27 cases are **16 positive / 11 negative**
(0.59 vs the 0.5378 corpus base rate), so the blinded sampler did not draw a degenerate set.
**Reported, not acted on.** No question was kept, dropped, or reworded on the basis of these
labels, and no wording changed after this command was run. 27 cases cannot estimate an AUC, and
selecting questions by their correlation with `y` on 27 rows is precisely the overfitting the
pre-registration exists to prevent. Recorded for the audit trail only.

### The frozen set
`QUESTION_SET_VERSION = "2026-09-20.r6"` — **7 `TIER_PREDICTIVE` + 3 `TIER_LABEL_ECHO` = 10**:
`imaging_reports_no_companion`, `imaging_reports_companion_present`,
`spectroscopy_indicates_nonplanetary_companion`, `spectroscopy_consistent_with_planet`,
`host_star_described_as_evolved`, `followup_reported_concluded`, `author_certainty` (Score);
`indicates_retired_or_rejected`, `indicates_confirmed_planet`, `contains_object_designation`.
**k = 7 for the headline model D**, down from the provisional 8 the A-15 noise floor assumed.

**Noted for TASK C, not acted on:** `contains_object_designation` returns ≥ 0.90 on 26 of 27
cases (the exception is B03, which carries no designation at all). It is close to a constant
column. It is `TIER_LABEL_ECHO`, so it never enters the headline; it exists to detect the §2.0
leakage channel, and a near-constant high value is consistent with that channel being present
almost everywhere in this corpus. A-8 item 11's low-variance exemption for G3 may apply to it.
**Jev spend this step:** $0.00500 · **running total:** ~$0.0144
**Next:** re-run the A-2/A-15 noise floor at the frozen k = 7, re-project the TASK C cost from
the realised length distribution, then register §11.3.
---
## [2026-09-20T20:09Z] TASK B — DONE
**Result:** Step 2.5 is re-run on real observer-note text and the question set is re-frozen at
**`2026-09-20.r6`**, discharging `PREREGISTRATION.md` §2's binding precondition on Step 3.

| | |
| :--- | :--- |
| frozen set | **7 `TIER_PREDICTIVE` + 3 `TIER_LABEL_ECHO` = 10** (was 8 + 3 = 11) |
| gate | **219/221 assertions on 27 label-blinded real notes**, 3 mid-band |
| rounds | r5 (212/221, 12 mid-band) → r6. **No question reached a third wording.** |
| k for model D | **7** (was provisionally 8) |
| dilution floor / MDE at k=7 | **−0.0105 / +0.0082**; bar unchanged at **≈0.68** |
| TASK C projection | **$0.2434**, tripwire $0.50 **does not fire**; **no truncation** |
| Jev spend | 54 calls, 233k input tokens, **$0.00979** this task |

**Registered as `PREREGISTRATION.md` §11.3, amendments A-18 … A-23.** §2's warning box is
marked discharged and now points at §11.3, which supersedes the §2.1/§2.2 tables.

### The three things a later reader most needs from this task
1. **The corpus does not contain the study §2 was designed around.** Six of the eight r4
   predictive questions were retired on measured prevalence — `mentions_instrumental_artifact`
   had **23 supporting rows out of 1,482**. `Comments` was TFOP vetting shorthand; observer
   notes are reconnaissance-spectroscopy and speckle-imaging reports. The questions were
   rebuilt around what is actually here (A-19).
2. **Metadata alone scores 0.6817 AUC — the same bar a Jev feature must clear.** The strongest
   signals in this corpus are provenance (which group wrote a note), not content, and A-7's
   B+meta arm holds all of it. Every r6 question is written to be unanswerable from author,
   note count, or length, and `evidence_depth` was retired for failing that test (A-23).
3. **A null is the registered expectation, not a surprise.** No content probe in this corpus
   clears 0.68 by regex; the best is 0.643. That is written down **before** any feature exists
   (A-23), next to §8.1's standing commitment to publish a null.

### Corrections to earlier entries in this session, recorded rather than edited
- **19:31Z was wrong about the run-together text mattering.** I predicted the glued negation
  (`832nmNo secondary sources were detected`, 129 rows) might flip the imaging judgment. It does
  not: the clean short case B18 scored **lower** (0.65) than three glued long ones (0.71–0.78).
  Length drove it, not the glue, and the repair was to the instruction, not to the text. **No
  amendment to A-17 was warranted and none was made.**
- **19:14Z's worry that long states would be the problem was also wrong in direction.** The
  failures were on the **shortest** cases (255/256/372 chars), because my own exclusion clause
  described most of a standalone imaging note. jev-1.13 held up on 10.9k and 12.1k-char states
  (0.99 and 0.98 on the imaging question).
- My sampler's first T04 regex matched `No secondary sources were **detected**` and drew a
  duplicate rather than a companion-detection case. Fixed in
  `scripts/031_gate_cases_obsnotes.py` with a comment recording why the obvious regex is wrong.

**Artifacts:** `src/exonotes/questions.py` (r6), `scripts/031_gate_cases_obsnotes.py` (new),
`scripts/032_question_gate_obsnotes.py` (new),
`research/data/gate_cases_obsnotes_2026-09-20.json` (new),
`research/data/gate_obsnotes_2026-09-20.r5_2026-09-20.json` +
`…r6_2026-09-20.json` (new), `research/data/noise_floor_analysis_set_obsnotes_2026-09-20.json`
(re-measured at k=7), `duckdb::noise_floor_obsnotes` (k=7),
`PREREGISTRATION.md` §11.3 + §2 discharge note, `data/cache/gate_obsnotes/` (54 responses).
**Jev spend this step:** $0.00500 · **running total:** ~$0.0144
**Next:** TASK B2 — re-derive the G5 clause set on observer-note text ($0 Jev), register it in
§11 before TASK C. The binding order is B and B2 → C.
---
## [2026-09-20T20:26Z] TASK B2 — STARTED / DONE
**Doing:** re-derive the G5 clause set on observer-note text, as **A-3** requires, measure n
and P(y=1) per clause exactly as §5 does, audit the marginal rows by eye, and register the
result in §11 **before** TASK C.
**Command:** `.venv/bin/python scripts/033_leakage_obsnotes.py`
**Idempotent:** yes — read-only against the corpus, `CREATE OR REPLACE` on its own tables.
**Jev spend this step:** **$0.00** — this is a regex measurement, no API calls.

### A-3 confirmed by measurement: the `Comments` clause set is inoperative here
Run as-is on the 1,482 obsnotes rows, `L2` fires on **0**, `L4b` on **0**, `L4a` on **1**,
`L1` on 17. Only `L3` does real work (101 rows). Whole set: **118 rows (8.0%)**, against
**368 (24.8%)** for the set derived here. L4a/L4b are anchored to a comment that *is* a
designation — an observer note never is.

### The registered set: 10 clauses, three of them new
`OBSNOTES_PATTERNS` in `src/exonotes/leakage.py`. Full table in `PREREGISTRATION.md` §11.4.
**G5 arm = 1,114 rows · 1,043 TIC · base 0.426** (stripped 368 rows at P(y=1)=0.875).

| new clause | n | % | P(y=1) | what it catches |
| :--- | ---: | ---: | ---: | :--- |
| `L6_archive_provenance` | 231 | 15.6% | **0.948** | `Extracted KOI178 observing note from ExoFOP-Kepler` |
| `L7_structured_disposition_field` | 136 | 9.2% | 0.941 | `Possible planetary candidate = Yes` — the Kepler/K2 analogue of `Master Disp:` |
| `L8_status_line` | 97 | 6.5% | 0.866 | `Status: Solved by ESPRESSO-GTO (Sozzetti et al. 2021)` |
| `L9_disposition_transition` | 11 | 0.7% | 0.364 | `PC => NEB`, `VPC -> VPC+` |

### The §5 eye audit, on the rows each clause strips ALONE
- **`L1` (10 marginal): clean.** All genuine — *"Retired as an NEB"*, *"Retired as a False
  Alarm (FA)"*, *"retired as a false positive due to a nearby eclipsing binaries"*.
- **`L9` (4): clean.** All genuine transitions.
- **`L3` (19): clean, with a known over-strip** — *"Data will be published in Lillo-Box et al.
  (2014) in prep"* is future tense and not a confirmation. Safe direction per §5.
- **`L8` (53): MIXED, and recorded as such.** Most carry the verdict, but some carry only an
  observation — *"Status: No significant RV variation (RMS 4.4 m/s …), SB2 ruled out"*. L8
  over-strips those.
- **`L6` (82): carry NO disposition statement at all.** They read *"Extracted KOI178 observing
  note from ExoFOP-Kepler on 2020-11-02 Lick Recon: …"* and then ordinary observation.

### `L1_retired` is not the one-directional marker it was on `Comments`
P(y=1) = **0.235** here against **0.006** there, because observer notes record positive
transitions too: *"VPC -> VPC+ (and retired from SG1)"*, *"PC->CPC (and retired from SG1)"*.
Still a disposition echo, still stripped — but the asymmetry that made it look like a pure
negative marker on `Comments` does not exist here.

### The one judgment call, registered with both arms
`L6` strips on **provenance**, not on a disposition statement, so it is not "label echo" in
§2.0's sense. It is stripped because the provenance string alone predicts the label at
**0.948**, which is the effect G5 exists to rule out whatever its form; §5's standing
over-stripping rule decides it. **Both arms are registered before any result is seen** (A-25):

| arm | rows | TIC | base |
| :--- | ---: | ---: | ---: |
| **G5 registered (with L6)** | **1,114** | **1,043** | **0.426** |
| sensitivity (without L6) | 1,196 | 1,122 | 0.463 |

**A G5 verdict that flips between the two will be reported as flipping**, not settled after the
fact by choosing the arm with the nicer answer.

### Audit 01's `false positive` reading is now measured and is wrong
`false positive` fires on 31 rows at **P(y=1) = 0.613 — above the 0.5378 base rate.** In
observer notes the phrase is usually speculation (*"I wouldn't be surprised if this is a false
positive"*), not a disposition. **Not stripped.** `NEB`/`BEB` (34 rows, 0.059) and *"is an
eclipsing binary"* (17 rows, 0.059) are also **not stripped**: they are observational findings
and are exactly what model D is meant to be reading. Recorded in A-26 so the choice is visible.

### Tripwire
`L5_explicit_disposition` fires on **0 of 1,482** rows — the `Groupname` filter removes the
disposition channel completely, as §1.2 and A-13 record. **Now enforced in code:**
`scripts/033_leakage_obsnotes.py` raises and refuses to write its output if L5 ever fires,
saying in the message that this is a pipeline bug and not a finding, and that Step 3 stops.

**Registered as `PREREGISTRATION.md` §11.4, amendments A-24 … A-27.**
**Artifacts:** `src/exonotes/leakage.py` (rewritten: `OBSNOTES_PATTERNS` + `COMMENTS_PATTERNS`
kept for provenance), `scripts/033_leakage_obsnotes.py` (new),
`research/data/leakage_obsnotes_2026-09-20.json` (new), `duckdb::leakage_obsnotes`,
`duckdb::g5_arm_obsnotes` (new).
**Jev spend this step:** $0.00 · **running total:** ~$0.0144
**Next:** TASK C — Step 3, the full run. Projected **$0.2434** (A-21), tripwire $0.50.
Both preconditions are now discharged: B is `DONE` at 20:09Z, B2 is `DONE` here.
---
## [2026-09-20T20:44Z] TASK C / STEP 3 — STARTED
**Doing:** compute the Jev feature matrix over the full obsnotes corpus — one request per row,
all 10 r6 questions per request, bounded concurrency, content-addressed cache, full raw
response JSON persisted. `PLAN.md` §6 Step 3.
**Command:** `.venv/bin/python scripts/034_step3_features.py`
**Idempotent:** yes — every response cached on
`sha256(model + question_set_version + state + questions)` under `data/cache/step3/`. A re-run
makes no API calls and returns byte-identical results. **An interrupted run is safe to resume
and costs nothing for the rows already done.**
**Preconditions, both discharged:** TASK B `DONE` 20:09Z (§11.3 A-18…A-23), TASK B2 `DONE`
20:26Z (§11.4 A-24…A-27). Committed and pushed as `4198379`; `origin/master` verified identical
and not diverged **before** this run, so the criteria are public before the number exists.

**Cost tripwire evaluated BEFORE any call was made:**
| | |
| :--- | ---: |
| rows | 1,482 |
| **distinct states** | **1,382** (dedup saves 100 calls — the state is per-TIC text) |
| projected input tokens | 5,402,832 |
| **projected cost** | **$0.2269** |
| §6 tripwire | $0.50 — **not fired** |

The projection is slightly under A-21's $0.2434 because A-21 costed all 1,482 rows; 100 of them
share a TIC's text with another row and hash to the same cache key.

**DEVIATION from the handoff, logged per §0.5 rule 4.** The handoff specifies an *async client*
with a bounded semaphore. `aiohttp` and `httpx` are **not installed**, and `requirements.txt` is
part of this project's reproduction contract — the CI clean-clone check (side quest 01) installs
exactly it. Adding a dependency mid-study to change how a loop is scheduled is not worth
breaking that. `ThreadPoolExecutor(max_workers=8)` over the same blocking `urllib` transport
that `scripts/025` and `032` already use gives the **identical bounded-concurrency guarantee**;
8 workers sits far below the documented 1,200 requests/minute limit, and the retry path honours
`retry-after` when the response carries one.
**Jev spend this step:** $0.00 so far · **running total:** ~$0.0144
---
## [2026-09-20T20:56Z] TASK C / STEP 3 — DONE
**Result:** the Jev feature matrix over the full obsnotes corpus is computed and persisted.

| | |
| :--- | ---: |
| rows | **1,482** |
| features | **10** (7 predictive + 3 label-echo) + `author_certainty__conf` |
| new API calls | **1,462** · cache hits 20 · **failures 0** |
| input tokens | **5,763,547** |
| **cost** | **$0.2421** (projected $0.2269) |
| wall clock | **427 s** at 8 workers |
| nulls in the matrix | **0** |

Every response asserted `model == "jev-1.13.0"` before being cached (A-5). All 1,482 rows
persisted to `duckdb::jev_features_obsnotes`; full raw JSON for all 1,482 states is in
`data/cache/step3/` (content-addressed, so a re-run costs **$0.00** and is byte-identical).

### Small defect, recorded: a cache race made 80 redundant calls
The corpus has **1,382 distinct states** (100 rows share a TIC's text with another row), so a
perfect run makes 1,382 calls. It made **1,462** — 80 more. Cause: the cache is checked at the
top of `call()` and written at the bottom, so two workers holding the same state can both miss
and both call. **Cost of the race: ~$0.013.** Correctness is unaffected — both writes go to the
same content-addressed path and the second simply overwrites the first — and every subsequent
run is served from cache and is deterministic. Not worth a re-run to fix; recorded so the
1,462-vs-1,382 discrepancy is not mistaken later for a coverage problem. A keyed lock around
the miss path would remove it.

### Feature matrix sanity, before any gate is evaluated
| feature | mean | std |
| :--- | ---: | ---: |
| `imaging_reports_no_companion` | 0.264 | 0.367 |
| `imaging_reports_companion_present` | 0.150 | 0.265 |
| `spectroscopy_indicates_nonplanetary_companion` | 0.214 | 0.310 |
| `spectroscopy_consistent_with_planet` | 0.239 | 0.274 |
| `host_star_described_as_evolved` | 0.268 | 0.377 |
| `followup_reported_concluded` | 0.554 | 0.453 |
| `author_certainty` (0–4) | 2.738 | 0.773 |
| `indicates_retired_or_rejected` | 0.074 | 0.142 |
| `indicates_confirmed_planet` | 0.141 | 0.243 |
| `contains_object_designation` | **0.929** | **0.191** |

`contains_object_designation` is near-constant at full scale, exactly as the 20:09Z entry
predicted from 26 of 27 gate cases. It is `TIER_LABEL_ECHO`, never in the headline, and A-8
item 11's low-variance exemption is expected to apply to it at G3.
**Jev spend this step:** $0.2421 · **running total:** **~$0.2565**
**Next:** evaluate G2, G4, G5, G6 (`scripts/035_gates_g2_g6.py`, $0), then G3
(`scripts/036_gate_g3_stability.py`, ~200 extra calls).
---
## [2026-09-20T21:06Z] TASK C — GATES G2, G4, G5, G6: ALL PASS. The registered prior was WRONG.
**Command:** `.venv/bin/python scripts/035_gates_g2_g6.py` · **Jev spend: $0.00** (no API calls)
**Artifacts:** `scripts/035_gates_g2_g6.py` (new), `research/data/gates_g2_g6_2026-09-20.json`.

n = 1,482 · TIC = 1,388 · base 0.5378 · S1 GroupKFold(5)×3 · paired bootstrap 10,000 over TIC
groups · A-6 aggregation throughout. **B = 0.9044.**

| arm | AUC | ΔAUC vs B | 95% CI | verdict |
| :--- | ---: | ---: | :--- | :--- |
| **B+N** (A-1 dilution floor) | 0.8971 | **−0.0073** | [−0.0133, −0.0014] | as registered |
| **B+meta** (A-7 control) | 0.9256 | **+0.0212** | [+0.0132, +0.0293] | metadata *does* add |
| **D — THE HEADLINE (G2)** | **0.9483** | **+0.0440** | **[+0.0332, +0.0554]** | **G2 PASS** |
| **D vs B+meta** | 0.9483 | **+0.0228** | [+0.0133, +0.0329] | **survives A-23's control** |
| E (contaminated upper bound) | 0.9523 | +0.0479 | [+0.0367, +0.0596] | as expected, ≈ D |
| **G5 registered (with L6)** | 0.9323 | **+0.0394** | [+0.0272, +0.0523] | **G5 PASS** · n=1,114 base 0.426 |
| **G5 sensitivity (no L6)** | 0.9341 | **+0.0421** | [+0.0303, +0.0547] | **does not flip** · n=1,196 base 0.463 |
| **G6 (+missingness)** | 0.9472 | **+0.0425** | [+0.0316, +0.0540] | **G6 PASS** |
| **G4 (S2 temporal)** | 0.9136 | **+0.0927** | [+0.0608, +0.1264] | **G4 PASS** · train 1,070 / test 390 |
| C (TF-IDF on raw text) | **0.8766** | — | — | **BELOW B** |

**ΔAUC +0.0440 against an MDE of +0.0082 and a dilution floor of −0.0105 (A-20).** The effect
is ~5× the MDE and the CI is nowhere near zero.

### A-23's registered prior was wrong, and here is exactly why
I registered, before the run, that *"not one content probe clears 0.68"* and that a null was the
expected outcome. **Four of the seven predictive features clear it:**

| feature | regex proxy \|AUC\| (A-23) | **Jev \|AUC\|** | gain |
| :--- | ---: | ---: | ---: |
| `spectroscopy_indicates_nonplanetary_companion` | 0.586 | **0.748** | **+0.162** |
| `spectroscopy_consistent_with_planet` | 0.509 | **0.705** | **+0.196** |
| `host_star_described_as_evolved` | 0.590 | **0.696** | +0.106 |
| `imaging_reports_no_companion` | 0.643 | **0.687** | +0.044 |
| `followup_reported_concluded` | 0.613 | 0.648 | +0.035 |
| `imaging_reports_companion_present` | 0.528 | 0.637 | +0.109 |
| `author_certainty` | — | 0.578 | — |

**The error was in the estimator, not the reasoning.** A-23 bounded the signal with regex
proxies and said so explicitly — *"a regex is a tight proxy for a fixed token and a loose one
for a judgment … Jev can beat the token where the judgment is semantic."* That caveat is
exactly what happened, and it is larger than I allowed for: **the semantic judgment beats the
token by 0.10–0.20 AUC on the two spectroscopic questions.** The prior was stated in the right
place, in advance, and is now falsified in public. That is the system working.

### The three things that make this result harder to dismiss
1. **It survives the metadata control.** A-23's specific worry was that the "signal" is really
   *which group wrote a note*. **B+meta does reach 0.9256 — metadata alone adds +0.0212** — but
   **D still beats B+meta by +0.0228 with a CI excluding zero.** The prose adds beyond
   provenance.
2. **It survives leakage stripping, in both arms.** G5 = +0.0394 with L6, +0.0421 without.
   **The verdict does not flip between the two arms**, which A-25 committed to reporting either
   way.
3. **Baseline C is 0.8766 — BELOW B (0.9044).** On `Comments`, C was 0.9691 and was pure label
   echo. Here, raw text alone is *weaker than the numerics*, so there is no readable label lying
   in the text — yet Jev's structured judgments over that same text add +0.0440. **Whatever D is
   using, TF-IDF cannot find it.** That is the opposite of the leakage signature.

### DEFECT FOUND: `jev-1.13.0` is NOT run-to-run deterministic
Checking end-to-end row alignment by comparing the 27 r6 gate answers against the Step 3 matrix
— identical pinned model, identical state, identical questions, two separate calls — **60 of
162 compared values differ.** Measured across all 10 features on those 27 cases (scores
rescaled to 0–1):

| | |
| :--- | ---: |
| identical values | **169 / 270 (62.6%)** |
| **mean \|Δ\|** | **0.0049** |
| \|Δ\| ≤ 0.02 | 94.4% |
| \|Δ\| ≤ 0.05 | 99.3% |
| **max \|Δ\|** | **0.100** |

**Consequences, none of which change a gate verdict:**
- **The alignment check still passes.** Every value agrees to ~0.01 and the large ones move
  together (TOI 2151.01: gate 0.79/0.98/0.06, matrix 0.78/0.98/0.07). Rows are correctly joined;
  a misalignment would destroy signal, not create it.
- **Mean \|Δ\| 0.0049 is an order of magnitude below G3's 0.05 criterion**, so run-to-run noise
  cannot by itself fail G3 — but it is **not zero**, and G3 was registered without a control for
  it. **G3 is therefore being run with an added same-wording repeat arm** so the paraphrase
  effect is measured against this noise floor rather than against an assumed zero.
- **`PLAN.md` §0.5's claim that re-running a judging step "returns byte-identical results" is
  true only from a WARM cache.** From a cold cache Step 3 would return slightly different
  features and a slightly different ΔAUC. The cache is what makes this study reproducible, and
  `data/` is gitignored, so **a clean clone does not reproduce the headline number exactly.**
  This needs to be said plainly in `PROVENANCE.md` and `README.md` and is registered in §11.5.
**Jev spend this step:** $0.00 · **running total:** ~$0.2565
**Next:** G3 with the repeat control arm, then register §11.5.
---
## [2026-09-20T21:28Z] TASK C — GATE G3: PASS on TIER_PREDICTIVE (7/7)
**Command:** `.venv/bin/python scripts/036_gate_g3_stability.py`
**Artifacts:** `scripts/036_gate_g3_stability.py` (new),
`research/data/gate_g3_stability_2026-09-20.json`, `data/cache/g3/`.
**394 genuinely new API calls · 1,513,280 input tokens · $0.0636** · running total **~$0.3201**.

200 rows sampled with a fixed seed. Registered criterion: **Spearman ρ ≥ 0.85 per feature AND
mean |Δp| ≤ 0.05**, with A-8 item 11's exemption for a feature whose IQR is below one
quantisation step (0.01).

| feature | tier | ρ (para) | mean\|Δp\| | IQR | ρ (repeat) | mean\|Δp\| (repeat) | |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `imaging_reports_no_companion` | pred | 0.884 | 0.0456 | 0.475 | 0.997 | 0.0001 | ok |
| `imaging_reports_companion_present` | pred | 0.888 | 0.0158 | 0.030 | 1.000 | 0.0000 | ok |
| `spectroscopy_indicates_nonplanetary_companion` | pred | 0.949 | 0.0196 | 0.092 | 0.999 | 0.0001 | ok |
| `spectroscopy_consistent_with_planet` | pred | 0.948 | 0.0309 | 0.200 | 1.000 | 0.0002 | ok |
| `host_star_described_as_evolved` | pred | 0.964 | 0.0130 | 0.100 | 1.000 | 0.0000 | ok |
| `followup_reported_concluded` | pred | 0.960 | 0.0128 | 0.940 | 1.000 | 0.0000 | ok |
| `author_certainty` | pred | 0.992 | 0.0135 | 0.268 | 1.000 | 0.0001 | ok |
| `indicates_retired_or_rejected` | **echo** | **0.812** | 0.0096 | 0.010 | 0.996 | 0.0001 | **FAIL** |
| `indicates_confirmed_planet` | echo | 0.939 | 0.0189 | 0.050 | 0.999 | 0.0000 | ok |
| `contains_object_designation` | **echo** | **0.814** | **0.0626** | 0.010 | 1.000 | 0.0000 | **FAIL** |

**G3 VERDICT: PASS.** All 7 `TIER_PREDICTIVE` features clear both halves of the criterion, and
§7 puts only those in the headline.

### The two failures are label-echo, and they are reported, not excused
- `contains_object_designation` fails **both** halves (ρ 0.814, mean |Δp| 0.0626). It is the
  near-constant column — mean 0.929 across the corpus — so this is a genuine instability, not
  a tie artefact.
- `indicates_retired_or_rejected` fails only ρ; its mean |Δp| is 0.0096, five times inside the bar.
- **Both have IQR exactly 0.010, so A-8 item 11's exemption ("below one quantisation step")
  misses on a strict reading of *below*.** Relaxing `<` to `<=` after seeing the numbers would
  convert both to passes. **I have not done that.** The threshold stands as registered and the
  failures are reported as failures. Neither feature enters the headline.

### G3(b) is vacuous, and that is registered rather than skipped
§6 asks for a **permuted state key order**. A-4 removed `toi`, so the registered state is
`{"notes": ...}` — **one key, nothing to permute.** §6 was written when the state had two keys.
The script asserts the state has exactly one key, so if an amendment ever re-introduces a second
one this stops being vacuous and the assertion fires.

## [2026-09-20T21:31Z] CORRECTION to the 21:06Z entry — the nondeterminism is TIME-dependent, not per-request
**What 21:06Z said.** *"`jev-1.13.0` is NOT run-to-run deterministic … mean |Δ| 0.0049."*
That measurement is real, but the label I put on it was too broad, and the G3 repeat arm shows why.

**What is actually true.** Two identical requests behave very differently depending on *when*:

| comparison | gap | mean \|Δ\| | ρ |
| :--- | :--- | ---: | ---: |
| r6 gate vs Step 3 (27 cases, 270 values) | **~1 hour** | **0.0049** | — |
| G3 repeat arm vs Step 3 (200 rows, 10 features) | **minutes** | **0.0001** | 0.996–1.000 |

**The payloads really were identical in both comparisons** — verified, not assumed: the
`gate_obsnotes` and `step3` cache directories **share 27 key strings**, and a key is
`sha256(model + version + state + questions)`, so the same key means the same bytes were sent.
The case-file text and the DuckDB text are also byte-identical for every case checked.

So within a session Jev is **effectively deterministic** (mean |Δ| 0.0001, 412× smaller than the
paraphrase effect); across about an hour it drifts slightly. That is consistent with server-side
variation — a serving fleet, batching, or a rolling deployment — rather than per-request sampling.

**What this changes, and what it does not.**
- **G3 is unaffected and is strengthened**: the paraphrase effect (mean |Δp| 0.0242) is **412×**
  the within-session noise, so it is measuring wording, not jitter.
- **The reproducibility caveat in the 21:06Z entry still stands**, and this is the sharper
  statement of it: **a clean clone re-running Step 3 from a cold cache will not reproduce the
  headline ΔAUC exactly.** `data/` is gitignored, so the cache is not in the repo. The numbers
  are reproducible *from the cache*, which is a weaker claim than `PLAN.md` §0.5's
  "byte-identical", and `PROVENANCE.md`/`README.md` must say so. Registered in §11.5.
- No gate verdict moves. The smallest CI distance from zero across G2–G6 is G5's +0.0272, which
  is far outside anything a 0.005 feature perturbation could reach.

### Two self-inflicted defects found and fixed during G3, recorded so they are not repeated
1. **The first repeat arm measured nothing.** `call_variant` patched `s3.QUESTIONS`/`s3._QJSON`
   but not `s3.CACHE`, so `s3.call` looked the repeat payload up in the **Step 3** cache
   directory — where, being byte-identical, it hit — and returned the cached Step 3 response.
   The arm reported a perfect ρ = 1.000 / Δ = 0.0000 **because it never made a call.** A
   too-good-to-be-true number is what exposed it. Fixed by redirecting `s3.CACHE`; the stale
   outer entries were invalidated by bumping the salt to `r6-repeat2`, since the second run was
   still being served from the first run's outer cache.
2. **That same bug wrote 197 paraphrase responses into `data/cache/step3/`**, inflating it to
   1,579 files. Verified before touching anything: **all 1,382 legitimate Step 3 keys present,
   0 missing, 197 extra, and all 197 extras byte-identical to a file already in
   `data/cache/g3/`.** They were **moved** to `data/cache/g3_inner_paraphrase/`, not deleted, so
   nothing is lost. `data/cache/step3/` is now exactly **1,382** files = the distinct-state count.
**Jev spend this step:** $0.0636 · **running total:** ~$0.3201
**Next:** register TASK C in `PREREGISTRATION.md` §11.5.
---
## [2026-09-20T21:36Z] TASK C — DONE
**Result:** Step 3 is complete and **all five gates pass.**

| | |
| :--- | :--- |
| **headline (§7)** | **ΔAUC(D − B) = +0.0440, 95% CI [+0.0332, +0.0554]** |
| vs registered MDE | **5.4×** the +0.0082 of A-20 |
| G2 / G3 / G4 / G5 / G6 | **PASS / PASS / PASS / PASS / PASS** |
| D vs B+meta | +0.0228 [+0.0133, +0.0329] — survives A-23's control |
| G5 sensitivity | +0.0394 with L6, +0.0421 without — **verdict does not flip** |
| baseline C (TF-IDF) | **0.8766, below B's 0.9044** |
| Jev spend | **~$0.3201** cumulative |

**Registered as `PREREGISTRATION.md` §11.5, A-28 … A-32.** That section is explicitly marked as
written **after** the result; every criterion it is judged against was committed and pushed as
`4198379` **before** `scripts/034_step3_features.py` made its first call.

### What was NOT done, stated plainly
- **S2b was not applied.** §4's note-level `Lastmod` filter needs every training row's features
  recomputed on time-filtered text — a second full-corpus run. **G4 is the S2 + S2a result**,
  and A-28 says so rather than leaving it implicit.
- **`RESULTS.md` is not written.** §9's definition of done calls for it; this session produced
  the numbers and the registration, not the write-up.
- **G3's two label-echo failures were not explained away.** `contains_object_designation` fails
  both halves of the criterion. Relaxing A-8 item 11's `<` to `<=` would have cleared both; it
  was not done (A-32).

**Artifacts:** `scripts/034_step3_features.py`, `scripts/035_gates_g2_g6.py`,
`scripts/036_gate_g3_stability.py` (all new), `duckdb::jev_features_obsnotes`,
`research/data/step3_features_2026-09-20.json`, `research/data/gates_g2_g6_2026-09-20.json`,
`research/data/gate_g3_stability_2026-09-20.json`, `data/cache/step3/` (1,382),
`data/cache/g3/`, `PREREGISTRATION.md` §11.5, `PROVENANCE.md` (step3 block + the cold-cache
caveat), `README.md` (headline reproduction steps + the same caveat).
**Jev spend this step:** $0.00 · **running total:** ~$0.3201
**Next:** `RESULTS.md` per §9, and S2b if the corpus is re-run.
---
## [2026-09-20T21:42Z] SESSION END — Claude Opus 5
**Completed:** TASK B (20:09Z), TASK B2 (20:26Z) and TASK C (21:36Z) — the full scope the
handoff set for this session, in the binding order B and B2 → C.

**Headline:** **ΔAUC(D − B) = +0.0440, 95% CI [+0.0332, +0.0554]** — 5.4× the registered MDE.
**All five gates pass: G2, G3, G4, G5, G6.** §9's definition of done is now items 1–6 and 8;
**only item 7, `RESULTS.md`, remains.**

**Registered:** `PREREGISTRATION.md` §11.3 (A-18…A-23), §11.4 (A-24…A-27), §11.5 (A-28…A-32).
§11.3 and §11.4 were committed and pushed as `4198379` **before** the first full-corpus call,
so every criterion the result is judged against is timestamped in public ahead of the number.

**The honest headline about the headline:** A-23 registered, in advance, that a null was
expected. **That prior was falsified.** A-29 records why — the regex proxies I bounded the
signal with understated the semantic judgment by 0.10–0.20 AUC. Reported rather than dropped.

**Defects found this session, all logged and fixed:**
- The `Comments` G5 clause set is inoperative on obsnotes (`L2`/`L4b`/`L5` fire on 0 rows).
- Six of eight r4 predictive questions had near-zero corpus support.
- `jev-1.13.0` drifts over time — byte-identical requests differ by 0.0049 at an hour, 0.0001
  at minutes. `PLAN.md` §0.5's "byte-identical" claim holds only from a warm cache.
- My own G3 repeat arm measured nothing (never made a call) and reported a perfect score.
- My own sampler regex matched a negation and drew a duplicate case.
- 197 stray files in `data/cache/step3/`, verified and moved rather than deleted.

**Two prior claims of mine corrected in-session, by new entries rather than edits:** the 19:31Z
prediction that the glued negation would matter (it does not), and the 21:06Z framing of the
nondeterminism as per-request (it is time-dependent).

**Jev spend this session: $0.3057 · running total: ~$0.3201.**
**Committed and pushed:** `4198379` (TASK B + B2) and `d23d32d` (TASK C). `origin/master`
verified identical to local `HEAD`, not diverged, single commit identity.
**Handoff rewritten:** `HANDOFF_PROMPT.md`. **Next session starts at TASK D — `RESULTS.md`.**
---
## [2026-09-20T21:01Z] SESSION START — Claude Opus 5
**Inherited state:** TASK A/A2/B/B2/C complete; all five gates pass; registered as
`PREREGISTRATION.md` §11.5 (A-28…A-32). Last commit `de1336b`, working tree clean,
`origin/master` in sync. **Jev spend to date: ~$0.3201.**
**Resumption check (§0.5):** last entry `[2026-09-20T21:42Z] SESSION END` — a clean close, no
orphan `STARTED`, `Next:` field reads *"`RESULTS.md` per §9, and S2b if the corpus is re-run."*
**Scope this session:** TASK D (`RESULTS.md`, §9 item 7 — the last open item) and TASK E (S2b)
if the budget allows.
---
## [2026-09-20T21:03Z] TASK D — STARTED
**Doing:** §9 item 7 — `RESULTS.md`, *"whatever the answer is — with reliability diagrams and
CIs."* Two parts: (1) a new script producing reliability diagrams for baselines B and D from
their S1 out-of-fold CatBoost probabilities, (2) the write-up itself.
**Command:** `scripts/037_reliability.py` (new), then `RESULTS.md`.
**Idempotent:** yes — the script makes no API call and no network call, reuses the S1
construction and CatBoost config imported from `scripts/026_noise_floor.py`, and overwrites
its own outputs.
**Guardrail check:** `PLAN.md` §1 forbids thresholding on Jev's `confidence`. These diagrams
calibrate **CatBoost's** `predict_proba`, which is a different object and is not a guardrail
concern. No Jev probability is thresholded, plotted as a decision, or used as a conclusion.
**Jev spend this step:** $0.00 (projected) · **running total:** ~$0.3201
---
## [2026-09-20T21:14Z] TASK D — reliability diagrams produced
**Command:** `.venv/bin/python scripts/037_reliability.py` · **Artifacts:**
`scripts/037_reliability.py` (new), `assets/reliability_b_d.png`, `assets/gate_forest.png`,
`research/data/reliability_2026-09-20.json`. **0 API calls · $0.00.**

Fits B and D through the **same** `nf.oof_by_repeat` and the **same** DuckDB query as
`scripts/035_gates_g2_g6.py`, so the plotted probabilities are the ones that produced the gate
verdicts — confirmed: B 0.9044 and D 0.9483 reproduce `gates_g2_g6_2026-09-20.json` exactly.

| | B (numeric) | D (numeric + Jev) |
| :--- | ---: | ---: |
| AUC | 0.9044 | **0.9483** |
| Brier (mean over 3 repeats) | 0.1210 [0.1195–0.1231] | **0.0881** [0.0859–0.0895] |
| ECE, 10 equal-width bins | 0.0263 [0.0240–0.0295] | 0.0232 [0.0226–0.0237] |
| MCE | 0.0835 | 0.0929 |
| rows in the two extreme bins | 737 (49.7%) | **995 (67.1%)** |

**The gain is sharpness, not calibration.** ECE barely moves (0.0263 → 0.0232) while Brier
falls 27%. D is not better calibrated; it is more *decisive* — it pushes 258 more rows into
p<0.1 or p>0.9 and is right about them. D's MCE is slightly **worse** than B's, on the
44-row 0.5–0.6 bin. Reported rather than rounded away.

**Aggregation choice, stated because it is a choice.** Each row has one OOF prediction per S1
repeat and the three are correlated, not independent. Brier/ECE/MCE are therefore computed
per repeat and reported as mean [min–max]; the plotted curve pools all three repeats but its
Wilson intervals use **n_eff = count / 3**, the independent row count, rather than the pooled
count, which would claim 3× the precision the data has.

### DEFECT EXPLAINED (not a new defect): the repo contains two values of B
`030_gate_g1_obsnotes.py` reports **B = 0.9051**, `035_gates_g2_g6.py` reports **B = 0.9044**,
on the same 1,482 rows. This script fits both orderings and reproduces both numbers exactly:
the only difference is that 035 reads the rows `order by a.toi` for the feature join.
**Same rows, same folds, same seed, same config — CatBoost is sensitive to input row order,
worth 0.0008 AUC here.** That is ~10× below the MDE of 0.0082 and moves no verdict, but it is
now measured rather than unexplained, and `RESULTS.md` says which number belongs to which arm.
**Jev spend this step:** $0.00 · **running total:** ~$0.3201
**Next:** write `RESULTS.md`.
---
## [2026-09-20T21:26Z] TASK D — drift sensitivity arm — STARTED
**Doing:** A-31 and `PROVENANCE.md` both assert *"no gate verdict is at risk"* from the
`jev-1.13.0` time drift, and both argue it rather than measure it — the phrase used is "orders
of magnitude beyond what a 0.005 feature perturbation could move", which is an estimate, not a
result. While drafting `RESULTS.md` §8 I declined to repeat it unmeasured. The gates were
never re-run on a cold cache, so the sensitivity of ΔAUC to a drift-sized feature perturbation
is **unmeasured**. It is cheap to measure: perturb the 7 `TIER_PREDICTIVE` columns by the
measured drift magnitude (mean |Δ| = 0.0049 at ~1 hour), re-fit D, recompute G2, repeat over
seeds.
**Command:** `scripts/038_drift_sensitivity.py` (new).
**Idempotent:** yes — no network, no API calls, fixed seeds, JSON overwritten in place.
**This is a new arm, not a registered one.** It is a robustness check on a claim this session
is about to publish, reported as such. It changes no criterion and no gate verdict.
**Jev spend this step:** $0.00 (projected) · **running total:** ~$0.3201
---
## [2026-09-20T21:34Z] TASK D — drift sensitivity arm — DONE
**Command:** `.venv/bin/python scripts/038_drift_sensitivity.py` and `--drift 0.049 --seeds 10`
**Artifacts:** `scripts/038_drift_sensitivity.py` (new),
`research/data/drift_sensitivity_x1_2026-09-20.json`,
`research/data/drift_sensitivity_x10_2026-09-20.json`. **0 API calls · $0.00.**

**A-31's "no gate verdict is at risk" is now measured rather than argued.**

| simulated drift | realised mean \|Δ\| | draws | ΔAUC mean ± sd | worst | worst 95% CI | G2 |
| :--- | ---: | ---: | :--- | ---: | :--- | :--- |
| **1× measured (0.0049)** | 0.0042 | 20 | **+0.0444 ± 0.0010** | +0.0417 | [+0.0308, +0.0530] | **PASS** |
| **10× measured (0.0490)** | 0.0385 | 10 | +0.0402 ± 0.0015 | +0.0384 | [+0.0280, +0.0495] | **PASS** |

Reference (unperturbed) is +0.0440, reproduced exactly from the gate run. At the measured drift
the worst of 20 draws shifts ΔAUC by **−0.0023**, about a quarter of the MDE. **At 10× the
measured drift G2 still passes.**

**Stated limits of the arm, in the script docstring and in `RESULTS.md` §8:** it is **not** a
cold-cache re-run — real drift is whatever the serving fleet does and may be correlated across
rows, where this perturbs every row independently — and it is **not** a registered gate. The
realised perturbation also lands ~14% below target at 1× because re-quantising to 0.01 rounds
small perturbations back to zero, making the arm marginally weaker than the drift it simulates.
The 10× row exists to cover that gap rather than to argue it away.

**Output naming fixed mid-step:** the first two runs both wrote
`drift_sensitivity_2026-09-20.json` and the 10× run overwrote the 1× result. The filename now
carries the drift multiple and both runs were re-run to restore both artifacts. No data lost —
caught before the entry was written.
**Jev spend this step:** $0.00 · **running total:** ~$0.3201
**Next:** finish `RESULTS.md`, then commit TASK D.
---
## [2026-09-20T21:47Z] TASK D — DONE
**Result:** `RESULTS.md` is written. **§9's definition of done is now items 1–8 complete.**

**Artifacts:** `RESULTS.md` (new), `scripts/037_reliability.py` (new),
`scripts/038_drift_sensitivity.py` (new), `assets/reliability_b_d.png`,
`assets/gate_forest.png`, `research/data/reliability_2026-09-20.json`,
`research/data/drift_sensitivity_x1_2026-09-20.json`,
`research/data/drift_sensitivity_x10_2026-09-20.json`, `PREREGISTRATION.md` §11.6
(A-33…A-36), `PROVENANCE.md`, `README.md`. **0 API calls this task · $0.00.**

`RESULTS.md` carries, as the handoff and §7 require: the one headline number with its CI and
all four §7 companions (E−B contaminated, baseline C as leakage, the G5 arm, S2 with its
base-rate shift stated); reliability diagrams for B and D; **A-29's falsified prior in full**;
A-31's reproducibility limit in `PROVENANCE.md`'s terms; **A-32's two G3 failures reported as
failures**; §10's limitations; and the one-corpus/one-archive/one-model-version bound.

### Three measurements this write-up needed that did not exist
1. **The calibration numbers themselves.** B Brier 0.1210 → D **0.0881** (−27%), but ECE barely
   moves (0.0263 → 0.0232). **The gain is sharpness, not calibration** — D pushes 258 more rows
   into p<0.1 or p>0.9 and is right about them. D's **MCE is worse** than B's (0.0929 vs
   0.0835); reported, not rounded away.
2. **The drift sensitivity arm** (21:34Z) — A-31's "no verdict at risk" is now measured.
3. **The two values of B** (21:14Z) — row-order sensitivity, 0.0008 AUC.

### Two corrections to committed documents, both made as additions, not rewrites
- **`PREREGISTRATION.md` §10 item 2's note-count medians do not describe this corpus.** Measured
  here: medians are **2 vs 2**, not 3 vs 2; the effect is in the tail (mean 3.44 vs 2.15,
  univariate AUC 0.571) and **number of authors is the stronger channel at 0.609**. The
  prohibition is unaffected. Registered as A-34, and flagged inside `RESULTS.md` §10 item 2
  rather than silently restated.
- **`README.md`'s status block was stale and the repo is public.** It still read *"Nothing in
  this repository yet answers the headline question"* and *"Spend ~$0.0002"*, three commits
  after all six gates passed. Rewritten to the result, with the caveats attached.

### Defect found: a `PROVENANCE.md` marker claims automation that does not exist
`<!-- BEGIN step3 (scripts/034_step3_features.py) -->` implies that script regenerates the
block, as `028_obsnotes_pull.py` genuinely does for the obsnotes block. **It does not** —
`grep 'BEGIN step3' scripts/` returns nothing. A cold re-run of 034 would leave those numbers
stale while looking machine-maintained. Marker corrected to say it is hand-maintained.

**§9 item 7 called for "reliability diagrams"; `PLAN.md` §9 separately asks for PER-QUESTION
ones.** Those are **not** produced and `RESULTS.md` §9 says so with the reason: the per-question
judgments have no independent ground truth, and the only hand-labelled set is 27 cases — far
too few for calibration bins. Plotting them against the *disposition* label would measure
something else. Registered as A-36.
**Jev spend this step:** $0.00 · **running total:** ~$0.3201
**Next:** commit TASK D, then assess TASK E (S2b) against the budget.
---
## [2026-09-20T21:58Z] TASK E — S2b — STARTED
**Doing:** §4's registered S2b — for the S2 **training** side only, include a note iff its
`Lastmod` < the 2021-10-28 cutoff — so G4 becomes the registered split rather than the
approximation A-28 reports.
**Command:** `scripts/039_gate_g4_s2b.py` (new).
**Idempotent:** yes — content-addressed cache, fixed seeds, CREATE OR REPLACE output. A re-run
costs $0.

**Dry measurement first, $0 spent (the handoff projected ~$0.18):**

| quantity | value |
| :--- | ---: |
| observer notes with `Lastmod` < cutoff | **2,865 of 3,963 (72.3%)** |
| S2 training rows | 1,070 |
| — text unchanged (cache hit, free) | **669** |
| — text changes | **401** |
| — text becomes **empty**, row leaves the corpus | **186** |
| — rows needing a new call | 215, over **203 distinct states** |
| **projected cost** | **$0.0332** |

**~5× cheaper than the handoff projected**, because 669 of 1,070 training rows have every note
already before the cutoff and 186 more lose all of their text, so neither group needs a call.
`Lastmod` is non-null on **all 6,855 notes**, so the undated-note case does not arise here.

**Four design decisions, fixed before the run:**
1. **A row whose text becomes empty leaves the training set.** §1.1 defines the corpus as rows
   with ≥1 observer note of non-zero length; under S2b, 186 training rows no longer qualify.
   Training drops 1,070 → **884**. This is §4's own "tests on *less* text, not on *older*
   text", made concrete.
2. **B and D both train on those same 884 rows.** If B kept all 1,070 while D lost 186, ΔAUC
   would conflate the text filter with a sample-size change. **B on the full 1,070 is also
   reported**, so the sample-size component is visible rather than buried.
3. **The test side is untouched** — the same 390 rows as A-28's G4, so G4 and G4b are directly
   comparable. Shrinking the training set can only shrink the train-TIC set, so the S2a
   group-leak fix stays valid on a fixed test set; re-running S2a would only *add* test rows
   back. Holding it fixed is the conservative direction.
4. **New responses are cached in `data/cache/s2b/`, not `data/cache/step3/`.** Step 3's
   directory is exactly 1,382 files = its distinct-state count, and `PROVENANCE.md` commits to
   that number. The script checks `step3/` for a legitimate hit first (identical request → free)
   and only ever *writes* to `s2b/`. This is the 21:31Z bug inverted: that one wrote paraphrase
   responses into `step3/` because `s3.CACHE` was not patched. Here it is patched on purpose.
**Jev spend this step:** $0.00 so far · **projected $0.0332** · **running total:** ~$0.3201
---
## [2026-09-20T22:09Z] TASK E — S2b — DONE. G4 is now the registered split, and it PASSES
**Command:** `.venv/bin/python scripts/039_gate_g4_s2b.py`
**Artifacts:** `scripts/039_gate_g4_s2b.py` (new), `research/data/gate_g4_s2b_2026-09-20.json`,
`duckdb::jev_features_obsnotes_s2b`, `data/cache/s2b/` (203 responses).
**203 new API calls · 804,981 input tokens · $0.0338** · running total **~$0.3539**.

**Actual cost $0.0338 against the $0.0332 projection** — 1.8% over, and **~5× below** the
handoff's ~$0.18 estimate.

| arm | train | B | D | ΔAUC | 95% CI | |
| :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| **G4 — S2+S2a, as published** | 1,070 | 0.8209 | 0.9136 | +0.0927 | [+0.0608, +0.1264] | reproduced exactly |
| **G4b — S2+S2a+S2b, REGISTERED** | 884 | 0.8039 | **0.9250** | **+0.1211** | **[+0.0869, +0.1578]** | **PASS** |
| G4c — 884 rows, unfiltered text | 884 | 0.8039 | 0.9115 | +0.1076 | [+0.0755, +0.1423] | not a gate |

Test side unchanged throughout: **390 rows, base 0.6487**. Train base 0.4888 → **0.4514**.

### The gain does not collapse under S2b — it grows, and the growth decomposes cleanly
G4c exists precisely so the two effects are not confounded, and they separate:

- **G4 → G4c, dropping the 186 emptied rows:** B falls **0.8209 → 0.8039 (−0.0170)**, D falls
  only **0.9136 → 0.9115 (−0.0021)**. ΔAUC rises **because the numeric baseline suffers more
  from the smaller training set than the text-enriched model does**, not because D improved.
- **G4c → G4b, the text filter itself:** B is **identical** (same rows, same numeric columns),
  so the whole move is D, **0.9115 → 0.9250**.

### That second step was tested directly, because the two CIs overlap heavily
Reading +0.0135 off two overlapping intervals would not establish it. Paired bootstrap on the
same 390 test rows, B identical in both arms so the ΔAUC difference **is** D(S2b) − D(full):

> **+0.0135, 95% CI [+0.0006, +0.0269] — excludes zero, but barely.**

**It is reported as marginal and it is not a gate.** The lower bound is +0.0006; this is a
post-hoc comparison on 390 test rows that no section registered in advance. **The claim that
survives is the weaker one: training D on time-filtered text does not degrade it.** The
stronger reading — that older-only training text actively helps — is suggestive and not
established here.

### Four pre-fixed decisions held; the cache separation was verified, not assumed
`data/cache/step3/` is **still exactly 1,382 files** and `data/cache/s2b/` holds **203** —
checked after the run. `PROVENANCE.md`'s committed distinct-state count is intact. The 21:31Z
defect (paraphrase responses leaking into `step3/` because `s3.CACHE` was not patched) did not
recur, because the patch was made deliberately this time and the step3 lookup is read-only.

### A note on what S2b does and does not control
`Lastmod` is **last-modified, not created** (§10 item 1). A 2019 note edited in 2023 is dropped
by the 2021 cutoff, so **S2b tests on *less* text, not on *older* text** — §4 says this and it
remains the honest description. 2,865 of 3,963 observer notes (72.3%) survive.
**Jev spend this step:** $0.0338 · **running total:** ~$0.3539
**Next:** fold G4b into `RESULTS.md`, register as §11.6, update `PROVENANCE.md`.
---
## [2026-09-20T22:18Z] TASK E — registered and folded into the write-up
**Artifacts:** `PREREGISTRATION.md` §11.7 (A-37), `RESULTS.md` §6a (new section) plus the §1
S2 companion row, the §2 gate table, §9 item 1 and §11's falsifier list, `PROVENANCE.md`
(new `s2b` block), `README.md` (spend, caveats, reproduce block). **0 API calls · $0.00.**

**§7's S2 companion is now the registered split:** +0.1211 [+0.0869, +0.1578], with the
pre-S2b +0.0927 kept beside it rather than replaced. **§9's item 1 — "S2b was not applied" —
is struck**, and §11's last open falsifier ("S2b, once applied, collapsing the G4 gain. Not
yet tested") is closed: it did not.

**The `research/data/gate_g4_s2b_*.json` cost fields were made self-describing.** The first
persisted copy came from a *cached* re-run and read `new_calls: 0, usd: 0.0` — true of that
run, but it silently lost the record of the 203 paid calls. Fields renamed to
`*_this_run` (matching `step3_features_*.json`) and a `paid_run` block added pointing at the
22:09Z entry. **Noticed by reading the artifact back rather than trusting it.**
**Jev spend this step:** $0.00 · **running total:** ~$0.3539
**Next:** verify the whole document set is consistent, then commit TASK E.
---
## [2026-09-20T22:24Z] TASK D figure CORRECTED — the forest plot contradicted its own table
**Found by reading the figure back after the S2b result landed.** `RESULTS.md` §2's gate table
was updated to G4 = **+0.1211**, but `assets/gate_forest.png` is generated from
`gates_g2_g6_2026-09-20.json` and still drew G4 at +0.0927. **A figure disagreeing with the
table beside it is a defect**, not a cosmetic issue, and on a public repo it is the kind a
reader finds first.

**Fix:** `scripts/037_reliability.py` now reads `gate_g4_s2b_2026-09-20.json` when it exists and
draws **both** S2 rows — S2+S2a as a grey reference arm and **+S2b as the blue registered
gate** — so the figure does not quietly replace the first-reported number either. If the S2b
JSON is absent the script says so and falls back to the S2+S2a row alone, so a clean clone that
has not run TASK E still gets a correct figure rather than a crash.

**Second fix, same pass:** the negative-arm label (`B+N`, −0.0073) collided with its own row
label after the x-axis widened for the S2b row. Labels now always start right of both the
interval and the zero line. Verified by rendering and looking at it.
**Jev spend this step:** $0.00 · **running total:** ~$0.3539
---
## [2026-09-20T22:31Z] Step 3 cache race — STARTED
**Doing:** `scripts/034_step3_features.py` made **1,462 calls for 1,382 distinct states.** The
cache is checked at the top of `call()` and written at the bottom, so two workers that pick up
the same state both miss and both pay. **80 duplicate calls, ~$0.013.** Correctness is
unaffected — both responses are valid and the last write wins on an identical key — but a
clean clone re-running cold pays it again, and the repo is public.
**Fix:** a per-key lock, so the second worker on a state waits and then hits the cache.
**Command:** edit `scripts/034_step3_features.py`; verify against the warm cache.
**Idempotent:** yes. **The cache key, the request body and the response handling are NOT
touched** — only the concurrency around them — so cached responses stay valid and the
reproduction contract is unchanged.
**Jev spend this step:** $0.00 · **running total:** ~$0.3539
---
## [2026-09-20T22:40Z] DEFECT FOUND — the Step 3 race did more than waste $0.013
**How it surfaced.** After adding the per-key lock I re-ran `034_step3_features.py` warm to
prove the change was harmless: **0 new calls, $0.0000, 1,482 rows persisted.** I then
checksummed the rebuilt feature matrix against the one already in DuckDB:

| | sha256 of `jev_features_obsnotes` (first 16) |
| :--- | :--- |
| **as persisted by the original TASK C run** | `c58de4de6f01c31f` |
| **rebuilt from the cache, 0 calls** | `d7b5be5675778f44` |
| rebuilt again, 0 calls | `d7b5be5675778f44` (stable) |

**A zero-call re-run changed the matrix.** That should be impossible, and the cause is the
race itself:

- For each of the **80 duplicated states**, two workers both missed the cache and both called.
- **`results[(tic, toi)] = out` kept whichever response that row's own future returned**, while
  **the cache file on disk kept the LAST write.** For a duplicated state these are two
  *different* API responses — and by A-31 two calls seconds apart differ by mean |Δ| ≈ 0.0001.
- So the **originally persisted matrix is a mixture of in-memory and on-disk responses**, and
  **is not exactly reproducible from its own cache.**

**This is strictly worse than the "~$0.013 wasted" the handoff recorded**, and the handoff's
"correctness unaffected" was too generous. The per-key lock removes the cause: with one caller
per state, the in-memory response and the cached file are the same object by construction, and
the matrix is now **stable across re-runs** (verified twice above).

**What it does NOT mean.** The perturbation is bounded by the within-session drift, mean |Δ|
**0.0001** — **49× smaller** than the 0.0049 the A-33 arm perturbs by, and that arm moved ΔAUC
by sd 0.0010 with a worst case of −0.0023. So no gate verdict can plausibly move. **But
"plausibly" is what A-33 exists to stop me saying**, so the gates are being re-run on the
cache-consistent matrix and the published numbers checked against it.
**Jev spend this step:** $0.00 · **running total:** ~$0.3539
**Next:** re-run `035_gates_g2_g6.py` and compare every arm to the published table.
---
## [2026-09-20T22:58Z] Step 3 cache race — DONE. Every published number restated
**Command:** `034` (warm, 0 calls) → `035` → `039` → `038` ×2 → `037`. **0 API calls · $0.00.**
**Artifacts:** `scripts/034_step3_features.py` (per-key lock + `paid_run` block),
`scripts/039_gate_g4_s2b.py` (fit-variance arm), all five `research/data/*.json` regenerated,
both figures, `RESULTS.md`, `PREREGISTRATION.md` §11.8 (A-38), `PROVENANCE.md`, `README.md`.

**The matrix is now stable:** `sha256(jev_features_obsnotes)[:16] = d7b5be5675778f44`,
reproduced on three separate zero-call rebuilds.

| arm | first published | **cache-consistent** | shift |
| :--- | ---: | ---: | ---: |
| **G2 — headline** | +0.0440 | **+0.0432** [+0.0324, +0.0547] | **−0.0008** |
| D − B+meta | +0.0228 | +0.0220 [+0.0126, +0.0321] | −0.0008 |
| E − B | +0.0479 | +0.0482 [+0.0370, +0.0600] | +0.0003 |
| G5 registered (L6) | +0.0394 | +0.0391 [+0.0268, +0.0519] | −0.0003 |
| G5 sensitivity (no L6) | +0.0421 | +0.0426 [+0.0308, +0.0552] | +0.0005 |
| G6 | +0.0425 | +0.0425 [+0.0314, +0.0540] | −0.0000 |
| G4 — S2+S2a | +0.0927 | +0.0936 [+0.0622, +0.1268] | +0.0010 |
| **G4 — S2+S2a+S2b** | +0.1211 | **+0.1296** [+0.0948, +0.1670] | **+0.0085** |
| B+N · B+meta · C | — | unchanged | 0.0000 |

**Every S1 shift is ≤0.0010 — under ⅛ of the MDE — no verdict moves, every CI still excludes
zero.** The size matches the A-33 drift arm's sd of 0.0010, which is a useful check on that arm.
G2 is **5.3×** the MDE, not 5.4×. Calibration also moved: D Brier 0.0881 → **0.0892**, ECE
0.0232 → 0.0228, **MCE 0.0929 → 0.1196** (worst pooled bin now 0.7–0.8: 63 rows, pred 0.750 vs
obs 0.668). **A-29 survives unchanged in substance** — re-measured univariate |AUC| 0.749,
0.705, 0.695, 0.683, 0.648, 0.636, 0.579; **four of seven still clear ≈0.68**.

### The S2b arm moved 8× more than any S1 arm, so I measured why rather than guessing
**S2 is ONE train/test split and ONE CatBoost fit per arm; S1 averages 5 folds × 3 repeats.**
The paired bootstrap resamples *test groups*, not the fit, so an S2 point estimate carries fit
noise its interval does not show. Over 10 CatBoost seeds:

| arm | mean | sd | range |
| :--- | ---: | ---: | :--- |
| G4 — S2+S2a | +0.0954 | 0.0044 | [+0.0887, +0.1034] |
| **G4 — +S2b** | **+0.1286** | 0.0047 | [+0.1210, +0.1342] |
| G4c — 884 rows, full text | +0.1091 | 0.0050 | [+0.1045, +0.1179] |

**~±0.005 of seed noise on any S2 ΔAUC — roughly 5× the S1 figure.** The +0.0085 move is ~2 sd.
**The S2b effect survives it**: G4's worst seed (+0.1210) still clears G4c's best (+0.1179).

### A correction to my own 22:09Z entry
That entry called the S2b text effect **"marginal"** at +0.0135 [+0.0006, +0.0269] and said the
weaker claim was all that survived. On the corrected matrix it is **+0.0246 [+0.0115, +0.0383]**
and no longer marginal. **It is still not a gate and still post-hoc** — no section registered
that comparison — and `RESULTS.md` §6a says so. The stronger wording is earned by the number,
not by preference.

### And a correction to the handoff's characterisation of this defect
The handoff called the race *"cost ~$0.013, correctness unaffected."* **The cost was right and
"correctness unaffected" was wrong.** The race did not corrupt any response — every cached
response is valid — but it made the *persisted matrix* a mixture of in-memory and on-disk
responses and therefore **irreproducible from its own cache**, which is the property this whole
repository is built on. Found only because the fix was verified by checksum instead of by
"0 calls, $0.00, looks fine."
**Jev spend this step:** $0.00 · **running total:** ~$0.3539
**Next:** final consistency sweep, rewrite the handoff, commit.
---
## [2026-09-20T23:04Z] §11.6 pre-publication checklist — re-run after TASK D/E
**Command:** the checks in `PLAN.md` §11.6, including the widened absolute-path grep that item 9
warns about. **0 API calls · $0.00.**

| check | result |
| :--- | :--- |
| key anywhere in `git log -p` | **0 hits** |
| `.env` tracked | no |
| `data/` tracked | 0 files |
| `LICENSE` / `CITATION.cff` / `CONTRIBUTING.md` / `PROVENANCE.md` / `requirements.txt` | all present |
| absolute paths in `scripts/`, `src/`, `*.md` (both greps) | **none** |
| README acknowledgements · `research/01–02` superseded | intact |

**One checklist item is obsolete and is ticked with that said rather than silently:** *"README
states current status honestly, **including that the headline question is still open**"* was
written before the result. The question is answered. The item's intent — an honest status — is
met; its literal text is not, and cannot be. Flagged in `PLAN.md` §11.6 rather than quietly
reworded.
**Jev spend this step:** $0.00 · **running total:** ~$0.3539
---
## [2026-09-20T23:12Z] SESSION END — Claude Opus 5
**Completed:** **TASK D** (`RESULTS.md`, §9 item 7 — the last open item) and **TASK E** (S2b),
plus a defect found while closing out that restated every published number.

**§9's definition of done is now items 1–8 COMPLETE. The study has no required work left.**

**Headline:** **ΔAUC(D − B) = +0.0432, 95% CI [+0.0324, +0.0547]** — 5.3× the registered MDE.
**All six gates pass.** G4 is now the **registered** split (S2 + S2a + S2b) at **+0.1296**.

**Registered:** §11.6 (A-33…A-36), §11.7 (A-37), §11.8 (A-38).

### What changed that a reader needs to know
**The headline was +0.0440 for about two hours of this session and is now +0.0432.** The Step 3
cache race did not merely waste $0.013 — it made the persisted feature matrix a mixture of
in-memory and on-disk responses and therefore **irreproducible from its own cache**, which is
the property the whole repository rests on. Fixed with a per-key lock; matrix now stable at
`d7b5be5675778f44` across three zero-call rebuilds. Every arm re-run: **every S1 shift ≤0.0010,
no verdict moved.** The correction moves the headline **down**.

**It was found only because the "harmless" fix was verified by checksum rather than by
`0 calls, $0.00, looks fine`.** That is the transferable lesson and it is in the handoff.

### Defects found this session, all logged and fixed
1. **The Step 3 cache race was worse than recorded** (§11.8 A-38) — the headline defect above.
2. **The forest plot contradicted the table beside it** after G4 was updated, because it was
   generated from the pre-S2b JSON. Now reads the S2b result and draws both S2 rows.
3. **Two result JSONs were silently clobbered by cached re-runs**, erasing the record of the
   runs that paid. Cost fields are now `*_this_run` plus an explicit `paid_run` block.
4. **A `PROVENANCE.md` marker claimed automation that does not exist** — `<!-- BEGIN step3
   (scripts/034_step3_features.py) -->` implied that script rewrites the block; nothing does.
5. **`README.md`'s status block was stale on a public repo**, still reading "Nothing in this
   repository yet answers the headline question" three commits after all six gates passed.
6. **§10 item 2's note-count medians do not describe this corpus** (A-34).
7. **The repo's two values of B are input row order** (A-35) — explained, not left dangling.
8. **A figure label collision** in the forest plot, found by rendering it and looking at it.

### Claims I turned from arguments into measurements
- **A-31's "no gate verdict is at risk"** → A-33: sd 0.0010 at the measured drift, **G2 still
  passes at 10× the drift.**
- **"The S2b move is just fit noise"** → measured: **~±0.005 seed noise on any S2 ΔAUC**,
  ~5× the S1 figure. The S2b effect survives it (worst seed +0.1210 > G4c's best +0.1179).

### Two corrections to my own earlier entries in this session, made as new entries
- **22:09Z called the S2b text effect "marginal"** at +0.0135 [+0.0006, +0.0269]. On the
  corrected matrix it is **+0.0246 [+0.0115, +0.0383]** and is not marginal. **Still post-hoc,
  still not a gate.**
- **21:58Z projected S2b at $0.0332**; actual **$0.0338**, 1.8% over, ~5× under the handoff's
  ~$0.18.

**Not done, and stated plainly:** per-question reliability diagrams (no ground truth — would
need more labelled cases, A-36); CI still does not cover the gates and cannot without either a
key in CI or the cache committed, neither decision made; nothing external has checked any of
this — that is the single highest-value next step and it is not something this session could do.

**Jev spend this session: $0.0338 · running total: ~$0.3539.**
**Committed and pushed:** `3dadbf4` (TASK D), `4b50b7e` (TASK E), `6beb0a1` (the correction).
**Handoff rewritten:** `HANDOFF_PROMPT.md` — **the next session has no required work.**
---
## [2026-09-20T23:16Z] PUSHED — origin/master verified
`de1336b..8cf95a6` pushed to https://github.com/KevinArce/ExoNotes on the user's confirmation.
`HEAD` and `origin/master` both `8cf95a676439230cc05d4362b83de3081dd9a8b1`; branch not
diverged, working tree clean. The four commits: `3dadbf4` TASK D · `4b50b7e` TASK E ·
`6beb0a1` the cache-race correction · `8cf95a6` the handoff rewrite.
**Jev spend this step:** $0.00 · **running total:** ~$0.3539
---
## [2026-09-20T23:52Z] SESSION START — Claude Opus 5
**Picking up:** the completed study. `HANDOFF_PROMPT.md` states §9 items 1–8 are done and that
**no work is required**. Last entry was `23:16Z PUSHED`, an outcome, not an orphan `STARTED`,
so nothing was interrupted.
**First action:** verify the inherited state against the handoff's four claims before proposing
anything. Read-only, no API calls.
**Jev spend this step:** $0.00 · **running total:** ~$0.3539
---
## [2026-09-20T23:52Z] INHERITED STATE VERIFIED — all four claims hold
**Doing:** check the handoff's state claims against the repo rather than trusting them.
**Idempotent:** yes — read-only, no writes to `data/`, no API calls.

| claim in the handoff | measured | verdict |
| :--- | :--- | :--- |
| `data/cache/step3/` holds **exactly 1,382** responses | 1,382 | ✅ |
| `data/cache/s2b/` holds **203** responses | 203 | ✅ |
| corpus `analysis_set_obsnotes` = 1,482 rows | 1,482 | ✅ |
| `jev_features_obsnotes` = 1,482 × 10 (+2 key cols) | 1,482 × 13 (`tic_id`, `toi`, 10 features, 1 `__conf`) | ✅ |
| `jev_features_obsnotes_s2b` present | 1,482 | ✅ |
| **`sha256(jev_features_obsnotes)[:16] = d7b5be5675778f44`** | **`d7b5be5675778f44`** | ✅ |

Also present and matching: `analysis_set` 2,721 · `g5_arm_obsnotes` 1,114 · `obsnotes_text`
1,388 · `leakage_obsnotes` 10 · `toi_snapshot` 8,148. Working tree clean at `dbec09e`.

**GAP FOUND (documentation, not data): the checksum recipe was never recorded.** The handoff
says "if a rebuild does not produce this, stop and find out why", but no committed script or
document states *how* the 16 hex characters are produced, so a future session cannot actually
perform that check without guessing. It was recovered here by trying candidate serialisations:

```
sha256(duckdb.execute("select * from jev_features_obsnotes").fetchdf()
       .to_csv(index=False).encode()).hexdigest()[:16]   ->  d7b5be5675778f44
```

Load order matters, as A-35 already established for B: `to_csv(index=False)` on the table **as
stored** matches, and so does an explicit `sort_values('toi')` (the stored order is already
`toi`-sorted). Sorting by `['tic_id','toi']` instead gives `d952de67733cbfa8` — a **different**
checksum on **identical data**. Recorded because the check is worthless if the next session
sorts differently and concludes the matrix drifted.
**Jev spend this step:** $0.00 · **running total:** ~$0.3539
**Next:** await direction — the study has no required work; see the session's proposal.
---
## [2026-09-20T23:58Z] DECISION — CI will cover the gates via an API key in a GitHub secret
**Context.** `RESULTS.md` §9 item 5 says CI does not cover the gates and "cannot without either
an API key in CI or the response cache committed — both are real decisions with real trade-offs,
neither has been made." **The user has now made it: API key in a CI secret.**

**Two facts established before the choice, both of which the handoff's framing was missing.**

1. **A committed cache would not have worked on its own.** `cache_key()` hashes
   `MODEL + QUESTION_SET_VERSION + state + questions`, and the state is `{"notes": <raw text>}`
   read live from `analysis_set_obsnotes` (`034_step3_features.py:88` and `:165`). A cache hit
   therefore requires the note text to be **byte-identical**. ExoFOP gains notes continuously —
   which is precisely why `029_verify_reproduction.py` asserts tolerances and not equality. So
   "commit the cache" actually meant "commit the cache **and** freeze 1.9 MB of ExoFOP note
   text", or CI drifts into misses and silently starts paying.
2. **That would have collided with a stated position.** `README.md:173` — "No archival data is
   redistributed here."

**A third option was offered and declined:** commit only derived numbers (feature matrix +
numeric columns, ~200 KB, no prose), covering G2/G4/G5/G6 exactly for $0. It does not cover G3
or baseline C. The user chose full coverage with a live key instead.

**What the choice costs, recorded so it is not a surprise later.** ~$0.33 per cold full run
(step3 ~$0.24 + G3 ~$0.06 + S2b ~$0.03); CI becomes dependent on a paid third-party API's
availability; and **the assertions must be tolerance-based, not exact** — A-31 established that
a cold-cache run lands *near* +0.0432, not on it, and a CI run also re-pulls a drifted corpus.
**Jev spend this step:** $0.00 · **running total:** ~$0.3539
---
## [2026-09-20T23:58Z] CI GATE COVERAGE — STARTED
**Doing:** build CI that runs the full pipeline cold and asserts all six gates.
1. make the `.env` loader fall back to the process environment (no `.env` exists on a runner);
2. new `scripts/040_verify_gates.py` — asserts G1–G6 with drift-aware tolerances;
3. new `.github/workflows/gates.yml` — manual/scheduled, cost-capped, fork-safe;
4. update `RESULTS.md` §9 item 5, `README.md`, `PREREGISTRATION.md`.
**Idempotent:** yes for 1/2/3/4 (source edits, re-runnable). **The workflow itself is NOT
free to re-run** — each dispatch costs ~$0.33 against a cold cache.
**Two traps this must avoid, both already paid for in this repo:**
- **The result JSONs have hardcoded filenames** (`gates_g2_g6_2026-09-20.json`), so a CI run
  **overwrites** them. Reference values must be **constants inside the verifier**, never read
  from the committed JSON — otherwise the run clobbers the file it is about to be compared to
  and the check passes vacuously. That is defect 24, and defect 20 in a different costume.
- **G4's registered value is NOT in `gates_g2_g6*.json`.** That file's `G4` key is the pre-S2b
  +0.0936. The registered +0.1296 is `gate_g4_s2b*.json → arms → "G4b S2+S2a+S2b (train 884)"`.
  Reading the wrong one is what produced the contradictory forest plot last session.
**Jev spend this step:** $0.00 · **running total:** ~$0.3539
---
## [2026-09-21T00:04Z] `.env` loader now falls back to the process environment — DONE
**Doing:** `(ROOT / ".env").read_text()` raises `FileNotFoundError` on a runner, where there is
no `.env` by construction (the `reproduce` workflow asserts `.env` is not tracked). Guarded with
`_envfile.exists()`. An existing `.env` still wins, so a local run is bit-for-bit unchanged.
**Files:** `scripts/034_step3_features.py`, `scripts/025_question_gate.py`,
`scripts/032_question_gate_obsnotes.py`. 036 and 039 load 034 as a module, so they inherit it.
**Idempotent:** yes.

**Verified by output, three ways:**

| path | result |
| :--- | :--- |
| `.env` present (local) | `already cached 1382 · to call: 0 · $0.0000` — unchanged |
| no `.env`, `TYPESAFE_API_KEY` in env (**the CI path**) | same output, runs |
| no `.env`, no key | **exit 1**, `no TYPESAFE_API_KEY found` — fails closed |

**Correction to my own first attempt at that table.** The no-key case initially reported
**exit 0**, which I nearly recorded as "fails closed" without looking. It was a **bad test**:
the scratch tree used *symlinks* to `scripts/` and `src/`, and `ROOT` is
`pathlib.Path(__file__).resolve().parent.parent` — **`.resolve()` follows the symlink**, so ROOT
came back as the real repo and the loader read the real `.env`. Re-run with real copies, the
no-key case exits 1 as it should. **The patch was fine; the test was measuring the wrong tree.**
Recorded because it is the §11.8 lesson again: a green result from a test that never touched the
thing under test is worth nothing.
**Jev spend this step:** $0.00 · **running total:** ~$0.3539
**Next:** `scripts/040_verify_gates.py`.
---
## [2026-09-21T00:22Z] VERIFIER + WORKFLOW — DONE
**Artifacts:** `scripts/040_verify_gates.py`, `scripts/041_test_verify_gates.py`,
`.github/workflows/gates.yml`.
**Idempotent:** yes for the scripts (read-only). **The workflow is NOT** — each dispatch spends
~$0.33 against a cold cache.

**`040_verify_gates.py`** asserts G1–G6 plus two controls, 11 criteria. Reference values are
**constants in the file**, not read from `research/data/` — a pipeline run overwrites those
JSONs, so comparing a run against the file it just rewrote would pass vacuously (defect 24).
Run against the current state: **11/11 PASS**, and every value it reads matches `RESULTS.md`
exactly — G2 +0.0432, G4 +0.1296 (from the **S2b** arm, not `gates_g2_g6`'s pre-S2b +0.0936),
G5 +0.0391, G6 +0.0425, B+N −0.0073, D−B+meta +0.0220, C 0.8766.

**It asserts registered criteria, not equality**, because a cold CI run differs from publication
by model drift (A-33, sd 0.0010) and, much more, by **corpus drift** — ExoFOP gains notes
continuously, so CI re-pulls different data. A point estimate moving more than 5× the A-33 sd
raises a **NOTICE**, not a failure: corpus drift can legitimately cause it, and a build that
goes red on normal archive drift trains everyone to ignore it (`029`'s docstring, same reason).

**`041_test_verify_gates.py` — the verifier is proven to FAIL.** 15 mutations, each breaking one
claim: G2's CI crossing zero, G2 real but under the MDE, G4/G5/G6 collapsing, G3 losing a
predictive feature, B dropping under 0.85, **the dilution floor flipping positive**, prose
ceasing to beat metadata, the corpus halving, a zero-call run under `--require-paid`, and
missing inputs. **All 15 behaved correctly.** This exists because a verifier only ever seen to
pass is defect 20 in waiting. CI runs it **before** the paid steps — no point spending $0.33 to
feed a check that cannot fail.

**Workflow guards, each tested rather than assumed:**

| guard | behaviour |
| :--- | :--- |
| `if: github.repository == 'KevinArce/ExoNotes'` | forks never burn 90 min discovering they lack the secret |
| secret presence check | fails in seconds; prints **length only**, never the value |
| cold-start assert | fails if `data/` or `.env` appears in a clean clone |
| mutation test first | free, and gates the paid steps |
| cost preflight | parsed **$0.2421** from real cold output; **aborts** over the `$0.50` ceiling, **aborts** at `$0.00` (a warm/empty cache means the run would test nothing), **aborts** if the projection cannot be parsed rather than spending blind |
| `cancel-in-progress: false` | cancelling a paid run wastes money already spent |
| no `push` trigger | a five-commit afternoon would otherwise cost $1.65 |
| artifacts uploaded, never committed back | the published numbers stay published |

**Triggers:** `workflow_dispatch` + monthly cron (~$4/year). YAML validated with pyyaml
installed to a **scratch** dir — `requirements.txt` is the reproduction contract and was not
touched.

**Noted, not changed:** `036_gate_g3_stability.py` has **no cost tripwire of its own**; its spend
is bounded structurally by `N_ROWS = 200` over two arms (~$0.06). Editing a study script to add
one is not something to do quietly at this stage, so it is recorded here instead.
**Jev spend this step:** $0.00 · **running total:** ~$0.3539
**Next:** `RESULTS.md` §9 item 5, `README.md`, `PREREGISTRATION.md` §11.9.
---
## [2026-09-21T00:41Z] CI GATE COVERAGE — DONE. `RESULTS.md` §9 item 5 is closed
**Artifacts:** `.github/workflows/gates.yml`, `scripts/040_verify_gates.py`,
`scripts/041_test_verify_gates.py`, `.env` loader patch in 025/032/034,
`PREREGISTRATION.md` §11.9 (**A-39**), `RESULTS.md` §9 item 5, `README.md`, `HANDOFF_PROMPT.md`.

**Verification, by output:**

| check | result |
| :--- | :--- |
| `041` mutation test | **15/15 mutations caught** — the verifier can fail |
| `040` against current state | **11/11 criteria hold**, every value matching `RESULTS.md` |
| matrix checksum after all edits | **`d7b5be5675778f44`** — unchanged |
| `034 --dry-run`, `039 --dry-run` | run clean post-patch, **0 calls, $0.0000** |
| both workflow YAMLs | parse (pyyaml in a scratch dir; `requirements.txt` untouched) |
| all patched/new scripts | `py_compile` clean |
| literal-secret scan over the whole diff | none; `.env` ignored and untracked |

**Jev spend this step:** $0.00 · **session total: $0.00** · **running total:** ~$0.3539

**Three documentation defects found and fixed while doing this, none of them CI:**
1. **The checksum recipe was never recorded** (00:04Z entry). The handoff ordered the next
   session to verify `d7b5be5675778f44` and **stop** on a mismatch, without saying how to
   compute it. Now in `HANDOFF_PROMPT.md`, with the warning that row order changes the answer
   (`['tic_id','toi']` gives `d952de67733cbfa8` on identical data).
2. **`README.md:173` said "No archival data is redistributed here" and that was not true.**
   `research/data/gate_cases_obsnotes_2026-09-20.json` carries **27 verbatim ExoFOP observing
   notes, 66,804 characters** — counted, not estimated. The claim now states the exception and
   why it exists (the gate cannot be audited without the text that was judged).
3. **A cross-reference I wrote myself was wrong** and is corrected here as a new entry rather
   than silently: the new §9 item 5 first ended "item 1 below stands untouched", but §9 item 1
   is the struck-through S2b item and **§9 has no external-validation entry at all**. Replaced
   with the plain statement instead of a pointer to nothing.

**A-5 is superseded but was NOT rewritten.** It says "The CI reproduction does not cover this —
it makes no API calls" about the model pin; `gates.yml` now does cover it. §11 is append-only,
so A-5 keeps its text and §11.9 records the supersession, exactly as §11.7 did for A-36 item 2.

**NOT DONE, and it is a hand step nobody else can do:** the `TYPESAFE_API_KEY` secret is **not
set** on the GitHub repository, so `gates.yml` **has never run**. It fails at step two by design
until someone adds it under *Settings → Secrets and variables → Actions*. Flagged at the top of
the handoff's CI section.

**What this does not achieve, stated because the badge will imply otherwise:** CI is this
pipeline checking itself, by its own author, against the same archive. **It is not independent
replication** and the handoff's gap 1 is untouched by it.
**Next:** commit; ask before pushing (the repo is public).
---
## [2026-09-21T00:52Z] PUSHED — origin/master verified · secret confirmed present
`dbec09e..83d6251` pushed to https://github.com/KevinArce/ExoNotes on the user's confirmation.
`HEAD` and `origin/master` both `83d62516ebbb81844541ccbc7bace008ce833394`; not diverged, tree
clean. One commit: `83d6251` CI gate coverage (§11.9 A-39).

**`TYPESAFE_API_KEY` is now set**, confirmed by the user against the repository settings page —
as a **Repository secret**, which is the form `${{ secrets.TYPESAFE_API_KEY }}` resolves. An
*Environment* secret would not have reached the job without an `environment:` key, and that
page showed "This environment has no secrets", so the distinction mattered. `gates.yml` is
therefore live and **able to run for the first time**.

**Consequence now in effect, flagged rather than left to be discovered on an invoice:** the
monthly cron (`41 7 1 * *`) will spend **~$0.33 unattended on the 1st of each month**, ~$4/year.
Until today it would have failed free at the secret check. The user has been asked whether to
keep the schedule or move to dispatch-only; **unanswered as of this entry, schedule retained.**

**Still true, and the badge will imply otherwise:** this is the pipeline checking itself, by its
author, against the same archive. **Not independent replication.** Handoff gap 1 stands.
**Jev spend this step:** $0.00 · **session total: $0.00** · **running total:** ~$0.3539
---
## [2026-09-21T00:56Z] FIRST `gates.yml` RUN — STARTED
**Doing:** dispatch `gates.yml` for the first time. Everything to date was verified locally;
only a real run exercises the runner path — cold ingest, the ExoFOP pull from a GitHub IP, the
secret reaching the four paid steps, and the verifier's tolerances against a **genuinely
re-pulled** corpus rather than the committed one.
**Command:** `gh workflow run gates.yml --ref master`
**Idempotent: NO.** Each dispatch spends **~$0.33** against a cold cache. Do not re-run to
"see if it works" — read the run log instead.
**Decision recorded:** the monthly cron is **kept** (~$0.33/mo, ~$4/yr) on the user's
instruction. Rationale: on a finished study, unattended detection of *upstream* drift — ExoFOP
changing the corpus, the API changing behaviour, `jev-1.13.0` being retired — is the main thing
CI can still report.
**Expected:** ~$0.33 · up to ~90 min · **all six gates PASS**, with point estimates *near* but
not equal to publication. A **NOTICE** is an acceptable outcome and is not a failure.
**Jev spend this step:** $0.00 so far · **running total:** ~$0.3539 (about to rise by ~$0.33)
---
## [2026-09-21T00:31Z] FIRST `gates.yml` RUN — DONE. **All six gates pass from a cold cache**
**Run:** [35547134433](https://github.com/KevinArce/ExoNotes/actions/runs/35547134433) ·
**conclusion `success`** · **10.9 min** of the 120 min cap · **12/12 criteria hold, no NOTICE.**

**This is the first true cold-cache end-to-end reproduction the study has ever had.** `RESULTS.md`
§8 could only *predict* where one would land ("near +0.0432, not on it"). It is now measured.

| arm | published | **CI, cold, 2026-09-21** | Δ |
| :--- | ---: | ---: | ---: |
| **G2 — the headline** | +0.0432 | **+0.0451** [+0.0344, +0.0567] | **+0.0019** |
| **G4** S2+S2a+S2b | +0.1296 | **+0.1265** [+0.0911, +0.1642] | −0.0031 |
| **G5** with L6 | +0.0391 | **+0.0403** [+0.0278, +0.0537] | +0.0012 |
| **G6** | +0.0425 | **+0.0434** [+0.0326, +0.0549] | +0.0009 |
| **D − B+meta** | +0.0220 | **+0.0241** [+0.0147, +0.0342] | +0.0021 |
| **B+N** dilution floor | −0.0073 | **−0.0069** [−0.0129, −0.0011] | +0.0004 |
| G1 ΔAUC · G1 B · baseline C | +0.4212 · 0.9051 · 0.8766 | **identical to 4 dp** | **0.0000** |
| G2's B (numeric only) | 0.9044 | 0.9042 | −0.0002 |

**The decomposition is clean, and it is the point of the table.**
1. **The corpus did not drift at all.** 1,482 rows / 1,388 TIC / base 0.5378, and the
   **numeric-only** arms — G1's B, baseline C — reproduce to four decimals. ExoFOP served the
   same data a day later. So none of the movement below is corpus drift.
2. **G2's B moved 0.0002** — numeric-only, so not the model. That is the **documented
   macos/arm64 vs linux/x64 offset** (~5×10⁻⁴), landing where PLAN says it does.
3. **Every arm containing a Jev feature moved 0.0009–0.0031** — that is **model drift over ~28
   hours**, and it is the only channel left once 1 and 2 are accounted for.

**A-33 predicted this and the prediction holds.** A-33 simulated the *1-hour* drift (0.0049) and
got ΔAUC sd **0.0010**; this run is ~28 h out, so a larger shift is expected, and **+0.0019** is
about 2× that sd — far inside the 10× band where G2 still passed (+0.0385). The arm was built to
answer exactly this question and it answered it correctly **before** the question was asked.

**⚠️ The headline moved UP and that changes nothing. The published headline is +0.0432.** A cold
re-run is a reproduction check, not a re-measurement; adopting +0.0451 because it flatters the
study is precisely what §11.8 refused to do in the other direction. **+0.0451 is what drift looks
like, not an improvement.**

**Operational results, each of which was previously only asserted:**
- **`requirements.txt` installs clean on a fresh linux/x64 Python 3.14.7 runner.**
- **Cold ExoFOP pull: 2,573 TIC in ~2.5 min at 5 workers, 0 failures** — no throttling from a
  GitHub IP. My earlier worry that the 120 min cap might be tight was **wrong**: 10.9 min total.
- **The A-38 per-key lock is verified under real concurrency on different hardware:**
  **1,382 calls for 1,382 distinct states, `failed=0`** — exactly one call per state. The buggy
  version made 1,462 for the same 1,382. The 100 `cached` are within-run dedup hits.
- **G3's two label-echo failures reproduce exactly** (`indicates_retired_or_rejected` ρ 0.806,
  `contains_object_designation` ρ 0.801). Still FAIL, still not relaxed (A-32). G3 verdict PASS
  on 7/7 predictive. G3(b) still correctly reported VACUOUS.
- **S2b re-scored 203 states for 804,981 tokens — byte-identical token count to the original
  run**, confirming the same states were constructed from the same text.

**Cost:** Step 3 **$0.2285** (1,382 calls, 82 s) · S2b **$0.0338** (203 calls) · G3 ~$0.06
(not itemised by `036`; bounded by `N_ROWS = 200` × 2 arms). **≈$0.32 this run**, against the
~$0.33 projected. Preflight projected $0.2269 for Step 3 and it came in at $0.2285, **0.7% over**.
**Jev spend this step: ~$0.32** · **running total: ~$0.674**

**The verifier's tolerance design is vindicated by the one thing that did not happen: no NOTICE.**
Every delta is under the 0.0050 threshold, so the run passed cleanly without the escape hatch —
while an equality check would have failed on all six gates.
**Next:** record the measurement in `RESULTS.md` §8 and A-39; the handoff says "never been run".
---
## [2026-09-21T00:38Z] First-run measurement recorded in the write-up — DONE
**Artifacts:** `RESULTS.md` **§8a** (new section, the cold-cache reproduction with the
three-way decomposition), `RESULTS.md` §8 opener and the §11.1 spend row, `PREREGISTRATION.md`
**A-39a**, `HANDOFF_PROMPT.md` (CI section now reads "run once, and it passed"; spend to date),
`README.md` (status table spend, and the cold-cache caveat now carries the measured +0.0451).
**Idempotent:** yes — documentation only.

**Verified after editing:** local matrix checksum still **`d7b5be5675778f44`** and
`040_verify_gates.py` still **11/11** — the CI run is ephemeral and changed nothing here, which
is what it should do. The published headline still reads **+0.0432** in `RESULTS.md`, `README.md`
and `HANDOFF_PROMPT.md`; **the +0.0451 appears only as a reproduction measurement and nowhere as
a headline.** No document still claims the workflow has never run.
**Jev spend this step:** $0.00 · **running total:** ~$0.674
**Next:** commit; ask before pushing.
---
## [2026-09-21T00:44Z] PUSHED — origin/master verified
`e64c250..d245892` pushed to https://github.com/KevinArce/ExoNotes on the user's confirmation.
`HEAD` and `origin/master` both `d2458927e023132c6f7e7e482cfb360424db5c15`; not diverged, tree
clean. Three commits this session: `83d6251` CI gate coverage · `e64c250` push log + secret
confirmation · `d245892` the first cold-cache reproduction.
**Jev spend this step:** $0.00 · **running total:** ~$0.674
---
## [2026-09-21T00:45Z] SESSION END — Claude Opus 5
**Completed:** the user's chosen direction — **CI now covers the gates** — plus the first run of
it, which produced a measurement the study did not previously have.

**`RESULTS.md` §9 item 5 is CLOSED.** Registered as §11.9 **A-39** (the design and its
trade-offs) and **A-39a** (the first run). The study's definition of done was already complete
before this session; nothing here changes a published number.

**Built:** `.github/workflows/gates.yml` · `scripts/040_verify_gates.py` (11 criteria, 12 with
`--require-paid`) · `scripts/041_test_verify_gates.py` (15 mutations, all caught) · `.env`
loader fallback in 025/032/034.

**First run:** [35547134433](https://github.com/KevinArce/ExoNotes/actions/runs/35547134433) —
`success`, 10.9 min, 1,382 calls, ~$0.32, **12/12, no notice**. **G2 +0.0451 vs published
+0.0432**, decomposed in `RESULTS.md` §8a: corpus did not drift (numeric-only arms identical to
4 dp), 0.0002 is the platform offset, the rest is ~28 h of model drift. **A-33 predicted the
magnitude before the question was asked.**

**Three things I got wrong during the session, each corrected as a new entry rather than edited
away:** a symlinked scratch tree made the no-key test read the real `.env` and report a false
pass (00:04Z); a cross-reference I wrote pointed at a `RESULTS.md` §9 item that does not exist;
and I flagged the 120-minute CI cap as a schedule risk on the basis of a *warm* 6-minute figure —
the real cold run took 10.9 minutes total.

**Three documentation defects found and fixed, none of them CI:** the matrix checksum had no
recorded recipe, making the handoff's "stop if this does not reproduce" unfollowable;
`README.md` claimed no archival data is redistributed while 27 verbatim ExoFOP notes (66,804
characters) sit in `research/data/`; and A-5's "the CI reproduction makes no API calls" is now
superseded — left intact, with the supersession recorded, because §11 is append-only.

**Decisions the user made this session:** API key in a CI secret (over a committed cache or a
derived-numbers artifact); **monthly cron kept** at ~$0.33/run unattended; first run triggered
immediately rather than left to fire unattended.

**Unchanged and still the largest gap: nothing external has checked this.** CI is this pipeline
checking itself on borrowed hardware. `PLAN.md` §8 lists the registered extensions; a second
corpus or an outside runner remains the highest-value next step.

**Jev spend this session: ~$0.32 · running total: ~$0.674.**
**Pushed:** `83d6251`, `e64c250`, `d245892`. **Working tree clean.**
---
## [2026-09-21T01:12Z] `CITATION.cff` rewritten — it described the ABANDONED corpus
**Doing:** step 1 of the publication track. **Idempotent:** yes — metadata only, no API calls.

**What was wrong, and it was not cosmetic.** The file still described the study the project
**abandoned**:
- **Title** read *"do ExoFOP follow-up **comments** carry disposition signal…"*. The study moved
  off the `Comments` field precisely **because** it restates the label in 47.9% of rows. The
  citation named the discredited corpus, not the one the result is on.
- **`authors: - name: "ExoNotes contributors"`** — no real person, so no credit and no
  discoverability. Rendered as an anonymous artifact.
- **Abstract** described the `Comments` design and carried **no result at all** — no ΔAUC, no
  interval, no corpus size, three sessions after all six gates passed.

**Now:** correct title (**observer notes**, numeric **TOI** catalogue); a named author from the
git identity; an abstract carrying the headline **+0.0432 [+0.0324, +0.0547]**, B 0.9044 → D
0.9476, 5.3× the MDE, the B+meta control **+0.0220**, baseline C **0.8766 below B**, both
leakage cautions (**47.9%** of 2,725 rows; `pscomppars` **P=0.995 vs 0.074**), the pinned model,
and an explicit scope paragraph stating that **the label is a human judgment and the notes are
the evidence record produced on the way to it** — so the study anticipates expert consensus and
is **not** a planet detector. Keywords extended to 11 for discoverability.

**Verified, not eyeballed:** `cffconvert --validate` → *"Citation metadata are valid according to
schema version 1.2.0."* Renders as `Arce, Kevin` in APA and BibTeX. Validator installed to a
**scratch** venv; `requirements.txt` untouched.

**Three fields deliberately left as `TODO-CONFIRM`, because I cannot derive them and a DOI
records them permanently:** the **name split** (`Kevin` / `Arce` is inferred from
`KevinArce <iav.kevinarce@ufg.edu.sv>`; Spanish naming often carries two surnames), the
**ORCID**, and whether to claim the **UFG affiliation** or publish as independent. `doi:`,
`version:` and `date-released:` are commented pending the Zenodo release — which is why the
rendered citation currently carries no year.

**Not in the repo, by request:** the publication plan lives in `LOCAL_PLAN.md`, excluded via
**`.git/info/exclude`** rather than `.gitignore` — `.gitignore` is itself committed, so listing
it there would publish the filename. Verified invisible: `git status` clean with the file
present.
**Jev spend this step:** $0.00 · **running total:** ~$0.674
**Next:** ORCID → confirm identity fields → Zenodo release → DOI back into this file.
---
## [2026-09-21T01:24Z] `CITATION.cff` author identity finalised — the work is now attributable
**Doing:** resolve the three `TODO-CONFIRM` fields left at 01:12Z. **Idempotent:** yes.

```yaml
- given-names: "Kevin Javier"
  family-names: "Arce Alfaro"
  orcid: "https://orcid.org/0000-0003-3453-6551"
  affiliation: "Independent Researcher"
```

**Verified rather than accepted, because a DOI records this permanently:**
1. **ORCID checksum** `0000-0003-3453-6551` recomputed by ISO 7064 MOD 11-2 → check digit **1**,
   matches. A transposed digit would have passed a visual read and failed here.
2. **The public ORCID record was fetched and it returns `given-names: Kevin Javier` /
   `family-name: Arce Alfaro`** — so the two-surname split is **confirmed against an external
   source**, not inferred from the git identity. My earlier guess of `Kevin` / `Arce` was wrong
   and would have dropped the second surname into a permanent citation.
3. **`cffconvert --validate`** still passes schema 1.2.0; renders **`Arce Alfaro, Kevin Javier`**
   in APA and BibTeX.

**No affiliation claimed** — the work was done independently, stated explicitly rather than left
blank so it reads as deliberate.

**The institutional email was REMOVED, deliberately.** `iav.kevinarce@ufg.edu.sv` remains in the
git history and is not being hidden, but it does not belong in a permanent citation record: no
affiliation is being claimed, and an institutional address stops working when the affiliation
does. **The ORCID is the durable identifier and routes contact.** A personal address can be added
later if a direct path is wanted.
**Jev spend this step:** $0.00 · **running total:** ~$0.674
**Next:** step 2 — Zenodo: link GitHub + ORCID, tag `v1.0.0`, publish the Release, DOI back into
`CITATION.cff` and the README badge.
---
