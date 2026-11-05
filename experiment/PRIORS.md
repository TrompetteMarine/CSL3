# Frozen prior-elicitation specification: the top-3 lab-to-field quantities

Frozen 2026-11-05 under `freezes/00_freeze_I023.yaml`, before any human data
exist. This document states, for each of the three quantities the preregistered
experiment is designed to measure, (i) what the quantity is in the model, (ii)
the model-generated value at the frozen defaults, (iii) the lab estimator that
replaces it, and (iv) the field prior it seeds for the later social-media
analysis. The chain is always **model → lab posterior → field prior**; a
model-generated number is never used as a field prior once the lab posterior
exists, and no lab-confirmed claim is recycled as a field prior without this
chain being stated.

**Confirmatory discipline.** Only H1 is confirmatory (one-sided Welch on the
P1→P2 legitimacy drop, HIGH vs LOW reference; α = 0.005, N = 320/cell, d = 0.25
design floor). P-B is a preregistered secondary; P-C is instrumental. Neither
is promoted post hoc. Model-implied effect sizes (d = 1.8–6.6) are upper bounds
under homogeneous agents and play no role in the design basis.

---

## P-A. Reference-dependence magnitude (from confirmatory H1)

**Model quantity.** The share of delegitimation attributable to the reference,
not the outcome stream: both arms of the H1 contrast receive identical own
outcomes in P2; only the yoked peer-reference regime (HIGH/LOW) differs. In
window terms (main text, "The window" section) the manipulation is a controlled
displacement of cross-exposure x: HIGH holds the participant inside the
grievance region while own outcomes run below entitlement; LOW sits below it.

**Model-generated value (frozen generator `predict_taskv3.py`, 300
subjects/condition).** P2 trust 53 (HIGH) vs 74 (LOW) on the 0–100 fairness
scale — a reference-driven gap of ~21 points on identical outcomes. The
utility-rival class (inequity-in-utility, R3) mimics roughly half the drop with
the same ordering, so the *magnitude ratio* (reference-driven gap / total P1→P2
drop) is the discriminating statistic, not the sign.

**Lab estimator.** Preregistered primary: one-sided Welch t on the P1→P2
fairness drop, HIGH vs LOW. Prior-seeding output: the standardized gap with its
CI, plus the magnitude ratio against the total drop.

**Field prior seeded.** The coefficient linking *reference exposure*
(visibility of others' success) to legitimacy-laden language, holding own-side
outcomes fixed. Functional form: a normal prior on the standardized effect,
centred on the lab posterior mean, with the lab posterior SD inflated ×2 for
transfer loss. Identification in the field leans on exposure shifts with
outcomes held fixed (platform feature changes, feed-composition
discontinuities), mirroring the lab's own-outcome-matched contrast.

## P-B. Restoration dissociation and the recovery threshold (from H2/H3)

**Model quantity.** Two coupled signatures of gate-type (uptake-side)
delegitimation that no instantiated rational rival reproduces:
(1) after restoration, behaviour corrects at evidence speed while legitimacy
repairs on the 1/ρ aspiration clock (model: P3 accuracy 0.95 vs trust 43,
FULL restoration);
(2) reopening requires restored quality above a threshold — reopening time
diverges as restored quality approaches the resignation boundary at the
agent's current aspiration (model: ~3×10⁴ trials at μ_good = 0.5 vs ~10² at
0.9; MODERATE restoration flatlines at trust ≈ 14 while FULL repairs).

**Lab estimators.** H2: midpoint-lag between the behavioural and trust recovery
curves, with censoring at session end handled as preregistered (censored
observations bound, never imputed). H3: the FULL vs MODERATE reopening
contrast; the analysis refuses an incomplete 2×2 crossing.

**Field priors seeded.** (1) The persistence half-life of delegitimated
discourse after corrective exposure, relative to the half-life of behavioural
adjustment — a lognormal prior on the lag ratio centred on the lab posterior.
(2) The minimum visible-success dosage below which corrective exposure does not
reopen uptake — a threshold prior for dose-response models of exposure
interventions. Both make the gate's *field* signature concrete: exposure
campaigns below threshold, or judged on behaviour alone, will look like
successes while legitimacy stays collapsed.

## P-C. The aspiration-rigidity distribution (instrumental, from H4 + slider)

**Model quantity.** Individual aspiration rigidity ρ — the one gate parameter
identifiable at the individual level. The entitlement slider breaks the
latent-aspiration likelihood ridges; synthetic recovery r = 0.91 (frozen
identification study). Group means of νF and τF are recoverable with small
bias (+1.5%, +2.4%); νR is group-biased −30% and is **excluded** — no νR
priors are issued at any level.

**Lab estimator.** Per-subject ρ posterior from the slider-instrumented fits;
the population output is the distribution of log ρ (location, scale, and its
moderation of H1–H3 effects, preregistered as the rigidity moderator). The
induced learning-rate asymmetry (dual-α DiD +0.42 HIGH / +0.21 LOW vs gate-off)
remains exploratory: its level-sanity check failed in the frozen record and
all claims are difference-based.

**Field prior seeded.** The heterogeneity prior for all field models: the
population distribution of rigidity determines, through the gate-reopening
clock t*(x) = ρ⁻¹ ln[(A₀−Aᵉᵠ)/(A*−Aᵉᵠ)] (Supplementary Section S13), the
*predicted distribution of persistence times* at any exposure level x. The
field analysis therefore needs two inputs and produces one test: the platform's
exposure distribution (measured) and the lab's ρ̂ distribution (this prior)
jointly predict the persistence distribution of delegitimated discourse — a
quantitative, falsifiable field prediction rather than a directional one.

---

## What the field stage must measure

The window makes the field quantity explicit: the distribution of
cross-exposure x that a platform's structure induces over communities.
Operationally: the share of a community's consumed content originating from
communities on the corrected side of the relevant dispute. The theory locates
every community's fate on that distribution (defensive consensus inside the
window, resignation below it on the t* clock, correction above x_B), so the
field analysis is an out-of-sample test of the window map with all three
priors above as inputs, not a refit.

## Explicitly out of scope

No individual νR inference (excluded above); no dual-α confirmatory claims;
no DDM/RT claims (the choice rule is a first-passage reduction; RTs are
recorded exploratory only); no field claim without the model → lab → field
chain stated. The scope conditions (conformist, confidence-weighted
transmission under uniformly weak exposure) go directly to the field stage as
measurable moderators; they are not lab quantities.
