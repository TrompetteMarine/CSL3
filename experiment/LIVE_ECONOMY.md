# The live economy (design W): specification for the build

Status: certified on simulated sessions only (KGi-DISS-I044). Nothing is built and nothing
has been run on people. The simulated traders order and trade by assumed rules. Group
size, baskets, wording, payment, recruitment and ethics are author decisions. The
individual app (`MARKET_APP.md`, design B) is unchanged and stays usable.

Record: `../records/market_cert_I044.txt` (seed 140000; re-run bit-identical) and
`../records/sorting_benchmark_I044.txt`. Freeze and scorecards:
`../freezes/00_freeze_I044.yaml`. Memo: `../records/113_live_economy_I044.md`. References:
`../freezes/00_citation_verification_I032.md`, I044 addendum.

Gate points P0–P4, the gate kernel and the two revision rules are those of
`YOKED_DESIGN.md`. Power is at one-sided .005.

## What the experimenter controls

Everything random is drawn before the session and stored in a script:

- the units of each good that arrive at each clearing, in each market;
- every trader's private value at each clearing;
- tie-breaks;
- the claims: events, evidence, settlement;
- interventions, each with its round and clearing.

Participants submit orders and nothing else. The engine is a function of script and
orders: the same script and the same orders give the same session to the last price.

- **Twins.** Sessions that are to be compared run the same script.
- **Replay.** A recorded session can be run again under other orders: the model's traders,
  or another session's people.
- **Interventions.** An intervention is the same event in every session that carries it.

| intervention examined | result in the model |
|---|---|
| the neighbour's supply, rich or scarce | the treatment (below) |
| the plentiful good switches at round 5 | learning test 1.000 at P1; .842 at P4 against .894 without |
| clearing by shares instead of units | the contrast vanishes (below) |
| board with totals since the start instead of recent fills | the control arm is contaminated (below) |
| rich supply scaled to the market's size | equal dose across sizes (below) |

Not simulated: a shock inside a round, a reserve price, withdrawing the rich neighbour in
mid-session.

## The session

Two markets of N traders in one room, a focal market and a neighbour. No trade between
them. Each market sees the other's fills. The arm is a property of the session.

- **HIGH.** From round 2 the focal market is scarce and the neighbour stays rich.
- **LOW.** From round 2 both markets are scarce.
- **Round 1** is rich in both markets in both arms.

| stage | what happens |
|---|---|
| procurement, rounds 1–6 | one standing order per round; the market clears 120 times; after each round three fairness items and one entitlement item |
| claims | claims on a simulated good; private forecast, private evidence, private forecast; then trading against a market maker; settlement after the closing questions |

The traders of a rich neighbour are participants like the others. Their fills are the
reference; their own legitimacy stays at .98–1.00 in the model; they are not units of the
confirmatory tests.

## Procurement: the auctioneer

One good at one clearing: `k` scripted units, `n` bidders, each wants one unit.

