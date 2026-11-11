# Testing the theorems with people: what the market design satisfies and what it must measure (KGi-DISS-I040, 2026-11-11)

Everything in this record is synthetic. No assumption has been tested on
people. The record says which hypotheses the design satisfies, which are
assumptions about people, how each could be tested, and with what power.

- **Freeze.** `freezes/00_freeze_I040.yaml` was pushed before any run;
  addendum AD-T2 before its own run. Scorecards are verbatim in the freeze.
- **Scope.** Design S1x as simulated. The ten-repetition oTree build does not
  exist yet, so nothing here audits a deployed instrument.

## The ledger

Classes: **D** guaranteed by the design; **Dx** not guaranteed, fixable by a
design change; **H** an assumption about people, testable with the data the
design records; **Hx** testable only with a design change.

### T13, reference monotonicity

| hypothesis | class | what the simulation shows |
|---|---|---|
| outcomes are win or lose | D | settlements are binary |
| same outcomes in both arms | Dx | never in the design as it stands (independent draws). With yoked draws: in 41–73% of pairs, the ones that pick the same ticket every round |
| reference ordered at every settlement | Dx | in 56% of pairs. Broken at 0.44% of settlements, at the start of deprivation |
| equal starting state | Dx | holds for a yoked pair of identical agents; two people differ |
| a win never erodes fairness (`φ⁺ ≤ τ`) | H | see below |
| aspiration rises with the reference (K3) | H | entitlement rating, HIGH above LOW: power .89–1.00 at 36 per arm |
| legitimacy falls with aspiration (K2) | H in name only | within-arm association of entitlement and fairness: power .07–.25 at 72 per arm. Not testable at this scale |

- **Theorem check.** Among 30,656 simulated pairs that satisfy both design
  hypotheses, the conclusion holds at every settlement without exception.
- **The hypotheses are sufficient, not necessary.** They fail in about half
  the pairs, yet at the six round ends legitimacy is ordered in 99.6–99.7% of
  pairs.
- **Why the order breaks.** The LOW reference is the participant's own
  trailing record. For the first settlements of deprivation it still holds
  rich-round outcomes and can sit above the HIGH board.
- **Conclusion with people** (pairs of different people, rating noise 5.8):
  last fairness rating, LOW above HIGH. Power 1.00 from 18 per arm at P0–P3.
  At the anchoring edge .76 (yoked) and .71 (unpaired) at 18 per arm, .99 at
  36.

**If a win can erode fairness.** This is the hypothesis found while writing
the Lean proof. It matters:

| `φ⁺` | legitimacy at probe, HIGH / LOW | conclusion holds (pairs meeting the other hypotheses) | rating after the rich round | slope test rejects |
|---|---|---|---|---|
| .25 (frozen) | .11 / .87 | 100% | 70 | .01 |
| .5 | .03 / .71 | 29% | 69 | .59 |
| 1.0 | .00 / .52 | 97% | 32 | .97 |

- With `φ⁺` above the tolerance, the LOW arm also loses legitimacy (.71 or
  .52 instead of .87). LOW stops being a clean control.
- Two checks need no new measurement. One is the fairness rating after the
  rich round. The other is, within LOW, the slope of the round-to-round
  change in the fairness rating on the round's share of wins (rounds 4–6).
- A moderate violation (`φ⁺ = .5`) is invisible in the rich round and is
  caught by the slope test only 59% of the time at 72 participants.

**Ticket choice matters.** Removing the choice in deprivation makes outcomes
identical in every pair. It also changes the model's levels: LOW legitimacy
at probe time is .73 instead of .87, and HIGH at the anchoring edge .24
instead of .41. On the worse ticket the aspiration falls further and
legitimacy repairs sooner. A choice-free variant would need its own
certification.

### T6 and T7, the gain

| hypothesis | class | what the simulation shows |
|---|---|---|
| zero legitimacy can be identified | H | the third of HIGH with the lowest rating has an uptake ratio of .01–.05 under full coupling: the stratum is nearly pure |
| the gain depends on legitimacy only | H | not simulated. Free check: revisions after favourable and unfavourable records should be equal in size |

Decision "residual uptake in that stratum is below δ of normal" (upper limit
of the ratio below δ):

