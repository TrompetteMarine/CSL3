# I028 — task foundations: calibration, severity, and the logic of the inference

Research document for the shared abstract-market / prediction-market engine. No
task spec is written here; this is the reasoning the spec must satisfy. All
numbers recomputed from frozen quantities (script in the freeze record); nothing
recalled.

## 1. Where the task sits in the canon

The single-player, seeded-settlement configuration inherits from four literatures,
and takes one thing from each. From experimental asset markets (Smith's induced-
value method; Plott–Sunder information aggregation; Smith–Suchanek–Williams
bubbles): institutions are experimenter-built objects, so "the market" can be a
controlled rule rather than an emergent one — our settlement engine is an induced
institution, which is what makes "the game is rigged" objectively false and the
rival class disciplined. From prediction markets (Hanson's market scoring rules;
the Iowa Electronic Markets): the bet as an incentive-compatible belief statement,
and the documented failure mode that matters to us — wishful betting by invested
traders (the IEM partisan-trader results, verified I032: Forsythe et al. 1992
§III Table 8; "contagion of wishful thinking", which is Seybert & Bloomfield
2009, *Manag. Sci.* 55(5) — attribution added I032; in
market settings) — which is evidence that motivated distortions survive market
discipline, i.e., that the construct we hunt lives in this habitat. From the
belief-elicitation literature: proper scoring is behaviourally fragile — showing
participants the incentive details of a binarized scoring rule pulls reports
toward the center (Danz–Vespa–Wilson, AER 2022) — so any probability-report layer
must use minimal-information BSR, and the legitimacy construct must NOT ride on
probability reports (it rides on the fairness slider and the paid rule-switch,
which have no scoring rule to game). From motivated-beliefs theory
(Kunda; Bénabou–Tirole): the standard mechanism is belief *distortion* about
states; our gate is a different object — a weight on the *evidential authority of
outcomes* — and the task's job is to separate those (Section 4).

Verification queue (before any manuscript use, per the citation log discipline):
Smith 1962/1976; Plott & Sunder 1988; Smith, Suchanek & Williams 1988; Hanson
2003/2007 (LMSR); Forsythe, Nelson, Neumann & Wright 1992 (IEM wishful thinking);
Hossain & Okui 2013 (binarized scoring rule); Danz, Vespa & Wilson 2022 AER
112(9); Thaler & Johnson 1990 (house money); Platt 1964 (strong inference); Mayo
2018 (severity); Kunda 1990; Bénabou & Tirole 2016.

## 2. What the paper calibrates in the task

The decisive discovery of this iteration: at the frozen constants
(A*(μ) = 0.3 + 0.25·μ/(1−μ)), **the HIGH/LOW manipulation is the relative-
deprivation theorem's permanence condition, realized as a design cell.** The gate
stays shut permanently iff χ(μ_ref − μ_own) > A*(μ_own) − μ_own, i.e. iff
χ > χ_min(μ_ref) = [A*(μ_own) − μ_own]/(μ_ref − μ_own). At task-realistic P2 own
rates:

| μ_own | A* | gap | χ_min at μ_ref=.65 | at .55 | at .45 |
|---|---|---|---|---|---|
| .30 | .4071 | .1071 | **.306** | .429 | .714 |
| .225 | .3726 | .1476 | **.347** | .454 | .656 |
| .15 | .3441 | .1941 | .388 | .485 | .647 |

At the model's χ = .4, only the μ_ref = .65 column is inside the permanence
region: the storyboard-style rich peer sustains grievance indefinitely; a .55 or
.45 peer does not. Three consequences. (i) The HIGH cell is not merely "more
reference" — it is on the other side of a theorem's frontier from LOW, so the
theory forces a qualitative contrast (sustained versus self-extinguishing), not a
graded one. (ii) μ_ref is the severity dial: the experiment can be placed as
close to or as far from the frontier as we choose. (iii) Human χ is the unknown
that locates participants relative to the frontier (the identification study
recovers χ only descriptively, r = .62), so the design must either sit deep
inside the region (μ_ref = .65 covers χ ≥ .35) or measure the frontier itself
(Section 3).

The clocks calibrate the phase lengths. Under LOW, grievance self-extinguishes at
t* = ρ⁻¹ ln[(A₀ − μ_own)/(A* − μ_own)] ≈ 1.0–1.3/ρ for A₀ ∈ [.55,.60] — about
100 trials at ρ = .01, about 500 at ρ = .002. And the H1a aspiration gap at the
end of a 150-trial P2 is χ(μ_ref − μ_own)(1 − e^{−150ρ}): at χ = .4 it runs from
.044 (ρ = .002) to .162 (ρ = .02) — a factor of nearly four. This is the ρ-band
risk stated as an equation: slow-ρ humans compress the confirmatory contrast not
because the gate is absent but because the anchor difference has not yet
propagated into aspiration. The pilot's ρ̂ distribution therefore does not just
gate secondaries; it predicts the H1a effect size through this formula, and the
pre-stated remedy (lengthen P2) has a derived dose: at ρ̂ = .005, extending P2
from 150 to 225 trials moves the gap from .090 to .122 (×1.35 on the manipulated
component). The windfall cadence and the MODERATE restoration level calibrate as
before (the φ⁺ restriction; the recovery-threshold divergence), unchanged by the
market skin because the skin is isomorphic on (μ₁, μ₂).