- The units go to the `k` highest bids (ties in the script's order).
- The price is the highest losing bid, or the reserve (0) when no bid loses.
- A filled trader earns value minus price, in cash.

**The price clears the market and is the lowest that does.** At most `k` bids lie above
it and at least `k` at or above it; any lower price leaves `k + 1` bids above. Checked at
10.2 million clearings of the run. For buyers who want one unit each, a market-clearing
price vector that is best for the buyers exists across several goods as well (Demange,
Gale & Sotomayor 1986).

**Bidding one's value is a dominant strategy.** Fix the other bids for the good and let `c`
be the `k`-th highest of them (the reserve if there are fewer). A trader is filled exactly
when the own bid is above `c`, and then pays `c`, which the own bid does not move. A bid
equal to the value is filled exactly when a fill is worth having. This is the argument for
one object sold at the second-highest bid (Vickrey 1961). Checked numerically: no change of
one bid gains anything in 200 clearings. Not machine-checked.

**So the engine can bid the value for the trader.** The trader's decision is the order of
the round: which good to bid for. That is the certified reading.

Two limits of the property:

- It concerns the bid, given the good. Which good to bid for is strategic; the benchmark
  is below.
- It needs one unit per trader and clearing. When a trader wants several units a uniform
  price invites lower bids on the later units (Ausubel et al. 2014).

### Institutions compared

| institution | prices | DISS, in the model |
|---|---|---|
| unit orders, lowest clearing price (certified) | exist; truthful | the contrast holds |
| every bidder receives a share (divisible goods) | exist | the contrast vanishes: legitimacy under HIGH stays at .938, the learning test rejects in .025 |
| several units per trader and clearing | exist; not truthful | not simulated |
| a basket with a completion payment, cleared at each clearing | may not exist | not simulated |

**Why shares remove the contrast.** The kernel erodes legitimacy when an outcome falls
short of aspiration by more than a tolerance and repairs it otherwise. Per clearing in
scarce rounds, HIGH arm, P1:

| | erosion | repair | clearings inside the tolerance |
|---|---|---|---|
| unit orders | .0052 | .0026 | .21 |
| shares | .0030 | .0060 | .48 |

With all-or-nothing fills four clearings in five are misses and erosion runs at twice the
repair. With shares a clearing that brings any unit gives every bidder something, and the
balance reverses. The model's delegitimation needs lumpy outcomes.

**Why a completion payment can leave no clearing prices.** One square and one circle
arrive. Trader 1 completes a basket with both, worth 3, and values neither alone. Trader 2
wants one unit of either, worth 2.

- If trader 1 holds both, neither price may tempt trader 2: both are at least 2, the pair
  costs at least 4, and trader 1 does not want it.
- If trader 2 holds one unit and the other is unsold, the unsold one is free. Trader 2
  prefers the free one unless the held one is free too, and with both free trader 1 wants
  the pair.
- Any other allocation leaves a unit unsold, or alone with trader 1, who pays nothing for
  it. That unit is free, and the same two steps apply.

No prices clear this market (`test_market_I044.py` searches a grid). Market-clearing
prices are guaranteed with indivisible objects when the objects are substitutes for every
buyer (Kelso & Crawford 1982, shown for a labour market with discrete choices). A
completion payment makes them complements.

**A basket that keeps the certified institution.** The basket is a target for the round
("x squares and y circles by the end of the round"), paid on completion and served by unit
orders: the trader decides how many of the 120 clearings to bid for each good. Every
clearing stays a unit market. Not certified: it needs an assumption on how people split,
and it adds one outcome per round (completed or not) to the outcome per clearing.

### Benchmark: where competitive traders would sort

Values uniform on (0, 1), `n` bidders, `k < n` units: the expected price is
`(n − k)/(n + 1)` and a bidder's expected surplus `k(k + 1)/(2n(n + 1))`; with `k ≥ n` the
price is 0 and the surplus 1/2. A split of the traders between the goods is an equilibrium
when nobody gains by changing good (`analysis/sorting_benchmark_I044.py`).

| scarce market | split on surplus | split on the chance of a fill | fill rate | expected price, plentiful \| other |
|---|---|---|---|---|
| 4 traders | 3 : 1 | 3 : 1 | .196 | .60 \| .41 |
| 6 traders | 4 : 2 | 5 : 1 | .200, .194 | .62 \| .57, .68 \| .37 |
| 8 traders | 6 : 2 | 6 : 2 | .199 | .69 \| .54 |

- The model's traders fill .18 of their orders in scarce rounds: they crowd the plentiful
  good a little more than the benchmark.
- Surplus per trader and clearing is .05–.07 in a scarce market and .31–.35 in a rich one.
  The rich round earns about as much cash as the five scarce rounds together.

## What a trader sees

- The own order, the price path of the good bid for, the own fills, the own cash.
- **The other market's fills over its last 15 clearings.** Never its total since the start
  of the session: with totals the control arm's legitimacy falls from .935 to .684 and the
  learning test from 1.000 to .856 at P1 and from .894 to .271 at P4.
- Nothing about arms.

## Supply

- Units of a good per clearing: Binomial(N, π).
- Scarce market: π = (.15, .05) for the plentiful and the other good.
- Rich market: π = (.55, .22) times a factor by market size: 1.15 for 4 traders, 1.10 for
  6, 1.05 for 8. The model's rich neighbour then fills .71–.72 of its orders, the level of
  the certified board.
- **Why the factor.** Fewer traders waste more of a rich supply. Unscaled, legitimacy under
  HIGH is .325, .175, .111 for 4, 6, 8 traders; scaled, .102, .068, .059.
- **With people** the neighbour's fill rate depends on how they sort between the goods.
  The factor has to be set again on pilot orders. Alternative, not simulated: let the
  neighbour's supply follow its demand, which pins the rate.

## Claims

- **On a simulated good only.** Nobody in the room trades it. Its events are scripted, so
  evidence is the same in twin sessions.
- **Sequence per claim.** Forecast (0–100), evidence, forecast, trading. `T` is computed
  from the two private forecasts as before. Trading does not enter `T`.
- **Market maker.** A logarithmic market scoring rule (Hanson 2007) with liquidity `b`.
  With `q_Y`, `q_N` the shares sold so far, the cost function is
  `C = b · ln(exp(q_Y/b) + exp(q_N/b))`, a trade costs the change in `C`, the YES price is
  `exp(q_Y/b) / (exp(q_Y/b) + exp(q_N/b))`, YES and NO prices sum to 1, a winning share
  pays 1.
- **What it costs the experimenter.** If YES wins the maker has collected `C − b · ln 2`
  and pays `q_Y ≤ C`: the loss per claim and market is at most `b · ln 2` (41.6 at
  `b = 60`).
- **Assumed trading rule of the simulation.** Bankroll = 5 × cash earned; at most a quarter
  of it staked per claim; in random order each trader moves the price toward the own
  forecast as far as the stake allows; one pass.
- **The platforms.** Polymarket runs an order book and Kalshi matches buyers with sellers.
  On both, users' orders set the price, a share is priced between 0 and 1 dollar, and the
  two sides of a trade together put up 1 dollar (their documentation, read 2026-11-16).
  With 4 to 8 traders an order book is too thin to quote. The market maker gives a price
  that moves with every trade, in the same vocabulary: YES and NO in cents that sum to 100.
- **Variant for a collective read-out.** Twelve successive records on one claim, a forecast
  after each (statistic PLAT2, below).

## Layout: sessions and people

A **twin pair** is a HIGH and a LOW session on one focal script; the focal markets are the
units. A **triplet** is a LOW session whose two markets each run the focal script of one
HIGH session; all four scarce markets are units and the triplet is the unit of analysis.

Six traders per market, calibrated supply, learning test at the anchoring edge (P4),
one-update rule:

| layout | sessions | people | units of the test | no session effect | session effect .1 |
|---|---|---|---|---|---|
| twin pairs: 12 HIGH + 12 LOW | 24 | 288 | 144 (half) | .926 | .774 |
| triplets: 12 HIGH + 6 LOW | 18 | 216 | 144 (two thirds) | .900 | .588 |
| triplets: 16 HIGH + 8 LOW | 24 | 288 | 192 (two thirds) | .980 | .770 |

- At the paper's values (P1) every cell is .987 or more.
- The fairness test at P4 is .99 or more, except .936 for 18 sessions with the session
  effect.
- **For a given number of people the triplet layout is at least as good.**
- The session effect is one shift per session with an intraclass correlation of .1, shared
  by the two markets of a LOW session. Its size in people is unknown.
- Power figures carry about ±.03 from the simulated pool: the first row came out as
  .951 and .811 with other rating and forecast draws on the same sessions. The lower
  figures are used.
- **More, smaller markets.** 72 traders per arm at P4 with a session effect of .1 per
  market: .861 as 18 markets of 4, .811 as 12 of 6, .633 as 9 of 8. The layouts above were
  run for 6 per market only.
- For comparison, the individual design B needs 144 people for 72 pairs.

## Analysis

The value of a market is the mean over its traders (last fairness rating; `T`).

| layout | fairness (H1a_M) | learning (D1_M) |
|---|---|---|
| twin pairs, S pairs | paired t on the S differences LOW − HIGH, S − 1 df | upper Fieller limit of mean T_HIGH / mean T_LOW below 1, from S + S market values, 2S − 2 df |
| triplets, n triplets | the same on n triplet values (mean of the two LOW markets minus mean of the two HIGH focal markets), n − 1 df | the same on n + n triplet means, 2n − 2 df |

- **Sizes** at nominal .005: .0035–.0085 for the tests above, with and without session
  effects (2,000 samples; Monte Carlo standard error .0016).
- **Not valid: tests on individual traders.** With session effects of .1 to .2 they reject
  a true null in 2.0–2.5% (learning) and 2.4–4.8% (fairness) of samples.
- **Not valid: the markets of a triplet taken as independent.** With a session effect of .1
  the tests reject a true null in .8–1.1%.
- **Why the two markets of a LOW session are not independent.** Each takes the other as
  its reference, so they carry nearly the same aspiration. Their mean fairness ratings
  correlate at +.16 to +.29.
- **Supporting, from the claim market.** The ratio of price responses HIGH to LOW tracks the
  forecast ratio (.200 against .190 at P1). Its test has less power than the forecasts: .94
  at P1, .45 at P4.
- **Supporting, if twelve-record claims are run.** PLAT2 separates the gate from a uniform
  slowdown of the HIGH arm: at P1 it rejects in .61 (one-update rule) and .96 (count rule)
  with 72 traders per arm, and in .001–.008 under the uniform slowdown. It does not
  separate the gate from disengagement that differs by arm.
- **Not recomputed at market level:** the entitlement test, FREEZE, the association by arm,
  the PHI flag.

## To build (next iteration; the implementation gate is closed)

1. **Script format 4.** One file per twin pair or triplet: the focal scripts, the rich
   neighbours' scripts, per market, round and clearing the units of each good, per seat and
   clearing the value, the tie-break order, the claims, the interventions, the supply
   factor, a hash. The arm is not in the script; a session is created from a script and a
   role.
2. **Engine without oTree.** Clearing (the certification's `auction` in plain Python),
   rounds, the reference over the last 15 clearings, cash, the market maker, replay. Tests:
   those of `analysis/tests/test_market_I044.py`, and the model's traders on the engine
   against section 1 of the record.
3. **oTree.** A session of 2N seats in two groups; a wait page before each round's
   clearing; a deadline with a default order; the claim market on `live_method`; a stand-in
   for an empty or abandoned seat, defined in the script and flagged in the export.
4. **Screens.** Order; Clearing (price, own fills, the other market's recent fills, cash);
   Rate; Claim (forecast, evidence, forecast); Trade (price chart, YES and NO in cents,
   position, cash); Results. The charts and the palette of I043 carry over.
5. **Export and analysis.** Trader-level and market-level tables; an adapter to the tests
   above.
6. **Replay tool.** Script and stored orders give the session again; script and model
   traders give the model's prediction for that script.

## Decisions for the author

1. **Two readings to confirm.** The cash earned in procurement is the bankroll of the claim
   market. The claims are on a simulated good.
2. **Market size and layout.** 4 or 6 traders; twin pairs or triplets; how many sessions.
3. **Who bids.** The engine bids the value (one decision per round, incentive-compatible),
   or the trader sets a bid. In the model, shading bids by up to half changes the control
   arm's legitimacy from .935 to .925 and the learning test at P4 from .894 to .850.
4. **Baskets.** A count of goods as in design B, or a round target with a completion
   payment. The second needs a certification.
5. **What a trader sees of the own market** beyond the price path, and whether values are
   shown.
6. **Twelve-record claims**, replacing or added to the single-record ones.
7. **The market maker's liquidity** and the conversion of cash to bankroll and to money.
8. **Empty seats and dropouts.** The stand-in's rule; whether a market with a stand-in stays
   in the analysis.
9. **The neighbour's supply.** Scripted and calibrated on a pilot, or following its demand.
10. **As before:** consent, the rating items, payment, devices, time-outs.

## References

Each was read at the level stated in the citation log; none supplies a number used here.

- Ausubel, L. M., Cramton, P., Pycia, M., Rostek, M. & Weretka, M. (2014) Demand reduction
  and inefficiency in multi-unit auctions. *Review of Economic Studies* 81(4):1366–1400.
- Demange, G., Gale, D. & Sotomayor, M. (1986) Multi-item auctions. *Journal of Political
  Economy* 94(4):863–872.
- Fréchette, G. R. (2012) Session-effects in the laboratory. *Experimental Economics*
  15(3):485–498. (Observations within a session may be correlated; the reason the session
  effect is carried through every table above.)
- Hanson, R. (2007) Logarithmic market scoring rules for modular combinatorial information
  aggregation. *Journal of Prediction Markets* 1(1):3–15.
- Kelso, A. S. & Crawford, V. P. (1982) Job matching, coalition formation, and gross
  substitutes. *Econometrica* 50(6):1483–1504.
- Vickrey, W. (1961) Counterspeculation, auctions, and competitive sealed tenders. *Journal
  of Finance* 16(1):8–37.
