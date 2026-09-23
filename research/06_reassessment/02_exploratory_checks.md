# 02 — Exploratory checks run for this reassessment

> **Unregistered. Exploratory. Hypothesis generators, not findings.** Run 2026-09-23 (UTC) at
> **$0 of model spend**. Both scripts open `data/exonotes.duckdb` and `data/kepler.duckdb`
> **read-only** and write nothing to `data/`. The second makes two public NEA TAP reads.
> Every CV, CatBoost and bootstrap call is **imported unchanged** from
> [`scripts/026_noise_floor.py`](../../scripts/026_noise_floor.py), as `035` does.
>
> **None of these numbers changes a registered verdict and none of them should be cited as a
> result of this study.** About twenty arms were run in sequence, and later arms were chosen after
> earlier ones had been seen. No correction for multiple comparisons was applied, and this is
> exactly the forking path that [`PREREGISTRATION.md`](../../PREREGISTRATION.md) exists to close.
> Where a check matters, [`05_project_proposals.md`](./05_project_proposals.md) says how to
> register it properly.

**Bootstrap:** 2,000 paired resamples over TIC groups (the registered analysis uses 10,000).
**Sanity check:** the recomputed G2 lands at **+0.0432 [+0.0320, +0.0549]**, against the
registered +0.0432 [+0.0324, +0.0547]. The machinery reproduces the published value, and the
interval is equal within resampling noise.

---

## E1 — What the positive class is made of

| TFOPWG | n | y |
| :--- | ---: | :---: |
| FP | 634 | 0 |
| CP | 486 | 1 |
| **KP** | **311** | 1 |
| FA | 51 | 0 |

**39% of positives are KP**, planets known before TESS. Predicting that a known planet is a
planet is not the interesting case, so E4 removes them.

---

## E2 — Bag-of-words *with* the catalogue columns

**Why:** the README says *"TF-IDF on the same text scores 0.8766 — below the numeric baseline's
0.9044 … Whatever the signal is, bag-of-words does not reach it."* Baseline C is **text only**,
with no numeric columns. That makes it a comparison between two single-modality models. It does
not test whether bag-of-words adds what Jev adds when both sit on top of B.

**Arm:** B plus one stacked column, the out-of-fold score of C's own TF-IDF + logistic pipeline
(same configuration as `035`). Within each outer fold, the column is produced by an inner
GroupKFold(5) on the training rows, then refit on the whole training fold to score the test rows.
No label crosses a fold boundary.

| arm | full S1 arm (n 1,482) | G5 leakage-stripped arm (n 1,114, base 0.426) |
| :--- | :--- | :--- |
| D − B (registered) | +0.0432 [+0.0320, +0.0549] | +0.0391 [+0.0268, +0.0516] |
| **B+TFIDF − B** | **+0.0345** [+0.0237, +0.0457] · AUC 0.9388 | **+0.0244** [+0.0146, +0.0341] · AUC 0.9173 |
| **D − B+TFIDF** | **+0.0088** [+0.0004, +0.0174] | **+0.0147** [+0.0042, +0.0246] |
| D+TFIDF − B+TFIDF | +0.0165 [+0.0101, +0.0229] · AUC 0.9554 | — |

**Reading.**

- **Bag-of-words reaches 80% of the headline gain (full arm) and 62% of the leakage-stripped
  gain.** It needs only a numeric baseline to sit on. The README's sentence is not supported by
  the evidence it cites. What the evidence supports is narrower: *structured judgments add a
  modest increment (+0.009 to +0.017) beyond bag-of-words.* On the full arm the lower bound of
  that increment is +0.0004.
- On the full arm the TF-IDF column can read label-echo tokens (C is "leakage by construction").
  The G5 column is the fair one, and there Jev's increment over bag-of-words is clearer,
  +0.0147 [+0.0042, +0.0246].
- **An asymmetry favours Jev here.** TF-IDF learns only from in-fold labels. Jev's question
  *topics* were chosen with full-corpus label AUCs (A-19, A-23; see
  [`01`](./01_critical_assessment.md) W2). The increment over bag-of-words is about the size
  that such selection could plausibly produce. It is not evidence of selection bias. It is a
  reason to measure selection bias.

---

## E3 — A stronger catalogue baseline

**Why:** "beyond the numeric catalogue" was tested against 8 columns. The `toi` table carries
more, and **multiplicity is a textbook planet indicator** (Lissauer et al. 2012).

