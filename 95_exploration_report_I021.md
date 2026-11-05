# I021 exploration report — the M-community generalisation

Status: exploration complete, manuscript untouched (explore-before-writing). Design,
seeds and predictions frozen in `00_freeze_I021.yaml`; records `mnet_cells.csv`,
`mnet_comm.csv`, `mnetT.csv` (1,740 runs; 266,400 community-level records). The new
M-block engine path passed its pre-stated validation gate against the confirmatory
cell before any battery output was used.

## The central finding: an exposure window with a horizon clock

One community-level quantity governs fate at every scale from M = 2 to M = 10,000:
a losing community's cross-exposure to corrected communities,
x_c = Σ_{d corrected} W_cd. Pooled over every geometry, size and placement:

| x_c | P(trap) at T=600 | P(cbi) | n records |
|---|---|---|---|
| [0, .02) | 0.991 | 0.004 | 76,639 |
| [.02, .05) | 0.921 | 0.032 | 15,765 |
| [.05, .08) | 0.276 | 0.302 | 141,981 |
| [.08, .11) | 0.154 | 0.279 | 17,384 |
| [.11, .14) | 0.001 | 0.219 | 6,984 |
| [.14, .15] | 0.000 | 0.056 | 7,647 |

The behavioural threshold sits at x_B ≈ 0.11 (P(escape | x ≥ 0.1125) = 0.999). The
lower edge is the horizon clock: at x ≈ 0 the reference is shielded, aspiration
adapts on 1/ρ, and the T=2400 rerun resolves every T=600 "trap" — 45% into credulous
resignation (L̄ = 0.98, behaviour still wrong), the rest corrected. So the
two-community regime map generalises exactly as a window: below the window,
resignation on the ρ clock; inside it, defensive wrong consensus for horizons long
relative to 1/ρ; above it, correction with the legitimacy lag (the
correct-but-illegitimate transit). Geometry and M matter only through the
distribution of x_c they induce and through community size n, which seeds
fluctuation cascades.

## Headline rows

- Ladder (ring, clustered, N = 10,000; M = 10,000 at N = 100,000): trap ≈ 1.000 at
  every M ≥ 10 — harder than the two-community 0.843, because clustered interiors
  have x ≈ 0 and are reference-shielded at the horizon. The Γ = 0.1 two-community
  anchor at n = 5,000 traps 20/20: the confirmatory cell's escapes were pure finite
  size, as the scaling analysis claimed.
- Scattered losers at M = 10/100 stay trapped (deg-4 alternation puts every loser at
  x ≈ 0.075, inside the window) but correct at M = 1000 (n = 10 noise seeds escapes
  that cascade: trap 0.10, cbi 0.37). Scattering is not enough; scattering plus
  small communities is.
- Broadcast at M = 1000, n = 10: trap 0.000, behaviour fully corrected, and 45% of
  losing communities corrected-but-illegitimate at T=600 (L̄ = 0.31) — the
  behaviour/belief dissociation at 10,000-community scale. At M ≤ 100 (n ≥ 100)
  broadcast traps completely: the common field spreads whatever corrects, and
  nothing corrects without fluctuation seeds.
- Barabási–Albert: P(trap) is FLAT in meta-degree (0.62–0.71) — hubs do not escape
  because degree does not move x; the composition of neighbours does.
- Unequal sizes: the big loser among nine small winners has x = 0.15 and corrects;
  nine losers around one big winner have low x and trap. Exposure composition
  dominates size.

## Prediction scorecard (frozen before running)

P1 partial (trap survives everywhere at horizon; the n-dependence appears through
cascades, not interiors). P2 pass (the window regression). P3 fail at M = 10/100,
pass at M = 1000 — the window explains both. P4 fail (degree flat; x, not degree).
P5 fail at M = 1000 (broadcast corrects via common-field cascades), pass at M ≤ 100.
P6 fail as stated (composition, not size). Five informative failures, all absorbed
by one account — which is what makes the general theory writable.

## What the general theory section can now say (proposed, for your go-ahead)

1. Setup: M communities, sizes n_c, row-stochastic exposure matrix W; the
   block-aggregation identity of the companion framework licenses community-level
   fields at any M, including unequal sizes. B(Γ) is the two-community worked
   example.
2. The window proposition: a losing community's closure condition at the
   equilibrium reference reads χ·x_c·(μ₁−μ₂) > A*(μ₂)−μ₂ on the grievance side,
   against a behavioural correction threshold x_B set by the field; defensive wrong
   consensus occupies x_c ∈ (window), credulous resignation below, correction with
   the 1/ρ legitimacy lag above. Two-community Γ-sweeps are the one-parameter slice.
3. The horizon clause: inside the window, persistence is horizon-indexed exactly as
   in the two-community analysis (T=2400 resolution shown).
4. The empirical content at scale: the pooled P(class | x) table, the ladder, the
   broadcast dissociation, and the degree-flat BA result as the discriminating
   contrast with hub-centric intuitions.
5. Spectral remark (short): the common/relative amplification modes of the exposure
   matrix (eigenvalues 1 and the subdominant λ₂(W)) connect the lock-in strength to
   the companion framework's mode analysis — stated as a remark, not a theorem.

Proposed placement: the general setup and window statement replace the current
two-community-only framing of the collective section (two-community stays as the
worked example and the confirmatory cell); the ladder and exposure-collapse figures
go to the main text (two panels: P(class|x) pooled; ladder × geometry heatmap); the
full grid, BA, broadcast, unequal sizes and the T=2400 resolution go to the
appendix/SI with the record pointers. Echo-chamber positioning gains one sentence:
the window IS the chamber condition (enough visible winners to sustain grievance,
not enough contact to flip behaviour).

## Honest limits

Everything is finite-horizon (we keep horizon-indexed language). The window
thresholds are measured at the frozen defaults (λ = 0.7, ρ = 0.002, χ = 0.4,
w_in = 0.85); their closed-form dependence on (λ, χ, ρ) is theory to be written,
with the two-community formulas as the exact case. Exposure is block-uniform
(within the companion framework's exact-aggregation class); agent-level arbitrary
graphs remain outside, as before.
