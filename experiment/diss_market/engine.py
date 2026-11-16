"""Task engine of the yoked ten-repetition design (KGi-DISS-I042; the basket economy with
prediction markets, KGi-DISS-I043).

Pure Python, no oTree import: everything the app shows is computed here from a format-3
schedule (experiment/tools/yoked_schedules.py), the participant's arm and the participant's
own choices. Nothing is drawn while a participant plays.

    clearing price    cap * exp(sigma * (z(u) - z(p))): u is the schedule's settlement draw and
                      p the chance that the ordered good fills, so an order fills (price at or
                      below the cap) exactly when the schedule's bit says so
    market            'will ASSET close above X?': a forecast, the evidence (a record of ten
                      trial closes, or a source's forecast), a second forecast, a bet
    own settlements   the chosen ticket's bit of the schedule, settlement by settlement
    board, HIGH       the schedule's board bits (a trader winning at the board rate)
    board, LOW        the board uniform below the participant's own trailing rate over the
                      last TRAIL settlements, clipped to [LOW_CLIP, 1 - LOW_CLIP]; .5 before
                      the first settlement (the rule of analysis/twins_I040.twins)
    rich round        both members of a pair get the schedule's rich_board
    probe             T = mean over the two pairs of (revision after the favourable record
                      minus revision after the unfavourable record), revision = post - pre
"""
import json
import math
import random
from statistics import NormalDist

_Z = NormalDist().inv_cdf
TRAIL = 15
LOW_CLIP = 0.05
U16 = 65536
HIGH_BAND = (0.65, 0.80)          # pool source: rate of a rich-round record shown on a HIGH board
ARMS = ('HIGH', 'LOW')


class ScheduleError(ValueError):
    pass


def load_schedules(path):
    with open(path) as f:
        obj = json.load(f)
    check_schedules(obj)
    return obj


def check_schedules(obj):
    """structural checks the app relies on (the generator's verify() checks the yoking rules)"""
    if obj.get('version') != 3:
        raise ScheduleError('the app needs a format-3 schedule file (yoked_schedules.py --format 3)')
    d = obj['design']
    n = (d['rounds_rich'] + d['rounds_deprivation']) * d['settlements_per_round']
    keys = {m['key'] for m in obj['markets']}
    if len(keys) != 4:
        raise ScheduleError('four markets are needed')
    for m in obj['markets']:
        dear = max(m['price_yes'], 100 - m['price_yes'])
        if not 0 < m['price_yes'] < 100 or d['bet_payout'] * dear / 100 > d['bet_allowance']:
            raise ScheduleError(f"market {m['key']}: a ticket would cost more than the allowance")
    ids = set()
    for s in obj['schedules']:
        if not (len(s['good']) == len(s['bad']) == len(s['board']) == n and len(s['board_u']) == len(s['settle_u']) == 4 * n):
            raise ScheduleError(f"schedule {s['id']}: wrong length")
        if len(s['starts']) != d['rounds_rich'] + d['rounds_deprivation'] or len(s['probe']) != 4:
            raise ScheduleError(f"schedule {s['id']}: starts or markets missing")
        if {p['market'] for p in s['probe']} != keys or any(p['evidence'] not in ('record', 'source') for p in s['probe']):
            raise ScheduleError(f"schedule {s['id']}: markets or evidence types wrong")
        ids.add(s['id'])
    slots = [a['slot'] for a in obj['allocation']]
    if slots != list(range(len(slots))):
        raise ScheduleError('allocation slots must be 0, 1, 2, ...')
    for a in obj['allocation']:
        if a['schedule'] not in ids or a['arm'] not in ARMS:
            raise ScheduleError(f"slot {a['slot']}: unknown schedule or arm")
    return True


def n_rounds(design):
    return design['rounds_rich'] + design['rounds_deprivation']


def schedule_by_id(obj, sid):
    for s in obj['schedules']:
        if s['id'] == sid:
            return s
    raise ScheduleError(f'no schedule {sid}')


def round_slice(design, r):
    """settlement indices of market round r (0-based)"""
    k = design['settlements_per_round']
    return r * k, (r + 1) * k


def is_rich(design, r):
    return r < design['rounds_rich']


def own_bits(sched, design, r, chose_good):
    """the participant's settlements in round r: the chosen ticket's bits"""
    a, b = round_slice(design, r)
    return (sched['good'] if chose_good else sched['bad'])[a:b]


def fill_chance(design, r, chose_good):
    return (design['odds_rich'] if is_rich(design, r) else design['odds_deprivation'])[0 if chose_good else 1]


