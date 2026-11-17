# How many participants each step of a staged validation needs (KGi-DISS-I045, 2026-11-17)

Simulation only. Every figure is a power computed on simulated cohorts, with the gate
kernel as the truth and assumed rating noise, forecast noise and revision rules. Nothing
has been run on people and the app is untouched.

- **Request.** Simulate first, and see how many participants are required to have enough
  information.
- **My reading.** The steps are those I proposed in conversation: the assumptions, the gate,
  the rivals, then the economy one feature at a time. They are not an approved plan.
- **Conventions.** One-sided .005, the programme's level. Power .90, with .80 in brackets.
  The requirement is the smallest size of a fixed grid that reaches the target. "Binding"
  is the largest requirement over the gate points P1–P4. It is P4, the anchoring edge, in
  every step but the third, where the rival tests are taken over P1–P3. A pair is 2
  people; a triplet (one LOW session and its two HIGH twins) is 36 people at six per
  market and 24 at four.
- **Freeze.** `freezes/00_freeze_I045.yaml`, pushed before any code; one addendum pushed
  before the record was run. The scorecard is verbatim in it.
- **Record.** `records/staged_power_I045.txt` (seed 141000; a second run is bit-identical).
  Code: `experiment/analysis/staged_power_I045.py`.

## The budget

| step | what it establishes | people, power .90 (.80) |
|---|---|---|
| 1. first wave on the built app (one sample) | fairness falls at equal own outcomes | 48 (48) |
| | the reference raises aspiration, one entitlement item as built | 192 (168) |
| | the same with three items | 96 (72) |
| | how many outcomes a person takes from a round, read correctly in 95% of waves or more | 72 |
| | the size of the main study known within about a quarter | 144 |
| 2. the gate | less uptake of evidence under HIGH, one-update rule | 168 (120) |
| | the same, count rule | 120 (96) |
| 3. the gate against a uniform slowdown | HIGH-arm association, probes as built (one record pair, one source pair) | 960 (672) one-update; 480 (336) count |
| | the same with two record pairs | 576 (480); 384 (288) |
| | twelve-record claims | 576 (480); 336 (240) |
| 4. the live economy, six per market | the same contrast on markets, session effect 0 / .1 / .2 | 288 (216) / 360 (360) / 576 (432) |
| the live economy, four per market | | 240 (192) / 288 (288) / 384 (384) |

- **Step 1 is one sample.** 96 pairs (192 people) cover every row. With three entitlement
  items 72 pairs (144 people) do.
- **Step 2 assumes that a round is integrated settlement by settlement.** If a round counts
  for 80 or 40 settlements the gate test needs 672 or 576 people under the one-update rule
  and 384 or 480 under the count rule. Step 1 tells which case holds.
- **Step 2 with one adverse human parameter** (one-update rule): 240 (168) people if the
  forecast noise is 16 instead of 12, or if 20% are inattentive instead of 10%; 192 (168)
  if the weight on a source is .2 instead of .35. Combinations were not run.
- **Step 4 is given for the one-update rule.** Under the count rule: 216 (180), 288 (288),
  432 (360) at six per market and 192 (144), 240 (192), 288 (240) at four.

### Sums

| | favourable | unfavourable |
|---|---|---|
| revision rule; session effect | count rule; none | one-update rule; .1 |
| first wave | 192 | 192 |
| gate | 120 | 168 |
| live economy, four per market | 192 | 288 |
| **core** | **504** | **648** |
| rival test, two record pairs | 384 | 576 |
| institution contrast on fairness: the live rung at six per market (216, 360) in place of four, and a shares arm of 6 or 8 triplets | 24 + 216 | 72 + 288 |
| **every rung** | **1,128** | **1,584** |

- Both columns assume the favourable count of outcomes per round and the assumed noise.
- **If step 3 is run, its participants contain step 2** (same design, same people). The
  sums fall by 120 and 168, to 1,008 and 1,416.
- With the rival test on the probes as built the sums are 1,224 and 1,968.
- **Separating the gate from a mere slowdown costs more than showing it:** 384–576 people
  against 120–168.
