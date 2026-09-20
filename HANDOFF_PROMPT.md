# ExoNotes — handoff to the next session

You are picking up the ExoNotes project. **Work from the repo, not from memory.**

---

## ⚠️ START HERE — the study is DONE. §9 items 1–8 are all complete.

**TASK A, A2, B, B2, C, D and E are finished.** The pipeline has run, all six gates pass,
`RESULTS.md` is written, and S2b has been applied so G4 is the registered split rather than an
approximation to it.

**The headline, as §7 defines it:**

> **ΔAUC(D − B) = +0.0432, 95% CI [+0.0324, +0.0547]**, under S1, `TIER_PREDICTIVE` only,
> paired bootstrap over TIC groups. **5.3× the registered MDE of +0.0082.**

| gate | result | verdict |
| :--- | :--- | :--- |
| **G1** | B = 0.9051 ≥ 0.85, CI excludes 0 | ✅ PASS |
| **G2** | ΔAUC **+0.0432** [+0.0324, +0.0547] | ✅ PASS |
| **G3** | 7/7 `TIER_PREDICTIVE` stable under paraphrase | ✅ PASS |
| **G4** | S2+S2a+**S2b** temporal **+0.1296** [+0.0948, +0.1670] | ✅ PASS |
| **G5** | leakage-stripped **+0.0391** [+0.0268, +0.0519] | ✅ PASS |
| **G6** | missingness ablation **+0.0425** [+0.0314, +0.0540] | ✅ PASS |

**Jev spend to date: ~$0.3539.** Everything is committed and pushed (`6beb0a1`).

---

## ⚠️ IF YOU REMEMBER ONE NUMBER FROM AN OLDER DOCUMENT, IT IS WRONG

**The headline was +0.0440 for about two hours. It is +0.0432.** A concurrency defect in
`034_step3_features.py` made the original feature matrix **irreproducible from its own cache**:
the cache was checked at the top of `call()` and written at the bottom, so 80 duplicated states
were called twice, and the in-memory result kept one response while the cache kept the other.
A per-key lock fixed it; every arm was re-run. **Every S1 shift was ≤0.0010, no verdict moved.**
Full account: `PREREGISTRATION.md` §11.8 A-38, `RESULTS.md` §8, `WORKLOG.md` 22:40Z / 22:58Z.

**Matrix checksum to verify against:** `sha256(jev_features_obsnotes)[:16] = d7b5be5675778f44`,
stable across zero-call rebuilds. **If a rebuild does not produce this, stop and find out why.**

---

## The four things that make the result hard to dismiss — and the one that undercuts it

1. **It survives the metadata control.** B+meta reaches 0.9256 (metadata *alone* adds +0.0212),
   but **D beats B+meta by +0.0220, CI [+0.0126, +0.0321]**. The prose adds beyond provenance.
2. **It survives leakage stripping in both G5 arms** (+0.0391 with `L6`, +0.0426 without), and
   **the verdict does not flip** — which A-25 committed to reporting either way.
3. **Baseline C (TF-IDF on raw text) is 0.8766, BELOW B's 0.9044.** On `Comments` it was 0.9691
   of pure label echo. Raw text alone is *weaker* than the numerics here, yet structured
   judgments over that same text add +0.0432. **Whatever D uses, TF-IDF cannot find it.**
4. **The drift caveat is measured, not argued.** Perturbing the features by the measured
   model drift moves ΔAUC by sd 0.0010; **at 10× the drift G2 still passes.** (A-33.)

**The undercut, and it must stay in the write-up:** a pre-registered prior (**A-23**) said a
null was expected, because no content probe cleared 0.68 univariate AUC by regex. **That prior
was wrong** — four of seven predictive features clear it, because the semantic judgment beats
the token proxy by 0.10–0.20 AUC. A-29 records this in full. A study that registers a prior
and then reports its falsification is doing the right thing; do not quietly drop it.

---

## Read first, in this order

1. **[`RESULTS.md`](./RESULTS.md)** — the write-up. Start at §1, then §8 (the correction and
   the reproducibility limit) and §9 (what was not done).
