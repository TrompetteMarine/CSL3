# Yoked ten-repetition design (specification for the pilot build)

Status: certified on synthetic cohorts only (KGi-DISS-I041; records
`records/yoked_cert_I041.txt` and `records/yoked_ad_I041.txt`). Not built in
oTree. Recruitment, ethics, payment, board wording, the production seed and any
registration are author decisions.

## The session (ten repetitions)

| repetition | what happens |
|---|---|
| 1 | rich round: ticket choice, 120 settlements shown as a summary (odds .75 / .35), fairness and entitlement ratings |
| 2–6 | deprivation rounds: the same, at odds .25 / .10 |
| 7–10 | four probe tickets: forecast, a record of 10 settlements (9 or 1 wins), forecast again |

- **Board.** HIGH: a trader winning at .72. LOW: a replay of the participant's own
  trailing record. In the rich round both members of a pair see the same board.
- **Ratings.** Fairness and entitlement on 0–100 sliders after every round.
- **Probe.** Two pairs of tickets (one favourable, one unfavourable record each);
  one pair about the participant's own draws, one about another trader's.

## Yoking

Participants come in pairs: one HIGH, one LOW, same schedule. A schedule is drawn
before the session by `experiment/tools/yoked_schedules.py` and fixes:

- the rich-round board;
- for every settlement, one draw that settles both tickets (the same ticket pays
  the same to both members; the better ticket wins whenever the worse one does);
- the HIGH board's draws;
- the probe tickets (which is favourable, whose record, the order shown).

People choose their own tickets and give their own ratings and forecasts. Each
schedule is used once in each arm, with the arm order drawn at random
(`allocation` in the schedule file). `verify()` in the same tool checks a file.

```
python experiment/tools/yoked_schedules.py --pairs 40 --seed <seed> --out experiment/schedules/pilot.json
```

If one member of a pair is lost, the other stays in every unpaired analysis; the
paired tests use complete pairs.

## What is recorded (per participant)

| variable | use |
|---|---|
| schedule id, arm, slot | pairing |
| ticket chosen in each round, wins in each round | checks; `PHI` |
| fairness rating after each round | `H1a`, `FREEZE`, association, `PHI` |
| entitlement rating after each round | `K3` |
| the eight probe forecasts | probe statistic `T` |
| attention check, completion time | exclusions (supplementary trimming interval) |

## Reporting set

Code: `experiment/analysis/yoked_analysis.py` (`decisions`). All tests one-sided
at .005.

| name | statement | statistic |
|---|---|---|
| H1a | fairness is lower under the HIGH board | last fairness rating, LOW minus HIGH within pairs, signed rank |
| D1 | learning from evidence is reduced | `ψ = mean(T_HIGH) / mean(T_LOW)`, upper Fieller limit below 1 |
| K3 | entitlement is higher under the HIGH board | last entitlement rating, HIGH minus LOW within pairs, signed rank |
| FREEZE | the lowest-rated third of HIGH revises less than half as much as LOW | upper limit of the uptake ratio below .5 |
| ASSOC_H | within HIGH, revision follows reported fairness | rank association of `T` and the last fairness rating |
| ASSOC_L | the same within LOW | same |
| PHI | warning: wins erode fairness | in LOW, slope of the change in the rating on the round's win share |

- **Confirmatory pair:** H1a, then D1 only if H1a rejects.
- **Supporting:** K3, FREEZE, the association by arm; PHI is a check on an
  assumption.
- **ASSOC_H is the only statistic that bears on a homogeneous slowdown of the HIGH
  arm.** A pooled association (the frozen `ASSOC`) is carried largely by the LOW
  arm and rejects when only LOW is gated; it is kept in the code for the record
  and is not part of the set.
- `TOPQ` (top quarter of HIGH by rating against the rest) is computed alongside.
  It has more power than ASSOC_H where a recovered minority of about a quarter
  exists and less at the anchoring edge.
- `ψ` is reported with its 99% interval; the trimming interval of I038 is the
  supplementary analysis when exclusions differ by arm.

## Certified performance (synthetic, full coupling, plain ratings at gain .5)

Decision rates at 72 pairs (144 participants), one-update rule | count rule:

