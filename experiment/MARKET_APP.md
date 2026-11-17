# diss_market: the oTree build of the yoked ten-repetition design

Status (KGi-DISS-I042, redesigned in KGi-DISS-I043, interface polished in KGi-DISS-I046):
a basket economy followed by four prediction markets, built and verified with bots and in a
browser. Nothing has been run on people. The first wave is a pilot (author decision,
2026-11-17). Every sentence a participant reads is a draft; ethics, payment and the
description of the board and of the forecast sources are author decisions
(`diss_market/copy_en.py`, `settings.py`).

Design: `YOKED_DESIGN.md`. Contracts and scorecards: `../freezes/00_freeze_I042.yaml`,
`../freezes/00_freeze_I043.yaml`, `../freezes/00_freeze_I046.yaml`. Memos:
`../records/112_basket_market_I043.md`, `../records/115_interface_polish_I046.md` (with
pictures of every page before and after: `../records/ui_I046_*.png`).

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
| 1–6 | Order (one of two goods) → Clearing (120 clearing prices over 9 s) → Rate (three fairness items, one entitlement item) |
| 7–10 | Market (price history, first forecast) → Evidence (ten trial closes, or a source's forecast; second forecast) → Bet (YES, NO or pass at the posted price) → Recall |
| 10 (after the task) | Closing, Results (the markets settle) |

The Clearing page is one instrument on one sheet. Above, the price of the ordered good
against the cap, with a dot on the line and a coloured tick in the strip underneath for
every filled order. The caption of the zone under the cap stands in a band at its foot
that no price can reach, so it never meets a mark. Below the chart the two counters, own
and trader, with the baskets completed. Below them the running counts of filled orders as
two curves on a fixed axis. The two charts share one time axis at full width, at every
screen width. Once the round has cleared, pointing at a clearing shows its price, whether
the order filled, and the two counts at that clearing, in a readout beside the clearing's
crosshair (not on phones). The points total moves only when the round has cleared.

- The server decides every sequence. A reload replays a reveal; it cannot replay an order.
- A page holds only its own round and only the ordered good's prices. A market's evidence
  reaches the browser after the first forecast is stored, and its bet price after the second.
  How a market settles reaches the browser on the Results page.
- The two arms get the same pages, styles and scripts. Only the board's numbers differ.
- A participant takes the next free slot of the schedule file on leaving the quiz. Slots
  2j and 2j+1 are the two members of pair j. An arrival without a free slot sees a
  "session full" page and does not start.

## Colours, type and marks

One fixed light theme (the display is part of the stimulus). Goods carry colour: Square
`#2a78d6`, Triangle `#eb6834`. People are drawn in neutral tones: the trader on the board in
slate `#3f4756`, a forecast source in ink. YES `#1f9d55` and NO `#c93a9a` appear on the bet
buttons and the settled markets only, always with the word; the pair is green against
magenta so that it stays apart for people who do not tell red from green. Nothing on a
procurement screen is green or red. No name, logo or layout of a real market is used.

- **Type.** Prose in IBM Plex Sans, figures and their captions in IBM Plex Sans Condensed
  (SIL Open Font License 1.1; five files, shipped with the app). Every figure has the same
  width, so prices and counts do not jitter while they change.
- **Sheet.** One white sheet per page on a tinted ground: 720 px wide for forms, 860 px
  for the instructions, 1,120 px for the Clearing page (1,280 px on a large monitor). On a
  phone the sheet is the screen.
- **Contrast.** Body text at 7:1 or more, small text at 4.5:1 or more, boundaries of
  controls and data marks at 3:1 or more. Triangle's orange has 3.2:1 on white and nothing
  to spare: a good's colour is drawn at full strength, on white or on the good's own tint
  (its colour at 5%), nowhere else. Marks that only show an empty place (an order that did
  not fill, a basket slot not yet filled, a round to come) are faint on purpose.
- **Focus and keyboard.** The focus ring is ink. Every page can be completed with Tab,
  Space, the arrow keys and Enter.
- **Motion.** A page cross-fades in 200 to 250 ms; a control changes state in at most
  220 ms; nothing marks a fill, a miss, a basket or a bet with a flash or a burst. With
  "reduce motion" set in the browser or the system, no animation runs and the reveal of a
  round proceeds in steps over the same duration.
- **Where one is.** The top bar shows the ten rounds; the current one is wider and fills
  as its pages are passed. The Rate page marks each answered item and shows four pips
  beside the button.
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

All the browser checks at once (the accessibility audit needs `npm ci` in `frontend/`):

```
python tools/browser_run.py --strict --keyboard --sizes \
    --axe frontend/node_modules/axe-core/axe.min.js \
    --frames-config market_dev --timing-config market_dev --out report.json
```

Front end (only needed to change it; the bundle is in the repository):

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
| `market_bots_*`, `market_e2e` | | bots and browser tests |

Keys: `schedule_path`, `board_source`, `pool_path`, `reveal_ms`, `probe_reveal_ms`,
`source_reveal_ms`, `recall_check`, `prize_points`, `points_to_currency`, `completion_url`,
`min_window_width`, `first_slot`, `last_slot`. Two sessions on one schedule file need
disjoint slot ranges. Environment: `MARKET_SCHEDULE`, `MARKET_SEED_SCHEDULE`, `MARKET_POOL`.

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
is given a schedule with sources, or, for people in production, if the pool is a
placeholder. Bot records are refused by the pool tool unless `--allow-bots` is given.

## Data

Custom export (`/api/export_app_custom?app=diss_market`, or the admin's export page):

- one `repetition` row per participant and repetition. Procurement rounds: the good, fills,
  the fill record and the clearing prices, goods held, the board's record, source and
  label, the four ratings with their start positions, timings, reveal timing (planned,
  measured, time the tab was hidden). Markets: market and its uid, kind of evidence, the
  record or the source's forecast, id and track record, the two forecasts, the bet, its
  price and points, how the market closed, recall, timings;
- one `participant` row: `T`, the bet statistic, bet points, the paid forecast, points,
  closing answers, window size and reduced-motion setting.

`python experiment/analysis/yoked_from_export.py export.csv --config market_pilot` scores
the reporting set, the bet test, and `T` by kind of evidence.

## What was checked, and how to repeat it

| check | command |
|---|---|
| engine: fills and boards against the simulation's rule; price ≤ cap exactly when the order fills; markets, bets, sources; schedule formats | `pytest experiment/analysis/tests/test_market_engine_I043.py` |
| bots: stored data = schedule and engine; kernel against both certifications; 72 pairs of gate bots; seed wave → pool → board and sources; refusals | `pytest experiment/analysis/tests/test_market_app_I043.py` |
| browser: no error, no outside request, no leak, equal pages, reload, back, re-post; every stored rating and forecast equals the value dragged; chart marks counted; the zone's caption meets no mark and the hover readout does not cover its own point; every page fits at 1920 × 1080, 1366 × 768, 1366 × 650, 390 × 844 and 375 × 667 and does not scroll sideways at 320 px; accessibility audit (axe-core, WCAG 2.1 A and AA); a session with the keyboard alone; nothing moving with reduced motion; only the goods' colours on procurement pages. About a quarter of an hour | `pytest experiment/analysis/tests/test_market_browser_I043.py` |
| interface styles: contrast of the palette, the colour rule, a good's colour on white or its own tint, data marks at full strength, fonts shipped and nothing fetched elsewhere, weight, page hooks | `pytest experiment/analysis/tests/test_market_ui_I046.py` |
| the ground each good's colour stands on, read from screenshots | `python experiment/tools/mark_contrast.py DIR` |
| the words on every page, before a change against after it | `python experiment/tools/text_before_after.py before.json after.json` |
| text cut off, text over text, text outside the window or its sheet, at seven window sizes (server must be up) | `python experiment/tools/layout_check.py` |
| reveal timing and frame times at the session's real speed | `python experiment/tools/browser_run.py --frames-config market_dev --timing-config market_dev` |
| front end | `cd experiment/frontend && npm run check` |

## Not done here

- No page time-outs and no refill of slots left by dropouts.
- English only. No test with a screen reader. The charts carry no text alternative beyond
  the figures printed next to them. The Clearing page's lower chart has no caption (it
  would be a new sentence; wording is the author's).
- At 320 px the seven answer buttons of the closing questions are 37 px wide (44 px from
  375 px on).
- No check that people read a price curve as a record of fills.
- The official Docker base images could not be pulled where this was built; see the freezes.
