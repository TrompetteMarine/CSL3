# ODD+D model description

Model: dissonance-minimizing legitimacy gating in networked reinforcement learning.
Protocol: ODD+D (Müller et al., 2013, *Environmental Modelling & Software* 48:37–48),
the decision-making extension of the ODD protocol (Grimm et al., 2020, *JASSS*
23(2):7). This document is the authoritative model description; the paper's Methods
states only what is needed to read the results. Symbols follow the paper's
Supplementary Table 1; every default value and every experiment's cells and seeds are
in `freezes/`.

## I. Overview

### I.i Purpose
To study when repeated failure makes a population stop learning from outcomes and
start rejecting the rule that assigns them ("delegitimation"), and when the resulting
collective error defends itself. The model derives both reactions from one per-period
cognitive-dissonance functional and asks which network and entitlement conditions
produce persistent defensive wrong consensus, resignation, credulous error, or
legitimate consensus.

### I.ii Entities, state variables and scales
Agents i = 1..N (default 200) partitioned into two communities (default equal halves;
asymmetric variants in `freezes/00_freeze_I014.yaml`). Each agent holds:
- action values Q_i(a) ∈ [0,1] for two bandit arms a ∈ {1,2};
- legitimacy L_i ∈ [0,1] — the weight on outcomes as evidence about actions;
- aspiration (entitlement) A_i ∈ [0,1] — a recency-weighted benchmark of deserved
  outcomes.
Community coupling is the row-stochastic matrix B = [[1−Γ, Γ], [Γ, 1−Γ]] with
permeability Γ. Time is discrete, one bandit trial per step; default horizon T = 600
trials. Arms pay Bernoulli rewards with means μ1 > μ2 (default 0.6, 0.4).

### I.iii Process overview and scheduling
Within each trial, in order, all computed from pre-update states (synchronous commit):
1. Field: each community's decisiveness-weighted action mass from trial t−1 is mixed
   through B into the anticipatory field S_i(a).
2. Choice: augmented values V = Q + λS; choice by logistic rule
   P(a=1) = Λ(2βa_thr ΔV / σ²) — the first-passage probability of a symmetric-
   threshold diffusion; decisiveness C = |2P−1|.
3. Rewards drawn; community outcome statistics formed.
4. Updates committed simultaneously: private value update (gain αL), retrospective
   social value update (gain ηL), legitimacy threshold update (−ν_F[D−τ]₊ + ν_R·1{D≤τ}),
   aspiration update ((1−ρ)A + ρ[(1−χ)R + χ·R_ref]).

## II. Design concepts

### II.i Theoretical and empirical background
The decision model is derived, as margin-wise gradient steps, from one per-period
dissonance functional D(Q,L) = (L/2)(R−Q(a))² + w_f[LX + (1−L)κK] over the two
revisable cognitions (action values; legitimacy granted to the rule), with
reward-maximizing reinforcement learning as the corner where frame revision is
unavailable. Aspiration adaptation follows the Simon–Selten tradition; discomfort is
asymmetric in the Fehr–Schmidt sense; confidence-weighted social influence follows the
advice-taking literature. Full derivation: paper Supplementary Section S2.

### II.ii Individual decision making
Agents are myopic: each trial they take one choice (logistic in augmented value
difference) and one implicit frame decision (the legitimacy update), both gradient
steps on the same objective. No forward-looking belief management, no discounting, no
strategic reasoning. The lexicographic convention (the frame margin does not see the
evidence term) is load-bearing and tested: the non-lexicographic variant adds a
surprise-erosion term (mode `nlvar`).

### II.iii Learning
Individual: gated reinforcement learning, effective rate αL_i — the gate makes the
learning rate state-dependent (this induces apparent dual-learning-rate asymmetry when
fitted by fixed-asymmetry models; `generators/dualalpha.py`). Social: a retrospective
channel revises values towards decisiveness-weighted observed outcomes with gain ηL_i,
gated identically. Aspiration learns at rate ρ with social anchoring weight χ.

### II.iv Individual sensing
Each agent senses: own reward; its community's (and, through B, the other community's)
decisiveness-weighted action mass and outcome statistics; the reference outcome R_ref
(exposure-weighted neighbour mean, "local", or population mean, "global visibility" —
each experiment states which).

