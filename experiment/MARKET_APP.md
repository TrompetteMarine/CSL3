# diss_market: the oTree build of the yoked ten-repetition design

Status (KGi-DISS-I042, redesigned in KGi-DISS-I043): a basket economy followed by four
prediction markets, built and verified with bots and in a browser. Nothing has been run on
people. Every sentence a participant reads is a draft; ethics, payment and the description
of the board and of the forecast sources are author decisions (`diss_market/copy_en.py`,
`settings.py`).

Design: `YOKED_DESIGN.md`. Contracts and scorecards: `../freezes/00_freeze_I042.yaml`,
`../freezes/00_freeze_I043.yaml`. Memo: `../records/112_basket_market_I043.md`.

## What is where

| path | what |
|---|---|
| `diss_market/__init__.py` | the oTree app: pages, data model, export, bots |
| `diss_market/engine.py` | everything shown, computed from the schedule (no oTree import) |
| `diss_market/copy_en.py` | all wording (DRAFT) |
| `diss_market/*.html` | page templates (`_market.html` and `_ask.html` are shared parts) |
| `frontend/` | TypeScript and CSS sources, unit tests, build script |
| `frontend/src/chart.ts`, `svgchart.ts` | chart arithmetic (tested) and the SVG charts |
| `_static/diss_market/` | the built bundle and font (tracked; rebuilt by `npm run build`) |
| `tools/yoked_schedules.py` | pre-drawn schedules (`--format 3` for the app) |
| `tools/make_board_pool.py` | pool of real earlier records: board fills and forecast sources |
| `tools/browser_run.py` | plays whole sessions in Chromium and checks them |
| `analysis/yoked_from_export.py` | export → reporting set (the certification's code) |
| `Dockerfile`, `docker-compose.yml`, `.env.example` | container build and stack |

## The session, page by page

| oTree round | pages |
|---|---|
| 1 (before the task) | Consent, Instructions, Quiz (repeat until right) |
| 1–6 | Order (one of two goods) → Clearing (120 clearing prices over 9 s) → Rate (three fairness items, one entitlement item) |
| 7–10 | Market (price history, first forecast) → Evidence (ten trial closes, or a source's forecast; second forecast) → Bet (YES, NO or pass at the posted price) → Recall |
| 10 (after the task) | Closing, Results (the markets settle) |

The Clearing page shows, in one view: the price of the ordered good against the cap, with a
dot on the line and a coloured tick in the strip underneath for every filled order; the
running counts of filled orders, own and trader, as figures and as two curves on a fixed
axis; baskets completed. The points total moves only when the round has cleared.

- The server decides every sequence. A reload replays a reveal; it cannot replay an order.
- A page holds only its own round and only the ordered good's prices. A market's evidence
  reaches the browser after the first forecast is stored, and its bet price after the second.
  How a market settles reaches the browser on the Results page.
- The two arms get the same pages, styles and scripts. Only the board's numbers differ.
- A participant takes the next free slot of the schedule file on leaving the quiz. Slots
  2j and 2j+1 are the two members of pair j. An arrival without a free slot sees a
  "session full" page and does not start.

## Colours and marks

One fixed light theme (the display is part of the stimulus). Goods carry colour: Square
`#2a78d6`, Triangle `#eb6834`. People are drawn in neutral tones: the trader on the board in
slate `#3f4756`, a forecast source in ink. YES `#1f9d55` and NO `#c93a9a` appear on the bet
buttons and the settled markets only, always with the word; the pair is green against
magenta so that it stays apart for people who do not tell red from green. Nothing on a
procurement screen is green or red. No name, logo or layout of a real market is used.

## Run it

```
pip install -r requirements.txt
otree devserver 8000                       # demo page at http://localhost:8000
otree test market_bots_random 8            # bots; add --export=DIR for the data
python tools/browser_run.py --shots DIR    # full sessions in Chromium (server must be up)
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
| browser: no error, no outside request, no leak, equal pages, reload, back, re-post, charts in view on phones | `pytest experiment/analysis/tests/test_market_browser_I043.py` |
| front end | `cd experiment/frontend && npm run check` |

## Not done here

- No page time-outs and no refill of slots left by dropouts.
- English only. Keyboard use works by construction; no screen-reader test. The charts carry
  no text alternative beyond the figures printed next to them.
- No check that people read a price curve as a record of fills.
- The official Docker base images could not be pulled where this was built; see the freezes.
