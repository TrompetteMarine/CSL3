# CairoMakie figure pipeline v4 — reads Rust sweep CSVs + frozen KGi JSONs; no new runs.
# I005 redesign: one theme, consistent color semantics (vermillion = dissonance/gate-on/
# trapped, blue = Bayesian/corrected/legitimate, gray = neutral), validated categorical
# palette (dataviz validator: 4-regime set passes all pairs; contrast WARN relieved by
# on-map direct labels), direct labels over legends, labeled colorbars, phase annotations.
using CairoMakie, JSON, DelimitedFiles, Printf, Statistics
CairoMakie.activate!(type="pdf")

const VER  = RGBf(0.835, 0.369, 0.0)    # D55E00 dissonance / gate-on / trapped
const BLU  = RGBf(0.0, 0.447, 0.698)    # 0072B2 Bayesian / corrected / legitimate
const SKY  = RGBf(0.337, 0.706, 0.914)  # 56B4E9 credulous error
const ORA  = RGBf(0.902, 0.624, 0.0)    # E69F00 correct-but-illegitimate
const INK  = RGBf(0.28, 0.28, 0.30)
const INK2 = RGBf(0.45, 0.45, 0.47)
const GRY  = RGBf(0.72, 0.72, 0.72)
const BLUES = cgrad([RGBf(0.97,0.98,1.0), RGBf(0.13,0.36,0.58)])

set_theme!(Theme(
    fontsize = 11,
    Axis = (xgridvisible=false, ygridvisible=false, topspinevisible=false,
            rightspinevisible=false, spinewidth=1.0, spinecolor=INK2,
            xtickwidth=1.0, ytickwidth=1.0, xtickcolor=INK2, ytickcolor=INK2,
            xticksize=4, yticksize=4,
            xticklabelsize=9, yticklabelsize=9, xlabelsize=10.5, ylabelsize=10.5,
            titlesize=11.5, titlefont=:bold, titlealign=:left, titlegap=7,
            xticklabelcolor=INK, yticklabelcolor=INK, xlabelcolor=INK, ylabelcolor=INK,
            titlecolor=INK, subtitlesize=9, subtitlecolor=INK2),
    Legend = (framevisible=false, labelsize=9, patchsize=(16,9), rowgap=0, labelcolor=INK),
    Colorbar = (labelsize=9.5, ticklabelsize=8.5, spinewidth=.8, width=10,
                labelcolor=INK, ticklabelcolor=INK),
))

OUT = "figures"; RS = "rustsim/out"
I1 = "/home/claude/kgi-diss-i001"; I2 = "/home/claude/kgi-diss-i002"; I3 = "/home/claude/kgi-diss-i003"
nuF, nuR, tauF, phim, phip = .05, .0125, .3, 1.0, .25
Astar(mu) = (tauF + (nuR/nuF)*mu/(1-mu))/phim
panel!(fig, pos, l) = Label(fig[pos..., TopLeft()], l, font=:bold, fontsize=14,
                            padding=(0,8,8,0), halign=:left, color=INK)
tint(c, a) = RGBf(1-(1-c.r)*a, 1-(1-c.g)*a, 1-(1-c.b)*a)

readcsv(f) = begin
    raw, hdr = readdlm(f, ',', header=true)
    Dict(string(strip(h)) => raw[:, i] for (i, h) in enumerate(vec(hdr)))
end
drift(mu, a) = -nuF*((1-mu)*max(phim*a-tauF,0) + mu*max(phip*(1-a)-tauF,0)) +
                nuR*((1-mu)*(phim*a<=tauF) + mu*(phip*(1-a)<=tauF))

# ------------------------------- Fig 2: theory -----------------------------------
function fig_theory()
    f = Figure(size=(1100, 330))
    # --- a: drift with sign bands -------------------------------------------------
    ax1 = Axis(f[1,1], xlabel="aspiration A", ylabel="E[ΔL]",
               title="legitimacy drift and the critical aspiration",
               limits=(0,1,-.0165,.0165))
    hspan!(ax1, 0, .0165, color=(BLU,.055))
    hspan!(ax1, -.0165, 0, color=(VER,.055))
    text!(ax1, .985, .0145, text="repair  E[ΔL] > 0", fontsize=8.5, color=BLU,
          align=(:right,:center))
    text!(ax1, .015, -.0152, text="erosion  E[ΔL] < 0", fontsize=8.5, color=VER,
          align=(:left,:center))
    A = range(.02,.98,length=400)
    hlines!(ax1, [0], color=GRY, linewidth=1)
    lines!(ax1, A, drift.(0.4,A), color=INK, linewidth=2)
    lines!(ax1, A, drift.(0.6,A), color=INK2, linewidth=2, linestyle=:dash)
    text!(ax1, .91, -.0122, text="μ = 0.4", fontsize=9, color=INK,
          align=(:left,:center))
    text!(ax1, .88, drift(0.6,.88)+.0012, text="μ = 0.6", fontsize=9, color=INK2,
          align=(:left,:bottom))
    for (mu, dx) in ((0.4,-.015),(0.6,.015))
        as = Astar(mu)
        lines!(ax1, [as,as], [-.0165, 0], color=VER, linestyle=:dash, linewidth=1.2)
        scatter!(ax1, [as], [0], color=:white, strokecolor=VER, strokewidth=1.6, markersize=8)
        text!(ax1, as+dx, -.0115, text="A*($(mu))", fontsize=9, color=VER,
              align=(dx<0 ? :right : :left, :center))
    end
    # --- b, c: phase portraits with sign bands ------------------------------------
    rhoplot = 0.004
    for (k,(chi,ttl,sub)) in enumerate([
            (0.0,"resignation (χ = 0)","aspiration adapts to own outcomes: gate reopens"),
            (0.6,"grievance (χ = 0.6)","anchored above experience: gate absorbed shut")])
        ax = Axis(f[1,k+1], xlabel="aspiration A",
                  ylabel=(k==1 ? "legitimacy L" : ""), title="flow of (A, L): "*ttl,
                  subtitle=sub, limits=(0,1,-0.02,1.02))
        as = Astar(0.4)
        vspan!(ax, 0, as, color=(BLU,.05))
        vspan!(ax, as, 1, color=(VER,.05))
        Ainf = (1-chi)*0.4 + chi*0.6
        ffield(x) = begin
            u = rhoplot*(Ainf - x[1]); v = drift(0.4, clamp(x[1],0,1))
            if (x[2] >= 1 && v > 0) || (x[2] <= 0 && v < 0); v = 0.0; end
            n = sqrt(u^2+v^2); n = n>0 ? n : 1.0
            Point2f(u/n, v/n)   # direction field (unit speed): phase-portrait view
        end
        streamplot!(ax, ffield, 0.0..1.0, 0.0..1.0;
                    colormap=cgrad([RGBAf(.58,.58,.60,.75), RGBAf(.58,.58,.60,.75)]),
                    arrow_size=6.5, gridsize=(22,22), stepsize=0.004, linewidth=.6)
        vlines!(ax, [as], color=VER, linestyle=:dash, linewidth=1.8)
        vlines!(ax, [Ainf], color=INK, linestyle=:dot, linewidth=1.3)
        for (a0,l0) in ((.15,.75),(.85,.75),(.60,.25))
            a,l = a0,l0; ta=[a]; tl=[l]
            for _ in 1:6000
                l = clamp(l + drift(0.4,a), 0, 1)
                a = clamp(a + rhoplot*(Ainf-a), 0, 1)
                push!(ta,a); push!(tl,l)
            end
            c = tl[end] > .5 ? BLU : VER
            lines!(ax, ta, tl, color=c, linewidth=2.2)
            scatter!(ax, [ta[1]],[tl[1]], color=:white, strokecolor=c, strokewidth=1.3, markersize=7)
        end
        Lstar = Ainf < as ? 1.0 : 0.0
        ac = Ainf < as ? BLU : VER
        scatter!(ax, [Ainf],[Lstar], color=ac, markersize=14, marker=:circle,
                 strokecolor=:white, strokewidth=1.6)
        if k==1
            text!(ax, Ainf-.015, .895, text="resigned repair", fontsize=9, font=:bold,
                  color=ac, align=(:right,:center))
        else
            text!(ax, Ainf-.075, .07, text="grievance trap", fontsize=9, font=:bold,
                  color=ac, align=(:right,:center))
        end
        text!(ax, as+(k==1 ? .022 : -.022), .62, text="A*", fontsize=10, color=VER,
              align=(k==1 ? :left : :right,:center))
        if k==1
            text!(ax, Ainf-.025, .80, text="A∞", fontsize=10, color=INK, align=(:right,:center))
        else
            text!(ax, Ainf+.012, .33, text="A∞", fontsize=10, color=INK, align=(:left,:center))
        end
    end
    for (i,l) in enumerate(["a","b","c"]); panel!(f,(1,i),l); end
    save(joinpath(OUT,"fig_theory.pdf"), f)
end