2. **`WORKLOG.md` — read the TAIL first**, from `2026-09-20T21:01Z` onward. Append-only.
3. **[`PREREGISTRATION.md`](./PREREGISTRATION.md) §11.8 (A-38)** — it restates every number —
   then §11.7, §11.6, §11.5, §11.4, §11.3, §11.2, §11.1.
   **§11.8 > §11.7 > §11.6 > §11.5 > §11.4 > §11.3 > §11.2 > §11.1 > body text.**
4. **`PLAN.md` §0.5 (work logging) and §1 (guardrails)** before anything else.

`research/01_*` and `research/02_*` are **SUPERSEDED**. `research/05_*` describes the
`Comments`-era gate and **does not transfer** — the obsnotes gate is `WORKLOG.md` 19:41Z/19:58Z.

## Mandatory working rule — step logging and resumability

Narrate every step in your visible output **and** persist it to `WORKLOG.md` as you go — not at
the end. `STARTED` before each action, `DONE`/`FAILED`/`BLOCKED` after. **Append only; never
edit a past entry** — corrections go in a *new* entry. Format: `PLAN.md` §0.5.

State `Idempotent: yes/no` on every `STARTED`. Track cumulative Jev spend on every entry that
makes API calls. **Never log secrets.** Key is in `.env` (gitignored) as `TYPESAFE_API_KEY`.

**Verify a fix by checking its output, not by checking that it ran.** The §11.8 defect was
caught only because a "harmless" change was checksummed instead of eyeballed. `0 calls, $0.00`
is not evidence that nothing changed.

**THE REPO IS PUBLIC:** https://github.com/KevinArce/ExoNotes
**Git identity:** commit as `KevinArce <iav.kevinarce@ufg.edu.sv>`.

---

## Scope of the NEXT session — there is no required work left

§9's definition of done is **complete**. Everything below is optional. Pick from it, or take
the project somewhere new; nothing here is blocking.

### The three real gaps, in order of how much they would strengthen the study

1. **Nothing external has checked this.** The result rests entirely on one person's pipeline.
   The highest-value next step is not another arm — it is **someone else running it**, or a
   second corpus. `PLAN.md` §8 lists the registered extensions.
2. **`.github` CI still does not cover the gates.** It reruns ingest + baselines only, makes no
   API calls, and never touches `analysis_set_obsnotes`, Step 3 or G2–G6. It **cannot** without
   either an API key in CI or the response cache committed — both are real decisions with real
   trade-offs, neither has been made. Stated in `RESULTS.md` §9 item 5.
3. **The S2 arm is noisier than its interval suggests.** One train/test split, one CatBoost fit;
   the paired bootstrap resamples test groups, not the fit. Measured: **~±0.005 of seed noise**
   (`RESULTS.md` §6a). Repeated-fit S2 aggregation would tighten it. Not registered; would be a
   new arm.

### Smaller, clearly-scoped things

- **Per-question reliability diagrams** (`PLAN.md` §9) are not produced and `RESULTS.md` §9
  item 2 explains why: no independent ground truth, and the only hand-labelled set is 27 cases.
  **Producing them would require labelling more cases**, which is a real piece of work and
  would be a genuine contribution. A-36.
- **G3's two label-echo failures** stand as failures. `contains_object_designation` fails both
  halves. **Do not relax A-8 item 11's `<` to `<=`** to clear them — that was explicitly
  declined after seeing the numbers (A-32).
- **The 27-case question gate has two accepted residual failures** (§10 item 4). Reworking the
  questions would invalidate the cache and cost ~$0.24 to rebuild.

---

## State you are inheriting

- `data/exonotes.duckdb` — `toi_snapshot`, `analysis_set`, `analysis_set_obsnotes` (**the
  corpus**, 1,482 rows / 1,388 TIC / base 0.5378), `obsnotes_raw`, `obsnotes_text`,
  `obsnotes_coverage`, `gate_g1_obsnotes`, `noise_floor_obsnotes` (**at the frozen k=7**),
  `leakage_obsnotes`, `g5_arm_obsnotes`, `jev_features_obsnotes` (1,482 × 10, checksum above),
  and **new this session: `jev_features_obsnotes_s2b`**.
