"""I033 AD-B1: a <= 10-period task carrying the evidence of hundreds of rounds
(protocol frozen in freezes/00_freeze_I033.yaml, AD_B1_batched_periods, before
this ran). Seed 133600.
Run from the repo root:
    python experiment/analysis/batched_periods_I033.py > records/batched_periods_I033.txt
"""
import itertools
import sys

import numpy as np

sys.path.insert(0, 'experiment/analysis')
import market_generator as mg
import design_generator as dg
import stats_v2 as sv

rng = np.random.default_rng(133600)
NP, B = 12000, 200
NGRID = (60, 100, 160, 250, 320)
NUF0, NUR0 = mg.NUF, mg.NUR
S_STAR, R_STAR, R3_SHARE = 0.895, 0.2918, .5595
SIG0 = dg.SIG_EPS


def chi_min(ratio, p, mu_ref=.65):
    return (.3 + ratio * p / (1 - p) - p) / (mu_ref - p)


P2ODDS = (.30, .15)
PTS = [('P0', 1.0, .25, .6), ('P1', 1.0, .25, .4), ('P2', 1.0, R_STAR, .4),
       ('P3', S_STAR, .25, .4), ('P4', 1.0, .25, chi_min(.25, .77 * .30 + .23 * .15))]


def sim(kind, arm, phases, k, cad, chi, s=1.0, ratio=.25, reg3=None, resto=(1, 0)):
    mg.NUF, mg.NUR = NUF0 * s, NUF0 * s * ratio
    try:
        return dg.simulate_design(kind, NP, arm, rng, phases=phases, cadence=cad,
                                  p2_odds=P2ODDS, chi=chi, resto_mix=resto,
                                  reg3_fixed=reg3, choice_every=k)
    finally:
        mg.NUF, mg.NUR = NUF0, NUR0


# ------------------------------------------------------------------ B1 equivalence
print("AD-B1 batched periods (seed 133600)\n")
print("B1  latent trust x100 at period ends: per-round task (choice every draw, ratings every 5)")
print("    vs batched task (choice + rating every 25 draws); geometry 50/100/75 = 2/4/3 periods")
GEO = (50, 100, 75)
worst = 0.0
for name, kind, s, ratio, chi in [(p[0], 'gate', p[1], p[2], p[3]) for p in PTS] + [('R3', 'rival_au', 1.0, .25, .4)]:
    line = [f"  {name:3s}"]
    for cell, arm, reg3 in (('HM', 'HIGH', True), ('LM', 'LOW', False)):
        a = sim(kind, arm, GEO, 1, 5, chi, s, ratio, reg3)
        b = sim(kind, arm, GEO, 25, 25, chi, s, ratio, reg3)
        ta = 100 * a['ratings'][:, 4::5].astype(float).mean(0)
        tb = 100 * b['ratings'].astype(float).mean(0)
        rel = np.max(np.abs(tb - ta) / np.maximum(ta, 1))
        worst = max(worst, rel)
        line.append(f"{cell} per-round " + " ".join(f"{x:4.0f}" for x in ta) +
                    f" | batched " + " ".join(f"{x:4.0f}" for x in tb) + f" | max rel diff {rel:.3f}")
    print("\n      ".join(line))
print(f"  worst relative difference over all cells and periods: {worst:.3f}  (EB1: <= .10)\n")


