# The basket economy with prediction markets (KGi-DISS-I043, 2026-11-16)

Nothing here has been run on people. Bot data are for checking the pipeline only. Every
sentence a participant reads is a draft.

- **Request.** Return the session to the storyboard's institutions (a basket task and a
  prediction market in an abstract economy), with the look of a market screen: coloured
  quotation curves, prices.
- **Freeze.** `freezes/00_freeze_I043.yaml` was pushed before the certification and before
  any code. Both scorecards are verbatim in it.
- **Specification and operator's guide.** `experiment/YOKED_DESIGN.md`,
  `experiment/MARKET_APP.md`.

## Design B

The statistical skeleton of the yoked ten-repetition design is unchanged: pairs on one
schedule, one HIGH and one LOW; one rich round and five deprivation rounds; three fairness
items and one entitlement item per round; four probes in two pairs; the same reporting set.

| repetition | design Y (I041, I042) | design B (I043) |
|---|---|---|
| 1–6 | choose a ticket; 120 settlements; the ticket pays or not | order a good; the goods market clears 120 times; the order fills when the clearing price is at or below the cap |
| board | a trader's paid settlements | a trader's filled orders |
| 7–10 | a new ticket; forecast, a record of ten settlements, forecast again | a prediction market ("Will ASSET close above X?"); forecast, evidence, forecast again; then a bet |
| evidence | two pairs of records (own, other) | one pair of records (ten trial closes, own tickets), one pair of a source's forecast |
| points | 1 per paid settlement | 1 per filled order (a good; six goods are a basket, a count with no quota) |

**The price is a display of the schedule's draw.** `price = cap · exp(σ (z(u) − z(p)))`: the
order fills exactly where the schedule says, and no second draw exists. Only the ordered
good's own price path is shown.

**Left out of this session, on purpose:** prices that inform beyond the ordered good's own
path, the other good's prices, the two-stage route task, live order matching, mixed-good
baskets, a stated basket quota.

## What changed statistically, and what the certification says

Two things changed. One of the two probe pairs now measures the weight on a source's
forecast, assumed to be `κ_s · g` (gate `g`, `κ_s` unknown). A bet was added, under an
assumed betting rule. Record: `records/basket_cert_I043.txt` (seed 139000; a second run is
bit-identical).

| at 72 pairs, one-sided .005 | κ_s = .5 | κ_s = .35 | κ_s = .2 |
|---|---|---|---|
| D1 and confirmatory pair, P0–P3 | 1.000 | 1.000 | 1.000 |
| D1 at the anchoring edge (P4), one-update rule | .947 | .893 | .790 |
| D1 at P4, count rule | .990 | .990 | .966 |
| bet test, P0–P3 | 1.000 | 1.000 | 1.000 |
| bet test at P4, one-update rule | .994 | .973 | .916 |
| FREEZE, P1–P3, one-update rule | .90–.93 | .77–.84 | .59–.60 |
| HIGH-arm association, P1 / P2 / P3 | .28 / .41 / .31 | .23 / .32 / .24 | .16 / .18 / .19 |

- 96 pairs give D1 .973 at κ_s = .35 and .913 at κ_s = .2 at the anchoring edge.
- Sizes hold: D1 .004–.007, bet test .002–.006.
- **Five of my eight frozen predictions failed.** B3 by .004, B6 by .009, and the FREEZE
  half of B8 by .01–.09 (.77–.84 against a predicted .85 or more; the association half
  passed). One in the favourable direction: the bet test is sharper than I said
  (.973 against .55–.85), because under the assumed rule a bet carries one noise term and a
  revision two. One was wrong outright: I said 96 pairs would not suffice at κ_s = .2; they
  give .913. My estimate in conversation of "about threefold" the sample was also wrong.
- **The cost of the source pair sits in the supporting statistics.** FREEZE and the
  HIGH-arm association lose power as κ_s falls. The confirmatory pair loses power only at
  the anchoring edge.

`κ_s` and the betting rule are human quantities. That people discount another person's
advice relative to their own opinion is documented (Yaniv & Kleinberger 2000, read at
abstract level; no number was taken from it). The pilot estimates `κ_s` from the LOW arm's
source pair.

## What was built

| piece | where |
|---|---|
| schedule format 3: the settlement draw, four markets per file, evidence kind per pair, bet price | `experiment/tools/yoked_schedules.py --format 3` (`--no-social`, `--markets-from`) |
| engine: price path, price axis, baskets, markets, bet points, bet statistic, sources | `experiment/diss_market/engine.py` |
| app pages: Order, Clearing, Rate; Market, Evidence, Bet, Recall; Results settles the markets | `experiment/diss_market/` |
| charts: clearing price against the cap with a fill strip; filled orders, you against the trader; a market's price history; ten trial closes | `experiment/frontend/src/chart.ts`, `svgchart.ts` |
| pool of real earlier records: board fills and forecast sources | `experiment/tools/make_board_pool.py` |
| export → reporting set, bet test, `T` by kind of evidence | `experiment/analysis/yoked_from_export.py` |

