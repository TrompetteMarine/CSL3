"""I033 AD-S1: minimise rounds and humans by simulation (protocol frozen in
freezes/00_freeze_I033.yaml, addendum AD_S1_design_minimisation, before this ran).

Stage 1 (seed 133400): every design in the grid -> kappa (frozen rule), power
curves for H1a and the H1b conjunction (SId-S AND SId-BA) at a = .25 and .5,
n_min, n_F_min, session minutes.
Stage 2 (seed 133500): the 3 smallest-N designs with session <= 15 min, plus the
baseline -> false positives, worst shape M5, initial aspiration A0 .4/.6, rho
classification AUC.

Run from the repo root:
    python experiment/analysis/design_search_I033.py 1   # -> records/design_search_I033_stage1.{csv,txt}
    python experiment/analysis/design_search_I033.py 2   # -> records/design_search_I033_stage2.txt
"""
import itertools
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, 'experiment/analysis')
import market_generator as mg
import design_generator as dg
import stats_v2 as sv

STAGE = int(sys.argv[1])
NP, B = 12000, 200
NGRID = (40, 60, 80, 100, 130, 160, 200, 250, 320)
NFGRID = (20, 30, 40, 60, 80)
NUF0, NUR0 = mg.NUF, mg.NUR
EDGE = dict(s_star=0.895, ratio_star=0.2918)
R3_SHARE = .5595


def chi_min(ratio, p, mu_ref=.65):
    return (.3 + ratio * p / (1 - p) - p) / (mu_ref - p)


def points_for(p2):
    p = .77 * p2[0] + .23 * p2[1]
    return [('P0', 1.0, .25, .6), ('P1', 1.0, .25, .4), ('P2', 1.0, EDGE['ratio_star'], .4),
            ('P3', EDGE['s_star'], .25, .4), ('P4', 1.0, .25, chi_min(.25, p))]


def minutes(T, cad=5):
    return 5 + (2.0 * T + 4.5 * (T / cad) + 4 * (T / 15) + 30) / 60


def sim(rng, kind, arm, d, chi, s=1.0, ratio=.25, resto=(1, 0), reg3=None, a0=None, n=NP):
    mg.NUF, mg.NUR = NUF0 * s, NUF0 * s * ratio
    try:
        return dg.simulate_design(kind, n, arm, rng, phases=d['phases'], cadence=5,
                                  p2_odds=d['p2'], chi=chi, resto_mix=resto,
                                  reg3_fixed=reg3, a0=a0)
    finally:
        mg.NUF, mg.NUR = NUF0, NUR0


def cells(rng, kind, d, chi, s=1.0, ratio=.25, a0=None, full=True):
    out = dict(HM=sim(rng, kind, 'HIGH', d, chi, s, ratio, (1, 0), True, a0),
               LM=sim(rng, kind, 'LOW', d, chi, s, ratio, (1, 0), False, a0))
    if full:
        out['HF'] = sim(rng, kind, 'HIGH', d, chi, s, ratio, (0, 1), True, a0)
    return out


def latent_frac(lat):
    L = 100 * lat['ratings'].astype(float)
    i = lat['idx']
    end = L[:, i['end']].mean(1)
    depth = L[:, i['p1']].mean(1) - end
    rec = L[:, i['late']].mean(1) - end
    return rec.mean() / depth.mean()


def measured(rng, lat, a, kappa, shape='M2'):
    f, e, keep = dg.measure_design(lat, shape, a, rng)
    i = lat['idx']
    ok = dg.screens_design(f, e, lat['acc1'], keep, lat['phases'][0])
    end = f[:, i['end']].mean(1)
    late = f[:, i['late']].mean(1)
    return dict(ok=np.flatnonzero(ok),
                drop=f[:, i['p1']].mean(1) - f[:, i['p2']].mean(1),
                sel=f[:, i['p1a']].mean(1) - f[:, i['presel']].mean(1),
                cs=(late - end) - kappa * (f[:, i['p1b']].mean(1) - end),
                cf=(late - end) - kappa * (f[:, i['p1']].mean(1) - end),
                rec=late - end, e=e)


