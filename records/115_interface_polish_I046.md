# The interface of the pilot app, polished (KGi-DISS-I046, 2026-11-17)

Nothing here has been run on people. Every sentence a participant reads is still a draft, and
none was changed.

- **Request.** "let us consider it a pilot now take your ux and design grandmaster hat, expert
  in aesthetics guru and polish the experiment app for a user experience and graphical pov."
- **Decision recorded.** The first wave is a pilot (decision 2 of
  `records/114_staged_power_I045.md`). Which later steps are confirmatory is still open.
- **Reading.** Polish how `experiment/diss_market` looks and is used. Not the engine, the
  schedules, the data model, the session flow, the wording, the live economy, the earlier
  bandit app, or the database structure.
- **Freeze.** `freezes/00_freeze_I046.yaml` was pushed (b527df8) before any change to the
  app: nine invariants, twelve design decisions, fourteen gates, seven expectations. Its
  scorecard is verbatim in the file.
- **Operator's guide.** `experiment/MARKET_APP.md`.
- **Pictures, same session and same choices before and after.**
  `records/ui_I046_goods_market.png`, `records/ui_I046_prediction_markets.png`,
  `records/ui_I046_phone.png`, `records/ui_I046_clearing_full.png` (the clearing page at
  full size), `records/ui_I046_type_specimen.png` (the four typefaces compared).

**In short.** The presentation is redone and the behaviour is the same. Server, wording,
measures and stored data are unchanged; the exports of three bot sessions are identical
byte for byte. Fourteen gates pass on the final build. It took three full checks: after
each of the first two, going back over what the gates did not measure found defects, five
in all, three of them already in the old app. Five of my seven expectations failed in
whole or in part. The clearing page and the rating page, where the stimulus is read and
the dependent variable is taken, do not look as they did, and no person has seen either
version. Five points wait for the author.

## What changed

**Every page.**
- One white sheet on a tinted ground: 720 px wide for forms, 860 px for the instructions,
  1,120 px for the clearing page. On a phone the sheet is the screen. Before, a page lay
  directly on the grey ground, with white panels for its charts.
- Prose stays in IBM Plex Sans. Figures and their captions are now in IBM Plex Sans
  Condensed. Both have figures of one width, so a price or a count does not shift
  sideways while it changes.
- The top bar keeps its ten steps. The current step is wider and fills as the pages of
  the round are passed. The four market rounds were dots and are now bars like the
  others, set apart by a gap.
- The focus ring is ink. It was Square's blue, which could mark the Triangle card.
- Buttons are 48 px high (45 before). Boundaries of options, sliders and fields are
  drawn at 3.3:1 (1.3–1.4:1 before).
- The page declares its language and has a title and a tab icon. The framework sends an
  empty title and no language.

**Instructions.** Headings hang beside their text on wide screens. Two small legends
replace the old row of marks: the two goods with their shapes, and the marks of the price
chart on one filled and one unfilled order. They show four words the page did not show:
the goods' names in mixed case ("Square", "Triangle"; the text has them in capitals) and
"not filled". All are existing strings of `copy_en.py`.

**Order.** The two goods are white cards with a ring that fills when the good is chosen.
The word "ordered" is in ink. Before, it was white on the good's colour, at 4.4:1 on
Square and 3.2:1 on Triangle.

**Clearing.** One instrument on one sheet, the same on every screen: the price above, the
two counters in the middle, the running counts below, on one time axis at full width.
Before, a desktop showed two panels side by side, the price at the left and the counts at
the right, each about half as wide.
- The price line is at full strength and 1.25 px wide (1 px on a phone). It was 1.3 px at
  55% strength, 1.8–2.1:1 against its ground.
- The zone under the cap is the good's colour at 5% (8% before). Its caption stands in a
  band at the foot of the zone that no price can reach. Before, it lay where low prices
  are drawn, under their marks.
- Price labels are at the left; they were at the right, beside the cap's value. Hairlines
  mark clearings 30, 60 and 90 in both charts.
- Pointing at a clearing shows the same readout as before, now beside the clearing's
  crosshair and never over its point. Before, it was a line under the charts.
- The round's gain stands in the row of the button.

