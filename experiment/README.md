# diss-otree — task v3 instrument (KGi-DISS-I006)

oTree 6 implementation of the preregistration draft's task v3 (dissonance-gated
social learning: entitlement, legitimacy, and the evidential authority of feedback).

- `diss_bandit/` — the app (450-trial two-armed bandit, live pages, yoked
  no-deception peer display, fairness + entitlement sliders, custom export).
- `settings.py` — 4 experimental cells (p2_regime × restoration) + bot configs.
- `analysis/pipeline.py` — frozen H1–H5 + moderator pipeline; run:
  `python analysis/pipeline.py <custom_export.csv> <report.md>`
- `DESIGN.md` — design & ethics-readiness note (author review before OSF).
- `00_freeze_I006.yaml` lives in the paper bundle (kgi-diss-paper/).

Validate: `otree test bots_diss_HIGH_FULL --export <dir>` then run the pipeline on
`<dir>/diss_bandit_custom.csv`. Bot data is pipeline validation only.
