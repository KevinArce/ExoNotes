# ExoNotes — handoff to the next session

You are picking up the ExoNotes project. **Work from the repo, not from memory.**

---

## ⚠️ START HERE — the corpus now exists, and it is smaller than planned

**TASK A and TASK A2 are DONE** (2026-09-20). The observer-note corpus has been pulled,
asserted, persisted and baselined. Results are registered as amendments **A-13 … A-17** in
[`PREREGISTRATION.md`](./PREREGISTRATION.md) §11.2.

**The three numbers that change what you do next:**

1. **The corpus is 1,482 rows / 1,388 TIC**, not the projected ~1,814 / ~1,715 — **19% smaller**,
   near the low end of A-8's 1,200–2,140 interval. Base rate **0.5378**. Coverage **54%**, not
   the recon's 67%.
2. **The detection bar moved with it. A Jev feature now needs ≈ 0.68 univariate AUC**, not 0.65.
   The graded oracle at feature AUC **0.659 is no longer detectable** (paired CI
   [−0.0009, +0.0121]). **A question that would have cleared the old bar no longer clears.**
   MDE is now **+0.0084** (was +0.0073); dilution floor **−0.0115**; true signal required **0.0199**.
3. **G1 PASSES on the real row set:** B = **0.9051** (floor 0.85), B−A CI [+0.3977, +0.4441].
   B is **0.9051 on included rows vs 0.9197 on excluded** — D will be compared on slightly
   *harder* ground, which is the favourable direction for honesty.

**Nothing has been sent to Jev on this corpus. Jev spend is still ~$0.0046.** Every criterion is
still being fixed before the result. **Do not open that window wider.**

---

## Read first, in this order

1. **`WORKLOG.md` — read the TAIL first**, from `2026-09-20T17:05Z` onward. Append-only; the end
   is current. The TASK A entries record three defects found *during* the work that the audit
   did not anticipate.
2. **[`PREREGISTRATION.md`](./PREREGISTRATION.md) §11.2 (A-13…A-17)**, then §11.1 (A-1…A-8).
   **§11.2 overrides §11.1 overrides the body.** §2 is still provisional.
3. **[`AUDIT_01_PREFLIGHT_REVIEW.md`](./AUDIT_01_PREFLIGHT_REVIEW.md)** — still the reasoning
   behind A-1…A-8, but **two of its measurements have been superseded by the full corpus**
   (see "What audit 01 got wrong" below).
4. **`PLAN.md`** §0.5 (work logging) and §1 (guardrails) before anything else. **Treat the rest
   as a hypothesis:** twelve of its claims have been found wrong.
5. `research/05_question_design_gate.md` — how the question set was tested, and why that test
   **does not transfer**.

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

## 🚩 OPEN ITEM FOR THE USER — read before doing anything else

**TASK A and A2 are complete but UNCOMMITTED.** The previous session did not commit, by design —
it had no instruction to. Working tree as handed over:

```
 M PREREGISTRATION.md          (§11.2, amendments A-13…A-17)
 M PROVENANCE.md               (obsnotes block + manifest sha256)
 M WORKLOG.md                  (17:05Z → 18:34Z)
 M scripts/026_noise_floor.py  (additive --table flag; defaults unchanged)
?? scripts/028_obsnotes_pull.py          (new — the acquisition script)
?? scripts/030_gate_g1_obsnotes.py       (new — G1 on the obsnotes row set)
?? research/data/obsnotes_corpus_2026-09-20.json
?? research/data/gate_g1_obsnotes_2026-09-20.json
?? research/data/noise_floor_analysis_set_obsnotes_2026-09-20.json
```

**Confirm with the user, then commit.** Nothing downstream depends on it, but the work is not
durable until it is. `data/` is gitignored — the 2,573 cached responses and the DuckDB tables
are **local only**, so a clean clone re-pulls (~6 min, $0).

---

## The corpus — as measured, not as projected

**Not the TOI `Comments` field.** `download_obsnotes`, observer notes only, `Groupname != 'tfopwg'`
(in practice `Groupname IS NULL` — A-10, now asserted and holding). Rationale: `PREREGISTRATION.md` §1.

| | measured |
| :--- | ---: |
| TOI rows | **1,482** |
| unique TIC (CV groups) | **1,388** |
| base rate | **0.5378** |
| row coverage of `analysis_set` | **0.545** |
| median chars / row | **870** (vs 30 in `Comments`) |
| notes total | 6,855 over 2,573 TIC |
| `Master Disp:` / `Phot Disp:` / `Spec Disp:` in corpus text | **0 / 1,482** |

