# I024 exploration report — the fresh confirmatory battery for the window

Status: exploration complete, manuscript untouched (explore-before-writing). Design,
seeds, predictions and bands frozen in `00_freeze_I024.yaml` before any run; the
mnet2 engine path passed an exact-reproduction gate (40/40 rows of the I021
confirmatory-adjacent cell, bit-identical) before any battery output was used.
Records: `mnet2_cells.csv` (1,740 runs, 51 cells), `mnet2_comm.csv`,
`mnet2ad_*.csv` (addendum, 5 cells). Companion document:
`94_referee_implementation_plan_I024.md` (the round-3 implementation analysis).

## Headline

The window survives its first genuinely out-of-sample test, in sharpened form.
Three things changed shape, and all three make the theory better:

1. **M-invariance at fixed n is confirmed everywhere — "corrects at scale" is
   dead as an M-claim.** With community size held at n=100, trap fractions are
   M-invariant from 10 to 1,000 communities in every exposure-matched family
   (max drift 0.076); broadcast at M=1000, n=100 traps 1.000 (vs 0.000 at n=10 in
   I021), ring-scattered likewise. The n=10 cascade regime is itself M-invariant
   (0.085/0.096; broadcast 0/0.44–0.49). Scale does nothing; community size does.
   This was pre-stated in R8's direction against our own v10 phrasing, and it held.

2. **The upper edge is sharp everywhere but its location is
   architecture-dependent inside a narrow band; the envelope is clean.** Every
   w_in sweep shows a one-grid-step transition. Locations: M=2 singleton edge in
   (0.100, 0.1125] (the addendum edge cell corrects at x=0.1125); M=100
   ring-scattered in (0.075, 0.100]; M=100 broadcast in (0.076, 0.101]. So:
   trap is certain below x ≈ 0.075, escape is certain above x ≈ 0.1125 in every
   architecture tested (pooled at matched n: P(escape | x ≥ 0.1125) = 0.993), and
   inside the band cascade multiplicity decides — many losing communities escape
   at lower structural exposure than one big one, because any fellow loser that
   corrects adds corrective field beyond x. The I021 pooled x_B ≈ 0.11 is the
   singleton edge / upper envelope. P4 passed as frozen; P5 and P6 failed as
   frozen (edges one grid step below the claimed locations) — these are honest
   failures whose pattern is the refinement above. The broadcast inequality
   mechanism itself held: broadcast flips exactly when weight x winner-share
   crosses the (architecture's) edge.

3. **The t* clock is a reopening clock, not a resolution clock — the trap has
   TWO clocks, and the second is now confirmed out of sample.** P7 failed as
   frozen: all three rhoT >= 2.0 cells were still fully trapped (with legitimacy
   visibly recovering: L-bar 0.14–0.17). Diagnosis from the same drift algebra,
   no fitting: after the gate reopens at t*, repair is throttled by the
   continuing failure stream — dL/dt = nuR·mu2 − nuF(1−mu2)(A(t)−tau_F) with A
   still decaying on the rho clock — so classification-level resolution happens
   at a second closed-form time t** (L crossing the threshold), about 1.4–1.5x
   t*. This two-clock account was frozen as addendum 1 with three claim cells
   and one calibration cell BEFORE running: all three claims passed
   (trap 1.000 at T=1100; 0.000 at T=1600 with cred 0.922; 0.000 at
   rho=0.0015, T=2100), and the calibration cell puts empirical t**(rho=0.002,
   x=0) at ~1250–1300. The I022 manuscript sentence "t* ... predicts both
   battery outcomes with nothing fitted" OVER-CLAIMED: t* < T is necessary for
   resolution, not sufficient. The battery caught our own error — which is what
   it existed to do.

## Scorecard (frozen predictions, verbatim)

- P1 M-invariance (exposure-matched families): **PASS** (all bands met). The
  side-claim "clustered >= 0.9 at all M" **FAILED for ws1-clustered**
  (0.755/0.771/0.764) — a prediction-writing error: full rewiring destroys
  clustering, so ws1-clustered belongs in the invariance family, where its max
  drift across M is 0.016. Ring-clustered: 1.000 at every M as claimed.
- P2 decisive anti-"corrects at scale" cells: **PASS** (1.000/1.000/1.000).
- P3 cascade regime M-invariant at n=10: **PASS**.
- P4 M=2 threshold grid: **PASS** (trap 1/1/0/0/0 across x = .05/.10/.125/.15/.20).
- P5 M=100 scattered w_in sweep: **FAIL as frozen** — escape already at x=0.100
  (trap 0.100), edge in (0.075, 0.100]; sharp step confirmed, location shifted.
- P6 broadcast inequality: **FAIL as frozen** — trap 0.072 at x=0.1010; edge in
  (0.076, 0.101]; the flip mechanism confirmed, location shifted (same direction
  and cause as P5: cascade multiplicity).
- P7 (rho,T) hyperbola: **FAIL as frozen** — rhoT <= 1.6 cells all trapped (that
  half passed), rhoT >= 2.0 cells ALSO all trapped. Superseded by the two-clock
  account; addendum AD1–AD3 all **PASS**, calibration k ~ 1.4–1.5.
- P8 resolution split: **FAIL** at the C-arm cells (consequence of P7 — nothing
  resolved there); the addendum's resolved cells show the split (cred 0.92/0.85
  of losing communities, with the correction front reaching only a minority by
  those horizons).
