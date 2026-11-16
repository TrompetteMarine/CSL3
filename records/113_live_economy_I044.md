# The yoked design as a live economy (KGi-DISS-I044, 2026-11-16)

Simulation only. Nothing has been run on people and no screen of a live market has been
built. Every result is conditional on assumed rules for how traders order and trade.

- **Request.** Make participants' decisions affect each other: basket orders that create
  the clearing prices, the cash left after procurement carried into a prediction market,
  bets only on a good the physical economy does not trade, trading as on a prediction
  platform. Then: full experimental control of the abstract economy, with prices set by
  theory (a Walrasian auctioneer). The session must stay informative for DISS.
- **Source recovered.** The Social Cognition task draft (research proposal, 13 pages). Its
  Protocol III is this economy; its legitimacy extension is this programme.
- **Decisions taken by the author (dialog).** Lab first, online later. The reference is a
  live neighbouring market. Supply is scripted, demand is live. The claim market trades
  against an automated market maker.
- **My two readings, not confirmed.** "Remaining fees" is the cash a trader holds after
  procurement. "Things they are not buying" is a good of a simulated sector with pre-drawn
  events.
- **Freeze.** `freezes/00_freeze_I044.yaml`, pushed before any code. Five addenda, each
  pushed before its run. Both scorecards are verbatim in it.
- **Records.** `records/market_cert_I044.txt` (seed 140000; re-run bit-identical; the first
  run is kept as `market_cert_I044_run1.txt`), `records/sorting_benchmark_I044.txt`.
- **Specification for the build.** `experiment/LIVE_ECONOMY.md`.

## What interaction changes

1. **The market is the unit.** HIGH and LOW cannot share a market. Treatment is assigned
   per session and tests run on market values. The yoked pair becomes a pair of sessions
   on one script.
2. **Own outcomes are equal across arms in distribution only,** and only because the focal
   market runs the same script in both arms and the reference comes from another market.
3. **Cash links procurement to the bets.** A position mixes belief with bankroll. The DISS
   read-out stays the private forecast, taken before trading.

## The economy (design W)

Everything is scripted before the session: the supply of each good at each clearing, each
trader's private value at each clearing, tie-breaks, the claims, interventions.
Participants only submit orders. The engine is a function of script and orders, so any
session can be replayed under other orders.

- **Session.** Two markets of N traders, no trade between them; each sees the other's
  fills. In a HIGH session the neighbour stays rich; in a LOW session both markets are
  scarce.
- **Procurement, six rounds of 120 clearings.** One standing order per round. At each
  clearing a Walrasian auctioneer clears each good: every trader bidding for it wants one
  unit, the scripted units go to the highest bids, the price is the highest losing bid or
  the reserve. That is the lowest market-clearing price, and under it bidding one's value
  is a dominant strategy, so the engine can bid the value. A filled unit earns value minus
  price.
- **Claims.** On a simulated good only. Private forecast, private evidence, private
  forecast; then trading against a market maker with the cash earned; settlement at the
  end.

Two gaps against the request, both stated here and not hidden in the design:

- **The certified order is still "which good to bid for",** not a basket over the two
  goods. See "Baskets and the theory" below.
- **Nobody sells in procurement.** With scripted supply the traders' bids meet scripted
  units. Participants buy and sell among themselves through the claim market only.

## What the certification says

**The kernel is the certified one.** With one trader, fixed fill chances and a board, the
kernel step used here gives legitimacy at probe time .111 under HIGH and .871 under LOW
(certified .109 and .869). Every price in 10.2 million checked clearings clears its market.

**The confirmatory pair survives, on markets.** Twelve HIGH and twelve LOW sessions of two
markets of six, frozen supply, one-sided .005, t quantiles on market values:

| gate point | fairness (H1a) | learning (D1), one-update rule | D1, count rule | D1 with 8 + 8 sessions | D1 with a session effect of .2 |
|---|---|---|---|---|---|
| P0 strong anchoring | 1.000 | 1.000 | 1.000 | 1.000 | .999 |
| P1 paper's values | 1.000 | 1.000 | 1.000 | .991 | .967 |
| P2 repair-ratio edge | 1.000 | .999 | 1.000 | .989 | .943 |
| P3 speed edge | 1.000 | .999 | 1.000 | .987 | .955 |
| P4 anchoring edge | 1.000 | .894 | .979 | .653 | .410 |

- The fairness column is for 12 + 12 sessions without a session effect. At P4 it is .966
  with 8 + 8 sessions and .910 with a session effect of .2.
- With supply calibrated to the board's rate (below) the P4 cell of the third column is
  .93–.95.

**Tests on individual traders are not valid here.** The model alone correlates ratings
within a market (+.13 under HIGH), because a market shares one reference path. With session
effects at an intraclass correlation of .1 to .2 the individual-level tests of the earlier
design reject a true null in 2.0–2.5% (learning) and 2.4–4.8% (fairness) of samples at a
nominal 0.5%. The market-level tests reject in .40–.85% (Monte Carlo standard error .16).