def price_path(sched, design, r, chose_good):
    """clearing prices of the ordered good in round r, in cents-rounded units. The price is an
    increasing function of the settlement draw; rounding never moves a price across the cap."""
    a, b = round_slice(design, r)
    cap, sigma = design['cap'], design['price_sigma']
    zp = _Z(fill_chance(design, r, chose_good))
    bits = own_bits(sched, design, r, chose_good)
    out = []
    for i, t in enumerate(range(a, b)):
        u = (int(sched['settle_u'][4 * t:4 * t + 4], 16) + 0.5) / U16
        price = round(cap * math.exp(sigma * (_Z(u) - zp)), 2)
        if bits[i] == '1':
            price = min(price, cap)
        else:
            price = max(price, round(cap + 0.01, 2))
        out.append(price)
    return out


def price_range(design, schedules=None):
    """(low, high) for the price axis of every chart of a session, the same in every round
    and for both goods. With the schedules of a file: the extremes of every price path a
    participant on that file can meet, with a little room; without: bounds no clearing price
    can leave."""
    cap, sigma = design['cap'], design['price_sigma']
    zmax = _Z(1 - 0.5 / U16)
    ps = list(design['odds_rich']) + list(design['odds_deprivation'])
    lo = cap * math.exp(sigma * (-zmax - max(_Z(p) for p in ps)))
    hi = cap * math.exp(sigma * (zmax - min(_Z(p) for p in ps)))
    if schedules:
        flo, fhi = cap, cap
        for s in schedules:
            for r in range(n_rounds(design)):
                for good in (True, False):
                    path = price_path(s, design, r, good)
                    flo, fhi = min(flo, min(path)), max(fhi, max(path))
        lo, hi = max(lo, flo / 1.04), min(hi, fhi * 1.04)
    return math.floor(lo * 10) / 10, math.ceil(hi * 10) / 10


def baskets(goods, design):
    """completed baskets among a number of goods"""
    return goods // design['basket_size']


def board_regime(sched, design, r, arm):
    return sched['rich_board'] if is_rich(design, r) else arm


def _u16(sched, t):
    return int(sched['board_u'][4 * t:4 * t + 4], 16)


def low_board_bits(sched, design, r, history, own):
    """LOW board in round r. history: the participant's own bits in all earlier rounds, in
    order; own: this round's own bits. The board draw at a settlement uses the own record
    BEFORE that settlement."""
    a, b = round_slice(design, r)
    if len(history) != a or len(own) != b - a:
        raise ScheduleError('own record has the wrong length for this round')
    rec = [c == '1' for c in history + own]
    out = []
    for t in range(a, b):
        last = rec[max(0, t - TRAIL):t]
        trail = 0.5 if not last else sum(last) / len(last)
        thr = min(max(trail, LOW_CLIP), 1 - LOW_CLIP)
        out.append('1' if _u16(sched, t) / U16 < thr else '0')
    return ''.join(out)


def board_bits(sched, design, r, arm, history, own):
    """board record shown in round r under the 'schedule' source"""
    if board_regime(sched, design, r, arm) == 'HIGH':
        a, b = round_slice(design, r)
        return sched['board'][a:b]
    return low_board_bits(sched, design, r, history, own)


# ------------------------------------------------------------------ pool source (real earlier records)

def check_pool(pool, design, allow_placeholder):
    if pool.get('placeholder') and not allow_placeholder:
        raise ScheduleError('this pool is a placeholder built from bot data: it is never shown to people')
    k = design['settlements_per_round']
    for s in pool['streams']:
        if len(s['bits']) != k or not 0 <= s['round'] < n_rounds(design):
            raise ScheduleError(f"pool stream {s['id']}: wrong length or round")
    return True


def pool_board(pool, design, sched, r, arm, own, seed, used=()):
    """one real earlier record for the board of round r.
    HIGH: a rich-round record whose rate lies in HIGH_BAND, not shown to this participant
    before if possible. LOW: a record of the same round whose count is nearest to the
    participant's own. Returns (stream, distance) with distance = |count - own count| under
    LOW and None under HIGH; raises if no record qualifies."""
    regime = board_regime(sched, design, r, arm)
    k = design['settlements_per_round']
    if regime == 'HIGH':
        cands = [s for s in pool['streams'] if is_rich(design, s['round'])
                 and HIGH_BAND[0] <= s['bits'].count('1') / k <= HIGH_BAND[1]]
        fresh = [s for s in cands if s['id'] not in used]
        cands = fresh or cands
        if not cands:
            raise ScheduleError('the pool holds no rich-round record in the HIGH band')
        # in the rich round both members of a pair see the same record: the key leaves the arm out
        key = f"{seed}-{sched['id']}-{r}" if is_rich(design, r) else f"{seed}-{sched['id']}-{r}-{arm}"
        return random.Random(key).choice(sorted(cands, key=lambda s: s['id'])), None
    cands = [s for s in pool['streams'] if s['round'] == r]
    if not cands:
        raise ScheduleError(f'the pool holds no record of round {r}')
    mine = own.count('1')
    dist = min(abs(s['bits'].count('1') - mine) for s in cands)
    near = sorted((s for s in cands if abs(s['bits'].count('1') - mine) == dist), key=lambda s: s['id'])
    return random.Random(f"{seed}-{sched['id']}-{r}-{arm}").choice(near), dist


