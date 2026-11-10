# The task as a behavioural game: where the equilibria are, and what is worth a lab (KGi-DISS-I036, 2026-11-10)

The freeze was written before the runs: `freezes/00_freeze_I036.yaml`. The
closing scorecard is verbatim there, including three of my own claims that the
runs refuted.

Records:
- `records/bgt.csv`: engine mode `bgt`, 300 runs per cell. A re-run is
  bit-identical.
- `records/bgt_I036.txt`: the analysis output.
- `experiment/analysis/bgt_I036.py`: the analysis script.

The engine gained two switches, `gate_own` and `gate_soc`. Their defaults
reproduce the frozen engine, and the validation gate is unchanged.

## The game (read from the engine, not assumed)

- **Players and payoffs.** Two communities of 100. Each trial every agent picks
  one of two options paying with probability .6 or .4. Nobody's payoff depends
  on anyone else's choice.
- **Choice rule.** Agents choose by a logit rule with conformity:
  P(better) = σ(12·[ΔQ + λ·(S_better − S_worse)]). S is the confidence-weighted
  share of last trial's choosers; own community has weight 1 − Γ and the other
  community Γ.
- **Legitimacy and choice.** Legitimacy does not enter the choice rule.
- **Legitimacy and learning.** Legitimacy scales learning on both channels:
  from own outcomes, and from the observed outcomes of others.

This is a discrete-choice game with social interactions in mean-field form
(Brock & Durlauf 2001). The coupling is λ(1 − Γ) and the field is the perceived
payoff gap ΔQ. The solution concept is a logit (quantal-response) equilibrium
(McKelvey & Palfrey 1995). The gate acts on how the field is learned, not on
the best response.

## Where the equilibria are

**Mean-field fixed points (numerical).** Correct consensus is always an
equilibrium. Wrong consensus is an equilibrium only while the perceived payoff
gap is below a tipping value ΔQ*:

| conformity λ, exposure Γ | tipping gap ΔQ* | reading |
|---|---|---|
| .7, .1 (paper cell) | .200 | equals the true gap (.2): correct beliefs just dissolve the wrong consensus |
| .7, 0 (isolation) | .330 | above the true gap: conformity alone holds it even under correct beliefs |
| .7, .3 (open) | −.055 | a small belief correction tips it |
| .3, .1 (weak conformity) | −.025 | likewise |

Agents start with a perceived gap of −.24. The wrong consensus therefore lasts
exactly as long as learning fails to move the perceived gap up to ΔQ*.

**Census at the paper's configuration (share of 300 runs, community 2 at the horizon).**

| cell | wrong, distrusting | wrong, trusting | correct, trusting | correct, distrusting |
|---|---|---|---|---|
| paper cell, gate on | .840 | 0 | .013 | .147 |
| paper cell, gate off | 0 | 0 | 1.000 | 0 |
| neutral entitlement (A0 .5) | 0 | 0 | 1.000 | 0 |
| weak conformity (λ .3) | 0 | 0 | 1.000 | 0 |
| isolation (Γ 0), gate on or off | 0 | 1.000 | 0 | 0 |
| open (Γ .3) | 0 | 0 | 1.000 | 0 |
| paper cell, four times the horizon | 0 | 0 | 1.000 | 0 |

There are three kinds of rest point.

1. **Correct consensus.** The only long-run outcome whenever evidence gets in.
2. **Credulous wrong consensus under isolation.** Nobody ever observes the
   unchosen option. This is a self-confirming equilibrium in the standard sense
   (Fudenberg & Levine 1993), it does not need the gate, and it is the cascade
   logic already demonstrated in the laboratory (Anderson & Holt 1997).
3. **Defensive wrong consensus.** Evidence is available on both channels but
   is not taken up. This is the paper's new object. It is metastable, not
   permanent: it is gone at four times the horizon.

## What holds the defensive equilibrium up (ablation, paper cell)

| legitimacy scales… | wrong consensus | correct, distrusting | correct, trusting |
|---|---|---|---|
| both channels (paper) | .840 | .147 | .013 |
| own-outcome learning only | **0** | .817 | .183 |
| others'-outcome learning only | **0** | .213 | .787 |
| nothing (legitimacy still moves) | 0 | .200 | .800 |

**Either open channel is enough to escape.** The trap needs evidence from own
outcomes AND from others' outcomes to be discounted together.

Before the run I claimed that own-outcome gating alone would hold the trap, on
a "learning noise" account. That was wrong, and so was my claim that the wrong
consensus survives correct beliefs at the paper cell. Both are recorded as
refuted.

When only own-outcome learning is gated, behaviour corrects while distrust
persists. This is the paper's "correct but illegitimate" regime, obtained here
by ablation.

## The minimal mechanism worth a lab

Conformity, bistability and cascades under missing information are established
and can be left to the ABM and the literature. The one link that is new, that
carries the paper's equilibrium, and that only humans can settle is this:

> after reference-dependent delegitimation, a person revises beliefs less in
> response to evidence, both from their own outcomes and from others' outcomes.

The link is an individual updating rule, so no group is needed in the lab. The
ABM computes the collective consequence.

It also has the right signs against the rivals:
- the gate predicts less revision in HIGH than in LOW;
- the utility rival predicts no difference, because legitimacy is not in its
  learning rule;
- the slow-reporting variants of the utility rival predict no difference for
  the same reason;
- the group-contingent rival predicts no arm difference;
- the global Bayesian rival predicts the opposite sign.

It is a behavioural, payable measure (a forecast before and after a small
evidence sample). The slider-gain problem and the slow-reporting rival
therefore do not arise.

**Cost, from the simulation.** The probe is appended after the deprivation
rounds of the ten-round task. Revision weight is 1 − (1 − .2·L)^m, forecast
noise is assumed at sd 12 per report, and the worst theory-edge point is used.

| design | evidence leverage | one probe, n per arm | three probes, n per arm |
|---|---|---|---|
| 25 draws per round | .4 | 847 | 333 |
| 40 draws per round | .4 | 348 | 176 |
| 40 draws per round | .8 (post hoc) | 156 | 108 |

- The best evidence sample is about 7–10 draws.
- The effect is modest because a ten-round deprivation only opens a legitimacy
  gap of about .4–.5 against .7.
- Leverage (how far the evidence sits from the prior) and the number of probes
  are the levers.

## Limits

- The revision rule and the noise figure are model assumptions about humans,
  not measurements.
- The probe was not simulated with a rival-specific measurement layer. The
  rivals' zero differences follow from their learning rules by construction.
- Disengagement would also lower revision. It needs its own control: an
  attention check on the evidence, or a second, unrelated source.
- The paper cell sits exactly at the tipping gap (.200 against a true gap of
  .2). The headline trap is therefore sensitive to conformity strength as well
  as gate speed. This is flagged for the author, and the manuscript was not
  edited.
