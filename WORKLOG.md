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
**Doing:** `/Users/arce/Projects/Jev` → `/Users/arce/Projects/ExoNotes` (user request).
**Result:** Renamed. Converted absolute `file:///…/Jev/…` links in `research/README.md` to relative
paths so they survive future renames.
**Side effect handled:** Claude memory is keyed by project path — copied
`~/.claude/projects/-Users-arce-Projects-Jev/memory/` → `-Users-arce-Projects-ExoNotes/memory/`,
preserving the "always load the typesafe-ai skill" instruction. Old dir left in place, harmless.
**Note (not caused by this session):** `task.md` was moved to `~/.Trash` at 16:33 by a Finder/IDE
action (`rm` does not use the Trash). Left in place; README reference removed. Restore with
`mv ~/.Trash/task.md /Users/arce/Projects/ExoNotes/`.
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
`git grep` found `/Users/arce/...` in **`WORKLOG.md` lines 31 and 39** (the 16:26Z PROJECT
RENAME entry). Publishing would expose the macOS short username `arce`.
**I did not edit those lines.** PLAN.md §0.5 non-negotiable #2 is "append only — never edit or
delete a past entry", and silently rewriting history to tidy a public repo is exactly the kind
of edit that rule exists to prevent. This is the user's call. Options:
- **(a) Leave it.** The GitHub account name will be public anyway; "arce" reveals nothing more.
- **(b) Redact before the first push**, and record the redaction in a NEW worklog entry so the
  change is itself logged. Only clean while there is no published history.
No other tracked file contains a local path.
**Next:** initial commit (local only — NOT pushing; creating a public remote is the user's call).
---
