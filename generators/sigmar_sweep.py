"""I014: sigma_r sensitivity of the MAP_LA identification screen (frozen 00_freeze_I014).
Reruns the I003 screen's DISS-generator recovery (60 synthetic subjects, MAP, L+A,
6 starts) at sigma_r in {0.05, 0.10, 0.20}; generative and assumed noise move together.
Fresh seed bases 300000/310000/320000 (disjoint from all prior seed ranges).
"""
import sys, json, time
import numpy as np
from multiprocessing import Pool

sys.path.insert(0, '/home/claude/kgi-diss-i003/30_stats')
import recovery_v3 as RC

PN = ['alpha', 'beta', 'nuF', 'nuR', 'tauF', 'rho', 'chi']

def one(args):
    base, i = args
    rng = np.random.default_rng(base + i)
    th = RC.MODELS['DISS']['sample'](rng)
    ch, rw, refs, Lr, Ar, _ = RC.generate('DISS', th, np.random.default_rng(base + 1000 + i))
    f, x = RC.fit('DISS', ch, rw, refs, Lr, Ar, np.random.default_rng(base + 2000 + i),
                  map_prior=True, starts=6)
    return th, (x.tolist() if x is not None else None)

if __name__ == '__main__':
    out = {}
    t0 = time.time()
    for sig, base in [(0.05, 300000), (0.10, 310000), (0.20, 320000)]:
        RC.SIGR = sig
        with Pool(2) as pool:
            res = pool.map(one, [(base, i) for i in range(60)])
        tr = np.array([t for t, e in res if e is not None])
        es = np.array([e for t, e in res if e is not None])
        out[str(sig)] = {PN[j]: float(np.corrcoef(tr[:, j], es[:, j])[0, 1]) for j in range(7)}
        out[str(sig)]['n_ok'] = int(len(tr))
        print(sig, json.dumps({k: round(v, 3) if isinstance(v, float) else v
                               for k, v in out[str(sig)].items()}),
              round(time.time() - t0), flush=True)
    json.dump(out, open('rustsim/out/sigmar_sweep.json', 'w'), indent=1)
    print('DONE', round(time.time() - t0))
