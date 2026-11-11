"""KGi-DISS-I038 part C: Monte Carlo certification of the estimator of psi (freeze
00_freeze_I038.yaml, addendum AD-B1). Needs records/estimand_map_I038.json. Seed 135100.
    python experiment/analysis/estimand_cert_I038.py > records/estimand_cert_I038.txt
"""
import json

import numpy as np
from scipy import optimize, stats as st

import estimand_core_I038 as ec
import probe_generator as pg
import stats_v2 as sv

rng = np.random.default_rng(135100)
NL, NT, B = 40000, 300000, 4000
TH = json.load(open('records/estimand_map_I038.json'))
PSI_HI, PSI_CERT = TH['psi_hi'], TH['psi_cert']
gate = {p[0]: ec.pools('gate', p, NL, rng) for p in ec.GATE_POINTS}
ZA, ZB = st.norm.ppf(1 - ec.ALPHA1), st.norm.ppf(.90)


def tpool(mult, c, rule, sigma=12.0, inatt=.10, extra=0.0, attentive=False):
    """a large pool of probe statistics for one arm (resampled multipliers; c scalar or shape tuple)"""
    m = mult[rng.integers(0, len(mult), NT)]
    cc = ec.coupling(c[0], c[1], NT, rng) if isinstance(c, tuple) else c
    return ec.tstat(m, cc, sigma, rule, rng, inatt=inatt, extra=extra, attentive=attentive)


def c_for(psi, pt, rule):
    g = gate[pt]
    return optimize.brentq(lambda c: ec.weight_ratio(g['HIGH'], g['LOW'], c, c, rule) - psi, 0.0, 1.0)


def summ(th, tl, nh, nl, b=B):
    d = ec.draw(th, tl, nh, nl, b, rng)
    truth = th.mean() / tl.mean()
    return dict(truth=truth, bias=d['psi'].mean() - truth, se=d['psi'].std(ddof=1), se_if=ec.se_if(th, tl, nh, nl),
                cover=np.mean((d['lo'] <= truth) & (truth <= d['hi'])), width=np.median(d['hi'] - d['lo']),
                below1=np.mean(d['hi'] < 1), above_hi=np.mean(d['lo'] > PSI_HI), below_hi=np.mean(d['hi'] < PSI_HI),
                below_cert=np.mean(d['hi'] < PSI_CERT), d=d)


def n_asym(th, tl, psi0):
    """per-arm n (equal split) for power .90 at one-sided .005 to put psi on the far side of psi0"""
    psi = th.mean() / tl.mean()
    v1 = (th.var() + psi ** 2 * tl.var()) / tl.mean() ** 2
    return (ZA + ZB) ** 2 * v1 / (psi - psi0) ** 2


print("KGi-DISS-I038 part C: certification of psi-hat = mean(T_HIGH) / mean(T_LOW) (seed 135100)")
print(f"thresholds from the map: upper edge of the trap set {PSI_HI:.3f}; coupling-certified {PSI_CERT:.3f}\n")

# ------------------------------------------------------------------ I. invariance
print("I. DISS-PSI-INVARIANT: model value of psi from pooled reports (rounded, clipped, noisy)")
for pt, c in (('P1', 1.0), ('P1', .75), ('P4', 1.0)):
    for rule in ec.RULES:
        g = gate[pt]
        base = tpool(g['HIGH'], c, rule).mean() / tpool(g['LOW'], c, rule).mean()
        row = [f"base {base:.3f}"]
        dev = 0.0
        for lab, kw in (('noise 8', dict(sigma=8.0)), ('noise 16', dict(sigma=16.0)),
                        ('inattentive 0', dict(inatt=0.0)), ('inattentive .2', dict(inatt=.2))):
            v = tpool(g['HIGH'], c, rule, **kw).mean() / tpool(g['LOW'], c, rule, **kw).mean()
            dev = max(dev, abs(v - base)); row.append(f"{lab} {v:.3f}")
        for lab, (mu, sd) in (('prior 35', (35.0, 10.0)), ('prior 65', (65.0, 10.0)), ('prior sd 20', (50.0, 20.0))):
            pg.PRIOR_MU, pg.PRIOR_SD = mu, sd
            v = tpool(g['HIGH'], c, rule).mean() / tpool(g['LOW'], c, rule).mean()
            pg.PRIOR_MU, pg.PRIOR_SD = 50.0, 10.0
            dev = max(dev, abs(v - base)); row.append(f"{lab} {v:.3f}")
        pg.NOISE = 't3'
        v = tpool(g['HIGH'], c, rule).mean() / tpool(g['LOW'], c, rule).mean()
        pg.NOISE = 'normal'
        dev = max(dev, abs(v - base)); row.append(f"t3 noise {v:.3f}")
        print(f"  {pt} c={c} {rule:8s}: " + "  ".join(row) + f"   largest move {dev:.3f}", flush=True)

