"""I015: induced learning-rate asymmetry (frozen 00_freeze_I015.yaml).
Generate choices from the frozen dissonance agent (task-v3 geometry) and an OFF
control (L frozen at 1); fit per-subject dual-alpha Q-learning (choices only) on
P1 and P2 windows; report median log(alpha+/alpha-).
Seeds: 72000+k (diss), 72500+k (off). OUTPUT IS A MODEL PROPERTY, NOT DATA.
"""
import numpy as np
from scipy.optimize import minimize
from multiprocessing import Pool

T = 450
PH = {1: (.65, .35), 2: (.30, .15), 3: (.65, .35)}
NUF, NUR, TAUF, PHIM, PHIP, ALPHA, BETA = .05, .0125, .3, 1.0, .25, .2, 12.0
CHI, A0, L0 = .6, .5, 1.0
N = 300

def mu_t(t):
    return PH[1] if t < 150 else (PH[2] if t < 300 else PH[3])

def gen(agent, regime, seed):
    rng = np.random.default_rng(seed)
    out = []
    for s in range(N):
        rho = .002 if s % 2 == 0 else .02
        Q = np.array([.5, .5]); L, A = L0, A0
        peer_hits = 0; own = []
        ch = np.empty(T, np.int8); rw = np.empty(T)
        for t in range(T):
            mu = mu_t(t)
            p0 = 1/(1+np.exp(-BETA*(Q[0]-Q[1])))
            a = 0 if rng.random() < p0 else 1
            R = 1.0 if rng.random() < mu[a] else 0.0
            pr = .65 if regime == 'HIGH' else np.clip(np.mean(own[-15:]) if own else .5, .05, .95)
            peer_R = 1.0 if rng.random() < pr else 0.0
            peer_hits += peer_R; peer_rate = peer_hits/(t+1)
            own.append(R)
            g = L if agent == 'diss' else 1.0
            Q[a] += ALPHA*g*(R-Q[a])
            if agent == 'diss':
                D = PHIM*max(A-R, 0)+PHIP*max(R-A, 0)
                L = float(np.clip(L - NUF*max(D-TAUF, 0) + NUR*(D <= TAUF), 0, 1))
                ref = peer_rate if regime == 'HIGH' else np.mean(own[-15:])
                A = float(np.clip((1-rho)*A + rho*((1-CHI)*R + CHI*ref), 0, 1))
            ch[t], rw[t] = a, R
        out.append((ch, rw))
    return out

def nll_dual(th, ch, rw, lo, hi):
    ap, am, b = th
    if not (0 < ap < 1 and 0 < am < 1 and 0 < b < 40):
        return 1e9
    Q = np.array([.5, .5]); ll = 0.0
    for t in range(hi):
        p0 = 1/(1+np.exp(-b*(Q[0]-Q[1])))
        if t >= lo:
            p = p0 if ch[t] == 0 else 1-p0
            ll += np.log(max(p, 1e-12))
        d = rw[t]-Q[ch[t]]
        Q[ch[t]] += (ap if d >= 0 else am)*d
    return -ll

def fit_one(args):
    ch, rw, lo, hi, seed = args
    rng = np.random.default_rng(seed)
    best = (np.inf, None)
    for _ in range(4):
        x0 = [rng.uniform(.05, .5), rng.uniform(.05, .5), rng.uniform(2, 12)]
        try:
            r = minimize(nll_dual, x0, args=(ch, rw, lo, hi), method='Nelder-Mead',
                         options=dict(maxiter=1500, xatol=1e-4, fatol=1e-3))
            if r.fun < best[0]:
                best = (r.fun, r.x)
        except Exception:
            pass
    return best[1]

if __name__ == '__main__':
    res = {}
    jobs = [('diss', 'HIGH', 72000), ('diss', 'LOW', 72001),
            ('off', 'HIGH', 72500), ('off', 'LOW', 72501)]
    for agent, regime, seed in jobs:
        data = gen(agent, regime, seed)
        for win, (lo, hi) in [('P1', (0, 150)), ('P2', (150, 300))]:
            with Pool(2) as pool:
                fits = pool.map(fit_one, [(d[0], d[1], lo, hi, 73000+i)
                                          for i, d in enumerate(data)])
            lr = [np.log(f[0]/f[1]) for f in fits
                  if f is not None and f[0] > 1e-4 and f[1] > 1e-4]
            med = float(np.median(lr)); pos = float(np.mean([x > 0 for x in lr]))
            res[f'{agent}_{regime}_{win}'] = dict(median_log_ratio=round(med, 3),
                                                  frac_positive=round(pos, 3),
                                                  n=len(lr))
            print(agent, regime, win, 'median log(a+/a-) =', round(med, 3),
                  'frac>0 =', round(pos, 3), 'n =', len(lr), flush=True)
    import json
    json.dump(res, open('rustsim/out/dualalpha.json', 'w'), indent=1)
    print('DONE')
