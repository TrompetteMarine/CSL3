# diss-otree — task v3 instrument, market skin (I032 + audit)

oTree 6.0.15 implementation of the preregistered task (reference-dependent
delegitimation: entitlement, legitimacy and the evidential authority of
feedback). Design: `DESIGN.md`; task specification: `TASK_SPEC.md`; reasoning:
`TASK_INFERENCE.md`; lab-to-field priors: `PRIORS.md`; technique decisions:
`TECHNIQUES.md`; bias inventory: `BIAS_INVENTORY.md`.

- `diss_bandit/` — the app: two free tickets ↔ two arms, 450 rounds in three
  invisible phases, seeded settlement, fixed disclosed quotes, truthful trader
  board (trailing-15 win rate of a real prior participant), fairness and
  entitlement sliders (step 5, randomized starts), comprehension quiz,
  next-round forecasts (one paid), WTP re-draw probes, funnel, custom export.
  The live engine is reload-safe; production mode refuses the placeholder pool
  and the dev secret.
- `settings.py` — `main_confirmatory` (balanced blocks of 6), per-cell configs,
  dose cells (suspended), framing probe, pilot arms (sparse; bandit skin),
  `pool_rich` (rich-rule pool-source sessions), bot configs incl. `bots_refresh`.
- `tools/make_pool_from_pilot.py` — builds the truthful peer pool from human
  exports (schedule, per-block rates, variance terciles; feasibility report).
- `analysis/pipeline.py` — preregistered analysis (exclusions incl. zero-movement
  screen; H1a WMW; gatekept H1b in frozen and candidate forms; H2–H5; modules).
  Run: `python analysis/pipeline.py <custom_export.csv> <report.md>`.
- `analysis/tests/` — pytest suite (generator port vs scalar reference, statistics
  vs references and null levels, pipeline end-to-end, screens).
- `botdata/` — I006-era bot exports (old export format, no config column; kept
  for history only).

Validate: `otree test bots_refresh 12 --export <dir>`, then run the pipeline on
`<dir>/diss_bandit_custom.csv`; and `python -m pytest -q analysis/tests` from the
repo root. Bot data is pipeline validation only, never evidence about humans.

Not yet built (Docker/oTree phase): Prolific integration (participant label,
completion redirect), dependency pinning file, inactivity and timeout handling,
deployment manifests. See `records/98_audit_I032.md`.
