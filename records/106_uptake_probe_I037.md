# From the paper's trap to a ten-repetition lab design (KGi-DISS-I037, 2026-11-11)

Everything in this record is synthetic. There are no human data.

- **Freeze.** `freezes/00_freeze_I037.yaml` was written before any run. Each
  addendum (AD-A2, AD-B2, AD-B3) was committed before its own run.
- **Scorecard.** The closing scorecard is verbatim in the freeze, including
  the predictions that failed.
- **Reproducibility.** Every seeded record was re-run for bit-identity
  (status in the freeze).

## Question

I036 isolated one link worth a lab: after losing while a visible peer wins,
people revise their beliefs less on evidence. I037 asks three things.

- **(A)** How weak may that discounting be before the paper's trap disappears?
- **(B)** What is the cheapest design that detects it and is safe against the
  rivals?
- **(C)** What is left for the fairness measure?

## A. How much discounting the trap needs

The engine now scales learning by `1 − c·(1 − L)` on each channel, with `c_own`
for own outcomes and `c_soc` for others' outcomes. `c = 1` is the paper.
Defaults reproduce the frozen engine bit for bit.

The table gives the trap probability at the paper's cell (400 runs per cell).

| own \ others' | 0–.75 | .90 | 1.00 |
|---|---|---|---|
| 0–.50 | 0 | 0 | 0 |
| .75 | 0 | 0 | .01 |
| .90 | 0 | .02 | .56 |
| 1.00 | 0 | .55 | .84 |

Edges where the trap probability crosses one half:

