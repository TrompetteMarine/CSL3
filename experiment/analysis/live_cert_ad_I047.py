"""KGi-DISS-I047, addendum AD1 of the freeze: the rates of live_cert_I047.py over eight
independent pools, so that every rate comes with its Monte Carlo spread, and the frozen
decision rule read on the means. Each pool has its own seed (141100 + r) and its own stream
for who is informed (141200 + r).
    python experiment/analysis/live_cert_ad_I047.py > records/live_cert_ad_I047.txt
"""
import re

import numpy as np

import estimand_core_I038 as ec
import probe_generator as pg
import twins_I040 as tw
import yoked_analysis as ya

R = 8
N, B = 20000, 2000
PT = {p[0]: p for p in ec.GATE_POINTS}
PTS = ('P0', 'P1', 'P2', 'P3', 'P4')
KS = (0.5, 0.35, 0.2)
QS = (0.0, 0.5, 1.0)
RULES = ('event', 'outcome')
SIG_R, SIG_F, SIG_BET, BAND, PRICE = 5.8, 12.0, 8.0, 5.0, 50.0
TOL = 0.03
STATS = ('H1a', 'D1', 'PAIR', 'K3', 'FREEZE', 'ASSOC_H', 'ASSOC_L', 'TOPQ', 'BET', 'D1_rec', 'D1_src')
OLD = ('H1a', 'D1', 'PAIR', 'FREEZE', 'ASSOC_H', 'BET', 'D1_rec', 'D1_src')
r5 = lambda x: np.clip(np.round(x / 5) * 5, 0, 100)


class Pool:
    """the functions of basket_cert_I043.py on one generator"""

    def __init__(self, seed, mseed):
        self.rng, self.mrng = np.random.default_rng(seed), np.random.default_rng(mseed)

    def ratings(self, m, a=0.5):
        return r5(50 + a * (100 * m - 50) + self.rng.normal(0, SIG_R, m.shape))

    def market(self, w, e):
        rng, n = self.rng, len(w)
        b0 = np.clip(rng.normal(pg.PRIOR_MU, pg.PRIOR_SD, n), 5, 95)
        pre = r5(b0 + rng.normal(0, SIG_F, n))
        belief = b0 + w * (100 * e - b0)
        post = r5(belief + rng.normal(0, SIG_F, n))
        z = belief + rng.normal(0, SIG_BET, n)
        return post - pre, np.where(z > PRICE + BAND, 1, np.where(z < PRICE - BAND, -1, 0))

    def probe(self, l, c, rule, ks):
        g = 1 - c * (1 - l)
        off = self.rng.random(len(l)) < 0.10
        w_rec = np.where(off, 0.0, pg.weight(g, ec.M, rule))
        w_src = np.where(off, 0.0, ks * g)
        (dr1, br1), (dr0, br0) = self.market(w_rec, .9), self.market(w_rec, .1)
        (ds1, bs1), (ds0, bs0) = self.market(w_src, .9), self.market(w_src, .1)
        t_rec, t_src = dr1 - dr0, ds1 - ds0
        return dict(T=.5 * (t_rec + t_src), Tr=t_rec, Ts=t_src, B=.5 * ((br1 - br0) / 2 + (bs1 - bs0) / 2))

    def cohort(self, b, c, rule, ks):
        out = {}
        for arm in tw.ARMS:
            out[arm] = self.probe(b['L'][arm][:, -1], c, rule, ks)
            out[arm].update(F=self.ratings(b['L'][arm]), E=self.ratings(b['A'][arm]), wins=b['wins'][arm])
        return out

    def score(self, C, n):
        rng = self.rng
        i = rng.integers(0, N, (B, n))
        H, L = C['HIGH'], C['LOW']
        d = dict(fh=H['F'][i, -1], fl=L['F'][i, -1], eh=H['E'][i, -1], el=L['E'][i, -1], th=H['T'][i], tl=L['T'][i],
                 fl_rounds=L['F'][i][:, :, 2:6], wl=L['wins'][i][:, :, 3:6] / tw.K, jit=rng.uniform(-.01, .01, (B, n)))
        with np.errstate(divide='ignore', invalid='ignore'):
            s = {k: (v.mean() if v.dtype == bool else v) for k, v in ya.decisions(d).items()}
            s['D1_rec'] = (ya.fieller(H['Tr'][i], L['Tr'][i])[2] < 1).mean()
            s['D1_src'] = (ya.fieller(H['Ts'][i], L['Ts'][i])[2] < 1).mean()
        s['BET'] = (ya.signed_rank_z(L['B'][i] - H['B'][i]) > ya.ZC).mean()
        return s

    def pairs(self, k, q, regime=None):
        if q == 0:
            informed = None
        elif q == 1:
            informed = {a: np.ones(N, bool) for a in tw.ARMS}
        else:
            informed = {a: self.mrng.random(N) < q for a in tw.ARMS}
        return tw.twins(PT[k], N, self.rng, same_person=False, indep_choice=True, regime=regime, informed=informed)


