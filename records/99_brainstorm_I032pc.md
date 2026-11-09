# Post-I032 brainstorm: trader board, quantile attribution, H1b and dose (2026-11-09)

Exploratory record. Nothing here changes a frozen record or the build. Every
number comes from a committed script with a fixed seed, and every option needs
a freeze and certification (I033) before it can enter the preregistration.
Scripts (all `experiment/analysis/`): `explore_peer_source_I032pc.py` (seed
132950), `explore_h1b_candidates_I032pc.py` (132960),
`explore_reversal_strength_I032pc.py` (132970), `explore_p3_regime_I032pc.py`
(132980). Outputs: `records/{peer_source,h1b_candidates,reversal_strength,p3_regime}_I032pc.txt`.
Context: the superseded Social Cognition storyboard v0.81 (public board with
best/mean/worst track records, live circle traders, world-change vs
source-change 2×2) was read as an input to item 1.

## 1. Trader board and peer source

**Sizing.** Pool streams are proxied by Q-learning softmax agents (β = 12, the
frozen value, and β = 6, a noisier human-like bracket). The table gives the
displayed level during the participant's P2 (rounds 151–300). The participant's
own P2 rate is .25–.26.

| Option | p50 | p75 | p90 | share ≥ .60 |
|---|---|---|---|---|
| O1 same schedule, person-level on P2 window | .25–.26 | .28–.29 | .30–.32 | 0 |
| O2 same schedule, rolling top-decile index over 40 streams | — | — | .42–.44 | — |
| O3a replay of a standard stream's P1 stretch | .59–.61 | .63–.65 | .65–.67 | .47–.66 |
| O3b order-shifted pool session (P2-P1-P3) | .61–.64 | .64–.67 | .67–.69 | .58–.80 |
| O4 rich-rule pool session (current build) | .61–.63 | .64–.67 | .67–.69 | .57–.78 |

**Gate threshold.** With frozen constants the gate delegitimates in P2
asymptotically only if the displayed reference exceeds .474 (χ weight .6) or
.576 (χ weight .4, the D4 companion).

**H1a power against the HIGH level μ_ref.** M2 measurement at a = .0578,
asymptotic one-sided WMW at .005, n = 320/arm. The generator's reference is the
peer's cumulative rate, so below .60 these numbers are upper bounds for a
trailing-15 display.

| μ_ref | .35 | .40 | .45 | .50 | .55 | .60 | .65 |
|---|---|---|---|---|---|---|---|
| gate θ | .540 | .548 | .559 | .565 | .579 | .588 | .593 |
| power | .20 | .32 | .51 | .60 | .82 | .90 | .94 |
| R3 power | .04 | .04 | .05 | .07 | .09 | .10 | .20 |

**Construct finding.** The rich-rule build together with the "one of several
rules used across sessions" line creates a rival that no generator contains.
Call it R5, correct rule inference. A HIGH participant can correctly infer that
the peer's rule is better and rate the market less fair for a true distributive
reason, with no reference mechanism involved. A same-rule source removes R5 by
construction.

**Proposed: same-rule replay board.**
- *HIGH:* a stretch from the rich block (P1) of a standard-schedule participant
  with the same restoration level, replayed during the participant's P2. It is
  selected on a pre-registered level band of the displayed window and sampled
  uniformly within the band.
- *LOW:* the synchronized yoked stream, as built.
- *Wording, identical in both arms:* "The board replays a stretch of rounds
  played by a previous participant under the same payout rule as yours. The
  stretch may come from a different point in their session than the round you
  are at."

Effects:
- No pool-source sessions are needed, because standard-schedule pilot
  participants are the pool.
- The procedure is ex ante identical for the participant and the peer. A
  fairness drop therefore cannot be a justified complaint about the rule
  (procedural vs allocation fairness: Bolton, Brandts & Ockenfels 2005; ex ante
  vs ex post: Cappelen et al. 2013).
