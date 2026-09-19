# Handoff prompt for the next Claude Code session

Copy everything inside the box below into a fresh Claude Code session started in the
repository root.

---

```
You are picking up the ExoNotes project. Work from the repo, not from memory.

## Read first, in this order

1. `WORKLOG.md` — read the TAIL first. Steps 1 and 2 are DONE. Resume per PLAN.md §0.5.
   The entries at 23:08Z, 23:13Z and 23:20Z contain findings that change the study design.
2. `PLAN.md` — §0.5 (work logging) and §1 (guardrails) before anything else, then §2 (the
   validity threat — now backed by measurements, not fears), §3, §5, §6 Step 2.5, §7, §11.
3. `research/04_first_live_measurements.md` — how the question set was verified, and why
   that verification is NOT sufficient (see "Scope" below).

`research/01_*` and `research/02_*` are SUPERSEDED. Do not build from them.

## Mandatory working rule — step logging and resumability

This is not optional and applies to everything you do this session.

Narrate every step in your visible output, AND persist it to `WORKLOG.md` as you go — not at
the end. Write a STARTED entry BEFORE each action and a matching DONE / FAILED / BLOCKED entry
AFTER it. Append only; never edit a past entry. Format and non-negotiables: PLAN.md §0.5.

An orphan STARTED entry with no outcome is the interruption marker — it is how the session
after you knows exactly where things stopped.

Every script in `scripts/` must be safe to re-run from scratch. State `Idempotent: yes/no` on
every STARTED entry. Track cumulative Jev spend on every entry that makes API calls.

Never log secrets. The API key is in `.env` (gitignored) as TYPESAFE_API_KEY. Do not print it,
echo it, or write it to any file. THIS REPO IS GOING PUBLIC — see the publication task below.

## State you are inheriting

Steps 1 and 2 are complete and verified:
- `data/exonotes.duckdb` — tables `toi_snapshot`, `analysis_set`, `ingest_provenance`,
  `ingest_stats`, `baseline_results`, `baseline_summary`.
- Analysis set: 2,721 rows · 2,573 unique TIC · 50.3% positive · median comment 30 chars.
- Gate G1 PASSED: baseline B (numeric) 0.9154 AUC vs baseline A (prior) 0.5000.
- Baseline C (TF-IDF) 0.9691 AUC — this is LEAKAGE, not signal. See PLAN.md §2.0.
- Environment: Python 3.14 venv at `.venv`. CatBoost works on 3.14. Do not rebuild it.
- Jev spend to date: ~$0.0002.

Six defects in the original plan were found and are ALREADY FIXED in PLAN.md. Do not
re-litigate them; do not undo them:
1. `pscomppars` removed from the feature path (it predicts the label at P=0.995 vs 0.074).
2. `references_other_object` moved from TIER_PREDICTIVE to TIER_LABEL_ECHO.
3. Corpus is 2,721 rows, not ~7,000. Costs and power revised.
4. No comment timestamps exist; `download_obsnotes` has them instead.
5. Question set was verified on the wrong text length distribution.
6. Split S2 was unimplementable as written (no disposition timestamp); now uses
   `date_toi_alerted` as an explicitly weaker proxy.

## Scope of THIS session — three tasks, in this order

### TASK 1 — PLAN.md §6 Step 2.5: the question-design gate  (~$0.01)

Extend `scripts/00_smoke_test.py` into `scripts/025_question_gate.py`.

CRITICAL: draw the cases from REAL comments in `analysis_set`, NOT hand-written ones. The
previous round used 100–200-char hand-written prose; the median real comment is 30 characters.
Sample across the true length distribution, and include several of the terse fragments that
dominate the corpus (`low SNR; potential multi`, `variable host`, `centroid plot failed`).

For EACH question in PLAN.md §5, assemble its clear positive, its clear negative, and its
NEAREST CONFUSABLE. Target ~20 cases. Run them, inspect EVERY answer by eye, and fix what
fails. Budget two rounds: draft → test → revise → RE-TEST. The previous round found a 43%
defect rate on four cases; expect more on real text.

Apply the §5 writing rules literally — especially: ask what the text SAYS, never what it
IMPLIES, and when a question needs inference, DELETE it rather than reword it a third time.

### TASK 2 — `PREREGISTRATION.md`, committed BEFORE any full-corpus run (PLAN.md §7)

This is the artifact that makes the result credible. Write it, then STOP for review — do not
proceed to Step 3 in this session.

It must fix, in writing and before any result is seen:
- The final question set and `QUESTION_SET_VERSION`, with each question's tier.
- Gates G1–G6 with their exact numeric criteria. (G1 already passed — record the value.)
- The S2 temporal cutoff. PLAN.md §7 gives three measured options; PICK ONE and record it.
  Note the base-rate shift: 0.503 overall vs ~0.63 in the recent slice.
- The exact regex for the G5 leakage-stripped arm.
- The decision rule, including what a null result means and that it gets written up anyway.

THE OPEN DECISION — flag it for the user, do not decide it alone:
Should the study use the TOI `Comments` field (current, 30 chars median) or switch to
`download_obsnotes` (~80× more text, per-note timestamps, author attribution, ~2.3 h to pull)?
PLAN.md §2.2 has the measurements and the three caveats. This is a corpus-selection decision
with real trade-offs and it belongs to a human. Present it clearly and wait.

### TASK 3 — publication prep (no Jev spend)

THE REPO IS ALREADY PUBLIC: https://github.com/KevinArce/ExoNotes
Treat every commit as immediately visible. Scaffolding is done (LICENSE, CITATION.cff with the
real URL, CONTRIBUTING.md, PROVENANCE.md, requirements.txt, hardened .gitignore, README).

PLAN.md §11.6 passed 9 of 10 items before publication. Two remain:

- ITEM 10, UNVERIFIED — clean-clone reproduction. The test could not complete: ExoFOP began
  throttling this host after four full-table pulls in one day (TCP connects in 0.42 s, then
  zero bytes). Re-run it now that ExoFOP has cooled off:
      git clone https://github.com/KevinArce/ExoNotes /tmp/cc && cd /tmp/cc
      uv venv --python 3.14 .venv && VIRTUAL_ENV=.venv uv pip install -r requirements.txt
      .venv/bin/python scripts/01_ingest.py && .venv/bin/python scripts/02_baselines.py
  It passes when G1 reproduces (B ~0.9154 AUC vs A 0.5000). Until then, do not claim the repo
  is reproducible.

- ROBUSTNESS BUG, UNFIXED — `etta.download_toi()` accepts no timeout, so a withheld ExoFOP
  response hangs `01_ingest.py` forever with no output and no error. This is the FIRST command
  a new contributor runs on a public repo. Fix it: fetch the bulk CSV with
  `requests.get("https://exofop.ipac.caltech.edu/tess/download_toi.php?output=csv",
  timeout=(10, 300))` plus a bounded retry with backoff, print a clear "ExoFOP is throttling,
  retry later" message on timeout, and keep `etta` for the per-TIC endpoints.

OPEN ITEM FOR THE USER, not for you to decide: `WORKLOG.md` contains `/Users/arce/...` on four
lines, now public. It was NOT edited, because PLAN.md §0.5 is append-only and silently
rewriting history to tidy a repo is what that rule exists to prevent. If the user asks for a
redaction, record it in a NEW worklog entry rather than quietly amending the old one.

## Expected spend this session

~$0.01. Only Task 1 calls the API, on ~20 hand-inspected cases. If you are about to run the
full 2,721-row corpus, STOP — that is Step 3 and it belongs to the session after this one.

## What to report at the end

- Which questions failed the gate, what you changed, and the before/after numbers.
- Any question you DELETED, and why deletion beat rewording.
- The corpus-selection decision, presented for the user to make.
- The pre-publication checklist, item by item.
- Anything in PLAN.md that turned out to be wrong. The plan has been wrong six times already;
  treat it as a hypothesis about the data, not a specification. Log every deviation.

## Environment notes

- `.venv` exists (Python 3.14.7, catboost 1.2.10, duckdb 1.5.5, pandas 3.0.6, etta 0.1.1).
  Run scripts as `.venv/bin/python scripts/...`. Do not rebuild the venv.
- `typesafe-sdk` is NOT yet installed — Steps 1–2 needed no API calls. Install it for Task 1.
  `scripts/00_smoke_test.py` uses raw urllib and works without the SDK if you prefer.
- Live TypeSafe docs: https://docs.typesafe.ai/llms.txt (append `.md` to any page path). This
  project's memory directs that the `typesafe-ai` skill be loaded for work here.
```

