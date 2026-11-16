"""KGi-DISS-I043: what changes statistically when the probe becomes a prediction market
(freeze 00_freeze_I043.yaml). One pair's evidence is a record of ten closes (as before), the
other pair's is a source's forecast with weight kappa_s * g; each market also carries a bet.
The outcome rounds are the same random variables as design Y. Seed 139000.
    python experiment/analysis/basket_cert_I043.py > records/basket_cert_I043.txt
"""
import numpy as np

import estimand_core_I038 as ec
import probe_generator as pg
import twins_I040 as tw
import yoked_analysis as ya

rng = np.random.default_rng(139000)
N, B = 20000, 2000
PT = {p[0]: p for p in ec.GATE_POINTS}
PTS = ('P0', 'P1', 'P2', 'P3', 'P4')
KS = (0.5, 0.35, 0.2)
SIG_R, SIG_F, SIG_BET, BAND, PRICE = 5.8, 12.0, 8.0, 5.0, 50.0
r5 = lambda x: np.clip(np.round(x / 5) * 5, 0, 100)


def ratings(m, a=0.5):
    return r5(50 + a * (100 * m - 50) + rng.normal(0, SIG_R, m.shape))


def market(w, e):
    """one market: revision (post - pre) and the bet, for revision weight w and evidence e"""
    n = len(w)
    b0 = np.clip(rng.normal(pg.PRIOR_MU, pg.PRIOR_SD, n), 5, 95)
    pre = r5(b0 + rng.normal(0, SIG_F, n))
    belief = b0 + w * (100 * e - b0)
    post = r5(belief + rng.normal(0, SIG_F, n))
    z = belief + rng.normal(0, SIG_BET, n)
    return post - pre, np.where(z > PRICE + BAND, 1, np.where(z < PRICE - BAND, -1, 0))


def probe(l, c, rule, ks):
    """T and its two halves (record pair, source pair), and the bet statistic, for one arm"""
    g = 1 - c * (1 - l)
    off = rng.random(len(l)) < 0.10
    w_rec = np.where(off, 0.0, pg.weight(g, ec.M, rule))
    w_src = np.where(off, 0.0, ks * g)
    (dr1, br1), (dr0, br0) = market(w_rec, .9), market(w_rec, .1)
    (ds1, bs1), (ds0, bs0) = market(w_src, .9), market(w_src, .1)
    t_rec, t_src = dr1 - dr0, ds1 - ds0
    return dict(T=.5 * (t_rec + t_src), Tr=t_rec, Ts=t_src, B=.5 * ((br1 - br0) / 2 + (bs1 - bs0) / 2))


def cohort(b, c, rule, ks):
    out = {}
    for arm in tw.ARMS:
        out[arm] = probe(b['L'][arm][:, -1], c, rule, ks)
        out[arm].update(F=ratings(b['L'][arm]), E=ratings(b['A'][arm]), wins=b['wins'][arm])
    return out


def score(C, n):
    i = rng.integers(0, N, (B, n))
    H, L = C['HIGH'], C['LOW']
    d = dict(fh=H['F'][i, -1], fl=L['F'][i, -1], eh=H['E'][i, -1], el=L['E'][i, -1], th=H['T'][i], tl=L['T'][i],
             fl_rounds=L['F'][i][:, :, 2:6], wl=L['wins'][i][:, :, 3:6] / tw.K, jit=rng.uniform(-.01, .01, (B, n)))
    s = {k: (v.mean() if v.dtype == bool else v) for k, v in ya.decisions(d).items()}
    s['D1_rec'] = (ya.fieller(H['Tr'][i], L['Tr'][i])[2] < 1).mean()
    s['D1_src'] = (ya.fieller(H['Ts'][i], L['Ts'][i])[2] < 1).mean()
    s['BET'] = (ya.signed_rank_z(L['B'][i] - H['B'][i]) > ya.ZC).mean()
    s['bet_h'], s['bet_l'] = H['B'][i].mean(), L['B'][i].mean()
    return s


KEYS = ('H1a', 'D1', 'PAIR', 'FREEZE', 'ASSOC_H', 'BET', 'D1_rec', 'D1_src')
head = "  ".join(f"{k:>8}" for k in KEYS)
line = lambda s: "  ".join(f"{s[k]:8.3f}" for k in KEYS)
print("KGi-DISS-I043: the probe as a prediction market (20,000 simulated pairs per gate point; 2,000 samples; seed 139000)")
print("one record pair (weight as before) and one source pair (weight kappa_s * g); bets by the assumed rule; one-sided .005\n")
lat = {k: tw.twins(PT[k], N, rng, same_person=False, indep_choice=True) for k in PTS}

print("1. decision rates at 72 pairs, full coupling")
print("   rule     kappa_s point   " + head + "   mean psi-hat   mean bet statistic HIGH | LOW")
for r in ('event', 'outcome'):
    for ks in KS:
        for k in PTS:
            s = score(cohort(lat[k], 1.0, r, ks), 72)
            print(f"   {r:7s}  {ks:4.2f}    {k}      " + line(s) + f"   {s['psi'].mean():.3f}          {s['bet_h']:.3f} | {s['bet_l']:.3f}", flush=True)

print("\n2. ratings move, the gain does not (coupling 0), one-update rule, 72 pairs")
print("   kappa_s point   " + head + "   mean psi-hat")
for ks in KS:
    for k in ('P1', 'P4'):
        s = score(cohort(lat[k], 0.0, 'event', ks), 72)
        print(f"   {ks:4.2f}    {k}      " + line(s) + f"   {s['psi'].mean():.3f}", flush=True)

print("\n3. the anchoring edge (P4) by number of pairs, one-update rule: D1 | confirmatory pair | BET")
for ks in KS:
    C = cohort(lat['P4'], 1.0, 'event', ks)
    row = []
    for n in (72, 96, 120, 144, 192):
        s = score(C, n)
        row.append(f"{n}: {s['D1']:.3f} | {s['PAIR']:.3f} | {s['BET']:.3f}")
    print(f"   kappa_s {ks:4.2f}   " + "     ".join(row), flush=True)
