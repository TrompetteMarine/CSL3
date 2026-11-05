# Online experiment design — reference-dependent delegitimation (v2, I027)

Supersedes the I006 design document (v1 remains in repository history). Status:
complete design; constants marked PILOT are fixed by the pilot before OSF filing;
constants marked LAB feed the field project (see `../field/FIELD_DESIGN.md` and
`PRIORS.md`). The oTree 6 app `diss_bandit` implements the task; the build deltas
from v1 are listed in §10.

## 1. What the experiment must do, and nothing else

The simulations cover every question that does not require a human. The experiment
is the smallest humans × treatments grid that (i) confirms the central prediction
and (ii) identifies what no simulation can: whether the legitimacy gate exists in
people (restoration dissociation), the magnitude of reference-dependent
delegitimation against its utility rival, and the human distribution of aspiration
rigidity ρ (the lab-to-field instrument). Everything below is organised around
those three outputs.

## 2. Platform and logistics

Prolific, desktop only, English-fluent, approval ≥ 97%, no prior participation in
pilot or pool sessions. Session ≈ 28 minutes. Payment: base £4.20 (≈ £9/hr) +
performance bonus (expected £1.10, realized from points incl. windfalls) + the
WTP endowment residue (§5). Server: the existing oTree deployment (Lightsail or
Heroku tier as in v1); waves of ≤ 60 concurrent to protect yoking and server load.

## 3. Treatments and allocation (between-subject)

Factor A, reference regime in the deprivation block: HIGH (visibly successful
peer, realized mean in [.60,.70]) vs LOW (peer matched to the participant's own
realized band ± .05). Factor B, restoration: FULL (.65/.35) vs MODERATE (.45/.35).

Confirmatory allocation: N = 320 per reference arm post-exclusion (the
distribution-free worst-case N*; see §6), pooled across Factor B for H1a (Factor
B diverges only in P3); within each reference arm, MODERATE : FULL = 2 : 1
(≈ 213 : 107). FULL is the positive control that the fairness instrument can
move (a MODERATE flatline is otherwise confounded with slider insensitivity)
and carries the H3 contrast. Total confirmatory N = 640.

