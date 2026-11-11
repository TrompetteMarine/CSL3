# The yoked design and its reporting set, certified on synthetic cohorts (KGi-DISS-I041, 2026-11-11)

Everything in this record is synthetic. Nothing has been tested on people. The
oTree build does not exist; the pilot specification is a separate step.

- **Freeze.** `freezes/00_freeze_I041.yaml` was pushed before any run; addendum
  AD-Y2 before its own run. Both scorecards are verbatim in the freeze.
- **Records.** `records/yoked_cert_I041.txt` (seed 138000) and
  `records/yoked_ad_I041.txt` (seed 138100); both re-run bit-identically.
- **Artefacts.** `experiment/YOKED_DESIGN.md` (the specification),
  `experiment/tools/yoked_schedules.py` (pre-drawn schedules and allocation),
  `experiment/analysis/yoked_analysis.py` (the reporting set; the same code
  scores a pilot data set).

## What was certified

Design S1x with yoked pairs: one HIGH and one LOW participant share a schedule
that fixes the rich-round board, one draw per settlement that settles both
tickets, the board draws and the probe tickets. People choose their own tickets.
Simulated pairs are two different people: independent rigidity and independent
ticket-choice noise. Decisions on 2,000 samples from 20,000 pairs per cell,
one-sided .005.

## Results at 72 pairs (144 participants)

One-update rule | count rule, full coupling, plain ratings at gain .5:

| gate point | H1a | D1 | confirmatory pair | K3 | FREEZE | ASSOC_H | whole set with ASSOC_H |
|---|---|---|---|---|---|---|---|
| P0 strong anchoring | 1.00 | 1.00 | 1.00 | 1.00 | .89–.92 \| 1.00 | .00 \| .01 | .00 \| .01 |
| P1 paper's values | 1.00 | 1.00 | 1.00 | 1.00 | .92 \| 1.00 | .27 \| .44 | .27 \| .44 |
| P2 repair-ratio edge | 1.00 | 1.00 | 1.00 | 1.00 | .90–.95 \| 1.00 | .40 \| .68 | .39 \| .68 |
| P3 speed edge | 1.00 | 1.00 | 1.00 | 1.00 | .89–.92 \| 1.00 | .37 \| .53 | .36 \| .53 |
| P4 anchoring edge | 1.00 | .94 \| 1.00 | .94 \| 1.00 | 1.00 | .90–.91 \| 1.00 | 1.00 | .86 \| .99 |

- **The confirmatory pair holds.** H1a then D1: .94–1.00 at 72 pairs; at 36
  pairs ≥ .99 at P0–P3 and .67 at the anchoring edge.
- **Sizes hold.** Both members on the LOW board: H1a .004, K3 .007, D1 .006.
  Ratings move but the gain does not: D1 .005–.007.
- **K3 is fragile.** It fails my claim under every rating shape but the plain
  one at gain .5: .81–.97 with parked sliders, .63–.89 when 20% of people do
  not respond, .78–.98 with lognormal gains,
  and .17–.46 at gain .25 with parked or non-responsive sliders. H1a is not
  affected (lowest cell .947).

## Finding 1: yoking buys no power

- With independent ticket-choice noise the two members pick the same ticket in
  all five deprivation rounds in 10–16% of pairs. In I040 it was 41–73% because
  the choice noise was shared, which no two people do.
- H1a with yoked pairs against randomly re-matched pairs at the weakest point:
  .726 against .724 at 18 pairs, .990 against .990 at 36. At gain .25: .570
  against .593.
- The paired and unpaired intervals for `ψ` give .936 and .939.
- **The I040 statement that yoking gives a small power gain (.76 against .71) is
  withdrawn.** It rested on shared choice noise.
- What is left of the case for yoking: it is free, it balances the allocation,
  and it makes the same-outcome hypothesis of T13 hold in whichever pairs choose
  alike. The pilot will show how many do.

## Finding 2: the pooled association is not a test of the gate against a homogeneous slowdown

The run showed that pairs with both members on the LOW board reject on the
pooled association in .82 of samples. Under the model the gated LOW arm carries
an association of its own. The rival scored in I039 and in the main record had
an ungated LOW arm. Addendum AD-Y2 scored the rival that matters: LOW gated as
in the model, HIGH uniformly slowed.

