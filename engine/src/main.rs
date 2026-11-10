// KGi-DISS NHB-figure mapping engine — zero-dependency Rust port of the audited
// simulator (frozen design: 00_freeze_figruns.yaml). RNG: xoshiro256++ seeded by
// SplitMix64. Distributional cross-validation against the Python engine (CV1-CV5)
// must pass before any sweep output is used.
use std::env;
use std::fs::File;
use std::io::{BufWriter, Write};
use std::thread;

// ---------------- RNG ----------------
struct Rng { s: [u64; 4] }
impl Rng {
    fn new(seed: u64) -> Self {
        let mut sm = seed;
        let mut next = || { sm = sm.wrapping_add(0x9E3779B97F4A7C15);
            let mut z = sm; z = (z ^ (z >> 30)).wrapping_mul(0xBF58476D1CE4E5B9);
            z = (z ^ (z >> 27)).wrapping_mul(0x94D049BB133111EB); z ^ (z >> 31) };
        Rng { s: [next(), next(), next(), next()] }
    }
    fn next_u64(&mut self) -> u64 {
        let r = (self.s[0].wrapping_add(self.s[3])).rotate_left(23).wrapping_add(self.s[0]);
        let t = self.s[1] << 17;
        self.s[2] ^= self.s[0]; self.s[3] ^= self.s[1];
        self.s[1] ^= self.s[2]; self.s[0] ^= self.s[3];
        self.s[2] ^= t; self.s[3] = self.s[3].rotate_left(45);
        r
    }
    fn f64(&mut self) -> f64 { (self.next_u64() >> 11) as f64 * (1.0 / 9007199254740992.0) }
}

#[inline] fn sigmoid(x: f64) -> f64 { 1.0 / (1.0 + (-x).exp()) }
#[inline] fn clip01(x: f64) -> f64 { x.max(0.0).min(1.0) }

#[derive(Clone, Copy)]
struct P {
    mu: [f64; 2], lam: f64, eta: f64, beta2: f64, alpha: f64,
    nu_f: f64, nu_r: f64, tau_f: f64, phim: f64, phip: f64,
    l0: f64, a0: f64, n: usize, t: usize, gamma: f64, chi: f64, rho: f64,
    global_cmp: bool, mu_rig: f64, pi0: f64,
    // I014 structural-robustness knobs (defaults reproduce the frozen engine exactly)
    n1: usize,              // community-1 size; 0 => n/2 (frozen symmetric default)
    field_unweighted: bool, // credibility weight C := 1 (unweighted action frequency)
    field_paybias: bool,    // credibility weight := agent's recent-earnings EWMA
    gamma_het: bool,        // per-agent permeability in {0, 2*gamma}, half-half
    // I036 gate-scope ablation (defaults reproduce the frozen engine exactly)
    gate_own: bool,         // legitimacy scales learning from own outcomes
    gate_soc: bool,         // legitimacy scales learning from observed others' outcomes
}
impl Default for P {
    fn default() -> Self { P { mu: [0.6, 0.4], lam: 0.5, eta: 0.2, beta2: 12.0, alpha: 0.2,
        nu_f: 0.05, nu_r: 0.0125, tau_f: 0.3, phim: 1.0, phip: 0.25,
        l0: 1.0, a0: 0.5, n: 200, t: 600, gamma: 0.1, chi: 0.4, rho: 0.002,
        global_cmp: true, mu_rig: 0.4, pi0: 0.9,
        n1: 0, field_unweighted: false, field_paybias: false, gamma_het: false,
        gate_own: true, gate_soc: true } }
}

#[derive(Clone, Copy, PartialEq)]
enum Gate { Diss, Off, Bayes, RigUs, DissNL }

struct Out { m2: f64, m1: f64, l2: f64, l1: f64, dwell2: f64 }

fn run(p: &P, gate: Gate, q0c1: [f64; 2], q0c2: [f64; 2], seed: u64,
       traj: Option<&mut Vec<(Vec<f32>, f64, f64, f64, f64)>>) -> Out {
    let n = p.n; let half = if p.n1 == 0 { n / 2 } else { p.n1 }; let t_len = p.t;
    let sz = [half as f64, (n - half) as f64];
    let b = [[1.0 - p.gamma, p.gamma], [p.gamma, 1.0 - p.gamma]];
    // per-agent permeability (heterogeneous variant: {0, 2*gamma} half-half per community)
    let gi: Vec<f64> = (0..n).map(|i| {
        if !p.gamma_het { p.gamma }
        else {
            let k = if i < half { i } else { i - half };
            if k % 2 == 0 { 0.0 } else { 2.0 * p.gamma }
        }
    }).collect();
    let mut rng = Rng::new(seed);
    let mut q = vec![[0.0f64; 2]; n];
    for i in 0..n { q[i] = if i < half { q0c1 } else { q0c2 }; }
    let mut l = vec![p.l0; n];
    let mut a = vec![p.a0; n];
    let mut lo = vec![(p.pi0 / (1.0 - p.pi0)).ln(); n];
    let mut ew = vec![0.5f64; n]; // recent-earnings EWMA (payoff-biased field variant)
    let (mut prev_act, mut prev_c): (Option<Vec<u8>>, Option<Vec<f64>>) = (None, None);
    let mut opt_tail = [0.0f64; 2]; let mut l_tail = [0.0f64; 2];
    let mut dwell2 = 0.0; let tail_from = t_len - 50;
    let mut traj_buf = traj;
    let mut act = vec![0u8; n]; let mut cdec = vec![0.0f64; n]; let mut rew = vec![0.0f64; n];

    for t in 0..t_len {
        // anticipatory field per community
        let mut s = [[0.0f64; 2]; 2];
        let mut phi = [[0.0f64; 2]; 2];
        let have_field = prev_act.is_some();
        if let (Some(pa), Some(pc)) = (&prev_act, &prev_c) {
            for c in 0..2 {
                let (lo_i, hi_i) = if c == 0 { (0, half) } else { (half, n) };
                for i in lo_i..hi_i { phi[c][pa[i] as usize] += pc[i]; }
                phi[c][0] /= sz[c]; phi[c][1] /= sz[c];
            }
            for c in 0..2 { for arm in 0..2 {
                s[c][arm] = b[c][0] * phi[0][arm] + b[c][1] * phi[1][arm]; } }
        }
        // choice + reward
        for i in 0..n {
            let c = if i < half { 0 } else { 1 };
            let dq = if matches!(gate, Gate::Bayes | Gate::RigUs)
                     { sigmoid(lo[i]) * (q[i][0] - q[i][1]) }
                     else { q[i][0] - q[i][1] };
            let sfield = if p.gamma_het && have_field {
                let o = 1 - c;
                [(1.0 - gi[i]) * phi[c][0] + gi[i] * phi[o][0],
                 (1.0 - gi[i]) * phi[c][1] + gi[i] * phi[o][1]]
            } else { s[c] };
            let delta = dq + p.lam * (sfield[0] - sfield[1]);
            let p1 = sigmoid(p.beta2 * delta);
            act[i] = if rng.f64() < p1 { 0 } else { 1 };
            cdec[i] = (2.0 * p1 - 1.0).abs();
            rew[i] = if rng.f64() < p.mu[act[i] as usize] { 1.0 } else { 0.0 };
        }
        // credibility-weight variants (I014): applied after choices, before aggregation
        if p.field_paybias {
            for i in 0..n { ew[i] = 0.9 * ew[i] + 0.1 * rew[i]; cdec[i] = ew[i]; }
        } else if p.field_unweighted {
            for i in 0..n { cdec[i] = 1.0; }
        }
        // community outcome stats
        let mut rbar = [0.0f64; 2];
        let mut wmass = [[0.0f64; 2]; 2]; let mut wrew = [[0.0f64; 2]; 2];
        for c in 0..2 {
            let (lo_i, hi_i) = if c == 0 { (0, half) } else { (half, n) };
            for i in lo_i..hi_i {
                rbar[c] += rew[i];
                let arm = act[i] as usize;
                wmass[c][arm] += cdec[i]; wrew[c][arm] += cdec[i] * rew[i];
            }
            rbar[c] /= sz[c];
            for arm in 0..2 { wmass[c][arm] /= sz[c]; wrew[c][arm] /= sz[c]; }
        }
        let popmean = if p.n1 == 0 { 0.5 * (rbar[0] + rbar[1]) }
                      else { (sz[0] * rbar[0] + sz[1] * rbar[1]) / (n as f64) };
        let mut expo = [[0.0f64; 2]; 2]; let mut erew = [[0.0f64; 2]; 2];
        for c in 0..2 { for arm in 0..2 {
            expo[c][arm] = b[c][0] * wmass[0][arm] + b[c][1] * wmass[1][arm];
            erew[c][arm] = b[c][0] * wrew[0][arm] + b[c][1] * wrew[1][arm]; } }
        // updates (synchronous; pre-update states for PEs and DF)
        for i in 0..n {
            let c = if i < half { 0 } else { 1 };
            let g = match gate { Gate::Diss | Gate::DissNL => l[i], Gate::Off => 1.0,
                                 Gate::Bayes | Gate::RigUs => sigmoid(lo[i]) };
            let arm = act[i] as usize;
            let qch = q[i][arm];
            let delta = rew[i] - qch;
            // both increments from pre-update Q (synchronous, as in the audited engine)
            let (xpo, xre) = if p.gamma_het {
                let o = 1 - c;
                ([(1.0 - gi[i]) * wmass[c][0] + gi[i] * wmass[o][0],
                  (1.0 - gi[i]) * wmass[c][1] + gi[i] * wmass[o][1]],
                 [(1.0 - gi[i]) * wrew[c][0] + gi[i] * wrew[o][0],
                  (1.0 - gi[i]) * wrew[c][1] + gi[i] * wrew[o][1]])
            } else { (expo[c], erew[c]) };
            let soc0 = xre[0] - xpo[0] * q[i][0];
            let soc1 = xre[1] - xpo[1] * q[i][1];
            let g_own = if p.gate_own { g } else { 1.0 };
            let g_soc = if p.gate_soc { g } else { 1.0 };
            q[i][arm] += p.alpha * g_own * delta;
            q[i][0] = clip01(q[i][0] + p.eta * g_soc * soc0);
            q[i][1] = clip01(q[i][1] + p.eta * g_soc * soc1);
            match gate {
                Gate::DissNL => {
                    // non-lexicographic variant (frozen I012): surprise erosion
                    let z = a[i] - rew[i];
                    let df = p.phim * z.max(0.0) + p.phip * (-z).max(0.0);
                    l[i] = clip01(l[i] - p.nu_f * (df - p.tau_f).max(0.0)
                                  + p.nu_r * if df <= p.tau_f { 1.0 } else { 0.0 }
                                  - p.nu_f * 0.5 * delta * delta);
                    let rref = if p.global_cmp { popmean }
                               else { b[c][0] * rbar[0] + b[c][1] * rbar[1] };
                    a[i] = clip01((1.0 - p.rho) * a[i]
                                  + p.rho * ((1.0 - p.chi) * rew[i] + p.chi * rref));
                }
                Gate::RigUs => {
                    // group-contingent rig: others' outcomes carry NO likelihood (I012)
                    let qf = qch.max(0.05).min(0.95);
                    let own = if rew[i] > 0.5 { (qf / p.mu_rig).ln() }
                              else { ((1.0 - qf) / (1.0 - p.mu_rig)).ln() };
                    lo[i] = (lo[i] + own).max(-12.0).min(12.0);
                }
                Gate::Diss => {
                    let z = a[i] - rew[i];
                    let df = p.phim * z.max(0.0) + p.phip * (-z).max(0.0);
                    l[i] = clip01(l[i] - p.nu_f * (df - p.tau_f).max(0.0)
                                  + p.nu_r * if df <= p.tau_f { 1.0 } else { 0.0 });
                    let rref = if p.global_cmp { popmean }
                               else { b[c][0] * rbar[0] + b[c][1] * rbar[1] };
                    a[i] = clip01((1.0 - p.rho) * a[i]
                                  + p.rho * ((1.0 - p.chi) * rew[i] + p.chi * rref));
                }
                Gate::Bayes => {
                    let qf = qch.max(0.05).min(0.95);
                    let own = if rew[i] > 0.5 { (qf / p.mu_rig).ln() }
                              else { ((1.0 - qf) / (1.0 - p.mu_rig)).ln() };
                    let mut obs = 0.0;
                    for ar in 0..2 {
                        if expo[c][ar] > 1e-9 {
                            let rb = (erew[c][ar] / expo[c][ar]).max(0.0).min(1.0);
                            let qf2 = q[i][ar].max(0.05).min(0.95); // post-update Q, as python
                            obs += expo[c][ar] * (rb * (qf2 / p.mu_rig).ln()
                                + (1.0 - rb) * ((1.0 - qf2) / (1.0 - p.mu_rig)).ln());
                        }
                    }
                    lo[i] = (lo[i] + own + obs).max(-12.0).min(12.0);
                }
                Gate::Off => {}
            }
        }
        // records (post-update gate variable, this trial's actions)
        let mut mopt = [0.0f64; 2]; let mut lbar = [0.0f64; 2]; let mut abar2 = 0.0f64;
        for i in 0..n {
            let c = if i < half { 0 } else { 1 };
            if act[i] == 0 { mopt[c] += 1.0; }
            lbar[c] += match gate { Gate::Bayes | Gate::RigUs => sigmoid(lo[i]),
                                    Gate::Off => 1.0,
                                    Gate::Diss | Gate::DissNL => l[i] };
            if c == 1 { abar2 += a[i]; }
        }
        for c in 0..2 { mopt[c] /= sz[c]; lbar[c] /= sz[c]; }
        abar2 /= sz[1];
        if lbar[1] < 0.3 { dwell2 += 1.0; }
        if t >= tail_from {
            opt_tail[0] += mopt[0]; opt_tail[1] += mopt[1];
            l_tail[0] += lbar[0]; l_tail[1] += lbar[1];
        }
        if let Some(buf) = traj_buf.as_deref_mut() {
            if t % 2 == 0 {
                let lsnap: Vec<f32> = (0..n).map(|i| l[i] as f32).collect();
                buf.push((lsnap, mopt[1], lbar[0], lbar[1], abar2));
            }
        }
        prev_act = Some(act.clone()); prev_c = Some(cdec.clone());
    }
    Out { m2: opt_tail[1] / 50.0, m1: opt_tail[0] / 50.0,
          l2: l_tail[1] / 50.0, l1: l_tail[0] / 50.0, dwell2 }
}

