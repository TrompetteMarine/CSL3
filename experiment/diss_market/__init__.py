"""
diss_market — the yoked ten-repetition design as a basket economy with prediction markets
(KGi-DISS-I042, redesigned in KGi-DISS-I043; specification experiment/YOKED_DESIGN.md,
contracts freezes/00_freeze_I042.yaml and 00_freeze_I043.yaml).

One oTree round per repetition:
  rounds 1-6    procurement rounds: Order -> Clearing -> Rate
  rounds 7-10   prediction markets: Market -> Evidence -> Bet (-> Recall)
Round 1 opens with Consent, Instructions and Quiz; round 10 closes with Closing and Results
(where the markets settle).

Everything a participant sees comes from a pre-drawn format-3 schedule file through
engine.py. The browser only displays: no outcome is computed there. No page carries a later
round, the other good's prices, a market's evidence before its first forecast, or a bet
price before the second forecast.

All wording lives in copy_en.py and is DRAFT (author-gated). Bot data from this app is for
pipeline validation only.
"""
import hashlib
import json
import os
import random

from otree.api import *

from . import copy_en as copy
from . import engine as en
from .bots_model import ModelAgent

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class C(BaseConstants):
    NAME_IN_URL = 'market'
    PLAYERS_PER_GROUP = None
    MARKET_ROUNDS = 6
    PROBE_TICKETS = 4
    NUM_ROUNDS = MARKET_ROUNDS + PROBE_TICKETS
    TICKETS = ('SQUARE', 'TRIANGLE')
    N_FAIR = 3
    STEP = 5
    BOARD_SOURCES = ('schedule', 'pool', 'none')
    PRICE_CURVES = ('own', 'both')    # which clearing prices the market screen draws (KGi-DISS-I047)
    REVEAL_MS = 9000                   # DRAFT: time over which a round's clearings appear
    PROBE_REVEAL_MS = 6000             # DRAFT: time over which ten trial closes appear
    SOURCE_REVEAL_MS = 2500            # DRAFT: time before a source's forecast can be answered
    PRIZE_POINTS = 20                  # DRAFT: forecast bonus
    POINTS_TO_CURRENCY = 0.01          # DRAFT: money per point


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


def _likert(label):
    return models.IntegerField(label=label, min=1, max=7, blank=True)


class Player(BasePlayer):
    # ---- once per participant (round 1) ----
    consent = models.IntegerField(initial=0, blank=True)          # 1 = box ticked (posted by a checkbox)
    client_info = models.LongStringField(blank=True)          # viewport, pixel ratio, reduced motion, user agent
    cq_cost = models.StringField(blank=True)
    cq_count = models.StringField(blank=True)
    cq_draws = models.StringField(blank=True)
    cq_board = models.StringField(blank=True)
    cq_attempts = models.IntegerField(initial=0)
    slot = models.IntegerField(initial=-1)
    schedule_id = models.IntegerField(initial=-1)
    arm = models.StringField(initial='')
    # ---- every repetition ----
    kind = models.StringField(initial='')                      # market (a procurement round) | probe (a prediction market)
    # procurement rounds
    ticket = models.StringField(blank=True)                    # the good ordered: SQUARE | TRIANGLE
    chose_good = models.BooleanField(blank=True)               # the good with the higher chance of filling
    wins = models.IntegerField(blank=True)                     # orders filled in the round
    own_bits = models.LongStringField(blank=True)              # fill (1) or not (0), clearing by clearing
    prices = models.LongStringField(blank=True)                # clearing prices of the ordered good
    goods_total = models.IntegerField(blank=True)              # goods held after the round (baskets = goods // basket size)
    board_regime = models.StringField(blank=True)
    board_source = models.StringField(blank=True)
    board_stream = models.StringField(blank=True)
    board_label = models.StringField(blank=True)
    board_wins = models.IntegerField(blank=True)
    board_dist = models.IntegerField(blank=True)
    board_bits = models.LongStringField(blank=True)
    fair1 = models.IntegerField(min=0, max=100, blank=True)
    fair2 = models.IntegerField(min=0, max=100, blank=True)
    fair3 = models.IntegerField(min=0, max=100, blank=True)
    entitle = models.IntegerField(min=0, max=100, blank=True)
    rate_inits = models.StringField(blank=True)
    rate_meta = models.LongStringField(blank=True)             # per slider: touched, number of moves, first touch (ms)
    rt_choose_ms = models.IntegerField(blank=True)
    rt_settle_ms = models.IntegerField(blank=True)
    rt_rate_ms = models.IntegerField(blank=True)
    settle_views = models.IntegerField(initial=0)
    settle_done = models.IntegerField(initial=0, blank=True)       # 1 = the reveal ran to its end in the browser
    settle_meta = models.LongStringField(blank=True)               # reveal timing: planned, actual, time hidden, reduced motion
    # prediction markets
    probe_index = models.IntegerField(blank=True)
    probe_symbol = models.StringField(blank=True)
    probe_pair = models.IntegerField(blank=True)
    probe_record_of = models.StringField(blank=True)
    probe_favourable = models.BooleanField(blank=True)
    probe_shown = models.StringField(blank=True)               # the ten trial closes (record evidence)
    probe_points = models.IntegerField(blank=True)
    market = models.StringField(blank=True)                    # M1..M4
    market_uid = models.StringField(blank=True)
    evidence = models.StringField(blank=True)                  # record | source
    cue = models.IntegerField(blank=True)                      # the source's forecast shown
    source_id = models.StringField(blank=True)
    source_track = models.IntegerField(blank=True)             # the source's forecasts on the right side, other markets only
    forecast_pre = models.IntegerField(min=0, max=100, blank=True)
    forecast_post = models.IntegerField(min=0, max=100, blank=True)
    bet = models.StringField(blank=True)                       # YES | NO | PASS
    bet_price = models.IntegerField(blank=True)
    bet_points = models.IntegerField(blank=True)               # credited at settlement
    market_above = models.IntegerField(blank=True)             # 1 = closed above the threshold
    recall = models.IntegerField(min=0, max=100, blank=True)
    rt_pre_ms = models.IntegerField(blank=True)
    rt_post_ms = models.IntegerField(blank=True)
    rt_bet_ms = models.IntegerField(blank=True)
    record_views = models.IntegerField(initial=0)
    record_done = models.IntegerField(initial=0, blank=True)
    # ---- closing (round 10) ----
    peer_success = _likert(copy.CLOSING['peer_success'])
    peer_real = _likert(copy.CLOSING['peer_real'])
    rig_suspicion = _likert(copy.CLOSING['rig_suspicion'])
    betting_familiarity = _likert(copy.CLOSING['betting_familiarity'])
    purpose_guess = models.LongStringField(label=copy.CLOSING['purpose_guess'], blank=True)
    age = models.IntegerField(label=copy.CLOSING['age'], min=18, max=99, blank=True)
    gender = models.StringField(label=copy.CLOSING['gender'], blank=True)
    probe_T = models.FloatField(blank=True)
    bet_stat = models.FloatField(blank=True)
    bet_total = models.IntegerField(blank=True)
    paid_ticket = models.IntegerField(blank=True)
    paid_which = models.StringField(blank=True)
    paid_forecast = models.IntegerField(blank=True)
    paid_outcome = models.IntegerField(blank=True)
    prize_won = models.BooleanField(blank=True)
    points_total = models.IntegerField(blank=True)
    finished = models.BooleanField(initial=False)


