"""POST-HOC / EXPLORATORY (post-I032 brainstorm support; NOT a certification).

Question 1 — what displayed peer level chi (the HIGH reference during the
participant's P2, clock rounds 151-300) does each truthful peer-source option
deliver? Pool streams are proxied by plain Q-learning softmax agents (alpha .2,
beta 12 = frozen generator values; beta 6 = noisier, human-like bracket). Humans
will differ; this only sizes the options.

  O1 same schedule, person-level quantile on the P2 block window
  O2 same schedule, rolling index: p90 / max across a pool of 40 trailing-15 rates
  O3 time-shifted rich segment (replay of a standard stream's P1, or an
     order-shifted pool session P2-P1-P3 whose rich phase falls in rounds 151-300)
  O4 rich-rule pool session (current build): P2 odds = P1 odds

Question 2 — how much H1a effect survives at a given HIGH level? theta(mu_ref)
for the frozen gate and for R3 (rival_au), M2 measurement at its calibrated a,
60k/arm, screens applied; asymptotic one-sided WMW power at .005, n = 320/arm.

Seed 132950. Run from the repo root:
    python experiment/analysis/explore_peer_source_I032pc.py > records/peer_source_I032pc.txt
"""
import sys

import numpy as np
from scipy.stats import norm

sys.path.insert(0, 'experiment/analysis')
import market_generator as mg

rng = np.random.default_rng(132950)
T = 450
W2 = slice(150, 300)


def pool(n, schedule, beta, resto='FULL'):
    p3 = (.65, .35) if resto == 'FULL' else (.45, .35)
    if schedule == 'standard':
        ph = [(.65, .35), (.30, .15), p3]
    elif schedule == 'rich':
        ph = [(.65, .35), (.65, .35), p3]
    elif schedule == 'P2P1P3':
        ph = [(.30, .15), (.65, .35), p3]
    else:
        raise ValueError(schedule)
    Q = np.full((n, 2), .5)
    R = np.empty((n, T))
    acc = np.empty((n, T))
    rows = np.arange(n)
    for t in range(T):
        g, b = ph[t // 150]
        p0 = 1 / (1 + np.exp(-beta * (Q[:, 0] - Q[:, 1])))
        arm = (rng.random(n) >= p0).astype(int)
        r = (rng.random(n) < np.where(arm == 0, g, b)).astype(float)
        Q[rows, arm] += .2 * (r - Q[rows, arm])
        R[:, t] = r
        acc[:, t] = arm == 0
    return R, acc


def trailing15(R):
    c = np.cumsum(R, axis=1)
    out = np.empty_like(R)
    out[:, :15] = c[:, :15] / np.arange(1, 16)
    out[:, 15:] = (c[:, 15:] - c[:, :-15]) / 15
    return out


def q(x, ps=(.5, .75, .9)):
    return "  ".join(f"p{int(100*p)}={np.quantile(x, p):.3f}" for p in ps)


print("POST-HOC exploratory peer-source sizing (seed 132950). Agents proxy pool streams.")
print("Displayed level = mean trailing-15 win rate over the participant's P2 window (rounds 151-300).\n")
NP = 20000
for beta in (12.0, 6.0):
    print(f"--- pool agents softmax beta = {beta:g} ---")
    Rs, As = pool(NP, 'standard', beta)
    Rr, Ar = pool(NP, 'rich', beta)
    Ro, Ao = pool(NP, 'P2P1P3', beta)
    w_std = Rs[:, W2].mean(1)
    print(f"own-schedule P2 window rate (what a participant gets):   mean={w_std.mean():.3f}  {q(w_std)}  acc={As[:, W2].mean():.3f}")
    print(f"O1 same schedule, person-level quantile on block window: {q(w_std, (.9, .975))}")
    t15 = trailing15(Rs)[:, W2]
    idx = rng.permutation(NP)[: 40 * 400].reshape(400, 40)
    p90_idx = np.array([np.quantile(t15[i], .9, axis=0).mean() for i in idx])
    max_idx = np.array([t15[i].max(axis=0).mean() for i in idx])
    p50_idx = np.array([np.quantile(t15[i], .5, axis=0).mean() for i in idx])
    print(f"O2 same schedule, rolling index over 40 streams:  p50-index={p50_idx.mean():.3f}  "
          f"p90-index={p90_idx.mean():.3f}  max-index={max_idx.mean():.3f}")
    w_p1 = Rs[:, 0:150].mean(1)
    w_o = Ro[:, W2].mean(1)
    print(f"O3a replay of a standard stream's P1 segment:  {q(w_p1)}  share>=.60: {(w_p1 >= .60).mean():.3f}")
    print(f"O3b order-shifted P2-P1-P3, rounds 151-300:     {q(w_o)}  share>=.60: {(w_o >= .60).mean():.3f}")
    w_r = Rr[:, W2].mean(1)
    print(f"O4 rich-rule pool, rounds 151-300:              {q(w_r)}  share>=.60: {(w_r >= .60).mean():.3f}  "
          f"acc={Ar[:, W2].mean():.3f}\n")

# gate threshold (asymptotic, frozen constants): delegitimation in P2 iff
# (1-chi_w) p + chi_w * ref > A*(p) = .3 + .25 p/(1-p)
p = .27
print("gate asymptotic P2 threshold on the displayed reference (chi weight .6, own p = .27):")
print(f"  ref > {(.3 + .25 * p / (1 - p) - .4 * p) / .6:.3f}  (chi weight .4: ref > {(.3 + .25 * p / (1 - p) - .6 * p) / .4:.3f})\n")

print("theta(mu_ref) and asymptotic H1a power (n=320/arm, one-sided .005), M2 at a=.0578, 60k/arm:")
print(f"{'mu_ref':>6s} {'gate theta':>10s} {'power':>6s} {'R3 theta':>9s} {'power':>6s}")
A_M2 = 0.0578
N = 60000
n = 320
sd0 = np.sqrt((2 * n + 1) / (12 * n * n))
for mu in (.35, .40, .45, .50, .55, .60, .65):
    row = [f"{mu:6.2f}"]
    for kind in ('gate', 'rival_au'):
        d = {}
        for arm in ('HIGH', 'LOW'):
            lat = mg.simulate_latent(kind, N, arm, rng, mu_ref=mu)
            f, e, keep = mg.measure(lat, 'M2', A_M2, rng)
            ok = mg.screens(f, e, lat['acc1'], keep)
            d[arm] = mg.drops(f[ok])
        m = min(len(d['HIGH']), len(d['LOW']))
        dh, dl = d['HIGH'][:m], d['LOW'][rng.permutation(len(d['LOW']))[:m]]
        th = (dh > dl).mean() + .5 * (dh == dl).mean()
        pw = norm.cdf((th - .5) / sd0 - norm.ppf(.995))
        row += [f"{th:10.3f}", f"{pw:6.3f}"]
    print(" ".join(row))
