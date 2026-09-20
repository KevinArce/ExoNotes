# Side quest 01 — CI clean-clone reproduction

> **One-shot task. Do this BEFORE the main sequence in [`HANDOFF_PROMPT.md`](./HANDOFF_PROMPT.md).**
> **Status:** built and locally verified 2026-09-20. **Not yet run on GitHub.**
> **Cost:** $0 — no model API calls anywhere in this task.
> **Expected effort:** one workflow run, ~10–15 min wall clock, most of it waiting.

---

## Why this exists

`PLAN.md` §11.6 item 10 — *"a clean clone reproduces, and G1 passes"* — has been the **only**
unfinished item on the pre-publication checklist for **two sessions running**. Not because
anything is broken, but because ExoFOP started throttling the development host after it pulled
the full TOI table four times in one day. The server completes the TCP handshake in ~0.4 s and
then withholds the response body:

```
curl --max-time 30 'https://exofop.ipac.caltech.edu/tess/download_toi.php?output=csv'
http=000  connect=0.403s  total=30.004s  size=0
```

Probed five times across two sessions, always the same. Meanwhile the **per-TIC** endpoints
answered normally throughout (0.7–8.0 s), which is how we know this is endpoint-specific
throttling aimed at us, not an outage.

**A GitHub runner gets a different IP on every run.** That sidesteps the throttle entirely, and
it happens to be a *better* test than the manual one: `actions/checkout` is a clean clone by
construction, `data/` is gitignored so there is no snapshot to silently fall back on, and it
re-runs on a schedule instead of once when someone remembers.

---

## What was built

| file | what it does |
| :--- | :--- |
| [`.github/workflows/reproduce.yml`](./.github/workflows/reproduce.yml) | clean clone → install pinned deps → `01_ingest.py` → `02_baselines.py` → verify |
| [`scripts/029_verify_reproduction.py`](./scripts/029_verify_reproduction.py) | the assertion, as a standalone script so it also runs locally |
| `README.md` | status badge + an honest note on what the check does and does not prove |

### The assertion tolerates drift on purpose

`PLAN.md` §11.2 is explicit that the sources drift — ExoFOP updates continuously, the NASA
Exoplanet Archive syncs weekly — so **a later pull will not match the committed checksums.**

Asserting `B == 0.9154` exactly would turn ordinary archive drift into a red build, and a check
that cries wolf is a check everyone learns to ignore. So the script asserts the **finding**, not
the bytes:

| check | criterion | reference (2026-09-19) |
| :--- | :--- | ---: |
| analysis rows | within ±25% | 2,721 |
| unique TIC | > 0 | 2,573 |
| snapshot date | recorded | 2026-09-19 |
| A (prior) at chance | \|AUC − 0.5\| ≤ 0.02 | 0.5000 |
| B (numeric) predictive | **AUC ≥ 0.85** | 0.9154 |
| G1 relation | B > A on AUC **and** Brier | 0.9154 / 0.1136 |

Baseline C is **printed but never asserted on**, with its leakage warning attached, so nobody
reads 0.9691 out of CI logs and mistakes it for a result.

Exit codes: **0** reproduced · **1** a check failed · **2** inputs missing (ingest never ran).

---

## What was verified locally, before it ever runs on GitHub

- **The assertion passes on real data** — exit 0 against the committed database.
- **The assertion can fail.** Tested against a doctored copy with `B_numeric` forced to 0.61 and
  `rows_analysis` to 300 → **exit 1**, naming both failures. A check that cannot fail is theatre.
- **Missing database** → **exit 2**, distinct from a failed check.
- **Every `run:` block is valid bash** (`bash -n` on all 7).
- **The YAML parses** and has the intended triggers, defaults, timeout and concurrency.
- **The failure classifier works in both directions**, tested against a **real** throttled ingest
  log generated on this host: a throttle log matches and reports "upstream, not a code failure";
  a `KeyError` traceback does **not** match and reports a genuine code failure.

### Two bugs were caught and fixed in the draft
1. **`python … | tee log` returns *tee's* exit code.** GitHub's implicit shell is `bash -e`
   **without** `pipefail`, so a *failed* verification would have been masked and the badge would
   have gone **green on a broken reproduction** — the exact opposite of the point. Fixed by
   declaring `shell: bash` in the job defaults, which gets `-eo pipefail`.
2. **The draft probed ExoFOP with a separate full download**, doubling our load on the archive
   that is already throttling us. Removed; `01_ingest.py` is now its own probe and its failure is
   classified afterwards.

---

## How to finish it

1. Push, then open **Actions → reproduce → Run workflow** on `master`.
   (Manual dispatch is the one that closes item 10. Do not wait for the Monday cron.)
2. Read the run summary. Three outcomes:
   - **Green** → item 10 is **CLOSED**. Update `PLAN.md` §11.6 item 10 and `WORKLOG.md`, and the
     repo may finally be described as reproduction-verified. Note the drift figures — they are
     the interesting part, not a problem.
   - **Red, with "ExoFOP unavailable/throttled"** → upstream, nothing to fix. Re-run later. Item
     10 stays open and **must not** be claimed.
   - **Red, any other reason** → a genuine defect in a fresh environment. Most likely candidates:
     a Python 3.14 wheel missing for `ubuntu-latest`, or a path assumption that only holds on the
     dev machine. Fix it — that is precisely the class of bug this check exists to surface.
3. Log the outcome in `WORKLOG.md` per §0.5 (`STARTED` before, outcome after).
4. **Then go to [`HANDOFF_PROMPT.md`](./HANDOFF_PROMPT.md)** and start TASK A (obsnotes pull).

---

## Known risks

- **Python 3.14 on `ubuntu-latest`.** Pinned to `catboost==1.2.10`, which has 3.14 wheels on this
  machine (macOS/arm64). If the Linux wheel is missing, CatBoost will try to build from source and
  probably fail. **This is a real finding, not a CI annoyance** — it would mean `requirements.txt`
  is not portable, and anyone cloning on Linux hits it too.
- **First run may be slow** — no pip cache yet, plus a ~25 s ExoFOP pull and ~2 min of CV.
- **The badge reflects the last run, including a throttled one.** A red badge is not necessarily a
  broken repo; the run summary always says which of the two it was.
- **This does not verify Step 3 or the Jev pipeline.** It covers ingest and baselines only — the
  part with no API cost. Extending it would mean putting an API key in repository secrets and
  spending money on every run, which is not worth it for a check that runs weekly.
