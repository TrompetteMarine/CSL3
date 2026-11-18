# The goods market as one phone screen, and both goods' prices on it (KGi-DISS-I047, 2026-11-18)

Nothing here has been run on people. Every sentence a participant reads is still a draft; two
short strings were added ("Order", "Filled orders") and none was changed.

- **Request** (2026-11-17 21:12, in answer to the five points of
  `records/115_interface_polish_I046.md`): "1 - yes, 2 - keep both at the same units, abstract
  values are better,3- no, but color should be neutral, 4- let us focus on phones, 5 - yes, but
  I think the market should run live and the participant should select in a plolymarket way -
  [address of a prediction-market page] ; this should be the interface with the shapes, and
  curves."
- **Freeze.** `freezes/00_freeze_I047.yaml` was pushed (b389e71) before any change to the
  app, its tools or the analysis code: five readings, nine invariants with their amendments,
  one claim with a decision rule, fourteen design decisions, eighteen gates, ten expectations.
  Addendum AD1 (141cc67) was pushed after the first certification run and before the replicate
  run it adds. The scorecard is in the file.
- **Operator's guide.** `experiment/MARKET_APP.md`. **Design.** `experiment/YOKED_DESIGN.md`,
  section "Both goods' prices on screen (I047)".
- **Records.** `records/live_cert_I047.txt` (first run, kept as it came out),
  `records/live_cert_ad_I047.txt` (eight pools per cell).
- **Pictures**, all from the final build: `records/ui_I047_market_screen.png` (the screen from
  open to cleared), `records/ui_I047_two_displays.png` (both displays of the price key),
  `records/ui_I047_other_pages.png`, `records/ui_I047_small_phones.png` (360 × 640 and
  375 × 553), `records/ui_I047_before_after.png`.

**In short.**

1. Rounds 1 to 6 are one market screen in the pattern of a prediction-market page with several
   outcomes: a chart with a line per good, a row per good with its price and a button, a ticket
   to confirm. It runs in real time from the pre-drawn schedule. **Participants' orders do not
   set prices.** That would be design W of I044, which is not built; the instructions and one
   quiz item say that prices follow a rule fixed in advance. If "live" meant design W, this
   screen is its front end and the engine is the missing part.
2. The phone is the reference device. One column at every width. Both states of the market
   screen, a market's first forecast, the bet and the recall question are exactly as high as
   the window from 320 × 568 up.
3. Drawing both goods' prices tells every participant which good is cheaper, and the choice of
   good sets the model's levels. I certified the design for shares of 0, .5 and 1 of
   participants who then always order the better good. The confirmatory pair gains at the
   anchoring edge (.790 → .878 in the weakest cell) and loses at most .012 elsewhere. The rule
   frozen before the run makes `'both'` the default. It has costs, listed below: one
   supporting test stops being valid, two others stop speaking about the HIGH board alone, and
   one assumption cannot be tested without people.
4. The first certification run failed gate G18(b): its column for the certified design
   disagreed with the I043 record by up to .098 where I had allowed .03. The cause is the
   precision I had given the I041 and I043 records (±.03). The records' values stand; the
   stated precision was wrong and is corrected.
5. Server, measures and stored data are unchanged: the exports of three bot sessions are
   identical byte for byte.
6. It took two full checks. The first passed every gate. Looking at its pictures afterwards
   found two defects no gate measured: on small phones a dark tag hid part of two axis figures
   on the evidence and bet pages (mine, from this iteration); and in production mode every
   page was one line higher than the window, so a screen that fits could still be pushed up
   by a finger (the framework's own blank line, there since I042, hidden on a development
   server by its debug panel). Both are corrected and measured on every run now, and the
   browser test plays one of its runs on a production server.
7. Of thirteen expectations six held, six held in part and one failed.
8. Eight points wait for the author.

## How each answer was read

