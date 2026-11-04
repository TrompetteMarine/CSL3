"""M1b winner confirmation: full S1 (n=120 fresh) + S2 confusion (4x20) at the winning
screen cell. Winner = cell passing the frozen gate (all of nuF,nuR,tauF,rho,chi >= .7);
if several pass, the one with the highest minimum gate-r; if none pass, the best cell is
run anyway and reported as FAILED-GATE (frozen fallback: model-free-primary permanently).
"""
import numpy as np, json, time
from multiprocessing import Pool
import recovery_v3 as RC

PN = ['alpha', 'beta', 'nuF', 'nuR', 'tauF', 'rho', 'chi']
GATE = ['nuF', 'nuR', 'tauF', 'rho', 'chi']

screen = json.load(open('screen_results.json'))
def minr(c): return min(screen[c][p] for p in GATE)
passing = [c for c in screen if screen[c].get('PASS_GATE')]
WINNER = max(passing, key=minr) if passing else max(screen, key=minr)
USE_A = 'LA' in WINNER; USE_MAP = WINNER.startswith('MAP')
print('WINNER CELL:', WINNER, 'use_A:', USE_A, 'use_map:', USE_MAP, flush=True)

def s1_one(i):
    rng = np.random.default_rng(95000 + i)
    th = RC.MODELS['DISS']['sample'](rng)
    ch, rw, refs, Lr, Ar, _ = RC.generate('DISS', th, np.random.default_rng(96000 + i))
    f, x = RC.fit('DISS', ch, rw, refs, Lr, Ar if USE_A else None,
                  np.random.default_rng(97000 + i), map_prior=USE_MAP, starts=6)
    return th, (x.tolist() if x is not None else None)

def s2_one(args):
    g, i = args
    rng = np.random.default_rng(98000 + 97 * i + sum(map(ord, g)))
    th = RC.MODELS[g]['sample'](rng)
    ch, rw, refs, Lr, Ar, _ = RC.generate(g, th, np.random.default_rng(99000 + 100 * i + sum(map(ord, g))))
    bics = {}
    for m in RC.MODELS:
        f, x = RC.fit(m, ch, rw, refs, Lr, Ar if USE_A else None,
                      np.random.default_rng(99500 + i), map_prior=USE_MAP, starts=4)
        nobs = RC.T + len(Lr) * (2 if USE_A else 1)
        bics[m] = 2 * f + RC.MODELS[m]['k'] * np.log(nobs)
    return g, min(bics, key=bics.get)

if __name__ == '__main__':
    t0 = time.time(); out = {'winner_cell': WINNER}
    with Pool(2) as pool:
        res = pool.map(s1_one, range(120))
        tr = np.array([t for t, e in res if e is not None])
        es = np.array([e for t, e in res if e is not None])
        out['S1_final'] = {PN[j]: float(np.corrcoef(tr[:, j], es[:, j])[0, 1]) for j in range(7)}
        out['S1_PASS'] = bool(all(out['S1_final'][p] >= .7 for p in GATE))
        print('S1', json.dumps(out['S1_final']), 'PASS:', out['S1_PASS'], round(time.time()-t0), flush=True)
        jobs = [(g, i) for g in RC.MODELS for i in range(20)]
        res2 = pool.map(s2_one, jobs)
        conf = {g: {m: 0 for m in RC.MODELS} for g in RC.MODELS}
        for g, w in res2:
            conf[g][w] += 1
        out['S2_final'] = conf
        out['S2_PASS'] = bool(all(conf[g][g] >= 12 for g in conf))  # 12/20 = .6
        print('S2', json.dumps(conf), 'PASS:', out['S2_PASS'], round(time.time()-t0), flush=True)
    json.dump(out, open('winner_results.json', 'w'), indent=1)
    print('TOTAL', time.time() - t0)
