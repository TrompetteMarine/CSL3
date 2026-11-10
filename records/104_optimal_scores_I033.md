# Simulation-derived test statistics for the ten-round task (I033 AD-O1, 2026-11-10)

The protocol was frozen before running (`freezes/00_freeze_I033.yaml`, AD_O1).
The script is `experiment/analysis/optimal_scores_I033.py`, and the record is
`records/optimal_scores_I033.txt`.

- Weights were trained on simulated pools (seed 133700, gain .5) and then
  frozen.
- Power and false positives were computed on fresh pools (seed 133701).
- The S-c block is post hoc (seed 133702) and labelled as such.

One correction: the first run had the sign of the baseline row reversed. It was
fixed and re-run, and all other numbers are identical.

## The three roles of simulation

1. **Empirical distribution of the task.** The generator produces as many
   simulated participants as wanted under the gate (at each theory-edge point)
   and under each rival. The sampling distribution of any statistic of the ten
   ratings is therefore known by simulation, at any sample size.
2. **Deriving the statistic.** We do not hand-build contrasts. Each participant
   gets a linear score w'y of the ten fairness ratings.
   - The weights are w = Σ⁻¹d, where d is the between-arm mean difference the
     gate predicts and Σ is the within-arm covariance. This is the
     Neyman–Pearson direction under a Gaussian working model.
   - The gate-specific score S-b projects d away from the between-arm
     difference the utility rival R3 predicts. This is an orthogonalised score
     in the spirit of Neyman's C(α).
   - The test itself remains a rank test (WMW) on the scores. Its level
     therefore does not depend on the working model.
3. **Design constraint from prior work.** The literature fixes what does not
   need new humans. See the positioning section.

## Results (ten rounds; three-item scale; n per arm for power ≥ .90 at every inside theory point)

| statistic | gain ¼ | gain ½ | gain 1 |
|---|---|---|---|
| hand-built H1a (rich-phase mean − deprivation-phase mean) | 214 | 116 | 76 |
| S-a, simulation-derived reference-effect score | **80** | **70** | **58** |
| hand-built H1b conjunction (AD-B1) | 278 | 128 | 88 |
| S-b, gate-specific score (R3-orthogonal) | **145** | **90** | **86** |

- **S-a weights** load negatively on rounds 1–4 and positively on rounds 6–10,
  most heavily on round 10. The reference effect accumulates and persists.
- **S-b false positives** are ≤ .010 against R3 (both anchoring weights), R4,
  and the no-gate composite, at every gain.

**Limit found.** S-b is not specific against slow-reporting ("integrating")
utility rivals: false positives are .24–.39 at gain ½ and .57–.92 at gain 1.
Projecting those rivals out as well (S-c, post hoc) restores the level but
leaves almost no power: none at gain ≤ ½, and 168 per arm at gain 1. Over ten
rounds, the gate's mean fairness path is nearly a linear combination of the
paths of R3 and a slow-reporting R3.

Mean ratings alone therefore cannot separate "legitimacy is a slowly moving
stock that gates learning" from "fairness reports lag inequity". Separating
them needs a measure that is not the mean fairness path. Candidates:
- the response to full restoration, where a lagging report must catch up and a
  gated one is capped by its repair rate;
- person-level heterogeneity tied to measured entitlement;
- the paid re-draw offer.

## Positioning (verified bibliographic records; claims at abstract level)

- **Design optimisation for model discrimination.** Choose the design that best
  separates competing models before collecting data: Myung & Pitt (2009),
  *Psychological Review* 116(3), 499–518. Our design search over phase lengths,
  odds and round summaries is this, done by simulation.
- **Simulation-based inference.** When the likelihood is implicit in a
  simulator, inference and test statistics are learned from simulated draws:
  Cranmer, Brehmer & Louppe (2020), *PNAS* 117(48), 30055–30062.
- **Orthogonalised scores.** Tests of a parameter of interest made insensitive
  to nuisance directions: Neyman (1959), "Optimal asymptotic tests of composite
  statistical hypotheses" (C(α)). Cited from the canonical text; only the
  bibliographic record is verified.
- **Predictions plus a small labelled sample.** Combine many model predictions
  with few human observations and stay valid: Angelopoulos et al. (2023),
  *Science* 382, 669–674 (prediction-powered inference). This is a candidate
  for the analysis stage, with the generator's predicted rating path as the
  prediction. It is not yet evaluated.
- **Already in the record.** Theory-edge SESOI; internal pilot (Wittes &
  Brittain 1990); design calculations from external information (Gelman &
  Carlin 2014).

## Proposal

- **H1a** = S-a.
- **H1b** = S-b, gatekept after H1a. Weights are frozen from simulation before
  any human data. The claim is scoped to "not explained by R3, R4 or their
  mixtures".
- The slow-reporting rival is named as unexcluded, pending a dedicated
  discriminating measure.

At gain ½ the confirmatory core is about 90 per arm for ten rounds, plus the
small full-restoration arm.

Not yet done:
- maximin weights over the theory region;
- re-training at other gains;
- measurement shapes M1–M6;
- starting-entitlement sensitivity;
- bit-identical re-run.