print("  rule sensitivity given the control arm's absolute revision weight W0 (P1; w = 1 - (1 - a g)^k, a matched to W0)")
g = gate['P1']
for w0 in (.3, .5, .85):
    print(f"    W0 = {w0}:  " + "  ".join(f"c={c}" for c in (.5, .75, .9, .95, 1.0)) + "    (rows: k = 1, 3, 10; then range)")
    tab = []
    for k in (1, 3, 10):
        row = []
        for c in (.5, .75, .9, .95, 1.0):
            gl, gh = 1 - c * (1 - g['LOW']), 1 - c * (1 - g['HIGH'])
            f = lambda a: (1 - (1 - a * gl) ** k).mean() - w0
            if f(1.0) < 0:
                row.append(np.nan); continue
            a = optimize.brentq(f, 1e-6, 1.0)
            row.append((1 - (1 - a * gh) ** k).mean() / w0)
        tab.append(row)
        print(f"      k={k:<2}     " + "  ".join(f"{x:5.3f}" for x in row))
    tab = np.array(tab)
    print("      range    " + "  ".join(f"{x:5.3f}" for x in np.nanmax(tab, 0) - np.nanmin(tab, 0)), flush=True)

# ------------------------------------------------------------------ II. regularity
print("\nII. DISS-PSI-REGULAR (P1, noise 12; 99% Fieller interval; B = 4000)")
print("    target  rule     noise   n/arm  truth   bias    s.e.   s.e.(IF)  coverage  median width")
reg = {}
for psi in (.15, .26, .5, .8, 1.0):
    c = c_for(psi, 'P1', 'event') if psi < 1 else 0.0
    reg[psi] = (tpool(gate['P1']['HIGH'], c, 'event'), tpool(gate['P1']['LOW'], c, 'event'))
    for n in ((36, 72, 150) if psi == .26 else (72,)):
        s = summ(*reg[psi], n, n)
        print(f"    {psi:<6}  event    normal  {n:<5}  {s['truth']:.3f}  {s['bias']:+.4f}  {s['se']:.4f}  {s['se_if']:.4f}    "
              f"{s['cover']:.4f}    {s['width']:.3f}", flush=True)
s = summ(tpool(gate['P1']['HIGH'], 1.0, 'outcome'), tpool(gate['P1']['LOW'], 1.0, 'outcome'), 72, 72)
print(f"    c = 1   outcome  normal  72     {s['truth']:.3f}  {s['bias']:+.4f}  {s['se']:.4f}  {s['se_if']:.4f}    {s['cover']:.4f}    {s['width']:.3f}")
pg.NOISE = 't3'
for psi in (.26, 1.0):
    c = c_for(psi, 'P1', 'event') if psi < 1 else 0.0
    s = summ(tpool(gate['P1']['HIGH'], c, 'event'), tpool(gate['P1']['LOW'], c, 'event'), 72, 72)
    print(f"    {psi:<6}  event    t3      72     {s['truth']:.3f}  {s['bias']:+.4f}  {s['se']:.4f}  {s['se_if']:.4f}    {s['cover']:.4f}    {s['width']:.3f}")
pg.NOISE = 'normal'

# ------------------------------------------------------------------ III. allocation
print("\nIII. DISS-PSI-ALLOC (P1, event rule, noise 12, total N = 144)")
th, tl = reg[.26]
psi = th.mean() / tl.mean()
opt = th.std() / (psi * tl.std())
print(f"    psi = {psi:.3f}: s.d. of T HIGH {th.std():.1f}, LOW {tl.std():.1f}; efficient n_H / n_L = {opt:.2f}")
v_eq = ec.se_if(th, tl, 72, 72) ** 2
for nh, nl in ((72, 72), (96, 48), (108, 36), (115, 29)):
    s = summ(th, tl, nh, nl)
    print(f"    split {nh}/{nl}: s.e. {s['se']:.4f} (IF {s['se_if']:.4f}); median width {s['width']:.3f}; coverage {s['cover']:.4f}; "
          f"N for the s.e. of 72/72: {144 * s['se_if'] ** 2 / v_eq:.0f}", flush=True)