| answer | taken to mean | done |
|---|---|---|
| 1 "yes" | the lower chart of the clearing page gets a caption | "Filled orders" (new string, draft) |
| 2 "keep both at the same units, abstract values are better" | one unit on a bet, and an abstract one: points | the figure in cents is gone; a ticket shows "costs 10 points". Allowance 10, payout 20 and posted price 50 are untouched. A price on the forecasts' scale of 0 to 100 would need a payout of 100 points, which is a payment decision |
| 3 "no, but color should be neutral" | no text alternative for the charts. No colour stands for an outcome or a side | YES and NO are in ink and told apart by the word; green and magenta are gone. Colour says which good a mark belongs to and nothing else, and every such mark carries the good's shape |
| 4 "let us focus on phones" | the phone is the reference device; one layout at every width | a single column of at most 480 px; reference sizes 390 × 844 and 360 × 640. Who is admitted stays a recruitment setting (`min_window_width` is still 0) |
| 5 "yes, but I think the market should run live and the participant should select in a polymarket way … the interface with the shapes, and curves" | the two legends of the instructions stay. Rounds 1 to 6 become one market screen in that pattern, running in real time from the schedule | built. From the page at the address given only the interaction pattern is taken: no name, logo, colour scheme, typeface, icon or copied layout. I read that page once, as text; I did not see a picture of it |

Two of these readings could be wrong and change what was built: "neutral" (point 4 of the
last section) and "live" (point 1).

## What changed

**The goods market (rounds 1 to 6): one screen in two states**, on the two existing pages of
the server.

- *Open for orders.* The frame of the chart: the cap, the zone under it and what the zone
  means, no price. A row per good with its shape, its name and a button "Order". Once a good
  is chosen, its row and the zone take its colour and a ticket at the foot names it beside
  the cap; the existing button "Send the order" sends it.
- *Running.* The same chart, drawn clearing by clearing over the round's 9 seconds. The head
  of a price line is the good's own shape. The ordered good's line is 1.5 px, lies on top and
  carries a dot at every filled order; the other good's line is 1 px and lies behind. The
  strip under the plot has a tick per clearing, coloured where the order filled. Under the
  chart the two rows again, each with its good's clearing price, the ordered one marked.
  Then "Filled orders": the two counters and their running counts as two curves.
- *Cleared.* A finger or a pointer on either chart shows the clearing under it: its number,
  each good's price, whether the order filled, the two counts. The reading takes the place
  of the heading while it is shown.
- *Where it differs from a real market page, on purpose.* A row carries no price before the
  order: none is known before the round runs, and the order page may show none. An order
  cannot be placed or changed while the round runs. There is no order book, no volume and no
  trace of other traders, because there are none.

**Which prices are drawn** is the session key `price_curves`: `'both'` (both goods' clearing
prices of the round; the default in `settings.py`) or `'own'` (the ordered good's only, the
display of I043; what a configuration without the key gets). The other good's prices are
`engine.price_path` for that good: what the participant would have seen had they ordered it.
One draw settles both goods, so the two lines move in step and the better good is the cheaper
one at every clearing. The browser records how many lines it drew.

**Every page.**
- One column of at most 480 px at every window width; a laptop shows the same column on the
  tinted ground. The desktop layouts of I046 are gone.
- The column is as high as the visible window; on the goods market the charts take the room
  the rest leaves, and a page's button stands at the foot.
- Every control is at least 44 × 44 px from 360 px on; a page's button is 50 px high (48 px
  in a window lower than 620 px). Hover
  styles exist only where a pointer can hover. A pull at the top of the page does not reload
  it (not measured on a phone).
- The study's name stands in the top bar on the pages before the task and nowhere else:
  the ten steps need the room.

**Sliders under a finger.** A tap sets the value when the finger lifts, and only if it lifts
within 10 px of where it came down. A sideways drag sets it while it moves. A gesture the
browser takes for scrolling, or a finger that wanders up or down, stores nothing and leaves
the slider as it was. Mouse and keyboard as before.

**Bet page and settled markets.** Neutral cards; one figure per ticket, its cost in points.

**What a participant reads.** The page's text outside the charts, as bags of words, for the
same schedule and choices before (569c3f8) and after.

- *On a phone before and now* (the same words on 24 of 43 pages; 2,620 words before, 2,642
  after):
  - order page: the two cards each said "your cap 4.00"; the ticket now says it once. Each
    row has the word "Order". The ticket names the chosen good. The word "ordered" on the
    chosen card is gone from this page.
  - cleared screen: the caption "Filled orders"; the other good's name in its row with its
    last clearing price (a dash under `'own'`); the word "ordered" on the ordered good's row.
  - bet page: "50¢" on the two tickets is gone.
  - consent, instructions, quiz: the study's name "Basket market" is shown; the old phone
    layout hid it.