**Arm:** B plus `pl_insol`, `st_dist`, the number of sectors, and multiplicity (the number of
TOIs on the same TIC in `toi_snapshot`). Chosen by domain knowledge before the fit and not tuned.
`pl_insol` is partly redundant with B's columns.

| arm | ΔAUC | AUC |
| :--- | :--- | ---: |
| Bstrong − B | +0.0188 [+0.0109, +0.0269] | 0.9232 |
| **Dstrong − Bstrong** | **+0.0354** [+0.0257, +0.0454] | 0.9586 |

189 rows have multiplicity > 1, at **P(y=1) = 0.926** against 0.481 for singles.

**Reading:** the text gain **survives a stronger baseline and shrinks by about 18%**
(+0.0432 → +0.0354). This supports the claim, but the published number depends partly on
B being weak. A registered replication should use a strong B. Gaia DR3 RUWE, and the structured
ExoFOP tables in [`01`](./01_critical_assessment.md) W5, are the next columns to add.

---

## E4 — TESS-era discoveries only (KP removed)

| arm | n | base | B → D | ΔAUC |
| :--- | ---: | ---: | :--- | :--- |
| D − B, CP vs FP+FA | 1,171 | 0.415 | 0.9015 → 0.9356 | **+0.0342** [+0.0225, +0.0467] |

**Reading:** the gain is not carried by pre-known planets. The case that matters scientifically,
TESS candidates that later resolve, keeps about 80% of it.

---

## E5 — A residual label channel the TESS clause set does not strip

The Kepler clause set added `K10` because *"a `Kepler-N` system name exists only once a planet in
the system has been confirmed"*. The TESS set (`OBSNOTES_PATTERNS`) has no general analogue:
`L4a` is anchored `^…$`, and observer notes are never *just* a designation.

| inside the registered G5 arm (n 1,114) | rows | P(y=1 \| match) | P(y=1 \| no match) |
| :--- | ---: | ---: | ---: |
| survey system name (`WASP-`, `HAT-P-`, `KELT-`, `K2-`, `Kepler-`, `NGTS-` …) | 17 | **0.941** | 0.418 |
| planet-letter designation (`… b`) | 12 | 0.917 | 0.421 |

Re-fitting G5 with those 17 rows also removed gives **+0.0383 [+0.0262, +0.0517]**
(n 1,097, B 0.8936 → D 0.9319).

**Reading:** the channel is real, near-deterministic and small. It does not drive the result.
It belongs in a future TESS clause set by the same rule that produced `K10`.

---

## E6 — Which features carry the gain beyond follow-up volume?

**Why:** on TESS, D beat B+meta by +0.0220. On Kepler, D lost to B+meta. If "content beyond
volume" is spread evenly across the features, that disagreement is hard to explain. If it sits
in a few features, the explanation may be simple.

| feature family added to B | vs B | vs **B+meta** (AUC 0.9256) |
| :--- | :--- | :--- |
| imaging (2): `imaging_reports_no_companion`, `imaging_reports_companion_present` | +0.0221 [+0.0141, +0.0312] | **+0.0009 [−0.0077, +0.0089]** |
| **spectroscopy + evolved (3):** `spectroscopy_indicates_nonplanetary_companion`, `spectroscopy_consistent_with_planet`, `host_star_described_as_evolved` | +0.0342 [+0.0245, +0.0446] | **+0.0130 [+0.0025, +0.0233]** |
| closure + certainty (2): `followup_reported_concluded`, `author_certainty` | +0.0071 [+0.0010, +0.0135] | **−0.0141 [−0.0210, −0.0077]** |
| all 7, **plus** meta (D+meta − B+meta) | — | +0.0277 [+0.0186, +0.0369] |

**Reading.**

- **The imaging features add nothing that note count, length and authorship do not already
  give.** The part of the TESS result that survives the volume control is carried by the
  **three spectroscopy / evolved-host features**, which in practice are TRES reconnaissance
  spectroscopy conclusions.
- `D+meta − B+meta` (+0.0277) confirms, on TESS, that text adds beyond volume even when both are
  in the model. **This arm was never registered on TESS. On Kepler it must not be run without a
  registration first, as `RESULTS_KEPLER.md` §4 already says.** It is reported here only
  because the question "does content add beyond volume?" is logically D+meta vs B+meta. The
  registered comparison, D vs B+meta, only approximates it (see
  [`01`](./01_critical_assessment.md) W6).
- The families have different k, so their dilution costs differ. The k-matched B+N floors were
  not measured, and the ranking should be read with that in mind.

---

## E7 — Are the features volume proxies?

Spearman ρ between each feature and follow-up volume.

**TESS** (`jev_features_obsnotes`, n 1,482):