print("    test of psi < 1 at the weakest point (P4, c = 1, event rule): rejection rate of the rank test | of the interval")
t4h, t4l = tpool(gate['P4']['HIGH'], 1.0, 'event'), tpool(gate['P4']['LOW'], 1.0, 'event')
for nh, nl in ((72, 72), (96, 48), (108, 36)):
    d = ec.draw(t4h, t4l, nh, nl, 1000, rng)
    wm = np.mean([sv.wmw_one_sided(d['xh'][i], d['xl'][i])[0] for i in range(1000)])
    print(f"    split {nh}/{nl}: {wm:.3f} | {np.mean(d['hi'] < 1):.3f}", flush=True)

# ------------------------------------------------------------------ IV. decisions
print("\nIV. DISS-PSI-DECISIONS (noise 12; one-sided .005 each; n = 72 per arm unless stated)")
print("  D1 (psi < 1) and D4 (psi below the upper edge of the trap set), at full coupling:")
print("    point rule      psi    D1 power  n for .90   D4 power  n for .90   D3 power (psi < certified threshold)")
full = {}
for p in ec.GATE_POINTS:
    for rule in ec.RULES:
        th, tl = tpool(gate[p[0]]['HIGH'], 1.0, rule), tpool(gate[p[0]]['LOW'], 1.0, rule)
        full[(p[0], rule)] = (th, tl)
        s = summ(th, tl, 72, 72)
        print(f"    {p[0]}    {rule:8s}  {s['truth']:.3f}  {s['below1']:.3f}     {n_asym(th, tl, 1.0):5.0f}       "
              f"{s['below_hi']:.3f}     {n_asym(th, tl, PSI_HI):5.0f}       {s['below_cert']:.3f}", flush=True)
print("  Monte Carlo check of the asymptotic n (power at that n):")
for key, psi0, lab in ((('P4', 'event'), 1.0, 'D1'), (('P4', 'outcome'), PSI_HI, 'D4'), (('P1', 'event'), PSI_HI, 'D4')):
    th, tl = full[key]
    n = max(8, int(np.ceil(n_asym(th, tl, psi0))))
    d = ec.draw(th, tl, n, n, B, rng)
    print(f"    {lab} at {key[0]} {key[1]}: n = {n}, power {np.mean(d['hi'] < psi0):.3f}")
print("  false positives of D1 under the rivals (n = 72):")
riv = {'R3': dict(HIGH=np.ones(NL), LOW=np.ones(NL)), 'R4': ec.pools('rival_us', ('R', 1.0, .25, .6), NL, rng),
       'R1': ec.pools('rival', ('R', 1.0, .25, .6), NL, rng)}
k3 = int(round(.5595 * NL))
riv['composite'] = {a: np.r_[riv['R3'][a][:k3], riv['R4'][a][k3:]] for a in ('HIGH', 'LOW')}
for rule in ec.RULES:
    row = []
    for k, v in riv.items():
        s = summ(tpool(v['HIGH'], 1.0, rule), tpool(v['LOW'], 1.0, rule), 72, 72)
        row.append(f"{k} {s['below1']:.4f} (psi {s['truth']:.3f})")
    print(f"    {rule:8s}: " + "  ".join(row), flush=True)
print("  D2 (trap excluded: lower limit above the upper edge), homogeneous coupling at P1's gate parameters:")
print("    c     rule      psi    power at 72 / 150 / 300    n for .90")
for c in (0.0, .25, .5, .75):
    for rule in ec.RULES:
        th, tl = tpool(gate['P1']['HIGH'], c, rule), tpool(gate['P1']['LOW'], c, rule)
        pw = [summ(th, tl, n, n, 2000)['above_hi'] for n in (72, 150, 300)]
        psi = th.mean() / tl.mean()
        na = n_asym(th, tl, PSI_HI) if psi > PSI_HI else np.inf
        print(f"    {c:<4}  {rule:8s}  {psi:.3f}  {pw[0]:.3f} / {pw[1]:.3f} / {pw[2]:.3f}          {na:.0f}", flush=True)
cb = c_for(PSI_HI, 'P1', 'event')
s = summ(tpool(gate['P1']['HIGH'], cb, 'event'), tpool(gate['P1']['LOW'], cb, 'event'), 150, 150)
print(f"  error rates exactly at the upper edge (P1, event, c = {cb:.3f}, psi {s['truth']:.3f}, n = 150): "
      f"D2 {s['above_hi']:.4f}   D4 {s['below_hi']:.4f}")

