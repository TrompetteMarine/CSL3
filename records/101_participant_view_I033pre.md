# The theory edge from the participant's side (pre-I033, 2026-11-09)

This is an exploratory record. It is model output, not data, and nothing in it
is a certification. Script: `experiment/analysis/pov_theory_edge_I033pre.py`
(seed 133100). It was committed with its questions before it ran, and it
reproduces bit-identically.
- Outputs: `records/pov_theory_edge_I033pre.{csv,txt}`, `figures/pov_theory_edge_I033pre.png`.
- Design variant: the board is held at the participant's arm in P3.
- Sample: n = 9000 per arm.

## What is on the screen

Each round the participant sees:
- two tickets with fixed quotes;
- whether their ticket paid;
- their total points;
- a windfall of +3 every 15th round;
- the trader board: the previous participant's last ticket, and that trader's
  win rate over their last 15 rounds.

Every 5th round they answer two sliders: "The market settles fairly"
(completely disagree to completely agree), and "What I deserve to win per
round" (nothing to the maximum). There is a next-round forecast every 15
rounds, and a re-draw offer at rounds 300 and 375.

**The participant's own win rate is never shown.** The comparison is therefore
asymmetric: an exact number for the peer against a felt rate for themselves.

## What they live through (per-phase means, from the table)

| | P1 | P2 | P3 MODERATE | P3 FULL |
|---|---|---|---|---|
| own wins per 15 rounds | 9.2 | 4.0 | 6.5 | 9.6 |
| board, HIGH arm | ~.63 | .65 | .65 | .65 |
| board, LOW arm | ~.63 | .28 | .43 | — |

- In P2 a HIGH participant wins about 4 rounds in 15 while the board shows 65%
  throughout.
- Under MODERATE restoration they win about 2.5 more per 15 rounds (≈ 60%
  more), but the board still shows 65%. The gap narrows from .39 to .22 and
  stays open.
- Under FULL restoration the gap closes.

These switches are large enough to be felt. The pre-stated
"rounds-to-half-way" metric came out at 6–7 rounds in every cell. That
reflects the mechanics of a 15-round window, not awareness, so it carries no
information about noticing. Noticing is left to the pilot debrief (PV5).

## What the theory says they report and do

The fairness slider at the theory's own link (a = 1):

| | P2 mean | late P3 |
|---|---|---|
| HIGH × MOD, gate (by edge) | 54–66 | 38–56 |
| HIGH × MOD, P0 paper point | — | 15 |
| HIGH × MOD, R3 | ~82 | ~92 |
| LOW × MOD, gate | 73–79 | 73–84 |
| HIGH × FULL, gate (crawls back) | — | 78–92 (58 at P0) |

At the minimum certifiable gain (a = .25) the same story spans only about
47–62 on the slider. P1 sits near 62, HIGH × MOD ends P2 near 47–49 and stays
there, and R3 returns near 60. **A participant with a = .25 who fully trusts
the market answers about 62 in P1.** Moderate P1 levels in the pilot are
therefore expected, not alarming. What matters is the depth of the HIGH × MOD
collapse in points (freeze I033 T7).

**Entitlement barely moves in the theory.**
- "What I deserve" goes from about 50 to 58 in P1.
- In P2 it is HIGH ~48–53 (phase mean) against LOW ~43–44. At the anchoring edge the gap is
  about 5 points.
- At a = .25 the gap is about 1.5–2 points.

So the entitlement slider is a weak manipulation check. The gate works through
entitlement built in P1 being kept up by the board, not through a new jump in
what people feel they deserve. Perceived peer success (post-task) is the
stronger check.

**Choices hardly differ between models.**
- The better-ticket share dips to ~.71 at the start of P2 and recovers to ~.8.
- Gate HIGH × MOD runs slightly higher in P3 (.81–.87 vs R3 ~.78–.79). This is
  perseveration from a lowered learning rate.

Choices do not carry the gate-versus-R3 test. The fairness slider does.

## Threats from the participant's side, and what the pilot reads (freeze I033, PV1–PV5)

1. **Gain.** People rarely use the whole slider, and starts are randomized every
   time. Read the HIGH × MOD depth in points against D* (T7).
2. **Never-movers and anchoring.** Many fairness answers, one every 5 rounds
   across 450 rounds, invite mechanical answering. Read the zero-movement share
   and the lag-1 autocorrelation of the P1 ratings.
3. **Asymmetric suspicion.**
   - A HIGH participant watches a peer win 65% while they win 27% for 150
     rounds. Under S7 the tolerance is only about 0.2 points.
   - The replay disclosure gives a true reason for the gap. Read the
     board-realness and rig-suspicion probes by arm.
4. **Slider meaning.** "Settles fairly" can be read as "same rule for everyone"
   (procedural) or "draws are honest" (rigging). The replay wording ("same payout
   rule as yours") removes the first reading of a HIGH–LOW difference. The
   re-draw offer separates the second: willingness to pay above 0 means the
   participant believes the draws are arranged against them.
5. **Demand.** Repeated fairness questions after losses invite hypothesis
   guessing, and a salient HIGH board could make it asymmetric. Read the funnel
   debrief by arm.
6. **Own rate not shown (author decision).**
   - Showing it would make the shortfall explicit and the same for every
     participant. It would also make phase changes more salient.
   - The model is unchanged either way, because own outcomes enter round by
     round.
   - A pilot split could test it.
7. **Unmodelled measures.** The theory makes no quantitative prediction for the
   forecasts or the re-draw offer. They are construct checks only.
