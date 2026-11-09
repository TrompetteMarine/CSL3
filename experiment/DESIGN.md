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
pilot or pool sessions. (I032: the approval filter is kept as a standard
platform filter but is not a quality control. Peer et al. 2022 find
reputation does not predict data quality on Prolific. Quality is carried by the
in-task screens of §5 and the exclusions of §6.) Session ≈ 28 minutes. Payment: base £4.20 (≈ £9/hr) +
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

As built (I032), the task runs in the market skin of TASK_SPEC.md §1 (tickets,
seeded settlement, fixed quotes, trader board); the bandit skin remains behind
`skin='bandit'` for the pilot framing comparison. Slider conventions (forced by
TECHNIQUES.md #10): step 5 (21 points), matching the round-to-5 measurement
model the certification passed under; a **randomized start position on every
elicitation**, logged, because fixed defaults on 101-point sliders draw excess
responses at the default (midpoint included). A comprehension quiz on the
market rules and the peer's provenance precedes the task, repeated until
correct, with no exclusion attached (TECHNIQUES.md #7). An `iti_jitter_ms`
session knob (off online) keeps the shared engine imaging-compatible
(TECHNIQUES.md #14).

Peer display, truthful by construction: every trial shows the running earnings of
"another participant who previously completed this task." The displayed streams
are drawn from the pool of real pilot-session participants (the pilot is the pool
source; the v1 dev-pool placeholder is retired). HIGH streams: pool members whose
realized P2-window earnings fall in [.60,.70], stratified on trajectory shape
(terciles of within-block variance) so selection is on mean, not on volatility.
LOW streams: yoked to the participant's own realized earnings band (± .05),
re-matched each block. Instructions disclose exactly this provenance; no
deception anywhere in the protocol.

**Audit correction (post-I032, records/98_audit_I032.md).** The paragraph above
is not realizable as written, and the I027–I032 code did not implement it.
- *Infeasible HIGH source.* Every standard-schedule participant is deprived in
  P2: their P2-window rate is about .28 and their 450-trial rate about .44–.50.
  No pilot participant can supply a P2 window in [.60,.70]. The old code selected
  on the 450-trial rate, found nothing, and fell back silently to the first
  stream, a deprivation peer. With a real pilot pool, HIGH and LOW participants
  would both have seen deprivation peers in P2, so there would have been no
  manipulation at all.
- *Rich-rule pool source.* Truthful HIGH streams require **pool-source sessions
  under a rich rule** (.65/.35 in every phase, config `pool_rich`). This is
  disclosed by the existing "one of several rules used across sessions" line.
  A rich-rule participant reaches the .60 band only with accuracy ≳ .83, so pool
  size must be planned from the pilot (the pool tool reports, per block, how many
  streams qualify).
- *Selection rules as now built.* HIGH is selected on the stream's rate in the
  *current* block window. LOW draws a same-schedule stream (same restoration
  level) whose previous-block rate is within ±.05 of the participant's own
  previous-block rate. This is prospective yoking, and it is truthful.
- *Displayed statistic.* The board showed the peer's *cumulative* rate since
  round 1. For a LOW deprivation peer that averages about .50 during P2 (falling
  from .60 to .44), against about .28 for their actual P2 play. That would have
  kept only 31% of the HIGH−LOW reference gap the certified generator assumed
  (.10 against .33). The board now shows the peer's win rate over their last 15
  rounds, identically in both arms, matching the generator's references (own band
  under LOW, ~μ_ref under HIGH).
- **Author decisions** (§ Author decisions, audit report): the trader-board
  wording, given that HIGH peers played under a different rule (this also bears on
  how the global-rig Bayesian rival should read the peer); and pool-source size.

## 5. Measures

1. Choices per trial (behavioural accuracy = optimal-arm rate).
2. Fairness slider (primary legitimacy measure; rating = 100·L link stated as an
   auxiliary assumption, not a fact).
3. Entitlement slider (manipulation check + the ρ identification lever; slider-
   instrumented individual ρ, synthetic recovery r = .91).
4. Incentive-compatible legitimacy (new, preregistered secondary): at two fixed
   points (end of P2, mid-P3) a one-shot BDM option to pay from a dedicated
   20-point endowment to have the **random draws for the remaining rounds
   replaced with fresh draws generated the same way**. The screen states that
   the chances each ticket pays stay exactly as set and only the random draws
   change (I032 wording, TECHNIQUES.md #4). Truthful: the engine re-draws the
   remaining sequence at unchanged phase rates. With this wording a participant
   who believes the draws are fair values the switch at exactly 0, so a positive
   WTP reveals the belief that the draws are arranged against them. (The earlier
   "fresh rule" wording let WTP mix distrust with a belief that switching
   redraws the rates.) Stated maximum 0–20, price drawn uniformly 1–20, BDM
   dominance (Becker–DeGroot–Marschak 1964); unspent endowment paid out.
5. Manipulation/believability block (post-task): perceived peer success (1–7),
   perceived peer realness (1–7), rig-suspicion probe (1–7), betting
   familiarity (exploratory moderator), funnel debrief (free-text purpose
   guess), demographics.
6. Settlement forecasts (exploratory, pilot-gated): every 15 rounds
   (t mod 15 = 7) a minimal-information binarized-scoring-rule forecast of the
   **next** round's SQUARE settlement, one forecast paid at random. (I032 fix:
   the first build scored a forecast against the round just settled, which a
   SQUARE chooser had already seen.) Legitimacy is never elicited on a scored
   report.

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
recovery).

**H1b status after the I032 certification: OPEN, author decision before
filing** (records/95_pipeline_cert_I032.md). The frozen form above failed
certification in both directions. *Power:* at the design basis the
gate-vs-utility P3 dissociation compresses to about 2 slider points, inside
the 5-point band, so gate verdict power is 0.000 in every measurement shape.
It is also 0.000 at full scale. *(Erratum, post-close: not because the gate
declines in P3. Measured from the end of P2 it is flat, −3.9 points against
R3's +12.4. The frozen statistic's P2-mean baseline books the gate's
unfinished P2 collapse as P3 change; records/97_h1b_anatomy_I032pc.md.)* *Specificity:* a population with no gate in anyone (R3 types plus R4
types) passes H1a at .92, and the frozen H1b then declares the gate in 23% of
replicates. The pilot cannot fix this, because the defect is in the form of
the test, not in a constant.

The certified candidate, frozen before it was run (freeze I032 AD3/AD4), is
**H1b-SIc**. Restrict to HIGH × MODERATE participants whose P2 drop is above
the cohort median; compute c_i = (late-P3 − P2 fairness) − κ·(P1 − P2 fairness)
with κ = .25; reject H0: median c_i ≥ 0 by a one-sided Wilcoxon signed-rank
test at α = .005. The accuracy floor .70 still applies, and so does the
scale-free (iii): κ < R3's normalized recovery. Caveat (post-close anatomy): H1b-SIc inherits the P2-mean baseline, and at
the design basis its power leans on the gate's P2-collapse ramp, which any
slowly integrating rival would share; an end-of-P2 baseline is specific but
underpowered there (.27). Both need I033 certification against an
integrating-utility rival. Its ingredients are
attenuation-invariant (a subject's recovery is measured against their own
drop), and conditioning on high-drop subjects tests the gate's same-person
conjunction, which the composite rival cannot mimic. Certified results: gate
power .904–.966 across shapes under the attenuation reading and .948 in a
gate+R4 population; false positives .000 against pure R3 (both readings) and
.000 against the no-gate composite. Unconditional H1b-SI fails that last test
at .042. κ = .25 was fixed from latent ratios before the run; the sensitivity
κ = .40 raises the composite false-positive rate of the unconditional form to
.164, so κ is not a free dial.

Secondaries: H2 midpoint-lag dissociation; H3 Reference × Restoration
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
- Differential suspicion (I032, forced by the S7 addendum,
  records/power_free_s7.csv). Suspicion of the HIGH board is an *asymmetric*
  contamination and threatens the level of H1a, not just its power. At
  α = .005 the level holds within Monte Carlo error only while the residual
  load (q̂_H − q̂_L)·ŝ·(1 − π̂) stays ≲ 0.2 points, about 3% of the design effect.
  Here q̂ is the share flagged by the suspicion probe per arm, ŝ the drop
  inflation among the flagged, and π̂ the blind probe's capture rate. Rule: if
  the upper 80% bound of the pilot load exceeds 0.2, tighten the probe or revise
  the display before filing. The suspicion-exclusion cut (`SUSPICION_CUT`) is
  set from the pilot, blind to condition.
- Partial slider movers: the share of ratings left at the randomized start is
  measured; a partial-mover threshold (`UNMOVED_CUT`) is fixed before filing or
  explicitly left off. Complete non-movers are already excluded by the
  translated zero-movement screen (§6).
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

Per the preregistration draft: H1a null at sensitivity θ = .570 (≈ d = .25
under normality; I032 corrects the stale d-only wording) → reference-
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

Status (I032): all seven are built, together with the market skin and the
I032 additions: dose-cell configs, participant-level 2:1 assignment
(`main_confirmatory`), randomized slider starts, comprehension quiz,
next-round forecasts, sharpened WTP wording, and the ITI-jitter knob. The full
list is in `freezes/00_freeze_I032.yaml`. Bots pass on every bot config and on
the bandit-skin pilot arm. `pipeline.py` v2 implements the prereg tests; gate
G2 (agreement with the power engine) passed (records/g2_consistency.csv).

Audit additions (post-I032, records/98_audit_I032.md); all 17 session configs
pass the bots, and 23 tests pass.
- The forecast bonus promised in the instructions is now actually paid: one
  forecast drawn at random, 10 points with probability 1 − (o − f)². Before the
  audit it was announced but never paid, which is a truthfulness defect.
- The live engine survives page reloads. Block state persists server-side, a
  reload resumes with any owed rating, forecast or WTP screen, and duplicate or
  unsolicited submissions are refused. Before the audit a reload restarted the
  block counter and duplicated trials.
- Production guards: the secret key comes from the environment, and a human
  session without a real peer pool refuses to start rather than silently showing
  the simulated placeholder.
- Balanced permuted-block assignment (blocks of 6) in `main_confirmatory`.
- Payment aligned to §2: participation £4.20, £0.0035/point (~£1.10 expected).
  The I006 setting of £0.02/point would have paid ~£6.30 per participant.
- Export: config name, schedule, peer stream, ticket, betting familiarity,
  comprehension attempts, reloads, forecast bonus and payoff.
- `pipeline.py`: the confirmatory set is restricted by config, so dose,
  framing, pilot and pool sessions never enter H1a/H1b. H1b-SI, H1b-SIc and an
  exploratory end-of-P2 variant are computed and labelled beside the frozen form.

## 11. Timeline (indicative)

Build deltas 1–2 weeks, in parallel with ethics (2–4 weeks). Pilot: one week of
collection + one of analysis → constants frozen → OSF registration. Main run:
2–3 weeks in waves. Confirmatory analysis: push-button on the frozen pipeline
within days. Field project priors (PRIORS.md) issued from the lab posteriors
immediately after.