- Showing the institution contrast on uptake, not on fairness, takes 8 to 20 triplets per
  institution at the anchoring edge: up to 720 people per institution.

## Step 1: what a first wave tells

The built app is the case "streams completely separated". One cell, as built:

| question | how | result (anchoring edge unless stated) |
|---|---|---|
| does fairness fall at equal own outcomes | last fairness rating, LOW above HIGH | power .99 at 36 pairs, 1.00 at 72 |
| does the reference raise aspiration | entitlement rating, HIGH above LOW | one item: power .79 at 72 pairs, .90 or more at 96; three items: .996 at 72 |
| can a win erode fairness | slope inside the control arm | at P1: a strong violation (φ⁺ = 1) is flagged from 60 pairs; a moderate one (φ⁺ = .5) needs 168 |
| how many outcomes per round | the ratings after every round | read correctly in .95 of waves or more from 36 pairs, .99 from 72 (worst cell over P1 and P4) |
| the nuisance parameters | control arm's weight, spread of T | at P1: size of the main study known within ±24% (relative s.d.) from 72 pairs, ±36% from 36 |

**The count of outcomes per round is the cheapest thing to learn and the most valuable.**
It decides between 168 and 576–672 people for the gate test.

- **Within one cell.** In the model the control arm's fairness dips and recovers if a round
  is integrated settlement by settlement, and is still falling if a round counts for 80 or
  40. A classifier on the twelve mean ratings (six rounds, two arms) picks the true count.
  Worst cell over P1 and P4 and the three counts: .976 of waves of 24 pairs with the gate
  point known and .917 with it unknown; .994 and .951 at 36 pairs; 1.000 and .991 at 72.
- **The simple recovery test** (control arm, last rating above the rating after round 3)
  needs 30–36 control participants. It is not clean at the repair edge: when a round counts
  for 80 it still rejects in .02–.04, because the control arm recovers a little there (+1.2
  points against +16.2).
- **Two cells between participants** (40 against 120 settlements shown) are the expensive
  way. The control arm rated fairer at 120 needs 84 participants per cell; the HIGH arm
  rated less fair needs 120 at P1 and more than 288 at the anchoring edge.

**The revision rule needs a probe the app does not have.** Comparing the weight on a record
of 10 closes with the weight on a record of 4, within participant, identifies the count
rule with 120 control participants (84 for power .80), and keeps its level under the
one-update rule (.0035–.0050). The rule moves the gate test from 168 to 120 people and the
rival test from 576 to 384.

**A size computed from the wave runs low.** The closed form
`n = 14.88 (s_H² + s_L²) / (m_L − m_H)²` gives a median of 63 pairs from a wave where the
simulation needs 84. On the pools it gives 72 against 84, and 23 against 30. A lookup built
on it needs the simulated correction.

**Under the favourable count the wave is the size of the gate test itself.** 84 pairs
suffice for the confirmatory pair at the anchoring edge under the one-update rule. Whether
the first wave is a pilot, or the confirmatory study with its analysis frozen beforehand,
is the author's decision.

## Step 2: the gate on the individual design

Pairs for the confirmatory pair (fairness, then uptake), design B as built (one record pair
and one source pair):

| | P1 | P2 | P3 | P4 (anchoring edge) |
|---|---|---|---|---|
| one-update rule | 30 (24) | 24 (24) | 30 (24) | 84 (60) |
| count rule | 18 (18) | 18 (18) | 18 (18) | 60 (48) |

One change at a time, at the anchoring edge, one-update rule:

| change | pairs |
|---|---|
| weight on a source .2 / .5 (as built .35) | 96 / 72 |
| two record pairs in place of a source pair | 72 |
| forecast noise 8 / 16 (assumed 12) | 60 / 120 |
| 20% inattentive (assumed 10%) | 120 |
| a round counts for 80 / 40 settlements | 336 / 288 |

- Under the count rule a round counting for 80 or 40 needs 192 or 240 pairs.
- At the anchoring edge the two counts are one grid step apart under the one-update rule
  (uptake ratio .627 and .633), which is inside the uncertainty of the calculation. At P1
  a count of 40 is the worse case (120 pairs against 72).
