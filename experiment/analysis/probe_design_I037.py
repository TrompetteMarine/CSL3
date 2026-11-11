"""KGi-DISS-I037 part B stage 1: screen probe designs (freeze 00_freeze_I037.yaml).
Needs records/couple.csv (engine mode couple). Seed 134200.
    python experiment/analysis/probe_design_I037.py > records/probe_design_I037.txt
Writes records/probe_design_I037.csv and records/probe_design_I037_selected.json.
"""
import itertools
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, 'experiment/analysis')
import market_generator as mg
import design_generator as dg
import probe_generator as pg

rng = np.random.default_rng(134200)
NP = 12000
NUF0, NUR0 = mg.NUF, mg.NUR
ODDS = {'std': (.30, .15), 'harsh': (.25, .10)}
DESIGNS = [(2, 5, 25, 'std'), (2, 5, 40, 'std'), (2, 4, 40, 'std'), (1, 5, 40, 'std'), (1, 6, 40, 'std'),
           (2, 5, 40, 'harsh'), (2, 4, 40, 'harsh'), (1, 5, 40, 'harsh')]


def crossing(x, y, level=.5):
    """x ascending. First crossing of `level` by linear interpolation; None if y stays >= level."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if (y >= level).all():
        return None
    for i in range(len(x) - 1):
        if (y[i] - level) * (y[i + 1] - level) <= 0 and y[i] != y[i + 1]:
            return float(x[i] + (level - y[i]) * (x[i + 1] - x[i]) / (y[i + 1] - y[i]))
    return float('nan')


def edges():
    c = pd.read_csv('records/couple.csv')
    d = c[c.part == 'diag'].sort_values('c_own')
    s = c[c.part == 'soc'].sort_values('c_soc')
    o = c[c.part == 'own'].sort_values('c_own')
    e = dict(diag=crossing(d.c_own, d.p_dw), soc=crossing(s.c_soc, s.p_dw), own=crossing(o.c_own, o.p_dw))
    so = e['soc'] if e['soc'] is not None else 0.0
    ow = e['own'] if e['own'] is not None else 0.0
    if abs(so - ow) < .15:
        e['channel'], e['c_edge'] = 'both', e['diag']
    elif so > ow:
        e['channel'], e['c_edge'] = 'social', e['soc']
    else:
        e['channel'], e['c_edge'] = 'own', e['own']
    return c, e


def chi_min(p2, mu_ref=.65):
    p = .77 * p2[0] + .23 * p2[1]
    return (.3 + .25 * p / (1 - p) - p) / (mu_ref - p)


def points(p2, c_edge):
    return [('P0', 1.0, .25, .6, 1.0), ('P1', 1.0, .25, .4, 1.0), ('P2', 1.0, .2918, .4, 1.0),
            ('P3', .895, .25, .4, 1.0), ('P4', 1.0, .25, chi_min(p2), 1.0), ('P6', 1.0, .25, .4, c_edge)]


def multipliers(kind, design, s, ratio, chi, n=NP, gen=None):
    """model's learning multiplier at the end of the last deprivation round, HIGH and LOW"""
    r1, r2, k, odds = design
    out = {}
    mg.NUF, mg.NUR = NUF0 * s, NUF0 * s * ratio
    try:
        for arm in ('HIGH', 'LOW'):
            lat = dg.simulate_design(kind, n, arm, gen if gen is not None else rng, phases=(r1 * k, r2 * k, k),
                                     cadence=k, p2_odds=ODDS[odds], chi=chi, resto_mix=(1, 0), choice_every=k)
            out[arm] = np.ones(n) if kind == 'rival_au' else lat['ratings'][:, r1 + r2 - 1].astype(float)
    finally:
        mg.NUF, mg.NUR = NUF0, NUR0
    return out