**Ratings.** Each answered item gets a tick, and four pips beside the button show how many
are answered. No word and no number was added. The sliders behave as before: a hollow
handle at a pre-drawn place until it is touched, steps of 5, no number shown, every slider
to be touched. Their track and its five marks are thinner and darker (4 px at 3.3:1; 6 px
at 1.4:1 before). The four items are set closer, so that they and the button fit in a
650 px window.

**Markets, evidence, bet, recall, closing, results.** The same parts on the sheet. On the
bet buttons the cost line is at full strength (it was at 85% on a tint, 3.6–4.5:1).
On phones the answer buttons of the recall and closing questions are 44 px high (42
before).

**Motion.** Unchanged in kind: a page cross-fades in 200–250 ms, a control changes state in
at most 220 ms, and nothing marks a fill, a miss, a basket or a bet with a flash or a
burst. With "reduce motion" set, no animation runs at all; see the third defect below.

## What did not change

| invariant | evidence |
|---|---|
| I1 server | `engine.py` and `bots_model.py` are byte-identical. `__init__.py` differs in eleven lines (nine added, two removed), all of which hand display values to templates: how far into its round a page is (for the top bar), and the goods and one existing string for the legends of the instructions. No model field, form field, validation, page order, payoff, export column or bot changed. The exports of three bot sessions are identical to the baseline's (G1). |
| I2 information | Same text on every page apart from four words on the instructions page (G3). Same durations and pacing: `settings.py`, `timeline.ts` and `env.ts` are unchanged. |
| I3 wording | `copy_en.py` is unchanged. No new string. |
| I4 arms | One set of templates, styles and scripts. The two members of a pair who make the same choices get the same pages apart from the board's numbers (G5). |
| I5 measures | `slider.ts` is unchanged. Rating sliders: pre-drawn start, hollow until touched, steps of 5, no number, all four to be touched. Forecast slider: no handle until placed. Every stored value equals the value set (G8). |
| I6 colour rule | Square `#2a78d6`, Triangle `#eb6834`, trader slate `#3f4756`, YES `#1f9d55`, NO `#c93a9a`; one light theme. On order, clearing and rating pages no colour but the goods' (G12). |
| I7 isolation | No request to another host. Five font files under the SIL Open Font License 1.1 ship with the app. No name, logo or layout of a real market. |
| I8 access | Keyboard use and the stepped reveal under reduced motion are kept. One part of reduced motion did not work in the old app and works now (third defect below). |
| I9 leaks | No page carries a later round, the other good's prices, evidence before the first forecast, a bet price before the second, or how a market settles (G6). |

## The gates

Measured with `tools/browser_run.py` on the final build and, with the same version of the
tool, on the tree before the change (c73284a): ten sessions in Chromium each time (two
members of a pair, a phone, a participant with reduced motion, a small phone, one session
played with the keyboard alone, four more window sizes). The old app was first measured
before any change, with an earlier version of the tool; the two measurements of it agree
on every check both made.

One run of the browser test failed, and I did not find why. It was the test at the end of
the second full check. The same checks had passed on that build a quarter of an hour
earlier, in the full run. The test's output was not kept, and while it ran I was
rebuilding the front end and playing two more browser sessions on the same two-core
machine. On the final build the test has passed four times: three times alone and once
with two more browser sessions playing beside it from start to end.