# ------------------------------- Fig 3: ABM --------------------------------------
function fig_abm()
    f = Figure(size=(1180, 320))
    raw = readdlm(joinpath(RS,"raster.csv"), ',')
    ts = Float64.(raw[:,1]); M = Matrix{Float64}(raw[:,2:end])  # time x agents
    ax1 = Axis(f[1,1], xlabel="trial", ylabel="agent", title="one trapped run",
               subtitle="rows 1–100: winning community · rows 101–200: losing community")
    hm = heatmap!(ax1, ts, 1:size(M,2), M, colormap=BLUES, colorrange=(0,1))
    hlines!(ax1, [100.5], color=:white, linewidth=1.8)
    Colorbar(f[1,2], hm, label="legitimacy Lᵢ,ₜ")
    # --- b: spaghetti with direct labels ------------------------------------------
    d = readcsv(joinpath(RS,"spaghetti.csv"))
    gates = strip.(string.(d["gate"]))
    ax2 = Axis(f[1,3], xlabel="trial", ylabel="m₂(a*) (losing community)",
               title="path dependence across runs", limits=(nothing,nothing,-.03,1.12))
    for rep in 0:59, (g,col,al) in [("off",INK,.13),("on",VER,.25)]
        idx = (d["rep"].==rep) .& (gates.==g)
        any(idx) || continue
        lines!(ax2, Float64.(d["t"][idx]), Float64.(d["m2"][idx]), color=(col,al), linewidth=.8)
    end
    text!(ax2, 300, 1.065, text="gate off: all 60 runs correct", fontsize=8.5, color=INK,
          align=(:left,:center))
    text!(ax2, 300, .15, text="gate on: most runs freeze,", fontsize=8.5, color=VER,
          align=(:left,:center))
    text!(ax2, 300, .085, text="a minority escape early", fontsize=8.5, color=VER,
          align=(:left,:center))
    # --- c: confirmatory contrast with paired-restore bracket ----------------------
    C = JSON.parsefile(joinpath(I2,"20_sim/results_confirmatory.json"))["confirmatory_trap"]
    m_on, m_off = C["m2_on"], C["m2_off"]
    lo, mn, hi = C["paired_restore"]; P, Plo, Phi = C["P_defwrong"]
    ax3 = Axis(f[1,4], ylabel="terminal m₂(a*)", title="confirmatory (R = 300)",
               subtitle=@sprintf("P(defensive wrong) = %.3f [%.3f, %.3f]", P, Plo, Phi),
               xticks=(1:2, ["gate on","gate off\n(CRN)"]), limits=(.45,2.75,0,1.12))
    barplot!(ax3, [1,2], [m_on,m_off], color=[tint(VER,.75), tint(INK,.45)],
             strokecolor=:white, strokewidth=1.5, width=.58)
    text!(ax3, 1, m_on+.035, text=@sprintf("%.3f",m_on), fontsize=9, color=INK,
          align=(:center,:bottom))
    text!(ax3, 2, m_off+.035, text=@sprintf("%.3f",m_off), fontsize=9, color=INK,
          align=(:center,:bottom))
    # CRN paired-restore bracket (CI from the frozen bootstrap record)
    bx = 2.47
    lines!(ax3, [bx,bx], [m_on, m_off], color=INK, linewidth=1.2)
    lines!(ax3, [bx-.05,bx], [m_on, m_on], color=INK, linewidth=1.2)
    lines!(ax3, [bx-.05,bx], [m_off, m_off], color=INK, linewidth=1.2)
    text!(ax3, bx-.09, (m_on+m_off)/2,
          text=@sprintf("restore +%.3f\n[%.3f, %.3f]", mn, lo, hi),
          fontsize=7.5, color=INK, align=(:right,:center))
    colsize!(f.layout, 1, Relative(.37)); colsize!(f.layout, 3, Relative(.31))
    for (i,l) in zip([1,3,4],["a","b","c"]); panel!(f,(1,i),l); end
    save(joinpath(OUT,"fig_abm.pdf"), f)
end

# ------------------------------- Fig 4: PT1 --------------------------------------
function fig_pt1()
    f = Figure(size=(1180, 310))
    d = readcsv(joinpath(RS,"pt1.csv"))
    a0s = sort(unique(d["a0"])); lams = sort(unique(d["lam"]))
    Pm = [Float64(d["p_dw"][findfirst((d["a0"].==a).&(d["lam"].==l))]) for a in a0s, l in lams]
    ax1 = Axis(f[1,1], xlabel="initial entitlement A₀", ylabel="transmission λ",
               title="a sharply bounded trap region")
    hm = heatmap!(ax1, a0s, lams, Pm, colormap=BLUES, colorrange=(0,1))
    contour!(ax1, a0s, lams, Pm, levels=[.5], color=:white, linewidth=1.6)
    # I014: deterministic community-map basin boundary (Supplementary Section S5)
    lamg = collect(range(lams[1], lams[end], length=22))
    mfb = [mf_dw_boundary_a0(l) for l in lamg]
    ok = .!isnan.(mfb)
    lines!(ax1, mfb[ok], lamg[ok], color=VER, linewidth=1.6, linestyle=:dash)
    text!(ax1, .62, .60, text="deterministic\nbasin boundary", fontsize=8, color=VER,
          align=(:right,:center))
    text!(ax1, .655, .795, text="defensive wrong\nconsensus", fontsize=9, font=:bold,
          color=:white, align=(:center,:center))
    text!(ax1, .55, .50, text="corrects", fontsize=9, font=:bold, color=INK2,
          align=(:center,:center))
    scatter!(ax1, [0.8],[0.7], marker=:star5, markersize=15, color=VER,
             strokecolor=:white, strokewidth=.8)
    text!(ax1, .785, .662, text="confirmatory cell", fontsize=8, color=VER, align=(:right,:center))
    Colorbar(f[1,2], hm, label="P(defensive wrong)")
    # --- b, c: order parameter and susceptibility with critical band ----------------
    dc = readcsv(joinpath(RS,"cuts.csv"))
    ax2 = Axis(f[1,3], xlabel="initial entitlement A₀", ylabel="mean m₂(a*)",
               title="order parameter", limits=(nothing,nothing,-.05,1.14))
    ax3 = Axis(f[1,4], xlabel="initial entitlement A₀", ylabel="Var(m₂) across runs",
               title="across-run variance (regime selection)")
    for ax in (ax2, ax3); vspan!(ax, .61, .71, color=(VER,.06)); end
    shades = [RGBf(.58,.70,.82), RGBf(.33,.53,.71), RGBf(.10,.30,.50)]
    for (k,lam) in enumerate([0.55,0.65,0.75])
        idx = dc["lam"].==lam
        a = Float64.(dc["a0"][idx]); o = sortperm(a)
        m = Float64.(dc["m2"][idx][o])
        se = 2 .* sqrt.(max.(Float64.(dc["var_m2"][idx][o]), 0) ./ 60)
        band!(ax2, a[o], m .- se, m .+ se, color=(shades[k], .18))
        lines!(ax2, a[o], m, color=shades[k], linewidth=2)
        v = Float64.(dc["var_m2"][idx][o])
        cv = 2 * sqrt(2/59)   # approx 95% band for a variance estimate at n=60
        band!(ax3, a[o], v .* (1 - cv), v .* (1 + cv), color=(shades[k], .14))
        lines!(ax3, a[o], v, color=shades[k], linewidth=2)
    end
    text!(ax2, .455, 1.075, text="λ = 0.55, 0.65", fontsize=8.5, color=shades[2],
          align=(:left,:center))
    text!(ax2, .72, .45, text="λ = 0.75", fontsize=8.5, color=shades[3], align=(:left,:center))
    text!(ax2, .66, -.02, text="regime-\nselection band", fontsize=7.5, color=VER, align=(:center,:bottom))
    text!(ax3, .655, .255, text="λ = 0.75", fontsize=8.5, color=shades[3], align=(:center,:bottom))
    text!(ax3, .845, .17, text="λ = 0.65", fontsize=8.5, color=shades[2], align=(:right,:center))
    text!(ax3, .50, .012, text="λ = 0.55: no trap on this range", fontsize=7.5,
          color=shades[1], align=(:left,:bottom))
    for (i,l) in zip([1,3,4],["a","b","c"]); panel!(f,(1,i),l); end
    save(joinpath(OUT,"fig_pt1.pdf"), f)
end

# ------------------------------- Fig 5: PT2 --------------------------------------
function fig_pt2()
    f = Figure(size=(1000, 330))
    d = readcsv(joinpath(RS,"pt2.csv"))
    rhos = sort(unique(d["rho"])); chis = sort(unique(d["chi"]))
    Pm = [Float64(d["p_persist"][findfirst((d["rho"].==r).&(d["chi"].==c))]) for c in chis, r in rhos]
    rtick = ([log10(.001), log10(.003), log10(.01), log10(.03)],
             ["0.001","0.003","0.01","0.03"])
    ax1 = Axis(f[1,1], xlabel="social anchoring χ", ylabel="aspiration adaptation ρ (log)",
               title="persistence requires slow aspiration", yticks=rtick)
    hm = heatmap!(ax1, chis, log10.(rhos), Pm, colormap=BLUES, colorrange=(0,1))
    hlines!(ax1, [log10(0.00641)], color=VER, linestyle=:dash, linewidth=1.8)
    text!(ax1, .02, log10(0.00641)+.055, text="ρ_c (mean field)", fontsize=9, color=VER,
          align=(:left,:bottom))
    text!(ax1, .45, -2.80, text="persistent collapse", fontsize=9, font=:bold,
          color=:white, align=(:center,:center))
    text!(ax1, .45, -1.78, text="aspiration adapts first: recovers", fontsize=9,
          font=:bold, color=INK2, align=(:center,:center))
    Colorbar(f[1,2], hm, label="P(persistent collapse)")
    # --- b: dwell times -------------------------------------------------------------
    ax2 = Axis(f[1,3], xlabel="aspiration adaptation ρ", ylabel="mean dwell, L̄₂ < 0.3 (trials)",
               title="dwell-time collapse at ρ_c", xscale=log10,
               xticks=([.001,.003,.01,.03],["0.001","0.003","0.01","0.03"]))
    shades = [RGBf(.58,.70,.82), RGBf(.33,.53,.71), RGBf(.10,.30,.50)]
    for (k,chi) in enumerate([0.0, 0.432, 0.9])
        idx = abs.(d["chi"].-chi).<1e-6
        r = Float64.(d["rho"][idx]); o = sortperm(r)
        dw = Float64.(d["dwell"][idx][o])
        se = 2 .* sqrt.(max.(Float64.(d["var_dwell"][idx][o]), 0) ./ 40)
        band!(ax2, r[o], dw .- se, dw .+ se, color=(shades[k], .16))
        lines!(ax2, r[o], dw, color=shades[k], linewidth=2)
    end
    vlines!(ax2, [0.00641], color=VER, linestyle=:dash, linewidth=1.4)
    text!(ax2, 0.0068, 500, text="ρ_c", fontsize=9.5, color=VER, align=(:left,:center))
    text!(ax2, 0.00105, 445, text="χ = 0", fontsize=8.5, color=shades[1], align=(:left,:center))
    text!(ax2, 0.00105, 505, text="χ = 0.43", fontsize=8.5, color=shades[2], align=(:left,:center))
    text!(ax2, 0.00105, 560, text="χ = 0.9", fontsize=8.5, color=shades[3], align=(:left,:center))
    colsize!(f.layout, 1, Relative(.5))
    for (i,l) in zip([1,3],["a","b"]); panel!(f,(1,i),l); end
    save(joinpath(OUT,"fig_pt2.pdf"), f)