| gate point | H1a | D1 | K3 | FREEZE | ASSOC_H | ASSOC_L | whole set with ASSOC_H |
|---|---|---|---|---|---|---|---|
| P0 strong anchoring | 1.00 | 1.00 | 1.00 | .89–.92 \| 1.00 | .00 \| .01 | .47 \| .39 | .00 \| .01 |
| P1 paper's values | 1.00 | 1.00 | 1.00 | .92 \| 1.00 | .27 \| .44 | .44 \| .36 | .27 \| .44 |
| P2 repair-ratio edge | 1.00 | 1.00 | 1.00 | .90–.95 \| 1.00 | .40 \| .68 | .18 \| .13 | .39 \| .68 |
| P3 speed edge | 1.00 | 1.00 | 1.00 | .89–.92 \| 1.00 | .37 \| .53 | .57 \| .54 | .36 \| .53 |
| P4 anchoring edge | 1.00 | .94 \| 1.00 | 1.00 | .90–.91 \| 1.00 | 1.00 | .38 \| .34 | .86 \| .99 |

Confirmatory pair by number of pairs (one-update rule): 36 pairs ≥ .99 at P0–P3
and .67 at P4; 54 pairs .85 at P4; 72 pairs .94–.95; 96 pairs .99.

ASSOC_H by number of pairs at P1 / P2 / P3:

| pairs | one-update rule | count rule |
|---|---|---|
| 72 | .27 / .38 / .35 | .49 / .68 / .53 |
| 144 | .58 / .76 / .69 | .83 / .96 / .87 |
| 216 | .76 / .91 / .88 | .95 / 1.00 / .97 |
| 288 | .89 / .98 / .96 | .99 / 1.00 / .99 |

(`TOPQ`: .37–.50 at 72 pairs, .71–.86 at 144, .89–.96 at 216 under the
one-update rule.)

False decisions at 72 pairs (one-update rule):

| world | H1a | D1 | FREEZE | ASSOC_H | pooled ASSOC | confirmatory pair | whole set with ASSOC_H |
|---|---|---|---|---|---|---|---|
| both members on the LOW board | .004 | .006 | .000 | n/a | (.82) | .000 | n/a |
| ratings move, gain does not | (1.00) | .005–.007 | .000 | .005 | .004 | .005–.006 | .000 |
| HIGH uniformly slowed, LOW ungated | (1.00) | (1.00) | (.05–.89) | not run | .005 | (1.00) | not run |
| HIGH uniformly slowed, LOW gated | (1.00) | (.99–1.00) | (.01–.67) | .006–.008 | **.19–.20** | (1.00) | .002–.008 |

Entries in brackets are true statements in that world, not errors. At 216 pairs
the pooled association rejects in .66 of samples in the last world; ASSOC_H
stays at .006.

## What the design can and cannot show

- **It shows, with power .94–1.00 at 72 pairs across the trap region,** that
  the HIGH board lowers reported fairness and reduces learning from evidence.
- **It does not separate the gate from a homogeneous slowdown of the HIGH arm at
  72 pairs.** That rests on ASSOC_H: .27–.40 at the central points under the
  one-update rule. About 216–288 pairs are needed for .90 (.89 at 288 at the
  paper's values; 144–216 under the count rule). At P0 the two are the same distribution and no sample size helps.
- **No statistic here shows mediation.** A within-arm association can come from a
  trait that links ratings and revision. Combined with a uniform slowdown that
  rival passes every test in the set.

## What yoking does and does not do

- **It costs nothing and breaks nothing.** Sizes hold; the paired and unpaired
  intervals for `ψ` agree within .003.
- **It does not add power.** H1a with yoked pairs against randomly re-matched
  pairs: .726 against .724 at 18 pairs and .990 against .990 at 36 at the
  weakest point; identical elsewhere.
- **Outcomes coincide only when both members pick the same tickets** in all five
  deprivation rounds. With model-like choices and independent choice noise that
  is 10–16% of pairs. The pilot will show how people actually choose.

## Known sensitivities

- **K3 depends on the rating scale.** At gain .25 its power is .65–.91 with plain
  ratings and .17–.46 when 15–20% of people park the slider. At gain .5 it is
  .63–.89 under the non-responsive shape. H1a is not affected (lowest cell .947).
- **Association rates carry about ±.03** from the simulated pool.
- Everything inherits the open human quantities: effective draws per summary,
  the revision rule, rating gain and noise, rigidity, ticket choice, and whether
  wins can erode fairness.

## What the pilot of this design will show (no sizes fixed here)

Ticket choices per round and the share of pairs with identical choices; the
control arm's absolute revision weight and the forecast noise; which revision
rule people follow (it sets the sample for ASSOC_H); the rating gain, noise and
parking rate; the entitlement path; the PHI slope; attention-check and dropout
rates by arm; completion time for ten repetitions.