def conj_power(rng, H, L, n, b=B, composite=None):
    h1a = s_ = ba = cj = 0
    for _ in range(b):
        if composite is None:
            sh = rng.choice(H['ok'], n, replace=False)
            sl = rng.choice(L['ok'], n, replace=False)
            dH, dL = H['drop'][sh], L['drop'][sl]
            selH, csH, cfH, cfL = H['sel'][sh], H['cs'][sh], H['cf'][sh], L['cf'][sl]
        else:   # composite: (H3, L3, H4, L4) mixed per replicate
            H3, L3, H4, L4 = composite
            parts = []
            for X3, X4 in ((H3, H4), (L3, L4)):
                k3 = rng.binomial(n, R3_SHARE)
                a3 = rng.choice(X3['ok'], k3, replace=False); a4 = rng.choice(X4['ok'], n - k3, replace=False)
                parts.append({k: np.concatenate([X3[k][a3], X4[k][a4]]) for k in ('drop', 'sel', 'cs', 'cf')})
            ph, pl = parts
            dH, dL, selH, csH, cfH, cfL = ph['drop'], pl['drop'], ph['sel'], ph['cs'], ph['cf'], pl['cf']
        r1 = sv.wmw_one_sided(dL, dH)[0]
        top = selH > np.median(selH)
        r2 = sv._signed_rank_less(csH[top], .005)[0]
        r3 = sv.wmw_one_sided(cfH, cfL)[0]
        h1a += r1; s_ += r2; ba += r3; cj += (r2 and r3)
    return h1a / b, s_ / b, ba / b, cj / b


def full_power(rng, F, n, b=B):
    r = 0
    for _ in range(b):
        sf = rng.choice(F['ok'], n, replace=False)
        r += sv._signed_rank_less(-F['rec'][sf], .005)[0]
    return r / b


def interp_nmin(ns, ok_power):
    for k, (n, p) in enumerate(zip(ns, ok_power)):
        if p >= .9:
            if k == 0:
                return float(n)
            n0, p0 = ns[k - 1], ok_power[k - 1]
            return n0 + (.9 - p0) * (n - n0) / (p - p0)
    return np.inf


DESIGNS = [dict(phases=(150, 150, 150), p2=(.30, .15), name='baseline 150/150/150')]
for T1, T2, T3, p2 in itertools.product((40, 60), (60, 90, 120), (45, 75), ((.30, .15), (.25, .10))):
    DESIGNS.append(dict(phases=(T1, T2, T3), p2=p2, name=f"{T1}/{T2}/{T3} P2 {p2[0]:.2f}/{p2[1]:.2f}"))


def design_kappa(rng, d, pts, gate_cells):
    gmax = max(latent_frac(gate_cells[p[0]]['HM']) for p in pts)
    chis = sorted({round(p[3], 4) for p in pts})
    rmin = min(latent_frac(sim(rng, 'rival_au', 'HIGH', d, c, resto=(1, 0), reg3=True)) for c in chis)
    return .5 * (gmax + rmin), gmax, rmin