end

# ------------------------------- Fig 7: transparency ------------------------------
function fig_trans()
    f = Figure(size=(1000, 640))
    d = readcsv(joinpath(RS,"pt3.csv"))
    ag = strip.(string.(d["agent"])); vr = strip.(string.(d["variant"]))
    sel(a,v) = (ag.==a).&(vr.==v)
    ax1 = Axis(f[1,1], xlabel="permeability Γ", ylabel="terminal m₂(a*)",
               title="behaviour corrects for all three", limits=(nothing,nothing,-.03,1.12))
    ax2 = Axis(f[1,2], xlabel="permeability Γ", ylabel="gate (L or π_fair)",
               title="rational trust recovers at evidence speed", limits=(nothing,nothing,-.03,1.12))
    for (a,col) in [("diss",VER),("bayes",BLU)]
        i = sel(a,"knife"); g = Float64.(d["gamma"][i]); o = sortperm(g)
        m = Float64.(d["m2"][i][o]); gt = Float64.(d["gate"][i][o])
        sm = 2 .* sqrt.(max.(Float64.(d["var_m2"][i][o]), 0) ./ 60)
        sg = 2 .* sqrt.(max.(Float64.(d["var_gate"][i][o]), 0) ./ 60)
        band!(ax1, g[o], m .- sm, m .+ sm, color=(col,.15))
        band!(ax2, g[o], gt .- sg, gt .+ sg, color=(col,.15))
        lines!(ax1, g[o], m, color=col, linewidth=2)
        lines!(ax2, g[o], gt, color=col, linewidth=2)
    end
    db = readcsv(joinpath(RS,"pt3b.csv"))
    gb = Float64.(db["gamma"]); ob = sortperm(gb)
    mb = Float64.(db["m2"])[ob]; tb = Float64.(db["gate"])[ob]
    smb = 2 .* sqrt.(max.(Float64.(db["var_m2"])[ob], 0) ./ 60)
    stb = 2 .* sqrt.(max.(Float64.(db["var_gate"])[ob], 0) ./ 60)
    band!(ax1, gb[ob], mb .- smb, mb .+ smb, color=(SKY,.18))
    lines!(ax1, gb[ob], mb, color=SKY, linewidth=2, linestyle=:dashdot)
    band!(ax2, gb[ob], tb .- stb, tb .+ stb, color=(SKY,.18))
    lines!(ax2, gb[ob], tb, color=SKY, linewidth=2, linestyle=:dashdot)
    text!(ax1, .095, .72, text="dissonance", fontsize=8.5, color=VER, align=(:right,:center))
    text!(ax1, .185, .30, text="global-rig Bayesian", fontsize=8.5, color=BLU, align=(:left,:center))
    text!(ax1, .31, .88, text="group-contingent Bayesian", fontsize=8.5, color=SKY, align=(:left,:center))
    i = sel("diss","generic"); g = Float64.(d["gamma"][i]); o = sortperm(g)
    gg = Float64.(d["gate"][i][o])
    sgg = 2 .* sqrt.(max.(Float64.(d["var_gate"][i][o]), 0) ./ 60)
    band!(ax2, g[o], gg .- sgg, gg .+ sgg, color=(VER,.10))
    lines!(ax2, g[o], gg, color=VER, linewidth=1.8, linestyle=:dash)
    text!(ax2, .26, 1.045, text="global-rig π_fair → 1", fontsize=8.5, color=BLU, align=(:center,:center))
    text!(ax2, .40, .90, text="group-contingent:\nown success heals trust", fontsize=8, color=SKY, align=(:center,:center))
    text!(ax2, .30, .50, text="dissonance, generic ν_R (slow 1/ρ clock)", fontsize=8.5,
          color=VER, align=(:center,:bottom))
    text!(ax2, .30, .115, text="dissonance, knife-edge: stays collapsed", fontsize=8.5,
          color=VER, align=(:center,:bottom))
    # --- c: recovery threshold -------------------------------------------------------
    cb = JSON.parsefile(joinpath(I1,"10_theory/check6b_results.json"))
    mg = [0.5,0.7,0.9]
    ax3 = Axis(f[2,1], xlabel="restored arm mean μ_good", ylabel="trials to reopening",
               title="recovery threshold", yscale=log10)
    for (key,col,lab) in [("diss",VER,"dissonance"),("bayes",BLU,"Bayesian")]
        v = [Float64(cb[key][string(m)]["t_reopen"]) for m in mg]
        lines!(ax3, mg, v, color=col, linewidth=2)
        scatter!(ax3, mg, v, color=col, markersize=8)
        text!(ax3, .905, v[end], text=lab, fontsize=8.5, color=col, align=(:left,:center))
    end
    vlines!(ax3, [0.5], color=GRY, linestyle=:dash)
    text!(ax3, .512, 6500, text="resignation boundary:\nreopening time diverges", fontsize=8,
          color=INK, align=(:left,:center))
    xlims!(ax3, .475, .99)
    # --- d: entitlement scaling -------------------------------------------------------
    a0 = [0.5,0.65,0.8]; cl = [Float64(cb["closure_vs_entitlement"][string(a)]) for a in a0]
    ax4 = Axis(f[2,2], xlabel="initial entitlement A₀", ylabel="trials to collapse",
               title="entitlement scaling")
    lines!(ax4, a0, cl, color=VER, linewidth=2); scatter!(ax4, a0, cl, color=VER, markersize=8)
    for (x,y) in zip(a0,cl)
        text!(ax4, x, y+9, text=@sprintf("%d",round(Int,y)), fontsize=8, color=INK,
              align=(:center,:bottom))
    end
    text!(ax4, .645, 230, text="fixed-hypothesis Bayesian collapse\nis A₀-invariant by construction\n(no curve to show)",
          fontsize=8, color=BLU, align=(:center,:center))
    for (k,l) in enumerate(["a","b","c","d"])
        gr, gc = divrem(k-1, 2) .+ (1, 1); panel!(f,(gr,gc),l)
    end
    save(joinpath(OUT,"fig_transparency.pdf"), f)
end

# ------------------------------- ED Fig 1: identification -------------------------
# Redesigned as a dot plot: 4 blues failed the palette validator (adjacent dE << floor);
# identity is now carried by shape (estimator) + fill (data richness), one hue.
function fig_ident()
    S = JSON.parsefile(joinpath(I3,"30_stats/screen_results.json"))
    pars = ["nuF","nuR","tauF","rho","chi"]
    pl = ["ν_F","ν_R","τ^F","ρ","χ"]
    rows = Dict(p => 6-i for (i,p) in enumerate(pars))   # nuF top (y=5) … chi bottom (y=1)
    f = Figure(size=(820, 330))
    ax = Axis(f[1,1], xlabel="synthetic-recovery correlation r",
              yticks=(1:5, reverse(pl)), limits=(-.25, 1.02, .45, 5.55),
              title="individual-level gate parameters are not identified; ρ is, with the aspiration slider",
              titlesize=10.5)
    hspan!(ax, rows["rho"]-.42, rows["rho"]+.42, color=(VER,.07))
    vlines!(ax, [0], color=GRY, linewidth=.8)
    vlines!(ax, [0.7], color=VER, linestyle=:dash, linewidth=1.6)
    text!(ax, .705, 5.48, text="preregistration gate (r ≥ 0.7)", fontsize=8.5, color=VER,
          align=(:left,:top))
    cells = [("MLE_L",:circle,false,.17), ("MAP_L",:diamond,false,.06),
             ("MLE_LA",:circle,true,-.06), ("MAP_LA",:diamond,true,-.17)]
    for p in pars, (c,mk,filled,dy) in cells
        v = Float64(S[c][p]); y = rows[p]+dy
        # Fisher-z 95% CI from r and n=60 alone
        z = atanh(clamp(v, -.999, .999)); se = 1/sqrt(57)
        loc, hic = tanh(z - 1.96*se), tanh(z + 1.96*se)
        lines!(ax, [loc,hic], [y,y], color=(BLU,.45), linewidth=2)
        lines!(ax, [0,v], [y,y], color=(GRY,.4), linewidth=.8)
        scatter!(ax, [v],[y], marker=mk, markersize=(mk==:circle ? 9.5 : 11),
                 color=(filled ? BLU : :white), strokecolor=BLU, strokewidth=1.5)
    end
    text!(ax, .925, rows["rho"]+.33, text="r = 0.92, 0.91", fontsize=8, color=INK,
          align=(:center,:bottom))
    elems = [MarkerElement(marker=:circle, color=:white, strokecolor=BLU, strokewidth=1.5, markersize=9.5),
             MarkerElement(marker=:diamond, color=:white, strokecolor=BLU, strokewidth=1.5, markersize=11),
             MarkerElement(marker=:circle, color=BLU, markersize=9.5),
             MarkerElement(marker=:diamond, color=BLU, markersize=11)]
    Legend(f[1,1], elems,
           ["MLE — ratings only (L)","MAP — ratings only (L)",
            "MLE — + aspiration slider (L+A)","MAP — + aspiration slider (L+A)"],
           tellwidth=false, tellheight=false, halign=:right, valign=:bottom,
           margin=(6,6,6,6), labelsize=8.5)
    save(joinpath(OUT,"fig_ident.pdf"), f)
