# One estimand for the lab: residual evidence uptake (KGi-DISS-I038, 2026-11-11)

Everything in this record is synthetic. There are no human data.

- **Freeze.** `freezes/00_freeze_I038.yaml` was written and pushed before any
  run. Each addendum (AD-A2, AD-B1, AD-C2) was committed before its own run.
- **Scorecard.** The scorecards are verbatim in the freeze, including the
  predictions that failed (listed at the end of this record).
- **Reproducibility.** Every seeded record was re-run for bit-identity (status
  in the freeze).

## Question

Treat the human experiment as a sample from a distribution, and the model as a
machine that generates a distribution on the same space. Which single number
computed from that distribution should the experiment estimate, so that the
estimate validates or rejects the model's prediction?

## Framing

- **Space.** What one participant produces in the ten-repetition design: arm,
  six fairness ratings, and the probe statistic `T` (paid forecast revisions on
  two ticket pairs).
- **Model side.** For every parameter value the simulators draw from the
  model's distribution without limit. Its functionals are known up to
  simulation error, which is driven to zero. The human sample is the only
  source of sampling error (the setting of simulation estimators: Pakes &
  Pollard 1989; Gouriéroux, Monfort & Renault 1993).
- **Estimand.** A functional `ψ` of the distribution. I required five things
  of it, before running anything:

| | requirement |
|---|---|
| Q1 | the paper's collective prediction depends on the parameters only through `ψ` |
| Q2 | `ψ` does not move with human nuisances (noise, prior, inattention) |
| Q3 | the rivals' values lie outside the model's set |
| Q4 | `ψ` is a smooth functional, so its interval has the stated coverage |
| Q5 | it is the cheapest functional meeting Q1–Q4 |

- **Validation.** The model is validated on the estimand if the interval for
  the human `ψ` lies inside the set of values the model generates over its
  trap region. It is rejected if the interval lies outside.

## A. What the collective prediction needs from individuals

The lab measures individuals. The paper's prediction is collective. So the
first question is which property of the distribution of individuals the trap
depends on: the average amount of discounting, or the share of people who shut
down.

The engine now takes a coupling `c_i` per agent (learning multiplier
`1 − c_i·(1 − L)`; `c = 1` is the paper). Defaults reproduce the frozen engine
bit for bit.

**Trap probability with a share of fully shut agents (`c = 1`), the rest at
`c_lo`** (paper cell, 400 runs per cell):

| shut share | rest at 0 | rest at .5 | rest at .75 | rest at .9 |
|---|---|---|---|---|
| ≤ .6 | 0 | 0 | ≤ .07 | .03–.66 |
| .7 | 0 | .03 | .29 | .76 |
| .8 | .04 | .26 | .57 | .79 |
| .9 | .40 | .61 | .77 | .83 |
| 1 | .79–.87 | | | |

- **A shut-down majority does not carry the trap.** With 80% of agents fully
  shut and 20% learning normally, the trap probability is .04. The edge is at
  a shut share of .93. I had predicted .45–.75.
- **Behaviour is collective.** In all 48 mixed cells, open and shut agents
  choose alike (largest difference in the share on the better option: .017).
  When the open agents correct, the rest follow.
- **The shut share is not what matters either.** At a shut share of .8 the
  trap probability runs from .04 to .57 depending on the other agents.

**What does matter is the mean coupling.** Edge of the trap (probability .5),
expressed in the mean coupling of the population:

| shape of the coupling distribution | edge (part A) | edge (fresh shapes and seeds) |
|---|---|---|
| homogeneous | .942 | .943 |
| two types (0; 1) | .926 | .915 |
| two types (.5; 1) | .935 | .936 |
| two types (.75; 1), (.9; 1) | .944, .948 | |
| three types | | .939 |
| skewed (a few very open agents) | | .927 |

- My first test of "the mean is sufficient" compared trap probabilities at
  equal means and failed (largest difference .38). The trap probability rises
  from 0 to .8 between mean coupling .90 and .975, so a shift of .02 in the
  edge produces large differences.
- I then re-stated the claim as an edge location and tested it only on shapes
  and seeds not yet run. It passed: every edge lies in [.90, .95].
- The mean locates the edge. The shape sets how sharp it is (at mean .88:
  .008 homogeneous, .31 for two types).
- Within a person, the two learning channels enter through their sum (read
  from the I037 record: .55–.61 at (1, .9), (.9, 1) and (.95, .95)).

**Consequence.** The right lab functional is a mean over participants and over
the two channels. The trap needs nearly everyone to have nearly stopped
learning: mean coupling of at least .90–.95.

## B. The estimand