# ------------------------------------------------------------------ session set-up

_CACHE = {}


def _load(path, loader, what='file'):
    full = path if os.path.isabs(path) else os.path.join(PROJECT_DIR, path)
    key = (what, full, os.path.getmtime(full))
    if key not in _CACHE:
        _CACHE[key] = loader(full)
    return _CACHE[key]


def schedules(session):
    return _load(session.config['schedule_path'], en.load_schedules)


def price_axis(session):
    """one price axis for the whole schedule file (computed once per file)"""
    def axis(full):
        obj = en.load_schedules(full)
        return en.price_range(obj['design'], obj['schedules'])
    return _load(session.config['schedule_path'], axis, 'axis')


def _json(path):
    with open(path) as f:
        return json.load(f)


def board_source(session):
    return session.config.get('board_source', 'schedule')


def pool(session):
    return _load(session.config['pool_path'], _json)


def price_curves(session):
    """'own': only the ordered good's clearing prices are drawn (the display certified in I043);
    'both': the other good's prices of the same round are drawn beside them (certified in I047)"""
    return session.config.get('price_curves', 'own')


def _is_production():
    return bool(os.environ.get('OTREE_PRODUCTION'))


def creating_session(subsession: Subsession):
    if subsession.round_number != 1:
        return
    session = subsession.session
    cfg = session.config
    obj = schedules(session)
    d = obj['design']
    if en.n_rounds(d) != C.MARKET_ROUNDS or any(len(s['probe']) != C.PROBE_TICKETS for s in obj['schedules']):
        raise RuntimeError('the schedule file does not describe six procurement rounds and four markets')
    src = board_source(session)
    if src not in C.BOARD_SOURCES:
        raise RuntimeError(f'board_source must be one of {C.BOARD_SOURCES}')
    if price_curves(session) not in C.PRICE_CURVES:
        raise RuntimeError(f'price_curves must be one of {C.PRICE_CURVES}')
    human = not cfg.get('bot_kind')
    social = any(p['evidence'] == 'source' for s in obj['schedules'] for p in s['probe'])
    if src == 'schedule' and human and _is_production():
        raise RuntimeError("board_source 'schedule' is a computer-generated trader and forecaster: it is never "
                           "shown to people in production. Use 'pool' (real earlier records) or 'none' (seed wave).")
    if src == 'none' and social:
        raise RuntimeError("a session without a board has no earlier forecast to show either: draw its schedule "
                           "with --no-social (two record pairs)")
    if src == 'pool':
        p = pool(session)
        en.check_pool(p, d, allow_placeholder=not (human and _is_production()))
        if social:
            for m in obj['markets']:
                en.pool_source(p, m, 0, 0)          # raises if a market has no usable forecast in the pool
    session.vars['next_slot'] = int(cfg.get('first_slot', 0))


def _allocate(player: Player):
    """K6: slots are taken in order of arrival at the first task page; each slot once."""
    part = player.participant
    if 'slot' in part.vars:
        return
    session = player.session
    alloc = schedules(session)['allocation']
    end = min(len(alloc), int(session.config.get('last_slot') or len(alloc)))
    nxt = session.vars['next_slot']
    if nxt >= end:
        part.vars['slot'] = None
        return
    a = alloc[nxt]
    session.vars['next_slot'] = nxt + 1
    part.vars.update(slot=a['slot'], schedule_id=a['schedule'], arm=a['arm'], own_hist='', points=0, goods=0,
                     used_streams=[], forecasts=[], bets=[], last=None)
    first = player.in_round(1)
    first.slot, first.schedule_id, first.arm = a['slot'], a['schedule'], a['arm']


