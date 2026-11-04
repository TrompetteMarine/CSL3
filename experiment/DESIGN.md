# Task v3 — experimental design and ethics-readiness note (KGi-DISS-I006)

Status: implementation complete and bot-validated; **for author review before OSF
registration and ethics submission**. The governing scientific document is the
preregistration draft (I003/M4); this note records how the built instrument realizes
it, the decisions the prereg left open, and the gates still ahead.

## 1. Instrument

oTree 6 app `diss_bandit` (project `diss-otree/`): two-armed bandit, 450 trials in
three 150-trial blocks delivered on three live pages (no page reload per trial),
~28 min. Phases (invisible): P1 (.65/.35), P2 (.30/.15), P3 restoration per Factor B.
Announced non-contingent bonus (+3 points) every 15th trial. Yoked peer-earnings
panel on every trial. Every 5th trial, two sliders: fairness ("the payout rule is
fair", 0–100) and entitlement ("what I deserve to earn per choice", 0–100 = % of
max). Side assignment of the better arm counterbalanced per participant; outcome
sequences pre-generated per participant from a session seed (reproducible, CRN-style).

## 2. Factors and cells

- **Factor A (reference regime of the P2 block)**: HIGH (yoked peer in the .60–.70
  earnings band) vs LOW (peer matched to own trailing 15-trial band ±.05). P1/P3
  block regimes counterbalanced at participant level; the primary contrast is the
  P2-block regime, per the prereg.
- **Factor B (P3 restoration)**: FULL (.65/.35) vs MODERATE (.45/.35).
- 4 cells × 320 post-exclusion (power: prereg §3, d = .25 floor, α = .005) + pilots.

## 3. No-deception yoking

The peer panel replays an *actual* earnings stream of a prior participant. Production
pool: streams harvested from pilot/earlier sessions, keyed by realized hit-rate band;
HIGH draws from the .60–.70 band, LOW matches the participant's own trailing band at
each block boundary. The instruction line "the payout rule used in your session is
one of several rules used across sessions" is made true by running separate
throwaway sessions with alternative rules. The development pool shipped in the repo
is bot-generated and **flagged `placeholder: true`**; it must be replaced by the
harvested pool before any session whose data will be analyzed.

## 4. Payment

Points = earned rewards + bonuses (expected ≈ 290–330 points over 450 trials).
Default conversion £0.02/point + £2.00 participation fee ≈ £8–9 for ~28 min
(≈ £17–19/hr), within Prolific fair-pay guidance. Rates are settings-level
parameters; final values are an author/ethics decision.

## 5. Exclusions (enforced in the analysis pipeline, never silently in the app)

Completion < 90% of trials; zero variance on both sliders; P1 accuracy below
chance + 2SE (enforced for human data; flag-only on bot smoke runs); median choice
RT < 300 ms. Every exclusion is written to the pipeline's audit log with its reason.

## 6. Pilot gates (before main data collection)

1. **MODERATE calibration (Factor B)**: MODERATE = (.45/.35) is an I006 design
   decision, not prereg-frozen. Pilot check: elicited late-P2 entitlement should
   typically sit *above* .45 ×100 on the slider scale, so that MODERATE restoration
   lands near the resignation boundary (theory: reopening time diverges there).
   Adjust within (.40–.55) on pilot evidence only, before registration.
2. **H5 cell**: the equal-misery (EQUAL) regime is pilot-gated per the prereg; the
   pipeline detects its absence and reports it as such.
3. **Yoked-pool coverage**: pilot must produce enough streams in the HIGH band and
   across LOW bands; otherwise band tolerances widen (documented change).
4. **Timing**: confirm ≈ 28 min median with the second slider.

## 7. Analysis pipeline (frozen logic, built and smoke-tested)

`analysis/pipeline.py` implements H1 (primary, Welch, α = .005), H2
(recovery-midpoint lag, censoring at 450 = no recovery), H3 (regime × restoration
on P3 rating slope; refuses incomplete crossings), H4 (MixedLM increment asymmetry
against elicited entitlement shortfall), H5 (runs only if the EQUAL cell exists),
and the model-free aspiration-rigidity moderator (slider-adaptation coefficient).
Computational layer per prereg §7: individual ρ preregistered (aspiration slider is
in the instrument); no individual claims about (ν_F, ν_R, τ^F); ν_R excluded even at
group level; model comparison exploratory only. Operationalizations the prereg left
open are marked `DESIGN-DECISION` inline in the code.

## 8. Validation record (I006 gates)

- `otree test` completes full 450-trial sessions for all bot configs (random and
  DISS-gate bots; the DISS bot runs the frozen I002 defaults ν_F=.05, ν_R=.0125,
  τ^F=.3, φ=(1,.25), α=.2 with slow/fast ρ and χ ∈ {0,.6} variants).
- Custom export schema validated: 450 trial rows + 90 rating rows per participant.
- Pipeline runs end-to-end on the combined bot export and emits the smoke report
  (labeled BOT DATA); DISS bots show the qualitative signature (mean fairness
  82.7 → 41.5 → 30.9 across phases) — a sanity check on plumbing, not evidence.

## 9. Open author decisions before registration

MODERATE value (pilot gate 1); payment rates; comprehension-check items (not yet
written); Prolific screening criteria; ethics text (information sheet + consent
wording beyond the in-app consent); OSF registration of the prereg draft with the
§7 identification fallback as already frozen.