- *On a laptop before* (the same words on 3 of 43 pages; 2,706 → 2,642): as above, and the
  study's name is no longer shown on the 40 task pages, where the old desktop layout showed
  it.
- *Inside the charts* (not in those counts): the order page now has a chart frame with the
  cap's tag, axis figures and the existing sentence "your order fills at or below your cap",
  which stood on the clearing chart only. Under `'both'` the running chart has the other
  good's line, and the reading on the cleared chart names both goods ("Square 4.70, not
  filled  Triangle 4.37").

## What did not change

- `diss_market/engine.py` and `diss_market/bots_model.py` are byte-identical.
- `diss_market/__init__.py`: its diff has 25 added lines and 3 removed ones. They hand display values to
  templates and scripts (the goods of the rows, the other good's price path and the names,
  the frame of the order page's chart, the bet's cost line). One addition is not a display
  value: a session refuses to start when `price_curves` is neither `'both'` nor `'own'`.
- No model field, form field, page, payoff or export column was added, removed or reordered.
  The export has its 82 columns; the exports of `market_bots_random`, `market_bots_model` and
  `market_bots_seed` are identical to those of the baseline.
- `settle_meta`, a text field the browser fills, gained keys: `curves`, `vw`, `vh`, `fit`,
  `scrolled`.
- Durations and pacing: the 9-second reveal, the two shorter reveals, the 500 ms pause.
- Every existing string of `copy_en.py`, character for character.
- `analysis/twins_I040.py` gained one optional argument; left at its default it returns the
  same arrays as before, byte for byte (four fingerprints in `test_live_I047.py`).
- Type, the goods' two colours, the neutrals and the motion rules of I046.

## Both goods' prices on screen: what it does to the design

**Why it had to be tested.** The ledger holds DISS-CHOICE-EFFECT (I040): the choice of good
sets the model's levels. On the worse good the aspiration falls further and legitimacy repairs
sooner. A participant who sees both price paths knows after round 1 which good is cheaper.
Design B was certified in I043 with model-like choices.

**Claim C1.** With a share q of participants who order the better good in every deprivation
round (round 1 chosen as before), q in {0, .5, 1}, the decision rates of the reporting set at
72 pairs, for the five gate points, both revision rules and κ_s in {.5, .35, .2}; kernel,
ratings, forecasts, bets and tests as in `basket_cert_I043.py`. q = 0 is the certified design.

**Two assumptions, both human quantities.** A_Q: informed participants order the better good
from round 2 on, the others choose as the model does, each member of a pair informed
independently. A_CF: the display reaches the kernel only through the good ordered; seeing the
other good's price has no effect of its own on legitimacy or aspiration. The model has no term
for regret. No simulation can test A_CF.

**The first run failed a gate, and why.** Before trusting the new script I ran the unchanged
I043 script: it reproduces its record byte for byte. The first run of the new script (one
pool of 20,000 pairs per cell, seed 141000) then disagreed with that record in its q = 0
rows by up to .038 (confirmatory pair, P4, κ_s .2), .049 (FREEZE), .091 (association within
HIGH) and .098 (D1 from the source pair alone). G18(b) allowed .03. Inside that run the same
cell read .828 in one section and .784 in another, which differ only in the forecasts drawn
for the pool. So the pool's own draw moves a rate by more than the ±.03 the I041 and I043
records claim. I wrote addendum AD1 and pushed it before running the replicate: eight
independent pools per cell, and G18(b′), that every compared value of the I043 record lies
inside the range of the eight q = 0 pools widened by .02.

- Across the eight pools the standard deviation of a rate is up to .017 for the confirmatory
  pair (P4, κ_s .2) and for BET, and .034 to .042 for FREEZE, the two associations, the top
  quarter and D1 from the source pair alone. Where the confirmatory pair is .99 or more it
  is below .001.
- G18(b′) passes: 240 values compared, none outside; the farthest lies .017 beyond the pools'
  own range.
- The I043 record is a correct single draw. Single figures of it can be off by twice those
  deviations. `YOKED_DESIGN.md` now says so.

**Results** (means over the eight pools; 72 pairs; one-sided .005).