def _active(player: Player):
    return player.participant.vars.get('slot') is not None


def _is_market(player: Player):
    return player.round_number <= C.MARKET_ROUNDS


def _sched(player: Player):
    obj = schedules(player.session)
    return obj['design'], en.schedule_by_id(obj, player.participant.vars['schedule_id'])


def _label(*parts):
    """a trader's display name: a letter and two digits from a hash (no real identity in it)"""
    h = hashlib.sha256('|'.join(str(p) for p in parts).encode()).hexdigest()
    return 'ABCDEFGHJKLMNPRSTUVWXYZ'[int(h[:4], 16) % 23] + f'{int(h[4:8], 16) % 90 + 10}'


def _settle(player: Player):
    """computes everything round r shows, once, when the order is stored"""
    part = player.participant
    d, s = _sched(player)
    r, arm = player.round_number - 1, part.vars['arm']
    good = player.ticket == s['good_ticket']
    own = en.own_bits(s, d, r, good)
    hist = part.vars['own_hist']
    src = board_source(player.session)
    player.kind = 'market'
    player.chose_good = good
    player.own_bits = own
    player.wins = own.count('1')
    player.prices = ','.join(f'{p:.2f}' for p in en.price_path(s, d, r, good))
    player.board_source = src
    if src == 'none':
        player.board_regime, player.board_bits = '', ''
    else:
        player.board_regime = en.board_regime(s, d, r, arm)
        if src == 'schedule':
            player.board_bits = en.board_bits(s, d, r, arm, hist, own)
            player.board_label = _label('board', s['id'], r)         # the same name for both members of a pair
        else:
            seed = player.session.config.get('pool_seed', 0)
            st, dist = en.pool_board(pool(player.session), d, s, r, arm, own, seed, part.vars['used_streams'])
            player.board_bits, player.board_stream = st['bits'], st['id']
            player.board_label = _label('trader', st['id'])
            if dist is not None:
                player.board_dist = dist
            part.vars['used_streams'] = part.vars['used_streams'] + [st['id']]
        player.board_wins = player.board_bits.count('1')
    part.vars['own_hist'] = hist + own
    part.vars['points'] = part.vars['points'] + player.wins
    part.vars['goods'] = part.vars['goods'] + player.wins
    player.goods_total = part.vars['goods']
    part.vars['last'] = dict(ticket=player.ticket, wins=player.wins,
                             board_wins=player.field_maybe_none('board_wins'))


def _market(player: Player):
    """the prediction market of this round, with the evidence this participant gets"""
    obj = schedules(player.session)
    d, s = _sched(player)
    i = player.round_number - C.MARKET_ROUNDS - 1
    m = en.market_of(obj, s, i)
    src = board_source(player.session)
    if m['evidence'] == 'source':
        if src == 'pool':
            x = en.pool_source(pool(player.session), m, player.session.config.get('pool_seed', 0), s['id'])
            m.update(cue=int(x['forecast']), source_id=x['id'], source_label=_label('source', x['id']),
                     source_track=int(x['right_others']), source_others=int(x['others']))
        else:
            m.update(source_id='computer', source_label=_label('source', m['uid']), source_track=None)
    return d, m


def _thr(m):
    return f"{m['threshold']:.2f}"


def _market_text(m):
    t = copy.PROBE
    name = t['names'][m['asset']]
    return dict(name=name, thr=_thr(m), question=t['question'].format(asset=name, thr=_thr(m)))


def _finalise(player: Player):
    """the markets settle: bets are credited, the paid forecast is drawn"""
    part = player.participant
    if part.vars.get('finalised'):
        return
    obj = schedules(player.session)
    d, s = _sched(player)
    f = [tuple(x) for x in part.vars['forecasts']]
    markets = [en.market_of(obj, s, i) for i in range(C.PROBE_TICKETS)]
    bets = list(part.vars['bets'])
    player.probe_T = en.probe_T(s, f)
    player.bet_stat = en.bet_statistic(markets, bets)
    total = 0
    for p, m, b in zip(player.in_rounds(C.MARKET_ROUNDS + 1, C.NUM_ROUNDS), markets, bets):
        p.bet_points = en.bet_points(m, b, d)
        p.market_above = int(en.market_closes_above(m))
        total += p.bet_points
    player.bet_total = total
    i, which, fc, outcome, won = en.paid_forecast(s, f)
    player.paid_ticket, player.paid_which, player.paid_forecast = i, which, fc
    player.paid_outcome, player.prize_won = outcome, won
    part.vars['points'] = part.vars['points'] + total + (_prize(player.session) if won else 0)
    player.points_total = part.vars['points']
    player.payoff = cu(part.vars['points'] * _rate(player.session))
    player.finished = True
    part.vars['finalised'] = True


def _prize(session):
    return int(session.config.get('prize_points', C.PRIZE_POINTS))


def _rate(session):
    return float(session.config.get('points_to_currency', C.POINTS_TO_CURRENCY))


def _step_ok(*values):
    return all(v is not None and 0 <= v <= 100 and v % C.STEP == 0 for v in values)


# how far into its round a page is: the top bar fills the current step by this share (display only, I046)
SUB_STEP = dict(order=0.33, clearing=0.67, rate=1, market=0.25, evidence=0.5, bet=0.75, recall=1)


