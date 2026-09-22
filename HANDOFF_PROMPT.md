# ExoNotes — handoff to the next session

You are picking up the ExoNotes project. **Work from the repo, not from memory.**

---

## ⚠️ START HERE — both studies are DONE and published as v1.1.0. There is no registered task pending.

### 1. TESS — positive, all six gates pass. Do not redo it.

> **ΔAUC(D − B) = +0.0432, 95% CI [+0.0324, +0.0547]**, S1, `TIER_PREDICTIVE` only, paired
> bootstrap over TIC groups. **5.3× the registered MDE of +0.0082.** D − B+meta **+0.0220**.

G1 B 0.9051 · G2 +0.0432 · **G3 7/7 (corrected in v1.1.0 — see below)** · G4 +0.1296 ·
G5 +0.0391 · G6 +0.0425. All pass. `RESULTS.md`.

### 2. Kepler transfer test — NEGATIVE, by the reading registered before the run.

> **TRANSFERS ONLY AS FOLLOW-UP VOLUME — the content claim does not transfer.**
> KG2 D − B **+0.0234** [+0.0186, +0.0282] (12× the +0.0019 MDE) — but **D − B+meta = −0.0023
> [−0.0041, −0.0004]**: a no-model control counting notes/characters/authors beats the features.
> KG5 (both arms), KG6, KG4 pass. **KG3 FAILS** — 3 of 6 predictive features miss ρ ≥ 0.85.

`RESULTS_KEPLER.md`; `PREREGISTRATION.md` §11.10 (registered before), §11.11 A-42 (after).
**Do not reach for another arm to rescue it.** D + meta vs B+meta was never registered and has
**not** been run; if anyone wants it, it needs its own pre-registration first.

### 3. A v1.0.0 number was wrong, and v1.1.0 corrects it (defect 34)

A thread race in the G3 scripts (`036` TESS, `049` Kepler) swapped shared module globals from 8
threads. On TESS it sent 4/197 paraphrase calls with the original wording **and** left `036`
reading its baseline from the repeat arm's own responses. **Verdicts unchanged**, but:
**paraphrase effect is 4.4× the noise, not 412×**, and **identical requests differ by ~0.005 per
feature at 9–21 min, not 0.0001** ("effectively deterministic within a session" is withdrawn).
Both scripts now lock the swap and stop if the globals are not restored. §11.12 A-43.

**Citable:** concept DOI **`10.5281/zenodo.22866246`** (cite this). Version DOIs: v1.0.0
`…22866247`, **v1.1.0 `…22886178`** (tag `v1.1.0` → `2f9acef`, released 2026-09-22T03:00:30Z).

**Jev spend to date: ~$1.608** (TESS ~$0.354 · CI runs ~$0.32 + ~$0.326 · Kepler ~$0.607).

---

## ⚠️ NUMBERS YOU MIGHT MISREMEMBER — ALL ARE TRAPS

1. **TESS headline +0.0432** — not +0.0440 (pre-A-38) nor +0.0451 (28 h drift on cold CI).
2. **TESS G3 noise ratio is 4.4×**, not 412×. Tightest predictive feature ρ **0.866**, not 0.884.
3. **Jev same-wording variation is ~0.005** per feature (0.0056 at 9–15 min; 196/197 states
   differ), not 0.0001. The old "~1 hour" gap was really 14–21 min (estimated log timestamps).
4. **Kepler: D − B+meta is −0.0023** — negative, CI excludes 0. D − B is +0.0234.
5. **Kepler Step 5 made 3,192 calls, not 3,843**: 3,843 hosts carry 3,192 distinct texts. The
   write-once `kepler_step3_paid_run.json` says `distinct_states: 3843` — that field counts hosts.
6. **Cite the CONCEPT DOI `…22866246`**, never the version DOI the badge endpoint hands you.
7. **The Kepler corpus is CFOP observer notes, not the FPWG table** (withdrawn, A-40 40.0).

**Checksums (`sha256(to_csv)[:16]`)** — TESS matrix `jev_features_obsnotes` **`d7b5be5675778f44`**
(re-verified 2026-09-22) · Kepler corpus `kepler_cfop_corpus` **`f3c30d2daf460095`** · Kepler matrix
`kepler_jev_features` **`647a73578551b2b4`**. Row order is part of each. If a rebuild does not
reproduce them, stop and find out why.