end

# ------------------------------- Fig 6: regime map --------------------------------
function fig_regmap()
    d = readcsv(joinpath(RS,"pt4.csv"))
    a0s = sort(unique(d["a0"])); gms = sort(unique(d["gamma"]))
    base = Dict("dw"=>VER, "cred"=>SKY, "ci"=>ORA, "leg"=>BLU, "mixed"=>RGBf(.72,.72,.72))
    img = Matrix{RGBf}(undef, length(a0s), length(gms))
    for (ia,a) in enumerate(a0s), (ig,g) in enumerate(gms)
        k = findfirst((d["a0"].==a).&(d["gamma"].==g))
        m = strip(string(d["modal"][k]))
        fr = Float64(d["f_"*(m=="leg" ? "leg" : m=="dw" ? "dw" : m=="ci" ? "ci" :
                              m=="cred" ? "cred" : "mixed")][k])
        img[ia,ig] = tint(base[m], fr)
    end
    f = Figure(size=(860, 470))
    ax = Axis(f[1,1], xlabel="initial entitlement A₀", ylabel="permeability Γ",
              title="modal regime at strong transmission (λ = 0.7)",
              subtitle="26 × 26 cells, 40 runs each; paler = modal regime less frequent across runs")
    da = (a0s[2]-a0s[1])/2; dg = (gms[2]-gms[1])/2
    image!(ax, (a0s[1]-da, a0s[end]+da), (gms[1]-dg, gms[end]+dg), img, interpolate=false)
    # hairline cell grid
    vlines!(ax, collect(a0s[1:end-1]).+da, color=(:white,.28), linewidth=.4)
    hlines!(ax, collect(gms[1:end-1]).+dg, color=(:white,.28), linewidth=.4)
    # direct region labels (identity on the map, not in a legend)
    text!(ax, .585, .33, text="legitimate consensus", fontsize=11, font=:bold,
          color=:white, align=(:center,:center))
    text!(ax, .585, .295, text="corrective field reaches everyone", fontsize=8,
          color=:white, align=(:center,:center))
    text!(ax, .735, .045, text="defensive wrong consensus", fontsize=10, font=:bold,
          color=:white, align=(:center,:center))
    text!(ax, .745, .022, text="trapped: wrong action, gate shut", fontsize=8,
          color=:white, align=(:center,:center))
    text!(ax, .862, .33, text="correct but\nillegitimate", fontsize=10, font=:bold,
          color=INK, align=(:center,:center))
    text!(ax, .862, .27, text="acts right,\nrejects the rule", fontsize=8,
          color=INK, align=(:center,:center))
    # credulous corner is small: leader line + outside-ish label
    text!(ax, .497, .085, text="credulous error", fontsize=9, font=:bold, color=:white,
          align=(:center,:bottom))
    text!(ax, .497, .062, text="isolated, wrong, content", fontsize=8, color=:white,
          align=(:center,:bottom))
    lines!(ax, [.487,.472], [.058,.012], color=:white, linewidth=.9)
    # mixed seam annotation
    text!(ax, .793, .445, text="mixed\n(regime-selection seam)", fontsize=8, color=INK,
          align=(:center,:center), rotation=0)
    # I014: deterministic community-map seams (Supplementary Section S5): the
    # behaviour boundary (terminal m2 = 0.5) and the legitimacy boundary (L2 = 0.5)
    m2g = [mf_terminal(lam=0.7, a0=a, gam=g)[1] for a in a0s, g in gms]
    l2g = [mf_terminal(lam=0.7, a0=a, gam=g)[2] for a in a0s, g in gms]
    contour!(ax, a0s, gms, m2g, levels=[0.5], color=(:black,.60), linewidth=1.3,
             linestyle=:dash)
    contour!(ax, a0s, gms, l2g, levels=[0.5], color=(:black,.60), linewidth=1.3,
             linestyle=:dot)
    # 2D legend: hue (regime) x tint (modal frequency)
    cols = [BLU, VER, ORA, SKY, RGBf(.72,.72,.72)]
    labs = ["legit.", "defens.", "corr.-illeg.", "credul.", "mixed"]
    sax = Axis(f[1,2], width=86, yaxisposition=:right,
               xticksvisible=false, xticklabelsvisible=false,
               yticks=([.08,.5,.92],["0","0.5","1"]),
               yticklabelsize=8, ylabel="modal-regime frequency", ylabelsize=9,
               topspinevisible=false, rightspinevisible=false,
               leftspinevisible=false, bottomspinevisible=false, yticksize=2)
    nf = 60
    leg = Matrix{RGBf}(undef, 5, nf)
    for (ci,c) in enumerate(cols), fi in 1:nf
        leg[ci,fi] = tint(c, (fi-1)/(nf-1))
    end
    image!(sax, (0,5), (0,1), leg, interpolate=false)
    vlines!(sax, 1:4, color=:white, linewidth=1.4)
    for (ci,lb) in enumerate(labs)
        text!(sax, ci-.35, -.03, text=lb, fontsize=6.4, color=INK,
              align=(:right,:center), rotation=pi/3)
    end
    xlims!(sax, 0, 5); ylims!(sax, -.40, 1.0)
    colgap!(f.layout, 10)
    save(joinpath(OUT,"fig_regimes_map.pdf"), f)
end

# ------------------------------- Supp: bimodality --------------------------------
function fig_bimodal()
    d = readcsv(joinpath(RS,"spaghetti.csv"))
    gates = strip.(string.(d["gate"]))
    tmax = maximum(Float64.(d["t"]))
    f = Figure(size=(640, 310))
    ax = Axis(f[1,1], xlabel="terminal m₂(a*)", ylabel="runs",
              title="terminal-outcome distribution at the confirmatory cell",
              limits=(-.03,1.03,0,68))
    edges = collect(range(0,1,length=21)); ctr = (edges[1:end-1].+edges[2:end])./2
    w = (edges[2]-edges[1])*0.42
    counts = Dict{String,Vector{Int}}(); low = Dict{String,Int}(); high = Dict{String,Int}()
    for (k,(g,col,lab)) in enumerate([("on",VER,"gate on"),("off",INK,"gate off")])
        term = Float64[]
        for rep in 0:59
            idx = (d["rep"].==rep).&(gates.==g).&(Float64.(d["t"]).==tmax)
            any(idx) && push!(term, Float64(d["m2"][idx][1]))
        end
        cnt = [count(x -> edges[j] <= x < edges[j+1] || (j==20 && x>=edges[21]), term)
               for j in 1:20]
        counts[g] = cnt; low[g] = count(x->x<.5, term); high[g] = count(x->x>=.5, term)
        barplot!(ax, ctr .+ (k==1 ? -w/2 : w/2), Float64.(cnt), width=w, color=(col,.88),
                 strokecolor=:white, strokewidth=.4, label=lab)
    end
    text!(ax, .09, counts["on"][1]+2, text="gate on: $(low["on"])/60 freeze", fontsize=9,
          color=VER, align=(:left,:bottom))
    text!(ax, .91, counts["on"][20]+2, text="$(high["on"])/60 escape", fontsize=9,
          color=VER, align=(:right,:bottom))
    text!(ax, .91, counts["off"][20]+2, text="gate off: $(high["off"])/60 correct", fontsize=9,
          color=INK, align=(:right,:bottom))
    text!(ax, .5, 30, text="no intermediate outcomes:\nthe regime-selection band is bimodal,\nnot graded", fontsize=8.5,
          color=INK2, align=(:center,:center))
    axislegend(ax, position=:ct)
    save(joinpath(OUT,"fig_bimodal.pdf"), f)
end


