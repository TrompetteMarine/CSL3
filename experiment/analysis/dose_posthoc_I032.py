"""POST-HOC dose diagnostic (I032, run after E6 failed) — committed verbatim in the
audit so that records/dose_posthoc_I032.txt has committed provenance. Latent
units, no measurement layer. Informs an author decision; not evidence for a
repair. Seed 132900. Run from the repo root:
    python experiment/analysis/dose_posthoc_I032.py > records/dose_posthoc_I032.txt
"""
import sys, numpy as np
sys.path.insert(0,'experiment/analysis')
import market_generator as mg
rng=np.random.default_rng(132900)
N=20000
print("POST-HOC latent dose diagnostic (seed 132900, n=20000/cell, MODERATE only, latent trust x100)")
print(f"{'gen':12s} {'mu_ref':>6s} {'P2drop':>7s} {'lateP2':>7s} {'lateP3':>7s} {'P3-P2':>7s}  by rho: P2drop(.002) P2drop(.02)")
for kind,chi in (('gate',.6),('gate',.4),('rival_au',.6)):
    res={}
    for mu in (.45,.55,.65):
        lat=mg.simulate_latent(kind,N,'HIGH',rng,mu_ref=mu,chi=chi,resto_mix=(1,0))
        L=100*lat['ratings'].astype(float)
        drop=L[:,0:30].mean(1)-L[:,30:60].mean(1)
        lateP2=L[:,45:60].mean(1); lateP3=L[:,75:90].mean(1)
        slow=lat['rho']==.002
        res[mu]=(drop.mean(),lateP2.mean(),lateP3.mean())
        print(f"{kind+'/'+str(chi):12s} {mu:6.2f} {drop.mean():7.1f} {lateP2.mean():7.1f} {lateP3.mean():7.1f} {(lateP3-L[:,30:60].mean(1)).mean():7.1f}   {drop[slow].mean():6.1f} {drop[~slow].mean():6.1f}")
    for k,name in ((0,'P2drop'),(1,'lateP2'),(2,'lateP3')):
        v=[res[m][k] for m in (.45,.55,.65)]
        C=v[2]-2*v[1]+v[0]; span=v[2]-v[0]
        print(f"   second difference {name}: C={C:+6.2f}  (span .45->.65 = {span:+6.1f}; |C|/|span| = {abs(C)/max(abs(span),1e-9):.2f})")
