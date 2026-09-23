# TypeSafe AI Jev Research Dossier

> **Comprehensive Investigation into System One Models, Machine-Native Automation, and Applications in Astrophysics & Scientific Discovery**

---

## Overview

This directory contains the complete technical research, practical use case analysis, architectural blueprints, and scientific evaluations for **Jev** (`jev-1.13.0`), the first **System One model** released by **TypeSafe AI** in September 2026.

Unlike traditional conversational LLMs, Jev is engineered specifically for **machine-to-machine decision automation**: it takes arbitrary program state (raw text or JSON) alongside typed questions, returning guaranteed type-safe values accompanied by mathematically calibrated probabilities in **70ms–500ms** at **$0.042 per million input tokens** with **free output tokens**.

---

## Document Index

```
research/
├── README.md                                    # This navigation index and executive briefing
├── 01_jev_fundamentals_and_ecosystem.md        # Architecture, RLCD, primitives, benchmarks, & general use cases
├── 02_astrophysics_and_scientific_discovery.md  # Scientific computing, exoplanets, MAST/Gaia, & discovery loops
└── 03_jev_astrophysics_evidence_based_assessment.md  # ⚠️ CRITICAL RE-ASSESSMENT — supersedes 01/02 where they conflict
```

> **2026-09-23:** a post-study critical reassessment and research roadmap is in
> [`06_reassessment/`](./06_reassessment/README.md). It changes no registered verdict.

> **⚠️ Read document 03 first.** Documents 01 and 02 contain claims that do not survive
> verification against the live TypeSafe docs and independent third-party evaluations.
> The most consequential: Jev's calibration is **not** near-zero-ECE out of distribution
> (independent measurement: ECE 0.107, 4.4× noise floor, refit temperature 2.74), and
> `confidence` is a distribution-shape statistic, **not** the probability an answer is
> correct — so the confidence-gated policy in 02 is unsound as written. Document 03
> itemizes ten corrections in §1.4.

---

### [1. Jev Fundamentals, Architecture, and Practical Applications](./01_jev_fundamentals_and_ecosystem.md)
*Core theoretical principles, API contracts, ecosystem tooling, and general industry applications:*
- **The System One Paradigm Shift**: Why RLHF conversational chatbots failed at software automation and how RLCD (Reinforcement Learning for Calibrated Decisions) enables machine-native intelligence.
- **Parallel Sampling & The Three Primitives**: Detailed breakdown of `Choice`, `Score`, and `Noul`, including sample payloads and Pydantic response structures.
- **First-Party Jaggedness & Limitations**: First-party analysis of Jev 1.13 failure modes (weak arithmetic, counting, date reasoning, and distractor context rot).
- **Tooling Landscape**: Review of official SDKs (`typesafe-sdk-python`, `typesafe-sdk-js`), database extensions (`duckdb-jev`, `pg-jev`), and community projects (`jev-belay`, `jev-ultrafast`, `kev`, `SemIf`).
- **11 Industry Application Domains**: Developer tools, software engineering, automation/agents, data engineering, DevOps, creative media, and gaming.
- **Brainstorming & Prioritization**: 8 novel architectural concepts and detailed blueprints for the top 6 open-source prototype projects (`AgentBelay`, `ColdStoragePruner`, `DuckJev-Analytics`, etc.).

---

### [2. Jev in Astrophysics, Exoplanet Research, and Scientific Discovery](./02_astrophysics_and_scientific_discovery.md)
*Rigorous scientific investigation into applying Jev to astronomical surveys, exoplanet vetting, and autonomous science systems:*
- **Scientific Computing Perspective**: Precise division of labor between classical numerical solvers (`astropy`, `scipy`, `batman`) and Jev's fast semantic decision gates.
- **Astrophysical Applications**: Vetting exoplanet transits against astrophysical false positives (eclipsing binaries, background blends), stellar classification, and radial-velocity activity disentanglement.
- **Real Astronomical Data & APIs**: Concrete access patterns for the NASA Exoplanet Archive TAP API, MAST TESS/Kepler light curves, and Gaia DR3 astrometry.
- **5 Concrete Exoplanet Research Projects**:
  1. `TESS-RoboVetter`: Autonomous Threshold Crossing Event (TCE) false-alarm vetting.
  2. `AstroHarmonizer`: Multi-catalog stellar binarity & radius contamination resolver.
  3. `TransitAnomaly-Scout`: Transit Timing Variation (TTV) & non-transiting planet hunter.
  4. `HabitableZone-Triage`: M-dwarf flaring & atmospheric retention evaluator.
  5. `RV-Followup-Prioritizer`: Real-time ground-based telescope observing scheduler.
