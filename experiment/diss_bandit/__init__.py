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
probability reports (exploratory, pilot-gated); WTP rule-switch probes at
end-P2 and mid-P3 (truthful re-seed); announced non-contingent windfall every
15th trial; believability/funnel block after the last block.

Build deltas 1-11 are enumerated in freezes/00_freeze_I032.yaml. Every numeric
default traces to the I006/I027/I029/I032 freezes. Bot data produced by this
app is for pipeline validation only.
"""
import json
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
    BSR_EVERY = 15                      # delta 3: probability report cadence
    BSR_OFFSET = 7                      # t % 15 == 7 (offset from windfalls/sliders)
    WTP_ENDOWMENT = 20                  # delta 4: dedicated endowment (points)
    WTP_TRIALS = (300, 375)             # end-P2, mid-P3 (global trial index)
    PHASE_P = {1: (0.65, 0.35), 2: (0.30, 0.15)}
    RESTORATION = {'FULL': (0.65, 0.35),
                   'MODERATE': (0.45, 0.35)}   # pilot-calibrated (open)
    HIGH_BAND_DEFAULT = (0.60, 0.70)    # mu_ref=.65 band; dose cells override
    LOW_BAND_TOL = 0.05
    TRAIL_WINDOW = 15
    # delta 1/2: truthful AMM display — prices fixed within phases. DESIGN-
    # DECISION (author review): default quote is 50/50 for the whole session
    # (a constant is the one within-phase-fixed schedule that cannot leak the
    # invisible phase boundaries); config 'phase_prices' can override.
    PHASE_PRICES_DEFAULT = {1: (50, 50), 2: (50, 50), 3: (50, 50)}
    TICKETS = ('SQUARE', 'TRIANGLE')


def total_trial(round_number: int, t_in_block: int) -> int:
    return (round_number - 1) * C.TRIALS_PER_BLOCK + t_in_block


class Subsession(BaseSubsession):
    pass


def _assign_factors(cfg, prng):
    """Delta 8: participant-level factor assignment for the main_confirmatory
    config (p2_regime 1:1; restoration MODERATE:FULL 2:1). Per-cell session
    configs still fix both factors session-wide (bots, pilot cells)."""
    if cfg.get('assign_factors') == 'participant':
        p2 = 'HIGH' if prng.random() < 0.5 else 'LOW'
        resto = 'MODERATE' if prng.random() < (2 / 3) else 'FULL'
        return p2, resto
    return cfg.get('p2_regime', 'HIGH'), cfg.get('restoration', 'FULL')


def creating_session(subsession: Subsession):
    cfg = subsession.session.config
    if subsession.round_number != 1:
        return
    pool = _load_peer_pool(cfg)
    subsession.session.vars['peer_pool'] = pool
    for p in subsession.get_players():
        part = p.participant
        prng = random.Random(f"{cfg.get('session_seed', 20261104)}-{part.code}")
        part.vars['good_side'] = prng.choice(['left', 'right'])
        part.vars['good_ticket'] = prng.choice(list(C.TICKETS))
        p2, resto = _assign_factors(cfg, prng)
        part.vars['p2_regime'] = p2
        part.vars['restoration'] = resto
        # pre-generated settlement sequences per arm (seeded, reproducible)
        part.vars['outcomes'] = _gen_outcomes(prng, resto, start_t=0)
        # block regime sequence: P2 regime = Factor A; P1/P3 counterbalanced
        others = [prng.choice(['HIGH', 'LOW']), prng.choice(['HIGH', 'LOW'])]
        part.vars['regimes'] = {1: others[0], 2: p2, 3: others[1]}
        part.vars['points'] = 0
        part.vars['wtp_left'] = C.WTP_ENDOWMENT
        part.vars['reseed_count'] = 0


def _gen_outcomes(prng, restoration, start_t=0):
    """Settlement sequences for trials start_t..449 (delta 2 + delta 4's
    truthful re-seed hook regenerates the tail with the SAME process)."""
    seqs = {'good': [], 'bad': []}
    for t in range(start_t, C.NUM_ROUNDS * C.TRIALS_PER_BLOCK):
        rn = t // C.TRIALS_PER_BLOCK + 1
        pg, pb = C.PHASE_P.get(rn) or C.RESTORATION[restoration]
        seqs['good'].append(1 if prng.random() < pg else 0)
        seqs['bad'].append(1 if prng.random() < pb else 0)
    return seqs


def _load_peer_pool(cfg):
    """Delta 7: yoked peer streams. Production: pilot-sourced pool built by
    tools/make_pool_from_pilot.py (real prior-participant streams, provenance
    metadata, stratified HIGH selection; no deception). Dev/bots: placeholder
    pool, FLAGGED, never for human sessions."""
    path = cfg.get('peer_pool_path', '')
    if path:
        with open(path) as f:
            pool = json.load(f)
        assert not pool.get('placeholder'), \
            'placeholder pool loaded via peer_pool_path — refuse'
        return pool
    rng = random.Random(99)
    pool = {'placeholder': True, 'streams': []}
    for band_lo in (0.15, 0.30, 0.45, 0.60):
        for k in range(8):
            rate = band_lo + 0.05 + 0.02 * rng.random()
            stream = [1 if rng.random() < rate else 0 for _ in range(450)]
            pool['streams'].append(
                {'id': f'dev-{band_lo:.2f}-{k}', 'rate': sum(stream) / 450.0,
                 'var_tercile': k % 3, 'earnings': stream})
    return pool


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    consent = models.BooleanField(initial=False)
    comprehension_ok = models.BooleanField(initial=False)
    block_regime = models.StringField(initial='')
    peer_stream_id = models.StringField(initial='')
    block_points = models.IntegerField(initial=0)
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
    report = models.IntegerField()              # 0..100 chance good ticket pays
    outcome = models.IntegerField()             # realized settlement that trial
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

def _pick_peer_stream(player: Player, pool, regime, trail_rate, rng):
    """HIGH: band from config (dose cells override), stratified on trajectory-
    variance tercile when the pool provides it (delta 7). LOW: own band."""
    cfg = player.session.config
    streams = pool['streams']
    if regime == 'HIGH':
        lo, hi = cfg.get('high_band', C.HIGH_BAND_DEFAULT)
        cands = [s for s in streams if lo <= s['rate'] <= hi]
        if cands and any('var_tercile' in s for s in cands):
            terc = rng.choice(sorted({s.get('var_tercile', 0) for s in cands}))
            strat = [s for s in cands if s.get('var_tercile', 0) == terc]
            cands = strat or cands
    else:
        cands = [s for s in streams
                 if abs(s['rate'] - trail_rate) <= C.LOW_BAND_TOL]
        if not cands:
            cands = sorted(streams, key=lambda s: abs(s['rate'] - trail_rate))[:3]
    return rng.choice(cands) if cands else streams[0]


def _slider_every(player: Player) -> int:
    return player.session.config.get('slider_every', C.SLIDER_EVERY_DEFAULT)


def live_trial(player: Player, data):
    part = player.participant
    sv = player.session.vars
    state = part.vars.setdefault('live', {})
    rng = random.Random(f"live-{part.code}-{player.round_number}")

    if data.get('type') == 'start':
        player.block_regime = part.vars['regimes'][player.round_number]
        trail = part.vars.get('trail_rate', 0.5)
        stream = _pick_peer_stream(player, sv['peer_pool'], player.block_regime,
                                   trail, rng)
        player.peer_stream_id = stream['id']
        state['peer'] = stream['earnings']
        state['t_in_block'] = 0
        state['recent'] = part.vars.get('recent', [])
        prices = player.session.config.get('phase_prices',
                                           C.PHASE_PRICES_DEFAULT)
        return {player.id_in_group: {'type': 'trial',
                                     't': total_trial(player.round_number, 1),
                                     'good_side': part.vars['good_side'],
                                     'good_ticket': part.vars['good_ticket'],
                                     'prices': prices[player.round_number]}}

    if data.get('type') == 'choice':
        state['t_in_block'] += 1
        tib = state['t_in_block']
        t = total_trial(player.round_number, tib)
        side = data['side']
        chose_good = int(side == part.vars['good_side'])
        arm = 'good' if chose_good else 'bad'
        ticket = part.vars['good_ticket'] if chose_good else \
            [x for x in C.TICKETS if x != part.vars['good_ticket']][0]
        reward = part.vars['outcomes'][arm][t - 1]
        bonus = C.BONUS_POINTS if t % C.BONUS_EVERY == 0 else 0
        peer_r = state['peer'][t - 1]
        peer_rate = sum(state['peer'][:t]) / t
        part.vars['points'] += reward + bonus
        player.block_points += reward + bonus
        state['recent'] = (state['recent'] + [reward])[-C.TRAIL_WINDOW:]
        part.vars['recent'] = state['recent']
        part.vars['trail_rate'] = sum(state['recent']) / len(state['recent'])
        prices = player.session.config.get('phase_prices',
                                           C.PHASE_PRICES_DEFAULT)
        Trial.create(player=player, t=t, block=player.round_number,
                     phase=player.round_number, regime=player.block_regime,
                     choice_good=chose_good, side=side, ticket=ticket,
                     reward=reward, bonus=bonus,
                     peer_reward=peer_r, peer_rate=round(peer_rate, 4),
                     price_good=prices[player.round_number][0],
                     rt_ms=int(data.get('rt_ms', -1)))
        resp = {'type': 'feedback', 't': t, 'reward': reward, 'bonus': bonus,
                'peer_reward': peer_r, 'peer_rate': round(peer_rate, 3),
                'points': part.vars['points'],
                'ask_rating': t % _slider_every(player) == 0,
                'ask_bsr': t % C.BSR_EVERY == C.BSR_OFFSET,
                'ask_wtp': t in C.WTP_TRIALS,
                'block_done': tib >= C.TRIALS_PER_BLOCK}
        return {player.id_in_group: resp}

    if data.get('type') == 'rating':
        t = total_trial(player.round_number, state.get('t_in_block', 0))
        Rating.create(player=player, t=t,
                      fairness=int(data['fairness']),
                      entitlement=int(data['entitlement']),
                      fairness_init=int(data.get('fairness_init', -1)),
                      entitlement_init=int(data.get('entitlement_init', -1)),
                      rt_ms=int(data.get('rt_ms', -1)))
        done = state.get('t_in_block', 0) >= C.TRIALS_PER_BLOCK
        return {player.id_in_group: {'type': 'rating_ok', 'block_done': done}}

    if data.get('type') == 'bsr':                      # delta 3
        tib = state.get('t_in_block', 0)
        t = total_trial(player.round_number, tib)
        # The report is a FORECAST of the NEXT round's SQUARE settlement,
        # scored against that settlement (0-based index t = trial t+1). I032 D
        # audit fix: the first build scored it against the round just settled,
        # which a SQUARE chooser had already seen. Cadence t % 15 == 7 keeps
        # t <= 442, so a next round always exists.
        sq_arm = 'good' if part.vars['good_ticket'] == 'SQUARE' else 'bad'
        outcome = part.vars['outcomes'][sq_arm][t] if tib else -1
        BsrReport.create(player=player, t=t, report=int(data['report']),
                         outcome=int(outcome),
                         report_init=int(data.get('report_init', -1)),
                         rt_ms=int(data.get('rt_ms', -1)))
        return {player.id_in_group: {'type': 'bsr_ok'}}

    if data.get('type') == 'wtp':                      # delta 4
        tib = state.get('t_in_block', 0)
        t = total_trial(player.round_number, tib)
        probe = 'endP2' if t <= 300 else 'midP3'
        wtp = max(0, min(C.WTP_ENDOWMENT, int(data['wtp'])))
        drng = random.Random(f"wtp-{part.code}-{t}")
        price = drng.randint(1, C.WTP_ENDOWMENT)
        switched = int(wtp >= price)
        if switched:
            part.vars['wtp_left'] -= price
            part.vars['reseed_count'] += 1
            # truthful re-seed: regenerate the REMAINING settlement tail with
            # the same generative process (phase schedule unaffected)
            rseed = random.Random(f"reseed-{part.code}-{t}-"
                                  f"{part.vars['reseed_count']}")
            tail = _gen_outcomes(rseed, part.vars['restoration'], start_t=t)
            for armk in ('good', 'bad'):
                part.vars['outcomes'][armk][t:] = tail[armk]
        WtpProbe.create(player=player, t=t, probe=probe, wtp=wtp,
                        price_drawn=price, switched=switched,
                        rt_ms=int(data.get('rt_ms', -1)))
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
        return dict(slider_every=_slider_every(player),
                    trials_per_block=C.TRIALS_PER_BLOCK,
                    block=player.round_number,
                    skin=player.session.config.get('skin', 'market'),
                    tickets=list(C.TICKETS),
                    iti_jitter_ms=player.session.config.get('iti_jitter_ms'))


class Funnel(Page):                                    # delta 6
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    form_model = 'player'
    form_fields = ['peer_success', 'peer_real', 'rig_suspicion',
                   'betting_familiarity', 'purpose_guess', 'age', 'gender']


class Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        pts = player.participant.vars.get('points', 0)
        wtp_left = player.participant.vars.get('wtp_left', C.WTP_ENDOWMENT)
        rate = player.session.config.get('points_to_currency', 0.02)
        player.payoff = (pts + wtp_left) * rate
        return dict(points=pts, wtp_left=wtp_left,
                    money=cu((pts + wtp_left) * rate))


page_sequence = [Intro, Comprehension, Block, Funnel, Results]


# ----------------------------- custom export -------------------------------------

def custom_export(players):
    yield ['row_type', 'session', 'participant', 'cell_p2_regime', 'restoration',
           'bot_kind', 't', 'block', 'regime', 'choice_good', 'reward', 'bonus',
           'peer_reward', 'peer_rate', 'fairness', 'entitlement', 'rt_ms',
           'fairness_init', 'entitlement_init', 'bsr_report', 'bsr_outcome',
           'wtp', 'wtp_probe', 'wtp_switched', 'peer_success', 'peer_real',
           'rig_suspicion', 'purpose_guess']
    for p in players:
        cfg = p.session.config
        part = p.participant
        base = [p.session.code, part.code,
                part.vars.get('p2_regime', cfg.get('p2_regime', '')),
                part.vars.get('restoration', cfg.get('restoration', '')),
                cfg.get('bot_kind', 'human')]
        pad = [''] * 11
        for tr in Trial.filter(player=p):
            yield (['trial'] + base +
                   [tr.t, tr.block, tr.regime, tr.choice_good, tr.reward,
                    tr.bonus, tr.peer_reward, tr.peer_rate, '', '', tr.rt_ms] +
                   pad)
        for r in Rating.filter(player=p):
            yield (['rating'] + base +
                   [r.t, '', '', '', '', '', '', '', r.fairness, r.entitlement,
                    r.rt_ms, r.fairness_init, r.entitlement_init] + [''] * 9)
        for b in BsrReport.filter(player=p):
            yield (['bsr'] + base +
                   [b.t, '', '', '', '', '', '', '', '', '', b.rt_ms, '', '',
                    b.report, b.outcome] + [''] * 7)
        for w in WtpProbe.filter(player=p):
            yield (['wtp'] + base +
                   [w.t, '', '', '', '', '', '', '', '', '', w.rt_ms, '', '',
                    '', '', w.wtp, w.probe, w.switched] + [''] * 4)
        if p.round_number == C.NUM_ROUNDS:
            yield (['funnel'] + base +
                   ['', '', '', '', '', '', '', '', '', '', ''] + [''] * 7 +
                   [p.field_maybe_none('peer_success') or '',
                    p.field_maybe_none('peer_real') or '',
                    p.field_maybe_none('rig_suspicion') or '',
                    (p.field_maybe_none('purpose_guess') or '').replace('\n', ' ')])


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
        dq = self.Q['good'] - self.Q['bad']
        import math
        p_good = 1.0 / (1.0 + math.exp(-self.beta * dq))
        pick_good = self.rng.random() < p_good
        if pick_good:
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
    group = kwargs['group']
    for p in group.get_players():
        part = p.participant
        kind = p.session.config.get('bot_kind', 'random')
        agent = part.vars.get('bot_agent')
        if kind == 'diss' and agent is None:
            rho = 0.002 if p.id_in_group % 2 == 1 else 0.02
            chi = 0.6 if (p.id_in_group // 2) % 2 == 1 else 0.0
            agent = DissAgent(seed=p.id_in_group * 7919, rho=rho, chi=chi)
            part.vars['bot_agent'] = agent
        rng = random.Random(p.id_in_group * 104729 + kwargs['round_number'])
        _drain(method(p.id_in_group, {'type': 'start'}))
        good_side = part.vars['good_side']
        for _ in range(C.TRIALS_PER_BLOCK):
            if kind == 'diss':
                side, arm = agent.choose(good_side)
            else:
                side = rng.choice(['left', 'right'])
                arm = 'good' if side == good_side else 'bad'
            out = _drain(method(p.id_in_group, {'type': 'choice', 'side': side,
                                                'rt_ms': rng.randint(350, 900)}))
            fb = out[p.id_in_group]
            if kind == 'diss':
                agent.update(arm, fb['reward'], fb['peer_rate'])
            if fb.get('ask_bsr'):
                if kind == 'diss':
                    rep = int(round(100 * max(0.0, min(1.0, agent.Q['good']))))
                else:
                    rep = rng.randint(0, 100)
                _drain(method(p.id_in_group,
                              {'type': 'bsr', 'report': rep,
                               'report_init': rng.randint(0, 100),
                               'rt_ms': rng.randint(400, 1500)}))
            if fb.get('ask_wtp'):
                if kind == 'diss':
                    w = int(round(C.WTP_ENDOWMENT * (1.0 - agent.L)))
                else:
                    w = rng.randint(0, C.WTP_ENDOWMENT)
                _drain(method(p.id_in_group,
                              {'type': 'wtp', 'wtp': w,
                               'rt_ms': rng.randint(600, 2500)}))
            if fb['ask_rating']:
                if kind == 'diss':
                    fair, ent = agent.ratings()
                else:
                    fair, ent = rng.randint(0, 100), rng.randint(0, 100)
                _drain(method(p.id_in_group,
                              {'type': 'rating', 'fairness': fair,
                               'entitlement': ent,
                               'fairness_init': rng.randint(0, 100),
                               'entitlement_init': rng.randint(0, 100),
                               'rt_ms': rng.randint(400, 1500)}))


class PlayerBot(Bot):
    def play_round(self):
        if self.round_number == 1:
            yield Submission(Intro, {'consent': True}, check_html=False)
            if self.session.config.get('skin', 'market') == 'market':
                yield Submission(Comprehension, dict(CQ_KEY), check_html=False)
        yield Submission(Block, check_html=False)
        if self.round_number == C.NUM_ROUNDS:
            yield Submission(Funnel,
                             {'peer_success': 5, 'peer_real': 6,
                              'rig_suspicion': 2, 'betting_familiarity': 3,
                              'purpose_guess': 'bot smoke', 'age': 30,
                              'gender': 'other'}, check_html=False)
            yield Results