| | δ = .5, 72 per arm | δ = .25: 72 | 150 | 300 |
|---|---|---|---|---|
| one-update rule, full coupling | .90–.93 | .28–.33 | .60–.69 | .92–.96 |
| count rule, full coupling | 1.00 | .65–.84 | .96–1.00 | 1.00 |
| false decisions at coupling .75 (δ = .25) | | ≤ .003 | ≤ .002 | ≤ .001 |

### T8 and T15, state dependence

| hypothesis | class | what the simulation shows |
|---|---|---|
| given legitimacy, revision and rating are independent | H / Hx | a trait can link them; the conjunction with `ψ < 1` rejects that rival (I039) |
| both rise with legitimacy | H | follows from K1 and the rating |

Within HIGH, at 72 per arm, the best simple contrast is the top quarter by
rating against the rest: power .41–.53 at P1–P3 under the one-update rule
(.62–.80 under the count rule), against .29–.40 for the rank correlation. A
top-third against bottom-third contrast is worse (.17–.25). The association
sits in the recovered minority. Pooling both arms (I039) remains the
strongest: .64–.87. Three cuts were tried; treat the choice as exploratory.

### T10 and T11, the horizon

| hypothesis | class | what the simulation shows |
|---|---|---|
| same weight at successive records | Hx | needs tickets with two records |
| common starting error, constant evidence | Hx | same |

A two-record probe estimates the dispersion of weights from arm means.
Participants per arm to detect the excess dispersion in HIGH: about 3,400 at
the paper's values and 620 at the anchoring edge under the one-update rule;
about 100–200 under the count rule. The asymptotic figures are unreliable
(Monte Carlo power .81, .85 and .99 where .90 was targeted). The direct test of the
horizon theorems is out of reach at this scale unless people integrate
records by the count rule.

### T12 and T14

- **T12 (two types).** The model's own HIGH population is not two-type.
  Applied to it, the inversion returns the true coupling times a factor:
  .96–.995 at P0–P3, .90 at the anchoring edge, at every coupling. The factor
  is `E[(1 − l)²] / E[1 − l] ≤ 1`, so the inversion is a lower bound on the
  coupling for any distribution, and a tighter one than `1 − ψ` (analytic;
  not yet machine-checked).
- **T14 (`ψ ≥ 1 − c`).** Holds at every gate point and coupling under both
  revision rules (smallest margin 0, at `c = 0`).

## What the experiment should do (author decisions)

1. **Keep recording fairness and entitlement after every round.** They carry
   the tests of K3 and of `φ⁺ ≤ τ` at no cost.
2. **Yoke the settlement draws across arms in pairs.** It costs nothing, makes
   the same-outcome hypothesis hold whenever a pair picks the same tickets,
   and gives a small power gain (.76 against .71 at 18 per arm at the weakest
   point).
3. **Keep the ticket choice** unless a choice-free variant is certified.
4. **Report three stratified analyses** next to `ψ`: the freeze decision at
   δ = .5, the pooled association, and the `φ⁺` slope test.
5. **Do not add a two-record probe** before the pilot shows which revision
   rule people follow.
6. Optional: cap the LOW reference at the board level so the order holds at
   every settlement. The round-end ratings do not need it.

## Predictions that failed (kept)

1. References ordered in at least 95% of pairs: 56%.
2. Conclusion in at least 90% of all pairs at every settlement: 62–63%
   (99.7% at round ends).
3. A win eroding fairness raises the HIGH/LOW ratio: it lowers it, and breaks
   the order in most pairs at `φ⁺ = .5`.
4. Choice-free deprivation changes levels by at most .05: by up to .18.
5. K2 testable with power at least .70: .07–.25.
6. The `φ⁺` slope test at least .90 at `φ⁺ = .5`: .59.
7. Freeze decision at δ = .25 at most .30 under the one-update rule and
   .30–.80 under the count rule: .28–.33 and .65–.84.
8. Top-third contrast beats the rank correlation: it is worse; the
   top-quarter contrast beats it.
9. Two-type inversion within .05 at coupling .75: off by .08 at the anchoring
   edge.
10. Two-record probe at 200–1,000 per arm under the count rule: 97–204.

## What this rests on

- Power figures use the model as the truth, with the assumed rigidity mix,
  rating gain .5 and rating noise 5.8.
- Pairs of "different people" differ only in rigidity. Real people differ in
  more ways; the yoked-pair gain may be smaller or larger.
- The stratified tests condition on a rating taken after treatment. They are
  model-based readings, not causal contrasts.
