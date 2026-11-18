# diss_market: the oTree build of the yoked ten-repetition design

Status (KGi-DISS-I042, redesigned in KGi-DISS-I043, interface polished in KGi-DISS-I046, laid
out for phones in KGi-DISS-I047): a basket economy followed by four prediction markets, built
and verified with bots and in a browser. Nothing has been run on people. The first wave is a
pilot (author decision, 2026-11-17). Every sentence a participant reads is a draft; ethics,
payment and the description of the board and of the forecast sources are author decisions
(`diss_market/copy_en.py`, `settings.py`).

Design: `YOKED_DESIGN.md`. Contracts and scorecards: `../freezes/00_freeze_I042.yaml`,
`../freezes/00_freeze_I043.yaml`, `../freezes/00_freeze_I046.yaml`,
`../freezes/00_freeze_I047.yaml`. Memos: `../records/112_basket_market_I043.md`,
`../records/115_interface_polish_I046.md`, `../records/116_phone_market_I047.md` (pictures:
`../records/ui_I047_*.png`).

## What is where

| path | what |
|---|---|
| `diss_market/__init__.py` | the oTree app: pages, data model, export, bots |
| `diss_market/engine.py` | everything shown, computed from the schedule (no oTree import) |
| `diss_market/copy_en.py` | all wording (DRAFT) |
| `diss_market/*.html` | page templates (`_market.html` and `_ask.html` are shared parts) |
| `frontend/` | TypeScript and CSS sources, unit tests, build script |
| `frontend/src/chart.ts`, `svgchart.ts` | chart arithmetic (tested) and the SVG charts |
| `_static/diss_market/` | the built bundle and fonts (tracked; rebuilt by `npm run build`) |
| `tools/yoked_schedules.py` | pre-drawn schedules (`--format 3` for the app) |
| `tools/make_board_pool.py` | pool of real earlier records: board fills and forecast sources |
| `tools/browser_run.py` | plays whole sessions in Chromium and checks them |
| `tools/mark_contrast.py` | reads the screenshots: the ground each good's colour stands on |
| `tools/text_before_after.py` | compares the words on every page between two runs |
| `tools/layout_check.py` | looks at every page for text that is cut off, overlaps or leaves its sheet |
| `analysis/yoked_from_export.py` | export → reporting set (the certification's code) |
| `Dockerfile`, `docker-compose.yml`, `.env.example` | container build and stack |

## The session, page by page

| oTree round | pages |
|---|---|
| 1 (before the task) | Consent, Instructions, Quiz (repeat until right) |
| 1–6 | the goods market: Order (open for orders) → Clearing (running: 120 clearing prices over 9 s) → Rate (three fairness items, one entitlement item) |
| 7–10 | Market (price history, first forecast) → Evidence (ten trial closes, or a source's forecast; second forecast) → Bet (YES, NO or pass) → Recall |
| 10 (after the task) | Closing, Results (the markets settle) |

**The goods market is one screen in two states**, on two pages of the server (I047). It
follows the pattern of a prediction-market page with several outcomes: a chart with one line
per outcome, a row per outcome with its price and a button, and a ticket to confirm. It
carries no name, logo, colour scheme, typeface or page of any real market.

- *Open for orders (Order).* The frame of the chart: the cap, the zone under it and what the
  zone means, no price. A row per good with its shape, its name and a button. Once a good is
  chosen, its row and the zone take its colour, and the ticket at the foot names it beside
  the cap; the button under the ticket sends the order.
- *Running (Clearing).* The same chart, drawn clearing by clearing in real time. The head of
  a price line is the good's own shape. The ordered good's line lies on top and carries a dot
  at every filled order; the strip under the plot has a tick per clearing, coloured where the
  order filled. Under the chart the two rows again, each with its good's clearing price; the
  ordered good is marked. Then "Filled orders": the two counters (You, Trader) and their
  running counts as two curves. The points total moves only when the round has cleared.
- *Cleared.* A finger or a pointer moved along either chart shows the clearing under it: its
  number, the price and whether the order filled, the two counts. The reading takes the
  place of the heading while it is shown, so it never lies over a mark.

**Which prices are drawn** is the session key `price_curves`:

| value | what the running screen draws | status |
|---|---|---|
| `'both'` (the default of every configuration in `settings.py`) | both goods' clearing prices of the round; the other good's row shows its price | certified in I047 on simulated cohorts, under an assumption no simulation can test (`YOKED_DESIGN.md`, "Both goods' prices on screen") |
| `'own'` (what a configuration without the key gets) | the ordered good's only; the other good's row shows a dash | the display certified in I043 |

The other good's prices are `engine.price_path` for that good: what the participant would have
seen had they ordered it. One draw settles both goods, so the two lines move in step and the
better good is the cheaper one at every clearing. The browser records how many price lines it
drew (`curves` in `settle_meta`).

- The server decides every sequence. A reload replays a reveal; it cannot replay an order.
- A page holds only its own round. The order page holds no price. A market's evidence reaches
  the browser after the first forecast is stored, and its bet after the second. How a market
  settles reaches the browser on the Results page.
- The two arms get the same pages, styles and scripts. Only the board's numbers differ.
- A participant takes the next free slot of the schedule file on leaving the quiz. Slots
  2j and 2j+1 are the two members of pair j. An arrival without a free slot sees a
  "session full" page and does not start.

## One layout, made for a phone

The phone is the reference device (I047): 390 × 844 and 360 × 640. The page is a single column
of at most 480 px at every window width; a laptop shows the same column on the tinted ground.
Every participant therefore gets the same arrangement of the same things.

- **Height.** The column is as high as the visible window (without the browser's bars). On the
  goods market the charts take the room the rest of the page leaves, between a least and a
  greatest height, and the page's button stands at the foot. A chart lower than 128 px is
  drawn without the zone's caption.
- **What fits.** At every size measured, from 320 × 568 up and including 375 × 553 and
  390 × 664 (phones with the browser's bars showing), five pages are exactly as high as the
  window, so nothing scrolls: both states of the market screen, a market's first forecast, the
  bet and the recall question. (The framework ends every page with an empty line, which made
  each of them a line higher than the window; the stylesheet takes it out. A development
  server hides this under its debug panel, so it is measured in production mode.)
- **What needs scrolling.** The rating page shows its four sliders and its button together at
  375 × 667, 390 × 664 and every larger size; its button lies 22 px below the window at
  360 × 640, 56 px at 375 × 553 and 65 px at 320 × 568. The evidence page shows the evidence
  and the second forecast with its button together at the same sizes; at 360 × 640 it is up to
  45 px too high with a record and 36 px with a source's forecast, at 375 × 553 63 and 66 px,
  at 320 × 568 91 and 74 px. When the second forecast opens below the fold it is brought into
  view. Instructions, quiz and closing questions are longer than a screen on every phone; the
  results page is at 375 × 667 and smaller.
- **Fingers.** Every control is at least 44 × 44 px from 360 px on (at 320 px the seven answer
  buttons of the closing questions are 39 px wide); a page's button is 50 px high (48 px in a
  window lower than 620 px). Hover
  styles exist only where a pointer can hover.
- **Sliders.** A finger that taps sets the value when it lifts; a finger that drags sideways
  sets it while it moves. A gesture that scrolls the page, or that wanders up or down without
  scrolling anything, leaves the slider exactly as it was: nothing is stored for it. Mouse
  and keyboard as before.
- **Held sideways, or zoomed.** There is no layout for a phone held sideways and no notice
  asking to turn it: the same column stands in the middle and every page scrolls (at
  844 × 390 and 667 × 375 no text is cut off or lies over other text). The layout holds down
  to 320 px of width. A 390 px phone at 150% page zoom has 260 px (one label of the
  development board then leaves the window); at 200% it has 195 px and the layout breaks.
  The window's size, whether the whole running screen was in view, and how far the page was
  scrolled during the reveal are written into `settle_meta` (`vw`, `vh`, `fit`, `scrolled`).
- **A pull at the top of the page** does not reload it (`overscroll-behavior`); not measured
  on a phone.

## Colours, type and marks

One fixed light theme (the display is part of the stimulus). **Colour says which good a mark
belongs to and nothing else** (I047): Square `#2a78d6`, Triangle `#eb6834`, always together
with the good's shape. The trader on the board is drawn in slate `#3f4756`, a forecast source
in ink. YES and NO are in ink and told apart by the word; nothing is green, red or magenta.

- **Type.** Prose in IBM Plex Sans, figures and their captions in IBM Plex Sans Condensed
  (SIL Open Font License 1.1; five files, shipped with the app). Every figure has the same
  width, so prices and counts do not jitter while they change.
- **Contrast.** Body text at 7:1 or more, small text at 4.5:1 or more, boundaries of
  controls and data marks at 3:1 or more. A good's colour is drawn at full strength. Triangle's
  orange has 3.20:1 on white and 3.02:1 on its own tint (its colour at 5%). With both price
  lines drawn, the line of the good not ordered crosses the fill zone, which has the ordered
  good's tint: Triangle's orange on Square's tint has 3.001:1, at the floor. Marks that only
  show an empty place (an order that did not fill, a basket slot not yet filled, a round to
  come) are faint on purpose.
- **Units.** A bet shows one figure, the ticket's cost in points ("costs 10 points"); what a
  winning ticket pays is in the sentence above. No currency sign before the last page.
- **Focus and keyboard.** The focus ring is ink. Every page can be completed with Tab,
  Space, the arrow keys and Enter.
- **Motion.** A page cross-fades in 200 ms; a control changes state in at most 220 ms;
  nothing marks a fill, a miss, a basket or a bet with a flash or a burst. With "reduce
  motion" set in the browser or the system, no animation runs and the reveal of a round
  proceeds in steps over the same duration.
- **Where one is.** The top bar shows the ten rounds; the current one is wider and fills
  as its pages are passed. Before the task the bar shows the study's name instead. The Rate
  page marks each answered item and shows four pips beside the button.
- **Title and language.** The page's language (`en`) and title are set by the script: the
  framework sends neither.

## Run it

```
pip install -r requirements.txt
otree devserver 8000                       # demo page at http://localhost:8000
otree test market_bots_random 8            # bots; add --export=DIR for the data
python tools/browser_run.py --shots DIR    # full sessions in Chromium (server must be up)
python tools/mark_contrast.py DIR          # the goods' colours against their grounds, from those screenshots (needs numpy, Pillow)
```

All the browser checks at once, for one display (the accessibility audit needs `npm ci` in
`frontend/`):

```
python tools/browser_run.py --config market_e2e_both --curves both --strict --keyboard --sizes \
    --axe frontend/node_modules/axe-core/axe.min.js \
    --frames-config market_real_both --timing-config market_real_both --out report.json
```

and the same with `own` in the three places. Against a production server (`otree prodserver`
with `OTREE_PRODUCTION=1`) the runner reads the export with the server's REST key, taken from
`OTREE_REST_KEY` in its own environment; only there, without the debug panel, can it measure
that a page is no higher than the window. The browser test does all three runs. Front end
(only needed to change it; the bundle is in the repository):

```
cd frontend && npm ci && npm run check     # type check, unit tests, bundle
```

Docker:

```
cp .env.example .env                       # set the three secrets
docker compose up --build -d               # http://localhost:8000, admin user "admin"
```

## Session configurations (`settings.py`)

| name | board and sources | use |
|---|---|---|
| `market_seed` | none (needs a `--no-social` schedule) | seed wave: its records feed the pool |
| `market_pilot` | pool | board and sources replay real earlier records |
| `market_dev` | computer-generated | development only; refused for people in production |
| `market_bots_*` | | bots |
| `market_e2e`, `market_e2e_both`, `market_e2e_own`, `market_e2e_seed` | | browser tests: short reveals; the display named, or the default; without a board |
| `market_real_both`, `market_real_own` | | one round at the real speed, for the timing and frame measurements |

Keys: `schedule_path`, `board_source`, `pool_path`, `price_curves`, `reveal_ms`,
`probe_reveal_ms`, `source_reveal_ms`, `recall_check`, `prize_points`, `points_to_currency`,
`completion_url`, `min_window_width`, `first_slot`, `last_slot`. Two sessions on one schedule
file need disjoint slot ranges. Environment: `MARKET_SCHEDULE`, `MARKET_SEED_SCHEDULE`,
`MARKET_POOL`. `min_window_width` is 0: every device may take part; which devices are admitted
is a recruitment setting.

## From a seed wave to a pilot with a truthful board and truthful sources

Run from the repository root.

1. Seed schedules, with record evidence only:
   `python experiment/tools/yoked_schedules.py --pairs N --seed S --format 3 --no-social --out experiment/schedules/seed.json`
2. Run the seed wave with `market_seed` (`MARKET_SEED_SCHEDULE` pointing at the file).
   Participants see no board and no source.
3. Build the pool: `python experiment/tools/make_board_pool.py seed_export.csv --out experiment/pools/pool.json`.
   It prints the records per round, how many fit the HIGH band, and for each market how
   many forecasts lie inside the band a source is taken from.
4. Pilot schedules that reuse the seed wave's markets:
   `python experiment/tools/yoked_schedules.py --pairs N --seed S2 --format 3 --markets-from experiment/schedules/seed.json --out experiment/schedules/pilot.json`
5. Run the pilot with `market_pilot`, `MARKET_SCHEDULE` and `MARKET_POOL` pointing at the
   files. HIGH shows a rich-round record with a rate in [.65, .80]; LOW shows a record of
   the same round nearest to the participant's own count. A source is a real forecast of
   the same market given after ten trial closes, inside 80–100 (favourable) or 0–20
   (unfavourable), from a forecaster with the best track record available, as near 90 / 10
   as the pool allows; both members of a pair get the same one.

The session does not start if the pool has no usable forecast for a market, if a seed wave
is given a schedule with sources, if `price_curves` is neither `'both'` nor `'own'`, or, for
people in production, if the pool is a placeholder. Bot records are refused by the pool tool
unless `--allow-bots` is given.

## Data

Custom export (`/api/export_app_custom?app=diss_market`, or the admin's export page). Its
columns are those of I043; I047 added none.

- one `repetition` row per participant and repetition. Procurement rounds: the good, fills,
  the fill record and the clearing prices of the ordered good, goods held, the board's record,
  source and label, the four ratings with their start positions, timings, and `settle_meta`:
  reveal timing (planned, measured, time the tab was hidden), reduced motion, the number of
  price lines drawn, the window's size, whether the screen fitted it, how far it was scrolled.
  Markets: market and its uid, kind of evidence, the record or the source's forecast, id and
  track record, the two forecasts, the bet, its price and points, how the market closed,
  recall, timings;
- one `participant` row: `T`, the bet statistic, bet points, the paid forecast, points,
  closing answers, window size, touch and reduced-motion setting.

The other good's prices are not stored: they are `engine.price_path` of the schedule, the
round and the good not ordered. The export names the session configuration.

`python experiment/analysis/yoked_from_export.py export.csv --config market_pilot` scores
the reporting set, the bet test, and `T` by kind of evidence.

## What was checked, and how to repeat it

| check | command |
|---|---|
| engine: fills and boards against the simulation's rule; price ≤ cap exactly when the order fills; markets, bets, sources; schedule formats | `pytest experiment/analysis/tests/test_market_engine_I043.py` |
| bots: stored data = schedule and engine; kernel against both certifications; 72 pairs of gate bots; seed wave → pool → board and sources; refusals | `pytest experiment/analysis/tests/test_market_app_I043.py` |
| browser, three runs: each display on a development server, and the default display on a production server (what a participant gets). No error, no outside request, no leak, equal pages across arms, reload, back, re-post; the prices sent are the engine's, one series under `'own'` and two under `'both'`; every stored rating and forecast equals the value set by mouse, by finger and by keyboard; three gestures that start on a slider and are not meant for it store nothing; chart marks counted, the ordered good's line on top; a finger on the cleared chart reads the clearing under it; every page fits as stated above at ten window sizes, nothing after the form takes room, and in production a screen that fits is not higher than the window; accessibility audit (axe-core, WCAG 2.1 A and AA); a session with the keyboard alone; nothing moving with reduced motion; no colour but the goods' on any page. About a quarter of an hour per run | `pytest experiment/analysis/tests/test_market_browser_I043.py` |
| the same with reveal timing and frame times at the real speed on the emulated phone, the reports and the screenshots kept | `MARKET_BROWSER_OUT=DIR pytest experiment/analysis/tests/test_market_browser_I043.py` |
| interface rules without a browser: contrast of the palette, no colour for a side or an outcome, a good's colour on white or a 5% tint, data marks at full strength, the market chart high enough for its axis figures to clear its tag, one column at every width, nothing after the column, sizes of controls, the slider's touch rule, one figure on a bet, wording against 569c3f8, fonts shipped and nothing fetched elsewhere, weight, page hooks | `pytest experiment/analysis/tests/test_market_ui_I046.py` |
| the ground each good's colour stands on, read from screenshots | `python experiment/tools/mark_contrast.py DIR` |
| the words on every page, before a change against after it | `python experiment/tools/text_before_after.py before.json after.json` |
| text cut off, text over text, a figure of a chart under the dark box of a tag, text outside the window or its sheet, at ten window sizes (server must be up; do not edit a Python file of the project meanwhile: the development server restarts) | `python experiment/tools/layout_check.py --config market_e2e_both` (also `market_e2e_own`, `market_e2e_seed`) |
| the certification of the two-curve display on simulated cohorts | `python experiment/analysis/live_cert_ad_I047.py`; `pytest experiment/analysis/tests/test_live_I047.py` |
| front end | `cd experiment/frontend && npm run check` |

## Not done here

- No page time-outs and no refill of slots left by dropouts.
- English only. No test with a screen reader. The charts carry no text alternative beyond
  the figures printed next to them (author decision, 2026-11-17).
- No real phone, no Safari, no Firefox: every check ran in Chromium, phones by emulation
  (window size, pixel ratio, touch events, a mobile user agent). What a phone's own browser
  does with its bars, with a pull at the top of the page and with its text-size setting is
  not measured.
- No layout for a phone held sideways, and none below 320 px of width.
- Two existing sentences speak to a mouse or a laptop and were left as they are (wording is
  the author's): the hint under an unset forecast ("Click or drag on the line…") and the
  notice shown when `min_window_width` is set ("…use a laptop or desktop computer…").
- The instructions do not say that both goods' prices are drawn, nor that one draw moves both.
- No check that people read a price curve as a record of fills.
- Prices set by the participants' own orders (design W, `LIVE_ECONOMY.md`) are not built.
- The official Docker base images could not be pulled where this was built; see the freezes.