**How the clearing screen works.** The price of the ordered good comes in clearing by
clearing over 9 seconds, drawn against the cap. A filled order is a dot on the line and a
coloured tick in a strip under the chart; the strip shows the share of filled orders at a
glance. Next to it, the counts of filled orders for the participant and the trader, as
figures and as two curves on a fixed axis from 0 to 120. The points total moves only when
the round has cleared. After the reveal, pointing at the chart reads out one clearing.

**How a market screen works.** A price history that ends exactly on the line the asset has
to close above, with the stretch from now to the close left empty. Record evidence: ten
trial closes appear one by one above or below the line. Source evidence: another trader's
forecast with a short description. Then the bet: YES and NO at the posted price, or pass.

**Colour.** Goods carry colour (Square blue, Triangle orange). People are drawn in neutral
tones (the board trader in slate, a source in ink). YES and NO appear on the bet buttons
and settled markets only, with the word. Nothing on a procurement screen is green or red.
No name, logo or layout of a real market is used.

## What was verified

| gate | result |
|---|---|
| H1 engine | PASS. 120 schedules, six rounds, both goods: every price is at or below the cap exactly when the order fills. Fills, boards and `T` equal I042's engine. The gate kernel on the engine: legitimacy at probe time .112 / .865 (certification .109 / .869); with one source pair, ratio of mean `T` .129 (.124), bet statistic .090 / .678 (.098 / .689) |
| H2 nothing shown early | PASS on the frozen checks (125 page sources per run). A copy of the app with planted leaks fails the run. One leak the checks could not see was found by eye (below) |
| H3 bots and browser | PASS. Stored data equal schedule and engine for every bot. Five browser participants (two desktop members of one pair, phone, small phone, reduced motion): no console error, no failed request, no request to another host; a pair making the same choices gets identical pages apart from the board's numbers; reload, back button and a second submission change nothing stored; both charts in view during the reveal on a 375 × 667 screen |
| reveal timing | 9,003 ms for 9,000 planned; a tab hidden for 3 s stops the reveal (0 clearings shown meanwhile) |
| H4 export | PASS. `T` and the bet statistic from the export equal the stored values, 144 of 144. At 72 pairs of gate bots: H1a, D1, the confirmatory pair and the bet test come out |
| seed wave → pool → pilot | PASS with bots. 32 seed forecasters on a record-only schedule give 192 fill records and 128 candidate forecasts; a pilot on the same markets shows one real forecast per pair and market, the same to both members (5, 85 and 90 in the test). A pilot on other markets, a seed wave on a schedule with sources, and a placeholder pool for people in production do not start |
| H5 Docker | PARTIAL, as in I042: builds and serves on stand-in base images; the browser run passes against the container with Postgres; the export without its key is refused |
| H6 regression | PASS with a stated replacement. Full suite 99 passed (I042: 96); the three I042 test files are rewritten for format 3 and keep their checks. Front end: 22 unit tests |
| H7 constraints | no credential in the repository; nothing run on people; main text untouched |

## Found while building

1. **A source's track record gave the market's outcome away.** The source card said "on the
   right side in 4 of 4 markets" next to a forecast of 90%. Four of four includes the
   market on screen, so the line told the reader that it closes above. Seen on a still, not
   by any test. The record now counts the forecaster's other three markets only.
2. **The palette validated in the freeze did not hold.** I had checked neighbouring colours
   in a list. With every pair checked, the violet chosen for the trader is separated from
   Square's blue by ΔE 3.8 for people who do not tell red from green, and 11.4 with full
   colour vision (the floors are 8 and 15). The trader is now a neutral slate. YES green
   against NO pink failed the same check (5.1; 2.1 for the selected buttons). The pair is
   now green against magenta (10.3; 9.3 for the button inks).
3. **In the rich round the fill marks piled up** (about 90 dots on one line). The strip
   under the chart was added for that.
4. **On a small phone the price axis labels collided.** Labels are now thinned by distance.
5. **Dimming the option not chosen made it hard to read** while it could still be chosen.
   Removed.
6. **A price axis fitted to the file can exceed the possible range** once padded. It is now
   cut to the bounds no price can leave.
7. **The I042 test files test an app that no longer exists** (format 2 is refused). They
   are renamed and rewritten for I043; the checks they held are kept.

## Decisions for the author

1. **Two waves.** A pilot with truthful sources needs a seed wave on a record-only schedule
   first; the pilot's schedule reuses its markets. Otherwise the source must be described as
   what it is.
2. **How a source is described,** and whether its track record is shown at all. The record
   raises the weight on the forecast and so the power of the source pair; it is one more
   thing a participant has to read.
3. **The bet.** Posted price 50, allowance 10, payout 20, pass allowed. The bet test rests
   on a rule nobody has observed.
4. **Market wording** ("Will Circle close above 12.00?"), the price history, ten trial
   closes "held with your own YES tickets" that add points.
5. **Whether the clearing price curve stays.** It is the market look that was asked for. It
   also shows by how much an order missed, which design Y did not.
6. **As before:** consent, the rating items, the board's description, reveal speed, devices,
   payment rates, recall, time-outs.

## Not done

- No check that people read a price curve as a record of fills.
- No page time-outs; no refill of slots left by dropouts.
- English only; no screen-reader test; the charts have no text alternative beyond the
  figures printed next to them.
- The official Docker base images were not pulled.
- The pilot specification.