def record_I043(path='records/basket_cert_I043.txt'):
    out = {}
    for line in open(path):
        m = re.match(r'\s+(event|outcome)\s+(0\.\d+)\s+(P\d)\s+((?:\d\.\d+\s+){8})', line)
        if m:
            out[(m.group(1), float(m.group(2)), m.group(3))] = dict(zip(OLD, (float(x) for x in m.group(4).split())))
    return out


main, null_a, null_b, edge, lat0 = {}, {}, {}, {}, {}
NS = (60, 72, 84, 96)
for r in range(R):
    P = Pool(141100 + r, 141200 + r)
    for q in QS:
        for k in PTS:
            b = P.pairs(k, q)
            lat0.setdefault((q, k), []).append((b['L']['HIGH'][:, -1].mean(), b['L']['LOW'][:, -1].mean()))
            for rule in RULES:
                for ks in KS:
                    s = P.score(P.cohort(b, 1.0, rule, ks), 72)
                    main.setdefault((q, rule, ks, k), []).append([s[x] for x in STATS])
            if k in ('P1', 'P4'):
                for ks in KS:
                    s = P.score(P.cohort(b, 0.0, 'event', ks), 72)
                    null_a.setdefault((q, ks, k), []).append([s[x] for x in STATS])
            if k == 'P4':
                for ks in KS:
                    C = P.cohort(b, 1.0, 'event', ks)
                    edge.setdefault((q, ks), []).append([P.score(C, n)['PAIR'] for n in NS])
        nul = P.pairs('P1', q, regime={'HIGH': 'LOW', 'LOW': 'LOW'})
        for ks in KS:
            s = P.score(P.cohort(nul, 1.0, 'event', ks), 72)
            null_b.setdefault((q, ks), []).append([s[x] for x in STATS])

M = {k: np.array(v) for k, v in main.items()}
mean = lambda key, x: M[key][:, STATS.index(x)].mean()
sd = lambda key, x: M[key][:, STATS.index(x)].std(ddof=1)

print(f"KGi-DISS-I047, addendum AD1: {R} independent pools of 20,000 pairs per cell (seeds 141100 to {141100 + R - 1}); 2,000 samples each")
print("every rate: mean over the pools, with the standard deviation across pools in brackets; 72 pairs; one-sided .005\n")

print("0. legitimacy at probe time HIGH / LOW, mean over the pools (largest standard deviation across pools: "
      f"{max(np.array(v).std(0, ddof=1).max() for v in lat0.values()):.4f})")
for q in QS:
    print(f"   q {q:3.1f}   " + "   ".join(f"{k} {np.mean(lat0[(q, k)], 0)[0]:.3f} / {np.mean(lat0[(q, k)], 0)[1]:.3f}" for k in PTS))

SHOW = ('H1a', 'D1', 'PAIR', 'K3', 'FREEZE', 'ASSOC_H', 'ASSOC_L', 'TOPQ', 'BET', 'D1_src')
print("\n1. decision rates at 72 pairs, full coupling")
print("   q    rule     kappa_s point   " + "  ".join(f"{x:>13}" for x in SHOW))
for q in QS:
    for rule in RULES:
        for ks in KS:
            for k in PTS:
                key = (q, rule, ks, k)
                print(f"   {q:3.1f}  {rule:7s}  {ks:4.2f}    {k}      " + "  ".join(f"{mean(key, x):.3f} ({sd(key, x):.3f})" for x in SHOW), flush=True)