Legitimacy at probe time, HIGH / LOW:

| | q = 0 | q = .5 | q = 1 |
|---|---|---|---|
| P1 paper's values | .112 / .868 | .107 / .799 | .099 / .728 |
| P4 anchoring edge | .411 / .874 | .324 / .808 | .239 / .741 |

Decision rates for κ_s = .5 \| .35 \| .2; each cell is q = 0 / .5 / 1:

| | κ_s = .5 | κ_s = .35 | κ_s = .2 |
|---|---|---|---|
| confirmatory pair, P4, one-update rule | .949 / .964 / .985 | .897 / .931 / .955 | .790 / .835 / .878 |
| confirmatory pair, P4, count rule | .989 / .994 / .998 | .977 / .988 / .996 | .957 / .978 / .990 |
| confirmatory pair, lowest of P0–P3, one-update rule | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / .998 | .999 / .995 / .987 |
| BET, P4, one-update rule | .990 / .992 / .996 | .974 / .981 / .988 | .903 / .922 / .944 |
| FREEZE, P1–P3, one-update rule | .90–.94 / .84–.91 / .77–.87 | .77–.83 / .70–.78 / .60–.72 | .58–.64 / .51–.58 / .41–.53 |
| association within HIGH, P4, one-update rule | .997 / .976 / .824 | .986 / .937 / .718 | .940 / .833 / .566 |
| D1 from the source pair alone, P1–P3, one-update rule | 1.00 / 1.00 / .99 | .95–.97 / .91–.94 / .84–.91 | .46–.54 / .41–.47 / .33–.41 |

H1a is 1.000 in every cell and K3 .997 or more. Pairs for .90 on the confirmatory pair at P4
under the one-update rule: 72 / 84 / 96 at q = 0 (κ_s .5 / .35 / .2), 60 / 72 / 96 at q = .5,
60 / 60 / 84 at q = 1.

**The rule frozen before the run** (default `'both'` if, at q = .5 and q = 1, the confirmatory
pair falls by no more than .03 in any of thirty cells and the sizes of H1a, D1 and BET in the
two null worlds stay at or below .010) gives `'both'`: largest fall .012 (P1, κ_s .2, q = 1),
largest rise .088 (P4, κ_s .2, q = 1), largest mean size .0061. Read on the first run alone
it gave the same (.011, .064, .0085). In AD1 I restated the rule on the means over the pools;
single pools have sizes up to .0105.

**What it costs.**

1. *FREEZE is no longer valid as defined.* When both members of a pair see the LOW board it
   rejects in .0002–.0003 of samples at q = 0, .007–.010 at q = .5 and .027–.045 at q = 1
   (nominal .005). Once the LOW board alone leaves people at different levels, the
   lowest-rated third of one arm revises less than the other arm's average. Its power also
   falls (first table). A version that compares like with like would need its own
   certification; none was written.
2. *The association and the top-quarter test stop speaking about the HIGH board alone.* The
   association within LOW rises from .21–.59 to .67–.95 at P1–P3 (κ_s .5). In the both-LOW
   world the association within an arm fires in .22–.43 of samples at q = 0 and .72–.95 at
   q = 1, the top quarter in .03–.06 and .16–.30. That is state dependence in both arms: true
   of the kernel, and no evidence about the reference.
3. *The control arm is no longer near the ceiling.* LOW legitimacy is .73 at q = 1 against
   .87. Its absolute revision is smaller, which is what takes power from the source pair
   alone (.46–.54 → .33–.41 at κ_s .2).
4. *A_CF.* If seeing the cheaper path one did not order erodes fairness by itself, both arms
   move and the contrast changes in a way no figure here covers.
5. *The seed wave.* The pool's LOW board is the record of the same round nearest to the
   participant's own count. A seed wave run under `'both'` will hold few records of the worse
   good. A pilot participant on the worse good would then be shown a trader who did better.
   The pool tool prints the range of counts per round and the app stores the distance
   (`board_dist`). Not measured; `market_seed` inherits `'both'` as built.

q is not a free parameter of the study: the share of participants who order the better good
in every deprivation round is read directly from the pilot's orders.

## The gates

Final build; three browser runs, in this order: `'both'` and `'own'` on a development server,
`'both'` on a production server. "per run" figures are the same in all three unless given as
three values.