`Groupname` domain across all 6,855 notes: `'tfopwg'` (2,892) and NULL (3,963). **No third value.**

---

## What audit 01 got wrong — do not carry these forward

Audit 01 was right about the design; two of its **measurements** were 20-TIC artifacts that do
not survive the full corpus. Both matter to TASK B2.

| audit 01 said (n=20) | full corpus (n=1,482) |
| :--- | :--- |
| `TOI-\d+` fires 13/20 — "the leak is real, just differently shaped" | fires **68.4%** at **P(y=1)=0.431**, against a 0.5378 base rate. **Near-neutral. It is the weakest probe, not the strongest.** |
| P(note\|y=1) 0.80 vs P(note\|y=0) 0.53, ratio 1.51 | **0.5822 vs 0.5067, ratio 1.149** — real, but about ⅓ as strong |

**The actual leak is the Kepler-sourced note:** `ExoFOP-Kepler` / `KOI\d+` fires on **108 rows
(7.3%) at P(y=1) = 0.954**. `NEB`/`BEB` fires on 34 rows at **P(y=1) = 0.059**. And
`false positive` fires on 31 rows at **P(y=1) = 0.613** — *above* base rate, the opposite of
what the phrase implies. Full table: `WORKLOG.md` 18:34Z.

---

## State you are inheriting

- `data/exonotes.duckdb` — `toi_snapshot`, `analysis_set`, `ingest_provenance`, `ingest_stats`,
  `baseline_results`, `baseline_summary`, `noise_floor`, and **new this session:**
  **`obsnotes_raw`** (6,855 notes), **`obsnotes_text`** (per-TIC concatenated observer text),
  **`analysis_set_obsnotes`** (**the corpus** — 1,482 rows, column `notes` holds the text),
  **`obsnotes_coverage`**, **`gate_g1_obsnotes`**, **`noise_floor_obsnotes`**.
- `data/cache/obsnotes/` — **2,573 per-TIC JSON files, all valid RFC-8259.** Re-runs are free.
- `src/exonotes/questions.py` — set `2026-09-20.r4`, 8 predictive + 3 label-echo. **Provisional.**
- `src/exonotes/leakage.py` — **known inoperative on obsnotes (A-3). TASK B2 owns it.**
- Environment: Python 3.14 venv at `.venv`. **Do not rebuild it.** Run `.venv/bin/python scripts/…`.
- **Jev spend to date: ~$0.0046.**

### Defects already found and fixed — do not re-litigate
1–12: see the previous handoff's list, preserved in `WORKLOG.md` (pscomppars removed; corpus is
2,721 rows; no comment timestamps; S2 fixed; G2 dilution control; MDE; G5 regex; `toi` dropped
from state; model pinned).
13. **`etta` cannot be used for the bulk pull** — `pd.read_csv(url)` with no timeout, and ExoFOP
    throttles by withholding the body. `scripts/028_obsnotes_pull.py` uses `requests` with an
    explicit timeout against the identical URL; `--check-etta` verifies they agree.
14. **A zero-byte body is a THROTTLE, not "no notes."** A *header-only* 51-byte response is the
    genuine empty. Getting this backwards caches throttles as "this TIC has no notes" and shrinks
    the corpus silently. Three TICs were poisoned this way and recovered. `WORKLOG.md` 17:34Z.
15. **`pd.read_csv(delimiter='|')` mis-parses notes containing a literal `|`** — 2 TICs of 2,573.
    One raises `ParserError` (TIC lost); the other, where the pipe is on the *first* data line,
    makes pandas infer a MultiIndex and **silently shift every column** — `notes` becomes NULL
    and `Groupname` becomes a timestamp. `parse_pipe()` splits with `maxsplit=6` instead.
    **`etta` has the identical defect.** `WORKLOG.md` 17:52Z.
16. **HTML entities were never decoded** — `&nbsp;` 5,746 times across 71.6% of rows. Fixed in
    `plain()`; the TAG→FRAG→unescape order is load-bearing. A-17.

### Hypotheses tested and FAILED — do not re-raise
- **"Known Planets inflate baseline B."** They do not (0.9231 KP-excluded vs 0.9128 all-in).
- **"The cross-platform 5×10⁻⁴ AUC offset matters."** ~17× below the current MDE of 0.0084.
  Keep the single-platform rule as hygiene; it is not a decision threshold.

---

## Scope of the NEXT session

