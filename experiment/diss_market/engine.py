"""Task engine of the yoked ten-repetition design (KGi-DISS-I042).

Pure Python, no oTree import: everything the app shows is computed here from a format-2
schedule (experiment/tools/yoked_schedules.py), the participant's arm and the participant's
own choices. Nothing is drawn while a participant plays.

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
import random

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
    if obj.get('version') != 2:
        raise ScheduleError('the app needs a format-2 schedule file (yoked_schedules.py --format 2)')
    d = obj['design']
    n = (d['rounds_rich'] + d['rounds_deprivation']) * d['settlements_per_round']
    ids = set()
    for s in obj['schedules']:
        if not (len(s['good']) == len(s['bad']) == len(s['board']) == n and len(s['board_u']) == 4 * n):
            raise ScheduleError(f"schedule {s['id']}: wrong length")
        if len(s['starts']) != d['rounds_rich'] + d['rounds_deprivation'] or len(s['probe']) != 4:
            raise ScheduleError(f"schedule {s['id']}: starts or probe tickets missing")
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
