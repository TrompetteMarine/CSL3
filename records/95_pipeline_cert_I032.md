# I032 synthetic pipeline certification — record

Freeze: `freezes/00_freeze_I032.yaml` (base spec + AD1–AD4 + run-1 defect note),
every element committed before the run it governs. Seeds: master 132000; G1
132100; S7 132400; G2 132500; run-2 cells 132000 + 10000/20000/30000 offsets;
run-3 cells 132000 + 40000/50000 offsets (per-cell offsets in the scripts).
Scripts: `experiment/analysis/{market_generator,stats_v2,pipeline_cert,
pipeline_cert_run3,g1_recovery,g2_consistency}.py`, `analysis/power_free_s7.py`.
Records: `pipeline_cert_I032{,_calib,_run3}.csv`, `g1_recovery_I032.csv`,
`g2_consistency.csv`, `power_free_s7.csv`, with logs.

Nothing here is evidence about humans. It is evidence about whether the
preregistered pipeline does what the preregistration says on synthetic people
whose truth is known.

## Headline

**The frozen H1b fails certification in both directions, and this blocks the
preregistration as drafted.**

1. *No power at the design basis (attenuation reading).* To bring the gate down
   to the design basis θ = .592, the measurement layer must attenuate by
   a ≈ .046–.063 (the slider registers ~5% of the latent legitimacy change).
   The same factor compresses the P3 dissociation: the gate's measured P3
   recovery is −1.5 to −2.0 points and R3's is +0.6 to +0.8. The equivalence
   band δ_eq = max(5, .5σ_r) = 5 swallows both, so criterion (iii) (δ_eq below
   R3's recovery) fails in every shape. Gate verdict power for the frozen H1b
   is 0.000 under all seven measurement cells, against H1a power of .91–.96.
2. *No specificity (heterogeneity reading).* A population with **no gate in
   anyone**, made of R3 types (who carry the H1a reference effect) and R4 types
   (who decline in P3 under MODERATE), drives H1a to reject at .920. The frozen
   H1b then declares the gate confirmed in **23.0%** of replicates.

The frozen H1b is unusable either way, and the pilot cannot rescue it, because
the problem is the form of the test and not a constant.

**What survives:** H1a (E1 passes in every shape; rivals contained). The gates
G1 and G2 pass. A drop-conditioned scale-invariant H1b (H1b-SIc, frozen in AD4
before run 3) is powered under the attenuation reading and specific against the
composite. **Adopting it is an author decision** (§ Author decisions in the
closing report); it is not substituted into the prereg here.

## Gates and expected outcomes (scorecard, verbatim)

| ID | Expectation (frozen) | Result | Verdict |
|---|---|---|---|
| G2 / E8 | pipeline WMW = engine within ±.02 at S1/S2/S6 × θ=.592 × N=320 | rates .9320/.8970/.8915 vs record .922/.905/.881 (|dev| .010/.008/.0105); per-draw agreement 1.000 | **PASS** |
| G1 / E5 | r(ρ̂, ρ) ≥ .7 on market skin, app windfall semantics, task-v3 geometry; I003 bias profile reproduced | r = .914 (60/60 fitted); χ r = .619 (I003 .62); τF +3.0% [−3.2, +10.5]; ν_R −23.4% [−35.0, −11.6] excluded as in I003; **ν_F −7.0% [−15.4, +1.0]** (I003 +1.5%): CI still covers 0, sign flipped | **PASS** (ν_F shift reported) |
| E1 | gate H1a power ≥ .90 at θ=.592, N=320, every shape | M1 .911, M2 .944, M3 .945, M4 .934, M5 .963, M6 .938 (360 recruited); anchoring variant .944. MC SE ≤ .009 | **PASS** |
| E2 | R1-global and R4: P(H1a rejects) ≤ .005 + 2 MC SE (.0095) | R1-global M2 .000, M6 .000 (θ̂ .220/.225, reversed); R4 M2 .002, M6 .004 (θ̂ .500) | **PASS** |
| E3 | R3: P(verdict "gate confirmed") ≤ .0095, every shape | frozen verdict .000 in all six (H1a rejects R3 at .145–.243, θ̂ .535–.543) | **PASS — but vacuous**: criterion (iii) fails for every generator, so the frozen H1b confirms nothing for anyone |
| E4 | gate: frozen two-sided TOST FAILS; repair (one-sided non-superiority) passes ≥ .90 | TOST pass rate (given H1a) **1.000** in every shape; non-superiority 1.000; both verdicts 0.000 via (iii) | **FAIL as predicted — the pre-run prediction was wrong.** It reasoned in latent units (−40) and missed the calibration's compression of P3 |
| E9 (AD3) | gate H1b-SI verdict power ≥ .80, every shape, attenuation reading | M1 .916, M2 .967, M3 .943, M4 .930, M5 .945, M6 .931 | **PASS** |
| E10 (AD3) | R3 H1b-SI verdict ≤ .0095, every shape | .000 in all six (R3 normalized recovery .674–.732 > κ = .25) | **PASS** |
| E13 (AD4) | composite R3+R4 (no gate): H1b-SIc false positives ≤ .005 + 2 SE (.0113 at B=500) | **.000** (H1a .920; R3 share .5595) | **PASS** |
| — (AD4, reported) | composite: frozen H1b and H1b-SI false positives | frozen **.230**; H1b-SI κ=.25 **.042**; κ=0 .010; κ=.40 .164 | vulnerability measured: frozen and unconditional forms are **not specific** |
| E11/E14 (AD3/AD4) | mixtures gate+R4, gate+R3: diagnostic | gate+R4 (gate share .5765, a=1): H1a .948; **frozen H1b .000**; H1b-SI .948; H1b-SIc .948. gate+R3: **INFEASIBLE**, θ(share 0) = .731, θ(share 1) = .764, so .592 is unreachable | diagnostic. The frozen H1b has zero power at **full scale** too: the gate's real P3 decline (≈ −32 latent) lies outside ±δ_eq. With R3 as the non-gate type, the heterogeneity reading cannot produce the design basis at all |
| E12 (AD3) | pure R3 at a=1: frozen and SI verdicts ≤ .0113 | H1a **1.000** (pure R3 at full scale: θ ≈ .731); frozen .000; H1b-SI .000; H1b-SIc .000 | **PASS**. At full scale H1a does not separate the gate from utility at all; H1b carries the whole discrimination |
| E6 | dose: P(reject linearity | gate) ≥ .80 at χ=.6 and .4; P(reject | R3) ≤ .05 + 2 SE (.0695) | gate χ=.6 **.040**, χ=.4 **.026**; R3 .044. Mean second difference 0.03–0.06 measured pts | **FAIL.** The dose module has no power to tell the gate from R3, and the cause is theoretical, not statistical (see below) |
| E7 | framing: P(reject | gate) ≥ .76; P(reject | R4-framing) ≤ .05 + 2 SE (.0695) | gate **.876**; R4 under fixed-rate framing **.010** | **PASS** |

H1b-SIc under the attenuation reading (same run-3 cells as E9): M1 .904,
M2 .966, M3 .943, M4 .930, M5 .945, M6 .930. R3: .000 in all six.

## Defects found and repaired during the iteration (all preserved)

- **Run-1 dispatch defect.** `kind='gate'` fell through to the R1-global kernel.
  Run 1 is invalid in full (`records/pipeline_cert_I032_run1_INVALID.log`).
  Unknown kinds now raise. Run 2 used the identical frozen spec and seeds.
- **Dose-test null (AD1, pre-run).** A label-permutation test of the second
  difference would test equality of distributions, which a graded line violates
  by construction. Replaced before running by a within-cell-centred studentized
  bootstrap.

## Readings, and what the pilot must decide

The design-basis effect (θ = .592, ≈ d = .33) is 5–20× smaller than the
model-implied effect. Two frozen readings of where the shrinkage comes from give
different pictures:

- *Attenuation*: people are gated, the slider is coarse. Frozen H1b has no power;
  H1b-SI and H1b-SIc both work.
- *Heterogeneity*: some people are gated, others are not. The danger is a
  composite with no gate at all, which defeats the frozen H1b (23%) and
  unconditional H1b-SI (4.2%). Only H1b-SIc holds.

H1b-SIc is the only form that holds under both readings. The pilot's
within-subject structure (drop distribution shape, P3 recovery by drop stratum)
is what distinguishes the readings for humans.

## Second failure: the dose module (E6), and why

The step-versus-line dose module (180 participants) fails: under the gate,
the second-difference test rejects linearity at .040 (χ = .6) and .026
(χ = .4), the same as under R3 (.044) and the nominal .05.

A post-hoc latent diagnostic (`records/dose_posthoc_I032.txt`, seed 132900,
run *after* the failure was recorded, labelled post-hoc, not used to repair
anything) shows the cause. Over the session horizon, **the frozen gate's dose
response is linear in μ_ref.** The curvature ratio |C|/span is 0.02 for the P2
drop, 0.02 for late-P2 trust and 0.00 for late-P3 trust at χ = .6; only
late-P3 at χ = .4 bends (0.19). The χ_min frontier of TASK_INFERENCE.md §2 is a
*permanence* statement (sustained grievance as t → ∞). Within 150 or 450
trials, with ρ ∈ {.002, .02}, the gate is graded. **The I028 claim that the
theory forces a qualitative step-versus-line contrast in this task is refuted
at the session horizon; it survives only asymptotically.**

The same diagnostic shows where the gate and R3 do separate across μ_ref: in
**slope and sign of the P3 response**, not curvature. Gate P3−P2 (χ = .6):
−11.4, −22.0, −32.5 at μ_ref .45/.55/.65. R3: +11.6, +12.3, +12.8, flat and
positive. A richer visible winner produces a deeper post-restoration decline
under the gate and no change under utility, which is the I028 "richer winner,
longer grievance" absurd-sign cell. This is a post-hoc observation. It can
become a test only through a new freeze and a fresh certification run (I033
candidate), and the dose module's place in the design is an author decision.

## Readings, revisited with all cells

| Reading | frozen H1b | H1b-SI | H1b-SIc |
|---|---|---|---|
| Attenuation, gate (power) | .000 | .916–.967 | .904–.966 |
| Attenuation, R3 (false positives) | .000 (vacuous) | .000 | .000 |
| Full scale, gate+R4 mixture (power) | **.000** | .948 | .948 |
| Full scale, pure R3 (false positives) | .000 | .000 | .000 |
| Full scale, no-gate R3+R4 composite (false positives) | **.230** | **.042** | **.000** |

H1b-SIc is the only form that is powered and specific under every frozen
cell. The frozen H1b is never powered for the gate, and is not specific
against the composite.
