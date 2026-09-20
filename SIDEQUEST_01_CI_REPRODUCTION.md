# Side quest 01 — CI clean-clone reproduction

> **One-shot task, taken ahead of the main sequence in [`HANDOFF_PROMPT.md`](./HANDOFF_PROMPT.md).**
> **Status:** ✅ **COMPLETE — green on the first run, 2026-09-20.**
> Run [35481446612](https://github.com/KevinArce/ExoNotes/actions/runs/35481446612), 1m32s.
> **B 0.9149 AUC vs A 0.5000**, all three raw sources byte-identical to the committed checksums.
> `PLAN.md` §11.6 item 10 is **CLOSED**. The repo may now be called reproduction-verified.
> Nothing left to do here; the workflow re-runs itself weekly.
> **Cost:** $0 — no model API calls anywhere in this task.
> **Actual effort:** one workflow run, **1m32s**.

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

## Outcome — green on the first run

Run [35481446612](https://github.com/KevinArce/ExoNotes/actions/runs/35481446612), triggered by
the push, **1m32s, success**:

```
=== corpus ===
  [PASS] analysis rows within +/-25% of reference     2721 (ref 2721, band 2040-3401)
  [PASS] unique TIC > 0                               2573 (ref 2573)
  [PASS] snapshot date recorded                       2026-09-19

=== gate G1 ===
  [PASS] A (prior) sits at chance                     AUC 0.5000 (ref 0.5000)
  [PASS] B (numeric) AUC >= 0.85                      AUC 0.9149 (ref 0.9154, delta -0.0005)
  [PASS] B beats A on AUC                             0.9149 > 0.5000
  [PASS] B beats A on Brier                           0.1141 < 0.2501

REPRODUCTION VERIFIED - gate G1 reproduces from a clean build.
```

`PLAN.md` §11.6 is now **10/10**. The repo is reproduction-verified.

### The interesting part: that −0.0005 is not archive drift

The check was built expecting the archives to have moved. **They had not.** All three raw
sources came back with **byte-identical SHA256** to the committed `PROVENANCE.md`:

| source | bytes | matches committed checksum |
| :--- | ---: | :---: |
| `exofop_toi` | 3,806,771 | ✅ |
| `nea_toi` | 2,048,596 | ✅ |
| `nea_pscomppars` | 1,147,680 | ✅ |

Identical inputs, and yet **B = 0.9149 on linux/x64 against 0.9154 on macos/arm64**. The
difference is **compute nondeterminism** — floating point, threading, BLAS — not data. Within a
single platform the pipeline is exactly repeatable (the dev host reproduces 0.9154 to four
decimals on every re-run).

**This matters for G2.** The headline test is a ΔAUC with a bootstrap CI excluding zero, and
there is now a measured **~5×10⁻⁴ cross-platform noise floor** from arithmetic alone. It is small
against the ~0.08 of headroom above baseline B, but it means: **run model-vs-model comparisons on
one platform, and treat any claimed gain below ~10⁻³ as noise.** We would not have known this
without running the same inputs on two architectures.

---

## Known risks

- ~~**Python 3.14 on `ubuntu-latest`.**~~ **RESOLVED** — `catboost==1.2.10` installed cleanly from
  a wheel on linux/x64 under Python 3.14.7. `requirements.txt` is portable across both platforms
  we have now tested.
- ~~**First run may be slow.**~~ It took **1m32s** end to end, including the ExoFOP pull.
- **ExoFOP answered the runner immediately** while still refusing this host, which confirms the
  throttle is per-IP. Local development still runs off the cached `data/raw/`.
- **The badge reflects the last run, including a throttled one.** A red badge is not necessarily a
  broken repo; the run summary always says which of the two it was.
- **This does not verify Step 3 or the Jev pipeline.** It covers ingest and baselines only — the
  part with no API cost. Extending it would mean putting an API key in repository secrets and
  spending money on every run, which is not worth it for a check that runs weekly.