# ------------------------- Fig: race anatomy (I008) ------------------------------
function fig_race()
    d = readcsv(joinpath(RS,"race.csv"))
    f = Figure(size=(1000, 330))
    Astar04 = Astar(0.4); Astar06 = Astar(0.6)
    for (k,(rho,ttl,sub)) in enumerate([(0.002,"trapped (ρ = 0.002 < ρ_c)",
                                         "the gate absorbs while aspiration has barely moved"),
                                        (0.02,"rescued (ρ = 0.02 > ρ_c)",
                                         "fast adaptation keeps the gate ajar: correction arrives, then repair")])
        ax = Axis(f[1,k], xlabel="trial", ylabel=(k==1 ? "community-2 mean" : ""),
                  title=ttl, subtitle=sub, limits=(0,600,-.02,1.02))
        idx = abs.(d["rho"].-rho).<1e-9
        t = Float64.(d["t"][idx]); o = sortperm(t); t=t[o]
        m2 = Float64.(d["m2"][idx][o]); l2 = Float64.(d["l2"][idx][o]); a2 = Float64.(d["a2"][idx][o])
        hlines!(ax, [Astar04], color=VER, linestyle=:dot, linewidth=1.3)
        hlines!(ax, [Astar06], color=(VER,.55), linestyle=:dot, linewidth=1.1)
        text!(ax, 597, Astar04-.03, text="A*(μ₂)", fontsize=8.5, color=VER, align=(:right,:top))
        text!(ax, 597, Astar06+.02, text="A*(μ₁)", fontsize=8.5, color=(VER,.75), align=(:right,:bottom))
        lines!(ax, t, a2, color=BLU, linewidth=2, linestyle=:dash)
        lines!(ax, t, l2, color=VER, linewidth=2)
        lines!(ax, t, m2, color=INK, linewidth=1.6)
        if k==1
            text!(ax, 300, a2[150]+.05, text="aspiration Ā₂", fontsize=8.5, color=BLU, align=(:center,:bottom))
            text!(ax, 300, l2[150]+.045, text="legitimacy L̄₂", fontsize=8.5, color=VER, align=(:center,:bottom))
            text!(ax, 300, .035, text="optimal mass m₂", fontsize=8.5, color=INK, align=(:center,:bottom))
            text!(ax, 592, .965, text="modal fate: 84% of runs\n(unselected draws: Supp. Fig. 7)",
                  fontsize=7.5, color=INK2, align=(:right,:top))
        else
            text!(ax, 250, a2[125]+.055, text="aspiration Ā₂", fontsize=8.5, color=BLU, align=(:center,:bottom))
            text!(ax, 250, .835, text="legitimacy L̄₂", fontsize=8.5, color=VER, align=(:center,:top))
            text!(ax, 135, .97, text="optimal mass m₂", fontsize=8.5, color=INK, align=(:left,:center))
        end
    end
    for (i,l) in enumerate(["a","b"]); panel!(f,(1,i),l); end
    save(joinpath(OUT,"fig_race.pdf"), f)
end

# --------------- Fig: predictions for the preregistered task (I008) --------------
function fig_pred()
    d = readcsv(joinpath(RS,"pred_series.csv"))
    ags = strip.(string.(d["agent"])); rgs = strip.(string.(d["regime"]))
    rss = strip.(string.(d["resto"]))
    sel(a,r,rs) = (ags.==a).&(rgs.==r).&(rss.==rs)
    gett(i) = (t=Float64.(d["t"][i]); o=sortperm(t);
               (t[o], Float64.(d["trust_m"][i][o]), Float64.(d["trust_q1"][i][o]),
                Float64.(d["trust_q3"][i][o]), Float64.(d["acc_m"][i][o])))
    f = Figure(size=(1000, 640))
    function phases!(ax)
        vspan!(ax, 150, 300, color=(INK,.055))
        vlines!(ax, [300], color=(INK,.25), linewidth=.8)
        text!(ax, 75, 103, text="P1 rich", fontsize=8, color=INK2, align=(:center,:bottom))
        text!(ax, 225, 103, text="P2 deprivation", fontsize=8, color=INK2, align=(:center,:bottom))
        text!(ax, 375, 103, text="P3 restoration", fontsize=8, color=INK2, align=(:center,:bottom))
    end
    # --- a: dissonance agent -------------------------------------------------------
    ax1 = Axis(f[1,1], xlabel="trial", ylabel="predicted fairness rating",
               title="dissonance: comparison drives the drop", limits=(0,450,0,112))
    phases!(ax1)
    for (r,ls) in [("HIGH",:solid),("LOW",:dash)]
        t,m,q1,q3,_ = gett(sel("diss",r,"FULL"))
        band!(ax1, t, q1, q3, color=(VER, r=="HIGH" ? .16 : .08))
        lines!(ax1, t, m, color=VER, linewidth=2, linestyle=ls)
    end
    text!(ax1, 252, 9, text="HIGH reference", fontsize=8.5, color=VER, align=(:center,:center))
    text!(ax1, 310, 88, text="LOW reference", fontsize=8.5, color=VER, align=(:left,:center))
    # --- b: Bayesian rival ----------------------------------------------------------
    ax2 = Axis(f[1,2], xlabel="trial", ylabel="predicted trust (π_fair)",
               title="rivals: the hypothesis class decides", limits=(0,450,0,112))
    phases!(ax2)
    for (r,ls) in [("HIGH",:solid),("LOW",:dash)]
        t,m,q1,q3,_ = gett(sel("rival",r,"FULL"))
        band!(ax2, t, q1, q3, color=(BLU, r=="HIGH" ? .14 : .08))
        lines!(ax2, t, m, color=BLU, linewidth=2, linestyle=ls)
    end
    tu,mu,q1u,q3u,_ = gett(sel("rival_us","HIGH","FULL"))
    band!(ax2, tu, q1u, q3u, color=(SKY,.14))
    lines!(ax2, tu, mu, color=SKY, linewidth=2, linestyle=:dashdot)
    # I014: aspiration-in-utility rival (the class implicated in the identification
    # confusion) — partial, reference-ordered drop with fast full recovery
    ta,ma,_,_,_ = gett(sel("rival_au","HIGH","FULL"))
    lines!(ax2, ta, ma, color=ORA, linewidth=2, linestyle=:dot)
    text!(ax2, 236, 68, text="aspiration-in-utility:\npartial drop, fast recovery", fontsize=8,
          color=ORA, align=(:center,:top))
    text!(ax2, 105, 86, text="group-contingent: no drop\n(own P1 evidence banked)", fontsize=8,
          color=SKY, align=(:center,:center))
    text!(ax2, 371, 84, text="global rig, HIGH: peer success\ndefeats the hypothesis", fontsize=8,
          color=BLU, align=(:center,:center))
    text!(ax2, 320, 40, text="LOW: self-confirming\ncollapse (trust and learning)", fontsize=8,
          color=BLU, align=(:center,:center))
    # --- c: P3 behaviour vs belief (H2) and restoration level (H3) ------------------
    ax3 = Axis(f[2,1], xlabel="trial (P3)", ylabel="per cent",
               title="restoration: behaviour heals, belief lags", limits=(300,450,0,112))
    t,m,_,_,acc = gett(sel("diss","HIGH","FULL"))
    p3 = t .>= 300
    lines!(ax3, t[p3], 100 .* acc[p3], color=INK, linewidth=1.8)
    lines!(ax3, t[p3], m[p3], color=VER, linewidth=2)
    t2,m2v,_,_,_ = gett(sel("diss","HIGH","MODERATE"))
    lines!(ax3, t2[p3], m2v[p3], color=VER, linewidth=2, linestyle=:dash)
    # I014: the aspiration-in-utility rival recovers fully at either restoration level
    tam,mam,_,_,_ = gett(sel("rival_au","HIGH","MODERATE"))
    lines!(ax3, tam[p3], mam[p3], color=ORA, linewidth=1.8, linestyle=:dot)
    text!(ax3, 352, 103, text="choice accuracy (fast)", fontsize=8.5, color=INK, align=(:left,:center))
    text!(ax3, 428, 80, text="utility rival: recovers even\nat moderate restoration", fontsize=8,
          color=ORA, align=(:right,:center))
    text!(ax3, 390, 55, text="fairness, full restoration\n(slow 1/ρ clock)", fontsize=8, color=VER, align=(:center,:center))
    text!(ax3, 383, 26, text="fairness, moderate restoration:\ntoo little, too late", fontsize=8, color=VER, align=(:center,:center))
    # --- d: increment asymmetry (H4) -------------------------------------------------
    h = readcsv(joinpath(RS,"pred_h4.csv"))
    hag = strip.(string.(h["agent"]))
    ax4 = Axis(f[2,2], xlabel="entitlement shortfall over rating interval",
               ylabel="Δ rating per interval", title="asymmetric updating of fairness")
    hlines!(ax4, [0], color=GRY, linewidth=.9)
    for (a,col,lab) in [("diss",VER,"dissonance"),("rival",BLU,"rival")]
        i = hag.==a
        b = Float64.(h["bin"][i]); v = Float64.(h["dtrust_m"][i])
        # pool duplicate bins across conditions, weighted by n
        n = Float64.(h["n"][i]); ub = sort(unique(b))
        vm = [sum(v[b.==x].*n[b.==x])/sum(n[b.==x]) for x in ub]
        lines!(ax4, ub, vm, color=col, linewidth=2)
        scatter!(ax4, ub, vm, color=col, markersize=7)
        text!(ax4, ub[end]+.012, vm[end], text=lab, fontsize=8.5, color=col, align=(:left,:center))
    end
    text!(ax4, .03, 4.6, text="repair capped at ν_R", fontsize=8, color=VER, align=(:left,:center))
    text!(ax4, .485, -3.1, text="graded erosion", fontsize=8, color=VER, align=(:left,:center))
    xlims!(ax4, -.02, .62)
    for (k,l) in enumerate(["b","c","d","e"])
        gr, gc = divrem(k-1, 2) .+ (1, 1); panel!(f,(gr,gc),l)
    end
    save(joinpath(OUT,"fig_pred.pdf"), f)
