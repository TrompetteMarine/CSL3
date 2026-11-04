"""
Model-generated predictions for the preregistered task v3 (KGi-DISS-I008).
Frozen design: 00_freeze_I008.yaml (task_v3_predictions + addendum 1).
OUTPUT IS MODEL PREDICTION, NOT DATA. n=300 simulated subjects per condition.
"""
import numpy as np, csv

T = 450; CAD = 5
PH = {1: (.65, .35), 2: (.30, .15)}
RESTO = {'FULL': (.65, .35), 'MODERATE': (.45, .35)}
NUF, NUR, TAUF, PHIM, PHIP, ALPHA, BETA = .05, .0125, .3, 1.0, .25, .2, 12.0
CHI, A0, L0, PI0, MURIG = .6, .5, 1.0, .9, .3
GAM_AU = 0.85   # I014: aspiration-in-utility rival (I003 R3 class, prior midpoint)
N = 300

def phase_means(t, resto):
    if t < 150: return PH[1]
    if t < 300: return PH[2]
    return RESTO[resto]

def simulate(agent, regime, resto, seed):
    rng = np.random.default_rng(seed)
    rows = []   # per subject: series of (t, trust, ent, acc)
    h4 = []     # (d_trust, shortfall)
    for s in range(N):
        rho = .002 if s % 2 == 0 else .02
        Q = np.array([.5, .5]); L, A = L0, A0
        lp = np.log(PI0/(1-PI0))
        ent_exp = A0; rec_au = 0.5
        peer_hits = 0; own_recent = []
        prev_trust = None; prev_ent = None; short_acc = []; series = []
        for t in range(T):
            mu = phase_means(t, resto)
            pi = 1/(1+np.exp(-lp))
            dq = (pi if agent=='rival' else 1.0)*(Q[0]-Q[1])
            p0 = 1/(1+np.exp(-BETA*dq))
            arm = 0 if rng.random() < p0 else 1
            R = 1.0 if rng.random() < mu[arm] else 0.0
            peer_R = 1.0 if rng.random() < (.65 if regime=='HIGH'
                       else np.clip(np.mean(own_recent[-15:]) if own_recent else .5,.05,.95)) else 0.0
            peer_hits += peer_R; peer_rate = peer_hits/(t+1)
            own_recent.append(R)
            if agent == 'diss':
                Q[arm] += ALPHA*L*(R-Q[arm])
                D = PHIM*max(A-R,0)+PHIP*max(R-A,0)
                L = float(np.clip(L - NUF*max(D-TAUF,0) + NUR*(D<=TAUF), 0, 1))
                ref = peer_rate if regime=='HIGH' else np.mean(own_recent[-15:])
                A = float(np.clip((1-rho)*A + rho*((1-CHI)*R + CHI*ref), 0, 1))
                trust, ent = 100*L, 100*A
                short_acc.append(max(A-R, 0.0))
            elif agent == 'rival_au':
                # I014: aspiration-in-utility rival, ported VERBATIM from the I003 R3
                # class (recovery_v3.py) incl. its own fairness-rating link
                # (freeze addendum 1); states: A (aspiration), rec_au (recent EWMA).
                u = R - GAM_AU*max(A-R, 0)
                Q[arm] = float(np.clip(Q[arm] + ALPHA*(u-Q[arm]), -1, 1))
                rec_au = 0.9*rec_au + 0.1*R
                ref = peer_rate if regime=='HIGH' else np.mean(own_recent[-15:])
                A = float(np.clip((1-rho)*A + rho*((1-CHI)*R + CHI*ref), 0, 1))
                L_au = float(np.clip(1 - GAM_AU*max(A - rec_au, 0), 0, 1))
                trust, ent = 100*L_au, 100*A
                short_acc.append(max(A-R, 0.0))
            else:
                muhat = np.clip(Q[arm], .05, .95)
                own = R*np.log(muhat/MURIG) + (1-R)*np.log((1-muhat)/(1-MURIG))
                if agent == 'rival_us':
                    obs = 0.0   # group-contingent rig: peer outcomes carry no likelihood
                else:
                    mup = np.clip(peer_rate, .05, .95)
                    obs = peer_R*np.log(mup/MURIG) + (1-peer_R)*np.log((1-mup)/(1-MURIG))
                lp = float(np.clip(lp + own + obs, -12, 12))
                Q[arm] += ALPHA*pi*(R-Q[arm])
                ent_exp = (1-.02)*ent_exp + .02*R
                trust, ent = 100/(1+np.exp(-lp)), 100*ent_exp
                short_acc.append(max(ent_exp-R, 0.0))
            if (t+1) % CAD == 0:
                acc = 1.0 if arm == 0 else 0.0
                series.append((t+1, trust, ent, acc))
                if prev_trust is not None:
                    h4.append((trust-prev_trust, float(np.mean(short_acc))))
                prev_trust = trust; short_acc = []
        rows.append(series)
    return rows, h4