# ------------------------------------------------------------------ B2 power
def idx_for(periods):
    r1, r2, r3 = periods
    return dict(p1=slice(0, r1), p2=slice(r1, r1 + r2), p1a=slice(0, r1 // 2),
                p1b=slice(r1 // 2, r1), presel=slice(r1, r1 + r2 // 2 + (r2 % 2) - (1 if r2 % 2 else 0) + (0 if r2 % 2 else 0)),
                end=slice(r1 + r2 - 2, r1 + r2), late=slice(r1 + r2 + r3 - 2, r1 + r2 + r3))


def latent_frac(lat, ix):
    L = 100 * lat['ratings'].astype(float)
    end = L[:, ix['end']].mean(1)
    return (L[:, ix['late']].mean(1) - end).mean() / (L[:, ix['p1']].mean(1) - end).mean()


def measured(lat, a, kappa, ix, sig):
    dg.SIG_EPS = sig
    try:
        f, e, keep = dg.measure_design(lat, 'M2', a, rng)
    finally:
        dg.SIG_EPS = SIG0
    ok = dg.screens_design(f, e, lat['acc1'], keep, lat['phases'][0])
    end = f[:, ix['end']].mean(1)
    late = f[:, ix['late']].mean(1)
    return dict(ok=np.flatnonzero(ok), drop=f[:, ix['p1']].mean(1) - f[:, ix['p2']].mean(1),
                sel=f[:, ix['p1a']].mean(1) - f[:, ix['presel']].mean(1),
                cs=(late - end) - kappa * (f[:, ix['p1b']].mean(1) - end),
                cf=(late - end) - kappa * (f[:, ix['p1']].mean(1) - end))


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
                parts.append({q: np.concatenate([X3[q][a3], X4[q][a4]]) for q in ('drop', 'sel', 'cs', 'cf')})
            ph, pl = parts
            dH, dL, selH, csH, cfH, cfL = ph['drop'], pl['drop'], ph['sel'], ph['cs'], ph['cf'], pl['cf']
        h1a += sv.wmw_one_sided(dL, dH)[0]
        top = selH > np.median(selH)
        cj += (sv._signed_rank_less(csH[top], .005)[0] and sv.wmw_one_sided(cfH, cfL)[0])
    return h1a / B, cj / B


def nmin(curve):
    for j, (n, p) in enumerate(zip(NGRID, curve)):
        if p >= .9:
            return float(n) if j == 0 else NGRID[j - 1] + (.9 - curve[j - 1]) * (n - NGRID[j - 1]) / (p - curve[j - 1])
    return np.inf


print("B2  batched designs: n_min per cell (H1a AND conjunction >= .90 at every inside point), M2")
best = None
summary = []
for k, periods in itertools.product((20, 25), ((2, 4, 3), (2, 5, 3))):
    phases = tuple(k * p for p in periods)
    ix = idx_for(periods)
    ix['presel'] = slice(periods[0], periods[0] + periods[1] - 2)
    gate = {p[0]: (sim('gate', 'HIGH', phases, k, k, p[3], p[1], p[2], True),
                   sim('gate', 'LOW', phases, k, k, p[3], p[1], p[2], False)) for p in PTS}
    gmax = max(latent_frac(gate[p[0]][0], ix) for p in PTS)
    r3 = {c: (sim('rival_au', 'HIGH', phases, k, k, c, reg3=True),
              sim('rival_au', 'LOW', phases, k, k, c, reg3=False)) for c in sorted({round(p[3], 4) for p in PTS})}
    rmin = min(latent_frac(r3[c][0], ix) for c in r3)
    kappa = .5 * (gmax + rmin)
    for sig in (10.0, 5.8):
        row = dict(k=k, periods=periods, draws=sum(phases), sigma=sig, kappa=round(kappa, 3))
        for a in (.25, .5, 1.0):
            worst_h, worst_c = [], []
            for p in PTS:
                H = measured(gate[p[0]][0], a, kappa, ix, sig)
                L = measured(gate[p[0]][1], a, kappa, ix, sig)
                cur = [power(H, L, n) for n in NGRID]
                worst_h.append([c[0] for c in cur]); worst_c.append([c[1] for c in cur])
            both = np.minimum(np.min(worst_h, 0), np.min(worst_c, 0))
            row[f'a{a}'] = nmin(both)
            row[f'a{a}_curve'] = dict(zip(NGRID, np.round(both, 2)))
        summary.append(row)
        print(f"  k={k} periods={periods} ({sum(periods)} periods, {sum(phases)} draws) sigma={sig} kappa={kappa:.3f}: "
              f"n_min a=.25 {row['a0.25']:.0f}  a=.5 {row['a0.5']:.0f}  a=1 {row['a1.0']:.0f}", flush=True)
        print(f"      worst-point power by n: a=.25 {row['a0.25_curve']}  a=.5 {row['a0.5_curve']}  a=1 {row['a1.0_curve']}", flush=True)
        if np.isfinite(row['a0.5']) and (best is None or row['a0.5'] < best[0]['a0.5']):
            best = (row, gate, r3, ix, kappa, phases, k)

# ------------------------------------------------------------------ B3 specificity
if best is not None:
    row, gate, r3, ix, kappa, phases, k = best
    n = int(np.ceil(row['a0.5']))
    r4 = (sim('rival_us', 'HIGH', phases, k, k, .6, reg3=True), sim('rival_us', 'LOW', phases, k, k, .6, reg3=False))
    print(f"\nB3  specificity of the best design at a=.5 (k={k}, periods={row['periods']}, sigma={row['sigma']}, n={n})")
    for a in (.5, 1.0):
        out = []
        for c in (.4, .6):
            if c in r3:
                out.append(f"R3 chi{c} {power(measured(r3[c][0], a, kappa, ix, row['sigma']), measured(r3[c][1], a, kappa, ix, row['sigma']), n)[1]:.3f}")
        if .6 in r3:
            comp = tuple(measured(x, a, kappa, ix, row['sigma']) for x in (r3[.6][0], r3[.6][1], r4[0], r4[1]))
            out.append(f"composite {power(None, None, n, composite=comp)[1]:.3f}")
        print(f"  a={a}: " + "  ".join(out))
