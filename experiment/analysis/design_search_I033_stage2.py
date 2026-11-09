"""I033 AD-S2 stage 2 (selection amended after stage 1, before this ran; see
freezes/00_freeze_I033.yaml AD_S2_after_stage1). Seed 133500.

For the 3 smallest-N designs at a = .5 with session <= 18 min, plus the baseline:
  - conjunction false positives vs R3 (chi .4, .6), the no-gate composite and
    R3-int (eta .01) at n_min(a=.5) for a in {.25, .5, 1}
  - worst shape M5 and initial aspiration A0 .4 / .6 at a = .5, n_min(a=.5)
  - power at a = .25 with n = 320 (record)
  - rho classification AUC (.002 vs .02) from the LOW x MOD entitlement drop
For the best design: the same geometry at rating cadence 3 (power curve at
a = .25 and .5, n_min, session minutes).
Run from the repo root:
    python experiment/analysis/design_search_I033_stage2.py > records/design_search_I033_stage2.txt
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, 'experiment/analysis')
import market_generator as mg
import design_generator as dg
import stats_v2 as sv

rng = np.random.default_rng(133500)
NP, B = 12000, 200
NGRID = (40, 60, 80, 100, 130, 160, 200, 250, 320)
NUF0, NUR0 = mg.NUF, mg.NUR
S_STAR, R_STAR, R3_SHARE = 0.895, 0.2918, .5595


def chi_min(ratio, p, mu_ref=.65):
    return (.3 + ratio * p / (1 - p) - p) / (mu_ref - p)


def points_for(p2):
    p = .77 * p2[0] + .23 * p2[1]
    return [('P0', 1.0, .25, .6), ('P1', 1.0, .25, .4), ('P2', 1.0, R_STAR, .4),
            ('P3', S_STAR, .25, .4), ('P4', 1.0, .25, chi_min(.25, p))]


def minutes(T, cad):
    return 5 + (2.0 * T + 4.5 * (T / cad) + 4 * (T / 15) + 30) / 60


def sim(kind, arm, d, chi, s=1.0, ratio=.25, resto=(1, 0), reg3=None, a0=None):
    mg.NUF, mg.NUR = NUF0 * s, NUF0 * s * ratio
    try:
        return dg.simulate_design(kind, NP, arm, rng, phases=d['phases'], cadence=d['cad'],
                                  p2_odds=d['p2'], chi=chi, resto_mix=resto,
                                  reg3_fixed=reg3, a0=a0)
    finally:
        mg.NUF, mg.NUR = NUF0, NUR0


def cells(kind, d, chi, s=1.0, ratio=.25, a0=None):
    return dict(HM=sim(kind, 'HIGH', d, chi, s, ratio, (1, 0), True, a0),
                LM=sim(kind, 'LOW', d, chi, s, ratio, (1, 0), False, a0))


def latent_frac(lat):
    L = 100 * lat['ratings'].astype(float)
    i = lat['idx']
    end = L[:, i['end']].mean(1)
    return (L[:, i['late']].mean(1) - end).mean() / (L[:, i['p1']].mean(1) - end).mean()


def measured(lat, a, kappa, shape='M2'):
    f, e, keep = dg.measure_design(lat, shape, a, rng)
    i = lat['idx']
    ok = dg.screens_design(f, e, lat['acc1'], keep, lat['phases'][0])
    end = f[:, i['end']].mean(1)
    late = f[:, i['late']].mean(1)
    return dict(ok=np.flatnonzero(ok), drop=f[:, i['p1']].mean(1) - f[:, i['p2']].mean(1),
                sel=f[:, i['p1a']].mean(1) - f[:, i['presel']].mean(1),
                cs=(late - end) - kappa * (f[:, i['p1b']].mean(1) - end),
                cf=(late - end) - kappa * (f[:, i['p1']].mean(1) - end))


def power(H, L, n, composite=None):
    h1a = cj = 0
    for _ in range(B):
        if composite is None:
            sh = rng.choice(H['ok'], n, replace=False); sl = rng.choice(L['ok'], n, replace=False)
            dH, dL, selH, csH, cfH, cfL = (H['drop'][sh], L['drop'][sl], H['sel'][sh], H['cs'][sh],
                                          H['cf'][sh], L['cf'][sl])
        else:
            parts = []
            for X3, X4 in ((composite[0], composite[2]), (composite[1], composite[3])):
                k3 = rng.binomial(n, R3_SHARE)
                a3 = rng.choice(X3['ok'], k3, replace=False); a4 = rng.choice(X4['ok'], n - k3, replace=False)
                parts.append({k: np.concatenate([X3[k][a3], X4[k][a4]]) for k in ('drop', 'sel', 'cs', 'cf')})
            ph, pl = parts
            dH, dL, selH, csH, cfH, cfL = ph['drop'], pl['drop'], ph['sel'], ph['cs'], ph['cf'], pl['cf']
        h1a += sv.wmw_one_sided(dL, dH)[0]
        top = selH > np.median(selH)
        cj += (sv._signed_rank_less(csH[top], .005)[0] and sv.wmw_one_sided(cfH, cfL)[0])
    return h1a / B, cj / B


def ema_cells(c, eta):
    out = {}
    for k, lat in c.items():
        x = lat['ratings'].astype(np.float64); e5 = 1 - (1 - eta) ** 5
        o = np.empty_like(x); o[:, 0] = x[:, 0]
        for j in range(1, x.shape[1]):
            o[:, j] = o[:, j - 1] + e5 * (x[:, j] - o[:, j - 1])
        d = dict(lat); d['ratings'] = o.astype(np.float32); out[k] = d
    return out


def kappa_for(d, pts, gate):
    gmax = max(latent_frac(gate[p[0]]['HM']) for p in pts)
    rmin = min(latent_frac(sim('rival_au', 'HIGH', d, c, resto=(1, 0), reg3=True))
               for c in sorted({round(p[3], 4) for p in pts}))
    return .5 * (gmax + rmin)


def nmin(curve):
    for k, (n, p) in enumerate(zip(NGRID, curve)):
        if p >= .9:
            return float(n) if k == 0 else NGRID[k - 1] + (.9 - curve[k - 1]) * (n - NGRID[k - 1]) / (p - curve[k - 1])
    return np.inf


st1 = pd.read_csv('records/design_search_I033_stage1.csv')
sel = st1[(st1.minutes <= 18) & np.isfinite(st1['total_N_a0.5'])].sort_values('total_N_a0.5').head(3)
chosen = list(sel.design) + ['baseline 150/150/150']
print("I033 AD-S2 stage 2 (seed 133500)\n")
for name in chosen:
    r = st1[st1.design == name].iloc[0]
    d = dict(phases=(int(r.T1), int(r.T2), int(r.T3)), p2=tuple(float(x) for x in r.p2.split('/')), cad=5)
    pts = points_for(d['p2'])
    n = int(min(320, np.ceil(r['n_min_a0.5'])))
    print(f"=== {name}: {r.rounds} rounds, {r.minutes} min; n_min a=.5 {r['n_min_a0.5']:.0f}, a=.25 "
          f"{r['n_min_a0.25']}; kappa {r.kappa}; tested at n = {n}", flush=True)
    gate = {p[0]: cells('gate', d, p[3], p[1], p[2]) for p in pts}
    kappa = kappa_for(d, pts, gate)
    r3 = {c: cells('rival_au', d, c) for c in (.4, .6)}
    r4 = cells('rival_us', d, .6)
    r3i = ema_cells(r3[.4], .01)
    for a in (.25, .5, 1.0):
        fp = [f"R3 chi.4 {power(measured(r3[.4]['HM'], a, kappa), measured(r3[.4]['LM'], a, kappa), n)[1]:.3f}",
              f"R3 chi.6 {power(measured(r3[.6]['HM'], a, kappa), measured(r3[.6]['LM'], a, kappa), n)[1]:.3f}",
              f"composite {power(None, None, n, composite=tuple(measured(x, a, kappa) for x in (r3[.6]['HM'], r3[.6]['LM'], r4['HM'], r4['LM'])))[1]:.3f}",
              f"R3-int.01 {power(measured(r3i['HM'], a, kappa), measured(r3i['LM'], a, kappa), n)[1]:.3f}"]
        print(f"  false positives (conjunction), a={a}: " + "  ".join(fp), flush=True)
    for label, shape, a0 in (('M5 shape', 'M5', None), ('A0 .4', 'M2', .4), ('A0 .6', 'M2', .6)):
        res = []
        for p in pts:
            g = gate[p[0]] if a0 is None else cells('gate', d, p[3], p[1], p[2], a0=a0)
            h1a, cj = power(measured(g['HM'], .5, kappa, shape), measured(g['LM'], .5, kappa, shape), n)
            res.append(f"{p[0]} {h1a:.2f}/{cj:.2f}")
        print(f"  {label}, a=.5, n={n} (H1a/conj): " + "  ".join(res), flush=True)
    res = []
    for p in pts:
        h1a, cj = power(measured(gate[p[0]]['HM'], .25, kappa), measured(gate[p[0]]['LM'], .25, kappa), 320)
        res.append(f"{p[0]} {h1a:.2f}/{cj:.2f}")
    print("  a=.25, n=320 (H1a/conj): " + "  ".join(res), flush=True)
    g = cells('gate', d, .4)['LM']
    f, e, keep = dg.measure_design(g, 'M2', .25, rng)
    i = g['idx']; r1 = i['p1'].stop
    chg = e[:, r1 - 4:r1].mean(1) - e[:, i['end']].mean(1)
    fast = g['rho'] == .02
    auc = (chg[fast][:, None] > chg[~fast][None, :]).mean() + .5 * (chg[fast][:, None] == chg[~fast][None, :]).mean()
    print(f"  rho classification AUC (LOW x MOD entitlement drop, a=.25): {auc:.3f}\n", flush=True)

# best design at cadence 3
r = st1[st1.design == chosen[0]].iloc[0]
d = dict(phases=(int(r.T1), int(r.T2), int(r.T3)), p2=tuple(float(x) for x in r.p2.split('/')), cad=3)
pts = points_for(d['p2'])
gate = {p[0]: cells('gate', d, p[3], p[1], p[2]) for p in pts}
kappa = kappa_for(d, pts, gate)
T = sum(d['phases'])
print(f"=== {chosen[0]} at cadence 3: {minutes(T, 3):.1f} min (cadence 5: {minutes(T, 5):.1f}); kappa {kappa:.3f}")
for a in (.25, .5):
    worst_h, worst_c = [], []
    for p in pts:
        H, L = measured(gate[p[0]]['HM'], a, kappa), measured(gate[p[0]]['LM'], a, kappa)
        cur = [power(H, L, n) for n in NGRID]
        worst_h.append([c[0] for c in cur]); worst_c.append([c[1] for c in cur])
    both = np.minimum(np.min(worst_h, axis=0), np.min(worst_c, axis=0))
    print(f"  a={a}: worst-point power by n {dict(zip(NGRID, np.round(both, 2)))}  n_min {nmin(both):.0f}", flush=True)
