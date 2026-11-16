"""A bot that plays the task with the paper's gate kernel (KGi-DISS-I042).

Pipeline validation only: it lets the whole chain (app -> export -> analysis) be compared
with the certification's simulation. The kernel, the rating rule and the forecast rule are
those of analysis/twins_I040.py and analysis/probe_generator.py; the agent sees exactly the
settlements the app shows.
"""
import math
import random

NUF, TAUF, PHIM, PHIP, ALPHA, BETA, A0, L0 = .05, .3, 1.0, .25, .2, 12.0, .5, 1.0
OMEGA = 0.5
GATE_POINTS = {'P0': (1.0, 0.25, 0.6), 'P1': (1.0, 0.25, 0.4), 'P2': (1.0, 0.2918, 0.4),
               'P3': (0.895, 0.25, 0.4), 'P4': (1.0, 0.25, 0.30361608493602193)}
TRAIL = 15
ITEM_NOISE = 10.0            # one slider; the mean of three fairness items has noise 5.8
GAIN = 0.5
FORECAST_NOISE = 12.0
INATTENTIVE = 0.10


def _clip(x, lo=0.0, hi=1.0):
    return min(max(x, lo), hi)


def _round5(x):
    return int(min(max(round(x / 5) * 5, 0), 100))


class ModelAgent:
    def __init__(self, seed, slow, point='P1', rule='event', coupling=1.0):
        speed, ratio, self.chi = GATE_POINTS[point]
        self.nuf, self.nur = NUF * speed, NUF * speed * ratio
        self.rho = 0.002 if slow else 0.02
        self.rule, self.c = rule, coupling
        self.rng = random.Random(seed)
        self.Q = [0.5, 0.5]                # [better ticket, worse ticket]
        self.L, self.A = L0, A0
        self.ring, self.t, self.hits = [], 0, 0
        self.inattentive = self.rng.random() < INATTENTIVE

    def choose_good(self):
        return self.rng.random() < 1 / (1 + math.exp(-BETA * (self.Q[0] - self.Q[1])))

    def observe(self, chose_good, own, board, regime):
        arm = 0 if chose_good else 1
        for i, c in enumerate(own):
            R = 1.0 if c == '1' else 0.0
            if board:
                self.hits += board[i] == '1'
            self.Q[arm] += ALPHA * self.L * (R - self.Q[arm])
            D = PHIM * max(self.A - R, 0) + PHIP * max(R - self.A, 0)
            self.L = _clip(self.L - self.nuf * max(D - TAUF, 0) + self.nur * (D <= TAUF))
            self.ring = (self.ring + [R])[-TRAIL:]
            trail = sum(self.ring) / len(self.ring)
            ref = self.hits / (self.t + 1) if (board and regime == 'HIGH') else trail
            self.A = _clip((1 - self.rho) * self.A + self.rho * ((1 - self.chi) * R + self.chi * ref))
            self.t += 1

    def ratings(self):
        item = lambda m: _round5(50 + GAIN * (100 * m - 50) + self.rng.gauss(0, ITEM_NOISE))
        return [item(self.L) for _ in range(3)], item(self.A)

    def forecasts(self, e):
        g = 1 - self.c * (1 - self.L)
        w = 0.0 if self.inattentive else (OMEGA * g if self.rule == 'event' else 1 - (1 - ALPHA * g) ** 10)
        b0 = _clip(self.rng.gauss(50, 10), 5, 95)
        pre = _round5(b0 + self.rng.gauss(0, FORECAST_NOISE))
        post = _round5(b0 + w * (100 * e - b0) + self.rng.gauss(0, FORECAST_NOISE))
        return pre, post
