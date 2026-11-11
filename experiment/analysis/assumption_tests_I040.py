"""KGi-DISS-I040 addendum AD-T2: tests of the behavioural assumptions behind T13 with the
ratings the design records (fairness F and entitlement E after every round). Pairs of
different people; gain .5, rating noise 5.8. Seed 137200.
    python experiment/analysis/assumption_tests_I040.py > records/assumption_tests_I040.txt
"""
import numpy as np
from scipy import stats as st

import estimand_core_I038 as ec
import twins_I040 as tw

rng = np.random.default_rng(137200)
N, B = 20000, 2000
PT = {p[0]: p for p in ec.GATE_POINTS}
ZC = st.norm.ppf(.995)
print("KGi-DISS-I040 AD-T2: tests of the assumptions behind T13 (20,000 simulated participants per arm; 2,000 replicates; seed 137200)\n")


def spear(x, y):
    rx, ry = st.rankdata(x, axis=1), st.rankdata(y, axis=1)
    rx, ry = rx - rx.mean(1, keepdims=True), ry - ry.mean(1, keepdims=True)
    den = np.sqrt((rx ** 2).sum(1) * (ry ** 2).sum(1))
    return np.where(den > 0, (rx * ry).sum(1) / np.maximum(den, 1e-12), 0.0)


print("A. aspiration rises with the reference (K3): entitlement rating after the last deprivation round, HIGH above LOW")
print("B. legitimacy falls with aspiration (K2): within-arm rank association of entitlement and fairness, pooled over arms, negative")
print("   point   mean entitlement rating HIGH / LOW   A: power at 36 | 72 per arm   B: power at 72 per arm   mean Spearman HIGH / LOW")
for k in ('P0', 'P1', 'P2', 'P3', 'P4'):
    b = tw.twins(PT[k], N, rng, same_person=False)
    e = {a: tw.rating(b['A'][a][:, -1], rng) for a in tw.ARMS}
    f = {a: tw.rating(b['L'][a][:, -1], rng) for a in tw.ARMS}
    pa = []
    for n in (36, 72):
        i, j = rng.integers(0, N, (B, n)), rng.integers(0, N, (B, n))
        pa.append(np.mean([st.mannwhitneyu(e['HIGH'][i[r]], e['LOW'][j[r]], alternative='greater').pvalue < .005 for r in range(B)]))
    i, j = rng.integers(0, N, (B, 72)), rng.integers(0, N, (B, 72))
    jit = lambda x: x + rng.uniform(-.01, .01, x.shape)
    sh, sl = spear(jit(e['HIGH'][i]), jit(f['HIGH'][i])), spear(jit(e['LOW'][j]), jit(f['LOW'][j]))
    z = (np.arctanh(np.clip(sh, -.999, .999)) + np.arctanh(np.clip(sl, -.999, .999))) * np.sqrt(69 / 1.06) / np.sqrt(2)
    print(f"   {k}      {e['HIGH'].mean():.1f} / {e['LOW'].mean():.1f}                       {pa[0]:.3f} | {pa[1]:.3f}"
          f"                 {np.mean(z < -ZC):.3f}                    {sh.mean():+.3f} / {sl.mean():+.3f}", flush=True)

print("\nC. a win never erodes fairness (phi_plus <= tolerance), P1: fairness rating after the rich round, and in LOW the slope of the")
print("   round-to-round change in the fairness rating on the round's win share (rounds 4-6, 72 participants, participant-clustered)")
print("   phi_plus   mean fairness rating after the rich round   mean slope (rating points per unit win share)   rate of 'slope below 0' at one-sided .005")
for pp in (0.25, 0.5, 1.0):
    b = tw.twins(PT['P1'], N, rng, phip=pp, same_person=False)
    fr = tw.rating(b['L']['LOW'][:, 2:6], rng)                       # rounds 3-6
    dF = fr[:, 1:] - fr[:, :-1]
    ws = b['wins']['LOW'][:, 3:6] / tw.K
    f1 = tw.rating(np.r_[b['L']['HIGH'][:, 0], b['L']['LOW'][:, 0]], rng).mean()
    i = rng.integers(0, N, (B, 72))
    x, y = ws[i], dF[i]                                              # (B, 72, 3)
    xc, yc = x - x.mean((1, 2), keepdims=True), y - y.mean((1, 2), keepdims=True)
    sxx = (xc ** 2).sum((1, 2))
    slope = (xc * yc).sum((1, 2)) / sxx
    res = yc - slope[:, None, None] * xc
    se = np.sqrt(((xc * res).sum(2) ** 2).sum(1)) / sxx
    print(f"   {pp:<5}      {f1:.1f}                                        {slope.mean():+.1f}"
          f"                                            {np.mean(slope / se < -ZC):.3f}", flush=True)
