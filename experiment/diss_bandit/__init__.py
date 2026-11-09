"""
diss_bandit — task v3, market skin (KGi-DISS-I032; supersedes the I006 bandit
build, which remains available behind config skin='bandit' for the pilot
framing comparison on the same seeds).

Two tickets (SQUARE / TRIANGLE) <-> two arms; 450 trials in three 150-trial
blocks (= the three phases, invisible to participants); seeded settlement <->
phase means; house-funded tickets (gains domain); truthful AMM disclosure with
fixed within-phase displayed prices; yoked no-deception peer trader board with
per-block reference regime (HIGH / LOW, or a dose band); two sliders every
SLIDER_EVERY trials with RANDOMIZED initial positions (fairness; entitlement —
the identification lever); minimal-information binarized-scoring-rule
forecasts of the next settlement (exploratory, pilot-gated; one paid at random);
WTP re-draw probes at end-P2 and mid-P3 (truthful re-seed); announced
non-contingent windfall every 15th trial; believability/funnel block.

Build deltas 1-11 are enumerated in freezes/00_freeze_I032.yaml; the I032 audit
fixes (records/98_audit_I032.md) are marked "AUDIT". Bot data produced by this
app is for pipeline validation only.
"""
import json
import os
import random

from otree.api import *


class C(BaseConstants):
    NAME_IN_URL = 'diss_bandit'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 3                      # 3 blocks = 3 phases
    TRIALS_PER_BLOCK = 150
    SLIDER_EVERY_DEFAULT = 5            # delta 10: sparse arm uses 10 via config
    BONUS_EVERY = 15                    # announced, non-contingent windfall
    BONUS_POINTS = 3
    BSR_EVERY = 15                      # delta 3: forecast cadence
    BSR_OFFSET = 7                      # t % 15 == 7 (offset from windfalls/sliders)
    BSR_PRIZE = 10                      # AUDIT: the promised forecast bonus, paid
    WTP_ENDOWMENT = 20                  # delta 4: dedicated endowment (points)
    WTP_TRIALS = (300, 375)             # end-P2, mid-P3 (global trial index)
    PHASE_P = {1: (0.65, 0.35), 2: (0.30, 0.15)}
    RICH_P = (0.65, 0.35)               # AUDIT: 'rich' pool-source schedule, all phases
    RESTORATION = {'FULL': (0.65, 0.35),
                   'MODERATE': (0.45, 0.35)}   # pilot-calibrated (open)
    HIGH_BAND_DEFAULT = (0.60, 0.70)    # mu_ref=.65 band on the CURRENT block window
    LOW_BAND_TOL = 0.05
    TRAIL_WINDOW = 15
    PEER_DISPLAY_WINDOW = 15            # AUDIT: board shows the peer's trailing-15 rate
    # delta 1/2: truthful AMM display — prices fixed within phases. DESIGN-
    # DECISION (author review): default quote is 50/50 for the whole session.
    PHASE_PRICES_DEFAULT = {1: (50, 50), 2: (50, 50), 3: (50, 50)}
    TICKETS = ('SQUARE', 'TRIANGLE')


def total_trial(round_number: int, t_in_block: int) -> int:
    return (round_number - 1) * C.TRIALS_PER_BLOCK + t_in_block


class Subsession(BaseSubsession):
    pass


BLOCK6 = [('HIGH', 'MODERATE'), ('HIGH', 'MODERATE'), ('HIGH', 'FULL'),
          ('LOW', 'MODERATE'), ('LOW', 'MODERATE'), ('LOW', 'FULL')]


def _balanced_assignment(players, seed):
    """AUDIT: permuted blocks of 6 within the session (p2_regime 1:1, restoration
    MODERATE:FULL 2:1 within each arm), in id_in_subsession order. Exact balance
    in every complete block; replaces independent per-participant coin flips,
    whose HIGH/LOW split has SD ~13 over 720 recruits."""
    rng = random.Random(f"blocks-{seed}")
    out = []
    while len(out) < len(players):
        blk = BLOCK6[:]
        rng.shuffle(blk)
        out += blk
    return {p.id_in_subsession: out[i]
            for i, p in enumerate(sorted(players, key=lambda q: q.id_in_subsession))}


def _assign_factors(cfg, prng, balanced=None):
    """Delta 8: participant-level factor assignment for the main_confirmatory
    config. Per-cell session configs still fix both factors session-wide."""
    if cfg.get('assign_factors') == 'participant':
        return balanced
    return cfg.get('p2_regime', 'HIGH'), cfg.get('restoration', 'FULL')