end


# ---------------- Fig: attractor flow charts per regime (I012 rebuild) -----------
# Pure theory: integral curves of the closed-form map; no simulation.
function flow_traj(mu, Ainf, a0, l0; rho=0.004, nmax=9000)
    a, l = a0, l0; ta = Float64[a]; tl = Float64[l]
    for _ in 1:nmax
        l = clamp(l + drift(mu, a), 0, 1)
        a = clamp(a + rho*(Ainf - a), 0, 1)
        push!(ta, a); push!(tl, l)
        if abs(a - Ainf) < 2e-3 && (l > 0.995 || l < 0.005); break; end
    end
    ta, tl
end

function arrowheads!(ax, ta, tl, col; fracs=(0.18, 0.55), size=9)
    n = length(ta)
    # arc-length parameterization so heads sit on visible path, not time
    seg = [hypot(ta[i+1]-ta[i], tl[i+1]-tl[i]) for i in 1:n-1]
    cs = cumsum(seg); tot = cs[end]
    for fr in fracs
        i = findfirst(x -> x >= fr*tot, cs)
        (i === nothing || i >= n) && continue
        dx, dy = ta[i+1]-ta[i], tl[i+1]-tl[i]
        hypot(dx,dy) < 1e-9 && continue
        scatter!(ax, [ta[i]], [tl[i]], marker=:rtriangle, markersize=size,
                 color=col, rotation=atan(dy, dx))
    end
end

function fig_flow()
    f = Figure(size=(1000, 680))
    cells = [
        ("legitimate consensus", BLU,  0.6, 0.6,  :stable,
         "superior arm, A∞ < A*(μ₁): every flow reaches repair"),
        ("credulous error", SKY, 0.4, 0.4,  :stable,
         "isolated: aspiration adapts to poverty, trust survives"),
        ("defensive wrong consensus", VER, 0.4, 0.52, :stable,
         "anchored to visible winners, A∞ > A*(μ₂): every flow is absorbed"),
        ("correct but illegitimate", ORA, 0.6, 0.6,  :meta,
         "entered from the trap: metastable transit, then repair"),
    ]
    for (k,(ttl, col, mu, Ainf, stab, sub)) in enumerate(cells)
        as = Astar(mu)
        gr, gc = divrem(k-1, 2) .+ (1, 1)
        ax = Axis(f[gr, gc], xlabel=(gr==2 ? "aspiration A" : ""),
                  ylabel=(gc==1 ? "legitimacy L" : ""),
                  title=ttl, subtitle=sub, limits=(0,1,-0.03,1.05))
        vspan!(ax, 0, as, color=(BLU,.05)); vspan!(ax, as, 1, color=(VER,.055))
        # nullclines
        vlines!(ax, [as], color=VER, linestyle=:dash, linewidth=1.6)
        vlines!(ax, [Ainf], color=INK, linestyle=:dot, linewidth=1.2)
        if stab == :stable
            # fate-coloured integral curves from a grid of initial states
            fate = Ainf < as ? BLU : VER
            Lstar = Ainf < as ? 1.0 : 0.0
            for a0 in 0.06:0.115:0.98, l0 in (0.14, 0.86)
                ta, tl = flow_traj(mu, Ainf, a0, l0)
                lines!(ax, ta, tl, color=(fate,.5), linewidth=1.1)
                arrowheads!(ax, ta, tl, (fate,.85))
            end
            # slow manifold guide (neutral grey everywhere so it matches the key)
            if Lstar == 1.0
                lines!(ax, [0.02, as], [1.0,1.0], color=(INK,.30), linewidth=5)
            else
                lines!(ax, [as, 0.985], [0.0,0.0], color=(INK,.30), linewidth=5)
            end
            scatter!(ax, [Ainf],[Lstar], color=col, markersize=16, marker=:circle,
                     strokecolor=:white, strokewidth=2)
            if Lstar == 1.0
                text!(ax, Ainf-.04, .92, text="stable", fontsize=8.5, font=:bold,
                      color=col, align=(:right,:center))
            else
                text!(ax, Ainf+.05, .12, text="stable", fontsize=8.5, font=:bold,
                      color=col, align=(:left,:center))
            end
        else
            # panel d: phase-coloured transits from the trap corner
            for (a0,l0) in ((.97,.02),(.88,.07),(.80,.03),(.92,.13),(.74,.015))
                ta, tl = flow_traj(mu, Ainf, a0, l0)
                phase = findfirst(x -> x > 0.5, tl)
                phase === nothing && (phase = length(tl))
                lines!(ax, ta[1:phase], tl[1:phase], color=(ORA,.75), linewidth=1.6)
                lines!(ax, ta[phase:end], tl[phase:end], color=(BLU,.55), linewidth=1.2)
                arrowheads!(ax, ta[1:phase], tl[1:phase], (ORA,.95))
                arrowheads!(ax, ta[phase:end], tl[phase:end], (BLU,.85), fracs=(0.5,))
            end
            lines!(ax, [as, 0.985], [0.0,0.0], color=(INK,.30), linewidth=5)
            text!(ax, .975, .225, text="metastable channel", fontsize=8.5, font=:bold,
                  color=ORA, align=(:right,:bottom))
            text!(ax, .975, .185, text="transit ≈ 1/ρ", fontsize=8, color=ORA,
                  align=(:right,:bottom))
            scatter!(ax, [Ainf],[1.0], color=BLU, markersize=16, marker=:circle,
                     strokecolor=:white, strokewidth=2)
            text!(ax, Ainf-.035, .92, text="eventual attractor", fontsize=8.5,
                  font=:bold, color=BLU, align=(:right,:center))
        end
        tx = k==3 ? as-.025 : as+.025
        text!(ax, tx, .56, text="A*", fontsize=9.5, color=VER,
              align=(k==3 ? :right : :left,:center))
        text!(ax, Ainf + (k==3 ? .025 : -.025), .36, text="A∞", fontsize=9.5, color=INK,
              align=(k==3 ? :left : :right,:center))
    end
    for (k,l) in enumerate(["a","b","c","d"])
        gr, gc = divrem(k-1, 2) .+ (1, 1); panel!(f,(gr,gc),l)
    end
    Legend(f[3, 1:2],
        [[LineElement(color=BLU, linewidth=2),
          LineElement(color=VER, linewidth=2),
          LineElement(color=ORA, linewidth=2)],
         [LineElement(color=(INK,.30), linewidth=5),
          LineElement(color=VER, linewidth=1.6, linestyle=:dash),
          LineElement(color=INK, linewidth=1.2, linestyle=:dot),
          MarkerElement(marker=:circle, color=(INK,.75), strokecolor=:white,
                        strokewidth=1.5, markersize=12)],
         [PolyElement(color=(BLU,.15)),
          PolyElement(color=(VER,.15))]],
        [["repair (L → 1)",
          "absorption (L → 0)",
          "metastable transit (panel d)"],
         ["attracting slow manifold",
          "A*(μ) — gate threshold",
          "A∞ — aspiration rest point",
          "stable attractor"],
         ["left of A*: trust repairs",
          "right of A*: gate engaged"]],
        ["trajectories — colour gives the destination", "landmarks", "background shading"],
        orientation=:horizontal, nbanks=2, framevisible=false, labelsize=9,
        titlesize=9, titlefont=:bold, titlegap=3, groupgap=26,
        patchsize=(22,10), colgap=14, rowgap=2, tellheight=true)
    rowgap!(f.layout, 2, 6)
    save(joinpath(OUT,"fig_flow.pdf"), f)
end

