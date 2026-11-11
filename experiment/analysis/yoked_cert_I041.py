"""KGi-DISS-I041: certification of the yoked design and its reporting set on synthetic
cohorts (freeze 00_freeze_I041.yaml). Seed 138000.
    python experiment/analysis/yoked_cert_I041.py > records/yoked_cert_I041.txt
"""
import numpy as np

import estimand_core_I038 as ec
import probe_generator as pg
import twins_I040 as tw
import yoked_analysis as ya

rng = np.random.default_rng(138000)
N, B = 20000, 2000
PT = {p[0]: p for p in ec.GATE_POINTS}
PTS = ('P0', 'P1', 'P2', 'P3', 'P4')
SIG_R = 5.8


def measure(L, A, shape, a):
    """fairness and entitlement ratings for one arm (design_generator.measure_design, shapes M1, M2, M3, M5)"""
    n, nr = L.shape
    g = np.exp(rng.normal(-0.32, 0.8, n)) if shape == 'M5' else np.ones(n)
    rep = lambda m: np.clip(np.round((50 + a * g[:, None] * (100 * m - 50) + rng.normal(0, SIG_R, m.shape)) / 5) * 5, 0, 100)
    f, e = rep(L), rep(A)
    if shape in ('M2', 'M3'):
        flat = rng.random(n) < (0.15 if shape == 'M2' else 0.20)
        level = rng.uniform(20, 80, flat.sum())
        for mat in (f, e):
            w = level[:, None] + rng.normal(0, SIG_R if shape == 'M2' else 8.0, (flat.sum(), nr))
            mat[flat] = np.clip(np.round(w / 5) * 5, 0, 100)
    return f, e


def pool(b, shape='M1', a=0.5):
    out = {}
    for arm in tw.ARMS:
        f, e = measure(b['L'][arm], b['A'][arm], shape, a)
        out[arm] = dict(F=f, E=e, wins=b['wins'][arm])
    return out


def probe(b, rule, world='gate'):
    lh, ll = b['L']['HIGH'][:, -1], b['L']['LOW'][:, -1]
    if world == 'hs':                       # every HIGH participant at the HIGH mean gain, LOW ungated
        lh, ll = np.full(N, lh.mean()), np.ones(N)
    c = 0.0 if world == 'r3' else 1.0
    return {'HIGH': pg.probe_stat(lh, c, ec.M, ec.SCHEME, 12.0, rule, rng),
            'LOW': pg.probe_stat(ll, c, ec.M, ec.SCHEME, 12.0, rule, rng)}


def score(P, T, n, rematch=False):
    i = rng.integers(0, N, (B, n))
    j = rng.integers(0, N, (B, n)) if rematch else i
    d = dict(fh=P['HIGH']['F'][i, -1], fl=P['LOW']['F'][j, -1], eh=P['HIGH']['E'][i, -1], el=P['LOW']['E'][j, -1],
             th=T['HIGH'][i], tl=T['LOW'][j], fl_rounds=P['LOW']['F'][j][:, :, 2:6],
             wl=P['LOW']['wins'][j][:, :, 3:6] / tw.K, jit=rng.uniform(-.01, .01, (B, n)))
    return {k: (v.mean() if v.dtype == bool else v) for k, v in ya.decisions(d).items()}


KEYS = ('H1a', 'K3', 'D1', 'D1_paired', 'FREEZE', 'ASSOC', 'PHI', 'PAIR', 'FULL')
print("KGi-DISS-I041: the yoked design and its reporting set (20,000 simulated pairs per cell; 2,000 samples; seed 138000)")
print("pairs of different people: independent rigidity and ticket-choice noise; one-sided .005 throughout\n")
lat = {k: tw.twins(PT[k], N, rng, same_person=False, indep_choice=True) for k in PTS}
print("0. the simulated pairs: legitimacy at probe time HIGH / LOW; pairs picking the same ticket in every deprivation round")
print("   " + "   ".join(f"{k} {lat[k]['L']['HIGH'][:, -1].mean():.3f} / {lat[k]['L']['LOW'][:, -1].mean():.3f}; {lat[k]['same_choice'].mean():.2f}" for k in PTS))

print("\n1. decision rates at 72 pairs, full coupling, plain ratings (gain .5)")
print("   point rule     " + "  ".join(f"{k:>9}" for k in KEYS) + "   mean psi-hat")
P0 = {k: pool(lat[k]) for k in PTS}
T = {}
for r in ec.RULES:
    for k in PTS:
        T[(k, r)] = probe(lat[k], r)
        s = score(P0[k], T[(k, r)], 72)
        print(f"   {k}    {r:7s}  " + "  ".join(f"{s[x]:9.3f}" for x in KEYS) + f"   {s['psi'].mean():.3f}", flush=True)

print("\n2. by number of pairs (one-update rule): H1a | D1 | confirmatory pair | full set")
for k in PTS:
    row = []
    for n in (36, 54, 72, 96):
        s = score(P0[k], T[(k, 'event')], n)
        row.append(f"{n}: {s['H1a']:.3f} | {s['D1']:.3f} | {s['PAIR']:.3f} | {s['FULL']:.3f}")
    print(f"   {k}   " + "     ".join(row), flush=True)

print("\n3. ratings under other shapes and gains, 72 pairs: H1a | K3")
print("   point   " + "   ".join(f"{sh} gain {a:<4}" for sh in ('M1', 'M2', 'M3', 'M5') for a in (.25, .5, 1.0)))
for k in PTS:
    row = []
    for sh in ('M1', 'M2', 'M3', 'M5'):
        for a in (.25, .5, 1.0):
            s = score(pool(lat[k], sh, a), T[(k, 'event')], 72)
            row.append(f"{s['H1a']:.3f}|{s['K3']:.3f}")
    print(f"   {k}      " + "   ".join(row), flush=True)

print("\n4. sizes and rivals at 72 pairs (one-update rule)")
nul = tw.twins(PT['P1'], N, rng, same_person=False, indep_choice=True, regime={'HIGH': 'LOW', 'LOW': 'LOW'})
s = score(pool(nul), probe(nul, 'event'), 72)
print("   null pairs (both members on the LOW board, P1):        " + "  ".join(f"{x} {s[x]:.4f}" for x in KEYS))
for k in ('P1', 'P4'):
    for world, lab in (('r3', 'ratings move, gain does not'), ('hs', 'homogeneous slowdown in HIGH')):
        s = score(P0[k], probe(lat[k], 'event', world), 72)
        print(f"   {k} {lab:30s}:                 " + "  ".join(f"{x} {s[x]:.4f}" for x in KEYS) + f"   psi {s['psi'].mean():.3f}", flush=True)

print("\n5. what yoking buys: H1a with yoked pairs | with LOW members re-matched at random")
for k in PTS:
    row = []
    for n in (18, 36):
        row.append(f"{n} pairs {score(P0[k], T[(k, 'event')], n)['H1a']:.3f} | {score(P0[k], T[(k, 'event')], n, rematch=True)['H1a']:.3f}")
    print(f"   {k} (gain .5)   " + "    ".join(row), flush=True)
Pq = pool(lat['P4'], 'M1', .25)
print("   P4 (gain .25)  " + "    ".join(
    f"{n} pairs {score(Pq, T[('P4', 'event')], n)['H1a']:.3f} | {score(Pq, T[('P4', 'event')], n, rematch=True)['H1a']:.3f}" for n in (18, 36, 72)))