def _shell(player: Player, page):
    """what every task page needs for the top bar"""
    part = player.participant
    now = player.round_number
    steps = [dict(n=n, kind='market' if n <= C.MARKET_ROUNDS else 'probe',
                  state='done' if n < now else ('now' if n == now else 'todo')) for n in range(1, C.NUM_ROUNDS + 1)]
    return dict(page=page, round=now, n_rounds=C.NUM_ROUNDS, steps=steps, brand=copy.STUDY['brand'],
                progress=copy.PROGRESS, points=part.vars.get('points', 0), step_share=SUB_STEP.get(page, 1))


def _plain(t):
    return dict(t=t, brand=copy.STUDY['brand'], steps=None)


# ------------------------------------------------------------------ pages

class _Base(Page):
    use_blank_layout = True
    preserve_unsubmitted_inputs = False


class Consent(_Base):
    form_model = 'player'
    form_fields = ['consent', 'client_info']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return _plain(copy.STUDY)

    @staticmethod
    def js_vars(player: Player):
        # DRAFT: min_window_width > 0 keeps small screens out (0 = every device may take part)
        return dict(page='consent', min_width=int(player.session.config.get('min_window_width', 0)))

    @staticmethod
    def error_message(player: Player, values):
        if not values['consent']:
            return copy.STUDY['consent_error']


class Instructions(_Base):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        d = schedules(player.session)['design']
        t = copy.INSTRUCTIONS
        fmt = dict(k=d['settlements_per_round'], prize=_prize(player.session), basket=d['basket_size'],
                   cap=f"{d['cap']:.2f}", pay=d['bet_payout'])
        blocks = [(h, b.format(**fmt)) for h, b in t['market']]
        board = t['board'][board_source(player.session)]
        if board:
            blocks.append(board)
        blocks.append(t['ratings'])
        blocks.append((t['probe'][0], t['probe'][1].format(**fmt)))
        # the first block gets a legend of the two goods, the second an example of the chart's marks (display only)
        return dict(blocks=[dict(head=h, body=b, goods=i == 0, legend=i == 1) for i, (h, b) in enumerate(blocks)],
                    goods=[dict(value=x, name=copy.MARKET['ticket_names'][x]) for x in C.TICKETS],
                    not_filled=copy.MARKET['not_filled'], **_plain(t))

    @staticmethod
    def js_vars(player: Player):
        return dict(page='instructions')


def _quiz_items(session):
    src = board_source(session)
    k = schedules(session)['design']['settlements_per_round']
    out = {}
    for name, it in copy.QUIZ['items'].items():
        if name == 'cq_board':
            if src == 'none':
                continue
            right, wrong, hint = it['right'][src], it['wrong'][src], it['hint'][src]
        else:
            right, wrong, hint = it['right'], it['wrong'], it['hint']
        out[name] = dict(label=it['label'], right=right.format(k=k), wrong=wrong.format(k=k), hint=hint.format(k=k))
    return out


class Quiz(_Base):
    """repeat until correct; the number of attempts is recorded, never an exclusion"""
    form_model = 'player'

    @staticmethod
    def get_form_fields(player: Player):
        return list(_quiz_items(player.session))

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        items = _quiz_items(player.session)
        rng = random.Random(f'quiz-{player.participant.code}')
        last = player.participant.vars.get('quiz_last', {})       # answers of a failed attempt stay ticked
        rows = []
        for name, it in items.items():
            opts = [it['right'], it['wrong']]
            rng.shuffle(opts)
            rows.append(dict(name=name, label=it['label'],
                             options=[dict(text=o, checked=last.get(name) == o) for o in opts]))
        return dict(rows=rows, **_plain(copy.QUIZ))

    @staticmethod
    def js_vars(player: Player):
        return dict(page='quiz')

    @staticmethod
    def error_message(player: Player, values):
        player.cq_attempts += 1
        items = _quiz_items(player.session)
        player.participant.vars['quiz_last'] = {k: values.get(k) for k in items}
        wrong = {k: copy.QUIZ['retry'] + it['hint'] for k, it in items.items() if values.get(k) != it['right']}
        if wrong:
            return wrong

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        _allocate(player)


class NoSlot(_Base):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1 and not _active(player)

    @staticmethod
    def vars_for_template(player: Player):
        return _plain(copy.NO_SLOT)

    @staticmethod
    def js_vars(player: Player):
        return dict(page='noslot')


class Order(_Base):
    form_model = 'player'
    form_fields = ['ticket', 'rt_choose_ms']

    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and _is_market(player)

    @staticmethod
    def vars_for_template(player: Player):
        d, s = _sched(player)
        k, cap = d['settlements_per_round'], f"{d['cap']:.2f}"
        t = copy.MARKET
        other = [x for x in C.TICKETS if x != s['good_ticket']][0]
        order = [s['good_ticket'], other] if s['good_side'] == 'left' else [other, s['good_ticket']]
        last = player.participant.vars.get('last')
        recap = None
        if last:
            recap = dict(you=t['recap_you'].format(ticket=t['ticket_names'][last['ticket']], wins=last['wins'], k=k),
                         board=(t['recap_board'].format(wins=last['board_wins'], k=k)
                                if last['board_wins'] is not None else ''))
        return dict(t=t, sub=t['choose_sub'].format(k=k, cap=cap), recap=recap, cap=cap,
                    tickets=[dict(value=x, name=t['ticket_names'][x]) for x in order],
                    **_shell(player, 'order'))

    @staticmethod
    def js_vars(player: Player):
        # the frame of the chart: the cap and the price axis of the whole schedule file; no price of any round
        d, s = _sched(player)
        lo, hi = price_axis(player.session)
        return dict(page='order', cap=d['cap'], price_lo=lo, price_hi=hi, k=d['settlements_per_round'],
                    text=dict(zone=copy.MARKET['zone_label']))

    @staticmethod
    def error_message(player: Player, values):
        if values.get('ticket') not in C.TICKETS:
            return 'Please choose a good.'

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        _settle(player)


