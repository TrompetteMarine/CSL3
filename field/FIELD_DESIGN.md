# Field project design — reference-dependent delegitimation at platform scale (I027)

Complete design, parameterised by the lab outputs: every constant below is either
frozen now, or a named slot filled by the experiment's posteriors through the
model → lab → field chain of `../experiment/PRIORS.md`. Nothing is estimated from
field outcomes before the priors, lexicon, partition and episode list are locked
(registered-report discipline; the OSF field registration is a separate document
generated from this one once the lab posteriors exist).

## 1. Research question

When online communities keep losing while winners are visible, does their
discourse delegitimate the game — and does persistence of that delegitimation
follow the theory's exposure window and two clocks? Three quantities carry the
test, one per lab prior: the exposure → legitimacy-language coefficient at fixed
own outcomes (P-A), the behaviour/legitimacy persistence dissociation and its
dosage threshold (P-B), and the predicted *distribution* of persistence times
from the platform's measured exposure distribution and the lab's rigidity
distribution through t* and t** (P-C) — a quantitative, falsifiable field
prediction, not a direction.

## 2. What is exportable from the model, and what is not

Never exported: the numeric x_B ≈ 0.11 and the window edge locations (frozen-
parameter, budget-dependent arithmetic). Exported: the shape battery — (i) a
step-like, not linear, transition of persistence in exposure share; (ii)
horizon-indexing (persistence scales with the rigidity clock, not calendar
time); (iii) the dissociation ordering (behavioural correction precedes
legitimacy repair, t** > t*); (iv) the signed counterintuitive derivative
dt*/dx > 0 below the behavioural edge — more exposure to winners LENGTHENS
grievance while failing to flip behaviour. (iv) is the field's sharpest
discriminating prediction because no exposure-cures-everything account produces
it.

## 3. Domains (adjudicable correctness is the entry condition)

Primary: retail-finance communities on Reddit (asset-specific communities such
as the GME/AMC ecosystem against benchmark/index-investing communities).
"Losing" is objective (realized returns of the community's focal position vs the
visible benchmark), winners are visible, and delegitimating discourse ("rigged,"
"manipulated," "shills," distrust of market institutions) is abundant and is
literally the model's dependent variable. Secondary (robustness domain):
sports-betting communities (settled outcomes, visible winners). Excluded by the
entry condition: general political content (no adjudicable correctness), per
R8's condition (ii).

## 4. Units, partition, panel

Community = subreddit (natural partition), with a pre-specified sensitivity
battery: community detection on the user–comment bipartite graph at two coarser
resolutions, and size-stratified replication of every window test (the model
says fate depends on community size inside the window, so the partition scale is
a theoretical variable, not a nuisance). Panel: community × month, 2019–2024,
target 200–500 communities across the two domains; user × month sub-panel inside
natural-experiment episodes. Data: Pushshift/academic archives plus the research
API; all extraction code in this repository.

## 5. Measures (all operationalisations locked before outcome extraction)

- Legitimacy-language index L̂_ct: classifier score for delegitimation of the
  game/rule-makers (not mere negativity), built by LLM-assisted annotation with a
  human-validated set (target κ ≥ .75 on 1,000 double-coded comments; lexicon and
  prompts versioned here before any panel estimation).
- Behavioural proxy B̂_ct: activity and position language reallocation (exit/
  switch language; migration of activity toward benchmark communities),
  acknowledged as a partial behaviour measure; the dissociation tests use
  within-community discourse–behaviour pairs.
- Structural exposure x̂_c: engagement-weighted share of community c's members'
  activity occurring in "winning" communities, measured at episode start
  (matching the lab's structural-x convention), with the within-episode realized
  path reported alongside. Stated plainly: this is an impressions proxy —
  follow-graph and engagement measures understate passive exposure; the
  limitation is carried in every claim.
- Outcomes: realized returns of the focal position vs benchmark (objective
  losing/winning), windfall analogues (dividend/squeeze events) for the
  asymmetry test.
- Entitlement language Ê_ct (exploratory): deservingness/price-target phrases;
  no individual ρ is estimated in the field — the lab ρ̂ distribution IS the
  heterogeneity input (P-C).

## 6. Identification

- F1 (P-A analogue): event studies around objective outcome shocks (drawdowns),
  within community, interacting shock size with x̂_c, own-outcome controls;
  staggered-adoption-robust estimators (Callaway–Sant'Anna class). The lab
  posterior enters as the prior on the standardized coefficient (transfer-
  inflated ×2 per PRIORS.md). This layer is calibrative-correlational and is
  labelled as such.
- F2 (P-B analogue): after corrective episodes (recovery or authoritative
  resolution), censored survival comparison of B̂ recovery vs L̂ recovery
  half-lives; prior = lognormal on the lag ratio from the lab posterior; the
  dosage threshold tested on episode intensity.
- F3 (the causal layer; any x_B-shaped claim lives here only): natural
  experiments that move exposure exogenously — subreddit bans, quarantines and
  forced migrations (displaced users land in communities with different x̂),
  platform feature changes. User-level difference-in-differences between
  displaced-to-high-x̂ and displaced-to-low-x̂ users on delegitimation
  persistence, with matching on pre-period activity and outcome exposure;
  dose–response against x̂ tested against the step shape, and the dt*/dx > 0
  sign tested below the behavioural edge.
- F4 (the quantitative test, P-C): the platform's measured x̂ distribution plus
  the lab ρ̂ distribution, pushed through t*(x) and t** ≈ k·t* (k from the lab/
  battery calibration), yields a predicted persistence-time distribution for
  delegitimated discourse after corrective episodes. Predicted vs observed
  distribution compared by quantile calibration, priors locked beforehand. This
  is the out-of-sample test of the theory as a measurement instrument, and it is
  the deliverable that distinguishes the project from descriptive echo-chamber
  work.

## 7. Power and pre-launch simulation

The ABM is the power engine: the frozen engine generates community panels under
the estimated x̂ distribution, the lab ρ̂ distribution and the measured shock
calendar; F1–F4 estimators run on simulated panels to size detectable effects
and false-positive behaviour BEFORE any real outcome extraction. The power
report is frozen alongside the registration (same discipline as the simulation
batteries: design and bands first, data second).

## 8. Risks, stated

Exposure is an engagement proxy, not impressions (carried in every claim; a
validation sub-study against any available impression data upgrades it).
Classifier construct validity (mitigated by the validation set and by
pre-registered negative controls: communities with losses but no visible
winners, where the model predicts resignation language, not delegitimation —
itself a discriminating test). Ban-displacement selection (matched user panels;
placebo bans). Partition degrees of freedom (pre-specification + sensitivity).
Archive completeness post-2023 (episode list restricted to covered windows).

## 9. Sequence and deliverables

(1) Now: this design + extraction/lexicon tooling scaffolded in `field/`.
(2) After the experiment: PRIORS.md slots filled from lab posteriors; power
simulation run and frozen; OSF field registration issued. (3) Estimation in the
locked order F1→F2→F3→F4; all records and freezes in this repository. The
strategic vehicle for the paper is the staged programme already stated in the
manuscript's Discussion: model (published) → experiment (confirmatory) → this
field test of the window as a measurement theory; a Registered Report format is
the natural fit for stage three.