## 3. Parameterising for "emergent or absurd"

The design principle: every cell is placed so that the gate's prediction and the
best rival's prediction are not merely different in size but different in kind —
the observed pattern should be forced if the theory is true and absurd under the
rival, or vice versa. Five placements follow from the arithmetic above.

**The step-versus-line cell.** The gate predicts a threshold in μ_ref: below the
frontier, sustained grievance does not occur (self-extinction on the ρ clock);
above it, it does. The inequity-in-utility rival — the one rival that survives
H1a — predicts disadvantage disutility *graded* in (μ_ref − μ_own): a .45 peer
produces roughly half the effect of a .65 peer. A three-point reference dose
(μ_ref ∈ {.45, .55, .65}, the middle point chosen near the χ = .4 frontier)
therefore makes the two accounts maximally distinguishable: step versus line.
This is the cheapest strong-inference addition the market engine enables (the
peer board displays any μ_ref), and it upgrades H1a from "a reference effect
exists" to "the reference effect has the gate's shape."

**The absurd-sign cells**, where the gate predicts what rational accounts call
backwards: (i) the richer the visible winner, the *longer* grievance persists
after conditions improve (dt*/dx > 0 in the collective theory; here, HIGH-peer
participants should show slower fairness recovery in early P3 than LOW-peer
participants, while every information account says a successful peer is evidence
the environment works and should speed trust recovery); (ii) announced windfalls
raise earnings but not legitimacy (capped repair) — money does not buy back the
game's authority, where any payout-based account says it must; (iii) "too little,
too late" — moderate restoration improves everything objectively and moves
behaviour, and fairness does not move (the H1b flatline), where the utility rival
recovers because its ratings track current outcomes.

**The null-region cell (absurdity in the other direction).** At neutral
entitlement the gate predicts *nothing*: no reference effect, no drop beyond the
rational baseline. The task already realizes this in P1 (own outcomes at or above
aspiration); stating it as a formal prediction (P1 fairness invariant to the
peer board) gives the theory a region where finding an effect would count
against it — a falsifiability region inside the same session, which is what
separates a severe design from a confirmatory-only one.

**What the market skin adds to severity.** The paid rule-switch is a dominance
test: a participant who reports the market unfair but will not pay one point to
replace it reveals the report as cheap talk; one who pays reveals the grievance
as consequential. And the bet/report separation (the storyboard's own two-screen
structure) lets us check that probability reports about settlements stay
coherent while fairness collapses — the gate is about the authority of outcomes,
not about probability arithmetic, so delegitimation with intact calibration is
the signature; global belief derangement would instead implicate confusion.
Both measures are flagged exploratory until the pilot shows the BSR layer does
not contaminate the fairness measure (Danz–Vespa–Wilson is the reason for
caution).

## 4. The logical structure of the inference

Let G be the gate model, and the rival class R = {R1 fixed-hypothesis Bayesian,
R2 associability (Pearce–Hall), R3 inequity-in-utility, R4 group-contingent
Bayesian, R5 unconstrained hierarchical Bayesian}. Auxiliaries: A1 the
rating↔legitimacy link; A2 stable anchoring weight χ within session; A3
instrument sensitivity (sliders can move); A4 believed display provenance.

The inference is a strong-inference tree with localized auxiliaries, not a single
test of G:

- H1a (reference-ordered drop at matched own outcomes) partitions the class:
  {G, R3} predict it; R1-global predicts null or reversal (the successful peer
  *rescues* the rigged-world hypothesis); R2 and own-outcome-only accounts
  predict null. H1a rejecting the null eliminates {R1-global, R2, own-outcome
  accounts} by modus tollens and establishes reference dependence — a class
  property, not yet the gate.
