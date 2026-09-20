# ExoNotes — handoff to the next session

You are picking up the ExoNotes project. **Work from the repo, not from memory.**

---

## ⚠️ START HERE — the study has a result, and all five gates passed

**TASK A, A2, B, B2 and C are DONE.** The full pipeline has run. Results are registered as
amendments **A-28 … A-32** in [`PREREGISTRATION.md`](./PREREGISTRATION.md) §11.5.

**The headline, as §7 defines it:**

> **ΔAUC(D − B) = +0.0440, 95% CI [+0.0332, +0.0554]**, under S1, `TIER_PREDICTIVE` only,
> paired bootstrap over TIC groups. **5.4× the registered MDE of +0.0082.**

| gate | result | verdict |
| :--- | :--- | :--- |
| **G1** | B = 0.9051 ≥ 0.85, CI excludes 0 | ✅ PASS |
| **G2** | ΔAUC **+0.0440** [+0.0332, +0.0554] | ✅ PASS |
| **G3** | 7/7 `TIER_PREDICTIVE` stable under paraphrase | ✅ PASS |
| **G4** | S2 temporal **+0.0927** [+0.0608, +0.1264] | ✅ PASS |
| **G5** | leakage-stripped **+0.0394** [+0.0272, +0.0523] | ✅ PASS |
| **G6** | missingness ablation **+0.0425** [+0.0316, +0.0540] | ✅ PASS |

**Jev spend to date: ~$0.3201.** Everything is committed and pushed (`d23d32d`).

---

## The three things that make the result hard to dismiss — and the one that undercuts it

1. **It survives the metadata control.** B+meta reaches 0.9256 (metadata *alone* adds +0.0212),
   but **D beats B+meta by +0.0228, CI [+0.0133, +0.0329]**. The prose adds beyond provenance.
2. **It survives leakage stripping in both G5 arms** (+0.0394 with `L6`, +0.0421 without), and
   **the verdict does not flip** — which A-25 committed to reporting either way.
3. **Baseline C (TF-IDF on raw text) is 0.8766, BELOW B's 0.9044.** On `Comments` it was 0.9691
   of pure label echo. Raw text alone is *weaker* than the numerics here, yet structured
   judgments over that same text add +0.0440. **Whatever D uses, TF-IDF cannot find it.**

**The undercut, and it must stay in the write-up:** a pre-registered prior (**A-23**) said a
null was expected, because no content probe cleared 0.68 univariate AUC by regex. **That prior
was wrong** — four of seven predictive features clear it, because the semantic judgment beats
the token proxy by **0.10–0.20 AUC**. A-29 records this in full. A study that registers a prior
and then reports its falsification is doing the right thing; do not quietly drop it.

---

## Read first, in this order

1. **`WORKLOG.md` — read the TAIL first**, from `2026-09-20T20:44Z` onward. Append-only.
2. **[`PREREGISTRATION.md`](./PREREGISTRATION.md) §11.5 (A-28…A-32)**, then §11.4, §11.3, §11.2,
   §11.1. **§11.5 > §11.4 > §11.3 > §11.2 > §11.1 > body text.**
3. **`PLAN.md` §0.5 (work logging) and §1 (guardrails)** before anything else.
4. `src/exonotes/questions.py` (`2026-09-20.r6`) and `src/exonotes/leakage.py`
   (`OBSNOTES_PATTERNS`) — the two pre-registered artifacts.

`research/01_*` and `research/02_*` are **SUPERSEDED**. `research/05_*` describes the
`Comments`-era gate and **does not transfer** — the obsnotes gate is `WORKLOG.md` 19:41Z/19:58Z.

## Mandatory working rule — step logging and resumability

Narrate every step in your visible output **and** persist it to `WORKLOG.md` as you go — not at
the end. `STARTED` before each action, `DONE`/`FAILED`/`BLOCKED` after. **Append only; never
edit a past entry** — corrections go in a *new* entry. Format: `PLAN.md` §0.5.

State `Idempotent: yes/no` on every `STARTED`. Track cumulative Jev spend on every entry that
makes API calls. **Never log secrets.** Key is in `.env` (gitignored) as `TYPESAFE_API_KEY`.

**THE REPO IS PUBLIC:** https://github.com/KevinArce/ExoNotes
**Git identity:** commit as `KevinArce <iav.kevinarce@ufg.edu.sv>`.

---

## Scope of the NEXT session

### TASK D — write `RESULTS.md` (§9 item 7) — **the only thing between here and done**

§9's definition of done is items 1–8. **1–6 and 8 are complete; item 7 is not.** It calls for
`RESULTS.md` *"whatever the answer is — with reliability diagrams and CIs."*

It must contain, at minimum:
- The §7 headline **one number** with its CI, and the four things §7 says must always appear
  beside it: the **E − B** contaminated gain, **baseline C** labelled as leakage, the **G5 arm**,
  and the **S2 result with its base-rate shift stated** (train 0.4888 → test 0.6487).
- **Reliability diagrams** for B and D. Not yet produced — no script exists. Note that `PLAN.md`
  §1 forbids thresholding on Jev's `confidence`; these diagrams are for the **CatBoost**
  probabilities, which is a different thing and is fine.
- **A-29 in full.** The falsified prior belongs in the write-up, not only in the amendments.
- **A-31's reproducibility limit**, in the terms `PROVENANCE.md` already uses.
- **A-32's two G3 failures**, reported as failures.
- §10's limitations, and the fact that this is one corpus, one archive, one model version.

