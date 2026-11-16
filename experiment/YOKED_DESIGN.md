# Yoked ten-repetition design (specification for the pilot build)

Status: certified on synthetic cohorts only (KGi-DISS-I041, records
`records/yoked_cert_I041.txt` and `records/yoked_ad_I041.txt`; the prediction-market
probe KGi-DISS-I043, record `records/basket_cert_I043.txt`). Built in oTree as
`experiment/diss_market` (KGi-DISS-I042, redesigned I043; see `MARKET_APP.md`); not
run on people. Recruitment, ethics, payment, the wording of the board and of the
forecast sources, the production seed and any registration are author decisions.

An interactive variant, in which the participants' orders set the clearing prices
(design W, KGi-DISS-I044), is specified in `LIVE_ECONOMY.md`. It is certified on
simulated sessions and not built; this document and the app are unchanged by it.

## The session (ten repetitions)

The statistical skeleton is that of I041. Since I043 it is presented as a basket
economy followed by prediction markets (design B); what changed statistically is
listed under "The prediction markets" below.

| repetition | what happens |
|---|---|
| 1 | rich procurement round: the participant orders one of two goods; the goods market clears 120 times; the order fills whenever the clearing price is at or below the cap (fill chances .75 / .35); fairness and entitlement ratings |
| 2–6 | deprivation rounds: the same, at fill chances .25 / .10 |
| 7–10 | four prediction markets ("Will ASSET close above X?"): forecast, evidence, forecast again, then a bet (YES, NO or pass) |

- **Prices.** The clearing price of the ordered good is a display of the schedule's
  own draw: `price = cap · exp(σ (z(u) − z(p)))`, with `u` the settlement draw and
  `p` the good's fill chance, so the order fills exactly where the schedule says.
  Only the ordered good's own price path is shown. Every filled order is one good
  and one point; six goods make a basket (a count, with no quota).
- **Board.** HIGH: a trader whose orders fill at .72. LOW: a replay of the
  participant's own trailing record. In the rich round both members of a pair see
  the same board. The board shows filled orders only.
- **Ratings.** After every procurement round, three fairness items and one
  entitlement item on 0–100 sliders. The fairness score is the mean of the three.
  The certified rating noise (5.8) is that of a three-item scale; the entitlement
  test was certified at the same noise, which one item does not deliver.

## The prediction markets (I043)

Four markets, the same for every schedule of a file, met in an order the schedule
fixes. Each shows a price history that ends on the line the asset has to close
above; the history carries no information about the close.

- **Two pairs** (one favourable, one unfavourable market each). In one pair the
  evidence is a **record**: ten trial closes held with the participant's own
  tickets (9 or 1 above the line). In the other it is a **source**: the forecast
  of another trader (90% or 10% in the development build; in a pilot, a real
  earlier forecast inside 80–100 or 0–20, described identically in both arms).
- **Forecasts.** One before the evidence and one after, on 0–100 in steps of 5.
  `T` is unchanged: the mean over the two pairs of the revision after the
  favourable market minus the revision after the unfavourable one.
- **Bet.** After the second forecast a price is posted (50) and the participant
  buys YES, buys NO or passes, from a 10-point allowance; a winning ticket pays
  20. The markets settle after the closing questions.
- **What changed statistically.** (S1) One of the two pairs now measures the weight
  on a source's forecast, assumed to be `κ_s · g` with `g` the gate and `κ_s`
  unknown (.2 to .5 examined). (S2) The bet adds a second read-out of the updated
  belief, under an assumed betting rule.
- **Kept out of the session:** informative prices beyond the ordered good's own
  path, the other good's prices, a two-stage route task, live order matching,
  mixed-good baskets, a stated basket quota.

## Yoking

Participants come in pairs: one HIGH, one LOW, same schedule. A schedule is drawn
before the session by `experiment/tools/yoked_schedules.py` and fixes:

- the rich-round board;
- for every settlement, one draw that settles both tickets (the same ticket pays
  the same to both members; the better ticket wins whenever the worse one does);
- the HIGH board's draws;
- the markets (which is favourable, which kind of evidence, the order met; since
  I043 the four markets themselves belong to the file, not to the schedule).

People choose their own tickets and give their own ratings and forecasts. Each
schedule is used once in each arm, with the arm order drawn at random
(`allocation` in the schedule file). `verify()` in the same tool checks a file.

```
python experiment/tools/yoked_schedules.py --pairs 40 --seed <seed> --format 3 --out experiment/schedules/pilot.json
```

`--no-social` draws a file with two record pairs (for a seed wave, which has no
earlier forecast to show); `--markets-from FILE` reuses another file's markets, so
that a pilot can show forecasts collected in the seed wave.

If one member of a pair is lost, the other stays in every unpaired analysis; the
paired tests use complete pairs.

## What is recorded (per participant)

| variable | use |
|---|---|
| schedule id, arm, slot | pairing |
| ticket chosen in each round, wins in each round | checks; `PHI` |
| fairness score (three items) after each round | `H1a`, `FREEZE`, association, `PHI` |
| entitlement rating after each round | `K3` |
| the eight forecasts | statistic `T`, and `T` by kind of evidence |
| the four bets | bet statistic `B`; `BET` |
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
| BET (I043) | bets follow the evidence less under the HIGH board | `B` = mean over pairs of (bet on the favourable market − bet on the unfavourable one) / 2, with YES 1, pass 0, NO −1; LOW minus HIGH within pairs, signed rank |

- **Confirmatory pair:** H1a, then D1 only if H1a rejects.
- **Supporting:** K3, FREEZE, the association by arm, BET; PHI is a check on an
  assumption. BET rests on an assumed betting rule and on a posted price of 50.
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

## Certified performance with one source pair (I043)

Record `records/basket_cert_I043.txt` (20,000 simulated pairs per gate point, 2,000
samples, seed 139000). Source weight `κ_s · g`; bets by the assumed rule (YES if
belief + N(0, 8) exceeds the price by 5, NO if it falls 5 below, else pass).

| at 72 pairs | κ_s = .5 | κ_s = .35 | κ_s = .2 |
|---|---|---|---|
| D1 and confirmatory pair, P0–P3, both rules | 1.000 | 1.000 | 1.000 |
| D1, P4, one-update rule | .947 | .893 | .790 |
| D1, P4, count rule | .990 | .990 | .966 |
| BET, P0–P3 | 1.000 | 1.000 | 1.000 |
| BET, P4, one-update rule | .994 | .973 | .916 |
| FREEZE, P1–P3, one-update rule | .90–.93 | .77–.84 | .59–.60 |
| ASSOC_H, P1 / P2 / P3, one-update rule | .28 / .41 / .31 | .23 / .32 / .24 | .16 / .18 / .19 |
| D1 from the source pair alone, P1–P3, one-update rule | 1.00 | .96–.97 | .45–.49 |

- At the anchoring edge (P4) under the one-update rule, 96 pairs give .973 at
  κ_s = .35 and .913 at κ_s = .2.
- Sizes: D1 .004–.007 and BET .002–.006 when ratings move and the gain does not.
- The source pair costs power wherever people give a source's forecast little
  weight. `κ_s` is a human quantity no simulation supplies; the pilot estimates it
  from the LOW arm's source pair.

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

Orders per round and the share of pairs with identical orders; the control arm's
absolute revision weight after a record and after a source's forecast (`κ_s`), and
the forecast noise; which revision rule people follow (it sets the sample for
ASSOC_H); how people bet at a posted price of 50 (shares of YES, NO and pass by
forecast); the rating gain, noise and parking rate; the entitlement path; the PHI
slope; whether a price curve is read as a record of fills (recall of the round's
count would show it; not built); attention-check and dropout rates by arm;
completion time for ten repetitions.