| feature | log chars | n notes | n authors | P(p > 0.5) |
| :--- | ---: | ---: | ---: | ---: |
| `imaging_reports_no_companion` | +0.16 | +0.30 | **+0.51** | 0.265 |
| `imaging_reports_companion_present` | **+0.41** | +0.37 | +0.27 | 0.109 |
| `spectroscopy_indicates_nonplanetary_companion` | +0.05 | +0.04 | +0.04 | 0.176 |
| `spectroscopy_consistent_with_planet` | +0.14 | +0.16 | +0.15 | 0.138 |
| `host_star_described_as_evolved` | +0.12 | +0.07 | +0.02 | 0.241 |
| `followup_reported_concluded` | +0.33 | +0.18 | −0.09 | 0.565 |
| `author_certainty` | −0.26 | −0.29 | −0.27 | — |

**Kepler** (`kepler_jev_features`, n 4,720):

| feature | log chars | n notes | n authors | P(p > 0.5) |
| :--- | ---: | ---: | ---: | ---: |
| `imaging_reports_no_companion` | +0.24 | +0.02 | +0.22 | 0.635 |
| `imaging_reports_companion_present` | +0.50 | **+0.65** | +0.45 | 0.444 |
| `spectroscopy_indicates_nonplanetary_companion` | +0.45 | +0.56 | +0.45 | **0.036** |
| `spectroscopy_reports_no_binary_signature` | **+0.71** | **+0.72** | **+0.73** | 0.179 |
| `recon_reported_concluded` | +0.62 | +0.54 | +0.66 | 0.109 |
| `author_certainty` | +0.14 | −0.08 | +0.11 | — |

**Reading.** The TESS content features that beat volume in E6 are nearly uncorrelated with
volume (|ρ| ≤ 0.16). **Every Kepler content feature except the no-companion imaging question is
moderately to strongly volume-correlated**, up to ρ 0.73. The Kepler feature most like TESS's
strongest one (`spectroscopy_indicates_nonplanetary_companion`) fires on **3.6%** of rows, against
17.6% on TESS, and the evolved-host question was retired for low prevalence (2.2%). This is
consistent with, though it does not prove, the reading that **Kepler failed the content test
because the corpus lacks the content that carried TESS**, not because the method does not
transfer. [`01`](./01_critical_assessment.md) §4 and P5 in
[`05`](./05_project_proposals.md) state it as a testable hypothesis.

---

## E8 — How much observer text post-dates the label?

"Anticipating expert consensus" would be undermined if most of the text were written after the
disposition. There is no disposition timestamp, so two loose proxies were used.

| proxy | coverage | share of notes after it | share of characters after it |
| :--- | :--- | ---: | ---: |
| `Lastmod` of the TFOPWG note carrying `Master Disp:` (an **upper** bound on disposition time; the 2020-09-18 bulk-migration stamps are excluded) | 3,513 notes · 1,131 TIC | **4.6%** (y=1 4.4%, y=0 4.8%) | 3.2% |
| CP rows only: note year > `pscomppars.disc_year` | 864 notes · 353 TIC | **8.1%** | 6.4% |

**Reading.** Both proxies say that most observer text predates the verdict, which supports the
study's framing. Both are loose. `Lastmod` is last-modified, and the TFOPWG proxy is an upper
bound, so the true post-disposition share is **at least** these values and possibly much higher.
Only a prospective design removes the question; see P1.

---

## E9 — The label mechanism differs between the missions

`pscomppars.rv_flag`, read through a live NEA TAP query on 2026-09-23 and **not audited by hand**:

| confirmed planets in each corpus | matched | `rv_flag = 1` | `ttv_flag = 1` |
| :--- | ---: | ---: | ---: |
| TESS CP hosts (analysis set) | 353 | **0.762** | — |
| Kepler CONFIRMED KOIs (CFOP corpus) | 2,665 of 2,714 | **0.047** | 0.134 |

**Reading.** TESS confirmations mostly run through radial-velocity follow-up, and that
follow-up process is what the observer notes document. Kepler's mostly run through statistical
validation (Rowe et al. 2014; Morton et al. 2016), which does not pass through the CFOP recon
prose. If the label is not generated by the process the text records, text should add little
beyond how much follow-up happened. That matches what Kepler shows. **This is a hypothesis
fitted after the result and is labelled as one.** P5 is the registered test.

---

## E10 — The text contradicts the catalogue's stellar parameters