print("\n2. sizes at 72 pairs, one-update rule: mean over the pools (largest single pool)")
size_means = []
print("   (a) ratings move, the gain does not (coupling 0): D1 | BET | FREEZE | association within HIGH")
for q in QS:
    for ks in KS:
        row = []
        for k in ('P1', 'P4'):
            a = np.array(null_a[(q, ks, k)])
            size_means += [a[:, STATS.index('D1')].mean(), a[:, STATS.index('BET')].mean()]
            row.append(f"{k}: " + " | ".join(f"{a[:, STATS.index(x)].mean():.4f} ({a[:, STATS.index(x)].max():.4f})" for x in ('D1', 'BET', 'FREEZE', 'ASSOC_H')))
        print(f"   q {q:3.1f}  kappa_s {ks:4.2f}   " + "     ".join(row))
print("   (b) both members of a pair on the LOW board (P1): H1a | D1 | BET | FREEZE | association within the arm labelled HIGH | top quarter")
for q in QS:
    for ks in KS:
        a = np.array(null_b[(q, ks)])
        size_means += [a[:, STATS.index(x)].mean() for x in ('H1a', 'D1', 'BET')]
        print(f"   q {q:3.1f}  kappa_s {ks:4.2f}   " + " | ".join(f"{a[:, STATS.index(x)].mean():.4f} ({a[:, STATS.index(x)].max():.4f})" for x in ('H1a', 'D1', 'BET', 'FREEZE', 'ASSOC_H', 'TOPQ')))

print("\n3. the anchoring edge (P4), one-update rule: confirmatory pair by number of pairs")
for q in QS:
    for ks in KS:
        a = np.array(edge[(q, ks)])
        print(f"   q {q:3.1f}  kappa_s {ks:4.2f}   " + "     ".join(f"{n}: {a[:, j].mean():.3f} ({a[:, j].std(ddof=1):.3f})" for j, n in enumerate(NS)))

print("\n4. the I043 record against the eight q = 0 pools (gate G18b'): a value passes inside [lowest pool - .02, highest pool + .02]")
old = record_I043()
out, n_cmp, worst = [], 0, (0.0, None)
for (rule, ks, k), vals in old.items():
    a = M[(0.0, rule, ks, k)]
    for x in OLD:
        col = a[:, STATS.index(x)]
        n_cmp += 1
        gap = max(col.min() - vals[x], vals[x] - col.max(), 0.0)
        if gap > worst[0]:
            worst = (gap, (rule, ks, k, x, vals[x], round(col.min(), 3), round(col.max(), 3)))
        if gap > 0.02:
            out.append((rule, ks, k, x, vals[x], round(col.min(), 3), round(col.max(), 3)))
print(f"   values compared: {n_cmp}; outside: {len(out)}" + ("" if not out else "  " + "; ".join(str(o) for o in out)))
print(f"   farthest value: {worst[1]} (outside the range of the pools by {worst[0]:.3f})")
print(f"   G18(b'): {'PASS' if n_cmp == 240 and not out else 'FAIL'}")
sds = sorted(((sd(key, 'PAIR'), key) for key in M if key[0] == 0.0), reverse=True)
print("   spread of the confirmatory pair across pools at q = 0: largest " +
      ", ".join(f"{s:.3f} at {key[3]} {key[1]} kappa_s {key[2]}" for s, key in sds[:3]) +
      f"; largest among cells with a mean of .99 or more: {max([s for s, key in sds if mean(key, 'PAIR') >= .99] or [0]):.4f}")

print("\n5. the frozen decision rule read on the means over the pools")
cells = [(rule, ks, k) for rule in RULES for ks in KS for k in PTS]
for q in (0.5, 1.0):
    d = {c: mean((q,) + c, 'PAIR') - mean((0.0,) + c, 'PAIR') for c in cells}
    se = {c: np.sqrt((sd((q,) + c, 'PAIR') ** 2 + sd((0.0,) + c, 'PAIR') ** 2) / R) for c in cells}
    lo, hi = min(d, key=d.get), max(d, key=d.get)
    print(f"   q {q}: change of the confirmatory pair against q = 0 over thirty cells: lowest {d[lo]:+.3f} (s.e. {se[lo]:.3f}) at {lo}, "
          f"highest {d[hi]:+.3f} (s.e. {se[hi]:.3f}) at {hi}")
falls = max(mean((0.0,) + c, 'PAIR') - mean((q,) + c, 'PAIR') for q in (0.5, 1.0) for c in cells)
print(f"   largest fall {falls:+.3f} (limit {TOL}); largest mean size of H1a, D1 and BET in the two null worlds {max(size_means):.4f} (limit .010)")
print(f"   rule: {'both' if falls <= TOL and max(size_means) <= 0.010 else 'own'}")
