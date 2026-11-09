# Reproducibility, verification and simulation protocol

Staged for the public repository. This document carries the full protocol and
verification statements summarized in the paper's Methods; the paper quotes only what a
reader needs, this file holds the machinery. Nothing here changes any number in the
paper; every value is quoted from the frozen records named below.

## Frozen-design protocol

Every confirmatory or baseline experiment fixed, in writing and before execution: the
parameter cells, the seeds, the outcome definitions, the classification thresholds, and
the acceptance criteria. Failed predictions are reported in the paper (main text and
Supplementary Section S12), not removed. Design files are the `00_freeze_*.yaml`
records; each closes with a dated closing record listing outcomes and surprises.

Outcome definitions. Defensive wrong consensus: terminal optimal-choice mass of the
losing community < 0.3 and its mean legitimacy < 0.3, terminal = mean over the last 50
trials. The four-regime map adds: credulous (m2 < 0.3, L2 > 0.5), correct-but-
illegitimate (m2 > 0.7, L2 < 0.3), legitimate (m2 > 0.7, L2 > 0.5); classification
frozen before the mapping runs.

Statistics. A replication is one population trajectory. Regime probabilities carry
Wilson 95% intervals with the replication count stated at each use (R = 300 for the
confirmatory cell; R = 200 for the CRN-paired baseline cells; R as stated for sweeps).
Paired gate-on/off contrasts use common random numbers with paired-bootstrap 95%
intervals (B = 2000).

## Engines and cross-validation

Three independent implementations, no shared code:

1. Primary engine (Python/NumPy): ran all confirmatory and baseline experiments. All
   confirmatory numbers quoted in the paper come from its frozen records.
2. Scalar audit implementation: an independent re-simulation of key cells with fresh
   seeds. STATUS: a consistency check, not a pre-stated gate. At the trapped
   confirmatory cell it gave optimal mass 0.112 with standard error 0.047 against the
   primary engine's 0.166 — a gap of 1.1 standard errors — and legitimacy 0.049 against
   0.062. The recorded criterion in the artifact (audit_confirmatory.json) was
   agreement within 4 s.e.; that criterion was recorded at run time, not pre-stated in
   the iteration freeze, which is why the paper does not present the audit as a gate.
3. High-throughput mapping engine (Rust, zero dependencies, xoshiro256++ with SplitMix64
   seeding): produced the dense maps, trajectory panels and scaling studies. Its random
   stream differs from the primary engine's, so validation is distributional, with five
   PRE-STATED gates (00_freeze_figruns.yaml) that had to pass before any sweep output
   was used:
   - trap cell, gate on: |m2 − 0.166| ≤ 0.06 and P_dw ∈ [0.78, 0.90]
     → observed m2 = 0.198, P_dw = 0.813 (vs primary 0.843). PASS
   - trap cell, gate off: corrects → m2 = 0.9998. PASS
   - knife-edge decoupling cell: L2 = 0.0651 vs primary 0.0649. PASS
   - credulous-error cell: L2 = 0.738 vs primary 0.739. PASS
   - single-agent resignation: L_tail = 0.985. PASS
   The engine's I014 structural extensions (asymmetric community sizes, heterogeneous
   permeability, payoff-biased field) were verified bit-identical on all five gates
   after the refactor, before any new run.

Mapping runs are descriptive; no confirmatory number in the paper is quoted from them.

Figure pipeline: Julia/CairoMakie, reading frozen CSV/JSON records only; no figure
triggers a simulation. Palette is colour-vision-deficiency validated.

Seed policy: every random stream is seeded from values pre-declared in the freeze
files; re-emissions of sweeps with added columns are verified bit-identical on the
original columns before use (verification notes in the freezes).

## Machine-checked statements (Lean 4)

Seven theorems compile in Lean 4 (v4.28.0, core library only, statements over the
rationals — the parameter space used in all experiments; general ordered-field versions
remain pen-and-paper):

