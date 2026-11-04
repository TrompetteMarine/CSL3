"""KGi-DISS-I003 / M1 — identification repair machinery (task v3).

Task v3 = 3 phases (arms as v2) + reference regime drawn iid per 150-trial block
+ windfalls every 15th trial + legitimacy slider every 5 trials
+ OPTIONAL aspiration slider every 5 trials (the model-derived repair).
Estimators: MLE, or MAP with weakly informative Gaussian priors (sd = full generative
range width — deliberately broader than generative; location at range midpoints).
R1/R2 carry a 1-param descriptive aspiration model (EWMA gain rho_d) so every model
accounts for ALL observations when aspiration ratings are included (recorded).
"""
import numpy as np
from scipy.optimize import minimize

T = 450
MU = np.zeros((T, 2)); MU[:150] = (.65, .35); MU[150:300] = (.30, .15); MU[300:] = (.70, .45)
BONUS = np.array([(t % 15) == 14 for t in range(T)])
PHIM, PHIP, SIGR, RATE_EVERY = 1.0, 0.25, 0.10, 5

# ---------------- state kernels (DISS, R1, R2, R3) ------------------------------
def diss_init(th): return {'Q': np.array([.5, .5]), 'L': 1.0, 'A': 0.5}

def diss_step(st, th, a, R, Rref, bonus):
    al, bs, nuF, nuR, tauF, rho, chi = th
    DF = PHIM * max(st['A'] - R, 0) + PHIP * max(R - st['A'], 0)
    if not bonus:
        st['Q'][a] = min(1, max(0, st['Q'][a] + al * st['L'] * (R - st['Q'][a])))
    st['L'] = min(1, max(0, st['L'] - nuF * max(DF - tauF, 0) + nuR * (DF <= tauF)))
    st['A'] = min(1, max(0, (1 - rho) * st['A'] + rho * ((1 - chi) * R + chi * Rref)))

def diss_p1(st, th): return 1 / (1 + np.exp(-th[1] * (st['Q'][0] - st['Q'][1])))
def diss_L(st, th): return st['L']
def diss_A(st, th): return st['A']

def r1_init(th): return {'Q': np.array([.5, .5]), 'lo': np.log(th[3] / (1 - th[3])), 'Ad': 0.5}

def r1_step(st, th, a, R, Rref, bonus):
    al, bs, mur, pi0, rhod = th
    if not bonus:
        pi = 1 / (1 + np.exp(-st['lo']))
        qf = min(.95, max(.05, st['Q'][a]))
        st['lo'] = min(12, max(-12, st['lo'] + (np.log(qf / mur) if R else np.log((1 - qf) / (1 - mur)))))
        st['Q'][a] = min(1, max(0, st['Q'][a] + al * pi * (R - st['Q'][a])))
    st['Ad'] = min(1, max(0, (1 - rhod) * st['Ad'] + rhod * R))

def r1_p1(st, th):
    pi = 1 / (1 + np.exp(-st['lo']))
    return 1 / (1 + np.exp(-th[1] * pi * (st['Q'][0] - st['Q'][1])))
def r1_L(st, th): return 1 / (1 + np.exp(-st['lo']))
def r1_A(st, th): return st['Ad']

def r2_init(th): return {'Q': np.array([.5, .5]), 'as': 0.5, 'Ad': 0.5}

def r2_step(st, th, a, R, Rref, bonus):
    k, om, bs, rhod = th
    if not bonus:
        d = R - st['Q'][a]
        st['Q'][a] = min(1, max(0, st['Q'][a] + min(1, k * st['as']) * d))
        st['as'] = (1 - om) * st['as'] + om * abs(d)
    st['Ad'] = min(1, max(0, (1 - rhod) * st['Ad'] + rhod * R))

def r2_p1(st, th): return 1 / (1 + np.exp(-th[2] * (st['Q'][0] - st['Q'][1])))
def r2_L(st, th): return 1 - st['as']
def r2_A(st, th): return st['Ad']

def r3_init(th): return {'Q': np.array([.5, .5]), 'A': 0.5, 'recent': 0.5}

def r3_step(st, th, a, R, Rref, bonus):
    al, bs, gam, rho3, chi3 = th
    if not bonus:
        u = R - gam * max(st['A'] - R, 0)
        st['Q'][a] = min(1, max(-1, st['Q'][a] + al * (u - st['Q'][a])))
    st['recent'] = 0.9 * st['recent'] + 0.1 * R
    st['A'] = min(1, max(0, (1 - rho3) * st['A'] + rho3 * ((1 - chi3) * R + chi3 * Rref)))

def r3_p1(st, th): return 1 / (1 + np.exp(-th[1] * (st['Q'][0] - st['Q'][1])))
def r3_L(st, th): return min(1, max(0, 1 - th[2] * max(st['A'] - st['recent'], 0)))
def r3_A(st, th): return st['A']