- P9 pooled window overlay at matched n: **PASS** (0.5-crossing in [0.095, 0.100);
  P(escape | x >= 0.1125) = 0.9932).

Five of nine frozen predictions passed as written; the four failures are each
absorbed by one of two refinements (edge-location band; two clocks), and the
second refinement was itself confirmed out of sample within the iteration.

## The two-level law, quantified (from the I021 records, R8's demand)

Conditional on community size, structural exposure is a near-step function:

| x bin | n=10 | n=100 | n=1000 |
|---|---|---|---|
| [0, .02) | .991 | 1.000 | 1.000 |
| [.02, .05) | .910 | 1.000 | 1.000 |
| [.05, .08) | .196 | .996 | .995 |
| [.08, .11) | .042 | .889 | .993 |
| [.11, .15] | .000 | .006 | .008 |

Run-split AUC for community fate: x alone 0.917; x + log n 0.962; adding
geometry dummies 0.972 — geometry adds almost nothing once x and n are in,
which is the window account's "geometry acts only through x" stated predictively.
The pooled curve's graded middle was composition (Simpson-style), as R8 said.

## Consequences for v11 (queued, not yet applied)

1. Window section and S13 recast as the two-level, two-clock law: structural
   exposure locates the edges (trap-certain below ~0.075, escape-certain above
   ~0.1125, cascade multiplicity deciding inside); community size selects within
   the window; t* (reopening) and t** (resolution, ~1.4–1.5x t*) replace the
   single-clock sentence — the I022 "predicts both battery outcomes" claim is
   corrected explicitly.
2. "Corrects at scale" retired; broadcast correction stated as the n=10 cascade
   effect it is, plus the confirmed weight-x-share flip mechanism.
3. The stratified table + AUC numbers carry the "one variable" recast; abstract
   drops "certain" for the horizon-indexed envelope phrasing.
4. All data now exist for the S13.6 out-of-sample confirmation subsection that
   answers R8's M6 — the window's laws were pre-stated this time, and where they
   failed, the failures and their refinements are reported.

## Honest limits

All thresholds remain at the frozen defaults and block-uniform exposure; the
within-community dispersion sweep (the class boundary R8 M7 / R9 M5 ask for) is
deliberately NOT in this battery and is the natural I025. The t** closed form is
exact for the mean path of the interior (x=0) community; its multiplier
k ~ 1.4–1.5 (agent-level aspiration spread) is calibrated, not derived — deriving
it is a small, well-posed theory item. The edge-location dependence on cascade
multiplicity is characterized empirically (three architectures); its closed form
is open.