- T1: the quadratic-expansion identity behind the gradient derivation (DissCore.lean)
- T2, T2b: the A* sign characterization, cleared and divided forms (DissCore.lean)
- T3: geometric decay of the between-community benchmark gap (DissCore.lean)
- T4: the branch-weighted expectation bridge, certifying E[ΔL] > 0 ⇔ A < A* in the
  generic region via the chain T4→T2→T2b (DissBridge.lean)
- T5a, T5b: the gated contraction and its n-step geometric form (DissBridge.lean)

Axiom closure of every theorem is exactly {propext, Classical.choice, Quot.sound}; no
sorry. The formal layer certifies algebra only; stochastic approximation, network
dynamics and all behavioural interpretation rest on analysis and simulation. Scope
statements and the exact correspondence to the paper's propositions: Supplementary
Section S7.

Sources: directory `formal_diss/` on branch `lean-diss-core` of the authors'
repositories (CSL @ 4049e6af8ef7fa2228034f5cd111d23bbad7f85c, CSL2 @
77e5c40445781b602ddda9a1714de71608306c01), with toolchain pin and verification logs.

## Citation verification

Every imported result is cited only after verification against an authoritative
bibliographic record; theorem or chapter numbers internal to a source are cited only
where independently confirmed. The log is `00_citation_verification_I004.md` (with
dated addenda per iteration).

## Bundle contents

Frozen design files (`00_freeze_*.yaml`), all result records (JSON/CSV), the primary
engine, the scalar audit implementation, the Rust mapping engine and its
cross-validation report, the Julia figure scripts, the Lean sources with verification
logs, the identification-study code (I003), the prediction generator
(`predict_taskv3.py`). Simulated referee reports and their dispositions are kept out
of this public repository by design (they live with the authors' private records).

## Experiment pipeline certification (I032) — how to reproduce and verify

Everything below is seeded; reruns from the committed code reproduce the committed
records bit-for-bit (verified in the I032 audit; `records/manifest_I032.sha256`
lists the hashes).

| Step | Command (from the repo root) | Output |
|---|---|---|
| Test suite (port vs scalar reference of `predict_taskv3.py`; statistics vs references and null levels; pipeline end-to-end; screens) | `python -m pytest -q experiment/analysis/tests` | pass/fail |
| G2 pipeline = power engine | `python experiment/analysis/g2_consistency.py` | `records/g2_consistency.csv` |
| S7 suspicion-contamination addendum | `python analysis/power_free_s7.py` | `records/power_free_s7.csv` |
| G1 rho recovery, market skin | `python experiment/analysis/g1_recovery.py` | `records/g1_recovery_I032.csv` |
| Certification run 2 (H1a, frozen H1b, dose, framing) | `python experiment/analysis/pipeline_cert.py` | `records/pipeline_cert_I032{,_calib}.csv` |
| Certification run 3 (H1b-SI/SIc, heterogeneity) | `python experiment/analysis/pipeline_cert_run3.py` | `records/pipeline_cert_I032_run3.csv` |
| Post-hoc H1b anatomy and baseline test | `python experiment/analysis/explore_h1b_anatomy.py`; `... explore_h1b_baseline.py` | `records/h1b_*_I032pc.*` |
| Post-hoc dose diagnostic | `python experiment/analysis/dose_posthoc_I032.py > records/dose_posthoc_I032.txt` | `records/dose_posthoc_I032.txt` |
| oTree bots (all configs; reload/duplicate robustness) | `cd experiment && otree test bots_refresh 12` (and each `bots_*`, `pilot_*`, `pool_rich`) | pass/fail |
| Hash check | `sha256sum -c records/manifest_I032.sha256` | OK lines |

Run order matters only for run 3 and the anatomy scripts, which read
`records/pipeline_cert_I032_calib.csv` written by run 2. Freezes, addenda and the
post-close audit are in `freezes/00_freeze_I032.yaml` and `records/98_audit_I032.md`.
