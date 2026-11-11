"""Evidence-uptake probe simulator (KGi-DISS-I037).

After the deprivation rounds a participant meets unfamiliar tickets. For each
ticket they give a paid forecast (0-100, steps of 5), see a small real record of
m settlements, and forecast again. The revision towards the evidence measures
how much authority the evidence has.

Model layer (assumptions about people; every one is a pilot quantity):
  learning multiplier   g = 1 - c (1 - M)      M = the model's own multiplier at
                                                probe time (gate: legitimacy L;
                                                R4/R1: belief the market is fair;
                                                R3: 1), c = coupling strength
  revision weight       per-outcome: w = 1 - (1 - ALPHA g)^m   (count-linear lemma)
                        per-event:   w = OMEGA g               (one update per record)
  prior                 b0 ~ N(50, 10) clipped to [5, 95], independent of arm
  reports               pre = round5(b0 + eps), post = round5(b0 + w (e - b0) + eps'),
                        eps ~ N(0, sigma_f), clipped to [0, 100]
  inattention           a share of participants do not revise on any probe (w = 0)

Schemes (statistic T per participant; HIGH is predicted to have smaller T):
  'single'   one ticket, favourable record e+ = (m-1)/m:          T = post - pre
  'pair'     two tickets, records e+ and e- = 1/m:                T = d(e+) - d(e-)
  'pair2'    two pairs, averaged
  'did'      one market pair minus one control-source pair (control: g = 1)
The pair cancels the prior: E[T] = 100 w (e+ - e-).
"""
import numpy as np

ALPHA = 0.2
OMEGA = 0.5
REPS = {'single': 1, 'pair': 2, 'pair2': 4, 'did': 4}


def weight(g, m, integration):
    if integration == 'outcome':
        return 1 - (1 - ALPHA * g) ** m
    if integration == 'event':
        return OMEGA * g
    raise ValueError(integration)


def _round5(x):
    return np.clip(np.round(x / 5) * 5, 0, 100)


def _revision(w, e, sigma_f, rng):
    n = len(w)
    b0 = np.clip(rng.normal(50, 10, n), 5, 95)
    pre = _round5(b0 + rng.normal(0, sigma_f, n))
    post = _round5(b0 + w * (100 * e - b0) + rng.normal(0, sigma_f, n))
    return post - pre


def _pair(w, m, sigma_f, rng):
    return _revision(w, (m - 1) / m, sigma_f, rng) - _revision(w, 1 / m, sigma_f, rng)


def probe_stat(mult, c, m, scheme, sigma_f, integration, rng, inattentive=0.10,
               extra_inattentive=0.0, return_attentive=False):
    """T for every participant. mult = model multiplier M at probe time (array)."""
    n = len(mult)
    g = 1 - c * (1 - np.asarray(mult, float))
    w = weight(g, m, integration)
    w_ctrl = np.full(n, weight(1.0, m, integration))
    off = rng.random(n) < min(1.0, inattentive + extra_inattentive)
    w = np.where(off, 0.0, w)
    w_ctrl = np.where(off, 0.0, w_ctrl)
    if scheme == 'single':
        t = _revision(w, (m - 1) / m, sigma_f, rng)
    elif scheme == 'pair':
        t = _pair(w, m, sigma_f, rng)
    elif scheme == 'pair2':
        t = 0.5 * (_pair(w, m, sigma_f, rng) + _pair(w, m, sigma_f, rng))
    elif scheme == 'did':
        t = _pair(w, m, sigma_f, rng) - _pair(w_ctrl, m, sigma_f, rng)
    else:
        raise ValueError(scheme)
    return (t, ~off) if return_attentive else t


def theta(t_high, t_low):
    """P(T_low > T_high) + .5 P(tie), exact from the two samples."""
    s = np.sort(t_high)
    lo = np.searchsorted(s, t_low, side='left')
    hi = np.searchsorted(s, t_low, side='right')
    return (lo.sum() + 0.5 * (hi - lo).sum()) / (len(t_high) * len(t_low))


def n_asymptotic(th):
    """per-arm n for a one-sided WMW at .005 with power .90 (no-tie approximation)."""
    return 2.48 / (th - 0.5) ** 2 if th > 0.5 else np.inf
