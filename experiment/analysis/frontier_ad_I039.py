"""KGi-DISS-I039 addendum AD-F2: the profiled likelihood-ratio test with a critical value
that holds over the whole range of the baseline weight (the fixed critical value of
section B lost its size). Event rule. Seed 136200.
    python experiment/analysis/frontier_ad_I039.py > records/frontier_ad_I039.txt
"""
import numpy as np

import estimand_core_I038 as ec
import likelihood_core_I039 as lc

rng = np.random.default_rng(136200)
Z = np.load('records/likelihood_pools_I039.npz')
G = {k: {a: Z[f"{k}_{a}"] for a in ('HIGH', 'LOW')} for k in ('P1', 'P4')}
OTHER = {'P1': 'P4', 'P4': 'P1'}
KAP = np.round(np.arange(.30, .7001, .025), 3)
NGRID = (4, 6, 8, 10, 12, 16, 20, 24, 30, 36, 48, 60, 72)
LOG = lambda p: np.log(np.maximum(p, 1e-300))
print("KGi-DISS-I039 AD-F2: likelihood-ratio test of c = 0 against c = 1, baseline weight profiled over .30-.70,")
print("critical value = the largest .995 null quantile over that range (10,000 replicates per cell; seed 136200)\n")
print("   n per arm:      " + "  ".join(f"{n:>5}" for n in NGRID) + "   n for .90")
for k in G:
    m = lc.Model(G[k], G[OTHER[k]], 'event', sigmas=(12.0,))
    tab = {(c, kp): {a: m.pT(a, {**lc.BASE, 'c': c, 'kap': kp}) for a in ('HIGH', 'LOW')} for c in (0.0, 1.0) for kp in KAP}
    LH = {c: np.array([LOG(tab[(c, kp)]['HIGH']) for kp in KAP]) for c in (0.0, 1.0)}
    LL = {c: np.array([LOG(tab[(c, kp)]['LOW']) for kp in KAP]) for c in (0.0, 1.0)}

    def glr(truth, n, b=10000):
        ch = lc.counts_of(lc.sample_idx(tab[truth]['HIGH'], n, b, rng), 161)
        cl = lc.counts_of(lc.sample_idx(tab[truth]['LOW'], n, b, rng), 161)
        return (ch @ LH[1.0].T + cl @ LL[1.0].T).max(1) - (ch @ LH[0.0].T + cl @ LL[0.0].T).max(1)

    pw, worst = [], []
    for n in NGRID:
        qs = [np.quantile(glr((0.0, kp), n), 1 - ec.ALPHA1, method='higher') for kp in KAP]
        crit = max(qs)
        worst.append(KAP[int(np.argmax(qs))])
        pw.append([np.mean(glr((1.0, kp), n) > crit) for kp in (0.35, 0.5, 0.65)])
    pw = np.array(pw)
    for j, kp in enumerate((0.35, 0.5, 0.65)):
        n90 = next((n for n, p in zip(NGRID, pw[:, j]) if p >= .90), None)
        print(f"   {k} power, true weight {kp}:  " + "  ".join(f"{x:.3f}" for x in pw[:, j]) + f"   {n90}")
    print(f"   {k} weight at which the null quantile is largest: " + "  ".join(f"{x:.3f}" for x in worst), flush=True)
