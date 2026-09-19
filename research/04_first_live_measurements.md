# First Live Jev Measurements

> **Date:** 2026-09-19 · **Model:** `jev-1.13.0` (via `jev-latest`) · **Cost:** ~$0.0001 (4 calls)
> **Script:** [`scripts/00_smoke_test.py`](../scripts/00_smoke_test.py) · **Raw:** [`data/smoke_2026-09-19.json`](./data/smoke_2026-09-19.json)
>
> **This is the first claim in this project backed by our own measurement.** Everything in
> documents 01–03 is sourced to vendor docs or third-party evaluation. This is not.

---

## 1. What was tested

Four hand-written comments in ExoFOP `Comments` style, against seven questions from `PLAN.md` §5
(5 Noul + 2 Score), one request per comment, all questions batched into that one request.

| Case | Comment | Designed to trigger |
| :--- | :--- | :--- |
| **A** | "SG1 observed 2023-04-12 in Rc. NEB detected at 1.2 arcmin NE, depth consistent with TESS signal. Target star clear. Retired as NEB." | nearby EB; alternate eclipse source |
| **B** | "V-shaped event, possible EB. Period may be 2x the reported value. Needs RV follow-up before further photometry." | ephemeris doubt |
| **C** | "Confirmed on-target by LCO 1m in zs. Depth consistent with TESS. Published as TOI-1234 b in Smith et al. 2024." | on-target detection; other-object reference |
| **D** | "period is likely correct" | near-empty control |

---

## 2. Operational findings

### 2.1 Cost model confirmed ✅

Input tokens per call: **603–645** (state ~40 tok + 7 question definitions ~580 tok).
Output tokens: 144, free, as documented.

Extrapolating to the MVP: 7,000 rows × ~630 tok = 4.4M input tokens × $0.042/MTok = **$0.185**.
The `PLAN.md` §6 estimate of ~$0.18 holds. Note the question definitions dominate the payload
~14:1 over the comment text, so **cost scales with the question set, not the corpus text.**
Adding the 7 remaining planned questions roughly doubles it — still under $0.50.

### 2.2 Latency did not match the advertised range ⚠️

Measured end-to-end: **550, 701, 1151, 1520 ms**. Advertised: 70–500ms.

Every call exceeded the advertised upper bound, the slowest by 3×. Caveats: these were cold,
sequential, single calls from a laptop over the public internet, including TLS setup, with no
connection reuse and no warm pool. This is not a careful latency benchmark and should not be
reported as one.

But it matters for planning: at ~1s/call sequential, 7,000 rows is ~2 hours. **Use the async
client with a bounded semaphore** (`PLAN.md` §6 Step 3) — this is now a requirement, not an
optimization.

### 2.3 Two-decimal probability quantization confirmed ✅

