# ExoNotes — handoff to the next session

You are picking up the ExoNotes project. **Work from the repo, not from memory.**

---

## ⚠️ START HERE — two studies, in two different states

### 1. The TESS study is DONE, published and citable. Do not redo it.

All six gates pass, `RESULTS.md` is written, CI covers the gates, **v1.0.0 is on Zenodo.**

> **ΔAUC(D − B) = +0.0432, 95% CI [+0.0324, +0.0547]**, S1, `TIER_PREDICTIVE` only, paired
> bootstrap over TIC groups. **5.3× the registered MDE of +0.0082.**

| gate | result | verdict |
| :--- | :--- | :--- |
| **G1** | B = 0.9051 ≥ 0.85, CI excludes 0 | ✅ PASS |
| **G2** | ΔAUC **+0.0432** [+0.0324, +0.0547] | ✅ PASS |
| **G3** | 7/7 `TIER_PREDICTIVE` stable under paraphrase | ✅ PASS |
| **G4** | S2+S2a+S2b temporal **+0.1296** [+0.0948, +0.1670] | ✅ PASS |
| **G5** | leakage-stripped **+0.0391** [+0.0268, +0.0519] | ✅ PASS |
| **G6** | missingness ablation **+0.0425** [+0.0314, +0.0540] | ✅ PASS |

**Concept DOI: `10.5281/zenodo.22866246`** (cite this). Version DOI v1.0.0: `…22866247`.

### 2. The Kepler transfer test is FULLY PRE-REGISTERED AND PUSHED. Its paid run has NOT happened.

**Your task is to run it — and nothing else first.** Everything the run needs is registered in
[`PREREGISTRATION.md`](./PREREGISTRATION.md) **§11.10 (A-40, A-41)**, pushed at `b14a97e`
(2026-09-21T03:24Z) **before any full-corpus Kepler model call**. The only Kepler calls so far
are the question-design gate's (165 calls, $0.024).

**Jev spend to date: ~$0.698.** Working tree: one local commit (this handoff + the session-end
log) may be unpushed — check `git status -sb`; **ask before pushing it.**

---

## ⚠️ NUMBERS YOU MIGHT MISREMEMBER — ALL ARE TRAPS

1. **TESS headline is +0.0432** — not +0.0440 (the pre-A-38 cache race) and not +0.0451 (28 h of
   model drift on the first cold CI run; refused because it flatters). §11.8, A-39a.
2. **Cite the CONCEPT DOI `…22866246`**, never the version DOI the badge endpoint hands you.
3. **The Kepler corpus is CFOP observer notes, NOT the FPWG table.** `PLAN.md` §8 names the
   Certified False Positive table (`fpwg_comment`); it was obtained, measured and **withdrawn**
   (A-40 40.0): TF-IDF on it alone beat every covariate and the FPWG's own verdict matched the
   label on 98.1% of rows — a transfer test there could not come out negative. **Do not revive it.**
4. **The Kepler MDE is +0.0019 (k = 6)** — not +0.0021 (k = 7, provisional in A-40).
5. **The Kepler question set is `kepler-2026-09-21.r3`** in `src/exonotes/questions_kepler.py`.
   `questions.py` / `2026-09-20.r6` is TESS's and stays frozen.

**TESS matrix checksum** `sha256(jev_features_obsnotes)[:16] = d7b5be5675778f44` (row order is
part of it). **Kepler corpus checksum** `sha256(kepler_cfop_corpus to_csv)[:16] = f3c30d2daf460095`.
**If a rebuild does not reproduce these, stop and find out why.**

---

# THE NEXT TASK — run the Kepler study exactly as registered

```bash
.venv/bin/python scripts/048_kepler_step3_features.py --dry-run   # must say 3,843 states, ~$0.6265, 0 calls
.venv/bin/python scripts/048_kepler_step3_features.py             # THE PAID RUN, ~$0.63, tripwire $0.80
.venv/bin/python scripts/050_kepler_gates.py                      # KG2/KG4/KG5/KG6 + the 40.9 verdict, $0
.venv/bin/python scripts/049_kepler_kg3_stability.py              # KG3, ~400 calls, ~$0.07
.venv/bin/python scripts/050_kepler_gates.py                      # re-run: picks up KG3's verdict
```

**Before the paid run:** `SESSION START` + `STARTED` entries (Idempotent: yes — cached per state).
**After it, verify by output, not exit code:** `new calls` ≈ 3,843 (not 0), 0 failed,
`research/data/kepler_step3_paid_run.json` written (it is **write-once**; a later run must not
overwrite it), `kepler_jev_features` has 4,720 rows. Record the matrix checksum `048` prints.

**Then read the result through A-40 40.9's table and nothing else.** `050` computes the reading;
do not re-derive it by hand, and do not reach for a different arm if you dislike it.