# ------------------------------------------------------------------ V. attention-check exclusion
print("\nV. DISS-PSI-ATTRITION (P1, event rule, noise 12, n = 72 randomised per arm; check: inattentive fail .8, attentive .05)")
print("    truth   extra disengaged   psi all randomised   psi after exclusion   trimming interval: covers truth | upper < 1 | median [lo, hi]")


def lee(xh, kh, xl, kl):
    """HIGH retained = always-retained under monotone exclusion; trim the LOW retained sample"""
    th_, tl_ = xh[kh], xl[kl]
    rh, rl = kh.mean(), kl.mean()
    if rl <= rh or len(th_) < 5:
        lo, hi = ec.fieller(th_.mean(), th_.var(ddof=1) / len(th_), tl_.mean(), tl_.var(ddof=1) / len(tl_),
                            len(th_) + len(tl_) - 2)
        return float(lo), float(hi)
    k = int(round(len(tl_) * (rl - rh) / rl))
    srt = np.sort(tl_)
    top, bot = srt[:len(srt) - k], srt[k:]           # top trimmed (smaller mean), bottom trimmed (larger mean)
    df = len(th_) + len(top) - 2
    mh, vh = th_.mean(), th_.var(ddof=1) / len(th_)
    _, hi = ec.fieller(mh, vh, top.mean(), top.var(ddof=1) / len(top), df)
    lo, _ = ec.fieller(mh, vh, bot.mean(), bot.var(ddof=1) / len(bot), df)
    return float(lo), float(hi)


for lab, mult, c in (('c = 1', gate['P1'], 1.0), ('.26', gate['P1'], c_for(.26, 'P1', 'event')),
                     ('R3', dict(HIGH=np.ones(NL), LOW=np.ones(NL)), 1.0)):
    for extra in (0.0, .1, .2):
        th, ah = tpool(mult['HIGH'], c, 'event', extra=extra, attentive=True)
        tl, al = tpool(mult['LOW'], c, 'event', attentive=True)
        fh = np.where(ah, rng.random(NT) < .05, rng.random(NT) < .8)
        fl = np.where(al, rng.random(NT) < .05, rng.random(NT) < .8)
        # attentive participants of the HIGH pool who are not among the extra disengaged: the first .9 share by draw
        truth = ec.weight_ratio(mult['HIGH'], mult['LOW'], c, c, 'event')
        cov = up = 0; los, his = [], []
        for _ in range(1500):
            ih, il = rng.integers(0, NT, 72), rng.integers(0, NT, 72)
            lo, hi = lee(th[ih], ~fh[ih], tl[il], ~fl[il])
            cov += lo <= truth <= hi; up += hi < 1; los.append(lo); his.append(hi)
        print(f"    {lab:6s}  +{extra:.0%}               {th.mean() / tl.mean():.3f}                {th[~fh].mean() / tl[~fl].mean():.3f}"
              f"                 {cov / 1500:.3f} | {up / 1500:.3f} | [{np.median(los):.2f}, {np.median(his):.2f}]   (truth among the attentive {truth:.3f})",
              flush=True)

# ------------------------------------------------------------------ VI. mean or median
print("\nVI. Q5: ratio of means against ratio of medians (P1, event rule, n = 72, B = 4000)")
for lab, c, noise in (('homogeneous, psi .26, normal noise', c_for(.26, 'P1', 'event'), 'normal'),
                      ('homogeneous, psi .26, t3 noise', c_for(.26, 'P1', 'event'), 't3'),
                      ('two types (0; 1) at the same mean coupling, normal noise', ('two01', c_for(.26, 'P1', 'event')), 'normal')):
    pg.NOISE = noise
    th, tl = tpool(gate['P1']['HIGH'], c, 'event'), tpool(gate['P1']['LOW'], c, 'event')
    pg.NOISE = 'normal'
    d = ec.draw(th, tl, 72, 72, B, rng)
    med = np.median(d['xh'], 1) / np.median(d['xl'], 1)
    print(f"    {lab}: mean-type truth {th.mean() / tl.mean():.3f}; ratio of means {d['psi'].mean():.3f} (s.e. {d['psi'].std():.3f}); "
          f"ratio of medians {med.mean():.3f} (s.e. {med.std():.3f})", flush=True)