| gate | result | what was measured |
|---|---|---|
| G1 data | pass | three bot exports (88 rows, 82 columns each) identical to the baseline: sha256 beginning ebc1e22e0d1da7ec, 5e0082b07b945e88, 0dbd4d4190087a36 |
| G2 suites | pass | 70 tests without a browser (8 engine, 6 app, 19 interface, 7 for the certification code, 30 earlier ones); the browser test, 3 runs in 49 min 48 s; type check and 22 unit tests of the front end; a second build byte-identical |
| G3 information | pass | `'own'`: one price series on each of 30 clearing pages; `'both'`: two, each equal to the engine's path; no price on an order page; chart marks right on 72 clearing pages per run; the word differences are listed above |
| G4 wording | pass | two strings added, none changed or removed |
| G5 arms | pass | no page difference inside the pair beyond the board |
| G6 leaks | pass | none on 125 pages per run |
| G7 isolation | pass | no request to another host, no console error, no failed request in 13 sessions per run |
| G8 measures | pass | 192 of 192 stored ratings and forecasts equal the values set (128 by mouse, 32 by finger, 32 by keyboard); three gestures that start on a slider and are not meant for it store nothing; the button stays off until the fourth slider is touched |
| G9 timing | pass | reveal 9,008 \| 9,001 \| 9,015 ms for 9,000; a tab hidden for 3 s stops it (3,007 \| 3,007 \| 3,006 ms, nothing shown meanwhile); with the processor slowed four-fold 9,008 \| 9,017 \| 9,011 ms |
| G10 fit | pass | 519 pages in 13 sessions per run at ten window sizes: nothing past the right edge from 320 px; every part the gate names in view at its sizes |
| G11 access | pass, one clause not as frozen | no audit finding of any impact on 86 pages per run; keyboard-only session complete; controls at least 44 × 44 px from 360 px (at 320 px the seven answer buttons of the closing questions are 39 px wide); nothing moving under reduced motion. Not as frozen: "a good's colour on white or its own tint only". Under `'both'` the other good's line crosses the ordered good's zone: Triangle's orange on Square's tint has 3.001:1, at the floor; Square's blue on Triangle's tint 4.17:1 |
| G12 colour | pass | no chromatic colour but the goods' and an error banner's on 519 pages per run |
| G13 weight | pass | 168,523 bytes (169,076 before) |
| G14 smooth | pass | emulated phone, pixel ratio 3: median frame 16.7 ms; longest 21.8 \| 19.1 \| 20.6 ms; slowed four-fold: median 16.7 ms, longest 48.9 \| 48.7 \| 47.9 ms |
| G15 touch | pass | a whole session by taps and drags at 360 × 640 stores a complete record; a finger on the cleared chart reads the clearing under it with its price and whether the order filled |
| G16 modes | pass | both displays |
| G17 layout | pass | no text cut off, over other text, under a tag's box or outside its sheet on 440 pages at ten sizes, for `'both'`, `'own'` and a session without a board. The first check passed this gate while a defect of that kind existed (next section) |
| G18 certification | (a) pass, (b) failed as frozen, (b′) pass, (c) `'both'` | section above |

Beyond the gates, on the final build:

- *Exactly window-high in production* at all ten sizes, 320 × 568, 375 × 553 and 390 × 664
  included: both states of the market screen, a market's first forecast, the bet, the recall
  question.
- *Rating page.* Four sliders and the button in view at 375 × 667, 390 × 664 and larger. The
  button lies 22 px below the window at 360 × 640, 56 px at 375 × 553, 65 px at 320 × 568.
- *Evidence page.* Evidence, second forecast and button in view at the same sizes. Too high
  by up to 45 px (record) and 36 px (source) at 360 × 640, 63 and 66 px at 375 × 553, 91 and
  74 px at 320 × 568; the question is brought into view when it opens.
- *Sizes nobody asked for.* A phone held sideways (844 × 390, 667 × 375): the same column,
  every page scrolls, no text cut off or over other text. A 390 px phone at 150% page zoom
  (260 px): one label of the development board leaves the window. At 200% (195 px): 35
  findings; the layout breaks.

## Two defects the first full check did not see

The first full check passed every gate on its build. I then looked at the pictures composed
for this memo.

