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
import pandas as pd
from probe_design_I037 import ODDS, P1TAG, points, multipliers

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
first = 'S1x' if ('S1x' in sel and sel['S1x']['n'] < sel['S1']['n']) else 'S1'
for tag in (first, 'S2'):
    d = sel[tag]
    design = (d['r1'], d['r2'], d['k'], d['odds'])
    p1 = d.get('p1', 'p65')
    n = d['n']
    pts = points(ODDS[d['odds']], c_edge, P1TAG[p1][1])
    print(f"=== {tag}: rounds {d['r1']}+{d['r2']}, {d['k']} draws per round, deprivation odds {d['odds']}; "
          f"probe {d['scheme']} with m = {d['m']}; {d['reps']} repetitions; n = {n} per arm")
    gate = {p[0]: multipliers('gate', design, p[1], p[2], p[3], n=NP, gen=rng, p1tag=p1) for p in pts}
    print("  power (rows: forecast noise; columns: theory points)")
    for integ in ('outcome', 'event'):
        for sig in (8.0, 12.0, 16.0):
            pw = [reject_rate(stat(gate[p[0]]['HIGH'], p[4], d, sig, integ), stat(gate[p[0]]['LOW'], p[4], d, sig, integ), n)
                  for p in pts]
            print(f"    {integ:8s} sigma {sig:4.0f}: " + "  ".join(f"{p[0]} {x:.3f}" for p, x in zip(pts, pw)), flush=True)
    if tag == first:
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
    riv = {'R3 chi .4': multipliers('rival_au', design, 1.0, .25, .4, n=NP, gen=rng, p1tag=p1),
           'R3 chi .6': multipliers('rival_au', design, 1.0, .25, .6, n=NP, gen=rng, p1tag=p1),
           'R4': multipliers('rival_us', design, 1.0, .25, .6, n=NP, gen=rng, p1tag=p1),
           'R1': multipliers('rival', design, 1.0, .25, .6, n=NP, gen=rng, p1tag=p1)}
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
            if tag == first:
                out.append(f"(with attention check {reject_rate(stat(riv['R3 chi .4']['HIGH'], 1.0, d, 12.0, integ, extra=dl, attn=True), stat(riv['R3 chi .4']['LOW'], 1.0, d, 12.0, integ, attn=True), n):.3f})")
        print(f"    {integ:8s}: " + "  ".join(out), flush=True)
    if tag == first:      # AD-B3 (scope fixed before running)
        coup = pd.read_csv('records/couple.csv'); coup = coup[coup.part == 'diag'].set_index('c_own').p_dw
        ct = pd.read_csv('records/ctime.csv').groupby('c').t_correct.median()
        print("  partial discounting at P1's gate parameters (sigma 12): c, HIGH/LOW weight ratio, power, [ABM: P_dw, median correction time]")
        for c in (0.0, .25, .5, .75, .85, .9, c_edge, 1.0):
            out = [f"    c={c:.3f}"]
            for integ in ('outcome', 'event'):
                wh = pg.weight(1 - c * (1 - gate['P1']['HIGH']), d['m'], integ).mean()
                wl = pg.weight(1 - c * (1 - gate['P1']['LOW']), d['m'], integ).mean()
                pw = reject_rate(stat(gate['P1']['HIGH'], c, d, 12.0, integ), stat(gate['P1']['LOW'], c, d, 12.0, integ), n)
                out.append(f"{integ}: ratio {wh / wl:.3f} power {pw:.3f}")
            pdw = coup.get(round(c, 2), np.nan); tc = ct.get(round(c, 2), np.nan)
            out.append(f"[P_dw {pdw if pdw == pdw else float('nan'):.2f}, correction {tc if tc == tc else float('nan'):.0f}]")
            print("  ".join(out), flush=True)
        print("  starting entitlement (sigma 12; power at the worst inside point | which point)")
        for a0 in (.4, .6):
            g2 = {p[0]: multipliers('gate', design, p[1], p[2], p[3], n=NP, gen=rng, p1tag=p1, a0=a0) for p in pts}
            out = [f"    A0={a0}"]
            for integ in ('outcome', 'event'):
                pw = {p[0]: reject_rate(stat(g2[p[0]]['HIGH'], p[4], d, 12.0, integ), stat(g2[p[0]]['LOW'], p[4], d, 12.0, integ), n) for p in pts}
                w = min(pw, key=pw.get)
                out.append(f"{integ}: " + " ".join(f"{k} {v:.2f}" for k, v in pw.items()))
            print("  ".join(out), flush=True)
    print(f"  R4 / R1 multiplier at probe time HIGH/LOW: {riv['R4']['HIGH'].mean():.2f}/{riv['R4']['LOW'].mean():.2f}  "
          f"{riv['R1']['HIGH'].mean():.2f}/{riv['R1']['LOW'].mean():.2f}\n")