class Clearing(_Base):
    form_model = 'player'
    form_fields = ['rt_settle_ms', 'settle_done', 'settle_meta']

    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and _is_market(player)

    @staticmethod
    def vars_for_template(player: Player):
        player.settle_views += 1
        d, s = _sched(player)
        t = copy.MARKET
        shell = _shell(player, 'clearing')
        shell['points'] -= player.wins          # the total rises only once the reveal is over (counted up in the browser)
        other = [x for x in C.TICKETS if x != s['good_ticket']][0]
        order = [s['good_ticket'], other] if s['good_side'] == 'left' else [other, s['good_ticket']]
        return dict(t=t, ticket_name=t['ticket_names'][player.ticket], cap=f"{d['cap']:.2f}",
                    goods=[dict(value=x, name=t['ticket_names'][x], ordered=x == player.ticket) for x in order],
                    has_board=player.board_source != 'none',
                    board_name=f"{t['trader']} {player.field_maybe_none('board_label') or ''}",
                    board_kind=t['trader_kind'][player.board_source],
                    k=len(player.own_bits), pips=list(range(d['basket_size'])), **shell)

    @staticmethod
    def js_vars(player: Player):
        cfg = player.session.config
        d, s = _sched(player)
        t = copy.MARKET
        part = player.participant
        lo, hi = price_axis(player.session)
        r = player.round_number - 1
        both = price_curves(player.session) == 'both'
        not_ordered = [x for x in C.TICKETS if x != player.ticket][0]
        return dict(page='clearing', own=player.own_bits, board=player.board_bits or None,
                    prices=[float(x) for x in player.prices.split(',')], cap=d['cap'], price_lo=lo, price_hi=hi,
                    # 'both': what the participant would have seen for the good not ordered, in this round only
                    other_ticket=not_ordered if both else None,
                    other_prices=en.price_path(s, d, r, not player.chose_good) if both else None,
                    ticket=player.ticket, reveal_ms=int(cfg.get('reveal_ms', C.REVEAL_MS)),
                    points_before=part.vars['points'] - player.wins,
                    goods_before=part.vars['goods'] - player.wins, basket_size=d['basket_size'],
                    text=dict(done=t['settle_done'], gain=t['points_gain'].format(wins=player.wins),
                              zone=t['zone_label'], you=t['you'], trader=t['trader'], clearing=t['clearing'],
                              filled=t['filled'], not_filled=t['not_filled'], names=t['ticket_names']))

    @staticmethod
    def error_message(player: Player, values):
        if not values.get('settle_done'):
            return 'Please wait until the round has cleared.'


FAIR_FIELDS = ['fair1', 'fair2', 'fair3']


class Rate(_Base):
    form_model = 'player'
    form_fields = FAIR_FIELDS + ['entitle', 'rate_meta', 'rt_rate_ms']

    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and _is_market(player)

    @staticmethod
    def vars_for_template(player: Player):
        d, s = _sched(player)
        t = copy.MARKET
        starts = s['starts'][player.round_number - 1]
        items = [dict(name=n, text=x, lo=t['fair_anchors'][0], hi=t['fair_anchors'][1], start=starts[i])
                 for i, (n, x) in enumerate(zip(FAIR_FIELDS, t['fair_items']))]
        items.append(dict(name='entitle', text=t['entitle_item'], lo=t['entitle_anchors'][0],
                          hi=t['entitle_anchors'][1], start=starts[C.N_FAIR]))
        return dict(t=t, items=items, **_shell(player, 'rate'))

    @staticmethod
    def js_vars(player: Player):
        return dict(page='rate', step=C.STEP)

    @staticmethod
    def error_message(player: Player, values):
        vals = [values.get(n) for n in FAIR_FIELDS + ['entitle']]
        try:
            meta = json.loads(values.get('rate_meta') or '{}')
            touched = meta.get('touched', [])
        except (ValueError, AttributeError):
            touched = []
        if not _step_ok(*vals) or len(touched) != len(vals) or not all(touched):
            return copy.MARKET['rate_untouched']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        d, s = _sched(player)
        player.rate_inits = ','.join(str(x) for x in s['starts'][player.round_number - 1])


class Market(_Base):
    """the market and the first forecast. Neither the evidence nor a bet price is on this page."""
    form_model = 'player'
    form_fields = ['forecast_pre', 'rt_pre_ms']

    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and not _is_market(player)

    @staticmethod
    def vars_for_template(player: Player):
        d, m = _market(player)
        t = copy.PROBE
        mt = _market_text(m)
        return dict(t=t, symbol=m['asset'], mt=mt, ask=t['question_pre'].format(asset=mt['name'], thr=mt['thr']),
                    last=f"{m['chart'][-1]:.2f}", compact=False, forecast_field='forecast_pre',
                    **_shell(player, 'market'))

    @staticmethod
    def js_vars(player: Player):
        d, m = _market(player)
        return dict(page='market', chart=m['chart'], threshold=m['threshold'], step=C.STEP)

    @staticmethod
    def error_message(player: Player, values):
        if not _step_ok(values.get('forecast_pre')):
            return copy.PROBE['unset']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        d, m = _market(player)
        player.kind = 'probe'
        player.probe_index, player.probe_symbol, player.probe_pair = m['index'], m['asset'], m['pair']
        player.probe_favourable, player.market, player.market_uid = m['favourable'], m['key'], m['uid']
        player.evidence = m['evidence']
        player.probe_record_of = 'own' if m['evidence'] == 'record' else 'other'
        if m['evidence'] == 'record':
            player.probe_shown = m['shown']
        else:
            player.cue, player.source_id = m['cue'], m['source_id']
            if m.get('source_track') is not None:
                player.source_track = m['source_track']