# ---------------- SI Fig: finite-size and horizon scaling (I012) ------------------
function fig_scaling()
    f = Figure(size=(1180, 640))
    d = readcsv(joinpath(RS,"fss.csv"))
    Ns = [50,100,200,400,800,1600]
    ramp = cgrad([RGBf(.75,.84,.92), RGBf(.08,.28,.48)], 6, categorical=true)
    ax1 = Axis(f[1,1], xlabel="initial entitlement A₀", ylabel="P(defensive wrong)",
               title="the front narrows with population size")
    widths = Float64[]; peaks = Float64[]
    for (k,n) in enumerate(Ns)
        idx = d["n"].==n
        a = Float64.(d["a0"][idx]); o = sortperm(a)
        p = Float64.(d["p_dw"][idx][o])
        lines!(ax1, a[o], p, color=ramp[k], linewidth=2)
        inb = findall(x-> .1 <= x <= .9, p)
        push!(widths, length(inb)>0 ? a[o][inb[end]]-a[o][inb[1]] + .01 : .01)
        push!(peaks, maximum(Float64.(d["var_m2"][idx])))
        text!(ax1, .582, .97-.065*k, text="N = $n", fontsize=8, color=ramp[k], align=(:left,:center))
    end
    ax2 = Axis(f[1,2], xlabel="population size N", ylabel="front width (A₀)",
               title="width shrinks; variance peak stays bounded",
               xscale=log10, yscale=log10)
    scatterlines!(ax2, Float64.(Ns), widths, color=INK, markersize=8, linewidth=1.6)
    nn = [50.0, 1600.0]
    lines!(ax2, nn, widths[2].*sqrt.(Ns[2]./nn), color=(VER,.6), linestyle=:dash, linewidth=1.4)
    text!(ax2, 700, .055, text="∝ N^(−1/2)", fontsize=9, color=VER, align=(:left,:center))
    ax2b = Axis(f[1,2], yaxisposition=:right, ylabel="variance peak", xscale=log10,
                limits=(40,2000,0,.3), xticksvisible=false, xticklabelsvisible=false,
                xgridvisible=false, ygridvisible=false)
    hidespines!(ax2b, :l, :t, :b)
    scatterlines!(ax2b, Float64.(Ns), peaks, color=BLU, markersize=7, linewidth=1.4,
                  linestyle=:dot)
    text!(ax2b, 60, .27, text="variance peak (bounded)", fontsize=8.5, color=BLU, align=(:left,:center))
    t = readcsv(joinpath(RS,"tsweep.csv"))
    ax3 = Axis(f[1,3], xlabel="horizon T (trials)", ylabel="collapse boundary ρ*(T)",
               title="persistence is horizon-indexed", xscale=log10, yscale=log10,
               limits=(400, 20000, 5e-4, 1e-2))
    bs = Float64[]; Ts = [600,2400,9600]
    for tt in Ts
        idx = t["t"].==tt
        r = Float64.(t["rho"][idx]); o = sortperm(r)
        p = Float64.(t["p_persist"][idx][o])
        i5 = findlast(x->x>=.5, p)
        push!(bs, i5 === nothing ? NaN : (i5 == length(p) ? r[o][end] :
              r[o][i5] + (r[o][i5+1]-r[o][i5])*(p[i5]-.5)/(p[i5]-p[i5+1])))
    end
    scatterlines!(ax3, Float64.(Ts[1:2]), bs[1:2], color=INK, markersize=9, linewidth=1.6)
    scatter!(ax3, [Float64(Ts[3])], [1e-3], marker=:dtriangle, color=INK, markersize=10)
    text!(ax3, 9600, 1.25e-3, text="≤ grid floor", fontsize=8, color=INK2, align=(:right,:bottom))
    tt2 = [500.0, 15000.0]
    lines!(ax3, tt2, 2.9*600 ./ tt2 ./ 600, color=(VER,.6), linestyle=:dash, linewidth=1.4)
    text!(ax3, 3000, 1.6e-3, text="∝ 1/T (escape on the\naspiration clock)", fontsize=8.5,
          color=VER, align=(:left,:center))
    hlines!(ax3, [0.00641], color=BLU, linestyle=:dot, linewidth=1.4)
    text!(ax3, 480, .0069, text="ρ_c (absorption)", fontsize=8.5, color=BLU, align=(:left,:bottom))
    # ---- d (I014): front extrapolation vs deterministic basin boundary ----------
    ax4 = Axis(f[2,1], xlabel="N^(−1/2)", ylabel="front location A₀*(N)",
               title="the front extrapolated against the deterministic boundary",
               subtitle="residual offset 0.025 = the community map's homogeneity error")
    fronts = Float64[]; nsq = Float64[]
    for n in Ns
        idx = d["n"].==n
        a = Float64.(d["a0"][idx]); o = sortperm(a)
        pv = Float64.(d["p_dw"][idx][o]); av = a[o]
        i5 = findfirst(x->x>=.5, pv)
        if i5 !== nothing && i5 > 1
            x0 = av[i5-1] + (av[i5]-av[i5-1])*(.5-pv[i5-1])/(pv[i5]-pv[i5-1])
            push!(fronts, x0); push!(nsq, 1/sqrt(n))
        end
    end
    scatter!(ax4, nsq, fronts, color=INK, markersize=9)
    X = hcat(ones(length(nsq)), nsq); bho = X \ fronts
    xs = [0.0, maximum(nsq)*1.06]
    lines!(ax4, xs, bho[1] .+ bho[2].*xs, color=(INK,.5), linewidth=1.4)
    mfb75 = mf_dw_boundary_a0(0.75)
    hlines!(ax4, [mfb75], color=VER, linestyle=:dash, linewidth=1.6)
    text!(ax4, 0.004, mfb75, text="deterministic basin boundary (S5 map)",
          fontsize=8.5, color=VER, align=(:left,:bottom))
    text!(ax4, 0.004, bho[1], text="extrapolated A₀*(∞) = $(round(bho[1], digits=3))",
          fontsize=8.5, color=INK, align=(:left,:top))
    # ---- e (I014): second cut — persistence front in χ sharpens with N ----------
    d2 = readcsv(joinpath(RS,"fss2.csv"))
    Ns2 = [50,100,200,400,800]
    ramp2 = cgrad([RGBf(.75,.84,.92), RGBf(.08,.28,.48)], 5, categorical=true)
    ax5 = Axis(f[2,2], xlabel="social anchoring χ", ylabel="P(persist to T = 600)",
               title="same selection mechanism in the (ρ, χ) plane",
               subtitle="ρ = 0.005; escape is a finite-size fluctuation")
    for (k,n) in enumerate(Ns2)
        idx = d2["n"].==n
        c = Float64.(d2["chi"][idx]); o = sortperm(c)
        pv = Float64.(d2["p_persist"][idx][o])
        lines!(ax5, c[o], pv, color=ramp2[k], linewidth=2)
        text!(ax5, 1.005, pv[end], text="N = $n", fontsize=7.5, color=ramp2[k],
              align=(:left,:center))
    end
    xlims!(ax5, 0, 1.17)
    # ---- f (I014): direct test of rho_c — absorption probability ----------------
    da = readcsv(joinpath(RS,"absorb.csv"))
    ax6 = Axis(f[2,3], xlabel="aspiration adaptation ρ (log)", ylabel="P(absorbed)",
               title="the race, measured directly", xscale=log10,
               subtitle="single agent: L reaches the floor before A crosses A*")
    rr = Float64.(da["rho"]); o = sortperm(rr)
    pv = Float64.(da["p_absorb"][o])
    wl = [wilson(round(Int, p*400), 400) for p in pv]
    band!(ax6, rr[o], [w[1] for w in wl], [w[2] for w in wl], color=(INK,.15))
    scatterlines!(ax6, rr[o], pv, color=INK, markersize=7, linewidth=1.8)
    vlines!(ax6, [0.00641], color=VER, linestyle=:dash, linewidth=1.6)
    text!(ax6, .00655, .78, text="ρ_c = 0.0064", fontsize=8.5, color=VER, align=(:left,:center))
    i5 = findlast(x->x>=.5, pv)
    rx = rr[o][i5] + (rr[o][i5+1]-rr[o][i5])*(pv[i5]-.5)/(pv[i5]-pv[i5+1])
    vlines!(ax6, [rx], color=INK, linestyle=:dot, linewidth=1.2)
    text!(ax6, .00285, .30, text="crossover $(round(rx, digits=4))\n(+$(Int(round(100*(rx/0.00641-1))))% finite-step\nfluctuation correction)",
          fontsize=8, color=INK, align=(:left,:center))
    for (k,l) in enumerate(["a","b","c","d","e","f"])
        gr, gc = divrem(k-1, 3) .+ (1, 1); panel!(f,(gr,gc),l)
    end
    save(joinpath(OUT,"fig_scaling.pdf"), f)
end

# ---------------- SI Fig (I014): robustness battery -------------------------------
function wilson(k, n; z=1.959964)
    p = k/n; d = 1 + z^2/n; c = p + z^2/(2n); h = z*sqrt(p*(1-p)/n + z^2/(4n^2))
    ((c-h)/d, (c+h)/d)
end

function fig_robust()
    f = Figure(size=(1000, 360))
    # a: repair-ratio neighbourhood
    d = readcsv(joinpath(RS,"nfsweep.csv"))
    ax1 = Axis(f[1,1], xlabel="repair ratio ν_R/ν_F", ylabel="P(defensive wrong)",
               title="the trap plateau in the repair ratio",
               subtitle="confirmatory cell; frozen default marked", limits=(.07,.53,-.04,1.08))
    r = Float64.(d["ratio"]); o = sortperm(r)
    pv = Float64.(d["p_dw"][o])
    wl = [wilson(round(Int, p*60), 60) for p in pv]
    band!(ax1, r[o], [w[1] for w in wl], [w[2] for w in wl], color=(VER,.15))
    scatterlines!(ax1, r[o], pv, color=VER, markersize=8, linewidth=2)
    vlines!(ax1, [0.25], color=INK, linestyle=:dot, linewidth=1.2)
    text!(ax1, .245, .5, text="frozen default", fontsize=8.5, color=INK, align=(:right,:center))
    text!(ax1, .33, .88, text="repair outruns erosion:\nA*(0.6) crosses the anchor", fontsize=8,
          color=INK2, align=(:left,:center))
    # b: field-form and structural variants
    dv = readcsv(joinpath(RS,"fieldform.csv")); dt = readcsv(joinpath(RS,"topo.csv"))
    labs = ["frozen cell", "unweighted field", "retrospective off (η = 0)", "both",
            "losing community 60/140", "losing community 140/60",
            "heterogeneous Γᵢ ∈ {0, 0.2}", "payoff-biased imitation"]
    vals = [0.843,
            Float64(dv["p_dw"][findfirst(strip.(string.(dv["variant"])).=="unweighted")]),
            Float64(dv["p_dw"][findfirst(strip.(string.(dv["variant"])).=="eta0")]),
            Float64(dv["p_dw"][findfirst(strip.(string.(dv["variant"])).=="both")]),
            Float64(dt["p_dw"][findfirst(strip.(string.(dt["variant"])).=="losing_small_60")]),
            Float64(dt["p_dw"][findfirst(strip.(string.(dt["variant"])).=="losing_large_140")]),
            Float64(dt["p_dw"][findfirst(strip.(string.(dt["variant"])).=="gamma_het")]),
            Float64(dt["p_dw"][findfirst(strip.(string.(dt["variant"])).=="paybias")])]
    ns = [300, 60, 60, 60, 60, 60, 60, 60]
    ax2 = Axis(f[1,2], xlabel="P(defensive wrong) at the confirmatory cell",
               title="where the trap lives — and where it does not",
               yticks=(1:8, labs), yreversed=true, limits=(-.05,1.1,nothing,nothing),
               yticklabelsize=8.5)
    for (k,(v,n)) in enumerate(zip(vals, ns))
        wlo, whi = wilson(round(Int, v*n), n)
        lines!(ax2, [wlo, whi], [k, k], color=(k<=6 ? VER : BLU, .5), linewidth=3)
        scatter!(ax2, [v], [k], color=(k<=6 ? VER : BLU), markersize=9,
                 strokecolor=:white, strokewidth=1)
    end
    text!(ax2, .56, 7.5, text="the trap needs conformist weighting\nand uniformly weak outside exposure",
          fontsize=8, color=BLU, align=(:center,:center))
    for (i,l) in enumerate(["a","b"]); panel!(f,(1,i),l); end
    save(joinpath(OUT,"fig_robust.pdf"), f)