| | |
| :--- | ---: |
| Spearman ρ(`host_star_described_as_evolved`, TIC `st_logg`) | −0.61 |
| rows called evolved in words (p > 0.5) | 357 |
| … of which TIC `st_logg` ≥ 4.1 (dwarf-like) | **148 (41%)** |
| P(y=1) among those 148 / among evolved with log g < 4.1 | 0.426 / 0.317 |

**Reading.** For about four in ten hosts that a spectroscopist described as evolved, the input
catalogue says dwarf. Either the words or the catalogue is wrong, and a wrong stellar radius
propagates straight into the planet radius. This is the most concrete instance of *"information
that never reaches the structured catalogue"* in the corpus. It can be adjudicated with Gaia DR3
and with the stellar parameters uploaded to ExoFOP. See P7.

---

## Appendix — reproducing these numbers

Run from the repository root, with the project venv, after the published pipeline has built
both databases. Each script writes one JSON file next to itself, so **save the scripts outside
the repository** or delete the JSON afterwards. The code below is what ran. The only change is
that `ROOT` was an absolute local path and is now the working directory.

```bash
.venv/bin/python /path/outside/repo/explore_reassessment.py     # ~1 min, $0
.venv/bin/python /path/outside/repo/explore_reassessment_2.py   # ~2 min, $0, 2 NEA TAP reads
```

<details>
<summary><code>explore_reassessment.py</code> (E1–E5, E8 first proxy, E10)</summary>

