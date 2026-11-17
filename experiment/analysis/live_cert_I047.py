"""KGi-DISS-I047: what changes statistically when both goods' clearing prices are on screen
(freeze 00_freeze_I047.yaml, claim C1). A participant who sees both price paths knows after
round 1 which good is cheaper. A share q of participants, drawn independently for each
member of a pair, then orders the better good in every deprivation round; the others choose
as the model does. Round 1 is chosen as before by everyone. The kernel gets no other input
from the display (assumption A_CF of the freeze).

Kernel, ratings, forecasts, bets and tests are those of basket_cert_I043.py; the functions
market, probe, cohort and score are copied from it. Seed 141000.
    python experiment/analysis/live_cert_I047.py > records/live_cert_I047.txt
"""
import re
import sys

import numpy as np

import estimand_core_I038 as ec
import probe_generator as pg
import twins_I040 as tw
import yoked_analysis as ya

rng = np.random.default_rng(141000)
mrng = np.random.default_rng(141001)          # who is informed: its own stream, so that q = 0 and q = 1 use none of the other
N, B = 20000, 2000
PT = {p[0]: p for p in ec.GATE_POINTS}
PTS = ('P0', 'P1', 'P2', 'P3', 'P4')
KS = (0.5, 0.35, 0.2)
QS = (0.0, 0.5, 1.0)
SIG_R, SIG_F, SIG_BET, BAND, PRICE = 5.8, 12.0, 8.0, 5.0, 50.0
TOL = 0.03                                      # the frozen tolerance of the decision rule and of the comparison with I043
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


def pairs(k, q, regime=None):
    """20,000 pairs at gate point k with a share q of informed members"""
    if q == 0:
        informed = None
    elif q == 1:
        informed = {a: np.ones(N, bool) for a in tw.ARMS}
    else:
        informed = {a: mrng.random(N) < q for a in tw.ARMS}
    return tw.twins(PT[k], N, rng, same_person=False, indep_choice=True, regime=regime, informed=informed)


def record_I043(path='records/basket_cert_I043.txt'):
    """{(rule, kappa_s, point): [H1a, D1, PAIR, FREEZE, ASSOC_H, BET, D1_rec, D1_src]} from section 1 of the I043 record"""
    out = {}
    for line in open(path):
        m = re.match(r'\s+(event|outcome)\s+(0\.\d+)\s+(P\d)\s+((?:\d\.\d+\s+){8})', line)
        if m:
            out[(m.group(1), float(m.group(2)), m.group(3))] = [float(x) for x in m.group(4).split()]
    return out


KEYS = ('H1a', 'D1', 'PAIR', 'K3', 'FREEZE', 'ASSOC_H', 'ASSOC_L', 'TOPQ', 'BET', 'D1_rec', 'D1_src')
OLD = ('H1a', 'D1', 'PAIR', 'FREEZE', 'ASSOC_H', 'BET', 'D1_rec', 'D1_src')
head = "  ".join(f"{k:>7}" for k in KEYS)
line = lambda s: "  ".join(f"{s[k]:7.3f}" for k in KEYS)

print("KGi-DISS-I047: both goods' prices on screen (20,000 simulated pairs per cell; 2,000 samples; seed 141000)")
print("q = share of participants who order the better good in every deprivation round; one-sided .005 throughout\n")

lat = {(k, q): pairs(k, q) for q in QS for k in PTS}
print("0. the simulated pairs: legitimacy at probe time HIGH / LOW; aspiration HIGH / LOW; filled share in deprivation rounds HIGH / LOW;")
print("   pairs with the same good in every deprivation round")
for q in QS:
    for k in PTS:
        b = lat[(k, q)]
        dep = [b['wins'][a][:, tw.R1:].mean() / tw.K for a in tw.ARMS]
        print(f"   q {q:3.1f}  {k}   L {b['L']['HIGH'][:, -1].mean():.3f} / {b['L']['LOW'][:, -1].mean():.3f}   "
              f"A {b['A']['HIGH'][:, -1].mean():.3f} / {b['A']['LOW'][:, -1].mean():.3f}   "
              f"filled {dep[0]:.3f} / {dep[1]:.3f}   same good {b['same_choice'].mean():.3f}", flush=True)