| gate | before | after | |
|---|---|---|---|
| G1 data: exports of three bot sessions (88 rows, 82 columns each) | hashes `ebc1e22e…`, `5e0082b0…`, `0dbd4d41…` | the same three | pass |
| G2 suites | | 8 engine, 6 app and 11 style tests pass; the browser test passes; type check and 22 unit tests pass; the bundle is the one built from the sources | pass |
| G3 information: text outside the charts, participant A | 2,702 words on 43 pages | 2,706 words; 42 pages the same; the instructions page gained "Square", "Triangle", "not", "filled" | pass with these four words |
| G3 marks on the clearing page: dots, ticks and vertices counted | right on 54 pages | right on 54 pages | pass |
| G4 wording | | `copy_en.py` unchanged, no new string | pass |
| G5 arms: page differences inside the pair beyond the board | none | none | pass |
| G6 leaks | none on 125 pages | none on 125 pages | pass |
| G7 isolation: requests elsewhere, console errors, failed requests (ten sessions) | none | none | pass |
| G8 measures: stored ratings and forecasts against the values set | 192 of 192 equal | 192 of 192 equal; the record of the sliders complete | pass |
| G9 timing of the reveal, planned 9,000 ms | 9,012 ms; 9,018 ms with the processor slowed four-fold | 9,014 ms; 9,009 ms | pass |
| G9 hidden tab (3 s) | stood still 3,005 ms, nothing shown | 3,010 ms, nothing shown | pass |
| G10 fit, 389 pages at seven window sizes | 34 findings | none | pass |
| G11 audit (axe-core, WCAG 2.1 A and AA; 86 pages) | serious: colour contrast on the bet and order pages; no language on any page | none of any impact | pass |
| G11 keyboard alone | session complete | session complete | pass |
| G11 controls under 44 × 44 px on 390 and 375 px phones | the answer buttons of the recall and closing questions (42 px high) | none | pass |
| G11 contrast of text, boundaries and data marks | price line 1.8–2.1:1; boundaries 1.3–1.4:1; Triangle 2.88 and 2.93:1 on two grounds | small text 4.8:1 or more, body text 8.3:1 or more, boundaries 3.0:1 or more, data marks 3.0:1 or more | pass after two corrections |
| G11 reduced motion: animations still running | six on every page change | none | pass after one correction |
| G12 colours on order, clearing and rating pages | goods' colours only | goods' colours only | pass |
| G13 weight of styles, script and fonts | 118,991 bytes | 169,076 bytes; a second build is byte-identical | pass |
| G14 frames during a reveal: median, longest | 16.7 ms, 53 ms | 16.7 ms, 39 ms | pass (limits 20 and 100) |
| G14 with the processor slowed four-fold: median, longest | 16.7 ms, 64 ms | 16.7 ms, 68 ms | pass (limit 34 for the median) |

Frame times vary from round to round, so they were taken in ten rounds on each tree, the
run's own and nine more. The median frame was 16.7 ms in every round on both trees, slowed
or not. The longest frame of a round, without slowdown: 24–72 ms on the final build, 30–53 ms
on the old app. With the processor slowed four-fold: 51–73 ms in nine rounds and 122 ms in
one on the final build, 52–88 ms on the old app. The reveal took 9,003–9,019 ms on the final
build and 9,001–9,019 ms on the old app.

Two checks were added to the run after the freeze, for defects 4 and 5 below. Marks of the
price chart that touch the caption of its zone: 117 on the 54 clearing pages before, none
after. The hover readout over the point it describes: not before (it was a line under the
charts), not after.

What the fit gate means in pixels: the rating page's button ended 884 px down in every
window before, out of view on a 768 px laptop and in the 860 px test window. It now ends
at 606 px of 650, 732 of 768 and 799 of 860. On a 375 × 667 phone the clearing page ends at
575 px (628 before).

Outside the gate's sizes: at 320 px the seven answer buttons of the closing questions are
37 × 44 px (42 × 42 before).

**Beyond what G3 compares.** Inside the charts the text is the same on 37 of 44 pages; on
the seven clearing pages the time axis of the lower chart gained the label "1", which the
upper chart already had. On phones the round label ("Round 3 of 10"), which the old app
hid, is kept for screen readers and still not shown; apart from it and the four words, the
phone sessions show the same text.

**In production mode** (the development server writes its own tab title, so the audit
cannot see this there): before, an empty title and no language on the pages opened, with
both audit rules failing; after, "Basket market", `en`, and no finding.

## Five defects the full checks did not see

Two complete checks of the build passed every gate they measured. Each time, going back
over what the gates did not measure found defects. Three of the five are older than this
iteration.

After the first full check, reading the clauses of gate G11 that it had not measured:

1. **A faint price line.** The line was drawn at 70% of its colour, 2.1–2.7:1 against its
   ground, under the 3:1 the gate asks of marks that carry data. In the old app it was at
   55% and 1.8–2.1:1. It is now at full strength, 1.25 px wide (1 px on phones), so the
   dots of filled orders still stand out on it.
2. **Triangle on grey.** Triangle's orange has 3.2:1 on white. On the grey panels I had
   put under the order cards and the goods legend, and on a tint of 7.5%, it had 2.96:1.
   In the old app the border of the chosen card stood on the grey ground (2.88:1) and the
   dots and ticks on a tint of 8% (2.93:1). The cards and the legend are white and the
   tint is 5% (3.02:1).