1. **A tag over two figures.** On the evidence and bet pages the market's small chart has
   two axis figures and a dark tag for the line. To make the evidence page fit small phones I
   had set that chart to 76 px at window heights up to 700 px. At that height the tag's box
   hid the foot of the upper figure and the head of the lower one: at 360 × 640, 375 × 667,
   375 × 553, 390 × 664 and 320 × 568, in all four markets. The layout check had passed: it
   compares pieces of text, and a box is not text. Corrected: 84 px, the least height at
   which both figures clear the box by 2 px. The evidence page is 8 px higher at those sizes
   and still fits 375 × 667 and 390 × 664. The layout check now measures the ink of every
   chart figure against every tag (on the old build it finds both figures in all four
   markets), and an
   interface test derives the least height from the chart's own geometry.
2. **Every page one line too high.** The framework ends each page with an empty line after
   the form. A page that filled the window was therefore 24 px higher than it in production:
   a swipe moved the whole screen, the running chart included. It has been so since I042. On
   a development server the debug panel under the page hides it, and my fit gate measured
   whether the parts were in view, which they were. I found it because full-page screenshots
   were longer than the window. Corrected in the stylesheet. Every run now measures that
   nothing after the form takes room, and the third run of the browser test plays a
   production server, where a fitting page must be exactly as high as the window.

Corrections during the build, before the first full check:

- A finger that moved on a slider without the browser scrolling ended as a tap and set the
  slider. A tap now counts only if the finger lifts within 10 px; a third stray gesture is
  played on every run.
- The order page did not fit 360 × 640 and 375 × 667 once the last round's recap was shown
  (the button 36–42 px below). The charts' heights were computed from constants; they now
  take the room the page leaves.
- In the counters the large figure's box overlapped its neighbours (17 findings per size).
- The ticket's shape was drawn in ink, not in the good's colour.
- The reading on the cleared chart named the other good and not the ordered one.
- `tools/mark_contrast.py` read screenshots taken at three device pixels per pixel with a
  reach meant for one, and reported Triangle at 2.75:1 on the colour of a hairline its line
  crosses. Corrected in the tool. Its other finding is real and stays: 3.00:1 on Square's
  tint.

Slips of mine in the records, each corrected where it stands:

- The freeze and the addendum carried times I had written without reading the clock; both
  now carry the commit times, and AD1 says so.
- The freeze speaks of "the two null worlds of the I043 record". One of them, both members
  on the LOW board, is in the I041 record. Both were evaluated.
- One run was cut off when the container restarted; nothing was lost and it was repeated.
- One layout run printed "console errors 2" without their text. The tool prints the text
  now, and I saw it once more: the framework's own auto-advance socket, reset while the
  development server restarted because I had just edited a Python file of the project. The
  first occurrence fits that and was not reproduced.

## Expectations

| | expected | result |
|---|---|---|
| E1 | G1, G4, G5, G7 pass at the first attempt | held |
| E2 | q = 1: H1a 1.00; the confirmatory pair at P4 rises to at least .97 / .94 / .85; 1.000 at P0–P3 | in part: .985 / .955 / .878 at P4, legitimacy .24 against .74 as predicted; at P0–P3 as low as .987 |
| E3 | q = 1: association within HIGH at P4 below .90; within .05 of the record at P1–P3 | in part: below .90 under the one-update rule only (.824 / .718 / .566; count rule .94–.98); changes of up to .071 at P1–P3 |
| E4 | q = .5: every rate between its values at q = 0 and q = 1, within .03 | in part: true of every test but one. The top quarter at P4 is highest at q = .5 in all six cells and outside the range by more than .03 in four (up to .09) |
| E5 | the rule selects `'both'` | held |
| E6 | the rating page does not fit 375 × 667; the evidence page fits 390 × 844 only with a smaller chart | in part: both fit 390 × 844, the evidence page with 148 px to spare; the rating page fits 375 × 667, after I tightened it |
| E7 | bundle between 170 and 200 KB | failed: 168,523 bytes; the stylesheet lost its desktop layouts |
| E8 | G14 passes in both displays; the longest frame is higher under `'both'` | in part: passes; the longest frame is not ordered by display (21.8 against 19.1 ms at pixel ratio 3, 18.8 against 23.7 at 1) |
| E9 | two lines in step look like a doubled line on a phone; the other line thinner and behind | held |
| E10 | the test browser can show a scroll that starts on a slider | held: the page scrolls, the pointer is cancelled, the slider stays untouched |
| E11 | standard deviation across pools .015–.04 for the confirmatory pair at P4; below .005 at .99 or more | in part: .005 / .006 / .017 at P4; below .001 at .99 or more |
| E12 | the rule read on the means gives `'both'` | held |
| E13 | FREEZE in the both-LOW world at q = 1 above .02 | held: .027–.045 |

