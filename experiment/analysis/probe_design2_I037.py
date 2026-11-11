"""KGi-DISS-I037 addendum AD-B2: extended exposure grid for the probe (frozen before
running). Seed 134250.
    python experiment/analysis/probe_design2_I037.py > records/probe_design2_I037.txt
Adds key 'S1x' to records/probe_design_I037_selected.json.
"""
import itertools
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, 'experiment/analysis')
import probe_generator as pg
import probe_design_I037 as pd1
from probe_design_I037 import ODDS, P1TAG, points, multipliers

pd1.rng = np.random.default_rng(134250)
rng = pd1.rng
sel = json.load(open('records/probe_design_I037_selected.json'))
c_edge = sel['edges']['c_edge']
rows = []
print("KGi-DISS-I037 AD-B2 extended exposure grid (seed 134250; pair2; sigma 12)\n")
for (r1, r2), k, odds, p1 in itertools.product(((2, 4), (1, 5)), (40, 60, 80, 120), ('std', 'harsh'), ('p65', 'p75')):
    design = (r1, r2, k, odds)
    pts = points(ODDS[odds], c_edge, P1TAG[p1][1])
    pools = {p[0]: multipliers('gate', design, p[1], p[2], p[3], p1tag=p1) for p in pts}
    leg = "  ".join(f"{p[0]} {pools[p[0]]['HIGH'].mean():.2f}/{pools[p[0]]['LOW'].mean():.2f}" for p in pts)
    for m in (7, 10):
        res = {}
        for integ in ('outcome', 'event'):
            if integ == 'event' and m != 7:
                continue
            worst, wp = np.inf, None
            for p in pts:
                th = pg.theta(pg.probe_stat(pools[p[0]]['HIGH'], p[4], m, 'pair2', 12.0, integ, rng),
                              pg.probe_stat(pools[p[0]]['LOW'], p[4], m, 'pair2', 12.0, integ, rng))
                if th < worst:
                    worst, wp = th, p[0]
            res[integ] = (pg.n_asymptotic(worst), wp)
        rows.append(dict(r1=r1, r2=r2, k=k, odds=odds, p1=p1, m=m, n_outcome=res['outcome'][0],
                         wp_outcome=res['outcome'][1], n_event=res.get('event', (np.nan, ''))[0],
                         wp_event=res.get('event', (np.nan, ''))[1], legitimacy=leg))
df = pd.DataFrame(rows)
ev = df[df.m == 7][['r1', 'r2', 'k', 'odds', 'p1', 'n_event', 'wp_event']]
df = df.drop(columns=['n_event', 'wp_event']).merge(ev, on=['r1', 'r2', 'k', 'odds', 'p1'])
df['n_max'] = df[['n_outcome', 'n_event']].max(axis=1)
df = df.sort_values('n_max')
df.to_csv('records/probe_design2_I037.csv', index=False)
pd.set_option('display.width', 250)
print(df[['r1', 'r2', 'k', 'odds', 'p1', 'm', 'n_outcome', 'wp_outcome', 'n_event', 'wp_event', 'n_max']].round(0).to_string(index=False))
b = df.iloc[0]
print("\nlegitimacy at probe time (HIGH/LOW) for the best row: " + b.legitimacy)
sel['S1x'] = dict(r1=int(b.r1), r2=int(b.r2), k=int(b.k), odds=b.odds, p1=b.p1, m=int(b.m), scheme='pair2',
                  reps=int(b.r1 + b.r2 + 4), n=int(np.ceil(b.n_max)), n_outcome=float(b.n_outcome), n_event=float(b.n_event))
json.dump(sel, open('records/probe_design_I037_selected.json', 'w'), indent=1)
print("selected S1x: " + json.dumps(sel['S1x']))
