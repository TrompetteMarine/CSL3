"""
diss_market — the yoked ten-repetition design (KGi-DISS-I042; specification
experiment/YOKED_DESIGN.md, contract freezes/00_freeze_I042.yaml).

One oTree round per repetition:
  rounds 1-6    market rounds: Choose -> Settle -> Rate
  rounds 7-10   probe tickets: ProbePre -> ProbePost (-> ProbeRecall)
Round 1 opens with Consent, Instructions and Quiz; round 10 closes with Closing and Results.

Everything a participant sees comes from a pre-drawn format-2 schedule file through
engine.py. The browser only displays: no outcome is computed there, and no page carries an
outcome of a later round or a probe record before its first forecast is stored.

All wording lives in copy_en.py and is DRAFT (author-gated). Bot data from this app is for
pipeline validation only.
"""
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
    REVEAL_MS = 9000                   # DRAFT: time over which a round's settlements appear
    PROBE_REVEAL_MS = 6000             # DRAFT: time over which a probe record appears
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
    kind = models.StringField(initial='')                      # market | probe
    # market rounds
    ticket = models.StringField(blank=True)
    chose_good = models.BooleanField(blank=True)
    wins = models.IntegerField(blank=True)
    own_bits = models.LongStringField(blank=True)
    board_regime = models.StringField(blank=True)
    board_source = models.StringField(blank=True)
    board_stream = models.StringField(blank=True)
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
    # probe tickets
    probe_index = models.IntegerField(blank=True)
    probe_symbol = models.StringField(blank=True)
    probe_pair = models.IntegerField(blank=True)
    probe_record_of = models.StringField(blank=True)
    probe_favourable = models.BooleanField(blank=True)
    probe_shown = models.StringField(blank=True)
    probe_points = models.IntegerField(blank=True)
    forecast_pre = models.IntegerField(min=0, max=100, blank=True)
    forecast_post = models.IntegerField(min=0, max=100, blank=True)
    recall = models.IntegerField(min=0, max=10, blank=True)
    rt_pre_ms = models.IntegerField(blank=True)
    rt_post_ms = models.IntegerField(blank=True)
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
    paid_ticket = models.IntegerField(blank=True)
    paid_which = models.StringField(blank=True)
    paid_forecast = models.IntegerField(blank=True)
    paid_outcome = models.IntegerField(blank=True)
    prize_won = models.BooleanField(blank=True)
    points_total = models.IntegerField(blank=True)
    finished = models.BooleanField(initial=False)


# ------------------------------------------------------------------ session set-up

_CACHE = {}


def _load(path, loader):
    full = path if os.path.isabs(path) else os.path.join(PROJECT_DIR, path)
    key = (full, os.path.getmtime(full))
    if key not in _CACHE:
        _CACHE[key] = loader(full)
    return _CACHE[key]


def schedules(session):
    return _load(session.config['schedule_path'], en.load_schedules)


def _json(path):
    with open(path) as f:
        return json.load(f)


def board_source(session):
    return session.config.get('board_source', 'schedule')


def pool(session):
    return _load(session.config['pool_path'], _json)


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
        raise RuntimeError('the schedule file does not describe six market rounds and four probe tickets')
    src = board_source(session)
    if src not in C.BOARD_SOURCES:
        raise RuntimeError(f'board_source must be one of {C.BOARD_SOURCES}')
    human = not cfg.get('bot_kind')
    if src == 'schedule' and human and _is_production():
        raise RuntimeError("board_source 'schedule' is a computer-generated trader: it is never shown to "
                           "people in production. Use 'pool' (real earlier records) or 'none' (seed wave).")
    if src == 'pool':
        en.check_pool(pool(session), d, allow_placeholder=not (human and _is_production()))
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
    part.vars.update(slot=a['slot'], schedule_id=a['schedule'], arm=a['arm'], own_hist='', points=0,
                     used_streams=[], forecasts=[], last=None)
    first = player.in_round(1)
    first.slot, first.schedule_id, first.arm = a['slot'], a['schedule'], a['arm']


def _active(player: Player):
    return player.participant.vars.get('slot') is not None


def _is_market(player: Player):
    return player.round_number <= C.MARKET_ROUNDS


def _sched(player: Player):
    obj = schedules(player.session)
    return obj['design'], en.schedule_by_id(obj, player.participant.vars['schedule_id'])