### TASK E — S2b, if the budget allows (~$0.18)

§4 registers **S2b**: for the S2 *training* side only, include a note iff its `Lastmod` < the
cutoff. **It was not applied** — it needs every training row's features recomputed on
time-filtered text, a second near-full-corpus run. **G4 as reported is S2 + S2a only** (A-28
says so). Doing S2b would make G4 the registered split rather than an approximation to it.
`obsnotes_raw.lastmod` carries the per-note timestamp, so the filtering itself is cheap; the
cost is the re-scoring.

### Optional — close the two loose threads

- **The Step 3 cache race.** 1,462 calls were made for 1,382 distinct states: the cache is
  checked at the top of `call()` and written at the bottom, so two workers on the same state
  both miss. Cost ~$0.013, correctness unaffected. A keyed lock fixes it. `WORKLOG.md` 20:56Z.
- **`.github` CI does not cover any of this.** It reruns ingest + baselines only, makes no API
  calls, and does **not** touch `analysis_set_obsnotes`, Step 3 or the gates.

---

## State you are inheriting

- `data/exonotes.duckdb` — `toi_snapshot`, `analysis_set`, `analysis_set_obsnotes` (**the
  corpus**, 1,482 rows / 1,388 TIC / base 0.5378), `obsnotes_raw`, `obsnotes_text`,
  `obsnotes_coverage`, `gate_g1_obsnotes`, `noise_floor_obsnotes` (**at the frozen k=7**),
  `leakage_obsnotes`, `g5_arm_obsnotes`, and **new this session: `jev_features_obsnotes`**
  (1,482 × 10).
- `data/cache/step3/` — **exactly 1,382 responses**, one per distinct state. `data/cache/g3/`
  holds the G3 arms. **Re-runs are free.** `data/` is gitignored.
- `src/exonotes/questions.py` — **`2026-09-20.r6`**, 7 predictive + 3 label-echo. **FROZEN**;
  bumping the version invalidates the whole cache and costs ~$0.24 to rebuild.
- `src/exonotes/leakage.py` — `OBSNOTES_PATTERNS` (10 clauses) is the registered set;
  `COMMENTS_PATTERNS` is kept for provenance only.
- Environment: Python 3.14 venv at `.venv`. **Do not rebuild it.** Run `.venv/bin/python scripts/…`.
- **Jev spend to date: ~$0.3201.**

### Defects found and fixed — do not re-litigate
1–16: see `WORKLOG.md` (pscomppars removed; corpus is 2,721 rows; S2 group leak; G2 dilution
control; MDE; G5 regex; `toi` dropped from state; model pinned; `etta` unusable for the bulk
pull; zero-byte body is a throttle, not "no notes"; `pd.read_csv(delimiter='|')` mis-parses
pipes **silently**; HTML entities never decoded).
17. **The `Comments`-derived G5 clauses are inoperative on obsnotes** — `L2`, `L4b`, `L5` fire
    on **0** rows. Replaced; three new channels found (`L6` archive provenance at P(y=1)=0.948,
    `L7` Kepler/K2 structured disposition fields, `L8` the DACE `Status:` line). §11.4.
18. **Six of eight r4 predictive questions had almost no support here** —
    `mentions_instrumental_artifact` had **23 rows of 1,482**. §11.3 A-19.
19. **`jev-1.13.0` drifts over time.** Byte-identical requests: mean |Δ| **0.0001** minutes
    apart, **0.0049** an hour apart. A cold-cache re-run lands *near* +0.0440, not on it. A-31.
20. **A too-good-to-be-true number caught a bug.** The first G3 repeat arm reported ρ = 1.000 /
    Δ = 0.0000 because it never made a call — `s3.CACHE` was not patched, so it was served the
    Step 3 cache. `WORKLOG.md` 21:31Z.

### Hypotheses tested and FAILED — do not re-raise
- **"Known Planets inflate baseline B."** They do not (0.9231 KP-excluded vs 0.9128 all-in).
- **"The cross-platform 5×10⁻⁴ AUC offset matters."** ~12× below the MDE of 0.0082.
- **"The run-together `832nmNo secondary sources` text flips the imaging judgment."** It does
  not — the clean short case scored *lower* than three glued long ones. `WORKLOG.md` 19:41Z.
- **"`false positive` is a label marker."** At full scale it fires at P(y=1)=**0.613**, *above*
  the 0.5378 base rate. Not stripped. A-26.

---

## Environment notes

- `.venv` exists (Python 3.14.7, catboost 1.2.10, duckdb 1.5.5, pandas 3.0.6, etta 0.1.1).
- `typesafe-sdk` is **not** installed and `aiohttp`/`httpx` are **not** installed — the scripts
  use raw `urllib` with a `ThreadPoolExecutor` bound. `requirements.txt` is part of the
  reproduction contract; **do not add dependencies mid-study.**
- Live TypeSafe docs: https://docs.typesafe.ai/llms.txt (append `.md` to any page path).
  Read `model-jaggedness/jev-1.13` before writing any new question.
- **Run model-vs-model comparisons on one platform.** macos/arm64 and linux/x64 differ by 5×10⁻⁴.
- Rebuilding from a clean clone: `028_obsnotes_pull.py` (~6 min, $0) →
  `034_step3_features.py` (~7 min, ~$0.24) → `035_gates_g2_g6.py` (~15 min, $0) →
  `036_gate_g3_stability.py` (~2 min, ~$0.06).