Framing-probe module (secondary, separable): one additional arm, HIGH × MODERATE
with group-contingent fixed-rate instructions ("the payout rule was set for your
group as a whole at a fixed rate"), n = 90. Gate predicts the P2 drop persists;
the group-contingent Bayesian banks first-phase evidence and predicts no drop.
Secondary α, one-sided; powered 0.76 at d = 0.5 (the rival-vs-gate gap here is
large by both accounts). This module can be dropped without touching the
confirmatory core.

Recruitment: 640 + 90 = 730 post-exclusion (dose module adds 180; TASK_SPEC.md);
inflate by the PILOT exclusion forecast (planning value 12%) → ≈ 1,020 recruited
for the main run incl. dose cells, plus pilot 100. Indicative cost at current
Prolific rates: ≈ £6,300 all-in. The simulated exclusion-selection power cell
independently confirms 360 recruited per confirmatory arm suffices.

## 4. Task (v3, as built, with the I027 additions)

Two-armed bandit, 450 trials, three 150-trial phases invisible to participants:
P1 rich (.65/.35), P2 deprivation (.30/.15), P3 restoration (Factor B). Announced
non-contingent +3 windfall every 15th trial. Arm-side counterbalanced; outcome
sequences seeded and reproducible. Every 5 trials, two sliders: "the payout rule
is fair" (0–100) and "what I deserve per trial" (entitlement). RTs recorded,
preregistered as exploratory only (the choice rule is a first-passage reduction;
no RT claims).

Peer display, truthful by construction: every trial shows the running earnings of
"another participant who previously completed this task." The displayed streams
are drawn from the pool of real pilot-session participants (the pilot is the pool
source; the v1 dev-pool placeholder is retired). HIGH streams: pool members whose
realized P2-window earnings fall in [.60,.70], stratified on trajectory shape
(terciles of within-block variance) so selection is on mean, not on volatility.
LOW streams: yoked to the participant's own realized earnings band (± .05),
re-matched each block. Instructions disclose exactly this provenance; no
deception anywhere in the protocol.

## 5. Measures

1. Choices per trial (behavioural accuracy = optimal-arm rate).
2. Fairness slider (primary legitimacy measure; rating = 100·L link stated as an
   auxiliary assumption, not a fact).
3. Entitlement slider (manipulation check + the ρ identification lever; slider-
   instrumented individual ρ, synthetic recovery r = .91).
4. Incentive-compatible legitimacy (new, preregistered secondary): at two fixed
   points (end of P2, mid-P3) a one-shot option to pay from a dedicated 20-point
   endowment to have the computer replace the payout rule with a fresh rule
   generated the same way (truthful: the engine re-seeds the same generative
   process; the phase schedule is unaffected). Willingness-to-pay = revealed
   distrust of the standing rule. Elicited as a 0–20 price list; unspent endowment
   paid out.
5. Manipulation/believability block (post-task): perceived peer success (1–7),
   perceived peer realness (1–7), funnel debrief (free-text purpose guess, rig
   suspicion probe), demographics.

## 6. Hypotheses and tests (serial gatekeeping; FWER = .005)

As preregistered (prereg draft, I025 amendment) and tabulated in the manuscript's
Table 1: H1a reference drop (one-sided Wilcoxon–Mann–Whitney at α = .005, effect
measured as θ = P(drop_HIGH > drop_LOW); N = 320/arm gives power ≥ .90 at the
design basis θ = .592 as the worst case over the frozen six-shape battery of
`analysis/power_free.py` — bounded, rounded, zero-inflated, heavy-tailed, skewed
and exclusion-selected shapes; mean-shift tests lose up to half their power under
the skewed shapes, hence rank-primary with studentized permutation Welch
co-reported; at the θ = .570 floor power is .65–.72, reported not claimed) → if
it rejects,
H1b the gate (HIGH × MODERATE: accuracy recovery above a pre-stated floor AND
fairness TOST within ± δ_eq AND the band excludes the utility rival's predicted
recovery). Secondaries: H2 midpoint-lag dissociation; H3 Reference × Restoration
threshold interaction; H4 shortfall-scaled decrements vs capped increments; H5
pilot-gated shared-failure contrast; WTP convergence with the slider (construct
validation); framing probe (§3). Rigidity moderator: slider-instrumented ρ̂,
within-subject, no cells of its own. Analysis by the frozen pipeline with blind,
preregistered exclusions.

## 7. Pilot (N = 100; precedes ethics-final + OSF filing; its outputs are design constants)

Arms: 60 standard-elicitation (40 HIGH-MODERATE, 10 LOW-MODERATE, 10 HIGH-FULL) +
40 sparse-elicitation (sliders every 10 trials) for the reactivity check.
Pre-stated outputs and decision rules:
- σ_r (rating noise) → δ_eq and H1b equivalence power; δ_eq = max(5 points,
  0.5·σ_r) unless the pilot shows floor effects, in which case the rule is
  re-stated before filing.
- ρ̂ distribution → the band rule: if fewer than 30% of pilot participants show an
  entitlement half-life ≥ 150 trials, P2 is lengthened to 225 trials (session
  ≈ 33 min) or the within-session persistence secondaries are dropped ex ante,
  stated in the preregistration either way.
- Believability: if > 20% fail the realness probe or name the yoking in the
  funnel, the display protocol is revised (provenance wording, stream selection)
  and the pilot repeated on the failing arm; exclusion forecast updated from the
  observed rate.
- Slider reactivity: dense vs sparse arms compared on P2 drop and entitlement
  drift; if elicitation density moves the primary by > 0.2 SD, the main run
  adopts sparse elicitation and the power arithmetic is restated.
- MODERATE calibration: realized fairness trajectory against the generator band;
  the .45/.35 setting is confirmed or shifted before filing.
- Pool generation: pilot streams (with consent) become the yoked display pool.
No pilot datum enters any confirmatory analysis.

## 8. Ethics

No-deception protocol (the display and the rule-switch are truthful as specified);
information sheet names earnings display of prior participants; anonymised
Prolific IDs only; standard withdrawal; payment floor independent of performance;
ethics application under the QMUL template (contact g.l.s.bontemps@qmul.ac.uk),
with the pilot covered by the same application as a named phase.

## 9. Decision rules (what refutes what)

Per the preregistration draft: H1a null at sensitivity d = .25 → reference-
dependent gating refuted in humans; programme reverts to the theory/ABM
contribution. H1a pass + H1b fail → reference dependence confirmed, gate not
identified; mechanism language demoted accordingly in any resulting paper. H1a+b
pass → the gate exists in people; ρ̂ and the magnitude ratio go to the field
project as priors. All intermediate patterns are enumerated in the prereg.

## 10. Build deltas from the v1 oTree app (small, enumerated)

(1) 2:1 MODERATE:FULL allocation switch; (2) WTP probe pages + endowment
accounting + truthful re-seed hook; (3) funnel debrief + manipulation-check
block; (4) pool loader replacing the dev stream generator (pilot-sourced,
stratified HIGH selection); (5) TOST/equivalence module in `pipeline.py` for H1b;
(6) framing-probe instruction variant; (7) sparse-elicitation toggle for the
pilot arm. Nothing else changes; bots and the smoke suite re-run after each
delta.

## 11. Timeline (indicative)

Build deltas 1–2 weeks, in parallel with ethics (2–4 weeks). Pilot: one week of
collection + one of analysis → constants frozen → OSF registration. Main run:
2–3 weeks in waves. Confirmatory analysis: push-button on the frozen pipeline
within days. Field project priors (PRIORS.md) issued from the lab posteriors
immediately after.