end

# ---------------- SI Fig (I014): unselected race trajectories ---------------------
function fig_race3()
    d = readcsv(joinpath(RS,"race3.csv"))
    f = Figure(size=(1000, 300))
    for (k,seed) in enumerate([38001, 38011, 38021])
        idx = d["seed"].==seed
        t = Float64.(d["t"][idx]); o = sortperm(t)
        ax = Axis(f[1,k], xlabel="trial", ylabel=(k==1 ? "losing-community mean" : ""),
                  title="seed $(seed)" * (seed==38021 ? " (shown in Fig. 7)" : " (escape draw)"),
                  limits=(0,600,-.02,1.05))
        lines!(ax, t[o], Float64.(d["m2"][idx][o]), color=INK, linewidth=1.8)
        lines!(ax, t[o], Float64.(d["l2"][idx][o]), color=VER, linewidth=1.8)
        lines!(ax, t[o], Float64.(d["a2"][idx][o]), color=BLU, linewidth=1.6, linestyle=:dash)
        if k == 1
            text!(ax, 300, .93, text="optimal mass m₂", fontsize=8.5, color=INK, align=(:left,:center))
            text!(ax, 395, .30, text="legitimacy L̄₂", fontsize=8.5, color=VER, align=(:left,:center))
            text!(ax, 430, .60, text="aspiration Ā₂", fontsize=8.5, color=BLU, align=(:left,:center))
        end
    end
    for (i,l) in enumerate(["a","b","c"]); panel!(f,(1,i),l); end
    save(joinpath(OUT,"fig_race3.pdf"), f)
end

# ---------------- SI Fig: mean-field map vs ABM bands (I012) ----------------------
function mf_map(rho; T=600, lam=0.7, a0=0.8, chi=0.4, gam=0.1)
    # deterministic community map of Lemmas S5.1-S5.3 (homogeneous limit)
    mu = [0.6, 0.4]; eta=0.2; alpha=0.2; kb=12.0
    nuF, nuR, tauF, phm, php = 0.05, 0.0125, 0.3, 1.0, 0.25
    B = [1-gam gam; gam 1-gam]
    Q = [0.62 0.38; 0.38 0.62]   # community x arm
    L = [1.0, 1.0]; A = [a0, a0]; m = [0.62, 0.38]
    Sprev = zeros(2,2)
    out = zeros(T, 3)
    for t in 1:T
        mm = zeros(2); Cc = zeros(2)
        for c in 1:2
            dV = Q[c,1]-Q[c,2] + lam*(Sprev[c,1]-Sprev[c,2])
            mm[c] = 1/(1+exp(-kb*dV)); Cc[c] = abs(2*mm[c]-1)
        end
        r = [mm[c]*mu[1] + (1-mm[c])*mu[2] for c in 1:2]
        pop = (r[1]+r[2])/2
        phi = [Cc[c]*(a==1 ? mm[c] : 1-mm[c]) for c in 1:2, a in 1:2]
        S = B*phi
        wj = [Cc[c]*(a==1 ? mm[c] : 1-mm[c]) for c in 1:2, a in 1:2]
        uj = [wj[c,a]*mu[a] for c in 1:2, a in 1:2]
        e = B*wj; ob = B*uj
        for c in 1:2
            for a in 1:2
                vis = a==1 ? mm[c] : 1-mm[c]
                delta = mu[a]-Q[c,a]
                soc = ob[c,a]-e[c,a]*Q[c,a]
                Q[c,a] = clamp(Q[c,a] + alpha*L[c]*vis*delta + eta*L[c]*soc, 0, 1)
            end
            p1 = r[c]
            dD = (1-p1)*max(phm*A[c]-tauF,0) + p1*max(php*(1-A[c])-tauF,0)
            dK = (1-p1)*(phm*A[c]<=tauF ? 1.0 : 0.0) + p1*(php*(1-A[c])<=tauF ? 1.0 : 0.0)
            L[c] = clamp(L[c] - nuF*dD + nuR*dK, 0, 1)
            A[c] = clamp((1-rho)*A[c] + rho*((1-chi)*r[c] + chi*pop), 0, 1)
        end
        Sprev = S
        out[t,:] .= (mm[2], L[2], A[2])
    end
    out
end

# ---- I014 deterministic-map helpers (no simulation) ------------------------------
function mf_terminal(; rho=0.002, lam=0.7, a0=0.8, gam=0.1, T=600)
    o = mf_map(rho; T=T, lam=lam, a0=a0, gam=gam)
    (mean(o[T-49:T,1]), mean(o[T-49:T,2]))
end
mf_isdw(; kw...) = (x = mf_terminal(; kw...); x[1] < 0.3 && x[2] < 0.3)
function mf_dw_boundary_a0(lam; gam=0.1, lo=0.45, hi=0.90)
    mf_isdw(lam=lam, gam=gam, a0=hi) || return NaN
    mf_isdw(lam=lam, gam=gam, a0=lo) && return lo
    for _ in 1:36
        mid = (lo + hi) / 2
        mf_isdw(lam=lam, gam=gam, a0=mid) ? (hi = mid) : (lo = mid)
    end
    (lo + hi) / 2
end
function mf_regclass(a0, gam; lam=0.7)
    m2, l2 = mf_terminal(lam=lam, a0=a0, gam=gam)
    if m2 > 0.7 && l2 > 0.5; 1.0        # legitimate
    elseif m2 < 0.3 && l2 < 0.3; 2.0    # defensive wrong
    elseif m2 < 0.3 && l2 > 0.5; 3.0    # credulous
    elseif m2 > 0.7 && l2 < 0.3; 4.0    # correct-but-illegitimate
    else; 0.0 end                       # mixed / between
end

function fig_mfcheck()
    d = readcsv(joinpath(RS,"mfband.csv"))
    f = Figure(size=(1000, 330))
    for (k,rho) in enumerate([0.002, 0.02])
        ax = Axis(f[1,k], xlabel="trial", ylabel=(k==1 ? "community-2 mean" : ""),
                  title=(k==1 ? "trapped cell (ρ = 0.002)" : "rescued cell (ρ = 0.02)"),
                  subtitle="bands: ABM mean ± s.d. over 20 runs · lines: deterministic map",
                  limits=(0,600,-.02,1.02))
        idx = abs.(d["rho"].-rho).<1e-9
        t = Float64.(d["t"][idx]); o = sortperm(t); t=t[o]
        for (col, mkey, skey) in [(INK,"m2_m","m2_s"), (VER,"l2_m","l2_s"), (BLU,"a2_m","a2_s")]
            mval = Float64.(d[mkey][idx][o]); sval = Float64.(d[skey][idx][o])
            band!(ax, t, clamp.(mval .- sval, 0, 1), clamp.(mval .+ sval, 0, 1), color=(col,.18))
        end
        mf = mf_map(rho)
        ts = 1:600
        lines!(ax, ts, mf[:,1], color=INK, linewidth=1.8)
        lines!(ax, ts, mf[:,2], color=VER, linewidth=1.8)
        lines!(ax, ts, mf[:,3], color=BLU, linewidth=1.8, linestyle=:dash)
        if k==1
            text!(ax, 420, .80, text="aspiration Ā₂", fontsize=8.5, color=BLU, align=(:left,:center))
            text!(ax, 420, .17, text="legitimacy L̄₂", fontsize=8.5, color=VER, align=(:left,:center))
            text!(ax, 420, .05, text="optimal mass m₂", fontsize=8.5, color=INK, align=(:left,:center))
        end
    end
    for (i,l) in enumerate(["a","b"]); panel!(f,(1,i),l); end
    save(joinpath(OUT,"fig_mfcheck.pdf"), f)
end

fig_theory();  println("theory ok")
fig_abm();     println("abm ok")
fig_pt1();     println("pt1 ok")
fig_pt2();     println("pt2 ok")
fig_trans();   println("transparency ok")
fig_ident();   println("ident ok")
fig_regmap();  println("regmap ok")
fig_bimodal(); println("bimodal ok")
fig_race();    println("race ok")
fig_pred();    println("pred ok")
fig_flow();    println("flow ok")
fig_scaling(); println("scaling ok")
fig_mfcheck(); println("mfcheck ok")
fig_robust();  println("robust ok")
fig_race3();   println("race3 ok")