**Four design rules follow from the model.**

| rule | evidence |
|---|---|
| Orders must be all-or-nothing | If every bidder receives a share, legitimacy under HIGH stays at .938 and the learning test rejects in .025. Measured per clearing, HIGH arm: erosion .0052 against repair .0026 with unit orders; .0030 against .0060 with shares |
| The board must show the neighbour's recent fills | With totals since the start of the session the control arm's legitimacy falls from .935 to .684, and the learning test from 1.000 to .856 at the paper's values and from .894 to .271 at the anchoring edge |
| Supply must be calibrated to fill rates, per market size | Under one fixed supply the HIGH arm's legitimacy is .325, .175, .111 for 4, 6, 8 traders. Calibrated so that the neighbour fills .72 of its orders: .102, .068, .059 |
| More, smaller markets | 72 traders per arm at the anchoring edge, session effect .1, calibrated supply: .861 with 18 markets of 4, .811 with 12 of 6, .633 with 9 of 8 |

**Bid shading does little.** Persistent shading of up to half the value changes the control
arm's legitimacy from .935 to .925; the learning test stays at 1.000 at the paper's values
and goes from .894 to .850 at the anchoring edge.

**Own outcomes are balanced, except at the extreme.** Fill rates in scarce rounds differ
between arms by .0013 or less at P1–P4. At P0 the HIGH arm fills 4.5% fewer orders:
traders who have stopped learning sort worse between the goods. Cash earned is within 1%.

## How many people

A **twin pair** is a HIGH and a LOW session on one focal script, with the focal markets as
units. A **triplet** is a LOW session whose two markets each run the focal script of one
HIGH session; the triplet is the unit of analysis. Six per market, calibrated supply,
learning test at the anchoring edge, one-update rule:

| layout | sessions | people | of whom units of the test | no session effect | session effect .1 |
|---|---|---|---|---|---|
| twin pairs: 12 HIGH + 12 LOW | 24 | 288 | 144 | .926 | .774 |
| triplets: 12 HIGH + 6 LOW | 18 | 216 | 144 | .900 | .588 |
| triplets: 16 HIGH + 8 LOW | 24 | 288 | 192 | .980 | .770 |

- At the paper's values every cell is .987 or more. The fairness test at the anchoring
  edge is .99 or more, except .936 for 18 sessions with the session effect.
- **For a given number of people the triplet layout is at least as good.**
- **The two markets of a LOW session are not independent.** Their mean fairness ratings
  correlate at +.16 to +.29. Taken as independent, the tests reject a true null in
  .8–1.1% with a session effect of .1. By triplets they keep their level (.35–.80%).
- **The individual design B needs 144 people** for 72 pairs and gives .94 at the anchoring
  edge with two record pairs. The live economy costs twice the people for about the same
  power there, and less if sessions differ.
- Power figures carry about ±.03 from the simulated pool: the first row came out as .951
  and .811 with other rating and forecast draws on the same sessions. The lower figures
  are used.

## Collective read-outs

**Procurement gives none.** The share of scripted units sold differs between arms by less
than .01, with or without a switch of the plentiful good; no test has power.

**A long news sequence separates the gate from a uniform slowdown.** Twelve successive
records on one claim, a forecast after each. A population with one common weight closes
the gap along a known curve; a gated population stops early. The first statistic (PLAT)
failed: one inattentive trader in ten bends the path enough for it to reject in up to .48
of samples with no gate at all. Dividing by the control arm's late closure (PLAT2,
addendum) removes that:

| 72 traders per arm | gate world | uniformly slowed HIGH arm | HIGH-arm association of I041 at 72 pairs |
|---|---|---|---|
| P1, one-update rule | .607 | .001 | .27 |
| P1, count rule | .961 | .007 | .44–.49 |
| P4, both rules | .993, .933 | .004, .008 | 1.00 |
| P0, both rules | .040, .083 | .007, .005 | at its size |

- The last column is the earlier test of the same rival, on four single-record probes.
  PLAT2 uses twelve records per claim.
- **It does not separate the gate from disengagement that differs by arm.** With 30%
  inattentive in a uniformly slowed HIGH arm it rejects in .066 at P1 under the one-update
  rule and in .48–.56 where closures are large.
- This read-out needs repeated evidence, not interaction. A market with news is the
  natural frame for it.

**The price repeats the forecasts, with less power.** Under the assumed trading rule the
ratio of price responses is .200 where the forecast ratio is .190 (P1). The price test
rejects in .94 at P1 and .45 at the anchoring edge (forecasts: 1.000 and .894). Within HIGH
markets cash and legitimacy are nearly uncorrelated (−.08 to +.09), except at P0 (+.58).

## Baskets and the theory

The specification gives the arguments and the references. In short:

| institution | market-clearing prices | DISS, in the model |
|---|---|---|
| one unit per trader and clearing, lowest clearing price (certified) | exist; bidding the value is dominant | the contrast holds |
| divisible goods, every bidder receives a share | exist | the contrast vanishes |
| several units per trader and clearing | exist; a uniform price is no longer truthful | not simulated |
| a basket with a completion payment, cleared at each clearing | may not exist (the goods are complements) | not simulated |

- **The textbook exchange economy and the model pull apart.** Divisibility gives existence
  and removes the lumpy outcomes on which the model's delegitimation runs.
- **A basket that keeps the certified institution** is a target for the round, paid on
  completion and served by unit orders: the trader decides how many clearings to bid for
  each good. Not certified.
- **Benchmark.** With values uniform on (0, 1), `n` bidders and `k < n` units, the expected
  price is `(n − k)/(n + 1)` and a bidder's expected surplus `k(k + 1)/(2n(n + 1))`. Six
  traders in a scarce market split 4 : 2 if they sort on surplus and 5 : 1 if they sort on
  the chance of a fill; the fill rate is .19–.20 either way. The model's traders fill .18.

## Predictions that failed

Sixteen sets of predictions were frozen: eleven claims and five addenda. Five passed in
full: the institution (W2), power (W5), size (W6), shading (W8) and the measured erosion
and repair (AD-W4). The others:

- **Levels (W1).** Legitimacy under HIGH is .175, not .06–.16; under LOW .935, not .80–.90.
  The rich neighbour fills .664 of its orders, not the certified board's .72.
- **Own outcomes (W3).** At P0 fill rates differ by .0084 against my .005.
- **Board (W4).** Direction right; control-arm legitimacy .684 against my .65 or less, and
  the ratio under the recent-fills board .190 against .16 or less.
- **Market size (W7).** Order right; the spread at the anchoring edge is .196, not .15.
- **Procurement (W9).** The main statement held. I expected traders to stay on the
  formerly plentiful good by .10 more under HIGH; it is .03. Three of the four differences
  in units sold have the opposite sign to mine (−.003 to −.005).
- **Repeated news (W10).** PLAT has neither the power I said (.556 against .70) nor its
  level.
- **Price (W11).** One cell at .888 against .90.
- **PLAT2 (AD-W1).** Two power cells off (.933 against .95; .083 against .05 at P0). I
  said differential disengagement would defeat it at P1 under the one-update rule; there
  it rejects in .066.
- **Calibrated supply (AD-W2).** Legitimacy under HIGH is .068 with six traders, lower than
  the certified .109 by more than my .03.
- **Dependence inside a LOW session (AD-W3).** I predicted a correlation between −.20 and
  +.05; it is +.24. I reasoned that one market's luck is the other's grievance. In the
  kernel a market's own fills raise its own aspiration too, so the two markets carry
  nearly the same aspiration.
- **Layouts (AD-W5).** One cell: fairness .936 against my .95.

Errors of mine found while working:

- **First run.** The rival world of the repeated-news test counted every trader with
  legitimacy 0 as inattentive. The first record is kept; all other sections are
  bit-identical in the corrected run.
- **Draft of this memo.** It costed the design at 216 people by counting both markets of a
  LOW session as control units, which no test had used; it explained the result on shares
  without a measurement; it counted five claims as passed where the scorecard said four.
  Addenda AD-W3 to AD-W5 replaced the first two before anything was committed.

## Limits

- The kernel has no rule for bidding, basket composition or trading. The order rule is its
  binary choice of a good; the trading rule is assumed.
- Session effects in people are unknown; .1 and .2 are examined.
- Layouts were compared for six per market only.
- Not simulated: baskets as round targets; the long news sequence under calibrated supply;
  dropouts and stand-ins; a neighbour whose supply follows its demand.
- Not recomputed at market level: the entitlement test, FREEZE, the association by arm,
  the PHI flag.
- The dominant-strategy property of the price rule was checked numerically, not
  machine-checked.

## Decisions for the author

1. **Confirm the two readings** (cash after procurement; a simulated good for the claims).
2. **Market size and layout.** The simulation favours 4 to 6 traders and triplets.
3. **Does the trader bid, or does the engine bid the value?** The second keeps the task to
   one decision per round and is incentive-compatible.
4. **Baskets.** A count of goods as now, or a round target with a completion payment. The
   second needs a certification under an assumed rule for how people split.
5. **The long news sequence.** Twelve records on some claims, replacing or added to the
   single-record ones.
6. **What a trader sees of the own market** beyond the price.
7. **The market maker's liquidity** and the conversion of cash to bankroll and to money.
   The maker's loss is at most liquidity × ln 2 per claim and market.
8. **Empty seats and dropouts.**

## Not done

- No oTree build of a live market (groups, synchronised rounds, live claim market).
- No pilot specification.
- No change to the built individual app, which stays as it is.