> **Binding order: B and B2 → C.** No step may start before its predecessor's `DONE` entry is in
> `WORKLOG.md`. **A and A2 are done.**

### TASK B — re-run Step 2.5 on observer-note text (~$0.01)

Same method as [`scripts/025_question_gate.py`](./scripts/025_question_gate.py): ~20–25 cases drawn
**verbatim** from `analysis_set_obsnotes.notes`, across the true length distribution (median 870,
IQR ~391–1,300, 95th pct ~3,324, max 41,268), each question's positive / negative / nearest
confusable, every answer inspected by eye.

**Binding constraints:**
- **Check each candidate against the ≈ 0.68 oracle bar (A-15), not 0.65.** A feature at 0.659 is
  now invisible. A question that cannot plausibly clear 0.68 is not worth a column — and every
  column you add costs ~0.0115 of dilution.
- **Blind the cases (A-9).** Sample programmatically across the length distribution and withhold
  labels until every answer is inspected. The r4 cases carried `y=` and were hand-picked.
- **Pin the model (A-5).** `MODEL = "jev-1.13.0"`, not `"jev-latest"`. Assert
  `response["model"] == MODEL` before persisting — the literal sits inside the cache key.
- **State is `{"notes": ...}` (A-4).** No `toi`.
- **Restore the two deleted questions as candidates** — `reports_on_target_detection` and
  `indicates_followup_complete` (§2.3). They were deleted for absence of support in `Comments`.
- **Watch the state size.** The 95th percentile row is ~3,300 chars and the max is ~41k. §6's
  cost projection assumed ~780. **Re-project TASK C's cost from the realised distribution before
  running it**, and truncate or the tripwire will fire.
- **Re-freeze with a new `QUESTION_SET_VERSION` and record it in §11.**

Apply the §2.4 writing rules literally, including: **when the model keeps making an inference,
name that inference and forbid it explicitly.**

Load the `typesafe-ai` skill and the live docs — this project's memory directs it. Noul supports
a structured `criteria: {true, false}`; §2.4 requires the negative case be stated and that is the
documented field for it.

### TASK B2 — re-derive the G5 clause set on observer-note text ($0 Jev)

`src/exonotes/leakage.py` fires on ~1/20 of observer-note TICs; `L1`, `L2`, `L4a`, `L4b` are dead.

**Start from the full-corpus probe table in `WORKLOG.md` 18:34Z, not from audit 01's 20-TIC
shapes** — see "What audit 01 got wrong" above. Derive the clauses, measure n and P(y=1) per
clause exactly as §5 does, **audit the marginal rows by eye**, and **register the result in §11
before TASK C.**

Keep `L5_explicit_disposition` as the tripwire: **if L5 fires on any row, the corpus filter has
failed and Step 3 stops** — a pipeline bug, not a finding. (It currently fires on **0 / 1,482**.)

### TASK C — Step 3, the full run (~$0.18, re-project first)

Only after B and B2. `PLAN.md` §6 Step 3. Async client, bounded semaphore, one request per row,
all questions per request, content-addressed cache, persist **full raw response JSON**.

- **Tripwire: if projected cost exceeds ~$0.50, stop and check the state size.** The corpus is
  smaller than planned but the text is longer — re-project from the realised distribution.
- Then evaluate G2–G6 **against the B+N and B+meta reference arms**, with ΔAUC aggregated as
  A-6 registers it.
- **Re-run `scripts/026_noise_floor.py --table analysis_set_obsnotes --groups 0 --k <final>`**
  once the feature count is frozen — A-2 and A-15 both require it. The `--k 8` numbers above are
  provisional.

---

## Environment notes

- `.venv` exists (Python 3.14.7, catboost 1.2.10, duckdb 1.5.5, pandas 3.0.6, etta 0.1.1).
- `typesafe-sdk` is **not** installed. `scripts/025_question_gate.py` uses raw `urllib`.
- Live TypeSafe docs: https://docs.typesafe.ai/llms.txt (append `.md` to any page path).
- **Run model-vs-model comparisons on one platform.** macos/arm64 and linux/x64 differ by 5×10⁻⁴.
- **`.github` CI reruns ingest + baselines only, makes no API calls**, and does **not** cover
  `analysis_set_obsnotes` or Step 3 reproducibility.
- Re-running the pull from a clean clone: `.venv/bin/python scripts/028_obsnotes_pull.py`
  (~6 min at 5 workers, $0). Stages: `repair`, `pull`, `verify`, `persist`.