| world (one-update rule) | pairs | pooled ASSOC | ASSOC_H | whole set, pooled | whole set, ASSOC_H |
|---|---|---|---|---|---|
| the model, P1 | 72 | .67–.70 | .27 | .63–.66 | .27 |
| HIGH uniformly slowed, LOW gated, P1 | 72 | .19 | .008 | .16 | .008 |
| the same | 216 | .66 | .006 | .65 | .006 |
| the same, P4 | 72 | .20 | .006 | .009 | .002 |

- In the model the LOW arm carries as much of the pooled statistic as the HIGH
  arm: alone, LOW rejects in .44 / .18 / .57 and HIGH in .27 / .40 / .37 at
  P1–P3.
- **The I039 figure for this rival (false positives .0035 for the conjunction
  with `ψ < 1`) is scoped to a world with no state dependence in LOW.** With a
  gated LOW arm the pooled conjunction passes the rival in .16 of samples at 72
  pairs and .65 at 216.
- **Adopted:** the association is reported by arm. ASSOC_H is the statistic that
  bears on a homogeneous slowdown. It holds its size (.003–.008) and has this
  power at P1 / P2 / P3:

| pairs | one-update rule | count rule |
|---|---|---|
| 72 | .27 / .38 / .35 | .49 / .68 / .53 |
| 144 | .58 / .76 / .69 | .83 / .96 / .87 |
| 216 | .76 / .91 / .88 | .95 / 1.00 / .97 |
| 288 | .89 / .98 / .96 | .99 / 1.00 / .99 |

- The top-quarter cut (TOPQ) does better at P1–P3 (.37–.50 at 72 pairs, .89–.96
  at 216) and worse at the anchoring edge (.94 against 1.00). It was the best of
  three cuts on this model in I040. Its advantage depends on a recovered
  minority of about a quarter.
- **FREEZE does not discriminate either.** Under a uniform slowdown the
  lowest-rated third does revise less than half as much as LOW (.67–.89 at P1).
- **At P0 nothing discriminates.** When everyone in HIGH has stopped, the gate
  and a homogeneous shutdown are the same distribution (ASSOC_H .004–.006).

## What the design supports, by claim

| claim | statistic | at 72 pairs | to reach .90 |
|---|---|---|---|
| the HIGH board lowers fairness | H1a | 1.00 | 18–36 pairs |
| it reduces learning from evidence | D1 | .94–1.00 | 72 at the anchoring edge, 36 elsewhere |
| it raises entitlement | K3 | 1.00 plain; .63–.98 other shapes | depends on the rating gain |
| the reduction is not a homogeneous slowdown | ASSOC_H | .27–.40 (1.00 at P4) | 216–288 pairs; 144–216 under the count rule |
| the reduction runs through fairness | none | not identified | a trait linking rating and revision, with a uniform slowdown, passes every test |

## Predictions that failed (kept)

1. K3 at least .90 under the other rating shapes: .63–.98 at gain .5.
2. FREEZE at most .05 under a homogeneous slowdown: .89 at P1.
3. Count-rule gain in the whole set of 5–15 points: 14–16.
4. LOW-arm association .30–.55 at P1–P3: .18 at P2, .57 at P3.
5. Whole set with TOPQ at least .85 at P4: .82.
6. TOPQ at least .72 at 144 pairs and .90 at 216 at P1: .71 and .89.
7. HIGH-arm statistics at most .008 under the rival: .0085 in one row of eight
   (TOPQ at P1, 216 pairs; Monte Carlo standard error .0016).

## What this rests on

- Power figures take the model as the truth, at full coupling, with the assumed
  rigidity mix, rating noise 5.8 and forecast noise 12.
- Association rates carry about ±.03 from the simulated pool (two independent
  pools: .667 and .696 at P1, .780 and .825 at P3).
- The uniform-slowdown rival is set at the HIGH arm's mean gain. Other
  slowdowns were not scored.
- ASSOC_H conditions on a rating taken after treatment. It is a model-based
  reading, not a causal contrast.

## Decisions for the author

1. **Sample.** 72 pairs certify the confirmatory pair. Separating the gate from
   a homogeneous slowdown needs 216–288 pairs under the one-update rule. The
   pilot's revision rule decides which.
2. **Association statistic.** ASSOC_H (shape-free) or TOPQ (more power if about
   a quarter recover). Fix one before the data.
3. **K3.** Keep as supporting only; its power depends on a rating gain that the
   pilot measures.
4. **Next step.** The oTree build of this design, or the pilot specification
   built on this ledger.
