"""KGi-DISS-I038 addendum AD-C2: Monte Carlo sample sizes for the decisions on psi (the
asymptotic formula failed its check in part C). Seed 135200.
    python experiment/analysis/estimand_n_I038.py > records/estimand_n_I038.txt
"""
import json

import numpy as np

import estimand_core_I038 as ec

rng = np.random.default_rng(135200)
NL, NT, B = 40000, 300000, 4000
TH = json.load(open('records/estimand_map_I038.json'))
PSI_HI, PSI_CERT = TH['psi_hi'], TH['psi_cert']
GRID = (12, 18, 24, 36, 48, 60, 72, 96, 120, 150, 200, 250, 300, 400, 500, 600, 800, 1000)
gate = {p[0]: ec.pools('gate', p, NL, rng) for p in ec.GATE_POINTS}


def tpool(mult, c, rule, extra=0.0, attentive=False):
    m = mult[rng.integers(0, len(mult), NT)]
    return ec.tstat(m, c, 12.0, rule, rng, extra=extra, attentive=attentive)


def n90(th, tl, hit, split=(1, 1)):
    """smallest grid n (size of the smaller arm) with Monte Carlo power >= .90; returns (n, power there)"""
    for n in GRID:
        nh, nl = (n * split[0], n * split[1])
        d = ec.draw(th, tl, nh, nl, B if nh + nl <= 800 else 2000, rng)
        pw = np.mean(hit(d))
        if pw >= .90:
            return n, pw
    return None, pw


below = lambda x: (lambda d: d['hi'] < x)
above = lambda x: (lambda d: d['lo'] > x)
fmt = lambda r: (f"{r[0]} (power {r[1]:.3f})" if r[0] else f"> {GRID[-1]} (power {r[1]:.3f} at {GRID[-1]})")

print("KGi-DISS-I038 AD-C2: smallest n per arm with Monte Carlo power >= .90 (seed 135200; noise 12; equal split unless stated)")
print(f"thresholds: upper edge of the trap set {PSI_HI:.3f}; coupling-certified {PSI_CERT:.3f}\n")
full = {(p[0], r): (tpool(gate[p[0]]['HIGH'], 1.0, r), tpool(gate[p[0]]['LOW'], 1.0, r))
        for p in ec.GATE_POINTS for r in ec.RULES}
print("at full coupling: D1 (psi < 1) | D4 (psi below the upper edge) | D3 (psi below the certified threshold)")
for (pt, r), (th, tl) in full.items():
    d3 = fmt(n90(th, tl, below(PSI_CERT))) if pt == 'P0' else 'truth above the threshold'
    print(f"  {pt} {r:8s} psi {th.mean() / tl.mean():.3f}:  D1 {fmt(n90(th, tl, below(1.0)))}   "
          f"D4 {fmt(n90(th, tl, below(PSI_HI)))}   D3 {d3}", flush=True)
print("\nD4 at the anchoring edge with a 2:1 split in favour of HIGH (n = size of the LOW arm):")
for r in ec.RULES:
    res = n90(*full[('P4', r)], below(PSI_HI), split=(2, 1))
    print(f"  P4 {r:8s}: LOW arm {fmt(res)}; total {3 * res[0] if res[0] else 'n/a'}", flush=True)
print("\nD2 (trap excluded), homogeneous coupling at P1's gate parameters:")
for c, r in ((0.0, 'outcome'), (0.0, 'event'), (.25, 'outcome'), (.25, 'event'), (.5, 'outcome')):
    th, tl = tpool(gate['P1']['HIGH'], c, r), tpool(gate['P1']['LOW'], c, r)
    print(f"  c = {c} {r:8s} psi {th.mean() / tl.mean():.3f}: {fmt(n90(th, tl, above(PSI_HI)))}", flush=True)


def lee_hi(xh, kh, xl, kl):
    """upper limit of the trimming interval (HIGH retained as is; LOW retained with its top share trimmed)"""
    a, b = xh[kh], xl[kl]
    rh, rl = kh.mean(), kl.mean()
    k = int(round(len(b) * (rl - rh) / rl)) if rl > rh else 0
    b = np.sort(b)[:len(b) - k]
    return float(ec.fieller(a.mean(), a.var(ddof=1) / len(a), b.mean(), b.var(ddof=1) / len(b), len(a) + len(b) - 2)[1])


print("\nD1 with the trimming interval (attention check: inattentive fail .8, attentive .05), anchoring edge P4, 1,500 replicates:")
for r in ec.RULES:
    for extra in (0.0, .1):
        th, ah = tpool(gate['P4']['HIGH'], 1.0, r, extra=extra, attentive=True)
        tl, al = tpool(gate['P4']['LOW'], 1.0, r, attentive=True)
        fh = np.where(ah, rng.random(NT) < .05, rng.random(NT) < .8)
        fl = np.where(al, rng.random(NT) < .05, rng.random(NT) < .8)
        row = []
        for n in (72, 96, 120, 150):
            hit = 0
            for _ in range(1500):
                ih, il = rng.integers(0, NT, n), rng.integers(0, NT, n)
                hit += lee_hi(th[ih], ~fh[ih], tl[il], ~fl[il]) < 1
            row.append(f"n {n}: {hit / 1500:.3f}")
        print(f"  {r:8s} extra disengaged in HIGH +{extra:.0%}:  " + "   ".join(row), flush=True)