3. **Motion that "reduce motion" did not stop.** On every page change the top bar
   cross-faded for 250 ms, in the old app and in my build: the rule switched off the page's
   cross-fade and missed the bar's. Measured on both trees: six animations per page change
   before, none after.

After the second, looking through its screenshots:

4. **A caption over the data.** In the old app the caption of the fill zone lay under
   the marks of the price chart, where low prices are drawn: in the first round of the
   test session the lowest dot reached the top of its letters and stayed in view. I had
   drawn the caption over the marks, on a halo, so that no mark would cut a letter. The
   halo then hid that dot, a filled order. The caption now has a band of its own under
   the lowest possible price, and is drawn under every mark.
5. **A readout over its own point.** I had centred the hover readout on the clearing it
   describes. It covered the upper half of the chart there, and the clearing's own point
   with it. It now stands beside the crosshair: to its right, or to its left near the
   right edge.

Each is now measured on every run. The style test forbids a faint data mark and any tint
but 5%, and fixes the caption's band and its place under the marks.
`tools/mark_contrast.py` reads from the screenshots the ground each good's colour stands
on. The browser run lists every animation still running in its reduced-motion session,
counts the marks that touch the caption, and tests that the readout does not cover its
point; each of the three must come out empty.

**A last look, done by a tool.** After the third full check I did not rely on another
look at reduced pictures. `tools/layout_check.py` plays a session at each of seven window
sizes and tests every piece of text on every page, in the page and in the charts: is it
cut off by the box that clips it, does it lie over another piece of text, does it leave
the window or its sheet. It finds nothing on 305 pages at the seven sizes, nothing on 87
pages of a session without a board, and nothing at 640 × 430, the test window at 200%
zoom. It does find each of three faults put into a page by hand.

Three more errors were in the tools. The browser run's completeness check counted five
participants, and the keyboard session adds a sixth: the run printed FAIL on the baseline
and on the first full check for that reason alone. The run read the order page at once
after the choice, while the word on the chosen card fades in over 180 ms: the word was
counted on some pages and not on others. And the browser test, since I043, stopped only
the parent of its server and left the server itself running after every run. All three
corrected.

## Expectations

Five of the seven I froze failed in whole or in part.

| | expectation | outcome |
|---|---|---|
| E1 | G1, G4, G5, G6, G7, G9 pass at the first attempt | **failed.** The first build crashed the order page: a display variable I added had the name of one the page already used. All six passed from the second build on. |
| E2 | the baseline audit finds no language and no title on every page and a contrast failure on the bet page; afterwards nothing serious | **partly.** No language: yes. Contrast on the bet page: yes, and on the order page, which I had not predicted. No title: not on the development server; yes in production mode. Afterwards: nothing of any impact. |
| E3 | the keyboard-only session completes before and after | held. |
| E4 | the rating page fits at 1366 × 768 and needs scrolling at 1366 × 650; the evidence page fits at 1366 × 768 | **partly.** Both fit at 1366 × 768. The rating page also fits at 1366 × 650, with 44 px to spare. |
| E5 | the bundle weighs 150–250 KB | held: 165 KB. |
| E6 | frames pass; with the four-fold slowdown the median frame is 17–34 ms | **partly.** They pass. The slowed median is 16.7 ms, below the interval I gave: the slowdown did not move the median. |
| E7 | the list of added text is empty or holds chart axis labels only | **failed.** Four words on the instructions page, from the two legends. One axis label inside a chart. |

One statement of the freeze was also wrong as written: decision D9 said control states
change in 120–240 ms. One, the chosen good's shape growing by 5%, took 280 ms, as in the
old app. It now takes 220 ms.

## Type and colour

**Typeface (decision D3).** Four candidates were set on the app's own screens
(`records/ui_I046_type_specimen.png`) and judged in the frozen order: legible at 16 px;
figures of one width, with 0 and O, and 1, l and I told apart at 12 px; open licence and
shipped with the app; at most 160 KB together; character.

