"""KGi-DISS-I044: the competitive benchmark of the live economy's procurement stage. Arithmetic only.

One good at one clearing: n bidders with independent values uniform on (0, 1) want one unit each, k
units are sold to the highest bids at the highest losing bid (reserve 0). Then
    expected price            (n - k) / (n + 1)             for k < n, else 0
    expected surplus a bidder k (k + 1) / (2 n (n + 1))     for k < n, else 1/2
    chance a bidder is filled min(k, n) / n
With units ~ Binomial(N, pi) per good, a split (n0, N - n0) of the N traders between the two goods is
a sorting equilibrium for a pay-off u when nobody gains by changing good:
    u0(n0) >= u1(N - n0 + 1)   and   u1(N - n0) >= u0(n0 + 1).
Two pay-offs are tabulated: expected surplus (a trader paid on surplus who knows the supply) and the
chance of a fill (what the gate kernel's traders learn from).
    python experiment/analysis/sorting_benchmark_I044.py > records/sorting_benchmark_I044.txt
"""
import numpy as np
from scipy.stats import binom

SCARCE, RICH = (0.15, 0.05), (0.55, 0.22)
FACTOR = {4: 1.15, 6: 1.10, 8: 1.05}                 # calibrated rich supply (records/market_cert_I044.txt, section 10)


def price(k, n):
    return (n - k) / (n + 1) if k < n else 0.0


def surplus(k, n):
    return k * (k + 1) / (2 * n * (n + 1)) if k < n else 0.5


def fill(k, n):
    return min(k, n) / n


def expect(f, N, pi, n):
    """expectation of f(units, n) over units ~ Binomial(N, pi); 0 for a good nobody bids for"""
    if n == 0:
        return 0.0
    return float(sum(binom.pmf(k, N, pi) * f(k, n) for k in range(N + 1)))


def equilibria(f, N, pis):
    """all splits n0 (bidders for the plentiful good) from which no single trader gains by changing good"""
    out = []
    for n0 in range(N + 1):
        n1 = N - n0
        stay0 = n0 == 0 or expect(f, N, pis[0], n0) >= expect(f, N, pis[1], n1 + 1) - 1e-12
        stay1 = n1 == 0 or expect(f, N, pis[1], n1) >= expect(f, N, pis[0], n0 + 1) - 1e-12
        if stay0 and stay1:
            out.append(n0)
    return out


def market(N, pis, n0):
    """expected fill rate, expected surplus per trader and clearing, expected prices of the two goods at a split"""
    n = (n0, N - n0)
    fr = sum(n[g] * expect(fill, N, pis[g], n[g]) for g in (0, 1)) / N
    su = sum(n[g] * expect(surplus, N, pis[g], n[g]) for g in (0, 1)) / N
    pr = tuple(expect(price, N, pis[g], n[g]) if n[g] else float('nan') for g in (0, 1))
    return fr, su, pr


if __name__ == '__main__':
    print("KGi-DISS-I044: sorting benchmark of the procurement stage (arithmetic; values uniform on (0, 1), reserve 0)")
    print("split = traders bidding for the plentiful good : for the other good\n")
    for label, base in (('scarce market (.15, .05)', SCARCE), ('rich market, calibrated', RICH)):
        print(label)
        for N in (4, 6, 8):
            pis = base if base is SCARCE else tuple(FACTOR[N] * x for x in base)
            for name, f in (('surplus', surplus), ('fill   ', fill)):
                for n0 in equilibria(f, N, pis):
                    fr, su, pr = market(N, pis, n0)
                    print(f"   {N} traders, sorting on {name}: {n0} : {N - n0}   fill rate {fr:.3f}   surplus per trader and clearing {su:.4f}"
                          f"   expected price {pr[0]:.3f} | {pr[1]:.3f}")
            best = max(range(N + 1), key=lambda n0: market(N, pis, n0)[0])
            print(f"   {N} traders, most units sold: {best} : {N - best}   fill rate {market(N, pis, best)[0]:.3f}")
        print()
