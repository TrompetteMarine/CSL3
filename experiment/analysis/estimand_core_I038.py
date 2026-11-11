"""KGi-DISS-I038: shared pieces for the estimand map and its certification.

Estimand: psi = E[T | HIGH] / E[T | LOW], the evidence uptake of participants after
reference-dependent deprivation relative to controls (T = probe pair statistic).
"""
import json
import sys

import numpy as np
from scipy import stats as st

sys.path.insert(0, 'experiment/analysis')
import probe_generator as pg
from probe_design_I037 import ODDS, P1TAG, chi_min, multipliers

SEL = json.load(open('records/probe_design_I037_selected.json'))
D = SEL['S1x']
DESIGN = (D['r1'], D['r2'], D['k'], D['odds'])
P1 = D.get('p1', 'p65')
M, SCHEME = D['m'], D['scheme']
GATE_POINTS = [('P0', 1.0, .25, .6), ('P1', 1.0, .25, .4), ('P2', 1.0, .2918, .4), ('P3', .895, .25, .4),
               ('P4', 1.0, .25, chi_min(ODDS[D['odds']], P1TAG[P1][1]))]
RULES = ('outcome', 'event')
ALPHA1 = .005                      # one-sided level of every decision


def pools(kind, pt, n, gen):
    """the model's multiplier at probe time for n simulated participants per arm"""
    return multipliers(kind, DESIGN, pt[1], pt[2], pt[3], n=n, gen=gen, p1tag=P1)


def coupling(shape, mean_c, n, gen):
    """a vector of couplings with the given mean, assigned independently of everything else"""
    if shape == 'hom':
        c = np.full(n, mean_c)
    elif shape == 'two01':                      # share mean_c at 1, the rest at 0
        c = (gen.random(n) < mean_c).astype(float)
    elif shape == 'two51':                      # share p at 1, the rest at .5
        c = np.where(gen.random(n) < (mean_c - .5) / .5, 1.0, .5)
    elif shape == 'skew':                       # c = 1 - u^k, mean 1 - 1/(k+1)
        c = 1 - gen.random(n) ** (1 / (1 - mean_c) - 1)
    else:
        raise ValueError(shape)
    return c


def weight_ratio(mh, ml, ch, cl, rule):
    """noise-free model value of psi among attentive participants"""
    return pg.weight(1 - ch * (1 - mh), M, rule).mean() / pg.weight(1 - cl * (1 - ml), M, rule).mean()


def tstat(mult, c, sigma, rule, gen, inatt=.10, extra=0.0, attentive=False):
    return pg.probe_stat(mult, c, M, SCHEME, sigma, rule, gen, inattentive=inatt, extra_inattentive=extra,
                         return_attentive=attentive)


def fieller(mh, vh, ml, vl, df, level=1 - 2 * ALPHA1):
    """confidence limits for mu_H / mu_L from means and variances OF THE MEANS (arrays allowed).
    Returns (lo, hi); (-inf, inf) where the denominator is not separated from zero."""
    t = st.t.ppf(.5 + level / 2, df)
    a = ml ** 2 - t ** 2 * vl
    b = mh * ml
    c = mh ** 2 - t ** 2 * vh
    disc = np.maximum(b ** 2 - a * c, 0.0)
    ok = a > 0
    lo = np.where(ok, (b - np.sqrt(disc)) / np.where(ok, a, 1.0), -np.inf)
    hi = np.where(ok, (b + np.sqrt(disc)) / np.where(ok, a, 1.0), np.inf)
    return lo, hi


def draw(th, tl, nh, nl, b, gen):
    """b replicate samples from two large pools: means, variances of the means, psi-hat, limits"""
    xh = th[gen.integers(0, len(th), (b, nh))]
    xl = tl[gen.integers(0, len(tl), (b, nl))]
    mh, ml = xh.mean(1), xl.mean(1)
    vh, vl = xh.var(1, ddof=1) / nh, xl.var(1, ddof=1) / nl
    lo, hi = fieller(mh, vh, ml, vl, nh + nl - 2)
    return dict(mh=mh, ml=ml, vh=vh, vl=vl, psi=mh / ml, lo=lo, hi=hi, xh=xh, xl=xl)


def se_if(th, tl, nh, nl):
    """standard error of psi-hat from the influence function, at the pool (population) values"""
    psi = th.mean() / tl.mean()
    return np.sqrt(th.var() / nh + psi ** 2 * tl.var() / nl) / tl.mean()