MODELS = {
    'DISS': dict(init=diss_init, step=diss_step, p1=diss_p1, L=diss_L, A=diss_A, k=7,
                 sample=lambda r: [r.uniform(.1, .4), r.uniform(3, 10), r.uniform(.02, .10),
                                   r.uniform(.005, .03), r.uniform(.15, .45),
                                   r.uniform(.002, .05), r.uniform(.2, .6)],
                 prior_mu=[.25, 6.5, .06, .0175, .30, .026, .40],
                 prior_sd=[.30, 7.0, .08, .025, .30, .048, .40],
                 bounds=lambda t: 0 < t[0] < 1 and 0 < t[1] < 30 and 0 <= t[2] < .5 and
                                  0 <= t[3] < .2 and 0 <= t[4] < 1 and 0 < t[5] < .5 and 0 <= t[6] <= 1),
    'R1': dict(init=r1_init, step=r1_step, p1=r1_p1, L=r1_L, A=r1_A, k=5,
               sample=lambda r: [r.uniform(.1, .4), r.uniform(3, 10), r.uniform(.1, .5),
                                 r.uniform(.6, .98), r.uniform(.002, .05)],
               prior_mu=[.25, 6.5, .30, .79, .026], prior_sd=[.30, 7.0, .40, .38, .048],
               bounds=lambda t: 0 < t[0] < 1 and 0 < t[1] < 30 and .02 < t[2] < .8 and
                                .5 < t[3] < .999 and 0 < t[4] < .5),
    'R2': dict(init=r2_init, step=r2_step, p1=r2_p1, L=r2_L, A=r2_A, k=4,
               sample=lambda r: [r.uniform(.2, 1.5), r.uniform(.05, .5), r.uniform(3, 10),
                                 r.uniform(.002, .05)],
               prior_mu=[.85, .275, 6.5, .026], prior_sd=[1.3, .45, 7.0, .048],
               bounds=lambda t: 0 < t[0] < 3 and 0 < t[1] < 1 and 0 < t[2] < 30 and 0 < t[3] < .5),
    'R3': dict(init=r3_init, step=r3_step, p1=r3_p1, L=r3_L, A=r3_A, k=5,
               sample=lambda r: [r.uniform(.1, .4), r.uniform(3, 10), r.uniform(.2, 1.5),
                                 r.uniform(.002, .05), r.uniform(.2, .6)],
               prior_mu=[.25, 6.5, .85, .026, .40], prior_sd=[.30, 7.0, 1.3, .048, .40],
               bounds=lambda t: 0 < t[0] < 1 and 0 < t[1] < 30 and 0 <= t[2] < 3 and
                                0 < t[3] < .5 and 0 <= t[4] <= 1),
}

def block_regimes(rng):
    return [('high' if rng.random() < .5 else 'own') for _ in range(3)]

def generate(model, th, rng):
    m = MODELS[model]
    st = m['init'](th)
    regs = block_regimes(rng)
    own_trail = 0.5
    ch = np.empty(T, int); rw = np.empty(T); refs = np.empty(T)
    Lr, Ar = [], []
    for t in range(T):
        p1 = m['p1'](st, th)
        a = 0 if rng.random() < p1 else 1
        R = 1.0 if BONUS[t] else float(rng.random() < MU[t, a])
        own_trail = 0.98 * own_trail + 0.02 * R
        pr = 0.65 if regs[t // 150] == 'high' else min(.95, max(.05, own_trail))
        Rref = float(rng.random() < pr)
        m['step'](st, th, a, R, Rref, BONUS[t])
        ch[t], rw[t], refs[t] = a, R, Rref
        if (t + 1) % RATE_EVERY == 0:
            Lr.append(min(1, max(0, m['L'](st, th) + rng.normal(0, SIGR))))
            Ar.append(min(1, max(0, m['A'](st, th) + rng.normal(0, SIGR))))
    return ch, rw, refs, np.array(Lr), np.array(Ar), regs

def nll(model, th, ch, rw, refs, Lr=None, Ar=None, map_prior=False):
    m = MODELS[model]
    if not m['bounds'](th):
        return 1e9
    st = m['init'](th)
    ll = 0.0; ri = 0
    for t in range(T):
        p1 = m['p1'](st, th)
        p = p1 if ch[t] == 0 else 1 - p1
        ll += np.log(max(p, 1e-12))
        m['step'](st, th, ch[t], rw[t], refs[t], BONUS[t])
        if Lr is not None and (t + 1) % RATE_EVERY == 0:
            ll += -0.5 * ((Lr[ri] - m['L'](st, th)) / SIGR) ** 2
            if Ar is not None:
                ll += -0.5 * ((Ar[ri] - m['A'](st, th)) / SIGR) ** 2
            ri += 1
    out = -ll
    if map_prior:
        for v, mu0, sd in zip(th, m['prior_mu'], m['prior_sd']):
            out += 0.5 * ((v - mu0) / sd) ** 2
    return out

def fit(model, ch, rw, refs, Lr, Ar, rng, map_prior=False, starts=6):
    best = (np.inf, None)
    for s in range(starts):
        x0 = MODELS[model]['sample'](rng)
        try:
            res = minimize(lambda x: nll(model, x, ch, rw, refs, Lr, Ar, map_prior), x0,
                           method='Nelder-Mead',
                           options=dict(maxiter=2500, xatol=1e-4, fatol=1e-3))
            if res.fun < best[0]:
                best = (res.fun, res.x)
        except Exception:
            pass
    return best