### II.v Individual prediction
None beyond the one-step value estimates; the anticipatory field uses last trial's
actions (one-trial delay).

### II.vi Interaction
Indirect, field-mediated: agents interact through community-level aggregates
(conformity pressure in choice via λS; retrospective outcome information via η; the
reference in the aspiration update). Credibility weighting variants: decisiveness
(default), unweighted, payoff-biased (modes `fieldform`, `topo`).

### II.vii Collectives
Two communities; one receives an early lead on the inferior arm in the lock-in
experiments (initial Q values 0.62/0.38 vs 0.38/0.62).

### II.viii Heterogeneity
Baseline: identical parameters, heterogeneous states. Tested heterogeneity: per-agent
permeability Γ_i ∈ {0, 2Γ̄} (mode `topo`); slow/fast aspiration-rigidity mix in the
prediction generator.

### II.ix Stochasticity
Bernoulli rewards; logistic choice. All streams seeded (xoshiro256++/SplitMix64 in the
mapping engine; NumPy default_rng in the primary and generator code); every seed is
pre-declared in `freezes/`.

### II.x Observation
Per-trial community means (optimal-choice mass, legitimacy, aspiration); terminal
classification over the last 50 trials: defensive wrong (m2 < 0.3 and L̄2 < 0.3),
credulous (m2 < 0.3, L̄2 > 0.5), correct-but-illegitimate (m2 > 0.7, L̄2 < 0.3),
legitimate (m2 > 0.7, L̄2 > 0.5). Regime probabilities carry Wilson 95% intervals;
paired contrasts use common random numbers.

## III. Details

### III.i Implementation
Three independent implementations sharing no code: primary engine (Python/NumPy; all
confirmatory numbers), scalar audit, high-throughput mapping engine (Rust, `engine/`;
validated against five pre-stated distributional gates before any sweep was used —
`REPRODUCIBILITY.md`). Figures: Julia/CairoMakie reading `records/` only.

### III.ii Initialisation
L_i = 1, A_i = A0 (experiment-specific; 0.8 at the confirmatory cell, built-in
"remembered affluence"), Q as in II.vii, fields zero at t = 0.

### III.iii Input data
None; all environments are synthetic Bernoulli bandits.

### III.iv Submodels (equations, defaults)
With δ = R − Q(a), discomfort D = φ⁻[A−R]₊ + φ⁺[R−A]₊, excess X = [D−τ]₊,
acceptability K = 1{D ≤ τ} (X·K = 0 by construction):

- Q(a) ← clip[0,1]( Q(a) + αL δ + ηL (o(a) − e(a)Q(a)) )
- L ← clip[0,1]( L − ν_F X + ν_R K )
- A ← clip[0,1]( (1−ρ)A + ρ((1−χ)R + χ R_ref) )

Defaults (frozen): μ = (0.6, 0.4); α = 0.2; η = 0.2; λ = 0.5 (0.7 in trap
experiments); κ_β = 12; ν_F = 0.05; ν_R = 0.0125; τ = 0.3; φ⁻ = 1; φ⁺ = 0.25;
ρ = 0.002; χ = 0.4; Γ = 0.1; N = 200; T = 600. Derived: A*(μ) =
(τ + (ν_R/ν_F)·μ/(1−μ))/φ⁻; ρ_c = 0.00641 at the confirmatory cell. The restriction
φ⁺ ≤ τ/(1−τ/φ⁻) excludes the windfall-erosion corner (illustrated outside it in
`records/corner.csv`).

Engine modes and the record each regenerates: see `engine/src/main.rs` headers and
`REPRODUCIBILITY.md`.

## References

- Müller, B., Bohn, F., Dressler, G., Groeneveld, J., Klassert, C., Schlüter, M.,
  Schulze, J., Weise, H., Schwarz, N. (2013). Describing human decisions in
  agent-based models — ODD+D, an extension of the ODD protocol. *Environmental
  Modelling & Software* 48, 37–48.
- Grimm, V., Railsback, S. F., Vincenot, C. E., et al. (2020). The ODD protocol for
  describing agent-based and other simulation models: a second update. *JASSS*
  23(2), 7.