# ------------------------------------------------------------------ markets

def market_of(obj, sched, i):
    """the i-th market a participant on this schedule meets: the file's market plus the
    schedule's own fields (pair, evidence, the order of the ten trial closes)"""
    tk = sched['probe'][i]
    m = next(x for x in obj['markets'] if x['key'] == tk['market'])
    return dict(m, pair=tk['pair'], evidence=tk['evidence'], cue=tk['cue'], shown=tk['shown'], index=i)


def market_closes_above(market):
    return market['score_u'] < market['chance']


BETS = ('YES', 'NO', 'PASS')


def bet_points(market, bet, design):
    """points from one market's bet. Every market comes with an allowance; a ticket costs
    payout * price / 100 (YES) or payout * (100 - price) / 100 (NO) and pays the payout if it
    wins; passing keeps the allowance."""
    if bet not in BETS:
        raise ScheduleError(f'unknown bet {bet}')
    allow, pay, price = design['bet_allowance'], design['bet_payout'], market['price_yes']
    if bet == 'PASS':
        return allow
    cost = pay * (price if bet == 'YES' else 100 - price) / 100
    won = market_closes_above(market) == (bet == 'YES')
    return int(round(allow - cost + (pay if won else 0)))


def bet_statistic(markets, bets):
    """B = mean over the two pairs of (bet on the favourable market - bet on the unfavourable
    one) / 2, with YES = 1, PASS = 0, NO = -1; markets and bets in the order met"""
    val = {'YES': 1, 'PASS': 0, 'NO': -1}
    pairs = {}
    for m, b in zip(markets, bets):
        pairs.setdefault(m['pair'], {})[m['favourable']] = val[b]
    return sum((d[True] - d[False]) / 2 for d in pairs.values()) / len(pairs)


SOURCE_BANDS = {True: (80, 100), False: (0, 20)}      # a favourable / unfavourable source's forecast


def pool_source(pool, market, seed, sched_id):
    """a real earlier forecast of this market to show as the source: inside the band, from a
    forecaster with the best record on the OTHER markets (the record never counts this
    market: counting it would tell how this market settles), as close to 90 / 10 as the pool
    allows. Both members of a pair get the same source."""
    lo, hi = SOURCE_BANDS[market['favourable']]
    target = 90 if market['favourable'] else 10
    cands = [x for x in pool.get('sources', []) if x.get('market_uid') == market['uid'] and lo <= x['forecast'] <= hi]
    if not cands:
        raise ScheduleError(f"the pool holds no forecast of market {market['key']} in the band {lo}-{hi}")
    best_track = max(x['right_others'] for x in cands)
    cands = [x for x in cands if x['right_others'] == best_track]
    dist = min(abs(x['forecast'] - target) for x in cands)
    near = sorted((x for x in cands if abs(x['forecast'] - target) == dist), key=lambda x: x['id'])
    return random.Random(f"{seed}-{sched_id}-{market['key']}").choice(near)


# ------------------------------------------------------------------ probe

def probe_pays(ticket):
    """the settlement that scores the forecasts of a probe ticket"""
    return ticket['score_u'] < ticket['chance']


def probe_T(sched, forecasts):
    """forecasts: [(pre, post), ...] in the order of sched['probe']"""
    if len(forecasts) != len(sched['probe']):
        raise ScheduleError('one (pre, post) pair per probe ticket is needed')
    pairs = {}
    for tk, (pre, post) in zip(sched['probe'], forecasts):
        pairs.setdefault(tk['pair'], {})[tk['favourable']] = post - pre
    return sum(d[True] - d[False] for d in pairs.values()) / len(pairs)


def paid_forecast(sched, forecasts):
    """(ticket index, 'pre' | 'post', forecast, outcome, prize won) for the forecast that is
    paid. Binarized quadratic scoring rule: the prize is won with probability
    1 - (outcome - forecast / 100) ** 2, decided by the schedule's lottery draw."""
    j = sched['paid_forecast']
    i, which = j // 2, ('pre', 'post')[j % 2]
    f = forecasts[i][j % 2]
    outcome = 1 if probe_pays(sched['probe'][i]) else 0
    return i, which, f, outcome, sched['prize_u'] < 1 - (outcome - f / 100) ** 2