- The as-built cell was drawn three times: 84, 84 and 72 pairs. The larger is used.

## Step 3: the gate against a uniform slowdown

Pairs at the binding point over P1–P3:

| | one-update rule | count rule |
|---|---|---|
| HIGH-arm association, record + source (as built) | 480 (336) | 240 (168) |
| HIGH-arm association, two record pairs | 288 (240) | 192 (144) |
| top quarter against the rest, two record pairs | 288 (192) | 144 (120) |
| freeze at .5, two record pairs | 72 (60) | 30 (24) |
| twelve-record claims (PLAT2), participants per arm | 288 (240) | 168 (120) |

- The freeze decision is cheap, but it does not exclude a uniform slowdown.
- A source pair costs the association two thirds more participants (480 against 288).
- **Twelve-record claims do not come cheaper on individuals.** With each participant a unit
  they need 576 people under the one-update rule, the same as the association, and 336
  against 384 under the count rule.
- At 72 per arm the statistic has power .35 at P1 here, where I044 gave .61 for 12 markets
  of six. The two are not a clean comparison: I044's figure is on the live market with
  unscaled supply (legitimacy .175 | .935 against .112 | .871 here) and with markets as
  units. I have not measured what accounts for the difference.

## Step 4: the economy, one feature at a time

**Cash carried into the claims, and ownership of the units,** are not simulated. T is taken
from private forecasts before any trade, and ownership leaves fills and prices unchanged,
so the model predicts no change in what is tested and the requirement is that of the rung
they are added to. That is a statement about the model. Whether people behave differently
once cash or ownership is at stake is what those rungs would test.

**Completion as a gate** (a basket of q fills per round ends the bidding; the prediction
market opens to those who completed the last basket), individual design, one-update rule:

| basket (30 fills expected on the better ticket) | complete it at P1, HIGH / LOW | uptake ratio at P1 | pairs for the uptake test, everyone measured / completers only: P1 | P4 |
|---|---|---|---|---|
| none | — | .127 | 24 | 72 |
| 20 | 83% / 87% | .193 | 48 / 60 | 240 / 336 |
| 15 | 89% / 89% | .267 | 72 / 84 | 576 / more than 576 |
| 10 | 96% / 95% | .387 | 120 / 120 | more than 576 |

- The loss comes from the events that stop, not from who is measured: measuring completers
  only moves the ratio by .02 at most.
- At the anchoring edge a basket of 20, which 85–87% complete there, multiplies the
  requirement by about three (240 pairs against 72–84), and a basket of 15 by seven to
  eight.

**The live economy by triplets** (calibrated supply; triplets for the confirmatory pair):

| | session effect 0 | .1 | .2 |
|---|---|---|---|
| six per market, P1 | 4 | 5 | 6 |
| six per market, P4 | 8 (6) | 10 (10) | 16 (12) |
| four per market, P4 | 10 (8) | 12 (12) | 16 (16) |

- One-update rule. Under the count rule at P4: 6, 8, 12 at six per market and 8, 10, 12 at
  four.
- **Four per market needs fewer people** at every session effect (240, 288, 384 against
  288, 360, 576), at the price of more sessions (36 sessions of 8 against 30 of 12 at a
  session effect of .1).

**The live economy with a stopping basket** of 15 units per round: 6 triplets at P1 without
a session effect and 10 with one of .1; at P4, 20 triplets (720 people) without and more
than 32 with it. A basket of 10: 8 and 12 at P1; more than 32 at P4.

**Unit orders against shares,** each in its own triplets of six per market: the fairness
contrast is 42 points with unit orders and 5 with shares at P1, and the uptake ratio .07
against .90. Showing that the fairness contrast differs takes 4 triplets per institution
at P1 and 6–8 at P4; showing that the uptake contrast (T under LOW minus T under HIGH)
differs takes 6–10 and 12–20.

## Gates