```python
"""Exploratory, UNREGISTERED checks for the reassessment (research/06_*). $0, no API calls."""
import importlib.util, json, pathlib, re, sys, warnings
import duckdb, numpy as np, pandas as pd
from scipy.stats import spearmanr
warnings.filterwarnings("ignore")

ROOT = pathlib.Path(".").resolve()          # run from the repository root
spec = importlib.util.spec_from_file_location("nf", ROOT / "scripts" / "026_noise_floor.py")
nf = importlib.util.module_from_spec(spec); spec.loader.exec_module(nf)
sys.path.insert(0, str(ROOT / "src"))
from exonotes.leakage import OBSNOTES_PATTERNS
from exonotes.questions import TIER_PREDICTIVE

N_BOOT = 2000
PRED = list(TIER_PREDICTIVE)
out = {}

con = duckdb.connect(str(ROOT / "data" / "exonotes.duckdb"), read_only=True)
df = con.execute("""
    select a.*, f.* exclude (tic_id, toi)
    from analysis_set_obsnotes a
    join jev_features_obsnotes f on f.toi = cast(a.toi as varchar)
    order by a.toi""").df()
df = df.loc[:, ~df.columns.duplicated()].reset_index(drop=True)
snap = con.execute("select tic_id, toi from toi_snapshot").df()
raw = con.execute("select tic_id, username, groupname, lastmod, notes_text, is_tfopwg from obsnotes_raw").df()
con.close()

y = df.y.astype(int).to_numpy(); groups = df.tic_id.to_numpy()
Xnum = df[nf.NUMERIC].apply(pd.to_numeric, errors="coerce")
Xpred = df[PRED].apply(pd.to_numeric, errors="coerce")
print(f"n={len(df)} TIC={df.tic_id.nunique()} base={y.mean():.4f}")

def cmp(PB, PD, label, yy=y, gg=groups):
    b, d = nf.score(PB, yy), nf.score(PD, yy)
    lo, hi, se = nf.paired_group_bootstrap(PB, PD, yy, gg, N_BOOT)
    print(f"  {label:<44} base={nf.score(PB,yy):.4f} arm={d:.4f} d={d-b:+.4f} [{lo:+.4f},{hi:+.4f}]")
    return dict(base=b, arm=d, dauc=d - b, lo=lo, hi=hi)

def fit(X, yy=y, gg=groups):
    return nf.oof_by_repeat(X.reset_index(drop=True), yy, gg)

# ---------------------------------------------------------------- 1. descriptive
print("\n[1] label composition:", df.tfopwg_disp.value_counts().to_dict())

NAME = re.compile(r"\b(?:WASP|HAT-P|HATS|KELT|XO|TrES|Qatar|NGTS|WTS|CoRoT|K2|Kepler|MASCARA|KPS|"
                  r"HIP|HD|GJ|LHS|LTT|TOI)-?\s?\d+\s?[A-C]?\s?[b-h]\b")
SURVEY = re.compile(r"\b(?:WASP|HAT-P|HATS|KELT|XO|TrES|Qatar|NGTS|WTS|CoRoT|K2|Kepler|MASCARA|KPS)-\d+")
leaky = df.notes.fillna("").map(lambda s: any(rx.search(s) for rx in OBSNOTES_PATTERNS.values()))
g5 = df[~leaky]
for nm, rx in [("planet-letter designation", NAME), ("survey system name", SURVEY)]:
    m = g5.notes.fillna("").map(lambda s: bool(rx.search(s)))
    print(f"[1b] G5 arm rows with {nm}: {m.sum()} of {len(g5)}  P(y=1|match)={g5.y[m].mean():.3f}"
          f"  P(y=1|no match)={g5.y[~m].mean():.3f}")
    out[f"g5_{nm}"] = dict(n=int(m.sum()), of=len(g5), p_match=float(g5.y[m].mean()),
                          p_nomatch=float(g5.y[~m].mean()))

vol = pd.DataFrame({"log_chars": np.log1p(df.n_chars), "n_notes": df.n_notes_obs, "n_authors": df.n_authors})
print("[1c] Spearman(feature, volume):")
out["volume_rho"] = {}
for f in PRED:
    r = {v: float(spearmanr(df[f], vol[v], nan_policy="omit")[0]) for v in vol}
    out["volume_rho"][f] = r
    print(f"   {f:<48} " + "  ".join(f"{k}={v:+.2f}" for k, v in r.items()))

lg = pd.to_numeric(df.st_logg, errors="coerce")
ev = df.host_star_described_as_evolved
dw = (lg >= 4.1)
print(f"[1d] rho(evolved, logg)={spearmanr(ev, lg, nan_policy='omit')[0]:+.2f};"
      f" rows called evolved (p>0.5) whose TIC logg>=4.1: {int(((ev>0.5)&dw).sum())} of {int((ev>0.5).sum())};"
      f" P(y=1) among them {df.y[(ev>0.5)&dw].mean():.3f} vs evolved&logg<4.1 {df.y[(ev>0.5)&~dw&lg.notna()].mean():.3f}")
out["evolved_vs_logg"] = dict(n_evolved=int((ev > 0.5).sum()), n_evolved_dwarf_logg=int(((ev > 0.5) & dw).sum()),
                              p_y1_evolved_dwarf=float(df.y[(ev > 0.5) & dw].mean()))

tf = raw[raw.is_tfopwg & raw.notes_text.fillna("").str.contains("Master Disp", case=False)].copy()
tf["lastmod"] = pd.to_datetime(tf.lastmod)
tf = tf[~tf.lastmod.dt.strftime("%Y-%m-%d %H").eq("2020-09-18 12")]
tproxy = tf.groupby("tic_id").lastmod.max()
obs = raw[raw.groupname.isna()].copy(); obs["lastmod"] = pd.to_datetime(obs.lastmod)
obs = obs[obs.tic_id.isin(df.tic_id)]
obs = obs.merge(tproxy.rename("t_disp"), left_on="tic_id", right_index=True, how="inner")
obs["after"] = obs.lastmod > obs.t_disp
lab = df.groupby("tic_id").y.max()
obs["y"] = obs.tic_id.map(lab)
print(f"[1e] observer notes with a usable disposition-time proxy: {len(obs)} on {obs.tic_id.nunique()} TIC;"
      f" share whose lastmod is AFTER it: {obs.after.mean():.3f}"
      f" (y=1: {obs.after[obs.y==1].mean():.3f}, y=0: {obs.after[obs.y==0].mean():.3f})")
chars_after = (obs.notes_text.str.len() * obs.after).sum() / obs.notes_text.str.len().sum()
print(f"     share of observer-note CHARACTERS after the proxy: {chars_after:.3f}")
out["post_disp"] = dict(n_notes=len(obs), n_tic=int(obs.tic_id.nunique()), share_after=float(obs.after.mean()),
                        share_after_y1=float(obs.after[obs.y == 1].mean()),
                        share_after_y0=float(obs.after[obs.y == 0].mean()), chars_after=float(chars_after))

# ---------------------------------------------------------------- 2. model arms
print("\n[2] exploratory arms (S1, registered CatBoost, paired bootstrap %d over TIC):" % N_BOOT)
PB = fit(Xnum); PD = fit(pd.concat([Xnum, Xpred], axis=1))
out["G2_recheck"] = cmp(PB, PD, "D - B (G2 recomputed, sanity)")

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GroupKFold
from catboost import CatBoostClassifier
text = df.notes.fillna("").to_numpy()
def tfidf_pipe():
    return make_pipeline(TfidfVectorizer(min_df=3, max_features=50_000, sublinear_tf=True),
                         LogisticRegression(max_iter=2000, C=1.0))
def stacked(Xbase, extra=None):
    P = np.zeros((nf.N_REPEATS, len(y)))
    for r, tr, te in nf.repeated_group_kfold(groups, nf.N_SPLITS, nf.N_REPEATS, nf.RANDOM_STATE):
        s_tr = np.zeros(len(tr))
        for itr, ite in GroupKFold(5).split(tr, groups=groups[tr]):
            p = tfidf_pipe().fit(text[tr][itr], y[tr][itr]); s_tr[ite] = p.predict_proba(text[tr][ite])[:, 1]
        s_te = tfidf_pipe().fit(text[tr], y[tr]).predict_proba(text[te])[:, 1]
        Xtr = Xbase.iloc[tr].copy(); Xtr["tfidf"] = s_tr
        Xte = Xbase.iloc[te].copy(); Xte["tfidf"] = s_te
        clf = CatBoostClassifier(random_seed=nf.RANDOM_STATE + r, **nf.CB).fit(Xtr, y[tr])
        P[r, te] = clf.predict_proba(Xte)[:, 1]
    return P
PBT = stacked(Xnum)
out["B+tfidf_vs_B"] = cmp(PB, PBT, "B+TFIDF(stacked) - B")
out["D_vs_B+tfidf"] = cmp(PBT, PD, "D - B+TFIDF(stacked)")
PDT = stacked(pd.concat([Xnum, Xpred], axis=1))
out["D+tfidf_vs_B+tfidf"] = cmp(PBT, PDT, "D+TFIDF - B+TFIDF (Jev beyond BoW)")

mult = snap.groupby("tic_id").toi.count()
Xs = Xnum.copy()
Xs["pl_insol"] = pd.to_numeric(df.pl_insol, errors="coerce")
Xs["st_dist"] = pd.to_numeric(df.st_dist, errors="coerce")
Xs["n_sectors"] = df.Sectors.fillna("").map(lambda s: len([t for t in str(s).split(",") if t.strip()]))
Xs["multiplicity"] = df.tic_id.map(mult).astype(float)
PS = fit(Xs)
out["Bstrong_vs_B"] = cmp(PB, PS, "Bstrong - B (+insol,dist,sectors,multiplicity)")
PDS = fit(pd.concat([Xs, Xpred], axis=1))
out["Dstrong_vs_Bstrong"] = cmp(PS, PDS, "Dstrong - Bstrong")
print(f"   multiplicity>1 rows: {(Xs.multiplicity>1).sum()}  P(y=1|multi)={y[Xs.multiplicity.to_numpy()>1].mean():.3f}"
      f"  P(y=1|single)={y[Xs.multiplicity.to_numpy()==1].mean():.3f}")

k = (df.tfopwg_disp != "KP").to_numpy()
yk, gk = y[k], groups[k]
PBk = fit(Xnum[k], yk, gk); PDk = fit(pd.concat([Xnum, Xpred], axis=1)[k], yk, gk)
out["CP_vs_FP_only"] = cmp(PBk, PDk, f"D - B, KP excluded (n={k.sum()}, base={yk.mean():.3f})", yk, gk)

m = (~leaky) & ~df.notes.fillna("").map(lambda s: bool(SURVEY.search(s)))
m = m.to_numpy(); ym, gm = y[m], groups[m]
PBm = fit(Xnum[m], ym, gm); PDm = fit(pd.concat([Xnum, Xpred], axis=1)[m], ym, gm)
out["G5_plus_names"] = cmp(PBm, PDm, f"D - B, G5 minus survey names (n={m.sum()}, base={ym.mean():.3f})", ym, gm)

(pathlib.Path(__file__).parent / "explore_results.json").write_text(json.dumps(out, indent=2, default=float))
print("\nwrote explore_results.json")
```