- **Computational Scientific Discovery System**: An autonomous 10-step discovery loop combining data ingestion, anomaly detection, hypothesis formulation, MCMC modeling, and auditable research trails.
- **Concrete Prototype (`ExoJev-Vetter`)**: Full end-to-end Python implementation using `lightkurve` and `typesafe_sdk`, including statistical validation methodology (Brier score, reliability diagrams).
- **Astrophysical Verdict**: Critical evaluation answering whether Jev can transform computational astrophysics.

---

### [3. Evidence-Based Assessment: Jev for Astrophysics (Critical Re-Examination)](./03_jev_astrophysics_evidence_based_assessment.md)
*Verification pass over documents 01 and 02, with sourced corrections and a revised project set:*
- **Verified Specifications**: What holds up against `docs.typesafe.ai` (pricing, limits, primitives, endpoint) and what does not.
- **Ten Itemized Corrections**: OOD calibration collapse, `confidence` misuse, numeric-threshold questions, multi-item batching degradation (Spearman 0.932 → 0.579), two-decimal probability quantization and silent `ORDER BY` ties.
- **The Decisive Constraint**: Jev is text-only and cannot ingest a light curve — which eliminates most of the astrophysics application space and makes `TESS-RoboVetter` the *weakest* proposal, not the strongest (it competes against ExoMiner at R@P0.99 = 0.936, ExoMiner++, LEO-Vetter, and TRICERATOPS, all of which see data Jev cannot).
- **Where Jev Actually Wins**: Astronomy's unexploited *text* corpora — ExoFOP `Comments`, TFOP notes, disposition rationales, ADS abstracts, catalogue provenance.
- **Revised Prototype (`ExoNotes`)**: Semantic feature discovery over ExoFOP follow-up text, built on the official `autoresearch_feature_discovery` pattern (measured RMSE 3.09 → 1.77), with Jev as **featurizer, never predictor** — an architecture that absorbs its miscalibration.
- **Pre-registered Validation**: Group-split CV by host star, temporal and cross-mission held-out splits, per-primitive ECE with noise floor, and a mandatory paraphrase/field-order stability audit.

---

## Quick Reference: Core Jev Primitives

```python
from typesafe_sdk import TypeSafeClient, Choice, Score, Noul

client = TypeSafeClient()

# Evaluated in parallel across a single forward pass (~150ms)
response = client.system_one(
    state={"object_name": "TOI-1234.01", "snr": 18.2, "odd_even_mismatch_sigma": 0.3},
    questions={
        "classification": Choice(
            instructions="Determine candidate disposition",
            criteria={"planet": "Planetary transit", "eb": "Eclipsing binary", "noise": "Artifact"}
        ),
        "shape_quality": Score(
            instructions="Rate profile quality from V-shape to U-shape",
            criteria=["Deep V-shape", "Intermediate", "Flat U-shape floor"]
        ),
        "is_genuine_transit": Noul(instructions="Is this signal a genuine astrophysical transit?")
    }
)

# Output is type-safe. Calibration is NOT guaranteed out of distribution.
disposition = response.answers["classification"].choice        # 'planet'
confidence = response.answers["classification"].confidence    # 0.94  ← distribution SHAPE
is_real = response.answers["is_genuine_transit"].noul         # 0.96 (float in [0, 1])

# ⚠️ `confidence` is NOT P(answer is correct). Gate on `probabilities[label]`,
#    and refit calibration on your own labelled astronomical data first. See 03 §1.4.
p_planet = response.answers["classification"].probabilities["planet"]
```

> **Note on the example above:** the numeric fields (`snr`, `odd_even_mismatch_sigma`) are
> shown for illustration. In production, code should compute *and threshold* those numbers
> and pass qualitative phrasings instead — Jev "cannot reliably judge whether two values are
> near each other" (`model-jaggedness/jev-1.13.md`). See 03 §3.2.
