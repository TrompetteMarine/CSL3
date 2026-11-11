"""KGi-DISS-I039 figure: the model-generated distribution of the probe statistic and the
functions built on it (reads the records; computes nothing new).
    python experiment/analysis/fig_likelihood_I039.py   ->  records/fig_likelihood_I039.png
"""
import json
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

SURFACE, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
S1, S2, S3 = '#2a78d6', '#eb6834', '#1baf7a'          # validated categorical slots 1-3 (light surface)
plt.rcParams.update({'font.size': 9.5, 'axes.edgecolor': GRID, 'axes.labelcolor': INK2, 'text.color': INK,
                     'xtick.color': INK2, 'ytick.color': INK2, 'axes.facecolor': SURFACE,
                     'figure.facecolor': SURFACE, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.6, 'axes.titlesize': 10.5,
                     'axes.titleweight': 'bold', 'axes.titlelocation': 'left'})
cv = json.load(open('records/likelihood_curves_I039.json'))['P1|event']
t = np.array(cv['t'])
sel = (t >= -60) & (t <= 110)


def row(path, key):
    for line in open(path):
        if key in line:
            return [float(x) for x in re.findall(r'\d\.\d{3}', line.split(key)[1])][:13]
    raise KeyError(key)


N = [4, 6, 8, 10, 12, 16, 20, 24, 30, 36, 48, 60, 72]
np_ = row('records/frontier_I039.txt', 'P4 event   T only, NP')
iv = row('records/frontier_I039.txt', 'P4 event   interval D1')
lr = row('records/frontier_ad_I039.txt', 'P4 power, true weight 0.5:')

fig, ax = plt.subplots(2, 2, figsize=(10.6, 7.4))
a = ax[0, 0]
for y, c, lab in ((cv['pH'], S1, 'HIGH, full coupling'), (cv['pL'], S2, 'LOW'), (cv['p0'], S3, 'HIGH, no coupling')):
    a.plot(t[sel], np.array(y)[sel] / 2.5, color=c, lw=2, label=lab)
a.text(1, 0.0219, 'HIGH', color=INK, fontsize=8.5, ha='center')
a.text(35, 0.0150, 'LOW', color=INK, fontsize=8.5, ha='center')
a.text(40, 0.0211, 'HIGH if no coupling', color=INK, fontsize=8.5, ha='center')
a.set_ylim(-0.0006, 0.0262)
a.set_title('What the model generates for the probe statistic T')
a.set_xlabel('T (forecast points)'); a.set_ylabel('probability per point')
a.legend(frameon=False, fontsize=8, loc='upper right')

b = ax[0, 1]
b.axhline(0, color=INK2, lw=0.6)
b.plot(t[sel], np.array(cv['score_c_H'])[sel], color=S1, lw=2)
b.set_title('Score for the coupling c, one HIGH participant')
b.set_xlabel('T (forecast points)'); b.set_ylabel('d log-likelihood / dc')

c_ = ax[1, 0]
c_.axhline(0, color=INK2, lw=0.6)
c_.plot(t[sel], np.array(cv['phi_np_H'])[sel], color=S1, lw=2, label='ratio of means (plug-in)')
c_.plot(t[sel], np.array(cv['phi_eff_H'])[sel], color=S2, lw=2, label='efficient (from the likelihood)')
c_.annotate('ratio of means', (80, 4.87), (52, 5.6), color=INK, fontsize=8.5)
c_.annotate('efficient', (70, 0.85), (78, -0.6), color=INK, fontsize=8.5)
c_.set_title('Influence of one HIGH participant on the estimate of ψ')
c_.set_xlabel('T (forecast points)'); c_.set_ylabel('influence')
c_.legend(frameon=False, fontsize=8, loc='upper left')

d = ax[1, 1]
d.axhline(0.9, color=INK2, lw=0.6)
for y, c, lab in ((np_, S1, 'most powerful test, everything known'),
                  (lr, S2, 'likelihood ratio, baseline weight unknown'),
                  (iv, S3, 'model-free interval')):
    d.plot(N, y, color=c, lw=2, marker='o', ms=4.5, mec=SURFACE, mew=1.2, label=lab)
d.text(71.5, 0.862, 'power .90', color=INK2, fontsize=8, ha='right')
d.set_title('Power to detect reduced learning at the weakest gate point')
d.set_xlabel('participants per arm'); d.set_ylabel('power at one-sided .005')
d.set_ylim(0, 1.03); d.set_xticks([4, 12, 24, 36, 48, 60, 72])
d.legend(frameon=False, fontsize=8, loc='lower right')

fig.suptitle('Model-generated likelihood for the lab probe (central gate point, one-update rule; synthetic)',
             x=0.012, ha='left', fontsize=11.5, fontweight='bold')
fig.tight_layout(rect=(0, 0, 1, 0.965))
fig.savefig('records/fig_likelihood_I039.png', dpi=200)