---

## Why this session stops where it does

It stops at the point where the two decisions that can invalidate the whole study are due, and
both need a human:

1. **Which corpus.** `Comments` is what the plan was built on, but it is 30 characters at the
   median and cannot be temporally controlled. `obsnotes` has ~80× more text and real
   timestamps, at the cost of 2.3 hours of scraping and a worse leakage profile.
2. **The pre-registered thresholds.** These only mean something if they are fixed by someone who
   has seen the data shape and no results. That is exactly where the project now sits.

Spending on the full corpus before both are settled would be buying inference against a design
that might still change.

## Sessions after this one

| Session | Scope | Spend |
| :--- | :--- | ---: |
| ~~Previous~~ | ~~Steps 1–2: ingest + baselines~~ ✅ **done, G1 passed** | $0.00 |
| **Next** | Step 2.5 question gate + `PREREGISTRATION.md` + publication prep. Stop for review. | ~$0.01 |
| +1 | Step 3: full-corpus judging with the content-addressed cache. | ~$0.15 |
| +2 | Steps 4–5: encoding, evaluation, calibration audit, stability audit, figures. | $0.00 |
| +3 | `RESULTS.md` — which gates passed, and the answer, including if it is no. | $0.00 |

## A note on going public

`PLAN.md` §11.7 argues for publishing **now** rather than waiting for `RESULTS.md`: a
pre-registration only means anything if it is public *before* the result exists. The repo
currently contains a verified data foundation, a passing G1, two genuinely useful negative
findings, and an explicitly open headline question. That is a credible thing to publish.