class Evidence(_Base):
    """the evidence (ten trial closes, or a source's forecast), then the second forecast"""
    form_model = 'player'
    form_fields = ['forecast_post', 'rt_post_ms', 'record_done']

    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and not _is_market(player)

    @staticmethod
    def vars_for_template(player: Player):
        player.record_views += 1
        d, m = _market(player)
        t = copy.PROBE
        mt = _market_text(m)
        src = board_source(player.session)
        out = dict(t=t, symbol=m['asset'], mt=mt, ask=t['question_post'].format(asset=mt['name'], thr=mt['thr']),
                   is_record=m['evidence'] == 'record', last=f"{m['chart'][-1]:.2f}", compact=True,
                   forecast_field='forecast_post', **_shell(player, 'evidence'))
        if m['evidence'] == 'record':
            out.update(record_text=t['record_text'].format(thr=mt['thr']), m=len(m['shown']),
                       sum_text=t['sum_paid'].format(m=len(m['shown'])),
                       above=t['above'].format(thr=mt['thr']), below=t['below'].format(thr=mt['thr']))
        else:
            track = m.get('source_track')
            out.update(source_label=m['source_label'], cue=m['cue'],
                       source_kind=t['source_kind'][src if src in t['source_kind'] else 'schedule'].format(label=m['source_label']),
                       source_says=t['source_says'].format(thr=mt['thr']),
                       source_track=(t['source_track'].format(k=track, n=m['source_others'])
                                     if track is not None else ''))
        return out

    @staticmethod
    def js_vars(player: Player):
        d, m = _market(player)
        cfg = player.session.config
        out = dict(page='evidence', chart=m['chart'], threshold=m['threshold'], evidence=m['evidence'], step=C.STEP)
        if m['evidence'] == 'record':
            out.update(shown=m['shown'], reveal_ms=int(cfg.get('probe_reveal_ms', C.PROBE_REVEAL_MS)),
                       gain=m['shown'].count('1'))
        else:
            out.update(cue=m['cue'], reveal_ms=int(cfg.get('source_reveal_ms', C.SOURCE_REVEAL_MS)), gain=0)
        return out

    @staticmethod
    def error_message(player: Player, values):
        if not values.get('record_done') or not _step_ok(values.get('forecast_post')):
            return copy.PROBE['unset']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        part = player.participant
        part.vars['forecasts'] = part.vars['forecasts'] + [[player.forecast_pre, player.forecast_post]]
        player.probe_points = player.probe_shown.count('1') if player.evidence == 'record' else 0
        part.vars['points'] = part.vars['points'] + player.probe_points


class Bet(_Base):
    """the bet price appears here for the first time, after both forecasts are stored"""
    form_model = 'player'
    form_fields = ['bet', 'rt_bet_ms']

    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and not _is_market(player)

    @staticmethod
    def vars_for_template(player: Player):
        d, m = _market(player)
        t = copy.PROBE
        mt = _market_text(m)
        price, pay, allow = m['price_yes'], d['bet_payout'], d['bet_allowance']
        cost = lambda p: t['bet_cost'].format(cost=f'<b>{int(round(pay * p / 100))}</b>')   # the figure is set off in the sentence
        return dict(t=t, symbol=m['asset'], mt=mt, price_yes=price, price_no=100 - price,
                    last=f"{m['chart'][-1]:.2f}", compact=True,
                    cost_yes=cost(price), cost_no=cost(100 - price),
                    bet_text=t['bet_text'].format(allow=allow, pay=pay),
                    pass_sub=t['bet_pass_sub'].format(allow=allow), **_shell(player, 'bet'))

    @staticmethod
    def js_vars(player: Player):
        d, m = _market(player)
        return dict(page='bet', chart=m['chart'], threshold=m['threshold'])

    @staticmethod
    def error_message(player: Player, values):
        if values.get('bet') not in en.BETS:
            return copy.PROBE['bet_error']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        d, m = _market(player)
        part = player.participant
        player.bet_price = m['price_yes']
        part.vars['bets'] = part.vars['bets'] + [player.bet]      # credited when the markets settle


class Recall(_Base):
    form_model = 'player'
    form_fields = ['recall']

    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and not _is_market(player) and player.session.config.get('recall_check', True)

    @staticmethod
    def vars_for_template(player: Player):
        d, m = _market(player)
        t = copy.PROBE
        if m['evidence'] == 'record':
            q, opts = t['recall_record'].format(thr=_thr(m)), [dict(v=i, label=str(i)) for i in range(len(m['shown']) + 1)]
        else:
            q, opts = t['recall_source'], [dict(v=i, label=f'{i}%') for i in range(0, 101, C.STEP)]
        return dict(t=t, question=q, options=opts, wide=m['evidence'] != 'record', **_shell(player, 'recall'))

    @staticmethod
    def js_vars(player: Player):
        return dict(page='recall')

    @staticmethod
    def error_message(player: Player, values):
        if values.get('recall') is None:
            return 'Please pick an answer.'


CLOSING_BOARD = ['peer_success', 'peer_real']
CLOSING_REST = ['rig_suspicion', 'betting_familiarity', 'purpose_guess', 'age', 'gender']