def _settle(player: Player):
    """computes everything round r shows, once, when the ticket choice is stored"""
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
    player.board_source = src
    if src == 'none':
        player.board_regime, player.board_bits = '', ''
    else:
        player.board_regime = en.board_regime(s, d, r, arm)
        if src == 'schedule':
            player.board_bits = en.board_bits(s, d, r, arm, hist, own)
        else:
            seed = player.session.config.get('pool_seed', 0)
            st, dist = en.pool_board(pool(player.session), d, s, r, arm, own, seed, part.vars['used_streams'])
            player.board_bits, player.board_stream = st['bits'], st['id']
            if dist is not None:
                player.board_dist = dist
            part.vars['used_streams'] = part.vars['used_streams'] + [st['id']]
        player.board_wins = player.board_bits.count('1')
    part.vars['own_hist'] = hist + own
    part.vars['points'] = part.vars['points'] + player.wins
    part.vars['last'] = dict(ticket=player.ticket, wins=player.wins,
                             board_wins=player.field_maybe_none('board_wins'))


def _probe(player: Player):
    d, s = _sched(player)
    i = player.round_number - C.MARKET_ROUNDS - 1
    return i, s['probe'][i]


def _finalise(player: Player):
    part = player.participant
    if part.vars.get('finalised'):
        return
    d, s = _sched(player)
    f = [tuple(x) for x in part.vars['forecasts']]
    player.probe_T = en.probe_T(s, f)
    i, which, fc, outcome, won = en.paid_forecast(s, f)
    player.paid_ticket, player.paid_which, player.paid_forecast = i, which, fc
    player.paid_outcome, player.prize_won = outcome, won
    if won:
        part.vars['points'] = part.vars['points'] + _prize(player.session)
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


def _shell(player: Player, page):
    """what every task page needs for the top bar"""
    part = player.participant
    now = player.round_number
    steps = [dict(n=n, kind='market' if n <= C.MARKET_ROUNDS else 'probe',
                  state='done' if n < now else ('now' if n == now else 'todo')) for n in range(1, C.NUM_ROUNDS + 1)]
    return dict(page=page, round=now, n_rounds=C.NUM_ROUNDS, steps=steps, brand=copy.STUDY['brand'],
                progress=copy.PROGRESS, points=part.vars.get('points', 0))


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
        return dict(t=copy.STUDY, brand=copy.STUDY['brand'], steps=None)

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
        fmt = dict(k=d['settlements_per_round'], prize=_prize(player.session))
        blocks = [(h, b.format(**fmt)) for h, b in t['market']]
        board = t['board'][board_source(player.session)]
        if board:
            blocks.append(board)
        blocks.append(t['ratings'])
        blocks.append((t['probe'][0], t['probe'][1].format(**fmt)))
        return dict(t=t, blocks=[dict(head=h, body=b) for h, b in blocks], brand=copy.STUDY['brand'], steps=None)

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
        rows = []
        for name, it in items.items():
            opts = [it['right'], it['wrong']]
            rng.shuffle(opts)
            last = player.participant.vars.get('quiz_last', {})       # answers of a failed attempt stay ticked
            rows.append(dict(name=name, label=it['label'],
                             options=[dict(text=o, checked=last.get(name) == o) for o in opts]))
        return dict(t=copy.QUIZ, rows=rows, brand=copy.STUDY['brand'], steps=None)

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
        return dict(t=copy.NO_SLOT, brand=copy.STUDY['brand'], steps=None)

    @staticmethod
    def js_vars(player: Player):
        return dict(page='noslot')


class Choose(_Base):
    form_model = 'player'
    form_fields = ['ticket', 'rt_choose_ms']

    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and _is_market(player)

    @staticmethod
    def vars_for_template(player: Player):
        d, s = _sched(player)
        k = d['settlements_per_round']
        t = copy.MARKET
        other = [x for x in C.TICKETS if x != s['good_ticket']][0]
        order = [s['good_ticket'], other] if s['good_side'] == 'left' else [other, s['good_ticket']]
        last = player.participant.vars.get('last')
        recap = None
        if last:
            recap = dict(you=t['recap_you'].format(ticket=t['ticket_names'][last['ticket']], wins=last['wins'], k=k),
                         board=(t['recap_board'].format(wins=last['board_wins'], k=k)
                                if last['board_wins'] is not None else ''))
        return dict(t=t, sub=t['choose_sub'].format(k=k), recap=recap,
                    tickets=[dict(value=x, name=t['ticket_names'][x]) for x in order],
                    **_shell(player, 'choose'))

    @staticmethod
    def js_vars(player: Player):
        return dict(page='choose')

    @staticmethod
    def error_message(player: Player, values):
        if values.get('ticket') not in C.TICKETS:
            return 'Please choose a ticket.'

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        _settle(player)