conds = [('diss','HIGH','FULL'), ('diss','LOW','FULL'), ('diss','HIGH','MODERATE'),
         ('rival','HIGH','FULL'), ('rival','LOW','FULL'), ('rival','HIGH','MODERATE'),
         ('rival_us','HIGH','FULL'), ('rival_us','LOW','FULL'), ('rival_us','HIGH','MODERATE'),
         # I014 (freeze addendum 1): aspiration-in-utility rival, seeds 71000..71002
         ('rival_au','HIGH','FULL'), ('rival_au','LOW','FULL'), ('rival_au','HIGH','MODERATE')]
fsub = open('rustsim/out/pred_subjects.csv','w',newline='')
wsub = csv.writer(fsub)
wsub.writerow(['agent','regime','resto','subj','rho','drop_p2','lag','slope_p3','h4_coef'])
with open('rustsim/out/pred_series.csv','w',newline='') as f1, \
     open('rustsim/out/pred_h4.csv','w',newline='') as f2:
    w1 = csv.writer(f1); w1.writerow(['agent','regime','resto','t','trust_m','trust_q1','trust_q3','ent_m','acc_m'])
    w2 = csv.writer(f2); w2.writerow(['agent','regime','resto','bin','dtrust_m','n'])
    for k,(ag,rg,rs) in enumerate(conds):
        seed = 70000+k if k < 9 else 71000+(k-9)   # frozen: new rival_au block at 71000+
        rows, h4 = simulate(ag, rg, rs, seed)
        arr = np.array(rows)  # (N, nprobe, 4)
        # subject-level summaries (frozen defs: drop = P1 mean - P2 mean of trust;
        # lag = rating-recovery midpoint minus choice-recovery midpoint in P3, censored
        # at 450; slope_p3 = OLS slope of trust on t in P3 (per 100 trials);
        # h4_coef = per-subject OLS of per-interval d-trust on shortfall)
        tgrid = arr[0,:,0]
        p1m = tgrid <= 150; p2m = (tgrid > 150) & (tgrid <= 300); p3m = tgrid > 300
        nprobe_per_subj = p3m.sum()
        h4arr = np.array(h4).reshape(N, -1, 2)  # per subject sequence
        for si in range(N):
            tr = arr[si,:,1]; ac = arr[si,:,3]
            drop = tr[p1m].mean() - tr[p2m].mean()
            halfb = (ac[p1m].mean() + ac[p2m].mean())/2
            halfr = (tr[p1m].mean() + tr[p2m].mean())/2
            t3 = tgrid[p3m]; a3 = ac[p3m]; r3 = tr[p3m]
            ib = np.argmax(np.convolve(a3, np.ones(3)/3, 'same') >= halfb) if (a3 >= halfb).any() else -1
            irx = np.argmax(r3 >= halfr) if (r3 >= halfr).any() else -1
            mb = t3[ib] if ib >= 0 else 450.0
            mr = t3[irx] if irx >= 0 else 450.0
            slope = np.polyfit(t3, r3, 1)[0]*100 if len(t3) > 3 else np.nan
            hh = h4arr[si]
            mask = ~np.isnan(hh[:,1])
            coef = np.polyfit(hh[mask,1], hh[mask,0], 1)[0] if mask.sum() > 10 and np.std(hh[mask,1]) > 1e-9 else np.nan
            rho = .002 if si % 2 == 0 else .02
            wsub.writerow([ag,rg,rs,si,rho,f"{drop:.3f}",f"{mr-mb:.1f}",f"{slope:.4f}",
                           f"{coef:.4f}" if not np.isnan(coef) else ''])
        for j in range(arr.shape[1]):
            t = int(arr[0,j,0])
            tr = arr[:,j,1]; en = arr[:,j,2]; ac = arr[:,j,3]
            w1.writerow([ag,rg,rs,t,f"{tr.mean():.3f}",f"{np.quantile(tr,.25):.3f}",
                         f"{np.quantile(tr,.75):.3f}",f"{en.mean():.3f}",f"{ac.mean():.4f}"])
        h = np.array(h4)
        bins = np.linspace(0, .7, 15)
        idx = np.digitize(h[:,1], bins)
        for b in range(1, 15):
            m = idx == b
            if m.sum() > 30:
                w2.writerow([ag,rg,rs,f"{(bins[b-1]+bins[b])/2:.3f}",
                             f"{h[m,0].mean():.3f}", int(m.sum())])
        print(ag, rg, rs, 'done')
fsub.close()