class Closing(_Base):
    form_model = 'player'

    @staticmethod
    def get_form_fields(player: Player):
        return (CLOSING_BOARD if board_source(player.session) != 'none' else []) + CLOSING_REST

    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        t = copy.CLOSING
        scales = []
        if board_source(player.session) != 'none':
            scales += [dict(name='peer_success', text=t['peer_success'], lo=t['peer_success_anchors'][0], hi=t['peer_success_anchors'][1]),
                       dict(name='peer_real', text=t['peer_real'], lo=t['peer_real_anchors'][0], hi=t['peer_real_anchors'][1])]
        scales += [dict(name='rig_suspicion', text=t['rig_suspicion'], lo=t['rig_anchors'][0], hi=t['rig_anchors'][1]),
                   dict(name='betting_familiarity', text=t['betting_familiarity'], lo=t['betting_anchors'][0], hi=t['betting_anchors'][1])]
        return dict(t=t, scales=scales, points7=list(range(1, 8)), **_shell(player, 'closing'))

    @staticmethod
    def js_vars(player: Player):
        return dict(page='closing')

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        _finalise(player)


class Results(_Base):
    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        _finalise(player)
        obj = schedules(player.session)
        d, s = _sched(player)
        t = copy.RESULTS
        prize = _prize(player.session)
        rows = []
        for p in player.in_rounds(C.MARKET_ROUNDS + 1, C.NUM_ROUNDS):
            m = en.market_of(obj, s, p.probe_index)
            above = bool(p.market_above)
            rows.append(dict(symbol=m['asset'], name=copy.PROBE['names'][m['asset']], above=above,
                             outcome=(t['closed_above'] if above else t['closed_below']).format(
                                 close=f"{m['close']:.2f}", thr=_thr(m)),
                             tag=t['resolved']['yes' if above else 'no'],
                             bet=t['your_bet'][p.bet], bet_kind=p.bet.lower(),
                             pts=t['bet_points'].format(pts=p.bet_points)))
        goods_points = player.points_total - player.bet_total - (prize if player.prize_won else 0)
        return dict(t=t, rows=rows, points_line=t['points'].format(points=goods_points),
                    bets_line=t['bets'].format(pts=player.bet_total),
                    bonus_line=(t['bonus_won'] if player.prize_won else t['bonus_lost']).format(prize=prize),
                    money_line=t['money'].format(money=player.payoff),
                    completion_url=player.session.config.get('completion_url', ''),
                    **_shell(player, 'results'))

    @staticmethod
    def js_vars(player: Player):
        return dict(page='results')


page_sequence = [Consent, Instructions, Quiz, NoSlot, Order, Clearing, Rate, Market, Evidence, Bet, Recall,
                 Closing, Results]


# ------------------------------------------------------------------ export

REP_COLS = ['repetition', 'kind', 'ticket', 'chose_good', 'wins', 'goods_total', 'board_regime', 'board_source',
            'board_stream', 'board_label', 'board_wins', 'board_dist', 'fair1', 'fair2', 'fair3', 'fairness', 'entitle',
            'rate_inits', 'probe_index', 'probe_symbol', 'probe_pair', 'probe_record_of', 'probe_favourable',
            'probe_shown', 'probe_points', 'market', 'market_uid', 'evidence', 'cue', 'source_id', 'source_track',
            'forecast_pre', 'forecast_post', 'bet', 'bet_price', 'bet_points', 'market_above', 'recall',
            'rt_choose_ms', 'rt_settle_ms', 'rt_rate_ms', 'rt_pre_ms', 'rt_post_ms', 'rt_bet_ms', 'settle_views',
            'settle_done', 'record_views', 'record_done', 'settle_meta', 'rate_meta', 'own_bits', 'board_bits',
            'prices']
PART_COLS = ['finished', 'probe_T', 'bet_stat', 'bet_total', 'paid_ticket', 'paid_which', 'paid_forecast',
             'paid_outcome', 'prize_won', 'points_total', 'payoff', 'cq_attempts', 'peer_success', 'peer_real',
             'rig_suspicion', 'betting_familiarity', 'purpose_guess', 'age', 'gender', 'client_info']
EXPORT_HEADER = ['row_type', 'session', 'config', 'participant', 'label', 'bot_kind', 'slot', 'schedule', 'arm'] \
    + REP_COLS + PART_COLS


def _val(p, name):
    v = p.field_maybe_none(name)
    if v is None:
        return ''
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, str):
        return v.replace('\n', ' ').replace('\r', ' ')
    return v


def custom_export(players):
    """one 'repetition' row per participant and repetition, then one 'participant' row"""
    yield EXPORT_HEADER
    by_part = {}
    for p in players:
        by_part.setdefault(p.participant.code, []).append(p)
    for code, ps in by_part.items():
        ps.sort(key=lambda q: q.round_number)
        first, last = ps[0], ps[-1]
        part, cfg = first.participant, first.session.config
        if first.slot < 0:
            continue                                            # never reached the task
        base = [first.session.code, cfg.get('name', ''), code, part.label or '', cfg.get('bot_kind') or 'human',
                first.slot, first.schedule_id, first.arm]
        for p in ps:
            if not p.kind:
                continue
            row = {c: _val(p, c) for c in REP_COLS if c not in ('repetition', 'fairness')}
            row['repetition'] = p.round_number
            f = [p.field_maybe_none(n) for n in FAIR_FIELDS]
            row['fairness'] = round(sum(f) / len(f), 4) if all(x is not None for x in f) else ''
            yield ['repetition'] + base + [row[c] for c in REP_COLS] + [''] * len(PART_COLS)
        tail = {c: _val(last, c) for c in PART_COLS}
        tail['cq_attempts'], tail['client_info'] = first.cq_attempts, _val(first, 'client_info')
        yield ['participant'] + base + [''] * len(REP_COLS) + [tail[c] for c in PART_COLS]


