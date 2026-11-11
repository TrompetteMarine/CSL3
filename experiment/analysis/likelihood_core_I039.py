"""KGi-DISS-I039: the likelihood of what one participant produces in design S1x, built
from the legitimacy distribution that ABM agents generate by performing the task.

Observables per participant: arm, last fairness rating F, probe statistic T.

    p(t | arm)    = q k(t | 0) + (1 - q) * sum_l G_arm(l) k(t | w(l; c))
    p(f, t | arm) = sum_l G_arm(l) h(f | l) [ q k(t | 0) + (1 - q) k(t | w(l; c)) ]

    G_arm   empirical distribution of legitimacy at probe time over ABM agents
    k(t|w)  exact distribution of the probe statistic for revision weight w (no Monte Carlo)
    h(f|l)  rating: 50 + a (100 l - 50) + N(0, sigma_r), rounded to 5, clipped to [0, 100]
"""
import sys

import numpy as np
from scipy import stats as st

sys.path.insert(0, 'experiment/analysis')
import estimand_core_I038 as ec
import probe_generator as pg

REP = np.arange(0, 101, 5.0)                    # support of one report (21 values)
TGRID = np.arange(-80, 81) * 2.5                # support of T (161 values)
DW = 0.001
WGRID = -0.05 + DW * np.arange(1051)            # revision weights -0.05 .. 1.00
LGRID = np.linspace(0, 1, 1001)                 # legitimacy grid
BASE = dict(c=1.0, kap=pg.OMEGA, alpha=pg.ALPHA, sig=12.0, q=0.10, a=0.5, sr=5.8, lam=0.0)
STEP = dict(c=0.01, kap=0.005, alpha=0.002, sig=0.25, q=0.01, a=0.01, sr=0.1, lam=None)


def report_pmf(mu, sigma):
    """P(report = v) for report = clip(round(x / 5) * 5, 0, 100), x ~ N(mu, sigma)."""
    edges = np.r_[-np.inf, REP[:-1] + 2.5, np.inf]
    return np.diff(st.norm.cdf((edges - np.asarray(mu, float)[..., None]) / sigma), axis=-1)


def prior_nodes(nb=361):
    """quadrature for the prior b0 = clip(N(PRIOR_MU, PRIOR_SD), 5, 95): nodes and weights"""
    b = np.linspace(5, 95, nb)
    w = st.norm.pdf(b, pg.PRIOR_MU, pg.PRIOR_SD)
    w[0] *= .5
    w[-1] *= .5
    lo = st.norm.cdf(5, pg.PRIOR_MU, pg.PRIOR_SD)
    hi = 1 - st.norm.cdf(95, pg.PRIOR_MU, pg.PRIOR_SD)
    w *= (1 - lo - hi) / w.sum()
    w[0] += lo
    w[-1] += hi
    return b, w


def revision_pmf(w, e, sigma):
    """distribution of one revision d = post - pre on -100..100 (41 values), one row per weight"""
    b, wb = prior_nodes()
    pre = report_pmf(b, sigma)
    out = np.zeros((len(w), 41))
    for s in range(0, len(w), 128):
        ww = w[s:s + 128]
        post = report_pmf(b[None, :] + ww[:, None] * (100 * e - b[None, :]), sigma)
        for k in range(-20, 21):
            if k >= 0:
                pr = (post[:, :, k:] * pre[None, :, :21 - k]).sum(-1)
            else:
                pr = (post[:, :, :21 + k] * pre[None, :, -k:]).sum(-1)
            out[s:s + 128, k + 20] = pr @ wb
    return out


def kernel_T(w, sigma, m=None):
    """k(t | w): T = mean of two independent pair differences d(e+) - d(e-), same weight"""
    m = ec.M if m is None else m
    dp, dm = revision_pmf(w, (m - 1) / m, sigma), revision_pmf(w, 1 / m, sigma)
    K = np.empty((len(w), len(TGRID)))
    for i in range(len(w)):
        pair = np.convolve(dp[i], dm[i][::-1])
        K[i] = np.convolve(pair, pair)
    return K


