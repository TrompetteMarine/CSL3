# Bias inventory → design counters (I032)

Every human bias that threatens identification of the confirmatory contrast
(H1a) or the gate dissociation (H1b), mapped to the counter that handles it.
Each entry is one of four kinds:

- **COUNTER (in design)** — an element that predates I032;
- **COUNTER (added I032)** — introduced by B or C this iteration;
- **ABSORBED** — represented by the certified measurement battery (M1–M6 +
  anchoring variant) or by the S7 addendum, with the representability check
  stated. Nothing is called absorbed unless the battery can actually generate it;
- **ACCEPTED, SCOPED** — not countered; the claim is narrowed accordingly.

One principle organizes the table. Randomized assignment protects the *level*
of the between-arm test against any bias that is distributed identically across
HIGH and LOW: under H0 the drops stay exchangeable whatever the bias does. Such
**symmetric** biases can cost power but cannot create a false positive.
**Asymmetric** biases, which act differently on HIGH and LOW, threaten the level
directly, and at α = .005 the tolerance is very tight. The S7 addendum measures
that tolerance once, and the number applies to every asymmetric threat below.

## The S7 tolerance (records/power_free_s7.csv, 2,000 reps per cell)

Null cells, S3 base, N = 320/arm. A fraction q of the HIGH arm only carries a
drop inflation of s points; a blind probe removes each contaminated subject
with probability π. Residual load = q·s·(1−π) points of mean drop. The
level-acceptance threshold is α + 2 MC SE = .0082.

| residual load (pts) | realized one-sided WMW level (cells) |
|---|---|
| ≤ 0.20 | .0050–.0085 (within MC error of .005, one cell at .0085) |
| 0.25 | .0050, .0065, .0135 |
| 0.50 | .0090–.0160 |
| 1.00 | .0210–.0350 |
| 2.00 | .1135 |
| 3.00 | .2710 |

Portable statement. In S3 units the design-basis shift is τ = 7.22 pts, so
residual asymmetric contamination must stay below **~3% of the design effect**
(load ≲ 0.2) to hold the level at .005. At ~7% the level is roughly triple
nominal; at ~14% it is 4–7×. The symmetric-suspicion power cell
(q = .10 both arms, s = 10, π = .5) keeps power at .924, so symmetric
contamination is cheap. The asymmetric kind is the one that matters.

## Inventory