## What was looked at, and what was not measured

- Looked at on the final build, one participant on the HIGH board with both prices drawn:
  every kind of page at 360 × 640, 375 × 667 and 320 × 568, the main pages at 375 × 553,
  430 × 932 and 1280 × 860. With the ordered good's prices only: the market screen at
  360 × 640. Without a board: the market screen and rating page at 390 × 844, five pages at
  360 × 640. The LOW board: three cleared screens at 390 × 844 from the first check; the
  two corrections do not touch that page.
- Not looked at: reduced motion (a still shows nothing of it; the runner measures it) and a
  page at 200% text size.
- Not measured, because it cannot be here: a real phone, Safari, Firefox, a screen reader,
  a person. On a phone in particular: what the browser's own bars do to the height, whether
  a pull at the top is really ignored, the phone's text-size setting, a finger's real
  scatter on a slider.

## Risks

- **The screen now looks like a live market and is not one.** The instructions say prices
  follow a rule fixed in advance, and the quiz item "How are clearing prices set?" has "By
  other traders, live, as I play" as its wrong answer. Whether people still take the lines
  for other traders' doing is not known.
- **The display is part of the stimulus and changed again.** Both arms get the same pages.
  How people read two lines in step, and whether they order the cheaper good afterwards, is
  what the pilot shows.
- **Small phones.** At 360 × 640 the price chart is 140 px high (115 px at 375 × 553, 255 px
  at 390 × 844) and the two lines cannot be told apart along their length; the rows carry
  the last prices and the strip the fills.
- **The costs of `'both'`** listed in the certification section.

## For the author

1. **"Live".** Built: real time from the pre-drawn schedule, which the instructions and the
   quiz describe truthfully. If you meant that participants' orders set the prices, that is
   design W: synchronous groups, an engine that is not written, an implementation gate that
   is closed, and instructions that would have to change.
2. **The default `'both'`.** The frozen rule chose it. Confirm it, or set `'own'` (one key).
   A third option is to run the display as a factor between sessions of the pilot: it gives
   q under each display and a first look at A_CF. That is my suggestion, not part of any
   plan.
3. **If `'both'` stays:** FREEZE leaves the reporting set or is redefined and certified; the
   seed wave's display is decided (`'own'` there keeps both goods in the pool); and the
   instructions get a sentence saying that both goods' prices are drawn. I wrote none.
4. **"Neutral".** I took it to mean that no colour stands for a side or an outcome. If you
   meant goods without hue, or goods of equal weight (Square has 4.42:1 on white, Triangle
   3.20:1), say so.
5. **The bet's unit.** One figure, in points. A price on the forecasts' scale needs a payout
   of 100 points.
6. **Devices.** At 360 × 640 the rating page needs 22 px of scrolling and the evidence page
   up to 45; at 375 × 553, 56 and 63 to 66. Which phones are admitted, and whether a phone held sideways
   is, are recruitment settings. There is no layout below 320 px or for 150% page zoom.
7. **Two sentences written for a mouse**, left as they are: "Click or drag on the line to
   set your forecast." and the notice for `min_window_width`, which asks for a laptop.
8. **Still open from `records/114_staged_power_I045.md`:** which later steps are
   confirmatory, and the pilot's specification with its frozen analysis.

## Not done

- Prices set by participants' orders (design W); an order placed or changed while a round
  runs; a time limit on ordering.
- A valid form of FREEZE under `'both'`; any test of A_CF; the pool's coverage of counts
  under each display of the seed wave.
- A text alternative for the charts (answer 3); a layout for a phone held sideways; a rule
  on devices.
- Translations, time-outs, refill of dropouts, the official Docker base images: as before.