fn cell_stats(p: &P, gate: Gate, q1: [f64; 2], q2: [f64; 2], reps: usize, seed0: u64)
              -> (f64, f64, f64, f64, f64, f64, f64, f64) {
    // returns mean m2, var m2, mean L2, var L2, P_defwrong, P_persist(L2<.3),
    // mean dwell, var dwell
    let nthreads = 2;
    let chunk = (reps + nthreads - 1) / nthreads;
    let mut handles = vec![];
    for th in 0..nthreads {
        let p = *p; let lo_r = th * chunk; let hi_r = ((th + 1) * chunk).min(reps);
        handles.push(thread::spawn(move || {
            let mut v = vec![];
            for r in lo_r..hi_r {
                let o = run(&p, gate, q1, q2, seed0.wrapping_add(r as u64 * 7919), None);
                v.push((o.m2, o.l2, o.dwell2));
            }
            v
        }));
    }
    let mut all = vec![];
    for h in handles { all.extend(h.join().unwrap()); }
    let nr = all.len() as f64;
    let mm2 = all.iter().map(|x| x.0).sum::<f64>() / nr;
    let vm2 = all.iter().map(|x| (x.0 - mm2).powi(2)).sum::<f64>() / (nr - 1.0);
    let ml2 = all.iter().map(|x| x.1).sum::<f64>() / nr;
    let vl2 = all.iter().map(|x| (x.1 - ml2).powi(2)).sum::<f64>() / (nr - 1.0);
    let pdw = all.iter().filter(|x| x.0 < 0.3 && x.1 < 0.3).count() as f64 / nr;
    let pper = all.iter().filter(|x| x.1 < 0.3).count() as f64 / nr;
    let dw = all.iter().map(|x| x.2).sum::<f64>() / nr;
    let vdw = all.iter().map(|x| (x.2 - dw).powi(2)).sum::<f64>() / (nr - 1.0);
    (mm2, vm2, ml2, vl2, pdw, pper, dw, vdw)
}

// ================= I021: M-community blocks on meta-/complex networks ============
// Exposure matrix W: row c = w_in on itself + (1-w_in) over meta-neighbours
// (equal split; population-weighted over all others for broadcast). Exact
// block-uniform aggregation licenses community-level fields at every M.

fn build_meta(m: usize, geom: &str, sizes: &[usize], w_in: f64, rng: &mut Rng)
              -> Vec<Vec<(usize, f64)>> {
    let mut rows: Vec<Vec<(usize, f64)>> = vec![vec![]; m];
    let out = 1.0 - w_in;
    if m == 1 { rows[0].push((0, 1.0)); return rows; }
    if m == 2 {
        for c in 0..2 { rows[c].push((c, w_in)); rows[c].push((1 - c, out)); }
        return rows;
    }
    let mut adj: Vec<Vec<usize>> = vec![vec![]; m];
    match geom {
        "broadcast" => {
            let tot: f64 = sizes.iter().sum::<usize>() as f64;
            for c in 0..m {
                rows[c].push((c, w_in));
                let rest = tot - sizes[c] as f64;
                for d in 0..m { if d != c {
                    rows[c].push((d, out * sizes[d] as f64 / rest)); } }
            }
            return rows;
        }
        "ba" => {
            // Barabasi-Albert m=2 over communities, seeded start triangle
            let mut targets: Vec<usize> = vec![0, 1, 2, 0, 1, 2];
            adj[0].push(1); adj[1].push(0); adj[1].push(2);
            adj[2].push(1); adj[2].push(0); adj[0].push(2);
            for v in 3..m {
                let mut chosen: Vec<usize> = vec![];
                while chosen.len() < 2 {
                    let t = targets[(rng.f64() * targets.len() as f64) as usize
                                    % targets.len()];
                    if t != v && !chosen.contains(&t) { chosen.push(t); }
                }
                for &t in &chosen {
                    adj[v].push(t); adj[t].push(v);
                    targets.push(v); targets.push(t);
                }
            }
        }
        _ => {
            // ring degree 4, then WS rewiring with prob p (geom "ring" => p=0)
            let p = match geom { "ws001" => 0.01, "ws01" => 0.1, "ws1" => 1.0,
                                 _ => 0.0 };
            let mut edges: Vec<(usize, usize)> = vec![];
            for c in 0..m { for k in [1usize, 2] {
                edges.push((c, (c + k) % m)); } }
            for e in edges.iter_mut() {
                if p > 0.0 && rng.f64() < p {
                    let mut t = (rng.f64() * m as f64) as usize % m;
                    let mut guard = 0;
                    while (t == e.0 || t == e.1) && guard < 50 {
                        t = (rng.f64() * m as f64) as usize % m; guard += 1; }
                    e.1 = t;
                }
            }
            for (a, b) in edges { if a != b { adj[a].push(b); adj[b].push(a); } }
        }
    }
    for c in 0..m {
        adj[c].sort(); adj[c].dedup();
        rows[c].push((c, w_in));
        if adj[c].is_empty() { rows[c] = vec![(c, 1.0)]; continue; }
        let share = out / adj[c].len() as f64;
        for &d in &adj[c] { rows[c].push((d, share)); }
    }
    rows
}