Every returned probability is quantized to 2 decimals (`0.93`, `0.01`, `0.06`, `0.37`…). This
reproduces the [jev-orderby-bench](https://github.com/yodablocks/jev-orderby-bench) finding on our
own data and confirms correction #6 in document 03 §1.4. Ranking by a raw Jev probability will
produce large tie groups. Not a problem for the MVP (features, not ranking) — but it forecloses
any ORDER BY use downstream without an explicit tiebreak.

---

## 3. Scientific findings — 3 of 7 questions are defective

This is the valuable result. On four hand-picked cases, **three questions failed in ways that
would have silently corrupted the full run.**

### 3.1 `names_alternate_eclipse_source` — FAILS (multi-hop inference) ❌

Case A states the eclipse source explicitly: *"NEB detected at 1.2 arcmin NE, depth consistent
with TESS signal. Target star clear. Retired as NEB."* The signal demonstrably originates on
another star.

**Jev returned 0.370** — leaning *no*.

Meanwhile `reports_nearby_eclipsing_binary` on the same comment returned **0.920**. So the model
correctly extracted the surface fact (*an NEB is present*) but failed the inferential step
(*therefore the eclipse is not on the target*). This is exactly the documented **indirection /
multi-hop reasoning** weakness in `model-jaggedness/jev-1.13.md`, reproduced on the first try.

**Lesson:** questions must ask what the text *says*, never what the text *implies*. The inference
belongs in Python, downstream of the extracted facts.

### 3.2 `reports_nearby_eclipsing_binary` — FAILS (over-broad) ❌

Case B says *"possible EB"* — an EB hypothesis for the target itself, with no nearby or background
source mentioned. The question asks specifically about a *nearby* EB.

**Jev returned 0.710** — a false positive. It conflated "an EB is mentioned" with "a nearby EB is
reported." The discriminating word (*nearby*) was not weighted.

Case A (genuinely an NEB) → 0.920 and Case C (no EB) → 0.050 are both correct, so the question
works at the extremes and fails precisely on the distinction it exists to make.

**Lesson:** when a question hinges on one qualifier, that qualifier must be spelled out with
concrete cues in the instructions, not left as a single adjective.

### 3.3 `expresses_doubt_about_ephemeris` — FAILS (literal reading) ❌

Case D is the control: *"period is likely correct"* — a mild endorsement.

**Jev returned 0.780** — strong doubt.

Literally defensible: "likely" *is* hedging language, and the question asked about "uncertainty."
Jev answered the question as written, which is precisely the documented **literal reading**
behaviour: *"answers the question you wrote, not the one you meant."* But scientifically it is
backwards — this comment reassures about the ephemeris, and would have entered the feature matrix
as evidence of doubt.

**Lesson:** "expresses uncertainty" is the wrong frame. Ask whether the text asserts a specific
problem, not whether it contains hedging.

### 3.4 What worked ✅

- `reports_on_target_detection`: C → 0.940, B → 0.050. Clean separation.
- `references_other_object`: C → 0.950, others ≤ 0.130. Clean.
- `evidence_depth` (Score): D → 0.97, B → 1.19, A → 2.13, C → 2.71. Correctly ordered by how much
  observation each comment describes. **The Score primitive performed best of anything tested.**
- **Confidence behaved honestly.** Case A `author_certainty` returned an exact 50/50 split between
  levels 3 and 4 with confidence 0.58 — "Retired as NEB" genuinely sits on that rubric boundary.
  Case C `evidence_depth` returned confidence 0.380 with probability spread 0.52/0.23/0.24, and
  that case genuinely is ambiguous between one facility, several, and a publication. In both cases
  low confidence tracked real rubric ambiguity rather than noise. This does **not** license
  thresholding on `confidence` (doc 03 §1.4, correction #2) — but as a *diagnostic for
  underspecified rubrics*, it earned its place.

---

## 4. Revised questions for `PLAN.md` §5

| ID | Old (defective) | Revised |
| :--- | :--- | :--- |
| `names_alternate_eclipse_source` | "Does `comment` indicate that the eclipse or transit signal originates on a star other than the target star?" | **Split into literal extraction.** "Does `comment` explicitly name or locate a specific star, other than the target, as the source of the eclipse signal — for example by giving an offset, a direction, or a designation?" Python infers "off-target" from this **plus** `reports_offset_eclipsing_binary`. |
| `reports_nearby_eclipsing_binary` → rename `reports_offset_eclipsing_binary` | "Does `comment` report a nearby or background eclipsing binary?" | "Does `comment` report an eclipsing binary at a position **offset from the target star** — described as nearby, background, NEB, a contaminating star, or at a stated angular separation? Answer no if an eclipsing binary is proposed for the target star itself." |
| `expresses_doubt_about_ephemeris` → rename `asserts_ephemeris_problem` | "Does `comment` express uncertainty about the orbital period, the epoch, or whether the ephemeris is correct?" | "Does `comment` assert a **specific problem** with the period or epoch — that it is wrong, aliased, a harmonic or multiple of the true value, or requires revision? Answer no if the text merely affirms the ephemeris, even with hedging such as 'likely' or 'probably'." |

### 4.1 Verification round — run 2026-09-19, same four cases

Raw: [`data/smoke_revised_2026-09-19.json`](./data/smoke_revised_2026-09-19.json)

| Question | Case | Before | After | Result |
| :--- | :--- | ---: | ---: | :--- |
| `reports_offset_eclipsing_binary` | B (EB on target) | 0.710 | **0.070** | ✅ fixed |
| `reports_offset_eclipsing_binary` | A (genuine NEB) | 0.920 | **0.870** | ✅ held |
| `reports_offset_eclipsing_binary` | C (no EB) | 0.050 | **0.070** | ✅ held |
| `asserts_ephemeris_problem` | D ("likely correct") | 0.780 | **0.050** | ✅ fixed |
| `asserts_ephemeris_problem` | B (period may be 2x) | 0.940 | **0.890** | ✅ held |
| `names_alternate_eclipse_source` | A (NEB at 1.2' NE) | 0.370 | **0.590** | ❌ still failing |

**Two of three repaired by rewording.** Both now separate cleanly (≥0.87 positive, ≤0.07 negative),
and adding the explicit negative case ("answer no if…") was what did the work in each.

### 4.2 `names_alternate_eclipse_source` — dropped, not reworded again

The rewrite moved it 0.370 → 0.590: a coin flip. Case A gives an angular offset *and* a compass
direction ("NEB detected at 1.2 arcmin NE"), which satisfies the revised criteria literally, yet
the model still would not commit — plausibly because no stellar *designation* is given and it is
hedging across the three cues offered.

**The correct fix is deletion.** `reports_offset_eclipsing_binary` already captures the same fact
with clean separation (0.870 / 0.070 / 0.070). The alternate-source question is redundant and
would contribute a near-0.5 noise column to the feature matrix.

**Generalizable lesson: when a question needs inference, the remedy is often not better wording
but removing it in favour of a question that asks for the underlying fact directly.** A third
rewrite attempt would have been the wrong move — two independent questions about one fact is
worse than one question that works.

---

## 5. Consequences for the plan

1. **Add a question-design gate before Step 3.** A ~20-case hand-labelled set covering each
   question's positive case, negative case, and its nearest confusable — run and inspect before
   spending anything on the full corpus. Cost: cents. This smoke test found a 43% defect rate on
   four cases; the full set will find more.
2. **`PLAN.md` §5's writing rules need one more entry:** *ask what the text says, never what it
   implies.* Finding 3.1 is a clean demonstration of why.
3. **Gate G3 (stability) is vindicated.** Three questions moved on wording alone. Paraphrase
   sensitivity is not hypothetical here — it is the dominant failure mode observed.
4. **Async client is now required**, not optional (§2.2).
5. **The `TIER_LABEL_ECHO` concern is real.** Case A's "Retired as NEB" is exactly the
   post-hoc-annotation pattern `PLAN.md` §2 warns about — a comment that restates the disposition.
   Any question reading it scores well and means nothing.

## 6. What this does *not* establish

Four hand-written comments, no labels, no ground truth, no calibration measurement. It tests
**question design**, not scientific validity. None of §1.4's out-of-distribution calibration
concerns are addressed here — those need the labelled corpus and the reliability diagrams in
`PLAN.md` §6 Step 5. The headline question — *does comment text add signal beyond numeric
columns?* — remains completely open.