| gate | result |
|---|---|
| G1 the individual runner | equal to `twins_I040.twins` on the same seed |
| G2 the live runner | equal to `market_cert_I044.run` bit for bit |
| G3 sizes | at most .0095 at nominal .005 and .067 at nominal .05 for every test behind a requirement. The PHI flag is the exception: it fires under the frozen model in .008–.009 up to 288 pairs and .013 at 576 |
| G4 determinism | a second run is bit-identical |
| G5 constraints | nothing run on people; app, wording and main text untouched; no credential |
| G6 closed form | within one grid step, on the low side |

## Predictions that failed

Thirteen sets were frozen. Three passed in full: fairness (S1), entitlement (S2) and the
completion gate in the individual design (S9). The others:

- **S3.** The PHI flag's false-alarm rate reaches .013 at 576 pairs against my .012.
- **S4.** The two-cell comparison needs 84 participants per cell, not 24–60.
- **S5.** The revision rule needs 120 control participants, not 54–84.
- **S6.** One cell by .01 (.36 against .35).
- **S7.** Four cells: the count rule at the anchoring edge needs 60 pairs (I said 40–54);
  forecast noise 8 needs 60 (36–54); 20% inattentive 120 (90–108); a round counting for 80
  settlements 336 (120–300).
- **S8.** Twelve-record claims on individuals need 288 and 144 per arm at P1, not 96–144
  and at most 72.
- **S10.** Three cells, each one grid step above my range.
- **S11.** Under the count rule a stopping basket of 15 needs 24 triplets at P4 with a
  session effect of .1, not more than 32.
- **S12.** The fairness contrast between institutions needs 8 triplets at P4 with a session
  effect of .1, not 4–6. The uptake contrast needs 6–20, not 4–10.
- **AD-S1.** The recovery test needs 30–36, not 24, and is not clean at the repair edge. The
  classifier is better than I said: I predicted that it would fail at the anchoring edge
  with the gate point unknown.

Two notes in my first draft of the scorecard gave a mechanism that no run had measured.
Both are withdrawn (closing record of the freeze).

## What the figures rest on

- **The effect is the model's own.** Power .90 is reached if people sit at the anchoring
  edge, the weakest point examined at which the paper's trap still holds (uptake ratio
  .48–.50; legitimacy .41 under HIGH against .88). A weaker gate than that is outside the
  paper's claim, and these samples would not detect it reliably.
- Ratings are plain: linear in legitimacy with gain .5 and noise 5.8 (10 for one item).
  I041 found the entitlement test much weaker under other rating shapes (.63–.98 at 72
  pairs with three items; .17–.46 at gain .25 with parked or non-responsive sliders).
  Those shapes were not rerun here, for any check.
- Forecasts have noise 12; one participant in ten does not revise. Each was varied alone,
  never together.
- Two members of a pair differ in rigidity and noise only. People differ in more ways.
- The classifier chooses among the model's own trajectories (three counts, four gate
  points) on a linear rating scale. People outside that family would show as a poor fit,
  which the calculation does not score.
- Requirements carry about one grid step of uncertainty: three draws of one cell gave 84,
  84 and 72 pairs here, and ±.03 in power between pools was seen in I044.
- Sessions of the individual design are taken as independent.
- Not simulated: shares in the individual design; a basket as a milestone with trading on;
  the classifier under session effects; stand-ins and dropouts.

## Decisions for the author

1. **Which steps are to be confirmatory.** The core is 504–648 people; the rival test adds
   384–576 and an institution contrast 240–360.
2. **The first wave:** a pilot, or the confirmatory study with its analysis frozen
   beforehand. 96 pairs cover both under the favourable count; if the count turns out to be
   40–80, a wave of that size is underpowered at the anchoring edge (288–336 pairs needed).
3. **One entitlement item or three.** Three bring the first wave from 192 people to 144.
4. **Whether to add a 4-close probe** to identify the revision rule (an app change).
5. **Whether the second probe pair stays a source.** A second record pair brings the rival
   test from 960 people to 576 (one-update rule).
6. **Market size for the live rung.** Four per market needs fewer people and more sessions.
7. **A stopping basket.** At the anchoring edge it multiplies the requirement by about
   three or more.

## Not done

- No change to the app; no specification of the first wave.
- No plan was approved; the steps are my proposal.
