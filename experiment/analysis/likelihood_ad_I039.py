"""KGi-DISS-I039 addendum AD-L2: the least favourable direction for the depth of
delegitimation (every HIGH legitimacy eps higher), and the efficiency of the ratio of means
when the depth is not assumed known. Deterministic given records/likelihood_pools_I039.npz.
    python experiment/analysis/likelihood_ad_I039.py > records/likelihood_ad_I039.txt
"""
import numpy as np

import estimand_core_I038 as ec
import likelihood_core_I039 as lc

Z = np.load('records/likelihood_pools_I039.npz')
G = {k: {a: Z[f"{k}_{a}"] for a in ('HIGH', 'LOW')} for k in ('P1', 'P4')}
OTHER = {'P1': 'P4', 'P4': 'P1'}
print("KGi-DISS-I039 AD-L2: depth of delegitimation as a uniform shift of HIGH legitimacy (eps), full coupling\n")
print("information for c per participant pair, share kept when the depth is unknown")
print("  point rule      T: only c | + eps        (F, T), rating gain known: only c | + eps       (F, T), rating gain unknown: + eps, a, sr")
out = {}
for k in G:
    for r in ec.RULES:
        m = lc.Model(G[k], G[OTHER[k]], r)
        kap = 'kap' if r == 'event' else 'alpha'
        th = dict(lc.BASE)
        sum_i = lambda names, joint: sum(m.info(th, names, joint).values())
        t2 = sum_i(['c', 'eps'], False)
        f2 = sum_i(['c', 'eps'], True)
        f4 = sum_i(['c', 'eps', 'a', 'sr'], True)
        print(f"  {k}    {r:7s}   {t2[0, 0]:7.3f} | {lc.eff_info(t2):7.3f} ({lc.eff_info(t2) / t2[0, 0]:.0%})        "
              f"{f2[0, 0]:7.3f} | {lc.eff_info(f2):7.3f} ({lc.eff_info(f2) / f2[0, 0]:.0%})                 "
              f"{lc.eff_info(f4):7.3f} ({lc.eff_info(f4) / f2[0, 0]:.0%})", flush=True)
        # efficiency of the ratio of means for psi when the depth is unknown
        psi = m.psi(th)
        (muH, vH), (muL, vL) = lc.moments(m.pT('HIGH', th)), lc.moments(m.pT('LOW', th))
        vnp = (vH + psi ** 2 * vL) / muL ** 2
        row = {}
        for lab, depth in (('lam', ['lam']), ('eps', ['eps']), ('both', ['lam', 'eps'])):
            nT = ['c', kap, 'sig', 'q'] + depth
            nF = ['c', kap, 'sig', 'q', 'a', 'sr'] + depth
            gT = m.grad_psi(th, nT)
            bT = gT @ np.linalg.inv(sum_i(nT, False)) @ gT
            gF = np.r_[gT[:4], 0.0, 0.0, gT[4:]]
            bF = gF @ np.linalg.inv(sum_i(nF, True)) @ gF
            row[lab] = (bT / vnp, bF / vnp)
        out[(k, r)] = (psi, np.sqrt(vnp / 72), row)
print("\nrelative efficiency of the ratio of means for psi (bound / plug-in variance) when the depth is unknown")
print("  point rule      psi    plug-in s.e. at 72 | depth = mixture: T only  with F | depth = shift: T only  with F | both: T only  with F")
for (k, r), (psi, se, row) in out.items():
    print(f"  {k}    {r:7s}   {psi:.3f}  {se:.4f}             |        {row['lam'][0]:.3f}    {row['lam'][1]:.3f}        |"
          f"       {row['eps'][0]:.3f}    {row['eps'][1]:.3f}      |    {row['both'][0]:.3f}    {row['both'][1]:.3f}")