if STAGE == 1:
    rng = np.random.default_rng(133400)
    rows, curves = [], []
    for d in DESIGNS:
        pts = points_for(d['p2'])
        gc = {p[0]: cells(rng, 'gate', d, p[3], p[1], p[2]) for p in pts}
        kappa, gmax, rmin = design_kappa(rng, d, pts, gc)
        T = sum(d['phases'])
        res = dict(design=d['name'], T1=d['phases'][0], T2=d['phases'][1], T3=d['phases'][2],
                   p2=f"{d['p2'][0]:.2f}/{d['p2'][1]:.2f}", rounds=T, minutes=round(minutes(T), 1),
                   kappa=round(kappa, 3), gate_max_frac=round(gmax, 3), r3_min_frac=round(rmin, 3))
        for a in (.25, .5):
            worst_h1a, worst_cj, worst_f = [], [], []
            for p in pts:
                H = measured(rng, gc[p[0]]['HM'], a, kappa)
                L = measured(rng, gc[p[0]]['LM'], a, kappa)
                F = measured(rng, gc[p[0]]['HF'], a, kappa)
                ph1a, pcj = [], []
                for n in NGRID:
                    h1a, s_, ba, cj = conj_power(rng, H, L, n)
                    ph1a.append(h1a); pcj.append(cj)
                    curves.append(dict(design=d['name'], a=a, point=p[0], n=n, h1a=h1a, sids=s_, sidba=ba, conj=cj))
                pf = [full_power(rng, F, n) for n in NFGRID]
                worst_h1a.append(ph1a); worst_cj.append(pcj); worst_f.append(pf)
            both = np.minimum(np.min(worst_h1a, axis=0), np.min(worst_cj, axis=0))
            res[f'n_min_a{a}'] = interp_nmin(NGRID, both)
            res[f'h1a_nmin_a{a}'] = interp_nmin(NGRID, np.min(worst_h1a, axis=0))
            res[f'nF_min_a{a}'] = interp_nmin(NFGRID, np.min(worst_f, axis=0))
            res[f'total_N_a{a}'] = 2 * res[f'n_min_a{a}'] + res[f'nF_min_a{a}']
        rows.append(res)
        print(res, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv('records/design_search_I033_stage1.csv', index=False)
    pd.DataFrame(curves).to_csv('records/design_search_I033_stage1_curves.csv', index=False)
    with open('records/design_search_I033_stage1.txt', 'w') as fh:
        fh.write("I033 AD-S1 stage 1 (seed 133400; M2; B=200; n per cell post-exclusion)\n\n")
        fh.write(df.sort_values('total_N_a0.25').to_string(index=False))
        fh.write("\n")

if STAGE == 2:
    rng = np.random.default_rng(133500)
    df = pd.read_csv('records/design_search_I033_stage1.csv')
    cand = df[(df.minutes <= 15) & np.isfinite(df['total_N_a0.25'])].sort_values('total_N_a0.25').head(3)
    chosen = list(cand.design) + ['baseline 150/150/150']
    out = ["I033 AD-S1 stage 2 (seed 133500)\n"]
    for name in chosen:
        d = next(x for x in DESIGNS if x['name'] == name)
        row = df[df.design == name].iloc[0]
        kappa, n = row.kappa, int(np.ceil(row['n_min_a0.25'])) if np.isfinite(row['n_min_a0.25']) else 320
        n = min(n, 320)
        pts = points_for(d['p2'])
        out.append(f"=== {name}: rounds {row.rounds}, {row.minutes} min, kappa {kappa}, n_min(a=.25) {row['n_min_a0.25']:.0f}, "
                   f"n_F {row['nF_min_a0.25']}, total N {row['total_N_a0.25']:.0f}  (tested at n = {n})")
        # false positives
        r3 = {c: cells(rng, 'rival_au', d, c, full=False) for c in (.4, .6)}
        r4 = cells(rng, 'rival_us', d, .6, full=False)
        for a in (.25, .5, 1.0):
            line = [f"  a={a}:"]
            for c in (.4, .6):
                H, L = measured(rng, r3[c]['HM'], a, kappa), measured(rng, r3[c]['LM'], a, kappa)
                line.append(f"R3 chi{c} conj {conj_power(rng, H, L, n)[3]:.3f}")
            comp = tuple(measured(rng, x, a, kappa) for x in (r3[.6]['HM'], r3[.6]['LM'], r4['HM'], r4['LM']))
            line.append(f"composite conj {conj_power(rng, None, None, n, composite=comp)[3]:.3f}")
            for c in (.4,):
                hi = dict(r3[c]['HM']); lo = dict(r3[c]['LM'])
                for x in (hi, lo):
                    rr = x['ratings'].astype(np.float64); e5 = 1 - (1 - .01) ** 5
                    o = np.empty_like(rr); o[:, 0] = rr[:, 0]
                    for k in range(1, rr.shape[1]):
                        o[:, k] = o[:, k - 1] + e5 * (rr[:, k] - o[:, k - 1])
                    x['ratings'] = o.astype(np.float32)
                H, L = measured(rng, hi, a, kappa), measured(rng, lo, a, kappa)
                line.append(f"R3-int.01 conj {conj_power(rng, H, L, n)[3]:.3f}")
            out.append("  ".join(line))
        # worst shape and initial aspiration
        for label, shape, a0 in (('M5 shape', 'M5', None), ('A0 .4', 'M2', .4), ('A0 .6', 'M2', .6)):
            worst = []
            for p in pts:
                g = cells(rng, 'gate', d, p[3], p[1], p[2], a0=a0, full=False)
                H, L = measured(rng, g['HM'], .25, kappa, shape), measured(rng, g['LM'], .25, kappa, shape)
                h1a, s_, ba, cj = conj_power(rng, H, L, n)
                worst.append((p[0], h1a, cj))
            out.append(f"  {label}, a=.25, n={n}: " + "  ".join(f"{p}: H1a {h:.2f} conj {c:.2f}" for p, h, c in worst))
        # rho classification from the LOW x MOD entitlement slider
        g = cells(rng, 'gate', d, .4, full=False)['LM']
        f, e, keep = dg.measure_design(g, 'M2', .25, rng)
        i = g['idx']
        r1 = i['p1'].stop
        chg = e[:, r1 - 4:r1].mean(1) - e[:, i['end']].mean(1)
        fast = g['rho'] == .02
        auc = (chg[fast][:, None] > chg[~fast][None, :]).mean() + .5 * (chg[fast][:, None] == chg[~fast][None, :]).mean()
        out.append(f"  rho classification AUC (.02 vs .002; entitlement drop end-P1 -> end-P2, LOW x MOD, a=.25): {auc:.3f}")
        print("\n".join(out[-6:]), flush=True)
    open('records/design_search_I033_stage2.txt', 'w').write("\n".join(out) + "\n")