---

## What is worth doing next (none is registered; each is the owner's call)

1. ~~Dispatch CI once~~ **Done 2026-09-22, run `35682030220`: all 12 criteria hold cold.** G3's
   repeat arm now reads **0.0055** (the previous CI run read 0.0000 — the defect), ratio 4.5×.
   Corpus verified identical to publication by summed tokens (5,441,507). One NOTICE (G4 −0.0057)
   = ~1 CatBoost seed-sd of a single S2 fit (seed sd 0.0047–0.0050), not corpus drift.
   **Follow-up done:** `040` now requires G3's repeat mean |Δp| ≥ 0.001 (measured 0.0050–0.0056);
   it FAILS the defective CI run's artifacts (0.0000) and v1.0.0's file (0.00006), PASSES this
   run's (0.0055). `041` has a mutation for each → 17/17.
2. **External replication** — still the largest open gap. Nothing outside this repo has checked it.
3. **An RNAAS note** — now with a stronger story: the leakage findings (TESS `Comments` restates
   the label in 47.9% of rows; `pscomppars` leaks at P = 0.995; Kepler FPWG comments track the
   label at 98.1%; `koi_comment` *is* the vetting rationale) **plus** a pre-registered transfer
   test that came out negative, **plus** a follow-up-volume control that decided it.
4. **Contact ExoFOP** with the leakage finding, now that a DOI exists.
5. **CI does not cover Kepler.** Adding it would be infrastructure, not a new result.

---

## Read first, in this order

1. **`WORKLOG.md` — the TAIL.** Append-only. This session starts at `2026-09-22T02:08Z`.
2. **`RESULTS_KEPLER.md`**, then **`PREREGISTRATION.md` §11.10–§11.12**.
3. **`RESULTS.md`** §1, §2, §6 (corrected), §8 (corrected), §9.
4. **`PLAN.md` §0.5 (work logging) and §1 (guardrails).**

## Mandatory working rules

Narrate every step **and** persist it to `WORKLOG.md` as you go. `STARTED` before, `DONE` /
`FAILED` / `BLOCKED` after. **Append only** — corrections go in a *new* entry. `Idempotent:
yes/no` on every `STARTED`; cumulative Jev spend on every entry that calls the API. **Never log
secrets** — the key is `TYPESAFE_API_KEY` in `.env` (gitignored).

**Take every timestamp from `date -u`.** Two sessions estimated theirs and both drifted — one by
~20 min, the TESS one by ~1 h 40 min — and the TESS drift made a published "~1 hour" gap wrong.
For *when a call happened*, use cache-file mtimes and commit times, not log headings.

**Chain dependent commands with `&&`, never `;`. Verify by output, not by exit path** — `0 calls`
is not evidence that anything happened. **New this session: verify which wording a call carried
from `usage.input_tokens`** — for one state, same wording ⇒ identical token count; a paraphrase ⇒
a constant offset. That is how defect 34 was found and how its fix was verified.

**Never mutate another module's globals from worker threads.** If a script must swap them, lock
swap + call + restore as one step and assert they are restored before reading anything through
them (defect 34).

**THE REPO IS PUBLIC.** Commit as `KevinArce <iav.kevinarce@ufg.edu.sv>`. **Ask before pushing.**

---

## State you are inheriting

### Kepler (`data/kepler.duckdb` — separate; TESS's DB is only ever opened read-only by Kepler code)

| table / dir | what |
| :--- | :--- |
| `kepler_cfop_corpus` | **the corpus** — 4,720 KOIs / 3,843 hosts / base 0.5750 |
| **`kepler_jev_features`** | **the matrix** — 4,720 rows × 8 questions, 0 nulls, `647a73578551b2b4` |
| `data/cache/kepler_step3/` | 3,192 responses (one per distinct text) — re-runs are free |
| `data/cache/kepler_kg3/` | 362 outer + inner dirs `…r3-para/`, `…r3-repeat/` (724 files) |
| `kepler_fpwg_raw`, `kepler_corpus` | the **withdrawn** FPWG corpus — do not revive |