# ------------------------------------------------------------------ bots (pipeline validation only)

_AGENTS = {}          # model-policy bots, kept in the process (bots run in one process)


class PlayerBot(Bot):
    def play_round(self):
        cfg = self.session.config
        kind = cfg.get('bot_kind', 'random')
        code = self.participant.code
        rng = random.Random(f"bot-{self.player.id_in_subsession}-{self.round_number}")
        agent = _AGENTS.get(code)
        # self.participant and self.player are read afresh after every submission: the objects
        # held across a request are stale
        if self.round_number == 1:
            yield SubmissionMustFail(Consent, {'consent': 0, 'client_info': '{}'}, check_html=False)
            yield Submission(Consent, {'consent': 1, 'client_info': '{"bot": true}'}, check_html=False)
            yield Submission(Instructions, check_html=False)
            items = _quiz_items(self.session)
            right = {k: it['right'] for k, it in items.items()}
            wrong = dict(right, cq_cost=items['cq_cost']['wrong'])
            yield SubmissionMustFail(Quiz, wrong, check_html=False)
            yield Submission(Quiz, right, check_html=False)
            if self.participant.vars.get('slot') is None:
                return
            if kind == 'model':
                agent = ModelAgent(seed=self.player.id_in_subsession * 7919 + int(cfg.get('bot_seed', 0)),
                                   slow=rng.random() < 0.5, point=cfg.get('bot_point', 'P1'),
                                   rule=cfg.get('bot_rule', 'event'),
                                   kappa_source=float(cfg.get('bot_kappa_source', 0.35)))
                _AGENTS[code] = agent
        if self.participant.vars.get('slot') is None:
            return
        d, s = _sched(self.player)
        if self.round_number <= C.MARKET_ROUNDS:
            good = agent.choose_good() if agent else rng.random() < 0.5
            other = [x for x in C.TICKETS if x != s['good_ticket']][0]
            yield SubmissionMustFail(Order, {'ticket': 'CIRCLE', 'rt_choose_ms': 900}, check_html=False)
            yield Submission(Order, {'ticket': s['good_ticket'] if good else other,
                                     'rt_choose_ms': rng.randint(600, 4000)}, check_html=False)
            yield SubmissionMustFail(Clearing, {'rt_settle_ms': 200, 'settle_done': 0}, check_html=False)
            yield Submission(Clearing, {'rt_settle_ms': rng.randint(11000, 16000), 'settle_done': 1}, check_html=False)
            p = self.player
            if agent:
                agent.observe(p.chose_good, p.own_bits, p.board_bits or None, p.board_regime)
                fair, ent = agent.ratings()
            else:
                fair, ent = [C.STEP * rng.randint(0, 20) for _ in range(C.N_FAIR)], C.STEP * rng.randint(0, 20)
            ok = dict(zip(FAIR_FIELDS, fair), entitle=ent, rt_rate_ms=rng.randint(4000, 20000),
                      rate_meta=json.dumps(dict(touched=[True] * 4, moves=[1] * 4)))
            yield SubmissionMustFail(Rate, dict(ok, rate_meta=json.dumps(dict(touched=[True, True, True, False]))),
                                     check_html=False)
            yield SubmissionMustFail(Rate, dict(ok, fair1=52), check_html=False)
            yield Submission(Rate, ok, check_html=False)
        else:
            d, m = _market(self.player)
            e = m['shown'].count('1') / len(m['shown']) if m['evidence'] == 'record' else m['cue'] / 100
            if agent:
                pre, post, bet = agent.market(e, m['evidence'], m['price_yes'])
            else:
                pre, post, bet = C.STEP * rng.randint(0, 20), C.STEP * rng.randint(0, 20), rng.choice(en.BETS)
            yield SubmissionMustFail(Market, {'forecast_pre': 33, 'rt_pre_ms': 1000}, check_html=False)
            yield Submission(Market, {'forecast_pre': pre, 'rt_pre_ms': rng.randint(1500, 9000)}, check_html=False)
            yield SubmissionMustFail(Evidence, {'forecast_post': post, 'rt_post_ms': 100, 'record_done': 0},
                                     check_html=False)
            yield Submission(Evidence, {'forecast_post': post, 'rt_post_ms': rng.randint(8000, 20000),
                                        'record_done': 1}, check_html=False)
            yield SubmissionMustFail(Bet, {'bet': 'MAYBE', 'rt_bet_ms': 500}, check_html=False)
            yield Submission(Bet, {'bet': bet, 'rt_bet_ms': rng.randint(1200, 8000)}, check_html=False)
            if cfg.get('recall_check', True):
                seen = m['shown'].count('1') if m['evidence'] == 'record' else m['cue']
                yield Submission(Recall, {'recall': seen}, check_html=False)
        if self.round_number == C.NUM_ROUNDS:
            closing = {'rig_suspicion': 2, 'betting_familiarity': 3, 'purpose_guess': 'bot run', 'age': 30,
                       'gender': 'bot'}
            if board_source(self.session) != 'none':
                closing.update(peer_success=5, peer_real=4)
            yield Submission(Closing, closing, check_html=False)      # Results is the last page: nothing to submit