if __name__ == '__main__':
    coup, e = edges()
    print("KGi-DISS-I037 part B stage 1 (seed 134200)\n")
    print("Coupling edges from records/couple.csv: " + json.dumps(e))
    rows = []
    for design in DESIGNS:
        r1, r2, k, odds = design
        pts = points(ODDS[odds], e['c_edge'])
        pools = {p[0]: multipliers('gate', design, p[1], p[2], p[3]) for p in pts}
        print(f"design rounds {r1}+{r2}, {k} draws, {odds}: legitimacy at probe time HIGH/LOW: " +
              "  ".join(f"{p[0]} {pools[p[0]]['HIGH'].mean():.2f}/{pools[p[0]]['LOW'].mean():.2f}" for p in pts), flush=True)
        for m, scheme, sig, integ in itertools.product((5, 7, 10), ('single', 'pair', 'pair2', 'did'),
                                                      (8.0, 12.0, 16.0), ('outcome', 'event')):
            if integ == 'event' and m != 7:
                continue                                  # per-event weight does not depend on m
            worst, wp = np.inf, None
            for p in pts:
                th = pg.theta(pg.probe_stat(pools[p[0]]['HIGH'], p[4], m, scheme, sig, integ, rng),
                              pg.probe_stat(pools[p[0]]['LOW'], p[4], m, scheme, sig, integ, rng))
                if th < worst:
                    worst, wp = th, p[0]
            rows.append(dict(r1=r1, r2=r2, k=k, odds=odds, m=m, scheme=scheme, sigma=sig, integration=integ,
                             theta=worst, worst_point=wp, n=pg.n_asymptotic(worst),
                             reps=r1 + r2 + pg.REPS[scheme]))
    df = pd.DataFrame(rows)
    df.to_csv('records/probe_design_I037.csv', index=False)

    def table(schemes):
        o = df[(df.sigma == 12) & (df.integration == 'outcome') & df.scheme.isin(schemes)]
        ev = df[(df.sigma == 12) & (df.integration == 'event') & df.scheme.isin(schemes)]
        ev = ev[['r1', 'r2', 'k', 'odds', 'scheme', 'n', 'worst_point']].rename(columns={'n': 'n_event', 'worst_point': 'wp_event'})
        t = o.merge(ev, on=['r1', 'r2', 'k', 'odds', 'scheme'])
        t['n_max'] = t[['n', 'n_event']].max(axis=1)
        return t.sort_values(['n_max', 'reps'])

    sel = {}
    for tag, schemes in (('S1', ['single', 'pair', 'pair2']), ('S2', ['did'])):
        t = table(schemes)
        tb = t[t.reps <= 10]
        print(f"\n{tag}: best rows within 10 repetitions (sigma 12; n per arm; worst theory point)")
        print(tb.head(8)[['r1', 'r2', 'k', 'odds', 'm', 'scheme', 'reps', 'n', 'worst_point', 'n_event', 'wp_event', 'n_max']]
              .round(0).to_string(index=False))
        b = tb.iloc[0]
        sel[tag] = dict(r1=int(b.r1), r2=int(b.r2), k=int(b.k), odds=b.odds, m=int(b.m), scheme=b.scheme,
                        reps=int(b.reps), n=int(np.ceil(b.n_max)), n_outcome=float(b.n), n_event=float(b.n_event))
    sel['edges'] = e
    json.dump(sel, open('records/probe_design_I037_selected.json', 'w'), indent=1)
    print("\nselected: " + json.dumps({k: v for k, v in sel.items() if k != 'edges'}))

    b = sel['S1']
    q = df[(df.r1 == b['r1']) & (df.r2 == b['r2']) & (df.k == b['k']) & (df.odds == b['odds']) & (df.m == b['m'])]
    print("\nS1 design, all schemes, n per arm by forecast noise and integration rule:")
    print(q.pivot_table(index='scheme', columns=['integration', 'sigma'], values='n').round(0).to_string())
    print("\nS1 design and scheme, n per arm by evidence size m (sigma 12, per-outcome):")
    q = df[(df.r1 == b['r1']) & (df.r2 == b['r2']) & (df.k == b['k']) & (df.odds == b['odds']) &
           (df.scheme == b['scheme']) & (df.sigma == 12) & (df.integration == 'outcome')]
    print(q[['m', 'n', 'worst_point']].round(0).to_string(index=False))
