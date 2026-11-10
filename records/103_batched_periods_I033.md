# Ten decisions instead of hundreds of rounds (I033 AD-B1, 2026-11-10)

The protocol was frozen before running (`freezes/00_freeze_I033.yaml`,
AD_B1). The script is `experiment/analysis/batched_periods_I033.py` (seed
133600) and the record is `records/batched_periods_I033.txt`. The generator
gained one option, `choice_every`. Its defaults are unchanged, and all 23
equivalence tests pass.

## The idea

Take the frozen gate kernel. While aspiration stays above the tolerance τF and
legitimacy is not at a bound, one period of k draws moves legitimacy by

  ΔL = −νF·(A − τF)·(number of losses) + νR·(number of wins).

A win always has D = .25(1 − A) ≤ τF, so it only repairs. The gate therefore
depends on a period's outcomes **only through its win count**. Over k draws,
the aspiration update is, to first order in ρ, a function of the period's mean
outcome and the mean displayed reference.

A task of at most 10 decision periods can therefore show, at the end of each
period, a summary: "your ticket paid in x of k draws; the board trader's paid
in y of k". It carries the evidence of 10k rounds. Within each period the
participant makes one ticket choice, which is held for the period, and answers
one rating block.

## Results

**Equivalence (EB1, PASS).**
- Latent trust at period ends in the batched task (k = 25; 2/4/3 periods)
  stays within 3.8% of the per-round task with the same draws.
- This holds in every cell, at every theory point P0–P4, and for R3.
- The predicted fairness path is the same, with 9 decisions instead of 225.

**Sample size per cell.** n is the smallest per-cell n with power ≥ .90 for
both H1a and the H1b conjunction at every inside theory point (M2).

| design | decisions | draws shown | one slider, a = .5 | three-item scale, a = .25 | three-item, a = .5 | three-item, a = 1 |
|---|---|---|---|---|---|---|
| k 25, 2/5/3 periods | 10 | 250 | 224 | 278 | **128** | 88 |
| k 25, 2/4/3 periods | 9 | 225 | 265 | > 320 | 138 | 83 |
| k 20, 2/5/3 periods | 10 | 200 | 309 | > 320 | 137 | 97 |
| k 20, 2/4/3 periods | 9 | 180 | > 320 | > 320 | 320 | 130 |

For comparison, the per-round 225-round task needed 146 per cell at a = .5
with one slider rated every 5 rounds, and was not adequate at a = .25.

**Specificity (B3).** For the best design (k 25, 10 periods, three-item scale,
n = 129), conjunction false positives are .000 against R3 (χ .4 and .6) and the
no-gate composite, at a = .5 and a = 1.

## What changes for participants

The session is about 10 periods. Each period is one ticket choice, one summary
screen, three short fairness items and one entitlement item, roughly 25
seconds. Add about 2 minutes of instructions and quiz, about a minute of
entitlement induction, and the debrief, and the session is about 8–10 minutes.

## What the simulations cannot settle (human-necessary, for the pilot)

1. **Per-outcome vs per-event integration.**
   - The lemma assumes people weigh a summary by its counts.
   - If instead they update once per period on the shortfall of the period
     rate, the qualitative predictions survive: reference dependence, and no
     relegitimation while the reference gap persists. The per-period rates
     would then be new human parameters.
   - Test: vary k between pilot participants (say 10 vs 25). Under per-outcome
     integration the drop scales with k; under per-event integration it does not.
2. **Gain and noise of the three-item scale** (a, σ). The design needs
   a ≥ .25 with three items; a ≥ .5 brings n to about 130 per cell.
3. **Initial entitlement and rigidity**, as before. Inducing entitlement with a
   short earned-endowment step should narrow the spread of starting
   entitlement. Its effect on power is not yet simulated.

## Not yet checked in the batched task

- slow-integrator rivals;
- the size of the FULL control;
- sensitivity to initial entitlement;
- the worst measurement shape M5;
- bit-identical re-run.
