# The oTree build of the yoked design (KGi-DISS-I042, 2026-11-16)

Nothing here has been run on people. Bot data are for checking the pipeline only. Every
sentence a participant reads is a draft.

- **Freeze.** `freezes/00_freeze_I042.yaml` was pushed before any code. The scorecard is
  verbatim in it.
- **Operator's guide.** `experiment/MARKET_APP.md`.

## What was built

| piece | where |
|---|---|
| oTree app, one oTree round per repetition | `experiment/diss_market/` |
| task engine, pure Python | `experiment/diss_market/engine.py` |
| front end: TypeScript (strict), plain CSS, bundled fonts | `experiment/frontend/` → `experiment/_static/diss_market/` |
| schedule format 2 | `experiment/tools/yoked_schedules.py --format 2` |
| pool of real earlier records for the board | `experiment/tools/make_board_pool.py` |
| export → reporting set | `experiment/analysis/yoked_from_export.py` |
| container image and stack with Postgres | `experiment/Dockerfile`, `docker-compose.yml`, `.env.example` |
| browser run (Chromium) | `experiment/tools/browser_run.py` |

**How the screen works.** A round's 120 settlements appear one by one over 9 seconds,
the participant's ticket and the trader board in step, with a running count. They then
regroup, paid first, so each panel reads as a proportion. Paid and not paid differ by
shape as well as colour. A probe record appears settlement by settlement before the
second forecast can be given. The theme is fixed for everyone.

## What was verified

| gate | result |
|---|---|
| engine = the simulation's rule | PASS. 200 schedules: own record, HIGH board and LOW board equal an independent implementation, settlement by settlement |
| the gate kernel played on the engine | legitimacy at probe time .110 / .869 (certification .109 / .869); same tickets in all five rounds .126 (.13) |
| bots | PASS. Stored data equal the schedule for every participant; ten arrivals for eight slots: two do not start |
| export → analysis | PASS. `T` from the export equals `T` stored, 144 of 144. At 72 pairs of gate bots the confirmatory pair comes out |
| nothing shown early | PASS on the frozen check; one defect found by eye and fixed (below) |
| front end | PASS. No console error, no failed request, no request to another host; desktop, phone, reduced motion |
| equal display | PASS. A pair making the same choices gets identical pages apart from the board's numbers |
| reload, back button, second submission | nothing stored changes |
| reveal timing | 9,008 ms for 9,000 planned; a hidden tab stops the reveal |
| Docker | PARTIAL. See below |

## Found while building

1. **The points total gave a round away.** The top bar showed the total including the
   round's wins while the round was still being revealed. Seen on a frame of the screen
   recording, not by any test. Fixed; the browser run now checks it.
2. **On a phone the board fell below the fold** during the reveal. The two panels now stay
   side by side. Whether phones are admitted at all is an author decision
   (`min_window_width`).
3. **The certified rating noise assumes three fairness items.** My recap said two
   sliders. The app shows three fairness items and one entitlement item. The entitlement
   test was certified at the three-item noise, which one item does not deliver.
4. **The earlier project could not run from a clone.** `.gitignore` excluded `_static`,
   and oTree 6 stops without it.
5. **A bot run in the project directory mixes with a development server's data.** My
   first 72-pair score counted 80 pairs. The tests now run in a fresh copy.
6. **Schedule files of I041 could not rebuild the LOW board.** Format 2 stores the draw.

## Docker: what was and was not run

Docker Hub and ghcr.io are refused where this was built. The official images
(`node:22-slim`, `python:3.13-slim`, `postgres:16-alpine`) were never pulled.

Run instead, on stand-in images made from the build machine's own Ubuntu 24.04 files
(Python 3.13.18 with no package installed, Node 22, Postgres 16):

- the Dockerfile builds unchanged: `npm ci`, type check, unit tests, bundle; `pip install`;
- the container runs as a non-root user in production mode and reports healthy;
- under `docker compose` with Postgres: both services healthy, the browser run passes,
  the data survive a restart of the web container;
- with the study access level, the demo page asks for the login and the export without
  its key is refused.

**Not verified: anything specific to the official images.** Build once on a machine with
registry access before relying on it.

## One expectation failed

I expected ψ̂ from 72 pairs of gate bots within .05 of the certification's .123. It came
out at .025. The band ignored sampling error: the standard error of ψ̂ at 72 pairs is
about .09. On 3,000 pairs the same kernel on the app's engine gives .136.

## Decisions for the author

1. **Board for the pilot.** A seed wave without a board, then replay of its records
   (built), or another truthful description.
2. **Wording.** Consent, the three fairness items, the entitlement item, the probe
   questions, the board's description. All in `diss_market/copy_en.py`.
3. **Probe tickets.** The draft pays a favourable ticket at .9 and an unfavourable one at
   .1 and shows ten real settlements chosen to hold nine or one wins. One of the eight
   forecasts is paid by a binarized scoring rule. The "other" record is described as "not
   yours", not as another person's.
4. **Reveal speed** (9 s). It bears on how people integrate a summary, the first open
   human quantity. It can be a pilot factor.
5. **Devices, payment rates, recall check, page time-outs.**

## Not done

- No page time-outs; no refill of slots left by dropouts.
- English only; no screen-reader test.
- The association by arm under other rating shapes; the pilot specification.
