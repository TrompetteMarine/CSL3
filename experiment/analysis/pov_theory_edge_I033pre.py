"""Participant-view predictions at the theory edges (pre-I033; exploratory, NOT a
certification). Written before running.

Questions:
Q1  Inside the market task, what does a participant at each theory point see,
    report and do, round by round? Cells: HIGH x MODERATE and HIGH x FULL with
    the board held HIGH in P3, and LOW x MODERATE with it held LOW (P3 regime =
    arm, realised by conditioning on the iid P3 regime).
    Seen: own win rate over the last 15 rounds (the screen does NOT show it; it
    is the participant's felt rate), the board's last-15 win rate (shown),
    total points incl. windfalls (shown).
    Reported: fairness slider ("the market settles fairly") and entitlement
    slider ("what I deserve to win per round") as expected positions at the
    theory's own link (a = 1: 100*L, 100*A) and at the minimum gain the
    exploratory certification needs (a = .25: 50 + .25*(100*L - 50)); noise-free
    expectations, no rounding.
    Done: share of rounds choosing the better ticket.
Q2  Perceptibility from the participant's side: rounds after each phase switch
    until the own last-15 rate first crosses half-way to the new phase level
    (median over subjects); own wins per 15 rounds by phase.
Points: P0 paper (s 1, ratio .25, chi .6); P1 ABM (1, .25, .4); P2 ratio edge
(1, .2918, .4); P3 speed edge (.895, .25, .4); P4 anchoring edge (1, .25, .322);
R3 at chi .4 and .6. Edge values from records/invcal.csv via
records/100_inverse_calibration_I032pc.md. n = 9000 per arm. Seed 133100.
Outputs: records/pov_theory_edge_I033pre.{csv,txt}, figures/pov_theory_edge_I033pre.png
Run from the repo root:
    python experiment/analysis/pov_theory_edge_I033pre.py
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, 'experiment/analysis')
import market_generator as mg

rng = np.random.default_rng(133100)
N = 9000
NUF0, NUR0 = mg.NUF, mg.NUR
POINTS = [('P0 paper', 'gate', 1.0, .25, .6), ('P1 ABM', 'gate', 1.0, .25, .4),
          ('P2 ratio edge', 'gate', 1.0, .2918, .4), ('P3 speed edge', 'gate', .895, .25, .4),
          ('P4 anchor edge', 'gate', 1.0, .25, .322),
          ('R3 chi .4', 'rival_au', 1.0, .25, .4), ('R3 chi .6', 'rival_au', 1.0, .25, .6)]
CELLS = [('HIGH x MOD', 'HIGH', False), ('LOW x MOD', 'LOW', False), ('HIGH x FULL', 'HIGH', True)]


def trailing15(x):
    c = np.cumsum(x, axis=1, dtype=float)
    out = np.empty(x.shape)
    out[:, :15] = c[:, :15] / np.arange(1, 16)
    out[:, 15:] = (c[:, 15:] - c[:, :-15]) / 15
    return out


def run(kind, s, ratio, chi, arm):
    mg.NUF, mg.NUR = NUF0 * s, NUF0 * s * ratio
    try:
        return mg.simulate_latent(kind, N, arm, rng, chi=chi, trace=True)
    finally:
        mg.NUF, mg.NUR = NUF0, NUR0


def first_cross(tr, t0, target, up):
    seg = tr[:, t0:t0 + 150]
    hit = seg >= target if up else seg <= target
    first = np.where(hit.any(1), hit.argmax(1), 150)
    return float(np.median(first))


series, rows, percept = [], [], []
for name, kind, s, ratio, chi in POINTS:
    pools = {arm: run(kind, s, ratio, chi, arm) for arm in ('HIGH', 'LOW')}
    for cname, arm, full in CELLS:
        lat = pools[arm]
        reg = lat['reg3'] if arm == 'HIGH' else ~lat['reg3']
        sel = reg & (lat['resto_full'] == full)
        own = trailing15(lat['R'][sel])
        board = trailing15(lat['peer'][sel])
        better = (lat['arm'][sel] == 0).astype(float)
        wind = np.zeros(450); wind[14::15] = 3
        points = np.cumsum(lat['R'][sel].mean(0)) + np.cumsum(wind)
        L = 100 * lat['ratings'][sel].astype(float)
        A = 100 * lat['ent'][sel].astype(float)
        t_rate = np.arange(5, 451, 5)
        for k, t in enumerate(t_rate):
            series.append(dict(point=name, cell=cname, t=t, own15=own[:, t - 1].mean(),
                               board15=board[:, t - 1].mean(),
                               better=better[:, max(0, t - 15):t].mean(),
                               points=points[t - 1], fair_a1=L[:, k].mean(),
                               fair_a025=50 + .25 * (L[:, k].mean() - 50), ent_a1=A[:, k].mean()))
        for ph, sl, rs in (('P1', slice(0, 150), slice(0, 30)), ('P2', slice(150, 300), slice(30, 60)),
                           ('P3 late', slice(375, 450), slice(75, 90))):
            rows.append(dict(point=name, cell=cname, phase=ph,
                             own_rate=lat['R'][sel][:, sl].mean(), board_rate=lat['peer'][sel][:, sl].mean(),
                             wins_per_15=15 * lat['R'][sel][:, sl].mean(),
                             fair_a1=L[:, rs].mean(), fair_a025=50 + .25 * (L[:, rs].mean() - 50),
                             ent_a1=A[:, rs].mean(), better_ticket=better[:, sl].mean()))
        p1 = own[:, 100:150].mean(); p2 = own[:, 250:300].mean(); p3 = own[:, 400:450].mean()
        percept.append(dict(point=name, cell=cname,
                            p2_switch_rounds=first_cross(own, 150, (p1 + p2) / 2, up=False),
                            p3_switch_rounds=first_cross(own, 300, (p2 + p3) / 2, up=True),
                            own_late_p1=p1, own_late_p2=p2, own_late_p3=p3))

ser = pd.DataFrame(series)
tab = pd.DataFrame(rows)
per = pd.DataFrame(percept)
ser.to_csv('records/pov_theory_edge_I033pre.csv', index=False)
with open('records/pov_theory_edge_I033pre.txt', 'w') as fh:
    fh.write("Participant-view predictions at the theory edges (seed 133100; n=9000/arm; P3 regime = arm)\n")
    fh.write("fair_a1 = 100L (theory link); fair_a025 = 50 + .25(100L - 50); ent_a1 = 100A\n\n")
    fh.write(tab.round(3).to_string(index=False))
    fh.write("\n\nPerceptibility (median rounds after the switch until own last-15 rate first crosses half-way)\n")
    fh.write(per.round(3).to_string(index=False))
    fh.write("\n")
print(open('records/pov_theory_edge_I033pre.txt').read())

# ------------------------------------------------------------------ figure
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
COL = {'P1 ABM': '#2a78d6', 'P2 ratio edge': '#eb6834', 'P3 speed edge': '#1baf7a',
       'P4 anchor edge': '#eda100'}
GATES = list(COL)
plt.rcParams.update({'font.size': 9, 'axes.edgecolor': INK2, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'axes.facecolor': SURF,
                     'figure.facecolor': SURF, 'axes.spines.top': False, 'axes.spines.right': False})
fig, axes = plt.subplots(5, 3, figsize=(13, 15), sharex=True)
rowdefs = [('seen', 'What they see:\nwin rate, last 15 rounds'),
           ('fair_a1', 'Fairness slider\n(theory link, a = 1)'),
           ('fair_a025', 'Fairness slider\n(minimum gain, a = .25)'),
           ('ent_a1', 'Entitlement slider\n("what I deserve")'),
           ('better', 'Chooses the better ticket\n(share, last 15 rounds)')]
for j, (cname, _, _) in enumerate(CELLS):
    for i, (key, lab) in enumerate(rowdefs):
        ax = axes[i, j]
        for x0 in (150, 300):
            ax.axvline(x0, color=GRID, lw=1, zorder=0)
        ax.grid(axis='y', color=GRID, lw=.6)
        if key == 'seen':
            d = ser[(ser.point == 'P1 ABM') & (ser.cell == cname)]
            ax.plot(d.t, d.board15, color=INK2, lw=2, ls='--', label='board (shown on screen)')
            ax.plot(d.t, d.own15, color=INK, lw=2, label='own (felt; not shown)')
            ax.set_ylim(0, 1)
            if j == 0:
                ax.legend(frameon=False, loc='lower left', fontsize=8)
        else:
            d = ser[(ser.point == 'R3 chi .4') & (ser.cell == cname)]
            ax.plot(d.t, d[key], color='#9a9993', lw=2, label='R3 utility rival (no gate)')
            for g in GATES:
                d = ser[(ser.point == g) & (ser.cell == cname)]
                ax.plot(d.t, d[key], color=COL[g], lw=2, label=f'gate, {g}')
            ax.set_ylim(0, 1.0 if key == 'better' else 100)
            if key == 'fair_a025':
                ax.set_ylim(30, 70)
            if i == 1 and j == 0:
                ax.legend(frameon=False, loc='lower left', fontsize=8)
        if i == 0:
            ax.set_title(cname + ('  (board held HIGH in P3)' if 'HIGH' in cname else '  (board held LOW)'),
                         color=INK, fontsize=10, loc='left')
        if j == 0:
            ax.set_ylabel(lab)
        if i == 4:
            ax.set_xlabel('round')
            ax.set_xticks([0, 150, 300, 450])
for ax in axes[0]:
    for x, txt in ((75, 'P1 rich'), (225, 'P2 deprivation'), (375, 'P3 restoration')):
        ax.text(x, .96, txt, ha='center', va='top', color=INK2, fontsize=8)
fig.suptitle('The theory edge as a participant lives it: predicted screen, sliders and choices '
             '(model output, not data)', x=.01, ha='left', color=INK, fontsize=12)
fig.tight_layout(rect=(0, 0, 1, .975))
fig.savefig('figures/pov_theory_edge_I033pre.png', dpi=150)
print("figure written")
