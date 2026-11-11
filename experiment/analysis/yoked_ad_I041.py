"""KGi-DISS-I041, addendum AD-Y2: the association by arm, and a homogeneous slowdown of the
HIGH arm when the LOW arm is gated as in the model (freeze 00_freeze_I041.yaml). Seed 138100.
    python experiment/analysis/yoked_ad_I041.py > records/yoked_ad_I041.txt
"""
import numpy as np

import estimand_core_I038 as ec
import probe_generator as pg
import twins_I040 as tw
import yoked_analysis as ya

rng = np.random.default_rng(138100)
N, B = 20000, 2000
PT = {p[0]: p for p in ec.GATE_POINTS}
PTS = ('P0', 'P1', 'P2', 'P3', 'P4')
SIG_R = 5.8


def pool(b, a=0.5):
    """plain ratings (shape M1), as in yoked_cert_I041.measure"""
    rep = lambda m: np.clip(np.round((50 + a * (100 * m - 50) + rng.normal(0, SIG_R, m.shape)) / 5) * 5, 0, 100)
    return {arm: dict(F=rep(b['L'][arm]), E=rep(b['A'][arm]), wins=b['wins'][arm]) for arm in tw.ARMS}


def probe(b, rule, world='gate'):
    lh, ll = b['L']['HIGH'][:, -1], b['L']['LOW'][:, -1]
    if world == 'hs_g':                     # HIGH: everyone at the HIGH mean gain; LOW gated as in the model
        lh = np.full(N, lh.mean())
    c = 0.0 if world == 'r3' else 1.0
    return {'HIGH': pg.probe_stat(lh, c, ec.M, ec.SCHEME, 12.0, rule, rng),
            'LOW': pg.probe_stat(ll, c, ec.M, ec.SCHEME, 12.0, rule, rng)}


def score(P, T, n):
    i = rng.integers(0, N, (B, n))
    d = dict(fh=P['HIGH']['F'][i, -1], fl=P['LOW']['F'][i, -1], eh=P['HIGH']['E'][i, -1], el=P['LOW']['E'][i, -1],
             th=T['HIGH'][i], tl=T['LOW'][i], fl_rounds=P['LOW']['F'][i][:, :, 2:6],
             wl=P['LOW']['wins'][i][:, :, 3:6] / tw.K, jit=rng.uniform(-.01, .01, (B, n)))
    return {k: (v.mean() if v.dtype == bool else v) for k, v in ya.decisions(d).items()}


KEYS = ('D1', 'FREEZE', 'ASSOC', 'ASSOC_L', 'ASSOC_H', 'TOPQ', 'FULL', 'FULL_H', 'FULL_T')
line = lambda s: "  ".join(f"{s[x]:8.4f}" for x in KEYS)
head = "  ".join(f"{k:>8}" for k in KEYS)
print("KGi-DISS-I041 addendum AD-Y2: the association by arm (20,000 simulated pairs per cell; 2,000 samples; seed 138100)")
print("plain ratings at gain .5; one-sided .005 throughout\n")
lat = {k: tw.twins(PT[k], N, rng, same_person=False, indep_choice=True) for k in PTS}
P = {k: pool(lat[k]) for k in PTS}
T = {(k, r): probe(lat[k], r) for r in ec.RULES for k in PTS}

print("A. the model at 72 pairs")
print("   point rule     " + head)
for r in ec.RULES:
    for k in PTS:
        print(f"   {k}    {r:7s}  " + line(score(P[k], T[(k, r)], 72)), flush=True)

print("\nB. homogeneous slowdown of the HIGH arm, LOW gated as in the model")
print("   point rule    pairs  " + head + "   mean psi-hat")
Th = {(k, r): probe(lat[k], r, 'hs_g') for r in ec.RULES for k in ('P1', 'P4')}
for r in ec.RULES:
    for k in ('P1', 'P4'):
        for n in (72, 216):
            s = score(P[k], Th[(k, r)], n)
            print(f"   {k}    {r:7s}  {n:4d}   " + line(s) + f"   {s['psi'].mean():.3f}", flush=True)

print("\nC. ratings move, the gain does not (coupling 0), P1, one-update rule")
Tr = probe(lat['P1'], 'event', 'r3')
for n in (72, 216):
    print(f"   {n:4d} pairs   " + line(score(P['P1'], Tr, n)), flush=True)

print("\nD. the model by number of pairs: ASSOC_H | TOPQ | FULL_H | FULL_T")
for r in ('event', 'outcome'):
    for k in ('P1', 'P2', 'P3'):
        row = []
        for n in (72, 144, 216, 288):
            s = score(P[k], T[(k, r)], n)
            row.append(f"{n}: {s['ASSOC_H']:.3f} | {s['TOPQ']:.3f} | {s['FULL_H']:.3f} | {s['FULL_T']:.3f}")
        print(f"   {k} {r:7s}  " + "     ".join(row), flush=True)
