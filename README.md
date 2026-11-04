# CSL3 — Dissonance-Minimizing Agents in Networked Social Learning

Simulation, theory-verification and experiment code for the paper *When Losing
Delegitimizes the Game: Dissonance-Minimizing Agents in Networked Social Learning*
(working title). The formal Lean layer lives in the companion repositories
[CSL](https://github.com/TrompetteMarine/CSL) and
[CSL2](https://github.com/TrompetteMarine/CSL2), branch `lean-diss-core`,
directory `formal_diss/`.

## The insights this code establishes

1. **One functional, two reactions.** Legitimacy-gated reinforcement learning and
   threshold delegitimation are the margin-wise gradient steps of a single per-period
   cognitive-dissonance functional; reward maximization is the corner where frame
   revision is unavailable.
2. **Entitlement, not failure, closes the gate.** A critical aspiration A*(μ) in closed
   form; resignation under self-referential aspiration; relative deprivation requires
   visible unequal success; whether a population traps is a race between legitimacy
   collapse and aspiration adaptation with a closed-form critical rate ρ_c — tested
   directly (absorption crossover within 6% of ρ_c).
3. **Defensive wrong consensus.** At high entitlement under weak outside contact and
   conformist transmission, populations lock onto a wrong action with collapsed
   legitimacy (P = 0.843 at the pre-declared cell, 600-trial horizon). The trap is
   bistable regime selection, not criticality; persistence is horizon-indexed.
4. **Scope conditions, located by perturbation.** The trap needs conformist
   (confidence-weighted) transmission and uniformly weak exposure: payoff-biased
   imitation or heterogeneous contact dissolves it — while the behaviour/belief
   timescale dissociation survives.
5. **Transparency heals rational distrust, not grievance.** Bayesian rule-suspicion
   recovers at evidence speed (a theorem for fixed-likelihood rivals); dissonant
   grievance recovers on the aspiration clock 1/ρ. Behaviour corrects in both.
6. **Induced optimism.** Fitting standard dual-learning-rate models to gate-generated
   choices yields apparent positivity bias that is state-dependent — present under
   entitlement shortfall, ordered by the visible reference, absent without the gate.
7. **A measurement doctrine.** Individual-level recovery is limited to the aspiration
   adaptation rate ρ (and only with an entitlement elicitation); the decisive
   experimental test is one confirmatory hypothesis — reference-dependent
   delegitimation — with the restoration phase separating the gate from
   inequity-in-utility accounts.

## Layout

| Path | Contents |
|---|---|
| `engine/` | Zero-dependency Rust simulation engine (all dense maps, scaling, robustness and perturbation modes; `cargo build --release`, modes listed in `src/main.rs`) |
| `figures/` | Julia/CairoMakie figure pipeline — reads `records/` only, never simulates |
| `generators/` | Frozen prediction generator for the experimental task (`predict_taskv3.py`), the induced-asymmetry check (`dualalpha.py`), rating-noise sensitivity (`sigmar_sweep.py`) |
| `analysis/` | Identification / synthetic-recovery machinery (likelihood ridges, model confusion, recovery screens) |
| `experiment/` | oTree 6 implementation of the preregistration-ready three-phase task (yoked no-deception peer display, fairness and entitlement sliders), bots, and the preregistered analysis pipeline |
| `records/` | Frozen result records (CSV/JSON) from which every number in the paper is quoted and every figure regenerates |
| `freezes/` | Frozen design files: every run's cells, seeds, outcome definitions and acceptance criteria, fixed in writing before execution, with dated closing records |
| `paper/` | Manuscript sources (main text, supplement, bibliography) |
| `REPRODUCIBILITY.md` | Full protocol: engines and cross-validation gates, audit records, seed policy, machine-check statements |

## Reproduction in three commands

```
cd engine && cargo build --release          # build the simulation engine
./target/release/rustsim validate           # five pre-stated cross-validation gates
cd ../figures && julia make_figs_makie.jl   # regenerate every figure from records/
```

Engine modes (`rustsim <mode>`) regenerate any record in `records/` from its frozen
seeds; the mapping from record to mode and freeze file is in `REPRODUCIBILITY.md`.

## Verification

Seven Lean 4 theorems certify the algebraic core (statements, scope and axiom audits in
the paper's Supplementary Section S7; sources in CSL/CSL2 as above). Simulation results
are cross-checked by three independent implementations with pre-stated distributional
gates. Every citation of a technical result was verified against an authoritative
record before use (`freezes/00_citation_verification_I004.md`).