| candidate | figures of one width | 1, l, I apart | weight | result |
|---|---|---|---|---|
| A. IBM Plex Sans, as before | by default (every figure 600 units of 1,000) | yes: serifed I, tailed l, footed 1 | 71,024 bytes, three files | kept for prose |
| B. A with IBM Plex Sans Condensed for figures and captions | by default (540 units: a tenth narrower) | yes | 110,792 bytes, five files | **chosen** |
| C. Mona Sans | only with a font feature (325–612 units by default); the zero then has a slash | I and l the same | 98,124 bytes, one variable file | out on the second criterion |
| D. Archivo | within 2 units by default (575–577) | I and l the same | 90,104 bytes, one variable file | out on the second criterion |

All four families are under the SIL Open Font License 1.1. B keeps the face the app
already had and sets figures and their captions a tenth narrower.

**Colour.** The values of the colour rule did not change and were run through the palette
validator again, against the white sheet: Square and Triangle are apart by 24.7 under the
worst colour-vision type and 33.6 with full vision; the trader's slate is at least 21.6
from either good; YES against NO 10.3. The validator fails the slate on lightness (.397
against a band of .43–.77) and on colourfulness (.028 against .10). That is the rule
itself: people are drawn in a neutral, colour belongs to goods and bets.

| pair | contrast |
|---|---|
| body text on the sheet, on a grey panel, on the ground | 18.3, 16.9, 16.6 |
| second text colour on the sheet, on a grey panel | 8.9, 8.3 |
| small grey text on the sheet, on a grey panel, on the ground | 5.4, 5.0, 4.9 |
| the dash that stands for a forecast not yet given (38 px high) | 4.5 |
| YES and NO buttons: words on the tint; white on the chosen button | 4.8 and 5.8; 5.4 and 6.7 |
| boundaries of controls on the sheet, on a grey panel, on the ground | 3.3, 3.1, 3.0 |
| Square on white, on its tint | 4.4, 4.1 |
| Triangle on white, on its tint | 3.2, 3.0 |
| trader's slate on white | 9.4 |

Faint on purpose, because they show an empty place and the filled one carries the
information: the tick of an order that did not fill and an empty basket slot (1.4:1), a
round to come in the top bar (1.3:1), the track of the current step (1.5:1).

## Risks

- **The display is part of the stimulus.** The clearing page now shows the price above
  the counts instead of beside them, with both charts about twice as wide on a desktop and
  a stronger price line. Both arms get the same page, and no person has seen either
  version, so no comparison is broken. But how strongly people attend to the board, and
  how many outcomes they take from a round (the quantity that moves the main study from
  84 pairs to 288–336, memo 114), were assumptions before and are assumptions now. The
  pilot reads them on this display, not on the earlier one.
- **The rating page changed where the dependent variable is taken.** A tick on each
  answered item and four pips are new; they carry no outcome and no value. The slider
  behaves as before, but its track and its five marks (at 0, 25, 50, 75, 100) are darker,
  3.3:1 against 1.4:1. Darker marks may draw answers to them. The pilot's ratings will
  show whether answers heap at multiples of 25.
- **Triangle's colour has no margin.** It has 3.2:1 on white and 3.0:1 on its tint. A
  darker ground under it anywhere breaks 3:1. The style test and `tools/mark_contrast.py`
  guard this; a change of palette would have to move Triangle first.
- **Language and title are set by script.** A browser with scripts off gets neither; the
  app does not work there in any case.

## For the author (not applied: each needs a new sentence or changes a term)

1. A caption for the lower chart of the clearing page. It has none; "Filled orders" would
   do. The freeze allowed two new strings; I added none.
2. The bet button shows a price in cents ("50¢") and a cost in points ("costs 10 points").
   Two units on one button.
3. A text alternative for the charts, for people who use a screen reader.
4. Devices. On a 390 px phone a clearing has 2.3 px of the price chart, and the dots of
   filled orders are 3.8 px wide; the strip of ticks under the chart carries the fills.
   `min_window_width` is still 0. At 320 px the seven answer buttons of the closing
   questions are 37 px wide, and at 320 × 568 the price path has about 50 px of height.
5. Whether the two legends on the instructions page stay. They show the goods' names in
   mixed case and the words "not filled", which the page did not show before.

## Not done

- No test with a screen reader. No translation.
- No test on a real phone or in Firefox or Safari: every check ran in Chromium.
- The specification of the pilot and its frozen analysis, the data model, the live
  economy, recruitment: not part of this iteration.