- H1b (accuracy recovers ∧ fairness inside the equivalence band ∧ band excludes
  R3's recovery path, under moderate restoration) is the G-vs-R3 experiment.
  Its deductive force depends on A3, which is why the FULL arm exists: FULL
  moving the slider refutes the A3 explanation of a MODERATE flatline, so the
  conjunction (flatline ∧ FULL-moves) implicates the core, not the instrument.
  This is the general pattern: every Duhem–Quine escape route gets its own
  independent check (A4 by the believability funnel; A2 by the entitlement
  slider's own dynamics; A1 by the paid rule-switch converging with the slider),
  so a failed prediction localizes rather than dissolving into holism.
- The step-versus-line dose cell targets the surviving degeneracy after
  H1a∧H1b: it tests the gate's *functional form* against a graded-disutility
  repair of R3.
- R4 is addressed by the framing probe (banked evidence ⇒ no drop), R5 by
  explicit demarcation: an unconstrained hierarchical prior can mimic any
  pattern and is excluded on predictive-content grounds, stated in advance —
  this is the boundary where testing ends and theory choice begins, and the
  paper says so rather than pretending the data decide it.

Formally, each cell is a severe test in Mayo's sense: the probability of the
gate-pattern arising if the gate is false is made low *by construction* (the
rival's prediction at the same cell has the opposite sign, a different shape, or
a different margin), and the probability of detecting the departure if the gate
is true is the power arithmetic already fixed. The design converts "is G true?"
into an ordered sequence of eliminations with pre-stated verdicts.

## 5. What hypothesis testing does to the model

Pre-stated revision map, written before any data:

- **H1a∧H1b pass.** The gate exists in people. ρ̂, χ̂ (descriptive), the
  magnitude ratio and δ-calibrated effect sizes replace frozen defaults; the
  collective batteries re-run at the empirical parameter distribution become the
  field predictions (PRIORS.md slots fill; the window and the two clocks become
  a calibrated measurement theory). The model's status changes from "internally
  validated simulation" to "instrument."
- **H1a passes, H1b fails, FULL control passes.** Reference dependence is real;
  the gate is not identified as a separate margin. The model collapses onto the
  utility-rival class for individuals, and the collective layer must be
  re-derived: we already know from the frozen rival battery that the utility
  rival corrects under transparency, so defensive wrong consensus would lose its
  microfoundation — the uptake-side echo-chamber derivation dies, the
  relative-deprivation statics survive, and the paper's successor says exactly
  that. This is the branch with the largest model damage, and it is honest to
  write it down now.
- **H1a fails at sensitivity d = .25.** Reference-dependent delegitimation is
  refuted in this range: human χ is effectively below every frontier the task
  can realize. The resignation theorem becomes the model's central empirical
  content (grievance self-extinguishes; sour grapes), persistent delegitimation
  requires anchors the lab cannot instantiate (cultural constants, identity),
  and the collective trap is re-scoped to those. The programme reverts to the
  theory/ABM contribution with that scope condition stated.
- **Step-versus-line outcomes.** Step at the predicted frontier: the gate's
  functional form is confirmed and χ̂ gets a structural estimate (the frontier
  location identifies χ through χ_min(μ_ref) — the dose cell is secretly a χ
  measurement). Line: threshold structure refuted even if H1b passed —
  a hybrid (graded gate) forced; the A* closed forms survive only as
  approximations.
- **Null-region violation (P1 reference effects).** Entitlement-independence
  refuted; the gate's trigger condition (shortfall relative to aspiration) is
  wrong even if delegitimation itself is real; the dissonance functional's
  frame term needs a reference term independent of own shortfall.

## 6. The market structure: gains and threats, soberly

Gains: the induced institution makes the delegitimation target objectively fair
(discipline on rivals); the trader-board reference uses the storyboard's own
screens; the paid rule-switch adds revealed preference; the bet layer adds a
calibration check; the skin matches the field domain (betting/finance
communities), so the lab-to-field chain runs through one habitat; the EEG
configuration exists downstream for the entitlement-shortfall-versus-RPE
regressor dissociation.

Threats, each with its disposal: loss framing (house-funded tickets keep the
gains domain; Thaler–Johnson is the reason); scoring-rule gaming and
centre-pull (minimal-information BSR, and legitimacy never rides on scored
reports); richer paranoia space ("the AMM moves prices against me" — disclose
the AMM rule truthfully and fix prices within phases, so the settlement
process, not the price process, is the only degree of freedom); gambling-frame
heterogeneity (screen on betting familiarity, exploratory moderator);
probability-numeracy heterogeneity (the fairness construct must remain primary
precisely because it requires no numeracy).

## 7. What the task spec (next iteration) must now contain

The isomorphism table (two tickets ↔ two arms, settlement rates ↔ phase means,
house-funded payout ↔ gains domain); the reference-dose module (μ_ref ∈
{.45,.55,.65}) with the frontier arithmetic above as its preregistered
prediction; the P1 null-region prediction; the ρ̂→effect-size formula wired into
the pilot decision rules; the exploratory flags on bets and rule-switch pending
pilot; and the synthetic-recovery gate re-run on the market-skinned generator
before anything is frozen for preregistration — isomorphism is an argument,
and the gate is the proof.