- `data/cache/step3/` — **exactly 1,382 responses**, one per distinct state. `data/cache/g3/`
  holds the G3 arms. **`data/cache/s2b/` — 203 responses**, the S2b re-scores; it is kept
  separate on purpose so step3's committed count stays exact. **Re-runs are free.** `data/` is
  gitignored.
- `src/exonotes/questions.py` — **`2026-09-20.r6`**, 7 predictive + 3 label-echo. **FROZEN**;
  bumping the version invalidates the whole cache and costs ~$0.24 to rebuild.
- `src/exonotes/leakage.py` — `OBSNOTES_PATTERNS` (10 clauses) is the registered set;
  `COMMENTS_PATTERNS` is kept for provenance only.
- Environment: Python 3.14 venv at `.venv`. **Do not rebuild it.** Run `.venv/bin/python scripts/…`.
- **Jev spend to date: ~$0.3539.**

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
    apart, **0.0049** an hour apart. A cold-cache re-run lands *near* +0.0432, not on it. A-31.
    **Now quantified end-to-end (A-33):** that drift moves ΔAUC by sd 0.0010; G2 survives 10×.
20. **A too-good-to-be-true number caught a bug.** The first G3 repeat arm reported ρ = 1.000 /
    Δ = 0.0000 because it never made a call — `s3.CACHE` was not patched. `WORKLOG.md` 21:31Z.
21. **The Step 3 cache race — FIXED, and it was worse than recorded.** See the warning above
    and §11.8 A-38. A per-key lock now serialises callers per state.
22. **Two values of baseline B in the repo (0.9051 vs 0.9044) are input row order**, worth
    0.0008 AUC — ~10× below the MDE. Both reproduced exactly. A-35.
23. **§10 item 2's note-count medians (3 vs 2) were measured on the `Comments` set** and do not
    describe this corpus: medians are 2 vs 2, the effect is in the tail, and **number of authors
    is the stronger channel** (AUC 0.609 vs 0.571). The prohibition is unaffected. A-34.
24. **Two result JSONs were silently overwritten by cached re-runs**, erasing the record of the
    runs that paid. Cost fields are now `*_this_run` plus a `paid_run` block. `WORKLOG.md`
    22:18Z.

### Hypotheses tested and FAILED — do not re-raise
- **"Known Planets inflate baseline B."** They do not (0.9231 KP-excluded vs 0.9128 all-in).
- **"The cross-platform 5×10⁻⁴ AUC offset matters."** ~12× below the MDE of 0.0082.
- **"The run-together `832nmNo secondary sources` text flips the imaging judgment."** It does
  not — the clean short case scored *lower* than three glued long ones. `WORKLOG.md` 19:41Z.
- **"`false positive` is a label marker."** At full scale it fires at P(y=1)=**0.613**, *above*
  the 0.5378 base rate. Not stripped. A-26.
- **"S2b will collapse the G4 gain."** It does not — G4 rises to +0.1296. A-37.

---

## Environment notes

- `.venv` exists (Python 3.14.7, catboost 1.2.10, duckdb 1.5.5, pandas 3.0.6, matplotlib 3.11.2,
  etta 0.1.1).
- `typesafe-sdk` is **not** installed and `aiohttp`/`httpx` are **not** installed — the scripts
  use raw `urllib` with a `ThreadPoolExecutor` bound. `requirements.txt` is part of the
  reproduction contract; **do not add dependencies mid-study.**
- Live TypeSafe docs: https://docs.typesafe.ai/llms.txt (append `.md` to any page path).
  Read `model-jaggedness/jev-1.13` before writing any new question.
- **Run model-vs-model comparisons on one platform.** macos/arm64 and linux/x64 differ by 5×10⁻⁴.
- Rebuilding from a clean clone: `028_obsnotes_pull.py` (~6 min, $0) →
  `034_step3_features.py` (~7 min, ~$0.24) → `035_gates_g2_g6.py` (~2 min, $0) →
  `036_gate_g3_stability.py` (~2 min, ~$0.06) → `037_reliability.py` (~1 min, $0) →
  `038_drift_sensitivity.py` (~2 min, $0) → `039_gate_g4_s2b.py` (~1 min, ~$0.03).