| outcome | reading, registered before the run |
| :--- | :--- |
| KG2 ≥ MDE, **D beats B+meta**, KG5 (with L7) and KG6 pass | **Transfers** — a full paper becomes reasonable |
| KG2 CI includes 0, or point < +0.0019 | **Does not transfer** — a real negative: "beware: this does not transfer" |
| KG2 holds, D does **not** beat B+meta | **Transfers only as follow-up volume** — the content claim does not transfer |
| KG2 holds, KG5 fails / KG6 fails | label echo / tracks missingness — negative |
| all hold, KG4 fails | **qualified** transfer — say so in the first sentence |

### Three things you must say next to the result, because they were known before it

1. **A null is the likelier outcome, and that was written down first.** B = 0.9582 and **B+meta =
   0.9839** leave 0.016 of headroom; a synthetic oracle agreeing with the label **95%** of the
   time beat B+meta by only **+0.0078** (A-41 41.6). Criterion 2 is demanding.
2. **KG5's registered arm is not comparable to TESS's G5.** L7 strips 53% of CFOP rows at
   P(y=1) = **0.362** — the *opposite* direction from TESS (0.941) — so the headline KG5 arm is
   2,036 rows at base **0.811**. The **without-L7** arm (4,402 rows, base 0.557) is the
   representative one; a verdict that flips between them is reported as a flip (A-40 40.6).
3. **S2's test set is 84% false positives** (base 0.158 vs 0.714 in train). An S2 AUC is not an
   S1 AUC.

### Then write it up

A Kepler section in `RESULTS.md` (or a sibling `RESULTS_KEPLER.md` — your call, but link it from
the README), a **§11.11 "written AFTER the result"** amendment if anything needs recording, and
the README's "What this is" section updated either way. **Both outcomes are publishable.** If
this becomes v1.1.0, run the release checklist below.

---

## Read first, in this order

1. **`WORKLOG.md` — the TAIL.** Append-only. This session's entries start at `2026-09-21T02:15Z`.
2. **[`PREREGISTRATION.md`](./PREREGISTRATION.md) §11.10 — A-40, then A-41.** The whole Kepler
   design, with every measured number and every disclosure.
3. **[`RESULTS.md`](./RESULTS.md)** §1, §8/§8a, §9 — the TESS result and its limits.
4. **`PLAN.md` §0.5 (work logging) and §1 (guardrails).**

## Mandatory working rules

Narrate every step **and** persist it to `WORKLOG.md` as you go. `STARTED` before, `DONE` /
`FAILED` / `BLOCKED` after. **Append only** — corrections go in a *new* entry. `Idempotent:
yes/no` on every `STARTED`; cumulative Jev spend on every entry that calls the API. **Never log
secrets** — the key is `TYPESAFE_API_KEY` in `.env` (gitignored).

**Take every timestamp from `date -u`.** Never estimate one — this session's did, and they ran
20 minutes ahead (corrected in the log). Append order is evidence; clock times you typed are not.

**Chain dependent commands with `&&`, never `;`.** This session a patch died on a SyntaxError,
the next commands ran anyway, a gate re-served stale cache at `0 calls, $0.00`, and a log entry
said "r3 written" when it was not. **Verify by output, not by exit path** — `0 calls` is not
evidence that anything happened (now bitten four times).

**THE REPO IS PUBLIC.** Commit as `KevinArce <iav.kevinarce@ufg.edu.sv>`. **Ask before pushing.**

---

## State you are inheriting

### Kepler (`data/kepler.duckdb` — a SEPARATE database; TESS's is never opened for write)

| table / file | what | from |
| :--- | :--- | :--- |
| `kepler_fpwg_raw` | FPWG table, 9,564 × 68, body sha `bb98aa706bc3ef4d` — **withdrawn corpus** | `042` |
| `kepler_corpus` | the withdrawn FPWG corpus, n 1,993, sha `f1f470aaf74ef3e1` | `043` |
| `data/kepler/cumulative.csv` | TAP `CUMULATIVE` snapshot 02:23Z, sha `962947427b3038a3` — **the label** | `043` |
| `data/kepler/obsnotes_bulk.txt` | ExoFOP bulk dump 02:44Z, sha `475fc5dcafd43574` | `045` |
| `kepler_cfop_notes` | 14,980 in-scope CFOP notes | `045` |
| **`kepler_cfop_corpus`** | **THE CORPUS** — 4,720 KOIs / 3,843 hosts / base 0.5750, sha `f3c30d2daf460095` | `045` |
| `kepler_step2`, `kepler_cfop_step2` | zero-cost arms; the latter now holds the **k = 6** run | `044` |
| `data/cache/gate_kepler/` | 165 gate responses (r1, r2, r3) | `047` |

Scripts **042–050** are all Kepler; each docstring says what it registers. `048`/`049`/`050` were
written **before** any Kepler feature existed and `050` was smoke-tested both ways (noise →
DOES NOT TRANSFER; 95% oracle → TRANSFERS).

`src/exonotes/leakage.py` — `KEPLER_PATTERNS` / `KEPLER_PATTERNS_NO_L7` **appended**;
`OBSNOTES_PATTERNS` untouched (still strips 368 TESS rows — verified).