def bin_pool(l):
    """empirical distribution of a pool of legitimacy values on LGRID (linear binning)"""
    x = np.clip(np.asarray(l, float), 0, 1) * (len(LGRID) - 1)
    i = np.minimum(x.astype(int), len(LGRID) - 2)
    f = x - i
    return (np.bincount(i, 1 - f, len(LGRID)) + np.bincount(i + 1, f, len(LGRID))) / len(x)


def weight_of(l, th, rule):
    g = 1 - th['c'] * (1 - l)
    return th['kap'] * g if rule == 'event' else 1 - (1 - th['alpha'] * g) ** ec.M


class Model:
    """likelihood tables at one gate point. G: {'HIGH': weights on LGRID, 'LOW': ...};
    G_other: the distributions mixed in by the depth parameter lam."""

    def __init__(self, G, G_other, rule, sigmas=(11.75, 12.0, 12.25)):
        self.G, self.Go, self.rule = G, G_other, rule
        self.K = {s: kernel_T(WGRID, s) for s in sigmas}

    def _kt(self, th):
        w = weight_of(LGRID, th, self.rule)
        x = (w - WGRID[0]) / DW
        i = np.clip(x.astype(int), 0, len(WGRID) - 2)
        f = (x - i)[:, None]
        K = self.K[th['sig']]
        i0 = int(round(-WGRID[0] / DW))
        return (1 - f) * K[i] + f * K[i + 1], K[i0]

    def g(self, arm, th):
        return (1 - th['lam']) * self.G[arm] + th['lam'] * self.Go[arm]

    def pT(self, arm, th):
        kt, k0 = self._kt(th)
        return th['q'] * k0 + (1 - th['q']) * (self.g(arm, th) @ kt)

    def pFT(self, arm, th):
        kt, k0 = self._kt(th)
        h = report_pmf(50 + th['a'] * (100 * LGRID - 50), th['sr'])
        return (h * self.g(arm, th)[:, None]).T @ (th['q'] * k0[None, :] + (1 - th['q']) * kt)

    def table(self, arm, th, joint):
        return self.pFT(arm, th).ravel() if joint else self.pT(arm, th)

    def scores(self, arm, th, names, joint):
        """p and the score vectors d log p / d theta_j (central differences; lam is exact)"""
        p = self.table(arm, th, joint)
        s = []
        for nm in names:
            if nm == 'lam':
                d = self.table(arm, {**th, 'lam': 1.0}, joint) - self.table(arm, {**th, 'lam': 0.0}, joint)
            else:
                h = STEP[nm]
                d = (self.table(arm, {**th, nm: th[nm] + h}, joint) -
                     self.table(arm, {**th, nm: th[nm] - h}, joint)) / (2 * h)
            s.append(np.where(p > 1e-300, d / np.maximum(p, 1e-300), 0.0))
        return p, np.array(s)

    def info(self, th, names, joint):
        """Fisher information per participant in each arm"""
        out = {}
        for arm in ('HIGH', 'LOW'):
            p, s = self.scores(arm, th, names, joint)
            out[arm] = (s * p) @ s.T
        return out

    def psi(self, th):
        return (TGRID @ self.pT('HIGH', th)) / (TGRID @ self.pT('LOW', th))

    def grad_psi(self, th, names):
        g = []
        for nm in names:
            if nm == 'lam':
                g.append(self.psi({**th, 'lam': 1e-3}) / 1e-3 - self.psi(th) / 1e-3)
            else:
                h = STEP[nm]
                g.append((self.psi({**th, nm: th[nm] + h}) - self.psi({**th, nm: th[nm] - h})) / (2 * h))
        return np.array(g)


def eff_info(I, j=0):
    """information for parameter j after the others are profiled out"""
    return 1.0 / np.linalg.inv(I)[j, j]


def moments(p):
    mu = TGRID @ p
    return mu, (TGRID - mu) ** 2 @ p


def sample_idx(p, n, b, rng):
    p = np.asarray(p, float)
    return rng.choice(len(p), size=(b, n), p=p / p.sum())


def counts_of(idx, ncell):
    b = idx.shape[0]
    return np.bincount((idx + np.arange(b)[:, None] * ncell).ravel(), minlength=b * ncell).reshape(b, ncell)
