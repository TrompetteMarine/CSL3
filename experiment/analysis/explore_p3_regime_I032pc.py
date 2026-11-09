"""POST-HOC / EXPLORATORY (written after explore_h1b_candidates_I032pc.py; NOT a
certification).

Q5  At t = 300 the frozen design changes own odds AND (with prob .5, iid) the
    reference regime: two interventions at one interruption. If instead the
    reference regime is held fixed across restoration (P3 regime = P2 arm), what
    does each model predict for the restoration response rec_end = late-P3 -
    end-of-P2 (latent x100, MODERATE)? Computed on the P3-regime subsets of the
    frozen design (P3 regime is iid, so the subset equals the fixed-regime design
    in distribution for P3 dynamics). Also the between-arm contrast under the
    fixed design: HIGH(P3 HIGH) - LOW(P3 LOW).

Seed 132980. Run from the repo root:
    python experiment/analysis/explore_p3_regime_I032pc.py > records/p3_regime_I032pc.txt
"""
import sys

import numpy as np

sys.path.insert(0, 'experiment/analysis')
import market_generator as mg

rng = np.random.default_rng(132980)
N = 20000
END = slice(56, 60)
print("POST-HOC exploratory: reference held fixed across restoration (seed 132980; latent x100; MODERATE)")
print(f"{'model':6s} {'HIGH arm, P3 HIGH':>18s} {'HIGH arm, P3 LOW':>17s} {'LOW arm, P3 LOW':>16s} {'fixed-design H-L':>17s}")
for name, kind in (('gate', 'gate'), ('R3', 'rival_au'), ('R4', 'rival_us')):
    r = {}
    for arm in ('HIGH', 'LOW'):
        lat = mg.simulate_latent(kind, N, arm, rng, resto_mix=(1, 0))
        L = 100 * lat['ratings'].astype(float)
        rec = L[:, mg.LATE_IDX].mean(1) - L[:, END].mean(1)
        r[(arm, True)] = rec[lat['reg3']].mean()
        r[(arm, False)] = rec[~lat['reg3']].mean()
    print(f"{name:6s} {r[('HIGH', True)]:18.1f} {r[('HIGH', False)]:17.1f} {r[('LOW', False)]:16.1f} "
          f"{r[('HIGH', True)] - r[('LOW', False)]:17.1f}")
