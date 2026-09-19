# Contributing

## Reproducing the analysis

```bash
uv venv --python 3.14 .venv
uv pip install -r requirements.txt
.venv/bin/python scripts/01_ingest.py      # ~25 s; --refresh to re-download
.venv/bin/python scripts/02_baselines.py   # ~2 min
```

No API key is needed for either step — they make **no** model API calls. Steps 1 and 2 should
reproduce gate G1 (baseline B beats baseline A).

`data/` is gitignored. Both scripts regenerate it; `PROVENANCE.md` records the SHA256 of each
raw source so you can tell whether you pulled the same snapshot. **ExoFOP updates continuously
and the NASA Exoplanet Archive syncs from it weekly, so a later pull will not match** — that is
expected and is why the checksums, not the data, are committed.

## Working rules

Two rules make this repo what it is. Please keep them.

**1. Log every step to `WORKLOG.md` as you go.** `STARTED` before an action, `DONE`/`FAILED`/
`BLOCKED` after it. Append only — never edit or delete a past entry; corrections go in a new
entry that says what was wrong. The format is in [`PLAN.md`](./PLAN.md) §0.5. This is what makes
an interrupted session resumable and what makes the result auditable after the fact.

**2. Do not edit `PREREGISTRATION.md` after seeing results.** The gates exist to stop the build
loop from becoming a machine for overfitting. If a threshold turns out to be wrong, say so in a
new `WORKLOG.md` entry and in `RESULTS.md` — do not quietly move it.

## Scientific constraints

Before proposing changes to the modelling, read [`PLAN.md`](./PLAN.md) §1 (guardrails) and §2
(the label-echo threat). In short:

- The model is a **featurizer, never a predictor**. Its probabilities feed a validated model;
  they are never thresholded into a decision.
- **Never** reintroduce `pscomppars` into the feature path (§3.2). Membership in it predicts the
  label at P=0.995 vs 0.074.
- Questions must ask what the text **says**, never what it **implies**. Multi-hop inference is a
  documented failure mode and was the first thing to break in live testing.
- No question may require arithmetic, counting, date ordering, or numeric comparison.

## Secrets

The API key lives in `.env`, which is gitignored, and is read as `TYPESAFE_API_KEY`. Never
commit it, echo it into a log, or paste it into an issue. If one is ever exposed: **rotate it
first**, then rewrite history.