Results: `research/data/kepler_gates.json`, `kepler_kg3_stability.json`,
`kepler_step3_paid_run.json` (**write-once**), `kepler_step3_features_latest.json`.

### TESS (`data/exonotes.duckdb`)

`analysis_set_obsnotes` (1,482 / 1,388 TIC / 0.5378), `jev_features_obsnotes` (checksum above).
`data/cache/step3/` = 1,382 responses. `data/cache/g3/` = 792 (the 4 re-asked paraphrase files
are among them); **`data/cache/g3_defect34_quarantine/`** holds the 4 contaminated originals —
kept as evidence, not deleted. `research/data/gate_g3_stability_2026-09-20.json` was rewritten in
place by the fixed `036` (the v1.0.0 version is in git at `d23d32d`).

Environment: Python 3.14 venv at `.venv`. **Do not rebuild it.** Run `.venv/bin/python scripts/…`.
`requirements.txt` is the reproduction contract — add nothing. Tools like `cffconvert` run via
`uvx` (isolated), never into `.venv`.

### CI — it costs money

`gates.yml` runs the TESS pipeline cold and asserts all six gates (`040`, mutation-tested by
`041`). **~$0.33 per run**, dispatch + monthly cron, **no `push` trigger**. Drift beyond 5× the
A-33 sd is a NOTICE, not a failure — do not tighten it into equality. `040` passes all 11
criteria locally against the corrected G3 file (13 with `--require-paid`, incl. the repeat-noise floor); `041` 17/17.

### Release checklist — three files can silently diverge

1. **`CITATION.cff`** — bump `version` and `date-released` (UTC date). Validate with
   `uvx cffconvert --validate -i CITATION.cff`.
2. **`README.md`** — badge uses the **concept** DOI (no change); bump the example citation's
   version; add the new version DOI under *How to cite* once minted.
3. **`.zenodo.json`** — **update it whenever the description changes** (Zenodo shows it and
   ignores `CITATION.cff`). It omits `version`/`publication_date` on purpose.
Then: annotated tag → push the tag → `gh release create <tag> --verify-tag` (`--target <short
sha>` is rejected). Verify the minted record through `zenodo.org/api/records/<id>`.

### Defects found and fixed — do not re-litigate

1–33: see `git show 5b36a7a:HANDOFF_PROMPT.md` and `WORKLOG.md`. New this session:

34. **Thread race in the G3 scripts** — shared-globals swap from 8 workers. Fixed in `049` before
    KG3 ran; fixed in `036` and TESS G3 recomputed (4 calls re-asked). Verdicts unchanged; the
    412× and 0.0001 figures were artefacts. A-42, A-43.
35. **A-41's cost projection counted hosts, not distinct states** (3,843 vs 3,192). Harmless;
    spend came in 16% under.
36. **`gh release create --target <short sha>`** fails with "target_commitish is invalid" and
    creates nothing. Use an annotated tag and `--verify-tag`.

### Hypotheses tested and FAILED — do not re-raise

- "Known Planets inflate baseline B." · "The cross-platform 5×10⁻⁴ offset matters." ·
  "`832nmNo secondary sources` flips the imaging judgment." · "`false positive` is a label marker."
  · "S2b will collapse the G4 gain." · "The Kepler FPWG comments are a fair transfer test."
- **"The TESS content effect transfers to Kepler CFOP notes."** It does not (A-42).
- **"Jev is effectively deterministic within a session."** It is not (A-43).

---

## Environment notes

- `.venv`: Python 3.14.7, catboost 1.2.10, duckdb 1.5.5, pandas 3.0.6, requests 2.34.2. No
  `typesafe-sdk` — scripts use raw `urllib` + a `ThreadPoolExecutor`.
- Live TypeSafe docs: https://docs.typesafe.ai/llms.txt. `jev-1.13.0` (checked live 2026-09-22:
  active, `jev-latest` aliases it): **$0.042 / Mtok input**, 32k tokens for state + longest question.
- **Run model-vs-model comparisons on one platform** (macos/arm64 vs linux/x64 differ by 5×10⁻⁴).
- **In zsh, never `echo ====`**, and quote globs in `grep --include='*.md'` (zsh expands them).