def creating_session(subsession: Subsession):
    cfg = subsession.session.config
    if subsession.round_number != 1:
        return
    pool = _load_peer_pool(cfg)
    subsession.session.vars['peer_pool'] = pool
    players = subsession.get_players()
    balanced = _balanced_assignment(players, cfg.get('session_seed', 20261104))
    for p in players:
        part = p.participant
        prng = random.Random(f"{cfg.get('session_seed', 20261104)}-{part.code}")
        part.vars['good_side'] = prng.choice(['left', 'right'])
        part.vars['good_ticket'] = prng.choice(list(C.TICKETS))
        p2, resto = _assign_factors(cfg, prng, balanced[p.id_in_subsession])
        part.vars['p2_regime'] = p2
        part.vars['restoration'] = resto
        part.vars['schedule'] = cfg.get('schedule', 'standard')
        part.vars['outcomes'] = _gen_outcomes(prng, resto, part.vars['schedule'])
        others = [prng.choice(['HIGH', 'LOW']), prng.choice(['HIGH', 'LOW'])]
        part.vars['regimes'] = {1: others[0], 2: p2, 3: others[1]}
        part.vars['points'] = 0
        part.vars['wtp_left'] = C.WTP_ENDOWMENT
        part.vars['reseed_count'] = 0
        part.vars['block_own'] = {}        # AUDIT: realized own rate per block


def _phase_p(rn, restoration, schedule):
    if schedule == 'rich':
        return C.RICH_P
    return C.PHASE_P.get(rn) or C.RESTORATION[restoration]


