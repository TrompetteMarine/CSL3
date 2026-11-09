# Task v3 (market skin) analysis pipeline v2 — report

**BOT DATA — pipeline validation only. Nothing here is evidence about humans.**

Input: `botexport2/diss_bandit_custom.csv` — 24 participants after exclusions (0 excluded). Suspicion hook: OFF (pre-pilot).

## H1a (confirmatory) — P2 fairness drop, HIGH vs LOW
one-sided WMW z = 0.31 -> no rejection at alpha = 0.005; theta-hat = 0.539, Hodges-Lehmann shift = 2.5 pts; studentized permutation Welch co-report: t = 0.30, p = 0.406 (no rejection). n = (8, 16).

## H1b — gatekept: not tested (H1a did not reject).

## H2 — recovery-midpoint lag (rating − choice), HIGH vs LOW
mean lag HIGH = 38 trials, LOW = 71; Welch t = -1.06, p = 0.3111, d = -0.48. Midpoints censored at 450 count as no recovery.

## H3 — P3 rating slope, regime × restoration interaction
interaction C(p2_regime)[T.LOW]:C(restoration)[T.MODERATE]: b = 11.87, p = 0.6289 (OLS; mixed model on human data).

## H4 — increment asymmetry (Δfairness ~ entitlement shortfall)
b(shortfall) = -14.66, p = 0 (MixedLM, random intercept). DISS predicts graded-down/constant-up.

## H5 — shared-failure cell absent from this dataset (pilot-gated).

## Dose module — dose cells absent from this dataset.

## Framing probe — framing cell absent from this dataset.

## Moderator — slider-adaptation speed × late-P3 fairness (HIGH)
r = 0.88, p = 0.003702; n = 8.

---
Participant-level table: 24 rows × 23 cols; written alongside the report.