</details>

<details>
<summary><code>explore_reassessment_2.py</code> (E2 on the G5 arm, E6, E7 Kepler, E8 second proxy, E9)</summary>

```python
"""Second exploratory pass (UNREGISTERED, $0 model spend; two public NEA TAP reads)."""
import importlib.util, io, json, pathlib, sys, urllib.parse, urllib.request, warnings
import duckdb, numpy as np, pandas as pd
from scipy.stats import spearmanr
warnings.filterwarnings("ignore")
ROOT = pathlib.Path(".").resolve()          # run from the repository root
def load(name, file):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
nf = load("nf", "026_noise_floor.py")
g = load("g", "035_gates_g2_g6.py")
sys.path.insert(0, str(ROOT / "src"))
from exonotes.leakage import OBSNOTES_PATTERNS
from exonotes.questions import TIER_PREDICTIVE
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GroupKFold
from catboost import CatBoostClassifier

N_BOOT = 2000; PRED = list(TIER_PREDICTIVE); out = {}
con = duckdb.connect(str(ROOT / "data" / "exonotes.duckdb"), read_only=True)
df = con.execute("""select a.*, f.* exclude (tic_id, toi) from analysis_set_obsnotes a
    join jev_features_obsnotes f on f.toi = cast(a.toi as varchar) order by a.toi""").df()
df = df.loc[:, ~df.columns.duplicated()].reset_index(drop=True)
raw = con.execute("select tic_id, groupname, lastmod, notes_text from obsnotes_raw").df()
con.close()
y = df.y.astype(int).to_numpy(); groups = df.tic_id.to_numpy()
Xnum = df[nf.NUMERIC].apply(pd.to_numeric, errors="coerce")
Xpred = df[PRED].apply(pd.to_numeric, errors="coerce")
fit = lambda X, yy=y, gg=groups: nf.oof_by_repeat(X.reset_index(drop=True), yy, gg)
def cmp(PB, PD, label, yy=y, gg=groups):
    b, d = nf.score(PB, yy), nf.score(PD, yy)
    lo, hi, _ = nf.paired_group_bootstrap(PB, PD, yy, gg, N_BOOT)
    print(f"  {label:<46} base={b:.4f} arm={d:.4f} d={d-b:+.4f} [{lo:+.4f},{hi:+.4f}]")
    return dict(base=b, arm=d, dauc=d - b, lo=lo, hi=hi)

def pipe():
    return make_pipeline(TfidfVectorizer(min_df=3, max_features=50_000, sublinear_tf=True),
                         LogisticRegression(max_iter=2000, C=1.0))
def stacked(Xbase, text, yy, gg):
    P = np.zeros((nf.N_REPEATS, len(yy)))
    for r, tr, te in nf.repeated_group_kfold(gg, nf.N_SPLITS, nf.N_REPEATS, nf.RANDOM_STATE):
        s_tr = np.zeros(len(tr))
        for itr, ite in GroupKFold(5).split(tr, groups=gg[tr]):
            s_tr[ite] = pipe().fit(text[tr][itr], yy[tr][itr]).predict_proba(text[tr][ite])[:, 1]
        s_te = pipe().fit(text[tr], yy[tr]).predict_proba(text[te])[:, 1]
        Xtr = Xbase.iloc[tr].copy(); Xtr["tfidf"] = s_tr
        Xte = Xbase.iloc[te].copy(); Xte["tfidf"] = s_te
        P[r, te] = CatBoostClassifier(random_seed=nf.RANDOM_STATE + r, **nf.CB).fit(Xtr, yy[tr]).predict_proba(Xte)[:, 1]
    return P

clean = ~df.notes.fillna("").map(lambda s: any(rx.search(s) for rx in OBSNOTES_PATTERNS.values())).to_numpy()
yc, gc = y[clean], groups[clean]
Xc = Xnum[clean].reset_index(drop=True); Xpc = Xpred[clean].reset_index(drop=True)
tc = df.notes.fillna("").to_numpy()[clean]
print(f"[a] G5 arm n={clean.sum()} base={yc.mean():.3f}")
PBc = fit(Xc, yc, gc); PDc = fit(pd.concat([Xc, Xpc], axis=1), yc, gc); PTc = stacked(Xc, tc, yc, gc)
out["g5_D_vs_B"] = cmp(PBc, PDc, "G5: D - B", yc, gc)
out["g5_BT_vs_B"] = cmp(PBc, PTc, "G5: B+TFIDF - B", yc, gc)
out["g5_D_vs_BT"] = cmp(PTc, PDc, "G5: D - B+TFIDF", yc, gc)

print("[b] feature families (full S1 arm)")
PB = fit(Xnum)
M = g.meta_frame(df); PM = fit(pd.concat([Xnum, M], axis=1))
fam = {"imaging (2)": ["imaging_reports_no_companion", "imaging_reports_companion_present"],
       "spectroscopy+evolved (3)": ["spectroscopy_indicates_nonplanetary_companion",
                                    "spectroscopy_consistent_with_planet", "host_star_described_as_evolved"],
       "closure+certainty (2)": ["followup_reported_concluded", "author_certainty"]}
out["families"] = {}
for k, cols in fam.items():
    P = fit(pd.concat([Xnum, df[cols].apply(pd.to_numeric, errors="coerce")], axis=1))
    out["families"][k] = dict(vs_B=cmp(PB, P, f"B+{k} - B"), vs_meta=cmp(PM, P, f"B+{k} - B+meta"))
PDM = fit(pd.concat([Xnum, Xpred, M], axis=1))
out["Dmeta_vs_meta"] = cmp(PM, PDM, "D+meta - B+meta (never registered)")

kc = duckdb.connect(str(ROOT / "data" / "kepler.duckdb"), read_only=True)
k = kc.execute("""select c.y, c.n_notes, c.n_authors, c.n_chars, f.* exclude (kepoi_name, host)
    from kepler_cfop_corpus c join kepler_jev_features f using (kepoi_name)""").df()
kc.close()
print("[c] Kepler Spearman(feature, volume) and prevalence p>0.5")
out["kepler_volume_rho"] = {}
for f in ["imaging_reports_no_companion", "imaging_reports_companion_present",
          "spectroscopy_indicates_nonplanetary_companion", "spectroscopy_reports_no_binary_signature",
          "recon_reported_concluded", "author_certainty"]:
    r = {v: float(spearmanr(k[f], np.log1p(k[v]) if v == "n_chars" else k[v])[0]) for v in ["n_chars", "n_notes", "n_authors"]}
    out["kepler_volume_rho"][f] = dict(r, prev=float((k[f] > 0.5).mean()))
    print(f"   {f:<46} " + "  ".join(f"{a}={b:+.2f}" for a, b in r.items()) + f"  prev={(k[f]>0.5).mean():.3f}")
print("   TESS prevalence p>0.5: " + ", ".join(f"{f}={(df[f]>0.5).mean():.3f}" for f in PRED if f != "author_certainty"))

def tap(q):
    u = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?" + urllib.parse.urlencode({"query": q, "format": "csv"})
    return pd.read_csv(io.StringIO(urllib.request.urlopen(u, timeout=120).read().decode()))
ps = tap("select pl_name, tic_id, disc_year, rv_flag, ttv_flag, disc_facility from pscomppars")
ps["tic"] = pd.to_numeric(ps.tic_id.astype(str).str.replace("TIC ", "", regex=False), errors="coerce")
cp = df[df.tfopwg_disp == "CP"][["tic_id"]].drop_duplicates()
cpd = cp.merge(ps.groupby("tic").agg(disc_year=("disc_year", "min"), rv=("rv_flag", "max")),
               left_on="tic_id", right_index=True, how="left")
obs = raw[raw.groupname.isna() & raw.tic_id.isin(cpd.tic_id)].merge(cpd, on="tic_id")
obs["yr"] = pd.to_datetime(obs.lastmod).dt.year
has = obs.disc_year.notna()
after = (obs.yr > obs.disc_year)[has]
ch = obs.notes_text.str.len()[has]
print(f"[d] TESS CP observer notes with disc_year: {has.sum()} on {obs[has].tic_id.nunique()} TIC; "
      f"lastmod year > disc_year: {after.mean():.3f} of notes, {(ch*after).sum()/ch.sum():.3f} of characters")
out["cp_post_discovery"] = dict(n=int(has.sum()), share_notes=float(after.mean()), share_chars=float((ch * after).sum() / ch.sum()))
print(f"[e] TESS CP hosts in corpus with rv_flag=1: {cpd.rv.mean():.3f} (n={cpd.rv.notna().sum()})")
cum = tap("select kepoi_name, kepler_name from cumulative where koi_disposition='CONFIRMED'")
kcp = cum.merge(ps[["pl_name", "rv_flag", "ttv_flag", "disc_year"]], left_on="kepler_name", right_on="pl_name", how="left")
kin = kcp[kcp.kepoi_name.isin(set(kc_names := duckdb.connect(str(ROOT / "data" / "kepler.duckdb"), read_only=True)
          .execute("select kepoi_name from kepler_cfop_corpus where y=1").df().kepoi_name))]
print(f"    Kepler CP KOIs in corpus matched: {kin.rv_flag.notna().sum()} of {len(kin)}; rv_flag=1: {kin.rv_flag.mean():.3f};"
      f" ttv_flag=1: {kin.ttv_flag.mean():.3f}")
out["rv_flag"] = dict(tess_cp=float(cpd.rv.mean()), tess_n=int(cpd.rv.notna().sum()),
                      kepler_cp=float(kin.rv_flag.mean()), kepler_n=int(kin.rv_flag.notna().sum()))
(pathlib.Path(__file__).parent / "explore_results_2.json").write_text(json.dumps(out, indent=2, default=float))
print("wrote explore_results_2.json")
```

</details>