| line | edge |
|---|---|
| both channels together | .945 |
| others' outcomes alone (own fully coupled) | .893 |
| own outcomes alone (others' fully coupled) | .881 |

At the speed edge the trap needs `c = 1`.

**The trap needs a shutdown of at least about 90% of learning on both channels
at once.** I had predicted that a half-open own channel would not matter. That
was wrong.

Partial discounting still has a graded consequence. It lengthens the wrong
consensus (median trials to correction, 200 runs each):

| c | 0 | .25 | .5 | .75 | .85 | .9 | .95 | 1 |
|---|---|---|---|---|---|---|---|---|
| trials | 54 | 60 | 74 | 96 | 210 | 382 | 633 | 979 |

## B. The probe

**Measure.** The participant meets an unfamiliar ticket and gives a paid
forecast. They then see a small real record of its settlements and forecast
again.

A **pair** of tickets, one with a favourable record and one with an
unfavourable record, cancels the participant's prior. The statistic is the
difference of the two revisions. It is averaged over two pairs, one about the
participant's own draws and one about another trader's, because both channels
matter.

**What the screen found.**

- A pair beats a single ticket: 298 against 468 per arm.
- At 40 draws per round the best design within ten repetitions needs 274 per
  arm.
- The lever is exposure. With about 600 deprivation draws, LOW participants'
  entitlement has adapted and their legitimacy recovers (about .87). HIGH
  participants stay collapsed (.11 at the central point, .41 at the anchoring
  edge).
- Between 240 and 480 draws LOW is still falling, and the design is worse.
  This is a threshold, not a smooth gain.

**Certified design (S1x).**

| element | value |
|---|---|
| rich rounds | 1 (ticket odds .75/.35, board .72) |
| deprivation rounds | 5 (odds .25/.10) |
| settlements summarised per round | 120 |
| probe tickets | 4 (two pairs), 10 settlements shown each |
| total repetitions | 10 |
| participants per arm | 72 |

The standard rich phase (.65/.35, board .65) gives the same sample size (73).

**Monte Carlo certification (1,000 replicates, actual rank test at .005).**

| | result at n = 72 per arm |
|---|---|
| power, count-based revision rule | ≥ .987 at every theory point, forecast noise 8–16 |
| power, one-update-per-record rule | .950 at noise 12; .862 at noise 16 (anchoring edge) |
| false positives: R3, R4, composite | .002–.006 |
| false positives: global Bayesian rival (R1) | .000 (it predicts the opposite sign) |
| starting entitlement .4 or .6 | power ≥ .90 at the worst point |
| 10% extra disengagement in HIGH only | .05–.06 raw; .011–.015 with an attention check |
| 20% extra disengagement in HIGH only | .24–.27 raw; .020–.022 with an attention check |

- The slow-reporting rival is R3 here, because a reporting lag does not touch
  forecasts.
- A control-source pair (difference in differences) removes the disengagement
  problem (.003–.008). It costs about 845 per arm and was not adequately
  powered at that size, so it is not pursued. The attention check is the
  practical control, and it leaves two to four times the nominal error rate
  under heavy differential disengagement.

**Reading a result against the ABM.** The table is for the central gate
parameters.

| discounting c | HIGH/LOW revision ratio (count rule \| one-update rule) | power at n = 72 | trap probability | trials to correction |
|---|---|---|---|---|
| 0 | 1.00 \| 1.00 | .004 | 0 | 54 |
| .25 | .92 \| .80 | .06 \| .30 | 0 | 60 |
| .5 | .79 \| .59 | .79 \| .95 | 0 | 74 |
| .75 | .55 \| .37 | 1.00 | 0 | 96 |
| .9 | .33 \| .23 | 1.00 | .03 | 382 |
| .945 | .26 \| .18 | 1.00 | .50 (edge) | — |
| 1 | .15 \| .13 | 1.00 | .82 | 979 |

- The design detects discounting from about `c = .5` upward.
- The paper's trap needs HIGH participants to revise at most about a quarter
  as much as LOW participants.
- A weaker result still maps to a predicted lengthening of the wrong
  consensus.

## C. The fairness measure

**A defect found while preparing this iteration.** In the round-summary task
the accuracy screen (rich-phase accuracy above chance) removes about half of
the simulated participants. Accuracy over one or two single choices is 0, .5
or 1, and the first choice is a coin flip. I033 AD-B1, AD-O1 and I034 applied
it.

Without the screen, the ten-round 2/5/3 design needs:

| score | gain .25 | gain .5 | gain 1 | previously reported |
|---|---|---|---|---|
| S-a (reference effect) | 155 | 111 | 96 | 80 / 70 / 58 |
| S-b (R3-orthogonal) | 652 | 243 | 163 | 145 / 90 / 86 |

The I034 span test (217 per cell) used the same screen and is not recomputed
here. Treat it as optimistic.

In the certified probe design, the six fairness ratings give S-a at 43 / 30 /
27 per arm (gain .25 / .5 / 1). The probe therefore sets the sample.

## Proposed confirmatory structure (author decision)

- **H1a:** fairness reference effect, score S-a.
- **H1b:** evidence-uptake probe. It is behavioural and paid, and it is the
  gate-specific test.
- H1b is tested only if H1a rejects.
- **Sample:** 72 per arm, 144 participants, ten repetitions each.
- A restoration phase is no longer needed.

## What this rests on (not settled by simulation)

1. **Effective draws per summary.** The sample of 72 depends on people
   integrating a round summary of 120 settlements roughly per settlement, for
   entitlement as well as legitimacy. If a summary counts for about 40, the
   number is about 300 per arm. The pilot must measure this first, for example
   by varying the number of settlements per round between participants. The
   number of settlements can then be set from the frozen lookup.
2. **The revision rule and the forecast noise** (assumed 12 points). Under the
   one-update rule with noise 16, power is .86.
3. **Rigidity.** The 600-draw threshold comes from the slow-adapting half of
   the simulated population (time constant about 500 draws).
4. **Disengagement** that differs by arm.
5. **Coupling in the task dynamics.** Legitimacy at probe time was simulated
   with full coupling. Only the probe uses the coupling value.
6. **Mediation by legitimacy.** The probe shows that a reference shortfall
   lowers evidence uptake. It does not show that legitimacy is the mediator. A
   direct "inequity slows learning" effect (the Ham & Jenkins 2025 class) has
   the same sign. Separating the two needs a mediation test through the
   fairness score, which is not yet designed.

## Flag for the manuscript (not edited)

The headline trap at the paper's cell requires all of the following together:

- a gate at least about 90% as fast as the frozen one;
- a repair-to-erosion ratio at most .29;
- conformity at the tipping gap;
- at least about 90% discounting on both learning channels.
