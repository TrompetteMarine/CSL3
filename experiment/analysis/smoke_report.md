# Task v3 analysis pipeline — smoke report

**BOT DATA — pipeline validation only. Nothing here is evidence about humans.**

Input: `botdata/combined_custom.csv` — 16 participants after exclusions (0 excluded).

Exclusion log: 22qvvwnz: P1-accuracy 0.440 < chance+2SE (bot data: flagged only); 65ka5dk3: P1-accuracy 0.527 < chance+2SE (bot data: flagged only); jvtnupvk: P1-accuracy 0.527 < chance+2SE (bot data: flagged only); mzuqr2tx: P1-accuracy 0.487 < chance+2SE (bot data: flagged only)

## H1 (primary) — P2 fairness drop HIGH vs LOW
mean drop HIGH = 30.0, LOW = 44.8; Welch t = -0.94, p = 0.3799, d = -0.52, n = (12, 4). (alpha = 0.005, two-sided)

## H2 — recovery-midpoint lag (rating − choice), HIGH vs LOW
mean lag HIGH = 39 trials, LOW = 70; Welch t = -0.76, p = 0.4848, d = -0.44. Midpoints censored at 450 count as no recovery.

## H3 — regime × restoration interaction: **incomplete 2×2 crossing in this dataset (3/4 cells)** — interaction not estimable; runs on the full design.

## H4 — increment asymmetry (Δfairness ~ entitlement shortfall)
b(shortfall) = -8.35, p = 0.005297 (MixedLM, random intercept). DISS predicts graded-down/constant-up; LR-symmetric updating predicts symmetry.

## H5 — shared-failure cell absent from this dataset (pilot-gated; runs only when the EQUAL-misery cell is collected).

## Moderator — slider-adaptation speed × late-P3 fairness (HIGH)
r = 0.38, p = 0.2269; slow adapters (small coefficient) are predicted to show durable grievance (lower late-P3 fairness). n = 12.

---
Participant-level table: 16 rows × 20 cols; written alongside the report.
