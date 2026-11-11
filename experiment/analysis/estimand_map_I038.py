"""KGi-DISS-I038 part B: the model-generated value of the estimand (freeze 00_freeze_I038.yaml,
addendum AD-B1). Seed 135000.
    python experiment/analysis/estimand_map_I038.py > records/estimand_map_I038.txt
Writes records/estimand_map_I038.json (thresholds used by the certification).
"""
import json

import numpy as np
import pandas as pd

import estimand_core_I038 as ec

rng = np.random.default_rng(135000)
NP = 40000
SHAPES = ('hom', 'two01', 'two51', 'skew')
CS = (0.0, .25, .5, .75, .85, .90, .95, 1.0)

print("KGi-DISS-I038 part B: model-generated value of psi = E[T|HIGH] / E[T|LOW] in design S1x (seed 135000)\n")
gate = {p[0]: ec.pools('gate', p, NP, rng) for p in ec.GATE_POINTS}
print("legitimacy at probe time, HIGH / LOW (mean; share below .05 in HIGH):")
for p in ec.GATE_POINTS:
    g = gate[p[0]]
    print(f"  {p[0]} (speed {p[1]}, ratio {p[2]}, anchoring {p[3]:.3f}): {g['HIGH'].mean():.3f} / {g['LOW'].mean():.3f}"
          f"   ({(g['HIGH'] < .05).mean():.2f})")

out = {'psi_c': {}, 'shape': {}}
print("\npsi by homogeneous coupling (columns) at each gate point (rows)")
for rule in ec.RULES:
    print(f"  rule: {rule}      " + "  ".join(f"c={c:<4}" for c in CS))
    for p in ec.GATE_POINTS:
        g = gate[p[0]]
        v = [ec.weight_ratio(g['HIGH'], g['LOW'], c, c, rule) for c in CS]
        out['psi_c'][f"{p[0]}|{rule}"] = dict(zip(map(str, CS), v))
        print(f"    {p[0]}            " + "  ".join(f"{x:6.3f}" for x in v))

print("\ndoes psi depend on the SHAPE of the coupling distribution at a given mean? (columns: shapes)")
worst = {}
for rule in ec.RULES:
    for mc in (.90, .95):
        print(f"  rule {rule}, mean coupling {mc}:   " + "  ".join(f"{s:>6}" for s in SHAPES) + "   range")
        for p in ec.GATE_POINTS:
            g = gate[p[0]]
            v = []
            for s in SHAPES:
                ch, cl = ec.coupling(s, mc, NP, rng), ec.coupling(s, mc, NP, rng)
                v.append(ec.weight_ratio(g['HIGH'], g['LOW'], ch, cl, rule))
            out['shape'][f"{p[0]}|{rule}|{mc}"] = dict(zip(SHAPES, v))
            worst[(rule, mc)] = max(worst.get((rule, mc), 0), max(v) - min(v))
            print(f"    {p[0]}                      " + "  ".join(f"{x:6.3f}" for x in v) + f"   {max(v) - min(v):.3f}")
print("  largest range across shapes: " + "  ".join(f"{r} at {m}: {v:.3f}" for (r, m), v in worst.items()))

# thresholds
psi_model = {k: v['1.0'] for k, v in out['psi_c'].items()}
edge90 = {k: max(v.values()) for k, v in out['shape'].items() if k.endswith('|0.9')}
edge95 = {k: min(v.values()) for k, v in out['shape'].items() if k.endswith('|0.95')}
psi_lo = min(psi_model.values())
psi_hi = max(edge90.values())
# coupling certified whatever the gate dynamics: HIGH legitimacy 0, LOW legitimacy 1, mean coupling .90
z, o = np.zeros(NP), np.ones(NP)
cert = min(ec.weight_ratio(z, o, ec.coupling(s, .90, NP, rng), ec.coupling(s, .90, NP, rng), r)
           for s in SHAPES for r in ec.RULES)
print("\nthresholds")
print("  model value at full coupling (c = 1), by point | rule: " +
      "  ".join(f"{k} {v:.3f}" for k, v in psi_model.items()))
print("  upper edge of the trap set by point | rule (largest psi at mean coupling .90): " +
      "  ".join(f"{k.rsplit('|', 1)[0]} {v:.3f}" for k, v in edge90.items()))
print("  tight edge by point | rule (smallest psi at mean coupling .95): " +
      "  ".join(f"{k.rsplit('|', 1)[0]} {v:.3f}" for k, v in edge95.items()))
print(f"  trap set over all points and both rules: psi in [{psi_lo:.3f}, {psi_hi:.3f}]")
print(f"  coupling-certified threshold (HIGH legitimacy 0, LOW legitimacy 1, mean coupling .90; smallest over "
      f"shapes and rules): {cert:.3f}")

riv = {'R3 (multiplier 1)': None, 'R4': ec.pools('rival_us', ('R', 1.0, .25, .6), NP, rng),
       'R1': ec.pools('rival', ('R', 1.0, .25, .6), NP, rng)}
print("\nrivals (their own multiplier, coupling 1):")
for k, v in riv.items():
    if v is None:
        print(f"  {k}: outcome 1.000  event 1.000")
    else:
        print(f"  {k}: " + "  ".join(f"{r} {ec.weight_ratio(v['HIGH'], v['LOW'], 1.0, 1.0, r):.3f}" for r in ec.RULES))

# the ABM side: trap probability of the same populations at mean coupling .90 and .95
h2 = pd.read_csv('records/hetc2.csv')
print("\nABM trap probability at the paper cell for populations with mean coupling near .90 and .95 (records/hetc2.csv):")
for fam, d in h2.groupby('family', sort=False):
    xs, ps = d.mean_c.values, d.p_dw.values
    e = next((xs[i - 1] + (xs[i] - xs[i - 1]) * (.5 - ps[i - 1]) / (ps[i] - ps[i - 1])
              for i in range(1, len(xs)) if ps[i - 1] < .5 <= ps[i]), None)
    print(f"  {fam:45s} P_dw at .90: {np.interp(.90, xs, ps):.3f}   at .95: {np.interp(.95, xs, ps):.3f}   "
          f"edge in mean coupling: {e:.3f}")

json.dump(dict(psi_model=psi_model, edge90=edge90, edge95=edge95, psi_lo=psi_lo, psi_hi=psi_hi, psi_cert=cert),
          open('records/estimand_map_I038.json', 'w'), indent=1)