**ψ = E[T | HIGH] / E[T | LOW]: residual evidence uptake under
reference-dependent deprivation.** It is the share of normal learning from
evidence that is left after a person has lost while a visible peer won.

| attribute | value |
|---|---|
| population | everyone randomised who reaches the probe |
| conditions | HIGH board (peer wins at .72) against LOW board (peer at own level); same own odds |
| variable | `T`, mean of two pair differences of paid forecast revisions |
| events after randomisation | not revising is the outcome. Attention-check failure and dropout: kept in the primary analysis, bounded by trimming in the supplementary one |
| summary | ratio of arm means, 99% Fieller interval |

The headings are those of the ICH E9(R1) addendum. The unit-level target is
each person's own ratio of revision weights with and without the winning peer;
`ψ` is its mean weighted by the control weight (the "theoretical estimand" of
Lundberg, Johnson & Stewart 2021).

**What the model generates** (40,000 simulated participants per cell):

| gate point | legitimacy at probe time, HIGH / LOW | ψ at full coupling (count rule \| one-update rule) | upper edge: ψ at mean coupling .90 |
|---|---|---|---|
| P0 strong anchoring | .005 / .86 | .013 \| .006 | .23 \| .12 |
| P1 paper's values | .11 / .87 | .153 \| .130 | .34 \| .23 |
| P2 repair-ratio edge | .14 / .91 | .186 \| .154 | .36 \| .25 |
| P3 speed edge | .11 / .85 | .154 \| .134 | .34 \| .24 |
| P4 anchoring edge | .41 / .87 | .507 \| .471 | .61 \| .53 |

- **Trap set** over the whole region and both rules: ψ between .006 and .613.
- **Rivals:** R3 1.000, R4 1.002, R1 3.7–4.2.
- Under the one-update rule, `ψ` depends on the coupling distribution through
  its mean only (largest difference across four shapes: .005). Under the count
  rule shapes differ by .05–.11 at mean .90.

**Four decisions from one interval** (they hold jointly):

| decision | condition | meaning |
|---|---|---|
| D1 | upper limit below 1 | learning from evidence is reduced; the rivals are rejected |
| D4 | upper limit below .613 | discounting is at least as strong as the weakest corner of the trap region |
| D2 | lower limit above .613 | the paper's trap region is excluded |
| D3 | upper limit below .10 | mean coupling is at least .90 whatever the gate dynamics |

## C. Certification of the estimator

**Invariance (Q2).** The model value of `ψ` moves by at most .008 with
forecast noise (8–16), equal inattention (0–20%), the prior (mean 35 or 65,
s.d. 20) and heavy-tailed noise.

**Regularity (Q4), at 72 per arm.**

- Bias at most .005.
- Standard error within 3% of the influence-function value.
- Coverage of the 99% interval: .984–.991 over ten cells, including
  heavy-tailed noise.
- False positives of D1 under the rivals: .004–.007 (R3, R4, composite), 0
  (R1). Error rates exactly at the .613 edge: .0045 and .0055.

**Cost (Q5).**

- The ratio of means has a smaller standard error than the ratio of medians
  (.077 against .089). The ratio of medians is also off the mean-type value,
  by .03–.04 with one type and .075 with two.
- For precision at small `ψ` the efficient split favours HIGH (3.4 : 1 at
  ψ = .26). A 108/36 split matches 72/72 with 111 participants instead of 144.
- For D1 at the weakest point the equal split is best (.945 against .869 at
  108/36). The equal split stays.

**Sample size per arm for power .90** (Monte Carlo search; count rule \|
one-update rule):

| decision | truth | n per arm |
|---|---|---|
| D1 | full coupling, P0–P3 | 12–18 \| 18–24 |
| D1 | full coupling, anchoring edge | 48 \| 60 |
| D4 | full coupling, P0–P3 | 12–36 \| 24–48 |
| D4 | full coupling, anchoring edge | 800 \| 600 |
| D2 | no coupling | 36 \| 60 |
| D2 | coupling .25 | 48 \| 200 |
| D2 | coupling .5 | 120 \| never (ψ = .60 is inside the trap set) |
| D3 | full coupling, P0 only | 200 \| 600 |

- **72 per arm stands.** It gives D1 at every point (.94 at the weakest), D4
  at every point except the anchoring edge, and D2 when there is no
  discounting.
- At 72 per arm under the one-update rule the readings are roughly: D1 when
  the estimate is below about .74; D4 below about .40; D2 above about .83.
  These come from the standard errors in the record and are approximate.
- The asymptotic sample-size formula I first used failed its Monte Carlo
  check (power .70–.87 at its n). The numbers above replace it.