| # | Bias | Threat to | Symmetric? | Entry | Counter / evidence |
|---|---|---|---|---|---|
| 1 | Experimenter demand | H1a level | Instruction-borne demand: symmetric. Arm-specific demand needs the hypothesis inferred | COUNTER (in design) + COUNTER (added I032) | Identical instructions in both arms; non-deceptive obfuscation (Zizzo: demand matters when correlated with the true hypothesis). DQHR's bounds under *explicit* demand average ~0.13 SD; implicit, arm-specific demand plausibly far smaller but **subject to the S7 tolerance**. Added: sensitivity re-run of H1a excluding participants whose blind-coded purpose guess names the reference hypothesis |
| 2 | Suspicion of the display despite no deception | H1a level | **Asymmetric** (the HIGH board is the one that looks too good) | ABSORBED by S7 + COUNTER | S7 quantifies the tolerance above. The pilot believability rule is **amended** (forced by S7): estimate the differential load (q̂_H − q̂_L)·ŝ·(1 − π̂) from the pilot; if its upper 80% bound exceeds 0.2 pts (3% of the design effect), tighten the probe or revise the display before filing. The overall 20% trigger stays. Comprehension quiz on provenance added (C#7) |
| 3 | Windfall / house-money wealth effects | power | symmetric (announced, non-contingent, identical schedule in both arms) | ACCEPTED, SCOPED | Level protected by randomization. House-funded tickets keep the gains domain (Thaler–Johnson). Windfalls are non-evidential in the certified generator (app semantics, D5). House money may raise WTP *levels* from the separate allowance, but equally in both arms |
| 4 | Slider anchoring to the default | power; level only if defaults differ by arm (they do not) | symmetric | COUNTER (added I032) + ABSORBED | Randomized starts (C#10, ISR study: 101-point sliders anchor to defaults, midpoint included), logged per rating. AR(1) reporting variant certified: gate H1a power .944 (run 2). Step-5 sliders match the certified round-to-5 model |
| 5 | Never-movers under randomized starts | power (noise) | symmetric | COUNTER (added I032) | **Found in this audit.** Randomized starts defeat the frozen zero-variance screen (a never-mover's reports have variance ~968). Screen translated to zero movement against logged starts; unit-tested (never-mover excluded, partial mover kept). Partial-mover threshold reserved for the pilot |
| 6 | Scale use: individual gain differences, floors/ceilings, rounding | power | symmetric | ABSORBED (in part) + ACCEPTED, SCOPED | Represented: linear per-subject gain heterogeneity (M4 heavy-tailed, M5 skewed), boundary compression (clip in every shape), rounding (round-to-5 in every shape). A *common* monotone transform of the drops leaves WMW unchanged exactly. **Correction to the agenda's premise:** rank tests do not absorb *individual-specific nonlinear* scale use. That is not representable by the battery, but randomization protects the level, so it is accepted as a power-only threat |
| 7 | Measurement attenuation: the slider registers a small share of latent change | **H1b identification** | symmetric | **NEW FINDING, run 2** | At the design basis θ = .592 the calibrated attenuation is a ≈ .046–.063. The frozen H1b's absolute ±δ_eq band (5 pts) then swallows the whole gate-vs-R3 P3 dissociation (−1.5 vs +0.6 pts): frozen H1b verdict power is 0 for the gate. Counter: scale-invariant H1b-SI (run 3, author decision) |
| 8 | Composite no-gate population (R3 types + R4 types) | **H1b specificity** | n/a (rival population structure) | **NEW FINDING, AD4** | R3 subjects supply the H1a effect; R4 subjects supply a P3 decline under MODERATE (frozen −35.7). Pooled, they can mimic both gate signatures. Counter candidate: drop-conditioned H1b-SIc (run 3). A within-subject coupling test was rejected pre-run: the gate's own coupling is +.475 |
| 9 | Income targeting / hedging across incentives | forecast layer; H1a not affected | symmetric | COUNTER (added I032) + ACCEPTED, SCOPED | **Bug found in this audit:** the first build scored the "forecast" against the round just settled, which a SQUARE chooser had already seen. Fixed: forecasts are of the next round. Residual hedging (forecast low on SQUARE, then choose SQUARE) is possible with one paid forecast round of 10 pts; the forecast layer stays exploratory, and the pilot checks forecast–choice coherence |
| 10 | Attention and satisficing | power | symmetric | ABSORBED + COUNTER | Represented: no-effect non-responders (M3, M6 with enriched exclusion). Counters: P1-accuracy screen, zero-movement screen, comprehension quiz with repeat-until-correct (Oppenheimer et al.: prompting rereading is preferred to excluding). Prolific (Peer et al.: highest quality without filters). Approval-rating filter kept but no longer cited as quality control |
| 11 | Block-order effects (P1/P3 regime, carry-over into the P2 drop) | H1a level if unbalanced | balanced by design | COUNTER (in design) + ABSORBED | P1/P3 regimes iid per participant in both arms. The certified generator uses exactly this structure (the reason it departs from the frozen one-regime generator). The phase *order* (rich → poor → restoration) is the manipulation and is not counterbalanced: claims are scoped to this order |
| 12 | Probability distortion on displayed prices | power; suspicion (→ #2) | symmetric | ACCEPTED, SCOPED + author decision | Quotes fixed at 50/50 (no phase leakage). Tickets are free, so price carries no payoff; any weighting of the displayed price is common to both arms. Open: a 50/50 quote against an experienced ~65% rate could seed "mispriced market" suspicion. It is symmetric, so it enters #2 only if it differs by arm. Whether to show prices at all is an author decision; the pilot framing comparison (market vs bandit skin) measures it |
| 13 | Generator dispatch / silent default kernel | certification validity | n/a | COUNTER (added I032) | **Run-1 defect:** the kind name 'gate' fell through to the R1-global kernel. Unknown kinds now raise; run 1 invalidated in full and preserved |

## What D changes in the design (carried into E)

1. Pilot believability rule gains the differential-load criterion from S7 (#2).
2. H1a sensitivity analysis excluding blind-coded hypothesis-guessers (#1).
3. Zero-movement screen replaces zero-variance under randomized starts (#5); prereg exclusion wording updated.
4. Forecast layer redefined as next-round forecasts (#9).
5. H1b's form is reopened: the frozen form is not identified at the design basis (#7). The candidates are H1b-SI and H1b-SIc (#8). Adoption is an author decision informed by run 3.
6. The premise that "rank tests absorb monotone scale use" is corrected in the docs: exact only for a common transform. Individual nonlinear scale use is level-safe by randomization and costs only power (#6).
