# Task specification — market-skinned delegitimation task (I029)

Operational specification for the shared-engine configuration, built on
`TASK_INFERENCE.md` (the reasoning) and `DESIGN.md` (logistics, allocation,
pilot). Constants marked PILOT are fixed by the pilot; the synthetic-recovery
gate in §6 must pass before anything here is frozen for preregistration.

## 1. The isomorphism (task v3 ↔ market skin)

| task v3 (bandit) | market skin | invariant preserved |
|---|---|---|
| two arms | two tickets (SQUARE / TRIANGLE) each round | binary choice geometry |
| arm payout rates (μ₁, μ₂) | seeded settlement rates per phase | identical (μ₁, μ₂) schedule: .65/.35 → .30/.15 → restoration |
| payout rule | market + settlement engine (AMM, rule disclosed truthfully) | single attributable rule, objectively fair |
| reward ∈ {0,1} | house-funded ticket wins (no stake destroyed) | gains domain (no loss-aversion confound) |
| yoked peer earnings display | trader board: one prior participant's running winnings + track record | reference channel, HIGH/LOW as in DESIGN.md |
| fairness slider | "the market settles fairly" slider (0–100, every 5 rounds) | legitimacy measure unchanged |
| entitlement slider | "what I deserve to win per round" | ρ instrument unchanged |
| WTP rule-switch | pay to have the engine re-seeded ("a new rule generated the same way") | revealed-preference legitimacy, truthful |

Prices are fixed within phases and the AMM rule is stated in the instructions,
so the settlement process is the only degree of freedom a "rigged" belief can
attach to — and it is seeded and fair. Because the isomorphism preserves the
(μ₁, μ₂) geometry exactly, the model's generator, the identification results and
the collective calibrations transfer; what does not transfer automatically is
human behaviour under the betting frame, which is precisely what the pilot's
framing comparison measures (market skin vs plain bandit skin on the same seeds,
PILOT arm split).

## 2. Modules and cells

Confirmatory core (unchanged from DESIGN.md): HIGH/LOW × MODERATE/FULL with the
gatekept H1a/H1b structure, N per the distribution-free arithmetic of §5.

Reference-dose module (step-versus-line): two added cells at μ_ref = .45 and
.55, n = 90 each, MODERATE restoration; the .65 point is the existing HIGH arm,
so the full dose curve costs 180 participants. Preregistered prediction: the
gate places the sustained-grievance threshold between .55 and .65 (the
χ_min frontier of TASK_INFERENCE.md §2); the inequity-in-utility rival predicts
a graded response ∝ (μ_ref − μ_own). The dose module's secondary payoff is a
structural χ estimate from the frontier location.

Null-region prediction (free): P1 fairness ratings are invariant to the trader
board (own outcomes at or above aspiration ⇒ the gate predicts no reference
effect). Preregistered as a falsification region: a reliable P1 reference
effect counts against the trigger condition.

Framing probe (separable, n = 90): group-contingent fixed-rate instructions as
in DESIGN.md §3.

Exploratory layers, flagged pending pilot: minimal-information binarized-
scoring-rule probability reports on settlement (calibration-intact-while-
fairness-collapses signature); WTP convergence with the slider. Neither enters
confirmatory analyses; the pilot checks the BSR layer does not contaminate the
fairness measure.

## 3. Phase schedule and clocks

450 rounds, 150 per phase (PILOT: extended to 225 in P2 if the ρ̂ mass rule
fires; the extension dose is derived — at ρ̂ = .005 it raises the manipulated
aspiration-gap component by ×1.35). Windfalls every 15th round, announced,
non-contingent. The LOW-arm self-extinction clock t* ≈ 1.0–1.3/ρ and the
anchor-gap formula χ(μ_ref − μ_own)(1 − e^{−ρt}) are the pilot's translation
table from ρ̂ to expected effect size.

## 4. Measures

As DESIGN.md §5, with the market renames of §1. Order within a round: ticket
choice → settlement → (every 5th) sliders. WTP probes at end-P2 and mid-P3.
Funnel debrief includes the market-specific suspicion probes ("were the
settlements fair/random?", trader-board realness).

## 5. Power, distribution-free (supersedes every normal-theory number)

Rationale: the sample is weird by construction — bounded sliders with floor and
ceiling heaps, rounding to multiples of five, a non-responder mixture, skew,
heavy tails, and exclusion-induced selection. Power is therefore Monte Carlo
over the frozen six-shape battery of `analysis/power_free.py` (freeze I029):
truncated normal; zero-inflated censored-rounded; 80/20 attention mixture;
t(3) tails; lognormal skew; and the mixture with the preregistered exclusion
screens applied inside the simulation (the sample-bias-corrected cell —
selection is simulated, not assumed away).

Tests: H1a by one-sided Wilcoxon–Mann–Whitney at α = .005, with the studentized
permutation Welch test co-reported (level valid under heteroskedasticity and
non-normality); the effect measure is the Mann–Whitney θ = P(drop_HIGH >
drop_LOW) with the Hodges–Lehmann shift as the location summary. Design-basis
effect θ = .592 (the anchor corresponding to the old d = .33 under normality,
now defined without it). The design N is the WORST-CASE N*(power = .90) across the battery: N* = 320 per
arm post-exclusion under every measurement-weirdness shape, with 360 recruited
sufficing in the exclusion-selection cell (records/power_free.csv). The I025
normal-theory N = 280 is superseded. The battery also settles the test choice
empirically: the rank test is shape-stable (N* = 320 across all five shapes)
while the mean-shift test collapses under skew (power .32 at N = 280) and heavy
tails (.61) — rank-primary is a power decision, not only a level decision. At
the θ = .570 floor, power at N = 320 is .65–.72, reported not claimed.
H1b equivalence runs as two one-sided rank tests with the band δ_eq from pilot
σ_r; its power is a pilot-time computation by the same engine.

Pilot-time correction: power is re-estimated by resampling the pilot's
empirical drop distribution with the exclusion screens applied inside the
resampling, and the small-pilot optimism of plug-in bootstrap power is
corrected by a double bootstrap — the planning value is the 10th percentile of
the outer power distribution, not the mean (both functions are in
`power_free.py`, frozen now, executed at pilot time). Estimand note: the target
is the in-sample mechanism contrast; no demographic raking is applied, and
external heterogeneity is carried by the ρ̂ moderator, not by weights.

## 6. Gates before preregistration

(i) Synthetic-recovery gate on the market-skinned generator: the generator is
re-skinned (identical (μ₁, μ₂) geometry), synthetic participants are produced
under the market frame's measurement model (rounding, censoring, mixture), and
the analysis pipeline must recover individual ρ at r ≥ .7 and reproduce the
I003 group-level bias profile before the preregistration is frozen —
isomorphism is an argument, the gate is the proof. (ii) Pipeline gate: the
WMW/permutation and rank-TOST modules added to `pipeline.py` must reproduce the
power engine's rejection rates on its own battery draws (consistency check).
(iii) Pilot decision rules per DESIGN.md §7, with the framing-comparison arm
added (market skin vs bandit skin, same seeds, PILOT n split 50/50 within the
standard-elicitation arm).
