# diss_market: the oTree build of the yoked ten-repetition design

Status (KGi-DISS-I042): built and verified with bots and in a browser. Nothing has been run
on people. Every sentence a participant reads is a draft; ethics, payment and the board's
description are author decisions (`diss_market/copy_en.py`, `settings.py`).

Design: `YOKED_DESIGN.md`. Contract and scorecard: `../freezes/00_freeze_I042.yaml`.

## What is where

| path | what |
|---|---|
| `diss_market/__init__.py` | the oTree app: pages, data model, export, bots |
| `diss_market/engine.py` | everything shown, computed from the schedule (no oTree import) |
| `diss_market/copy_en.py` | all wording (DRAFT) |
| `diss_market/*.html` | page templates |
| `frontend/` | TypeScript and CSS sources, unit tests, build script |
| `_static/diss_market/` | the built bundle and fonts (tracked; rebuilt by `npm run build`) |
| `tools/yoked_schedules.py` | pre-drawn schedules (`--format 2` for the app) |
| `tools/make_board_pool.py` | pool of real earlier records for the trader board |
| `tools/browser_run.py` | plays whole sessions in Chromium and checks them |
| `analysis/yoked_from_export.py` | export → reporting set (the certification's code) |
| `Dockerfile`, `docker-compose.yml`, `.env.example` | container build and stack |

## The session, page by page

| oTree round | pages |
|---|---|
| 1 (before the task) | Consent, Instructions, Quiz (repeat until right) |
| 1–6 | Choose (one of two tickets) → Settle (120 settlements revealed over 9 s, own ticket and board in step, then regrouped) → Rate (three fairness items, one entitlement item) |
| 7–10 | ProbePre (forecast) → ProbePost (ten settlements revealed, forecast again) → ProbeRecall |
| 10 (after the task) | Closing, Results |

- The server decides every sequence. A reload replays a reveal; it cannot replay a choice.
- A page holds only its own round. A probe record reaches the browser after the first
  forecast is stored.
- The two arms get the same pages, styles and scripts. Only the board's numbers differ.
- A participant takes the next free slot of the schedule file on leaving the quiz. Slots
  2j and 2j+1 are the two members of pair j. An arrival without a free slot sees a
  "session full" page and does not start.

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

| name | board | use |
|---|---|---|
| `market_seed` | none | seed wave: its records feed the pool |
| `market_pilot` | pool | board replays real earlier records |
| `market_dev` | computer-generated | development only; refused for people in production |
| `market_bots_*`, `market_e2e` | | bots and browser tests |

Keys: `schedule_path`, `board_source`, `pool_path`, `reveal_ms`, `probe_reveal_ms`,
`recall_check`, `prize_points`, `points_to_currency`, `completion_url`,
`min_window_width`, `first_slot`, `last_slot`. Two sessions on one schedule file need
disjoint slot ranges.

## From a seed wave to a pilot with a truthful board

1. Draw schedules: `python tools/yoked_schedules.py --pairs N --seed S --format 2 --out schedules/x.json`
   (run from the repository root).
2. Run a seed wave with `market_seed`. Participants see no board.
3. Build the pool: `python tools/make_board_pool.py seed_export.csv --out pools/pool.json`.
   It prints how many records each round has and how many fit the HIGH band.
4. Run the pilot with `market_pilot`, `MARKET_SCHEDULE` and `MARKET_POOL` pointing at the
   files. HIGH shows a rich-round record with a rate in [.65, .80]; LOW shows a record of
   the same round nearest to the participant's own count.

Bot records are refused by the pool tool unless `--allow-bots` is given; such a pool is
marked as a placeholder and is refused for people in production.

## Data

Custom export (`/api/export_app_custom?app=diss_market`, or the admin's export page):

- one `repetition` row per participant and repetition: ticket, wins, the settlement record,
  the board's record and source, the four ratings with their start positions, the two
  forecasts, timings, reveal timing (planned, measured, time the tab was hidden);
- one `participant` row: the probe statistic `T`, the paid forecast, points, closing answers,
  window size and reduced-motion setting.

`python analysis/yoked_from_export.py export.csv --config market_pilot` scores the
reporting set.

## What was checked, and how to repeat it

| check | command |
|---|---|
| engine against the simulation's rule; schedule format | `pytest experiment/analysis/tests/test_market_engine_I042.py` |
| bots: stored data = schedule; 72 pairs of gate bots; seed wave → pool → board | `pytest experiment/analysis/tests/test_market_app_I042.py` |
| browser: no error, no outside request, no leak, equal pages, reload, back, re-post | `pytest experiment/analysis/tests/test_market_browser_I042.py` |
| front end | `cd experiment/frontend && npm run check` |

## Not done here

- No page time-outs and no refill of slots left by dropouts.
- English only. Keyboard use works by construction; no screen-reader test.
- The official Docker base images could not be pulled where this was built; see the freeze.