def _gen_outcomes(prng, restoration, schedule='standard', start_t=0):
    """Settlement sequences for trials start_t..449 (delta 2 + delta 4's
    truthful re-seed hook regenerates the tail with the SAME process)."""
    seqs = {'good': [], 'bad': []}
    for t in range(start_t, C.NUM_ROUNDS * C.TRIALS_PER_BLOCK):
        pg, pb = _phase_p(t // C.TRIALS_PER_BLOCK + 1, restoration, schedule)
        seqs['good'].append(1 if prng.random() < pg else 0)
        seqs['bad'].append(1 if prng.random() < pb else 0)
    return seqs


def _block_rates(earn):
    return [sum(earn[b * 150:(b + 1) * 150]) / 150.0 for b in range(3)]


def _load_peer_pool(cfg):
    """Delta 7 + AUDIT. Production: pool built by tools/make_pool_from_pilot.py
    from real prior-participant streams (schedule, per-block rates, variance
    terciles, provenance). The dev placeholder is SIMULATED and therefore refused
    whenever oTree runs in production mode (OTREE_PRODUCTION set) unless the
    session is a bot session; this closes the path by which a human session could
    silently display simulated peers."""
    path = cfg.get('peer_pool_path', '')
    if path:
        with open(path) as f:
            pool = json.load(f)
        assert not pool.get('placeholder'), \
            'placeholder pool loaded via peer_pool_path — refuse'
        return pool
    if os.environ.get('OTREE_PRODUCTION') and not cfg.get('bot_kind'):
        raise RuntimeError('No peer_pool_path for a human session in production: '
                           'the simulated placeholder pool is never shown to people.')
    rng = random.Random(99)
    pool = {'placeholder': True, 'streams': []}
    # dev placeholder mimics the two real source schedules so selection logic is
    # exercised: deprivation streams (P2 ~ .25) and rich streams (~ .6 throughout)
    for sched, rates in (('standard-MODERATE', (.60, .25, .42)),
                         ('standard-FULL', (.60, .25, .58)),
                         ('rich', (.60, .62, .62))):
        for k in range(12):
            earn = []
            for b in range(3):
                r = rates[b] + 0.06 * (rng.random() - 0.5)
                earn += [1 if rng.random() < r else 0 for _ in range(150)]
            pool['streams'].append({'id': f'dev-{sched}-{k}', 'schedule': sched,
                                    'block_rates': _block_rates(earn),
                                    'var_tercile': k % 3, 'earnings': earn})
    return pool


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    consent = models.BooleanField(initial=False)
    comprehension_ok = models.BooleanField(initial=False)
    block_regime = models.StringField(initial='')
    peer_stream_id = models.StringField(initial='')
    block_points = models.IntegerField(initial=0)
    resumes = models.IntegerField(initial=0)          # AUDIT: page reloads mid-block
    # I032 C#7: comprehension quiz, repeat until correct (Oppenheimer et al.
    # 2009 prefer prompting rereading to excluding failers). No exclusion.
    cq_cost = models.StringField(
        label='Do you pay for the tickets you choose?',
        choices=['No — tickets are free (house-funded)', 'Yes — each costs a point'],
        widget=widgets.RadioSelect)
    cq_prices = models.StringField(
        label='Do the displayed market prices change during your session?',
        choices=['No — they are held fixed', 'Yes — other traders move them'],
        widget=widgets.RadioSelect)
    cq_draws = models.StringField(
        label='How is each settlement decided?',
        choices=['By a rule fixed before my session, using pre-drawn random draws',
                 'By the experimenter, live, as I play'],
        widget=widgets.RadioSelect)
    cq_board = models.StringField(
        label='Who is shown on the trader board?',
        choices=['A real participant who previously completed this task',
                 'A computer simulation'],
        widget=widgets.RadioSelect)
    cq_attempts = models.IntegerField(initial=0)
    # delta 6: believability / funnel block (round 3 only)
    peer_success = models.IntegerField(min=1, max=7, blank=True)
    peer_real = models.IntegerField(min=1, max=7, blank=True)
    rig_suspicion = models.IntegerField(min=1, max=7, blank=True)
    betting_familiarity = models.IntegerField(min=1, max=7, blank=True)
    purpose_guess = models.LongStringField(blank=True)
    age = models.IntegerField(min=18, max=99, blank=True)
    gender = models.StringField(blank=True)
    # AUDIT: forecast bonus actually paid (promised in the instructions)
    bsr_paid_t = models.IntegerField(initial=-1)
    bsr_bonus = models.IntegerField(initial=0)


class Trial(ExtraModel):
    player = models.Link(Player)
    t = models.IntegerField()
    block = models.IntegerField()
    phase = models.IntegerField()
    regime = models.StringField()
    choice_good = models.IntegerField()
    side = models.StringField()
    ticket = models.StringField()
    reward = models.IntegerField()
    bonus = models.IntegerField()
    peer_reward = models.IntegerField()
    peer_rate = models.FloatField()
    price_good = models.IntegerField()
    rt_ms = models.IntegerField()


class Rating(ExtraModel):
    player = models.Link(Player)
    t = models.IntegerField()
    fairness = models.IntegerField()
    entitlement = models.IntegerField()
    fairness_init = models.IntegerField()      # delta 11: randomized starts
    entitlement_init = models.IntegerField()
    rt_ms = models.IntegerField()


class BsrReport(ExtraModel):                    # delta 3
    player = models.Link(Player)
    t = models.IntegerField()
    report = models.IntegerField()              # 0..100 chance SQUARE pays next round
    outcome = models.IntegerField()             # that settlement (index t = trial t+1)
    report_init = models.IntegerField()
    rt_ms = models.IntegerField()


class WtpProbe(ExtraModel):                     # delta 4
    player = models.Link(Player)
    t = models.IntegerField()
    probe = models.StringField()                # endP2 / midP3
    wtp = models.IntegerField()                 # stated max price 0..20
    price_drawn = models.IntegerField()
    switched = models.IntegerField()
    rt_ms = models.IntegerField()


# ----------------------------- live trial engine ---------------------------------

def _pick_peer_stream(player: Player, pool, regime, rng):
    """AUDIT rewrite. Selection is on the rate of the stream IN THE CURRENT BLOCK
    WINDOW (what the participant will actually see), never on the 450-trial rate.
    HIGH: block rate in the session's high band, stratified on variance tercile;
    under the standard schedule only rich-schedule streams can satisfy this in P2.
    LOW: a same-schedule stream (same restoration level) whose PREVIOUS-block rate
    is within +/- tol of the participant's own previous-block rate, so its
    current-block experience tracks the participant's own (prospective yoking);
    block 1: any same-schedule stream."""
    cfg = player.session.config
    part = player.participant
    rn = player.round_number
    b = rn - 1
    streams = pool['streams']
    if regime == 'HIGH':
        lo, hi = cfg.get('high_band', C.HIGH_BAND_DEFAULT)
        cands = [s for s in streams if lo <= s['block_rates'][b] <= hi]
        if cands and any('var_tercile' in s for s in cands):
            terc = rng.choice(sorted({s.get('var_tercile', 0) for s in cands}))
            cands = [s for s in cands if s.get('var_tercile', 0) == terc] or cands
        if not cands:   # logged via peer_stream_id; nearest in-window rate
            mid = (lo + hi) / 2
            cands = sorted(streams, key=lambda s: abs(s['block_rates'][b] - mid))[:3]
    else:
        sched = f"standard-{part.vars['restoration']}"
        same = [s for s in streams if s.get('schedule') == sched] or streams
        if b == 0:
            cands = same
        else:
            own_prev = part.vars['block_own'].get(str(rn - 1), 0.5)
            cands = [s for s in same
                     if abs(s['block_rates'][b - 1] - own_prev) <= C.LOW_BAND_TOL]
            if not cands:
                cands = sorted(same, key=lambda s: abs(s['block_rates'][b - 1]
                                                       - own_prev))[:3]
    return rng.choice(cands)


def _slider_every(player: Player) -> int:
    return player.session.config.get('slider_every', C.SLIDER_EVERY_DEFAULT)


def _peer_display_rate(peer, t, window):
    """Rate over the peer's last `window` rounds up to round t (AUDIT: matches the
    certified generator's reference — own band under LOW, ~mu_ref under HIGH —
    in a single statistic shown identically in both arms). window=0: cumulative."""
    if window and window > 0:
        seg = peer[max(0, t - window):t]
    else:
        seg = peer[:t]
    return sum(seg) / len(seg)


def _resume_payload(player, state):
    part = player.participant
    rn = player.round_number
    tib = state['t_in_block']
    prices = player.session.config.get('phase_prices', C.PHASE_PRICES_DEFAULT)
    return {'type': 'trial', 't': total_trial(rn, min(tib + 1, C.TRIALS_PER_BLOCK)),
            'good_side': part.vars['good_side'],
            'good_ticket': part.vars['good_ticket'],
            'prices': prices[rn], 'points': part.vars['points'],
            'pending': list(state.get('pending', [])),
            'block_done': tib >= C.TRIALS_PER_BLOCK and not state.get('pending')}


def live_trial(player: Player, data):
    part = player.participant
    sv = player.session.vars
    rn = player.round_number
    key = f'live_{rn}'                       # AUDIT: per-block state, survives reload
    msg = data.get('type')

    if msg == 'start':
        state = part.vars.get(key)
        if state is not None:                # AUDIT: reload mid-block -> resume
            player.resumes += 1
            return {player.id_in_group: _resume_payload(player, state)}
        rng = random.Random(f"live-{part.code}-{rn}")
        player.block_regime = part.vars['regimes'][rn]
        stream = _pick_peer_stream(player, sv['peer_pool'], player.block_regime, rng)
        player.peer_stream_id = stream['id']
        state = {'peer': stream['earnings'], 't_in_block': 0, 'pending': [],
                 'block_hits': 0}
        part.vars[key] = state
        return {player.id_in_group: _resume_payload(player, state)}

    state = part.vars.get(key)
    if state is None:
        return {player.id_in_group: {'type': 'noop'}}

    if msg == 'choice':
        # AUDIT guards: no choice while a modal is owed, none past the block end
        if state['pending'] or state['t_in_block'] >= C.TRIALS_PER_BLOCK:
            return {player.id_in_group: _resume_payload(player, state)}
        state['t_in_block'] += 1
        tib = state['t_in_block']
        t = total_trial(rn, tib)
        side = data['side']
        chose_good = int(side == part.vars['good_side'])
        arm = 'good' if chose_good else 'bad'
        ticket = part.vars['good_ticket'] if chose_good else \
            [x for x in C.TICKETS if x != part.vars['good_ticket']][0]
        reward = part.vars['outcomes'][arm][t - 1]
        bonus = C.BONUS_POINTS if t % C.BONUS_EVERY == 0 else 0
        peer_r = state['peer'][t - 1]
        window = player.session.config.get('peer_display_window', C.PEER_DISPLAY_WINDOW)
        peer_rate = _peer_display_rate(state['peer'], t, window)
        part.vars['points'] += reward + bonus
        player.block_points += reward + bonus
        state['block_hits'] += reward
        part.vars['block_own'][str(rn)] = state['block_hits'] / tib
        prices = player.session.config.get('phase_prices', C.PHASE_PRICES_DEFAULT)
        Trial.create(player=player, t=t, block=rn, phase=rn,
                     regime=player.block_regime, choice_good=chose_good, side=side,
                     ticket=ticket, reward=reward, bonus=bonus, peer_reward=peer_r,
                     peer_rate=round(peer_rate, 4), price_good=prices[rn][0],
                     rt_ms=int(data.get('rt_ms', -1)))
        pending = []
        if t in C.WTP_TRIALS:
            pending.append('wtp')
        if t % C.BSR_EVERY == C.BSR_OFFSET:
            pending.append('bsr')
        if t % _slider_every(player) == 0:
            pending.append('rating')
        state['pending'] = pending
        resp = {'type': 'feedback', 't': t, 'reward': reward, 'bonus': bonus,
                'peer_reward': peer_r, 'peer_rate': round(peer_rate, 3),
                'points': part.vars['points'],
                'ask_rating': 'rating' in pending, 'ask_bsr': 'bsr' in pending,
                'ask_wtp': 'wtp' in pending,
                'block_done': tib >= C.TRIALS_PER_BLOCK}
        return {player.id_in_group: resp}

    if msg in ('rating', 'bsr', 'wtp') and msg not in state['pending']:
        # AUDIT: duplicate / unsolicited submission (e.g. double click, reload)
        return {player.id_in_group: {'type': f'{msg}_ok', 'duplicate': True,
                                     'block_done': state['t_in_block'] >= C.TRIALS_PER_BLOCK
                                     and not state['pending']}}

    tib = state['t_in_block']
    t = total_trial(rn, tib)

    if msg == 'rating':
        Rating.create(player=player, t=t,
                      fairness=int(data['fairness']),
                      entitlement=int(data['entitlement']),
                      fairness_init=int(data.get('fairness_init', -1)),
                      entitlement_init=int(data.get('entitlement_init', -1)),
                      rt_ms=int(data.get('rt_ms', -1)))
        state['pending'].remove('rating')
        done = tib >= C.TRIALS_PER_BLOCK and not state['pending']
        return {player.id_in_group: {'type': 'rating_ok', 'block_done': done}}

    if msg == 'bsr':                                   # delta 3
        # Forecast of the NEXT round's SQUARE settlement (index t = trial t+1);
        # t % 15 == 7 keeps t <= 442 so a next round always exists; WTP rounds
        # (300, 375) never coincide, so a re-draw cannot race a forecast.
        sq_arm = 'good' if part.vars['good_ticket'] == 'SQUARE' else 'bad'
        outcome = part.vars['outcomes'][sq_arm][t]
        BsrReport.create(player=player, t=t, report=int(data['report']),
                         outcome=int(outcome),
                         report_init=int(data.get('report_init', -1)),
                         rt_ms=int(data.get('rt_ms', -1)))
        state['pending'].remove('bsr')
        return {player.id_in_group: {'type': 'bsr_ok'}}

    if msg == 'wtp':                                   # delta 4
        probe = 'endP2' if t <= 300 else 'midP3'
        wtp = max(0, min(C.WTP_ENDOWMENT, int(data['wtp'])))
        drng = random.Random(f"wtp-{part.code}-{t}")
        price = drng.randint(1, C.WTP_ENDOWMENT)
        switched = int(wtp >= price)
        if switched:
            part.vars['wtp_left'] -= price
            part.vars['reseed_count'] += 1
            # truthful re-draw: regenerate the REMAINING settlement draws with the
            # same generative process (phase rates unaffected)
            rseed = random.Random(f"reseed-{part.code}-{t}-{part.vars['reseed_count']}")
            tail = _gen_outcomes(rseed, part.vars['restoration'],
                                 part.vars['schedule'], start_t=t)
            for armk in ('good', 'bad'):
                part.vars['outcomes'][armk][t:] = tail[armk]
        WtpProbe.create(player=player, t=t, probe=probe, wtp=wtp,
                        price_drawn=price, switched=switched,
                        rt_ms=int(data.get('rt_ms', -1)))
        state['pending'].remove('wtp')
        return {player.id_in_group: {'type': 'wtp_ok', 'switched': switched,
                                     'price': price,
                                     'wtp_left': part.vars['wtp_left']}}

    return {player.id_in_group: {'type': 'noop'}}


# ----------------------------------- pages ---------------------------------------

class Intro(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    form_model = 'player'
    form_fields = ['consent']

    @staticmethod
    def vars_for_template(player: Player):
        cfg = player.session.config
        return dict(skin=cfg.get('skin', 'market'),
                    framing=cfg.get('framing', 'standard'),
                    wtp_endowment=C.WTP_ENDOWMENT)

    @staticmethod
    def error_message(player: Player, values):
        if not values['consent']:
            return "Consent is required to take part."


CQ_KEY = {
    'cq_cost': 'No — tickets are free (house-funded)',
    'cq_prices': 'No — they are held fixed',
    'cq_draws': 'By a rule fixed before my session, using pre-drawn random draws',
    'cq_board': 'A real participant who previously completed this task',
}


class Comprehension(Page):
    """I032 C#7. Shown only for the market skin; repeat until correct; the
    attempt count is recorded (descriptive), never an exclusion criterion."""
    form_model = 'player'
    form_fields = list(CQ_KEY)

    @staticmethod
    def is_displayed(player: Player):
        return (player.round_number == 1 and
                player.session.config.get('skin', 'market') == 'market')

    @staticmethod
    def error_message(player: Player, values):
        player.cq_attempts += 1
        wrong = [k for k, v in CQ_KEY.items() if values.get(k) != v]
        if wrong:
            return {k: 'Not quite — see the instructions: ' + {
                'cq_cost': 'tickets are house-funded; you never pay for one.',
                'cq_prices': 'the market maker\'s quotes are held fixed.',
                'cq_draws': 'settlements come from a rule fixed in advance with '
                            'pre-drawn random draws.',
                'cq_board': 'the board shows a real previous participant.',
            }[k] for k in wrong}

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.comprehension_ok = True


class Block(Page):
    live_method = live_trial

    @staticmethod
    def js_vars(player: Player):
        cfg = player.session.config
        return dict(slider_every=_slider_every(player),
                    trials_per_block=C.TRIALS_PER_BLOCK,
                    block=player.round_number,
                    skin=cfg.get('skin', 'market'),
                    tickets=list(C.TICKETS),
                    iti_jitter_ms=cfg.get('iti_jitter_ms'),
                    peer_window=cfg.get('peer_display_window', C.PEER_DISPLAY_WINDOW))


class Funnel(Page):                                    # delta 6
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    form_model = 'player'
    form_fields = ['peer_success', 'peer_real', 'rig_suspicion',
                   'betting_familiarity', 'purpose_guess', 'age', 'gender']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        _settle_forecast_bonus(player)


def _settle_forecast_bonus(player: Player):
    """AUDIT: pay the forecast bonus exactly as the instructions state — one
    forecast round drawn at random; prize with probability 1 - (o - f)^2, f on
    the 0-1 scale. Idempotent (settled once, seeded by participant code)."""
    part = player.participant
    if part.vars.get('bsr_settled'):
        return
    reports = [r for p in player.in_all_rounds() for r in BsrReport.filter(player=p)]
    if reports:
        drng = random.Random(f"bsr-pay-{part.code}")
        r = drng.choice(reports)
        prob = 1.0 - (r.outcome - r.report / 100.0) ** 2
        won = drng.random() < prob
        player.bsr_paid_t = r.t
        player.bsr_bonus = C.BSR_PRIZE if won else 0
        part.vars['points'] += player.bsr_bonus
    part.vars['bsr_settled'] = True


class Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        _settle_forecast_bonus(player)                 # no-op if already settled
        pts = player.participant.vars.get('points', 0)
        wtp_left = player.participant.vars.get('wtp_left', C.WTP_ENDOWMENT)
        rate = player.session.config.get('points_to_currency', 0.0035)
        player.payoff = (pts + wtp_left) * rate
        return dict(points=pts, wtp_left=wtp_left, bsr_bonus=player.bsr_bonus,
                    money=cu((pts + wtp_left) * rate))


page_sequence = [Intro, Comprehension, Block, Funnel, Results]


# ----------------------------- custom export -------------------------------------

EXPORT_HEADER = ['row_type', 'session', 'participant', 'cell_p2_regime', 'restoration',
                 'bot_kind', 't', 'block', 'regime', 'choice_good', 'reward', 'bonus',
                 'peer_reward', 'peer_rate', 'fairness', 'entitlement', 'rt_ms',
                 'fairness_init', 'entitlement_init', 'bsr_report', 'bsr_outcome',
                 'wtp', 'wtp_probe', 'wtp_switched', 'peer_success', 'peer_real',
                 'rig_suspicion', 'purpose_guess',
                 # AUDIT additions (appended so earlier column positions hold)
                 'config_name', 'skin', 'framing', 'schedule', 'peer_stream_id',
                 'betting_familiarity', 'cq_attempts', 'age', 'gender',
                 'bsr_paid_t', 'bsr_bonus', 'resumes', 'payoff', 'ticket']


def custom_export(players):
    yield EXPORT_HEADER
    n = len(EXPORT_HEADER)
    for p in players:
        cfg = p.session.config
        part = p.participant
        base = [p.session.code, part.code,
                part.vars.get('p2_regime', cfg.get('p2_regime', '')),
                part.vars.get('restoration', cfg.get('restoration', '')),
                cfg.get('bot_kind', 'human')]
        tail = [cfg.get('name', ''), cfg.get('skin', 'market'),
                cfg.get('framing', 'standard'), part.vars.get('schedule', 'standard'),
                p.peer_stream_id]

        def row(kind, cols):
            r = [kind] + base + cols
            r += [''] * (28 - len(r))
            r += tail + [''] * (n - 28 - len(tail))
            return r

        for tr in Trial.filter(player=p):
            r = row('trial', [tr.t, tr.block, tr.regime, tr.choice_good, tr.reward,
                              tr.bonus, tr.peer_reward, tr.peer_rate, '', '', tr.rt_ms])
            r[-1] = tr.ticket
            yield r
        for r in Rating.filter(player=p):
            yield row('rating', [r.t, '', '', '', '', '', '', '', r.fairness,
                                 r.entitlement, r.rt_ms, r.fairness_init,
                                 r.entitlement_init])
        for b in BsrReport.filter(player=p):
            yield row('bsr', [b.t, '', '', '', '', '', '', '', '', '', b.rt_ms, '', '',
                              b.report, b.outcome])
        for w in WtpProbe.filter(player=p):
            yield row('wtp', [w.t, '', '', '', '', '', '', '', '', '', w.rt_ms, '', '',
                              '', '', w.wtp, w.probe, w.switched])
        if p.round_number == C.NUM_ROUNDS:
            r = row('funnel', [''] * 11 + [''] * 7 +
                    [p.field_maybe_none('peer_success') or '',
                     p.field_maybe_none('peer_real') or '',
                     p.field_maybe_none('rig_suspicion') or '',
                     (p.field_maybe_none('purpose_guess') or '').replace('\n', ' ')])
            first = p.in_round(1)
            r[28 + len(tail):n - 1] = [p.field_maybe_none('betting_familiarity') or '',
                                  first.cq_attempts,
                                  p.field_maybe_none('age') or '',
                                  p.field_maybe_none('gender') or '',
                                  p.bsr_paid_t, p.bsr_bonus,
                                  sum(q.resumes for q in p.in_all_rounds()),
                                  p.participant.payoff]
            yield r


# ----------------------------------- bots ----------------------------------------
# Pipeline-validation bots. Their data is labeled by session config bot_kind and
# is never evidence about humans. The DISS bot runs the frozen single-agent gate.

class DissAgent:
    """Frozen defaults (I002): nuF=.05, nuR=.0125, tauF=.3, phi-=1, phi+=.25,
    alpha=.2, softmax beta=12. rho/chi vary per bot id (slow/fast; anchored/own)."""

    def __init__(self, seed, rho, chi, a0=0.8):
        self.rng = random.Random(seed)
        self.nuF, self.nuR, self.tauF = 0.05, 0.0125, 0.3
        self.phim, self.phip, self.alpha, self.beta = 1.0, 0.25, 0.2, 12.0
        self.rho, self.chi = rho, chi
        self.Q = {'good': 0.5, 'bad': 0.5}
        self.L, self.A = 1.0, a0

    def choose(self, good_side):
        import math
        dq = self.Q['good'] - self.Q['bad']
        p_good = 1.0 / (1.0 + math.exp(-self.beta * dq))
        if self.rng.random() < p_good:
            return good_side, 'good'
        return ('left' if good_side == 'right' else 'right'), 'bad'

    def update(self, arm, reward, peer_rate):
        self.Q[arm] += self.alpha * self.L * (reward - self.Q[arm])
        ref = (1 - self.chi) * reward + self.chi * peer_rate
        self.A += self.rho * (ref - self.A)
        d = self.phim * max(self.A - reward, 0) + self.phip * max(reward - self.A, 0)
        if d > self.tauF:
            self.L -= self.nuF * (d - self.tauF)
        else:
            self.L += self.nuR
        self.L = min(1.0, max(0.0, self.L))

    def ratings(self):
        return int(round(self.L * 100)), int(round(self.A * 100))


def _drain(agen):
    """oTree 6 bots: consume the wrapped live method's async generator."""
    import asyncio

    async def collect():
        out = {}
        async for item in agen:
            if item:
                out.update(item)
        return out

    try:
        return asyncio.run(collect())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(collect())
        finally:
            loop.close()


def call_live_method(method, **kwargs):
    """Bots. Config 'bot_refresh_test': each bot reloads the page (re-sends
    'start') mid-block, once with a modal owed, and submits a duplicate rating —
    the export must still hold exactly 450 trials / 90 ratings per participant."""
    group = kwargs['group']
    for p in group.get_players():
        part = p.participant
        cfg = p.session.config
        kind = cfg.get('bot_kind', 'random')
        refresh = cfg.get('bot_refresh_test', False)
        agent = part.vars.get('bot_agent')
        if kind == 'diss' and agent is None:
            rho = 0.002 if p.id_in_group % 2 == 1 else 0.02
            chi = 0.6 if (p.id_in_group // 2) % 2 == 1 else 0.0
            agent = DissAgent(seed=p.id_in_group * 7919, rho=rho, chi=chi)
            part.vars['bot_agent'] = agent
        rng = random.Random(p.id_in_group * 104729 + kwargs['round_number'])
        pid = p.id_in_group
        _drain(method(pid, {'type': 'start'}))
        good_side = part.vars['good_side']
        sq_is_good = part.vars['good_ticket'] == 'SQUARE'
        for i in range(C.TRIALS_PER_BLOCK):
            if refresh and i == 40:                       # plain reload
                _drain(method(pid, {'type': 'start'}))
            if kind == 'diss':
                side, arm = agent.choose(good_side)
            else:
                side = rng.choice(['left', 'right'])
                arm = 'good' if side == good_side else 'bad'
            fb = _drain(method(pid, {'type': 'choice', 'side': side,
                                     'rt_ms': rng.randint(350, 900)}))[pid]
            if refresh and fb.get('ask_rating') and i == 79:   # reload with modal owed
                res = _drain(method(pid, {'type': 'start'}))[pid]
                assert res['pending'] == ['rating'], res
                blocked = _drain(method(pid, {'type': 'choice', 'side': side}))[pid]
                assert blocked['type'] == 'trial', blocked     # choice refused
            if kind == 'diss':
                agent.update(arm, fb['reward'], fb['peer_rate'])
            if fb.get('ask_wtp'):
                w = (int(round(C.WTP_ENDOWMENT * (1.0 - agent.L))) if kind == 'diss'
                     else rng.randint(0, C.WTP_ENDOWMENT))
                _drain(method(pid, {'type': 'wtp', 'wtp': w,
                                    'rt_ms': rng.randint(600, 2500)}))
            if fb.get('ask_bsr'):
                if kind == 'diss':
                    q = agent.Q['good'] if sq_is_good else agent.Q['bad']
                    rep = int(round(100 * max(0.0, min(1.0, q))))
                else:
                    rep = rng.randint(0, 100)
                _drain(method(pid, {'type': 'bsr', 'report': rep,
                                    'report_init': rng.randint(0, 100),
                                    'rt_ms': rng.randint(400, 1500)}))
            if fb['ask_rating']:
                fair, ent = (agent.ratings() if kind == 'diss'
                             else (rng.randint(0, 100), rng.randint(0, 100)))
                msg = {'type': 'rating', 'fairness': fair, 'entitlement': ent,
                       'fairness_init': 5 * rng.randint(0, 20),
                       'entitlement_init': 5 * rng.randint(0, 20),
                       'rt_ms': rng.randint(400, 1500)}
                _drain(method(pid, msg))
                if refresh and i == 99:                    # duplicate submission
                    dup = _drain(method(pid, msg))[pid]
                    assert dup.get('duplicate'), dup


class PlayerBot(Bot):
    def play_round(self):
        if self.round_number == 1:
            yield Submission(Intro, {'consent': True}, check_html=False)
            if self.session.config.get('skin', 'market') == 'market':
                wrong = dict(CQ_KEY, cq_board='A computer simulation')
                yield SubmissionMustFail(Comprehension, wrong, check_html=False)
                yield Submission(Comprehension, dict(CQ_KEY), check_html=False)
        yield Submission(Block, check_html=False)
        if self.round_number == C.NUM_ROUNDS:
            yield Submission(Funnel,
                             {'peer_success': 5, 'peer_real': 6,
                              'rig_suspicion': 2, 'betting_familiarity': 3,
                              'purpose_guess': 'bot smoke', 'age': 30,
                              'gender': 'other'}, check_html=False)
            yield Results