- There is no omission-type gray zone (Charness, Samek & van de Ven 2022:
  researchers' views on omission and "misleading without lying" vary widely).
- The gap has a stated, true explanation, which plausibly lowers differential
  suspicion in HIGH. That matters because S7 tolerates only about 0.2 points.

Risks:
- The "different point" disclosure may weaken the comparison. Social comparison
  is drawn to similar others (Festinger 1954).
- The pilot checks this with entitlement H vs L in P2, which measures
  aspiration anchoring directly, plus perceived peer success and realness.

Bootstrap: the first pilot wave needs prior streams. Run a seed wave on the
standard schedule; beta-tester streams are dev-only.

**Rejected or dominated.**
- A distribution board (storyboard best/mean/worst): same-schedule quantiles sit
  below the gate threshold, and rich entries multiply pool needs.
- Live peers: same-time peers cannot be HIGH in P2 without different rules.
- Order-shifted sessions: same levels as replay, but they need special sessions.

## 2. Quantile attribution (p90)

- *As a level rule within the same schedule:* no. O1 gives .30–.32 and O2
  .42–.44, below the gate threshold, so H1a power is ≤ .2–.5.
- *As a sampling rule within rich stretches:* unnecessary at p90, because p50–p75
  already gives .59–.65.

Recommendation:
- Pre-register a **level band**, because the gate responds to the level of the
  reference, with a threshold, and H1a power falls steeply below .55.
- Report the realized quantile.
- Sample uniformly within the band.
- Cap reuse per stream, log `peer_stream_id` (already exported), and add the
  stream as a crossed random factor in robustness (Judd, Westfall & Kenny 2012).
- Do not label the peer "top 10%". That makes the peer a dissimilar comparison
  target.
- Card et al. (2012) find that rank matters more than level for satisfaction.
  That points to a rank board as a different manipulation, not a fix for this
  one.

## 3. Payment

Parked by the author (beta-testing stage). Beta configs must stay outside
`CONFIRMATORY_PREFIXES`, and beta exports outside the peer pool.

## 4. H1b and the dose module

**Latent restoration responses (×100, MODERATE).**

| model | drop_H | rec (P2-mean base) | rec_end (end-P2 base) | SI c, P2-mean | SI c, end-P2 | H−L rec_end | H−L, reference held fixed |
|---|---|---|---|---|---|---|---|
| gate | 43.5 | −32.5 | −2.8 | −47.2 | −13.4 | −7.4 | −13.8 |
| R3 | 18.5 | +12.8 | +12.4 | +10.0 | +9.4 | +6.5 | +3.6 |
| R4 | 2.6 | −34.8 | −23.7 | −41.8 | −21.0 | 0.0 | +0.1 |
| R3-int η=.02 | 12.9 | +5.9 | +10.4 | +3.6 | +8.4 | +3.7 | — |
| R3-int η=.01 | 9.0 | +0.4 | +5.4 | **−1.7** | +3.7 | +1.2 | — |
| R3-int η=.005 | 5.5 | −2.5 | +1.3 | **−4.4** | −0.1 | −0.3 | — |

Notes on the table:
- R3-int is an integrating-utility rival: reported fairness is the EMA of R3's
  instantaneous satisfaction. Its SI c with the P2-mean baseline goes negative
  for η ≤ .01, so H1b-SIc in its certified form is **not specific** against
  slow integrators. It is protected only by the H1a gate, and only while the
  integrator's reference effect stays small.
- The end-of-P2 baseline is specific (≥ −0.1), but at a = .058 its power is .27
  (anatomy record).
- The between-arm restoration contrast has opposite signs (gate negative, R3
  positive, R4 zero). It is randomized and composite-proof by sign, but small
  in latent units.
- Holding the reference fixed across restoration (P3 regime = arm) almost
  doubles that contrast for the gate (−13.8) and makes restoration a single
  interruption (Bernal et al. 2017: the impact model is pre-specified; time-varying
  confounders are a key issue).

**Reversal probe.** Here the better ticket swaps at t = 300.
- Under the frozen gate: late-P3 correct rate HIGH .374 vs LOW .619. R3 shows
  .624 vs .626, and R4 .569 vs .567.
- Halving the gate's delegitimation rate removes the contrast entirely (−.003;
  power .008).
- Inequity itself slows reward learning (Ham & Jenkins 2025, verified I032
  audit), so a learning deficit is not gate-specific.
- **Rejected** as an H1b form.

**Structural diagnosis.** Under the attenuation reading (a ≈ .05–.06) every
specific H1b form is power-starved. The powered form borrows the P2 ramp, and
slow integrators share that ramp.

Proposed:
- (i) Hold the reference fixed across restoration.
- (ii) Make the H1b form a pre-stated function of the **pilot-estimated slider
  gain â**. Pilot outputs are design constants (DESIGN §7). If â ≥ â*, H1b is
  the specific form, either the end-of-P2 SI or the between-arm fixed-reference
  contrast. If not, the H1b fairness test is filed as a secondary with an
  honest power statement. I033 computes power-vs-gain curves to set â*.
- κ keeps its fraction-retention rationale. It is the analogue of preserving a
  fraction of M1 when setting an M2 margin (FDA 2016 non-inferiority guidance).
- The serial gate is an intersection–union test (Berger 1982). The IUT controls
  the conjunction, but the same-person part needs drop conditioning.

Model-based alternatives:
- RFX-BMS model frequencies (Rigoux et al. 2014) need model and parameter
  recovery first (Wilson & Collins 2019).
- Prevalence inference (Ince et al. 2021) needs per-person tests, which are
  infeasible at this gain.
- Both are exploratory.

**Dose module.** Drop it from confirmatory.
- E6 failed. The in-session dose response is linear (|C|/|span| ≤ .02 on the
  P2 drop), and the step is asymptotic only.
- The post-hoc slope signature is the restoration contrast across μ_ref. With a
  late-P2 baseline the gate goes +0.6/−6.9/−14.3 against R3's +11.2/+12.1/+12.8.
  At a ≈ .06 that is about 1 point across the range, in n = 90 cells.
- If it were kept, the form would be a Jonckheere (1954) trend test.
- Reallocate the 180 to HIGH×MODERATE only if â makes the specific H1b form
  benefit from n.

## I033 candidates (freeze first)

1. Add R3-int to the generator set.
2. Certify the fixed-reference design with the end-P2 SI form and the
   between-arm contrast, as power-vs-gain curves.
3. Run the replay-board feasibility check on pilot-like streams.
4. Set the â* rule.
