# Inverse calibration from the paper's ABM (post-I032, 2026-11-09)

This is an exploratory record. Nothing frozen, built or written in the
manuscript was changed. Each script was committed with its questions before it
ran:
- `engine` mode `invcal`, seeds 61000+, output `records/invcal.csv`;
- `experiment/analysis/explore_inverse_calibration_I032pc.py` (part a, seed 132990);
- `explore_inverse_calibration_b_I032pc.py` (part b, 133000). Written after
  reading part a.
- `explore_inverse_calibration_c_I032pc.py` (part c, 133010). Written after
  reading part b.

Parts b and c are post hoc in form. They need an I033 freeze, fresh seeds and
the full M1–M6 battery before they can enter the preregistration.

## Direction (author)

The aim is to calibrate from what the theory says we should see, not from a
generic design-basis effect. I032 fixed θ = .592 from a prior. It then shrank
the frozen gate to that value through a slider gain a ≈ .058. Every dynamic
signature therefore shrank about 17-fold. The paper's prediction figure puts the
HIGH P2 drop at 45 points; at a = .058 it is about 2.6.

Here the theory's own parameters are weakened instead, down to the edge where
the paper's ABM headline still holds. The gain a is kept as a separate
nuisance that the pilot can measure.

## What the paper says we should see (prediction figure, slider = 100·L)

- P2 drop: HIGH 45 vs LOW 23 (latent θ .90).
- HIGH × MODERATE: flat after P2 (end of P2 20.5 → late P3 11.7).
- R3 recovers 79 → 89.
- HIGH × FULL crawls back 22 → 55.

## Theory edges (ABM confirmatory cell: A0 .8, λ .7, ρ .002, χ .4; 200 runs/cell)

| speed s (νF = .05s, νR = .0125s) | 2 | 1.5 | 1.25 | 1 | .8 | .65 | ≤ .5 |
|---|---|---|---|---|---|---|---|
| P(defensive wrong consensus) | 1.00 | 1.00 | .985 | .82 | .21 | .005 | 0 |

| νR/νF (s = 1) | .25 | .26 | .27 | .28 | .29 | .30 | .31 |
|---|---|---|---|---|---|---|---|
| P_dw | .855 | .77 | .65 | .58 | .54 | .315 | .26 |

The interpolated edges are:
- s* = .895 (speed);
- ratio* = .292 (sensitivity);
- χ_min = (A*(p) − p)/(μ_ref − p) = .322 at ratio .25 and .363 at ratio* (anchoring, analytic).

χ does not enter P_dw at ρ = .002, because entry rides on A0. Its edge
therefore comes from the relative-deprivation permanence frontier.

The points evaluated are:
- P0: the paper's point;
- P1: the ABM's χ (.4);
- P2: the ratio edge;
- P3: the speed edge;
- P4: the anchoring edge;
- P5: the joint corner, which lies outside the region because both ABM edges
  hold at once.

**Flag for the author (manuscript not edited).** The confirmatory trap is a
fast-gate result. Slowing νF and νR together by 20% drops P_dw from .82 to
.21, and by 35% to ≈ 0. The paper states the ratio knife-edge but not this
speed edge. It does not contradict a stated prediction, so the main text was
not patched.

## Results at the edges

All results use the task generator, M2 measurement and the reference held
fixed across restoration (P3 regime = arm).

**H1a.**
- Power is ≥ .9 at N = 320/arm at every inside point once a ≥ .1.
- At a ≥ .35, N_.9 ranges 41–104/arm; at a = .25 it ranges 47–115.
- At a = .058 the gate's θ is .55–.60, which is where the old design basis
  sits.
- R3 also passes H1a at full gain (θ .62–.73). H1a does not separate the gate
  from R3.

**Latent restoration (HIGH × MODERATE, reference fixed): fraction = rec_end / depth.**

The depth is P1 minus end-of-P2, i.e. how deep the collapse went.

| point | gate | R3 |
|---|---|---|
| P0 paper | −.118 (−8.6 / 73.1) | +.560 |
| P1 χ .4 | −.019 | +.614 |
| P2 ratio edge | +.169 (+8.5 / 50.0) | +.614 |
| P3 speed edge | −.031 | +.614 |
| P4 anchor edge | +.065 | +.633 |
| P5 corner | +.219 | +.623 |

- The absolute recovery stops separating at the ratio edge (gate +8.5, R3 +9).
  That is why H1b-SIe fails there (power .02 at a = 1). SIe normalises by the
  P2-mean drop, which understates the gate's unfinished collapse.