### TESS (`data/exonotes.duckdb`)

`analysis_set_obsnotes` (**the corpus**, 1,482 rows / 1,388 TIC / base 0.5378),
`jev_features_obsnotes` (checksum above), and the gate tables. `data/cache/step3/` holds exactly
1,382 responses — re-runs are free. `data/` is gitignored.

Environment: Python 3.14 venv at `.venv`. **Do not rebuild it.** Run `.venv/bin/python scripts/…`.

### CI — it costs money

`.github/workflows/gates.yml` runs the TESS pipeline cold and asserts all six gates (`040`,
mutation-tested by `041`). **~$0.33 per run**, dispatch + monthly cron, **no `push` trigger**.
It asserts registered criteria, not published numbers; a drift beyond 5× the A-33 sd is a
**NOTICE, not a failure** — do not tighten it into equality. **CI does not cover Kepler.**

### Release checklist — three files can silently diverge

1. **`CITATION.cff`** — bump `version` and `date-released`. **These go stale.**
2. **`README.md`** — the badge uses the **concept** DOI and needs no change.
3. **`.zenodo.json`** — only if authorship, licence or description changed. It omits
   `version`/`publication_date` on purpose; **Zenodo ignores `CITATION.cff` when it exists.**

### Defects found and fixed — do not re-litigate

1–26: see the previous handoff's list in `git show 412012f:HANDOFF_PROMPT.md` and `WORKLOG.md`
(pscomppars; S2 group leak; dilution control; MDE; G5 regex; `toi` out of state; model pinned;
throttle-as-empty; silent pipe mis-parse; HTML entities; inoperative `Comments` clauses; drift;
the ρ = 1.000 un-patched cache; the A-38 cache race; row-order B; overwritten result JSONs;
stale `CITATION.cff`; a README claim that flattered the study). New this session:

27. **The FPWG table has no API** — TAP and the legacy API both refuse it. `042` replays the
    archive viewer's own download (`nph-tblView` → workspace → `nph-iceTbl` → `nph-iceTblDownload`).
28. **A raw-file checksum that changes on every download** — the archive stamps the download time
    into a `#` line. Checksum the header-stripped body instead (`042`).
29. **ExoFOP's comma CSV is broken by unescaped `"` inside HTML** (7 fields on only 25,395 of
    33,132 rows). Use `output=pipe` and `028.parse_pipe`; `045` cross-checks against a second,
    record-anchored parser (identical on all 33,132).
30. **Estimated log timestamps** ran ~20 min ahead of the clock. Corrected by a new entry.
31. **A `;`-chained command reported a false success** — see the working rules above.
32. **A gate passed on its own repair cases (208/208) and failed unseen text (95/103).** Holdouts
    are now part of the Kepler gate (A-41 41.1); TESS's gate never had one.
33. **L4a misfires on CFOP** — `CATALOGUE_PREFIX` carries `TRES` (the TrES survey), so TRES
    spectrograph headers ("TRES 20/21 Jun 2010") match. Recorded; the clause set is add-only.

### Hypotheses tested and FAILED — do not re-raise

- "Known Planets inflate baseline B." (0.9231 KP-excluded vs 0.9128.)
- "The cross-platform 5×10⁻⁴ offset matters." (~12× below the MDE.)
- "`832nmNo secondary sources` flips the imaging judgment." It does not.
- "`false positive` is a label marker." TESS 0.613 (A-26); Kepler 0.458 — **not stripped on either.**
- "S2b will collapse the G4 gain." It rises to +0.1296 (A-37).
- **"The Kepler FPWG comments are a fair transfer test."** They are not (A-40 40.0).

---

## Environment notes

- `.venv`: Python 3.14.7, catboost 1.2.10, duckdb 1.5.5, pandas 3.0.6, requests 2.34.2.
  `typesafe-sdk`/`aiohttp`/`httpx` are **not** installed — scripts use raw `urllib` + a
  `ThreadPoolExecutor`. **`requirements.txt` is the reproduction contract; add nothing mid-study.**
- Live TypeSafe docs: https://docs.typesafe.ai/llms.txt. `jev-1.13.0`: **$0.042 / Mtok input**,
  **32k tokens for state + longest question**, 1,200 req/min. Read `model-jaggedness/jev-1.13`
  before touching any question.
- **Run model-vs-model comparisons on one platform** (macos/arm64 vs linux/x64 differ by 5×10⁻⁴).
- **In zsh, never `echo ====`** — `=word` is command expansion. Use `echo -----`.

---

## If you would rather not run Kepler yet

- **Nothing external has checked the TESS result.** Someone else running the pipeline closes the
  gap CI cannot.
- **An RNAAS note on the leakage findings** — TESS `Comments` restates the label in 47.9% of rows;
  `pscomppars` leaks at P = 0.995; and now **Kepler's FPWG comments track the label at 98.1%** and
  `koi_comment` *is* the vetting rationale. Needs no further validation.
- **Contact ExoFOP** with the same finding, now that a DOI exists.
