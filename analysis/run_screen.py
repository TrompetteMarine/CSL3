"""M1 repair screen: 4 cells x 60 DISS subjects. Gate: winner needs r>=.7 on all of
nuF, nuR, tauF, rho, chi."""
import numpy as np, json, time
from multiprocessing import Pool
import recovery_v3 as RC

PN = ['alpha', 'beta', 'nuF', 'nuR', 'tauF', 'rho', 'chi']

def one(args):
    i, use_A, use_map = args
    rng = np.random.default_rng(90000 + i)
    th = RC.MODELS['DISS']['sample'](rng)
    ch, rw, refs, Lr, Ar, _ = RC.generate('DISS', th, np.random.default_rng(91000 + i))
    f, x = RC.fit('DISS', ch, rw, refs, Lr, Ar if use_A else None,
                  np.random.default_rng(92000 + i), map_prior=use_map, starts=6)
    return th, (x.tolist() if x is not None else None)

if __name__ == '__main__':
    t0 = time.time(); out = {}
    cells = [('MLE_L', False, False), ('MLE_LA', True, False),
             ('MAP_L', False, True), ('MAP_LA', True, True)]
    with Pool(2) as pool:
        for name, use_A, use_map in cells:
            res = pool.map(one, [(i + hash(name) % 500, use_A, use_map) for i in range(60)])
            tr = np.array([t for t, e in res if e is not None])
            es = np.array([e for t, e in res if e is not None])
            out[name] = {PN[j]: float(np.corrcoef(tr[:, j], es[:, j])[0, 1]) for j in range(7)}
            gate = all(out[name][p] >= .7 for p in ['nuF', 'nuR', 'tauF', 'rho', 'chi'])
            out[name]['PASS_GATE'] = bool(gate)
            print(name, json.dumps(out[name]), round(time.time() - t0), flush=True)
    json.dump(out, open('screen_results.json', 'w'), indent=1)
    print('TOTAL', time.time() - t0)