- The between-arm raw recovery contrast fails at the anchoring edge (.01).
- The fraction separates everywhere inside the region: gate ≤ .17, R3 ≥ .56.
- κ = midpoint = **.364**. The rule was fixed before part b's power run, after
  part a's latent numbers had been read.

**H1b forms, power at n = 213/arm, α .005.** The table gives the smallest
gain a at which power is ≥ .9 at all inside points (P0–P4).

| form | a for ≥ .9 everywhere | P5 at a = .35 |
|---|---|---|
| SId, conditioned on above-median depth (part b) | .35 | .76 |
| SId-S, split-sample conditioning (part c) | .25 | .98 |
| SId-BA, between arms on c (part c) | .25 | .74 |

- **SId-S** selects on P1 ratings 0:15 minus P2 ratings 50:56. It tests on
  c = (late − end) − κ·(P1 ratings 15:30 − end), with end = P2 ratings 56:60.
  Selection and test use disjoint ratings.
- **Conditioning on the same ratings costs power through regression to the
  mean.** Depth and recovery share the end-of-P2 ratings, so selecting high
  measured depth selects favourable noise.
- **SId-BA** is a one-sided WMW comparing c in HIGH × MOD against LOW × MOD.

**False positives (part c), SId-S | SId-BA, at a = 1, .35 and .15.**

| rival | a = 1 | a = .35 | a = .15 |
|---|---|---|---|
| R3 (χ .6 or .4) | 0 \| 0 | 0 \| .003 | 0 \| .007 |
| no-gate composite R3 + R4 (AD4 share) | 0 \| ≤ .003 | .025–.040 \| ≤ .007 | .16 \| ≤ .013 |
| R3-int, η = .01 (time constant ~100 trials) | ≤ .010 \| .26–.69 | ≤ .022 \| .07–.29 | ≤ .005 \| ≤ .013 |
| R3-int, η = .005 (~200 trials) | .78–.99 \| .46–.96 | .15–.33 \| .11–.16 | ≤ .055 \| ≤ .05 |

Reading:
- SId-S is R3-proof.
- SId-BA is composite-proof by randomisation.
- The conjunction of the two (an intersection–union test) keeps power ≥ ~.9
  at a ≥ .25 at every inside point. It excludes R3, the composite, and
  integrators with a time constant of about 100 trials.
- **It does not exclude a very slow integrating-utility rival (time constant
  ≈ 200 trials) at high gain.** That rival has to be separated by kinetics
  (H4: graded erosion vs capped repair) or by the A* threshold (H3), not by
  recovery magnitudes. This is the remaining identification frontier and an
  I033 item.

## Design consequences (proposals; author decisions)

1. **Design basis.** Use the theory edge (P1–P4) at a pilot-verified gain.
   θ = .592 stays as a reported external-prior row.
   - The theory supplies the effect and the pilot supplies the gain. This is
     the division of labour the paper's Discussion already states.
   - SESOI framing: Lakens, Scheel & Isager 2018. Plausible effects from
     external information, with Type S/M errors: Gelman & Carlin 2014.
2. **Pilot go/no-go in measured units.**
   - HIGH × MOD mean depth (P1 − last-4-P2) must be ≥ about 12 slider points,
     i.e. a ≳ .25 at a latent edge depth of about 50. The threshold is to be
     certified in I033.
   - If it fails, either the slider is too insensitive or the human gate is
     weaker than the paper's headline requires. Either way, the confirmatory
     H1b cannot run as designed.
3. **H1b = SId-S ∧ SId-BA**, with κ = .364 from the theory-region rule.
   - The reference is held fixed in P3.
   - The FULL arm remains the positive control.
4. **N.** H1a no longer binds (N_.9 ≤ 115/arm at a ≥ .25). The binding
   constraint is the H1b cells; n_min is an I033 computation, and the total N
   likely falls.
5. **Board.** χ_min falls as the displayed level rises (.371 at .60, .322 at
   .65, .286 at .70). The replay band should sit at ≥ .60.
6. **Dose module.** Still drop.

## I033 items

1. Freeze SId-S, SId-BA and κ, and certify on fresh seeds over M1–M6, with
   the AR(1) anchoring variant.
2. Compute n_min.
3. Certify the pilot gain rule.
4. Certify H4/H3 kinetics against R3-int (η ≤ .005).
5. Run an ABM check of P_dw over (s, ratio) at other cells. The edges here are
   specific to the confirmatory cell.