print("\n1. decision rates at 72 pairs, full coupling")
print("   q    rule     kappa_s point   " + head + "   mean psi-hat   mean bet statistic HIGH | LOW")
S = {}
for q in QS:
    for r in ('event', 'outcome'):
        for ks in KS:
            for k in PTS:
                s = S[(q, r, ks, k)] = score(cohort(lat[(k, q)], 1.0, r, ks), 72)
                print(f"   {q:3.1f}  {r:7s}  {ks:4.2f}    {k}      " + line(s) + f"   {s['psi'].mean():.3f}          {s['bet_h']:.3f} | {s['bet_l']:.3f}", flush=True)

print("\n2. sizes at 72 pairs, one-update rule")
print("   (a) ratings move, the gain does not (coupling 0)")
print("   q    kappa_s point   " + head + "   mean psi-hat")
sizes = []
for q in QS:
    for ks in KS:
        for k in ('P1', 'P4'):
            s = score(cohort(lat[(k, q)], 0.0, 'event', ks), 72)
            sizes += [s['D1'], s['BET']]
            print(f"   {q:3.1f}  {ks:4.2f}    {k}      " + line(s) + f"   {s['psi'].mean():.3f}", flush=True)
print("   (b) both members of a pair on the LOW board, paper's values (P1)")
print("   q    kappa_s         " + head + "   mean psi-hat")
for q in QS:
    nul = pairs('P1', q, regime={'HIGH': 'LOW', 'LOW': 'LOW'})
    for ks in KS:
        s = score(cohort(nul, 1.0, 'event', ks), 72)
        sizes += [s['H1a'], s['D1'], s['BET']]
        print(f"   {q:3.1f}  {ks:4.2f}            " + line(s) + f"   {s['psi'].mean():.3f}", flush=True)

print("\n3. the anchoring edge (P4) by number of pairs, one-update rule: D1 | confirmatory pair | BET")
for q in QS:
    for ks in KS:
        C = cohort(lat[('P4', q)], 1.0, 'event', ks)
        row = []
        for n in (48, 60, 72, 84, 96, 120):
            s = score(C, n)
            row.append(f"{n}: {s['D1']:.3f} | {s['PAIR']:.3f} | {s['BET']:.3f}")
        print(f"   q {q:3.1f}  kappa_s {ks:4.2f}   " + "     ".join(row), flush=True)

print("\n4. the q = 0 rows of section 1 against records/basket_cert_I043.txt (other random numbers, same design)")
old = record_I043()
gaps = {name: max(abs(S[(0.0,) + key][name] - vals[j]) for key, vals in old.items()) for j, name in enumerate(OLD)}
worst = max(gaps.values())
print(f"   cells compared: {len(old)} x {len(OLD)}; largest gap by statistic: " + ", ".join(f"{k} {v:.3f}" for k, v in gaps.items()))
print(f"   largest gap {worst:.3f}; tolerance {TOL}: {'PASS' if len(old) == 30 and worst <= TOL else 'FAIL'}")

print("\n5. the frozen decision rule for the default of price_curves")
drop = {q: max(S[(0.0, r, ks, k)]['PAIR'] - S[(q, r, ks, k)]['PAIR'] for r in ('event', 'outcome') for ks in KS for k in PTS)
        for q in (0.5, 1.0)}
gain = {q: max(S[(q, r, ks, k)]['PAIR'] - S[(0.0, r, ks, k)]['PAIR'] for r in ('event', 'outcome') for ks in KS for k in PTS)
        for q in (0.5, 1.0)}
print("   confirmatory pair at 72 pairs, thirty cells: largest fall against q = 0: " +
      ", ".join(f"q {q}: {v:+.3f}" for q, v in drop.items()) + "; largest rise: " + ", ".join(f"q {q}: {v:+.3f}" for q, v in gain.items()))
print(f"   largest size among H1a, D1 and BET in the two null worlds: {max(sizes):.4f} (limit .010; Monte Carlo standard error .0016 at .005)")
both = max(drop.values()) <= TOL and max(sizes) <= 0.010
print(f"   rule: {'both' if both else 'own'}")
sys.exit(0)
