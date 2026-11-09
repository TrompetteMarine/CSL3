# Why the frozen H1b failed — anatomy (post-hoc, after the I032 close)

Post-hoc exploration. No frozen record is altered, nothing here is a
certification, and any candidate it suggests must be frozen and certified
(I033) before it can go into the preregistration. Scripts:
`experiment/analysis/explore_h1b_anatomy.py`, `explore_h1b_baseline.py`.
Each was committed with its questions before it ran. Outputs:
`records/h1b_anatomy_I032pc.{txt,csv,log}`, `records/h1b_baseline_I032pc.{txt,log}`.

## What the gate actually does under moderate restoration (latent, n = 40,000)

Trust collapses through P2 and is still collapsing at the P2 midpoint: P1 97.5,
P2 mean 54.2, last-5-ratings of P2 25.4, t = 300 21.7. When restoration
arrives the collapse stops, and trust sits at 21.4–22.1 for the whole of P3.
The restoration response measured from the end of P2 is **−3.9 points**.
Restoration *arrests* the collapse but does not reverse it: "too little, too
late" as a flatline. The main text's "flatlining under moderate restoration"
is the correct description. **Correction:** the I032 closing report, the
certification record, DESIGN.md and the prereg amendment said the gate
"declines rather than flatlines". That was wrong, and they are corrected with
dated errata.

Mechanism. Under MODERATE the gate's aspiration stays just above the critical
level (late-P3 A = .506 vs A* = .493; A > A* in 69% of subjects), so expected
dL ≈ 0. The P3 reference regime (iid in the design) splits this.
P3-HIGH subjects stay shut (A > A* in 98.5%; d3 −9.5), and P3-LOW subjects
reopen slightly (40.5%; d3 +1.9). Slow adapters (ρ = .002) stay shut more than
fast ones (84% vs 54%). The utility rival R3 equilibrates within P2 (P2 mean =
end of P2 = 79.2) and recovers fast in P3 (+12.4 within ~30 trials). The
group-contingent R4 is the model that genuinely declines in P3 (−24.3 from the
end of P2).

## The three defects, separately

**1. Baseline.** The frozen statistic is rec = late-P3 − P2 *mean*. For the
gate this books the unfinished P2 collapse as a P3 change: of the −32.6, −28.7
is P2 and −3.9 is P3. For R3, which equilibrates fast, the baseline is
unbiased. The baseline therefore distorts precisely the model under test. The
two-sided equivalence test then rejects the gate for something it did *before*
restoration. This is why the frozen H1b has zero power at full scale.

**2. Scale.** δ_eq is an absolute band in slider points, set by rating noise.
The separating signal scales with how much of the latent change the slider
registers (gain a). With the P2-mean baseline the band would have to sit
between the gate (−32.6·a) and R3 (+12.8·a), which needs |gate| < R3. That is
false at every gain, so the frozen H1b has power 0.000 at every a in
[.05, 1] (Q3, all eight gains). With the correct baseline the band can sit
between them (3.9·a < δ < 12.4·a), but only when a > .4. The design basis
implies a ≈ .06, so it still fails there.

**3. Aggregation.** In a population with no gate (R3 types 56%, R4 types 44%),
the HIGH × MODERATE recoveries are bimodal: R3 median +10.3, R4 median −20.3.
The pooled median falls at **+2.3, inside the ±5 band**, so the pooled
equivalence test "sees" a flatline that no individual produces, in 23% of
replicates. The gate's claim is a same-person conjunction (this person
delegitimized *and* does not recover); a pooled cell test cannot check it.
Among the above-median-drop half, 91% are R3 types with median +11.2, which is
why the drop-conditioned H1b-SIc rejects the composite (.000).

## Does it depend on how the effect is deflated to θ = .592? (Q4)

| route to θ = .592 | parameter | frozen H1b gate power | H1b-SIc power | R3 false + (all forms) | R3 passes H1a |
|---|---|---|---|---|---|
| slider attenuation | a = .058 | .000 | .933 | .000 | .160 |
| rating noise | σ = 151 (implausible: ratings pile at 0/100) | .000 | .953 | .000 | .180 |
| weak anchoring | χ = .178 | .327 | .987 | .000 | .703 |
| slow aspiration | ρ = .0014 | .000 | .897 | .000 | .890 |

The frozen H1b is dead under every route except weak anchoring, where the
gate's P2 collapse is shallow enough to finish inside P2. Two further facts.
Under the anchoring and rigidity routes H1a also passes R3 most of the time
(.70, .89), so H1b carries the whole gate-vs-utility discrimination. And
H1b-SIc is powered and specific under all four routes.

## A caveat on H1b-SIc that this exploration exposes

H1b-SIc also uses the P2-mean baseline. At the design-basis attenuation its
power (.960) leans on the same P2-collapse ramp that broke the frozen test.
Replacing the baseline with the last five P2 ratings, which measures the
restoration response itself, keeps it perfect at full scale (gate 1.000,
gate+R4 .965, R3 .000, composite .010/.000). But power collapses at the design
basis (.270 all subjects, .030 high-drop half). Under attenuation, R3's
restoration response is about 0.7 slider points, below one rounding step. The
dissociation is near the detectability limit at N ≈ 213 unless the test
borrows the P2 ramp. The ramp, though, is a property of any *integrating*
rating dynamic, not of the gate specifically. A rival with a reference effect,
slowly integrating ratings and a genuine P3 recovery was **not simulated** and
could pass H1b-SIc. Specific and powered under attenuation are therefore in
tension. Which matters depends on the slider gain, and that is an empirical
quantity.

## What this implies (for the author; nothing adopted)

1. The prediction is fine; the test was wrong. "Under moderate restoration
   behaviour recovers and fairness stays flat" matches the model (d3 −3.9 vs
   R3 +12.4). What failed is the operationalization: the P2-mean baseline, an
   absolute band, and pooling.
2. The pilot must estimate the slider gain, and the FULL positive-control arm
   is the natural gauge (the model's FULL recovery in latent points vs the
   measured slider change). The gain decides whether a specific
   end-of-P2-baseline test is powered at N ≈ 213 or whether the design needs
   more HIGH × MODERATE participants, or denser ratings around the P2/P3
   boundary.
3. I033 certification candidates: (a) the end-of-P2 (or P2-trend-extrapolated)
   baseline, normalized by the subject's drop and conditioned on high drop;
   (b) an *integrating-utility* rival built and run against both H1b-SIc and
   (a); (c) a design option, setting the H1b cell's P3 regime equal to its P2
   regime (HIGH), where the gate's prediction is sharpest (d3 −9.5 vs +1.9).
