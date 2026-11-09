# Minimising rounds and humans by simulation (I033 AD-S1/AD-S2, 2026-11-09)

The protocol was frozen before running: `freezes/00_freeze_I033.yaml`,
addenda AD-S1 (before stage 1) and AD-S2 (stage-1 scorecard plus the
amended stage-2 selection, written before stage 2).

Code:
- `experiment/analysis/design_generator.py`: the frozen kernels with an
  explicit task geometry. It is bit-identical to `market_generator` at
  150/150/150 (`tests/test_design_generator.py`, 23 tests).
- `design_search_I033.py` (stage 1, seed 133400).
- `design_search_I033_stage2.py` (seed 133500).

Records:
- `records/design_search_I033_stage1{.csv,.txt,_curves.csv}`.
- `records/design_search_I033_stage2.txt`. After the run, numpy scalar reprs
  `np.float64(x)` were replaced by `x`. This is formatting only; a byte-level
  re-run must apply the same substitution.
- Neither stage has been re-run for bit-identity yet (about 1 h compute).

## What humans must supply, and what simulation sets

Human-necessary:
1. whether the gate exists in people (H1a, H1b);
2. the sliders' gain and noise;
3. whether human ratings move up at all (a small FULL arm). Without it, a
   "ratings only go down" habit would mimic the moderate-restoration flatline;
4. the human rigidity (ρ) distribution;
5. new from stage 2: the initial entitlement A0.

Everything else is set by simulation: effect sizes, the theory edges, κ, phase
lengths, odds, rating cadence, N, and the peer level.

Minimal confirmatory cells are HIGH × MODERATE and LOW × MODERATE, with the
board held at the arm in P3, plus a small HIGH × FULL. The dose module and the
framing probe are not needed for H1. The between-arm H1b leg is
arm-symmetric for R4 by construction.

## Stage 1: 24 short geometries + the 450-round baseline

The grid crossed P1 40/60, P2 60/90/120, P3 45/75, and P2 odds .30/.15 vs
.25/.10. Power was computed at every inside theory point (P0–P4), under M2.
n is per cell, after exclusions.

| design | rounds | min | n_min a=.25 | n_min a=.5 | n_FULL a=.5 | total N a=.5 |
|---|---|---|---|---|---|---|
| 150/150/150 (baseline) | 450 | 29.2 | 222 | 109 | 20 | 237 |
| 60/90/75, P2 .25/.10 | 225 | 17.4 | > 320 | 146 | 26 | 318 |
| 40/90/75, P2 .25/.10 | 205 | 16.3 | > 320 | 187 | 24 | 397 |
| 60/120/75, P2 .25/.10 | 255 | 19.0 | > 320 | 200 | 20 | 420 |
| 40/120/75, P2 .25/.10 | 235 | 17.9 | > 320 | 203 | 21 | 427 |
| any design with P2 = 60 | 145–195 | 13–16 | > 320 | > 320 | — | — |

Scorecard (verbatim from AD-S2):
- **ES1 PASS:** P2 = 60 never works.
- **ES2 PASS:** harsher P2 odds help in every pair.
- **ES3 FAIL:** no design of 15 minutes or less is adequate at a = .25 with
  ≤ 320 per cell. The closest, 60/90/75 at .25/.10, reaches .83 for the
  conjunction at the ratio edge and .90 for H1a at the anchoring edge at
  n = 320.
- **ES4 MIXED:** the FULL arm needs 20 at 450 rounds and 50–77 in short designs
  at a = .25. With P3 = 45 it never reaches .90 at a = .25.

## Stage 2: robustness of the three best short designs (≤ 18 min, a = .5) vs the baseline

Each design was tested at its own n_min (a = .5).

| check | 60/90/75 (n 146) | 40/90/75 (n 187) | 40/120/75 (n 204) | baseline (n 109) |
|---|---|---|---|---|
| false positives vs R3, composite (any a) | 0 | 0 | 0 | 0 |
| false positives vs R3-int η .01, a = .5 / 1 | .035 / .29 | .05 / .335 | .065 / .195 | 0 / 0 |
| worst shape M5, a = .5: H1a / conjunction, worst point | .64 / .80 | .77 / .82 | .98 / .90 | .94 / .81 |
| A0 = .4: conjunction at the ratio edge | .01 | .00 | .00 | .01 |
| A0 = .6: H1a / conjunction, worst point | .49 / .67 | .69 / .82 | .88 / .54 | .55 / .22 |
| a = .25 at n = 320: worst H1a / conjunction | .85 / .86 | .81 / .75 | .99 / .68 | 1.00 / .99 |
| ρ classification AUC (entitlement slider, a = .25) | .686 | .675 | .691 | .714 |

Rating every 3 rounds instead of every 5 (60/90/75, which adds 2.2 minutes)
moves n_min at a = .5 from 146 to 140. At a = .25 it is still > 320 (.88 at
n = 320). Denser measurement does not substitute for gain.

## What follows

1. **The session-length floor comes from the theory's clocks, not from
   convenience.** Aspiration adapts slowly (rigid subjects have a time constant
   of about 500 rounds). P2 therefore needs at least ~90 rounds to separate
   HIGH from LOW. The restoration signature needs P3 of at least ~75 rounds.
   The shortest adequate session is about 205–225 rounds (16–17 min). Below
   that, nothing works at any N up to 320 per cell.
2. **Shortening costs specificity and robustness.** With P3 = 75 the
   moderately slow integrating rival (time constant about 100 rounds) leaks
   (.29–.34 false positives at full gain); at 450 rounds it does not. Short
   designs are also more fragile to gain heterogeneity (M5).
3. **Three human parameters decide feasibility: slider gain a, initial
   entitlement A0, and the ρ distribution.**
   - At A0 = .4 the conjunction fails at the ratio edge in every design,
     including 450 rounds. With low initial entitlement, a gate at the
     sensitivity edge does not delegitimate enough to separate from R3.
   - At A0 = .6, H1a weakens because both arms delegitimate.
   - The rigidity output is weak at a = .25 in every design (AUC ≤ .71).
4. **Proposal: a calibration pilot plus a frozen simulation lookup.**
   - The pilot measures a (HIGH × MOD depth in points), A0 (first entitlement
     ratings), the fast/slow ρ mass, never-movers and exclusions.
   - A pre-registered table computed by the generator maps those numbers to
     the geometry and n. If the design is not changed, pilot participants count
     toward the main sample: an internal pilot that re-estimates only nuisance
     parameters (Wittes & Brittain 1990).
   - If the pilot puts the human parameters outside the adequate region (low
     A0, or a < .25 with short sessions), no main study runs as designed.
5. **Human time.** The current plan is about 1,120 recruited at 29 min (about
   32,000 person-minutes). The 17-minute design at a ≥ .5 needs about 320
   post-exclusion (about 360 recruited, about 6,300 person-minutes). The
   450-round design at a = .25 needs about 464 post-exclusion. That is roughly a
   5-fold saving if the gain is at least .5.

## Next (needs a freeze addendum)

- Build the pilot lookup over the grid (a, A0, ρ mass).
- Compute the precision of the calibration pilot as a function of its n.
- Test whether P1 odds or the peer level can make the design robust to A0.
- Re-run stages 1–2 for bit-identity.
