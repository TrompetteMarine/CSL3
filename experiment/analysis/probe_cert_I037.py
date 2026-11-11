"""KGi-DISS-I037 part B stage 2: Monte Carlo certification of the selected probe designs
(freeze 00_freeze_I037.yaml). Needs records/probe_design_I037_selected.json. Seed 134300.
    python experiment/analysis/probe_cert_I037.py > records/probe_cert_I037.txt
"""
import json
import sys

import numpy as np

sys.path.insert(0, 'experiment/analysis')
import probe_generator as pg
import stats_v2 as sv
from probe_design_I037 import ODDS, points, multipliers

rng = np.random.default_rng(134300)
NP, B, R3_SHARE = 20000, 1000, .5595
sel = json.load(open('records/probe_design_I037_selected.json'))
c_edge = sel['edges']['c_edge']


def reject_rate(th, tl, n, b=B):
    r = 0
    for _ in range(b):
        r += sv.wmw_one_sided(rng.choice(th, n, replace=False), rng.choice(tl, n, replace=False))[0]
    return r / b


def stat(mult, c, d, sig, integ, extra=0.0, attn=False):
    t, att = pg.probe_stat(mult, c, d['m'], d['scheme'], sig, integ, rng, extra_inattentive=extra,
                           return_attentive=True)
    if attn:      # attention check: inattentive fail with prob .8, attentive with prob .05
        fail = np.where(att, rng.random(len(t)) < .05, rng.random(len(t)) < .8)
        t = t[~fail]
    return t


print("KGi-DISS-I037 part B stage 2: Monte Carlo certification (seed 134300; B = 1000)\n")
for tag in ('S1', 'S2'):
    d = sel[tag]
    design = (d['r1'], d['r2'], d['k'], d['odds'])
    n = d['n']
    pts = points(ODDS[d['odds']], c_edge)
    print(f"=== {tag}: rounds {d['r1']}+{d['r2']}, {d['k']} draws per round, deprivation odds {d['odds']}; "
          f"probe {d['scheme']} with m = {d['m']}; {d['reps']} repetitions; n = {n} per arm")
    gate = {p[0]: multipliers('gate', design, p[1], p[2], p[3], n=NP, gen=rng) for p in pts}
    print("  power (rows: forecast noise; columns: theory points)")
    for integ in ('outcome', 'event'):
        for sig in (8.0, 12.0, 16.0):
            pw = [reject_rate(stat(gate[p[0]]['HIGH'], p[4], d, sig, integ), stat(gate[p[0]]['LOW'], p[4], d, sig, integ), n)
                  for p in pts]
            print(f"    {integ:8s} sigma {sig:4.0f}: " + "  ".join(f"{p[0]} {x:.3f}" for p, x in zip(pts, pw)), flush=True)
    if tag == 'S1':
        print("  expected HIGH/LOW ratio of mean revision weights (attentive, noise-free):")
        for integ in ('outcome', 'event'):
            out = []
            for p in pts:
                wh = pg.weight(1 - p[4] * (1 - gate[p[0]]['HIGH']), d['m'], integ).mean()
                wl = pg.weight(1 - p[4] * (1 - gate[p[0]]['LOW']), d['m'], integ).mean()
                out.append(f"{p[0]} {wh / wl:.3f}")
            print(f"    {integ:8s}: " + "  ".join(out))
        print("  with attention-check exclusion (sigma 12):")
        for integ in ('outcome', 'event'):
            pw = [reject_rate(stat(gate[p[0]]['HIGH'], p[4], d, 12.0, integ, attn=True),
                              stat(gate[p[0]]['LOW'], p[4], d, 12.0, integ, attn=True), n) for p in pts]
            print(f"    {integ:8s}: " + "  ".join(f"{p[0]} {x:.3f}" for p, x in zip(pts, pw)), flush=True)
    riv = {'R3 chi .4': multipliers('rival_au', design, 1.0, .25, .4, n=NP, gen=rng),
           'R3 chi .6': multipliers('rival_au', design, 1.0, .25, .6, n=NP, gen=rng),
           'R4': multipliers('rival_us', design, 1.0, .25, .6, n=NP, gen=rng),
           'R1': multipliers('rival', design, 1.0, .25, .6, n=NP, gen=rng)}
    print("  false positives (sigma 12)")
    for integ in ('outcome', 'event'):
        out = [f"{k} {reject_rate(stat(v['HIGH'], 1.0, d, 12.0, integ), stat(v['LOW'], 1.0, d, 12.0, integ), n):.3f}"
               for k, v in riv.items()]
        k3 = int(round(R3_SHARE * NP))
        mix = {a: np.r_[riv['R3 chi .6'][a][:k3], riv['R4'][a][k3:]] for a in ('HIGH', 'LOW')}
        out.append(f"composite {reject_rate(stat(mix['HIGH'], 1.0, d, 12.0, integ), stat(mix['LOW'], 1.0, d, 12.0, integ), n):.3f}")
        for dl in (.1, .2):
            out.append(f"disengaged +{dl:.0%} "
                       f"{reject_rate(stat(riv['R3 chi .4']['HIGH'], 1.0, d, 12.0, integ, extra=dl), stat(riv['R3 chi .4']['LOW'], 1.0, d, 12.0, integ), n):.3f}")
            if tag == 'S1':
                out.append(f"(with attention check {reject_rate(stat(riv['R3 chi .4']['HIGH'], 1.0, d, 12.0, integ, extra=dl, attn=True), stat(riv['R3 chi .4']['LOW'], 1.0, d, 12.0, integ, attn=True), n):.3f})")
        print(f"    {integ:8s}: " + "  ".join(out), flush=True)
    print(f"  R4 / R1 multiplier at probe time HIGH/LOW: {riv['R4']['HIGH'].mean():.2f}/{riv['R4']['LOW'].mean():.2f}  "
          f"{riv['R1']['HIGH'].mean():.2f}/{riv['R1']['LOW'].mean():.2f}\n")