**Disengagement that differs by arm.** This was the open weakness of I037
(false positives .24–.27 at 20% extra disengagement; .02 with an attention
check).

- Trimming the arm with the higher retention (Lee 2009) gives an interval for
  `ψ` among attentive participants. It covers the truth in .991–.999 of
  replicates when exclusion differs by arm.
- Under R3 with 20 points of extra disengagement in HIGH, the plain ratio is
  .78 for everyone randomised and .94 after exclusion. The trimming interval's
  upper limit is below 1 in .003 of replicates.
- Cost at the weakest point, one-update rule: D1 power .94 at 72 per arm with
  equal exclusion, .83 with 10 points extra, .93 at 96 per arm.

## What ψ cannot do

**ψ identifies a product, not the coupling.** Under a linear revision rule,

`ψ = [1 − c̄·(1 − L_HIGH)] / [1 − c̄·(1 − L_LOW)]`.

- A small `ψ` can come from strong coupling or from deep delegitimation.
  Without the legitimacy levels only `c̄ ≥ 1 − ψ` holds.
- So mean coupling of at least .90 is certified only when ψ ≤ .10. The model
  itself predicts that only at P0. At the paper's own values it predicts
  .13–.15, because legitimacy in HIGH has fallen to .11 and not to 0.
- A `ψ` inside the trap set is therefore necessary for the trap. It is not
  sufficient. D3 needs 200–600 per arm and is reachable only at P0.
- Separating the two factors needs the fairness ratings as a measure of the
  legitimacy level. That is the mediation analysis already listed as open.

**The revision rule.** The map from `ψ` to coupling depends on the rule. The
control arm's absolute revision weight `W0` is identified from the pair
(`E[T]/80`), and it bounds the problem: across rules the map differs by at
most .04 when `W0 = .3`, up to .07 when `W0 = .5`, and up to .18 when
`W0 = .85`.

**Inherited from the design.** Effective draws per round summary, rigidity,
starting entitlement, and simulation of the task at full coupling (I037).

## Predictions that failed (kept)

1. Prevalence edge at .45–.75. It is .93.
2. "80% shut with 20% open gives a trap probability of at least .40." It
   gives .04.
3. The shut share alone determines the trap. It does not (range .53).
4. Mean sufficiency in its first form (equal probabilities at equal means).
   Largest difference .38. The edge-location form passed on fresh shapes.
5. The skewed family has the lowest edge. The two-type (0; 1) family does.
6. My bands for shape sensitivity under the count rule missed at both ends.
7. Rule sensitivity at most .05 at control weight .5. It is .06–.07 for
   coupling up to .75.
8. D3 at 100–300 per arm at the central point. Unreachable. My update ("out
   of reach everywhere") was also wrong at P0.
9. D2 at coupling .5 within 150 per arm. Holds under the count rule only.
10. The asymptotic sample sizes.
11. Several AD-C2 bands (D2 needs fewer participants than I predicted at
    coupling 0 and .25; the 2:1 split saves 25% or nothing, not 5–15%).

One claim (open agents "know and conform" above the edge) could not be tested
as frozen: no mixed cell lies above the edge.

## Literature

Verification levels are in `freezes/00_citation_verification_I032.md` (I038
addendum).

- **Estimand language:** ICH E9(R1) addendum, read through Mitroiu et al.
  (2020); Lundberg, Johnson & Stewart (2021).
- **Model values by simulation:** Pakes & Pollard (1989); Gouriéroux, Monfort
  & Renault (1993).
- **Falsifying a model by what it generates:** Palminteri, Wyart & Koechlin
  (2017).
- **Interval for a ratio of means:** Fieller (1954).
- **Selection that differs by arm:** Lee (2009).
- **Critical mass:** Centola et al. (2018) report that a committed minority of
  25% overturns a convention. Here 20% of agents who keep learning are enough
  to break the trap (probability .04), and 10% halve it (.40). The mechanisms
  differ: these agents are not committed, they learn, and the others' beliefs
  sit just under the tipping gap.
- **Considered, not used:** Storey (2002) and Hsieh & Turnbull (1996), for a
  distribution-based bound on a shut-down share. The share turned out not to
  be the relevant quantity.

## Flag for the manuscript (not edited)

The headline trap needs nearly everyone in the disadvantaged community to
have nearly stopped learning (mean coupling at least .90–.95). A shut-down
majority of 80% is not enough.

## Next

1. Use the fairness ratings to separate coupling from achieved delegitimation
   (the mediation analysis), so that a small `ψ` can be read as coupling.
2. Pilot specification: effective draws per summary, the control weight `W0`,
   forecast noise.
3. Decide whether the primary analysis keeps everyone or uses the trimming
   interval (author decision).
