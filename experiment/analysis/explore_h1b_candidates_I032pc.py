"""POST-HOC / EXPLORATORY (post-I032 brainstorm support; NOT a certification).
Latent units (trust x100), no measurement layer, MODERATE restoration only.
Questions, written before the run:

Q1  Integrating-utility rival R3-int: reported fairness = EMA_eta of R3's
    instantaneous satisfaction (R3's trust does not feed back into choice, so
    filtering R3's rating series is exact for this rival). eta per trial in
    {.005, .01, .02}. Does the SI statistic c = rec - .25*drop on the
    above-median-drop HIGH half declare a gate (c < 0) with the P2-mean baseline?
    With the end-of-P2 baseline?
Q2  Between-arm restoration contrast (randomized, HIGH vs LOW within MODERATE):
    rec_end = late-P3 - end-of-P2. Sign of HIGH - LOW per model, overall and in
    the P3-LOW-regime subset (reference gap closed in P3).
Q3  P3 reversal (the better ticket swaps at t = 300): late-P3 correct-choice
    rate by arm per model (the gate scales its learning rate by L, so it predicts
    slower reversal learning after delegitimation).

Seed 132960. Run from the repo root:
    python experiment/analysis/explore_h1b_candidates_I032pc.py > records/h1b_candidates_I032pc.txt
"""
import sys

import numpy as np

sys.path.insert(0, 'experiment/analysis')
import market_generator as mg

rng = np.random.default_rng(132960)
N = 20000
END = slice(56, 60)   # last 4 ratings of P2 (t = 285..300)


def ema(x, eta):
    e5 = 1 - (1 - eta) ** 5
    out = np.empty_like(x)
    out[:, 0] = x[:, 0]
    for k in range(1, x.shape[1]):
        out[:, k] = out[:, k - 1] + e5 * (x[:, k] - out[:, k - 1])
    return out


def stats(L):
    p1 = L[:, mg.P1_IDX].mean(1)
    p2 = L[:, mg.P2_IDX].mean(1)
    endp2 = L[:, END].mean(1)
    late = L[:, mg.LATE_IDX].mean(1)
    return dict(drop=p1 - p2, rec=late - p2, rec_end=late - endp2)


def gen(kind, arm, reversal=False):
    saved = dict(mg.RESTO)
    if reversal:
        mg.RESTO.update({'FULL': (.35, .65), 'MODERATE': (.35, .45)})
    try:
        lat = mg.simulate_latent(kind, N, arm, rng, resto_mix=(1, 0))
    finally:
        mg.RESTO.clear()
        mg.RESTO.update(saved)
    return lat


models = [('gate', 'gate', None), ('R3', 'rival_au', None), ('R4', 'rival_us', None),
          ('R3-int .02', 'rival_au', .02), ('R3-int .01', 'rival_au', .01),
          ('R3-int .005', 'rival_au', .005)]
cache = {}
for kind in ('gate', 'rival_au', 'rival_us'):
    for arm in ('HIGH', 'LOW'):
        cache[(kind, arm)] = gen(kind, arm)

print("POST-HOC exploratory H1b candidates (seed 132960; latent x100; MODERATE; n=20000/arm)\n")
print("Q1/Q2. per model: HIGH drop, HIGH rec (P2-mean base), HIGH rec_end (end-P2 base);")
print("       SI c on above-median-drop HIGH half (P2-mean | end-P2 base);")
print("       between-arm rec_end HIGH-LOW (all | P3-LOW-regime subset)")
hdr = f"{'model':12s} {'dropH':>6s} {'recH':>6s} {'recEH':>6s} {'c_P2m':>7s} {'c_end':>7s} {'dRecE':>7s} {'dRecE|P3L':>9s}"
print(hdr)
for name, kind, eta in models:
    s = {}
    reg3 = {}
    for arm in ('HIGH', 'LOW'):
        lat = cache[(kind, arm)]
        L = 100 * lat['ratings'].astype(float)
        if eta is not None:
            L = ema(L, eta)
        s[arm] = stats(L)
        reg3[arm] = lat['reg3']
    h = s['HIGH']
    top = h['drop'] > np.median(h['drop'])
    c_m = (h['rec'] - .25 * h['drop'])[top]
    c_e = (h['rec_end'] - .25 * h['drop'])[top]
    d_all = h['rec_end'].mean() - s['LOW']['rec_end'].mean()
    d_p3l = h['rec_end'][~reg3['HIGH']].mean() - s['LOW']['rec_end'][~reg3['LOW']].mean()
    print(f"{name:12s} {h['drop'].mean():6.1f} {h['rec'].mean():6.1f} {h['rec_end'].mean():6.1f} "
          f"{np.median(c_m):7.1f} {np.median(c_e):7.1f} {d_all:7.1f} {d_p3l:9.1f}")

print("\nQ3. P3 reversal (better ticket swaps at t=300), MODERATE (.45 vs .35 after the swap):")
print(f"{'model':8s} {'arm':5s} {'P3 correct':>10s} {'late-P3 correct':>15s} {'late fair':>9s} {'rec_end':>8s}")
for name, kind in (('gate', 'gate'), ('R3', 'rival_au'), ('R4', 'rival_us')):
    for arm in ('HIGH', 'LOW'):
        lat = gen(kind, arm, reversal=True)
        L = 100 * lat['ratings'].astype(float)
        st = stats(L)
        print(f"{name:8s} {arm:5s} {1 - lat['acc3'].mean():10.3f} {1 - lat['acc_late'].mean():15.3f} "
              f"{L[:, mg.LATE_IDX].mean():9.1f} {st['rec_end'].mean():8.1f}")
print("\n(no reversal, for reference: late-P3 correct)")
for name, kind in (('gate', 'gate'), ('R3', 'rival_au'), ('R4', 'rival_us')):
    print(f"{name:8s} HIGH {cache[(kind, 'HIGH')]['acc_late'].mean():.3f}  LOW {cache[(kind, 'LOW')]['acc_late'].mean():.3f}")