class Settle(_Base):
    form_model = 'player'
    form_fields = ['rt_settle_ms', 'settle_done', 'settle_meta']

    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and _is_market(player)

    @staticmethod
    def vars_for_template(player: Player):
        player.settle_views += 1
        t = copy.MARKET
        return dict(t=t, ticket_name=t['ticket_names'][player.ticket],
                    board_label=t['board_label'][player.board_source],
                    has_board=player.board_source != 'none',
                    k=len(player.own_bits), **_shell(player, 'settle'))

    @staticmethod
    def js_vars(player: Player):
        cfg = player.session.config
        t = copy.MARKET
        return dict(page='settle', own=player.own_bits, board=player.board_bits or None,
                    ticket=player.ticket, reveal_ms=int(cfg.get('reveal_ms', C.REVEAL_MS)),
                    points_before=player.participant.vars['points'] - player.wins,
                    text=dict(done=t['settle_done'], gain=t['points_gain'].format(wins=player.wins)))

    @staticmethod
    def error_message(player: Player, values):
        if not values.get('settle_done'):
            return 'Please wait until the round has settled.'


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


class ProbePre(_Base):
    form_model = 'player'
    form_fields = ['forecast_pre', 'rt_pre_ms']

    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and not _is_market(player)

    @staticmethod
    def vars_for_template(player: Player):
        i, tk = _probe(player)
        t = copy.PROBE
        return dict(t=t, symbol=tk['symbol'], symbol_name=t['names'][tk['symbol']], **_shell(player, 'probe_pre'))

    @staticmethod
    def js_vars(player: Player):
        i, tk = _probe(player)
        return dict(page='probe_pre', symbol=tk['symbol'], step=C.STEP)      # the record is NOT sent here (K9)

    @staticmethod
    def error_message(player: Player, values):
        if not _step_ok(values.get('forecast_pre')):
            return copy.PROBE['unset']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        i, tk = _probe(player)
        player.kind = 'probe'
        player.probe_index, player.probe_symbol, player.probe_pair = i, tk['symbol'], tk['pair']
        player.probe_record_of, player.probe_favourable, player.probe_shown = tk['record_of'], tk['favourable'], tk['shown']


class ProbePost(_Base):
    form_model = 'player'
    form_fields = ['forecast_post', 'rt_post_ms', 'record_done']

    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and not _is_market(player)

    @staticmethod
    def vars_for_template(player: Player):
        player.record_views += 1
        i, tk = _probe(player)
        t = copy.PROBE
        return dict(t=t, symbol=tk['symbol'], symbol_name=t['names'][tk['symbol']],
                    record_text=t['record_own'] if tk['record_of'] == 'own' else t['record_other'],
                    m=len(tk['shown']), **_shell(player, 'probe_post'))

    @staticmethod
    def js_vars(player: Player):
        i, tk = _probe(player)
        cfg = player.session.config
        return dict(page='probe_post', symbol=tk['symbol'], shown=player.probe_shown, record_of=tk['record_of'],
                    reveal_ms=int(cfg.get('probe_reveal_ms', C.PROBE_REVEAL_MS)), step=C.STEP,
                    gain=player.probe_shown.count('1') if tk['record_of'] == 'own' else 0)

    @staticmethod
    def error_message(player: Player, values):
        if not values.get('record_done') or not _step_ok(values.get('forecast_post')):
            return copy.PROBE['unset']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        part = player.participant
        part.vars['forecasts'] = part.vars['forecasts'] + [[player.forecast_pre, player.forecast_post]]
        player.probe_points = player.probe_shown.count('1') if player.probe_record_of == 'own' else 0
        part.vars['points'] = part.vars['points'] + player.probe_points


class ProbeRecall(_Base):
    form_model = 'player'
    form_fields = ['recall']

    @staticmethod
    def is_displayed(player: Player):
        return _active(player) and not _is_market(player) and player.session.config.get('recall_check', True)

    @staticmethod
    def vars_for_template(player: Player):
        return dict(t=copy.PROBE, options=list(range(len(player.probe_shown) + 1)), **_shell(player, 'probe_recall'))

    @staticmethod
    def js_vars(player: Player):
        return dict(page='probe_recall')

    @staticmethod
    def error_message(player: Player, values):
        if values.get('recall') is None:
            return 'Please pick a number.'


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
        t = copy.RESULTS
        prize = _prize(player.session)
        market_points = player.points_total - (prize if player.prize_won else 0)
        return dict(t=t, points_line=t['points'].format(points=market_points),
                    bonus_line=(t['bonus_won'] if player.prize_won else t['bonus_lost']).format(prize=prize),
                    money_line=t['money'].format(money=player.payoff),
                    completion_url=player.session.config.get('completion_url', ''),
                    **_shell(player, 'results'))

    @staticmethod
    def js_vars(player: Player):
        return dict(page='results')


