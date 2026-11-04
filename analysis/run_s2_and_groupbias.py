"""M1b (amended under the frozen fallback): screen gate FAILED in all 4 cells, so
individual-level full-vector inference is settled (infeasible). Two remaining questions:
(1) S2 model-comparison confusion at MAP_LA — is model COMPARISON calibratable?
(2) EXPLORATORY group-level bias: does the MAP_LA group MEAN of (nuF, nuR, tauF)
    recover the generative group mean? (n=60 fresh; bootstrap CI on bias.)
Deviation from the frozen M1b: S1-final (n=120) skipped — the screen verdict is
dispositive under the frozen rule; running it could not change the gate outcome.
Logged as a deviation with reason.
"""
import numpy as np, json, time
from multiprocessing import Pool
import recovery_v3 as RC

PN = ['alpha', 'beta', 'nuF', 'nuR', 'tauF', 'rho', 'chi']
USE_A, USE_MAP = True, True   # MAP_LA

def s2_one(args):
    g, i = args
    rng = np.random.default_rng(98000 + 97 * i + sum(map(ord, g)))
    th = RC.MODELS[g]['sample'](rng)
    ch, rw, refs, Lr, Ar, _ = RC.generate(g, th, np.random.default_rng(99000 + 100 * i + sum(map(ord, g))))
    bics = {}
    for m in RC.MODELS:
        f, x = RC.fit(m, ch, rw, refs, Lr, Ar, np.random.default_rng(99500 + i),
                      map_prior=USE_MAP, starts=4)
        nobs = RC.T + len(Lr) * 2
        bics[m] = 2 * f + RC.MODELS[m]['k'] * np.log(nobs)
    return g, min(bics, key=bics.get)

def gb_one(i):
    rng = np.random.default_rng(95000 + i)
    th = RC.MODELS['DISS']['sample'](rng)
    ch, rw, refs, Lr, Ar, _ = RC.generate('DISS', th, np.random.default_rng(96000 + i))
    f, x = RC.fit('DISS', ch, rw, refs, Lr, Ar, np.random.default_rng(97000 + i),
                  map_prior=USE_MAP, starts=6)
    return th, (x.tolist() if x is not None else None)

if __name__ == '__main__':
    t0 = time.time(); out = {'cell': 'MAP_LA', 'deviation': 'S1-final skipped (screen dispositive)'}
    with Pool(2) as pool:
        tr_es = pool.map(gb_one, range(60))
        tr = np.array([t for t, e in tr_es if e is not None])
        es = np.array([e for t, e in tr_es if e is not None])
        gb = {}
        rngb = np.random.default_rng(5)
        for j, p in enumerate(PN):
            bias = float(es[:, j].mean() - tr[:, j].mean())
            bs = [es[idx, j].mean() - tr[idx, j].mean()
                  for idx in rngb.integers(0, len(es), (2000, len(es)))]
            gb[p] = dict(true_mean=float(tr[:, j].mean()), est_mean=float(es[:, j].mean()),
                         bias=bias, bias_CI=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                         rel_bias=float(bias / tr[:, j].mean()))
        out['group_bias'] = gb
        print('GB', json.dumps(gb), round(time.time() - t0), flush=True)
        jobs = [(g, i) for g in RC.MODELS for i in range(20)]
        res2 = pool.map(s2_one, jobs)
        conf = {g: {m: 0 for m in RC.MODELS} for g in RC.MODELS}
        for g, w in res2:
            conf[g][w] += 1
        out['S2_final'] = conf
        out['S2_PASS'] = bool(all(conf[g][g] >= 12 for g in conf))
        print('S2', json.dumps(conf), 'PASS:', out['S2_PASS'], round(time.time() - t0), flush=True)
    json.dump(out, open('winner_results.json', 'w'), indent=1)
    print('TOTAL', time.time() - t0)