struct MOut { m: Vec<f64>, l: Vec<f64> }

fn run_mblock(p: &P, sizes: &[usize], rows: &[Vec<(usize, f64)>], losing: &[bool],
              seed: u64, global_ref: bool) -> MOut {
    let m = sizes.len(); let n: usize = sizes.iter().sum();
    let mut comm = vec![0usize; n]; let mut off = vec![0usize; m + 1];
    { let mut k = 0; for c in 0..m { off[c] = k; k += sizes[c]; } off[m] = n; }
    for c in 0..m { for i in off[c]..off[c + 1] { comm[i] = c; } }
    let mut rng = Rng::new(seed);
    let mut q = vec![[0.0f64; 2]; n];
    for i in 0..n { q[i] = if losing[comm[i]] { [0.38, 0.62] } else { [0.62, 0.38] }; }
    let mut l = vec![p.l0; n]; let mut a = vec![p.a0; n];
    let (mut pa, mut pc): (Option<Vec<u8>>, Option<Vec<f64>>) = (None, None);
    let mut act = vec![0u8; n]; let mut cdec = vec![0.0f64; n]; let mut rew = vec![0.0f64; n];
    let mut mt = vec![0.0f64; m]; let mut lt = vec![0.0f64; m];
    let tail = p.t - 50;
    for t in 0..p.t {
        // community aggregates from t-1
        let mut phi = vec![[0.0f64; 2]; m];
        if let (Some(ca), Some(cc)) = (&pa, &pc) {
            for i in 0..n { phi[comm[i]][ca[i] as usize] += cc[i]; }
            for c in 0..m { for ar in 0..2 { phi[c][ar] /= sizes[c] as f64; } }
        }
        let mut s = vec![[0.0f64; 2]; m];
        for c in 0..m { for &(d, w) in &rows[c] { for ar in 0..2 {
            s[c][ar] += w * phi[d][ar]; } } }
        // choices + rewards
        for i in 0..n {
            let c = comm[i];
            let delta = (q[i][0] - q[i][1]) + p.lam * (s[c][0] - s[c][1]);
            let p1 = sigmoid(p.beta2 * delta);
            act[i] = if rng.f64() < p1 { 0 } else { 1 };
            cdec[i] = (2.0 * p1 - 1.0).abs();
            rew[i] = if rng.f64() < p.mu[act[i] as usize] { 1.0 } else { 0.0 };
        }
        // outcome aggregates
        let mut rbar = vec![0.0f64; m];
        let mut wm = vec![[0.0f64; 2]; m]; let mut wr = vec![[0.0f64; 2]; m];
        for i in 0..n {
            let c = comm[i]; let ar = act[i] as usize;
            rbar[c] += rew[i]; wm[c][ar] += cdec[i]; wr[c][ar] += cdec[i] * rew[i];
        }
        let mut pop = 0.0;
        for c in 0..m {
            pop += rbar[c];
            rbar[c] /= sizes[c] as f64;
            for ar in 0..2 { wm[c][ar] /= sizes[c] as f64; wr[c][ar] /= sizes[c] as f64; }
        }
        pop /= n as f64;
        let mut expo = vec![[0.0f64; 2]; m]; let mut erew = vec![[0.0f64; 2]; m];
        let mut rref = vec![0.0f64; m];
        for c in 0..m { for &(d, w) in &rows[c] {
            for ar in 0..2 { expo[c][ar] += w * wm[d][ar]; erew[c][ar] += w * wr[d][ar]; }
            rref[c] += w * rbar[d];
        } }
        // updates (synchronous, pre-update states)
        for i in 0..n {
            let c = comm[i]; let g = l[i];
            let ar = act[i] as usize;
            let delta = rew[i] - q[i][ar];
            let soc0 = erew[c][0] - expo[c][0] * q[i][0];
            let soc1 = erew[c][1] - expo[c][1] * q[i][1];
            q[i][ar] += p.alpha * g * delta;
            q[i][0] = clip01(q[i][0] + p.eta * g * soc0);
            q[i][1] = clip01(q[i][1] + p.eta * g * soc1);
            let z = a[i] - rew[i];
            let df = p.phim * z.max(0.0) + p.phip * (-z).max(0.0);
            l[i] = clip01(l[i] - p.nu_f * (df - p.tau_f).max(0.0)
                          + p.nu_r * if df <= p.tau_f { 1.0 } else { 0.0 });
            let rr = if global_ref { pop } else { rref[c] };
            a[i] = clip01((1.0 - p.rho) * a[i]
                          + p.rho * ((1.0 - p.chi) * rew[i] + p.chi * rr));
        }
        if t >= tail {
            for i in 0..n {
                let c = comm[i];
                if act[i] == 0 { mt[c] += 1.0; }
                lt[c] += l[i];
            }
        }
        pa = Some(act.clone()); pc = Some(cdec.clone());
    }
    for c in 0..m { mt[c] /= 50.0 * sizes[c] as f64; lt[c] /= 50.0 * sizes[c] as f64; }
    MOut { m: mt, l: lt }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mode = args.get(1).map(|s| s.as_str()).unwrap_or("validate");
    let wrong = ([0.62, 0.38], [0.38, 0.62]);
    match mode {
        "validate" => {
            let p = P { a0: 0.8, lam: 0.7, rho: 0.002, ..P::default() };
            let (m2, _v, l2, _vl, pdw, _pp, _d, _vd) = cell_stats(&p, Gate::Diss, wrong.0, wrong.1, 300, 41000);
            println!("CV1 trap_on  m2={m2:.4} L2={l2:.4} P_dw={pdw:.4}");
            let (m2o, _, _, _, _, _, _, _) = cell_stats(&p, Gate::Off, wrong.0, wrong.1, 300, 41000);
            println!("CV2 trap_off m2={m2o:.4}");
            let pk = P { a0: 0.8, lam: 0.7, rho: 0.002, gamma: 0.3, nu_r: 0.01, ..P::default() };
            let (m2k, _, l2k, _, _, _, _, _) = cell_stats(&pk, Gate::Diss, wrong.0, wrong.1, 200, 42000);
            println!("CV3 decouple m2={m2k:.4} L2={l2k:.4}");
            let pc = P { mu: [0.7, 0.3], a0: 0.5, lam: 0.7, rho: 0.002, chi: 1.0,
                         gamma: 0.0, global_cmp: false, ..P::default() };
            let (m2c, _, l2c, _, _, _, _, _) = cell_stats(&pc, Gate::Diss, [0.72, 0.28], [0.28, 0.72], 200, 43000);
            println!("CV4 credulous m2={m2c:.4} L2={l2c:.4}");
            let pr = P { n: 2, t: 20000, gamma: 0.0, chi: 0.0, rho: 0.01,
                         lam: 0.0, eta: 0.0, a0: 0.6, mu: [0.4, 0.4], ..P::default() };
            let (_, _, l2r, _, _, _, _, _) = cell_stats(&pr, Gate::Diss, [0.0, 1.0], [0.0, 1.0], 20, 44000);
            println!("CV5 resign  L_tail={l2r:.4}");
        }
        "pt1" => {
            let f = File::create("out/pt1.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "a0,lam,m2,var_m2,l2,p_dw").unwrap();
            for ia in 0..26 {
                let a0 = 0.45 + 0.45 * ia as f64 / 25.0;
                for il in 0..26 {
                    let lam = 0.40 + 0.45 * il as f64 / 25.0;
                    let p = P { a0, lam, rho: 0.002, ..P::default() };
                    let (m2, v, l2, _vl, pdw, _, _, _) = cell_stats(&p, Gate::Diss, wrong.0, wrong.1,
                        40, 31000 + (ia * 26 + il) as u64 * 1000);
                    writeln!(w, "{a0:.4},{lam:.4},{m2:.5},{v:.6},{l2:.5},{pdw:.4}").unwrap();
                }
                eprintln!("pt1 row {ia} done");
            }
        }
        "cuts" => {
            let f = File::create("out/cuts.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "lam,a0,m2,var_m2,p_dw").unwrap();
            for &lam in &[0.55, 0.65, 0.75] {
                for ia in 0..41 {
                    let a0 = 0.45 + 0.45 * ia as f64 / 40.0;
                    let p = P { a0, lam, rho: 0.002, ..P::default() };
                    let (m2, v, _l2, _vl, pdw, _, _, _) = cell_stats(&p, Gate::Diss, wrong.0, wrong.1,
                        60, 32000 + ((lam * 100.0) as u64) * 100 + ia as u64 * 7);
                    writeln!(w, "{lam:.2},{a0:.4},{m2:.5},{v:.6},{pdw:.4}").unwrap();
                }
                eprintln!("cuts lam={lam} done");
            }
        }
        "pt2" => {
            let f = File::create("out/pt2.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "rho,chi,p_persist,dwell,m2,var_dwell").unwrap();
            for ir in 0..26 {
                let rho = 10f64.powf(-3.0 + (1.699) * ir as f64 / 25.0); // 1e-3 .. 5e-2
                for ic in 0..26 {
                    let chi = 0.9 * ic as f64 / 25.0;
                    let p = P { a0: 0.8, lam: 0.7, rho, chi, ..P::default() };
                    let (m2, _v, _l2, _vl, _pdw, pper, dw, vdw) = cell_stats(&p, Gate::Diss, wrong.0, wrong.1,
                        40, 33000 + (ir * 26 + ic) as u64 * 1000);
                    writeln!(w, "{rho:.6},{chi:.4},{pper:.4},{dw:.2},{m2:.5},{vdw:.3}").unwrap();
                }
                eprintln!("pt2 row {ir} done");
            }
        }
        "pt3" => {
            let f = File::create("out/pt3.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "gamma,agent,variant,m2,gate,var_m2,var_gate").unwrap();
            for &(vname, nur) in &[("knife", 0.01), ("generic", 0.0125)] {
                for ig in 0..26 {
                    let gamma = 0.5 * ig as f64 / 25.0;
                    for (aname, gate) in [("diss", Gate::Diss), ("bayes", Gate::Bayes)] {
                        let p = P { a0: 0.8, lam: 0.7, rho: 0.002, gamma, nu_r: nur,
                                    ..P::default() };
                        let (m2, vm2, l2, vl2, _pdw, _pp, _d, _vd) = cell_stats(&p, gate, wrong.0, wrong.1,
                            60, 34000 + ig as u64 * 503 + if gate == Gate::Diss {0} else {77});
                        writeln!(w, "{gamma:.4},{aname},{vname},{m2:.5},{l2:.5},{vm2:.6},{vl2:.6}").unwrap();
                    }
                }
                eprintln!("pt3 {vname} done");
            }
        }
        "pt4" => {
            let f = File::create("out/pt4.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "a0,gamma,f_dw,f_cred,f_ci,f_leg,f_mixed,modal").unwrap();
            for ia in 0..26 {
                let a0 = 0.45 + 0.45 * ia as f64 / 25.0;
                for ig in 0..26 {
                    let gamma = 0.5 * ig as f64 / 25.0;
                    let p = P { a0, lam: 0.7, rho: 0.002, gamma, ..P::default() };
                    let reps = 40usize;
                    let nthreads = 2; let chunk = (reps + 1) / nthreads;
                    let mut handles = vec![];
                    for th in 0..nthreads {
                        let p = p; let lo_r = th * chunk; let hi_r = ((th + 1) * chunk).min(reps);
                        let seed0 = 37000u64 + (ia * 26 + ig) as u64 * 1000;
                        handles.push(thread::spawn(move || {
                            let mut v = vec![];
                            for r in lo_r..hi_r {
                                let o = run(&p, Gate::Diss, [0.62, 0.38], [0.38, 0.62],
                                            seed0.wrapping_add(r as u64 * 7919), None);
                                v.push((o.m2, o.l2));
                            }
                            v
                        }));
                    }
                    let mut all = vec![];
                    for h in handles { all.extend(h.join().unwrap()); }
                    let nr = all.len() as f64;
                    let fdw = all.iter().filter(|x| x.0 < 0.3 && x.1 < 0.3).count() as f64 / nr;
                    let fcr = all.iter().filter(|x| x.0 < 0.3 && x.1 > 0.5).count() as f64 / nr;
                    let fci = all.iter().filter(|x| x.0 > 0.7 && x.1 < 0.3).count() as f64 / nr;
                    let fle = all.iter().filter(|x| x.0 > 0.7 && x.1 > 0.5).count() as f64 / nr;
                    let fmx = 1.0 - fdw - fcr - fci - fle;
                    let fr = [fdw, fcr, fci, fle, fmx];
                    let names = ["dw", "cred", "ci", "leg", "mixed"];
                    let mi = (0..5).max_by(|&a, &b| fr[a].partial_cmp(&fr[b]).unwrap()).unwrap();
                    writeln!(w, "{a0:.4},{gamma:.4},{fdw:.4},{fcr:.4},{fci:.4},{fle:.4},{fmx:.4},{}",
                             names[mi]).unwrap();
                }
                eprintln!("pt4 row {ia} done");
            }
        }
        "traj" => {
            let p = P { a0: 0.8, lam: 0.7, rho: 0.002, ..P::default() };
            // raster: one gate-on run
            let mut buf: Vec<(Vec<f32>, f64, f64, f64, f64)> = vec![];
            let _ = run(&p, Gate::Diss, wrong.0, wrong.1, 35001, Some(&mut buf));
            let f = File::create("out/raster.csv").unwrap();
            let mut w = BufWriter::new(f);
            for (ti, (ls, _, _, _, _)) in buf.iter().enumerate() {
                let row: Vec<String> = ls.iter().map(|x| format!("{x:.3}")).collect();
                writeln!(w, "{},{}", ti * 2, row.join(",")).unwrap();
            }
            // spaghetti: m2(t) and Lbar(t) for 60 on + 60 off
            let f2 = File::create("out/spaghetti.csv").unwrap();
            let mut w2 = BufWriter::new(f2);
            writeln!(w2, "rep,gate,t,m2,l1,l2").unwrap();
            for gate_on in [true, false] {
                for rep in 0..60u64 {
                    let mut b2: Vec<(Vec<f32>, f64, f64, f64, f64)> = vec![];
                    let g = if gate_on { Gate::Diss } else { Gate::Off };
                    let _ = run(&p, g, wrong.0, wrong.1, 36000 + rep * 101, Some(&mut b2));
                    for (ti, (_, m2t, l1t, l2t, _)) in b2.iter().enumerate() {
                        if ti % 5 == 0 {
                            writeln!(w2, "{rep},{},{} ,{m2t:.4},{l1t:.4},{l2t:.4}",
                                     if gate_on {"on"} else {"off"}, ti * 2).unwrap();
                        }
                    }
                }
                eprintln!("traj gate_on={gate_on} done");
            }
        }
        "race" => {
            // frozen design 00_freeze_I008.yaml (+ addendum 2: modal-seed rule)
            let f = File::create("out/race.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "rho,t,m2,l2,a2").unwrap();
            // rho=.002: first seed in 38001,38011,... whose run is defensive-wrong
            let p_slow = P { a0: 0.8, lam: 0.7, rho: 0.002, ..P::default() };
            let mut chosen = 0u64; let mut skipped = 0;
            for k in 0..50u64 {
                let seed = 38001 + 10 * k;
                let o = run(&p_slow, Gate::Diss, wrong.0, wrong.1, seed, None);
                if o.m2 < 0.3 && o.l2 < 0.3 { chosen = seed; break; }
                skipped += 1;
            }
            eprintln!("race slow: chosen seed {chosen}, skipped {skipped}");
            for (rho, seed) in [(0.002f64, chosen), (0.02f64, 38002u64)] {
                let p = P { a0: 0.8, lam: 0.7, rho, ..P::default() };
                let mut buf: Vec<(Vec<f32>, f64, f64, f64, f64)> = vec![];
                let _ = run(&p, Gate::Diss, wrong.0, wrong.1, seed, Some(&mut buf));
                for (ti, (_, m2t, _, l2t, a2t)) in buf.iter().enumerate() {
                    writeln!(w, "{rho},{},{m2t:.4},{l2t:.4},{a2t:.4}", ti * 2).unwrap();
                }
                eprintln!("race rho={rho} seed={seed} done");
            }
        }
        "pt3b" => {
            // frozen I012: group-contingent rival over the pt3 Gamma grid
            let f = File::create("out/pt3b.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "gamma,agent,variant,m2,gate,var_m2,var_gate").unwrap();
            for ig in 0..26 {
                let gamma = 0.5 * ig as f64 / 25.0;
                let p = P { a0: 0.8, lam: 0.7, rho: 0.002, gamma, nu_r: 0.01, ..P::default() };
                let (m2, vm2, l2, vl2, _pdw, _pp, _d, _vd) = cell_stats(&p, Gate::RigUs,
                    wrong.0, wrong.1, 60, 34000 + ig as u64 * 503 + 154);
                writeln!(w, "{gamma:.4},rigus,knife,{m2:.5},{l2:.5},{vm2:.6},{vl2:.6}").unwrap();
            }
            eprintln!("pt3b done");
        }
        "nlvar" => {
            // frozen I012: non-lexicographic variant at confirmatory + neutral cells
            let p = P { a0: 0.8, lam: 0.7, rho: 0.002, ..P::default() };
            let (m2, _v, l2, _vl, pdw, _pp, _d, _vd) = cell_stats(&p, Gate::DissNL, wrong.0, wrong.1, 300, 45000);
            let (m2o, _, _, _, _, _, _, _) = cell_stats(&p, Gate::Off, wrong.0, wrong.1, 300, 45000);
            println!("NLVAR trap: m2={m2:.4} L2={l2:.4} P_dw={pdw:.4} m2_off={m2o:.4} restore={:.4}", m2o - m2);
            let pn = P { a0: 0.5, lam: 0.7, rho: 0.002, ..P::default() };
            let (m2n, _, _, _, pdwn, _, _, _) = cell_stats(&pn, Gate::DissNL, wrong.0, wrong.1, 300, 45500);
            println!("NLVAR neutral: m2={m2n:.4} P_dw={pdwn:.4}");
        }
        "fss" => {
            // frozen I012: finite-size scaling at the lambda=.75 cut
            let f = File::create("out/fss.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "n,a0,m2,var_m2,p_dw").unwrap();
            for (inx, nn) in [50usize, 100, 200, 400, 800, 1600].iter().enumerate() {
                for ia in 0..15 {
                    let a0 = 0.58 + 0.14 * ia as f64 / 14.0;
                    let p = P { a0, lam: 0.75, rho: 0.002, n: *nn, ..P::default() };
                    let (m2, vm2, _l2, _vl, pdw, _pp, _d, _vd) = cell_stats(&p, Gate::Diss,
                        wrong.0, wrong.1, 60, 46000 + inx as u64 * 10000 + ia as u64 * 100);
                    writeln!(w, "{nn},{a0:.4},{m2:.5},{vm2:.6},{pdw:.4}").unwrap();
                }
                eprintln!("fss N={nn} done");
            }
        }
        "tsweep" => {
            // frozen I012: horizon sweep of the rho boundary at chi=.432
            let f = File::create("out/tsweep.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "t,rho,p_persist,dwell").unwrap();
            for (it, tt) in [600usize, 2400, 9600].iter().enumerate() {
                for ir in 0..26 {
                    let rho = 10f64.powf(-3.0 + 1.699 * ir as f64 / 25.0);
                    let p = P { a0: 0.8, lam: 0.7, rho, chi: 0.432, t: *tt, ..P::default() };
                    let (_m2, _v, _l2, _vl, _pdw, pper, dw, _vd) = cell_stats(&p, Gate::Diss,
                        wrong.0, wrong.1, 40, 47000 + it as u64 * 10000 + ir as u64 * 1000);
                    writeln!(w, "{tt},{rho:.6},{pper:.4},{dw:.2}").unwrap();
                }
                eprintln!("tsweep T={tt} done");
            }
        }
        "sens" => {
            // frozen I012: classification-threshold sensitivity on the pt1 grid seeds
            let f = File::create("out/sens.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "thr,a0,lam,p_dw").unwrap();
            for (ith, thr) in [0.25f64, 0.30, 0.35].iter().enumerate() {
                for ia in 0..26 {
                    let a0 = 0.45 + 0.45 * ia as f64 / 25.0;
                    for il in 0..26 {
                        let lam = 0.40 + 0.45 * il as f64 / 25.0;
                        let p = P { a0, lam, rho: 0.002, ..P::default() };
                        let reps = 40usize;
                        let mut cnt = 0usize;
                        for r in 0..reps {
                            let o = run(&p, Gate::Diss, [0.62, 0.38], [0.38, 0.62],
                                        (31000 + (ia * 26 + il) as u64 * 1000)
                                            .wrapping_add(r as u64 * 7919), None);
                            if o.m2 < *thr && o.l2 < *thr { cnt += 1; }
                        }
                        writeln!(w, "{thr},{a0:.4},{lam:.4},{:.4}", cnt as f64 / reps as f64).unwrap();
                    }
                }
                eprintln!("sens thr={thr} ({ith}) done");
            }
        }
        "mfband" => {
            // frozen I012: 20-run ABM bands at the race cells for the MF comparison
            let f = File::create("out/mfband.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "rho,t,m2_m,m2_s,l2_m,l2_s,a2_m,a2_s").unwrap();
            for rho in [0.002f64, 0.02] {
                let p = P { a0: 0.8, lam: 0.7, rho, ..P::default() };
                let mut all: Vec<Vec<(f64, f64, f64)>> = vec![];
                for r in 0..20u64 {
                    let mut buf: Vec<(Vec<f32>, f64, f64, f64, f64)> = vec![];
                    let _ = run(&p, Gate::Diss, wrong.0, wrong.1, 38100 + r * 13, Some(&mut buf));
                    all.push(buf.iter().map(|x| (x.1, x.3, x.4)).collect());
                }
                let nt = all[0].len();
                for ti in 0..nt {
                    let n = all.len() as f64;
                    let (mut mm, mut ml, mut ma) = (0.0, 0.0, 0.0);
                    for a in &all { mm += a[ti].0; ml += a[ti].1; ma += a[ti].2; }
                    mm /= n; ml /= n; ma /= n;
                    let (mut sm, mut sl, mut sa) = (0.0, 0.0, 0.0);
                    for a in &all { sm += (a[ti].0 - mm).powi(2); sl += (a[ti].1 - ml).powi(2); sa += (a[ti].2 - ma).powi(2); }
                    writeln!(w, "{rho},{},{mm:.4},{:.4},{ml:.4},{:.4},{ma:.4},{:.4}",
                             ti * 2, (sm / (n - 1.0)).sqrt(), (sl / (n - 1.0)).sqrt(),
                             (sa / (n - 1.0)).sqrt()).unwrap();
                }
                eprintln!("mfband rho={rho} done");
            }
        }
        // ---------------- I014 referee-repair modes (frozen 00_freeze_I014.yaml) ----
        "absorb" => {
            // Direct rho_c test: single-agent race, absorption = L hits 0 before A
            // crosses A*(mu2). mu2=0.4 fixed-rate, A0=0.8, chi=0, defaults otherwise.
            let f = File::create("out/absorb.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "rho,p_absorb,n_absorb,n_escape,n_censor,reps").unwrap();
            let astar = (0.3 + (0.0125 / 0.05) * 0.4 / 0.6) / 1.0; // A*(0.4) = 7/15
            for ir in 0..15 {
                let rho = 10f64.powf((0.002f64).log10()
                          + ((0.02f64).log10() - (0.002f64).log10()) * ir as f64 / 14.0);
                let (mut nab, mut nes, mut ncen) = (0u32, 0u32, 0u32);
                let reps = 400u64;
                for r in 0..reps {
                    let mut rng = Rng::new(48000 + ir as u64 * 500 + r);
                    let (mut lv, mut av) = (1.0f64, 0.8f64);
                    let mut outcome = 2u8; // 0 absorb, 1 escape, 2 censor
                    for _t in 0..5000 {
                        let rew = if rng.f64() < 0.4 { 1.0 } else { 0.0 };
                        let z = av - rew;
                        let df = 1.0 * z.max(0.0) + 0.25 * (-z).max(0.0);
                        lv = clip01(lv - 0.05 * (df - 0.3).max(0.0)
                                    + 0.0125 * if df <= 0.3 { 1.0 } else { 0.0 });
                        av = clip01((1.0 - rho) * av + rho * rew);
                        if lv <= 1e-12 { outcome = 0; break; }
                        if av <= astar { outcome = 1; break; }
                    }
                    match outcome { 0 => nab += 1, 1 => nes += 1, _ => ncen += 1 }
                }
                let pa = nab as f64 / reps as f64;
                writeln!(w, "{rho:.6},{pa:.4},{nab},{nes},{ncen},{reps}").unwrap();
                eprintln!("absorb rho={rho:.5} P={pa:.3}");
            }
        }
        "fieldform" => {
            // Credibility-field form robustness at the confirmatory cell
            let f = File::create("out/fieldform.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "variant,m2,l2,p_dw,reps").unwrap();
            let base = P { a0: 0.8, lam: 0.7, rho: 0.002, ..P::default() };
            let cases: [(&str, P); 3] = [
                ("unweighted", P { field_unweighted: true, ..base }),
                ("eta0",       P { eta: 0.0, ..base }),
                ("both",       P { field_unweighted: true, eta: 0.0, ..base })];
            let seeds = [49000u64, 49500, 49750];
            for (k, (name, pp)) in cases.iter().enumerate() {
                let (m2, _v, l2, _vl, pdw, _, _, _) =
                    cell_stats(pp, Gate::Diss, wrong.0, wrong.1, 60, seeds[k]);
                writeln!(w, "{name},{m2:.5},{l2:.5},{pdw:.4},60").unwrap();
                eprintln!("fieldform {name} P_dw={pdw:.3}");
            }
        }
        "topo" => {
            // Structural robustness at the confirmatory cell
            let f = File::create("out/topo.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "variant,m2,l2,p_dw,reps").unwrap();
            let base = P { a0: 0.8, lam: 0.7, rho: 0.002, ..P::default() };
            let cases: [(&str, P); 4] = [
                ("losing_small_60",  P { n1: 140, ..base }),
                ("losing_large_140", P { n1: 60,  ..base }),
                ("gamma_het",        P { gamma_het: true, ..base }),
                ("paybias",          P { field_paybias: true, ..base })];
            let seeds = [50000u64, 50200, 50400, 50600];
            for (k, (name, pp)) in cases.iter().enumerate() {
                let (m2, _v, l2, _vl, pdw, _, _, _) =
                    cell_stats(pp, Gate::Diss, wrong.0, wrong.1, 60, seeds[k]);
                writeln!(w, "{name},{m2:.5},{l2:.5},{pdw:.4},60").unwrap();
                eprintln!("topo {name} P_dw={pdw:.3}");
            }
            // transparency check for the payoff-biased field at Gamma = 0.137
            let pt = P { a0: 0.8, lam: 0.7, rho: 0.002, gamma: 0.137,
                         field_paybias: true, ..P::default() };
            let (m2t, _v, l2t, _vl, pdwt, _, _, _) =
                cell_stats(&pt, Gate::Diss, wrong.0, wrong.1, 60, 50800);
            writeln!(w, "paybias_gamma137,{m2t:.5},{l2t:.5},{pdwt:.4},60").unwrap();
            eprintln!("topo paybias@0.137 m2={m2t:.3}");
        }
        "nfsweep" => {
            // knife-edge neighbourhood: P_dw vs nuR/nuF at the confirmatory cell
            let f = File::create("out/nfsweep.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "ratio,astar06,m2,p_dw,reps").unwrap();
            for (ir, ratio) in [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5].iter().enumerate() {
                let p = P { a0: 0.8, lam: 0.7, rho: 0.002, nu_r: 0.05 * ratio, ..P::default() };
                let astar06 = 0.3 + ratio * 0.6 / 0.4; // A*(0.6) at this ratio, phi-=1
                let (m2, _v, _l2, _vl, pdw, _, _, _) = cell_stats(&p, Gate::Diss,
                    wrong.0, wrong.1, 60, 51000 + ir as u64 * 100);
                writeln!(w, "{ratio},{astar06:.4},{m2:.5},{pdw:.4},60").unwrap();
                eprintln!("nfsweep ratio={ratio} P_dw={pdw:.3}");
            }
        }
        "corner" => {
            // windfall-delegitimation corner: phi+ above the exclusion bound
            let f = File::create("out/corner.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "t,l_mean,a_mean").unwrap();
            let reps = 20u64; let t_len = 600usize;
            let mut lsum = vec![0.0f64; t_len]; let mut asum = vec![0.0f64; t_len];
            for r in 0..reps {
                let mut rng = Rng::new(52000 + r);
                let (mut lv, mut av) = (1.0f64, 0.3f64);
                for t in 0..t_len {
                    let rew = if rng.f64() < 0.6 { 1.0 } else { 0.0 };
                    let z = av - rew;
                    let df = 1.0 * z.max(0.0) + 0.5 * (-z).max(0.0); // phi+ = 0.5 > bound
                    lv = clip01(lv - 0.05 * (df - 0.3).max(0.0)
                                + 0.0125 * if df <= 0.3 { 1.0 } else { 0.0 });
                    av = clip01((1.0 - 0.002) * av + 0.002 * rew);
                    lsum[t] += lv; asum[t] += av;
                }
            }
            for t in 0..t_len {
                writeln!(w, "{t},{:.5},{:.5}", lsum[t] / reps as f64, asum[t] / reps as f64).unwrap();
            }
            eprintln!("corner done: terminal L={:.3}", lsum[t_len-1] / reps as f64);
        }
        "fss2" => {
            // second finite-size cut: persistence front in chi at rho=0.005
            let f = File::create("out/fss2.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "n,chi,p_persist,var_m2").unwrap();
            for (inx, nn) in [50usize, 100, 200, 400, 800].iter().enumerate() {
                for ic in 0..11 {
                    let chi = ic as f64 / 10.0;
                    let p = P { a0: 0.8, lam: 0.7, rho: 0.005, chi, n: *nn, ..P::default() };
                    let (_m2, vm2, _l2, _vl, _pdw, pper, _, _) = cell_stats(&p, Gate::Diss,
                        wrong.0, wrong.1, 60, 53000 + inx as u64 * 10000 + ic as u64 * 100);
                    writeln!(w, "{nn},{chi:.2},{pper:.4},{vm2:.6}").unwrap();
                }
                eprintln!("fss2 N={nn} done");
            }
        }
        "race3" => {
            // SI panel: first three seeds of the pre-declared race sequence,
            // regardless of outcome (38001 escape-drawn, 38011, 38021 modal)
            let f = File::create("out/race3.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "seed,t,m2,l2,a2").unwrap();
            let p = P { a0: 0.8, lam: 0.7, rho: 0.002, ..P::default() };
            for seed in [38001u64, 38011, 38021] {
                let mut buf: Vec<(Vec<f32>, f64, f64, f64, f64)> = vec![];
                let _ = run(&p, Gate::Diss, wrong.0, wrong.1, seed, Some(&mut buf));
                for (ti, x) in buf.iter().enumerate() {
                    writeln!(w, "{seed},{},{:.4},{:.4},{:.4}", ti * 2, x.1, x.3, x.4).unwrap();
                }
                eprintln!("race3 seed {seed} done");
            }
        }
        "morris" => {
            // Morris elementary-effects screening on P_dw (frozen ranges, k=12, r=30)
            let f = File::create("out/morris.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "traj,step,param,ee").unwrap();
            let names = ["a0","lam","log10rho","chi","gamma","nuF","nuRratio",
                         "tauF","phip","alpha","eta","kbeta"];
            let lo = [0.5, 0.3, -3.3, 0.0, 0.0, 0.02, 0.1, 0.2, 0.1, 0.1, 0.1, 8.0];
            let hi = [0.9, 0.8, -2.0, 0.8, 0.3, 0.10, 0.5, 0.4, 0.4, 0.3, 0.3, 16.0];
            let k = 12usize; let delta = 2.0 / 3.0;
            let eval = |u: &[f64], seed: u64| -> f64 {
                let x: Vec<f64> = (0..k).map(|j| lo[j] + u[j] * (hi[j] - lo[j])).collect();
                let p = P { a0: x[0], lam: x[1], rho: 10f64.powf(x[2]), chi: x[3],
                            gamma: x[4], nu_f: x[5], nu_r: x[5] * x[6], tau_f: x[7],
                            phip: x[8], alpha: x[9], eta: x[10], beta2: x[11],
                            ..P::default() };
                let (_m2, _v, _l2, _vl, pdw, _, _, _) =
                    cell_stats(&p, Gate::Diss, wrong.0, wrong.1, 40, seed);
                pdw
            };
            for traj in 0..30u64 {
                let mut drng = Rng::new(54000 + traj * 1000);
                // base point on the 4-level grid restricted so u + delta <= 1
                let mut u: Vec<f64> = (0..k).map(|_| {
                    if drng.f64() < 0.5 { 0.0 } else { 1.0 / 3.0 } }).collect();
                // random permutation (Fisher-Yates) and random direction per param
                let mut order: Vec<usize> = (0..k).collect();
                for j in (1..k).rev() {
                    let m = (drng.f64() * (j + 1) as f64) as usize;
                    order.swap(j, m.min(j));
                }
                let dirs: Vec<f64> = (0..k).map(|_| {
                    if drng.f64() < 0.5 { delta } else { -delta } }).collect();
                // make each step feasible: start low when stepping up, high when down
                for j in 0..k { if dirs[j] < 0.0 { u[j] += delta; } }
                let mut y_prev = eval(&u, 54000 + traj * 1000 + 40);
                for (step, &j) in order.iter().enumerate() {
                    u[j] += dirs[j];
                    let y = eval(&u, 54000 + traj * 1000 + 40 * (step as u64 + 2));
                    let ee = (y - y_prev) / dirs[j];
                    writeln!(w, "{traj},{step},{},{ee:.5}", names[j]).unwrap();
                    y_prev = y;
                }
                eprintln!("morris traj {traj} done");
            }
        }
        "mnetval" => {
            // I021 validation gate: M=2 blocks through the NEW path must sit in the
            // pre-stated band (P_dw in [.78,.90], |m2-0.166|<=.06) before any battery use
            let p = P { a0: 0.8, lam: 0.7, rho: 0.002, ..P::default() };
            let sizes = vec![100usize, 100]; let losing = vec![false, true];
            let mut dw = 0; let mut msum = 0.0; let reps = 300;
            for r in 0..reps {
                let mut grng = Rng::new(579000 + r);
                let rows = build_meta(2, "ring", &sizes, 0.9, &mut grng);
                let o = run_mblock(&p, &sizes, &rows, &losing, 79000 + r, false);
                if o.m[1] < 0.3 && o.l[1] < 0.3 { dw += 1; }
                msum += o.m[1];
            }
            println!("mnetval m2={:.4} P_dw={:.4} (bands: |m2-.166|<=.06, P in [.78,.90])",
                     msum / reps as f64, dw as f64 / reps as f64);
        }
        "mnet" => {
            // I021 frozen battery (00_freeze_I021.yaml); seeds 80000+cell*1000+run
            let fcell = File::create("out/mnet_cells.csv").unwrap();
            let mut wc = BufWriter::new(fcell);
            writeln!(wc, "cell,m_comms,n_size,geom,place,run,frac_trap,frac_cbi,mean_m,mean_l").unwrap();
            let fcomm = File::create("out/mnet_comm.csv").unwrap();
            let mut wk = BufWriter::new(fcomm);
            writeln!(wk, "cell,run,comm,deg,xexp,m,l,class").unwrap();
            let base = P { a0: 0.8, lam: 0.7, rho: 0.002, ..P::default() };
            // cell table: (id, M, n, geom, place, runs, comm_csv, global_ref)
            let mut cells: Vec<(usize, usize, usize, &str, &str, u64, bool, bool)> = vec![
                (0, 2, 5000, "ring", "clustered", 40, false, false),
                (1, 10, 1000, "ring", "clustered", 40, false, false),
                (2, 100, 100, "ring", "clustered", 40, false, false),
                (3, 1000, 10, "ring", "clustered", 40, false, false),
                (4, 10000, 10, "ring", "clustered", 20, false, false)];
            let mut id = 5;
            for &(mm, nn) in &[(10usize, 1000usize), (100, 100), (1000, 10)] {
                for g in ["ring", "ws001", "ws01", "ws1", "ba", "broadcast"] {
                    for pl in ["clustered", "scattered"] {
                        cells.push((id, mm, nn, g, pl, 40, true, false)); id += 1;
                    }
                }
            }
            let uneq_big_loser = id; cells.push((id, 10, 0, "ring", "uneq_bigloser", 40, false, false)); id += 1;
            let uneq_big_winner = id; cells.push((id, 10, 0, "ring", "uneq_bigwinner", 40, false, false)); id += 1;
            cells.push((id, 100, 100, "broadcast", "clustered", 40, false, true));
            for (cid, mm, nn, geom, place, runs, comm_csv, gref) in cells {
                for r in 0..runs {
                    let (sizes, losing): (Vec<usize>, Vec<bool>) =
                        if cid == uneq_big_loser {
                            (std::iter::once(5500).chain(std::iter::repeat(500).take(9)).collect(),
                             std::iter::once(true).chain(std::iter::repeat(false).take(9)).collect())
                        } else if cid == uneq_big_winner {
                            (std::iter::once(5500).chain(std::iter::repeat(500).take(9)).collect(),
                             std::iter::once(false).chain(std::iter::repeat(true).take(9)).collect())
                        } else {
                            let sz = vec![nn; mm];
                            let lo: Vec<bool> = (0..mm).map(|c| match place {
                                "scattered" => c % 2 == 0,
                                _ => c < mm / 2,
                            }).collect();
                            (sz, lo)
                        };
                    let m = sizes.len();
                    let seed = 80000 + cid as u64 * 1000 + r;
                    let mut grng = Rng::new(seed + 500000);
                    let rows = build_meta(m, geom, &sizes, 0.85, &mut grng);
                    let o = run_mblock(&base, &sizes, &rows, &losing, seed, gref);
                    let (mut nt, mut nc, mut nl) = (0.0, 0.0, 0.0);
                    let (mut sm, mut sl) = (0.0, 0.0);
                    for c in 0..m { if losing[c] {
                        nl += 1.0; sm += o.m[c]; sl += o.l[c];
                        if o.m[c] < 0.3 && o.l[c] < 0.3 { nt += 1.0; }
                        if o.m[c] > 0.7 && o.l[c] < 0.3 { nc += 1.0; }
                    } }
                    writeln!(wc, "{cid},{m},{nn},{geom},{place},{r},{:.4},{:.4},{:.4},{:.4}",
                             nt / nl, nc / nl, sm / nl, sl / nl).unwrap();
                    if comm_csv {
                        for c in 0..m { if losing[c] {
                            let mut xe = 0.0; let mut deg = 0usize;
                            for &(d, w) in &rows[c] {
                                if d != c { deg += 1; if !losing[d] { xe += w; } }
                            }
                            let cl = if o.m[c] < 0.3 && o.l[c] < 0.3 { "trap" }
                                     else if o.m[c] > 0.7 && o.l[c] < 0.3 { "cbi" }
                                     else if o.m[c] > 0.7 && o.l[c] > 0.5 { "legit" }
                                     else { "mixed" };
                            writeln!(wk, "{cid},{r},{c},{deg},{xe:.4},{:.4},{:.4},{cl}",
                                     o.m[c], o.l[c]).unwrap();
                        } }
                    }
                }
                eprintln!("mnet cell {cid} ({mm}x{nn} {geom} {place}) done");
            }
        }
        "mnetT" => {
            // I021 addendum cells (freeze addendum 1)
            let f = File::create("out/mnetT.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "cell,run,frac_trap,frac_cred,frac_cbi,mean_m,mean_l").unwrap();
            // (A) horizon cell: M=100 n=100 ring clustered T=2400
            let pa = P { a0: 0.8, lam: 0.7, rho: 0.002, t: 2400, ..P::default() };
            let sizes = vec![100usize; 100];
            let losing: Vec<bool> = (0..100).map(|c| c < 50).collect();
            for r in 0..20u64 {
                let mut g = Rng::new(585000 + r);
                let rows = build_meta(100, "ring", &sizes, 0.85, &mut g);
                let o = run_mblock(&pa, &sizes, &rows, &losing, 85000 + r, false);
                let (mut nt, mut ncr, mut ncb, mut sm, mut sl, mut nl) = (0.,0.,0.,0.,0.,0.);
                for c in 0..100 { if losing[c] {
                    nl += 1.0; sm += o.m[c]; sl += o.l[c];
                    if o.m[c] < 0.3 && o.l[c] < 0.3 { nt += 1.0; }
                    if o.m[c] < 0.3 && o.l[c] > 0.5 { ncr += 1.0; }
                    if o.m[c] > 0.7 && o.l[c] < 0.3 { ncb += 1.0; }
                } }
                writeln!(w, "A,{r},{:.4},{:.4},{:.4},{:.4},{:.4}", nt/nl, ncr/nl, ncb/nl, sm/nl, sl/nl).unwrap();
            }
            eprintln!("mnetT A done");
            // (B) ladder anchor: M=2 n=5000 w_in=0.90
            let pb = P { a0: 0.8, lam: 0.7, rho: 0.002, ..P::default() };
            let s2 = vec![5000usize, 5000]; let l2 = vec![false, true];
            for r in 0..20u64 {
                let mut g = Rng::new(586000 + r);
                let rows = build_meta(2, "ring", &s2, 0.90, &mut g);
                let o = run_mblock(&pb, &s2, &rows, &l2, 86000 + r, false);
                let t = if o.m[1] < 0.3 && o.l[1] < 0.3 { 1.0 } else { 0.0 };
                writeln!(w, "B,{r},{t:.1},0,0,{:.4},{:.4}", o.m[1], o.l[1]).unwrap();
            }
            eprintln!("mnetT B done");
        }
        "mnet2gate" => {
            // I024 validation gate (00_freeze_I024.yaml): reproduce I021 cell 2
            // (M=100 n=100 ring clustered, seeds 80000+2000+r) through the mnet2
            // driver path; must match mnet_cells.csv cell-2 rows at 4 decimals.
            let base = P { a0: 0.8, lam: 0.7, rho: 0.002, ..P::default() };
            let sizes = vec![100usize; 100];
            let losing: Vec<bool> = (0..100).map(|c| c < 50).collect();
            for r in 0..40u64 {
                let seed = 80000 + 2 * 1000 + r;
                let mut grng = Rng::new(seed + 500000);
                let rows = build_meta(100, "ring", &sizes, 0.85, &mut grng);
                let o = run_mblock(&base, &sizes, &rows, &losing, seed, false);
                let (mut nt, mut nc, mut nl) = (0.0f64, 0.0f64, 0.0f64);
                let (mut sm, mut sl) = (0.0f64, 0.0f64);
                for c in 0..100 { if losing[c] {
                    nl += 1.0; sm += o.m[c]; sl += o.l[c];
                    if o.m[c] < 0.3 && o.l[c] < 0.3 { nt += 1.0; }
                    if o.m[c] > 0.7 && o.l[c] < 0.3 { nc += 1.0; }
                } }
                println!("2,100,100,ring,clustered,{r},{:.4},{:.4},{:.4},{:.4}",
                         nt / nl, nc / nl, sm / nl, sl / nl);
            }
        }
        "mnet2" | "mnet2ad" => {
            // I024 frozen confirmatory battery (00_freeze_I024.yaml)
            // seeds 90000 + cid*1000 + run; graph seeds +500000
            // "mnet2ad" runs only the addendum-1 cells (cid 51-55) into mnet2ad_*.csv
            let ad = mode == "mnet2ad";
            let fcell = File::create(if ad { "out/mnet2ad_cells.csv" } else { "out/mnet2_cells.csv" }).unwrap();
            let mut wc = BufWriter::new(fcell);
            writeln!(wc, "cell,m_comms,n_size,geom,place,w_in,rho,t,run,frac_trap,frac_cred,frac_cbi,mean_m,mean_l").unwrap();
            let fcomm = File::create(if ad { "out/mnet2ad_comm.csv" } else { "out/mnet2_comm.csv" }).unwrap();
            let mut wk = BufWriter::new(fcomm);
            writeln!(wk, "cell,run,comm,xexp,m,l,class").unwrap();
            let mut cells: Vec<(usize, usize, usize, &str, &str, f64, f64, usize, u64)> = Vec::new();
            let mut id = 0usize;
            // arm A1: n=100, M in {10,100,1000}
            for &(mm, runs) in &[(10usize, 40u64), (100, 40), (1000, 20)] {
                for g in ["ring", "ws1", "ba", "broadcast"] {
                    for pl in ["clustered", "scattered"] {
                        cells.push((id, mm, 100, g, pl, 0.85, 0.002, 600, runs)); id += 1;
                    }
                }
            }
            // arm A2: n=10, M in {100,1000}
            for &mm in &[100usize, 1000] {
                for g in ["ring", "broadcast"] {
                    for pl in ["clustered", "scattered"] {
                        cells.push((id, mm, 10, g, pl, 0.85, 0.002, 600, 40)); id += 1;
                    }
                }
            }
            // arm B1: M=2 n=1000 w_in sweep
            for &w in &[0.95, 0.90, 0.875, 0.85, 0.80] {
                cells.push((id, 2, 1000, "ring", "clustered", w, 0.002, 600, 40)); id += 1;
            }
            // arm B2: M=100 ring scattered w_in sweep
            for &w in &[0.775, 0.80, 0.85, 0.90] {
                cells.push((id, 100, 100, "ring", "scattered", w, 0.002, 600, 40)); id += 1;
            }
            // arm B3: broadcast inequality
            for &w in &[0.80, 0.775, 0.75] {
                cells.push((id, 100, 100, "broadcast", "clustered", w, 0.002, 600, 40)); id += 1;
            }
            // arm C: (rho, T) hyperbola
            for &(rr, tt) in &[(0.002f64, 750usize), (0.002, 920), (0.002, 1050),
                               (0.004, 400), (0.004, 600), (0.0015, 1000), (0.0015, 1400)] {
                cells.push((id, 100, 100, "ring", "clustered", 0.85, rr, tt, 20)); id += 1;
            }
            // addendum 1 (frozen post-battery, pre-run): two-clock cells 51-54 + edge cell 55
            for &(rr, tt) in &[(0.002f64, 1100usize), (0.002, 1300), (0.002, 1600),
                               (0.0015, 2100)] {
                cells.push((id, 100, 100, "ring", "clustered", 0.85, rr, tt, 20)); id += 1;
            }
            cells.push((id, 2, 1000, "ring", "clustered", 0.8875, 0.002, 600, 40)); id += 1;
            let _ = id;
            if ad { cells.retain(|c| c.0 >= 51); } else { cells.retain(|c| c.0 < 51); }
            for (cid, mm, nn, geom, place, w_in, rr, tt, runs) in cells {
                let p = P { a0: 0.8, lam: 0.7, rho: rr, t: tt, ..P::default() };
                let sizes = vec![nn; mm];
                let losing: Vec<bool> = (0..mm).map(|c| match place {
                    "scattered" => c % 2 == 0,
                    _ => c < mm / 2,
                }).collect();
                for r in 0..runs {
                    let seed = 90000 + cid as u64 * 1000 + r;
                    let mut grng = Rng::new(seed + 500000);
                    let rows = build_meta(mm, geom, &sizes, w_in, &mut grng);
                    let o = run_mblock(&p, &sizes, &rows, &losing, seed, false);
                    let (mut nt, mut ncred, mut ncbi, mut nl) = (0.0f64, 0.0f64, 0.0f64, 0.0f64);
                    let (mut sm, mut sl) = (0.0f64, 0.0f64);
                    for c in 0..mm { if losing[c] {
                        nl += 1.0; sm += o.m[c]; sl += o.l[c];
                        let (mv, lv) = (o.m[c], o.l[c]);
                        if mv < 0.3 && lv < 0.3 { nt += 1.0; }
                        else if mv < 0.3 && lv > 0.5 { ncred += 1.0; }
                        else if mv > 0.7 && lv < 0.3 { ncbi += 1.0; }
                    } }
                    writeln!(wc, "{cid},{mm},{nn},{geom},{place},{w_in},{rr},{tt},{r},{:.4},{:.4},{:.4},{:.4},{:.4}",
                             nt / nl, ncred / nl, ncbi / nl, sm / nl, sl / nl).unwrap();
                    for c in 0..mm { if losing[c] {
                        let mut xe = 0.0;
                        for &(d, w) in &rows[c] { if d != c && !losing[d] { xe += w; } }
                        let (mv, lv) = (o.m[c], o.l[c]);
                        let cl = if mv < 0.3 && lv < 0.3 { "trap" }
                                 else if mv < 0.3 && lv > 0.5 { "cred" }
                                 else if mv > 0.7 && lv < 0.3 { "cbi" }
                                 else if mv > 0.7 && lv > 0.5 { "legit" }
                                 else { "mixed" };
                        writeln!(wk, "{cid},{r},{c},{xe:.4},{mv:.4},{lv:.4},{cl}").unwrap();
                    } }
                }
                eprintln!("mnet2 cell {cid} ({mm}x{nn} {geom} {place} w={w_in} rho={rr} T={tt}) done");
            }
        }
        "invcal" => {
            // POST-I032 EXPLORATORY (inverse calibration; not a certification).
            // Questions, written before the run: at the confirmatory cell
            // (A0=.8, lam=.7, rho=.002, chi=.4, n=200, T=600), how weak can the gate be
            // before the paper's trap stops being the typical outcome (P_dw < .5)?
            //  part s:     speed scaling, nu_F=.05s and nu_R=.0125s (ratio .25, A* fixed)
            //  part ratio: sensitivity, nu_R/nu_F in .25..31 at s=1 (refines nfsweep)
            //  part joint: s x ratio grid near both edges
            // 200 runs per cell; seeds 61000 + 1000*cell; existing modes untouched.
            let f = File::create("out/invcal.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "part,s,ratio,m2,l2,p_dw,p_persist,reps").unwrap();
            let mut cell = 0u64;
            let mut emit = |w: &mut BufWriter<File>, part: &str, s: f64, ratio: f64, cell: u64| {
                let p = P { a0: 0.8, lam: 0.7, rho: 0.002, nu_f: 0.05 * s,
                            nu_r: 0.05 * s * ratio, ..P::default() };
                let (m2, _v, l2, _vl, pdw, pper, _, _) = cell_stats(&p, Gate::Diss,
                    wrong.0, wrong.1, 200, 61000 + cell * 1000);
                writeln!(w, "{part},{s},{ratio},{m2:.5},{l2:.5},{pdw:.4},{pper:.4},200").unwrap();
                eprintln!("invcal {part} s={s} ratio={ratio} P_dw={pdw:.3}");
            };
            for s in [2.0, 1.5, 1.25, 1.0, 0.8, 0.65, 0.5, 0.4, 0.3, 0.2] {
                emit(&mut w, "s", s, 0.25, cell); cell += 1;
            }
            for ratio in [0.25, 0.26, 0.27, 0.28, 0.29, 0.30, 0.31] {
                emit(&mut w, "ratio", 1.0, ratio, cell); cell += 1;
            }
            for s in [1.0, 0.75, 0.5, 0.35] { for ratio in [0.25, 0.27, 0.29] {
                emit(&mut w, "joint", s, ratio, cell); cell += 1;
            } }
        }
        "bgt" => {
            // KGi-DISS-I036 (freeze 00_freeze_I036.yaml, written before running):
            // census of end states at the paper's configuration and gate-scope ablation.
            // Per run: m2 (share of community 2 on the better arm, last 50 trials), l2.
            let f = File::create("out/bgt.csv").unwrap();
            let mut w = BufWriter::new(f);
            writeln!(w, "cell,run,m1,m2,l1,l2").unwrap();
            let base = P { a0: 0.8, lam: 0.7, rho: 0.002, ..P::default() };
            let cells: Vec<(&str, P, Gate)> = vec![
                ("c1 paper cell, gate on", base, Gate::Diss),
                ("c2 paper cell, gate off", base, Gate::Off),
                ("c3 neutral entitlement A0=.5", P { a0: 0.5, ..base }, Gate::Diss),
                ("c4 weak conformity lam=.3", P { lam: 0.3, ..base }, Gate::Diss),
                ("c5 isolation Gamma=0, A0=.5, gate on", P { a0: 0.5, gamma: 0.0, ..base }, Gate::Diss),
                ("c6 isolation Gamma=0, gate off", P { gamma: 0.0, ..base }, Gate::Off),
                ("c7 open Gamma=.3", P { gamma: 0.3, ..base }, Gate::Diss),
                ("c8 paper cell, T=2400", P { t: 2400, ..base }, Gate::Diss),
                ("a1 gate on own learning only", P { gate_soc: false, ..base }, Gate::Diss),
                ("a2 gate on social learning only", P { gate_own: false, ..base }, Gate::Diss),
                ("a3 legitimacy moves, gates nothing", P { gate_own: false, gate_soc: false, ..base }, Gate::Diss),
            ];
            for (ci, (name, p, gate)) in cells.iter().enumerate() {
                for r in 0..300u64 {
                    let o = run(p, *gate, wrong.0, wrong.1, 63000 + (ci as u64) * 100000 + r * 7919, None);
                    writeln!(w, "{name},{r},{:.4},{:.4},{:.4},{:.4}", o.m1, o.m2, o.l1, o.l2).unwrap();
                }
                eprintln!("bgt {name} done");
            }
        }
        _ => eprintln!("unknown mode"),
    }
}