page_sequence = [Consent, Instructions, Quiz, NoSlot, Choose, Settle, Rate, ProbePre, ProbePost, ProbeRecall,
                 Closing, Results]


# ------------------------------------------------------------------ export

REP_COLS = ['repetition', 'kind', 'ticket', 'chose_good', 'wins', 'board_regime', 'board_source', 'board_stream',
            'board_wins', 'board_dist', 'fair1', 'fair2', 'fair3', 'fairness', 'entitle', 'rate_inits',
            'probe_index', 'probe_symbol', 'probe_pair', 'probe_record_of', 'probe_favourable', 'probe_shown',
            'probe_points', 'forecast_pre', 'forecast_post', 'recall', 'rt_choose_ms', 'rt_settle_ms',
            'rt_rate_ms', 'rt_pre_ms', 'rt_post_ms', 'settle_views', 'settle_done', 'record_views', 'record_done',
            'settle_meta', 'rate_meta', 'own_bits', 'board_bits']
PART_COLS = ['finished', 'probe_T', 'paid_ticket', 'paid_which', 'paid_forecast', 'paid_outcome', 'prize_won',
             'points_total', 'payoff', 'cq_attempts', 'peer_success', 'peer_real', 'rig_suspicion',
             'betting_familiarity', 'purpose_guess', 'age', 'gender', 'client_info']
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
            slot = self.participant.vars.get('slot')
            if slot is None:
                return
            if kind == 'model':
                # rigidity alternates between pairs, so every pair has the two members alike in
                # nothing but their schedule: slots 2j and 2j+1 form pair j
                agent = ModelAgent(seed=self.player.id_in_subsession * 7919 + int(cfg.get('bot_seed', 0)),
                                   slow=rng.random() < 0.5, point=cfg.get('bot_point', 'P1'),
                                   rule=cfg.get('bot_rule', 'event'))
                _AGENTS[code] = agent
        if self.participant.vars.get('slot') is None:
            return
        d, s = _sched(self.player)
        if self.round_number <= C.MARKET_ROUNDS:
            good = agent.choose_good() if agent else rng.random() < 0.5
            other = [x for x in C.TICKETS if x != s['good_ticket']][0]
            yield SubmissionMustFail(Choose, {'ticket': 'CIRCLE', 'rt_choose_ms': 900}, check_html=False)
            yield Submission(Choose, {'ticket': s['good_ticket'] if good else other,
                                      'rt_choose_ms': rng.randint(600, 4000)}, check_html=False)
            yield SubmissionMustFail(Settle, {'rt_settle_ms': 200, 'settle_done': 0}, check_html=False)
            yield Submission(Settle, {'rt_settle_ms': rng.randint(11000, 16000), 'settle_done': 1}, check_html=False)
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
            i, tk = _probe(self.player)
            e = tk['shown'].count('1') / len(tk['shown'])
            pre, post = agent.forecasts(e) if agent else (C.STEP * rng.randint(0, 20), C.STEP * rng.randint(0, 20))
            yield SubmissionMustFail(ProbePre, {'forecast_pre': 33, 'rt_pre_ms': 1000}, check_html=False)
            yield Submission(ProbePre, {'forecast_pre': pre, 'rt_pre_ms': rng.randint(1500, 9000)}, check_html=False)
            yield SubmissionMustFail(ProbePost, {'forecast_post': post, 'rt_post_ms': 100, 'record_done': 0},
                                     check_html=False)
            yield Submission(ProbePost, {'forecast_post': post, 'rt_post_ms': rng.randint(8000, 20000),
                                         'record_done': 1}, check_html=False)
            if cfg.get('recall_check', True):
                yield Submission(ProbeRecall, {'recall': tk['shown'].count('1')}, check_html=False)
        if self.round_number == C.NUM_ROUNDS:
            closing = {'rig_suspicion': 2, 'betting_familiarity': 3, 'purpose_guess': 'bot run', 'age': 30,
                       'gender': 'bot'}
            if board_source(self.session) != 'none':
                closing.update(peer_success=5, peer_real=4)
            yield Submission(Closing, closing, check_html=False)      # Results is the last page: nothing to submit
