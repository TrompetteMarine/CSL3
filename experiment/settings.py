# diss-otree settings — task v3 market skin (I032; supersedes the I006 cells,
# which remain below for the pilot framing comparison and bot smoke runs).
from os import environ

BASE_CELL = dict(
    num_demo_participants=4,
    app_sequence=['diss_bandit'],
    # AUDIT: aligned to DESIGN.md §2 (base £4.20 + expected performance bonus ~£1.10).
    # ~315 points expected (≈203 settlements + 90 windfalls + ~8 forecast bonus +
    # ~15 unspent allowance) x £0.0035 ≈ £1.10. The I006 value (0.02) would have
    # paid ~£6.30 per participant, ~5.7x the budgeted bonus. Author to confirm.
    points_to_currency=0.0035,
    session_seed=20261104,
    peer_pool_path='',             # production: pilot-sourced pool (tools/)
    skin='market',                 # I032 default; 'bandit' = I006 skin
)

SESSION_CONFIGS = [
    # ---- main confirmatory run (delta 8: participant-level factors) --------
    dict(name='main_confirmatory', display_name='MAIN confirmatory '
         '(participant-level HIGH/LOW 1:1, MODERATE:FULL 2:1)',
         assign_factors='participant', **BASE_CELL),
    # ---- per-cell configs (pilot cells; session-level factors) -------------
    dict(name='cell_HIGH_FULL', display_name='Cell A=HIGH B=FULL',
         p2_regime='HIGH', restoration='FULL', **BASE_CELL),
    dict(name='cell_HIGH_MODERATE', display_name='Cell A=HIGH B=MODERATE',
         p2_regime='HIGH', restoration='MODERATE', **BASE_CELL),
    dict(name='cell_LOW_FULL', display_name='Cell A=LOW B=FULL',
         p2_regime='LOW', restoration='FULL', **BASE_CELL),
    dict(name='cell_LOW_MODERATE', display_name='Cell A=LOW B=MODERATE',
         p2_regime='LOW', restoration='MODERATE', **BASE_CELL),
    # ---- dose module (delta 5): mu_ref .45 / .55; .65 = the HIGH band ------
    dict(name='dose_45', display_name='DOSE mu_ref=.45 (HIGH-band .40-.50, MODERATE)',
         p2_regime='HIGH', restoration='MODERATE', high_band=(0.40, 0.50),
         **BASE_CELL),
    dict(name='dose_55', display_name='DOSE mu_ref=.55 (HIGH-band .50-.60, MODERATE)',
         p2_regime='HIGH', restoration='MODERATE', high_band=(0.50, 0.60),
         **BASE_CELL),
    # ---- framing probe (delta 9) -------------------------------------------
    dict(name='framing_probe', display_name='FRAMING group-contingent fixed-rate '
         '(HIGH x MODERATE)',
         p2_regime='HIGH', restoration='MODERATE', framing='group_fixed_rate',
         **BASE_CELL),
    # ---- pilot arms (delta 10: sparse; bandit skin for the framing check) --
    dict(name='pilot_sparse', display_name='PILOT sparse elicitation (every 10)',
         p2_regime='HIGH', restoration='MODERATE', slider_every=10, **BASE_CELL),
    dict(name='pilot_bandit_skin', display_name='PILOT bandit skin (same seeds)',
         p2_regime='HIGH', restoration='MODERATE',
         **{**BASE_CELL, 'skin': 'bandit'}),
    # ---- AUDIT: pool-source session with the RICH rule (.65/.35 in every phase).
    # Under the standard schedule nobody earns ~.65 in P2, so a truthful HIGH
    # trader board needs streams from participants who played under this rule
    # (disclosed by the 'one of several rules' line). Author decision: wording.
    dict(name='pool_rich', display_name='POOL source: rich rule all phases',
         p2_regime='LOW', restoration='FULL', schedule='rich', **BASE_CELL),
    # ---- pipeline-validation bot sessions (never human evidence) -----------
    dict(name='bots_random_HIGH_FULL', display_name='BOTS random (HIGH/FULL)',
         p2_regime='HIGH', restoration='FULL', bot_kind='random', **BASE_CELL),
    dict(name='bots_diss_HIGH_FULL', display_name='BOTS diss (HIGH/FULL)',
         p2_regime='HIGH', restoration='FULL', bot_kind='diss', **BASE_CELL),
    dict(name='bots_diss_LOW_FULL', display_name='BOTS diss (LOW/FULL)',
         p2_regime='LOW', restoration='FULL', bot_kind='diss', **BASE_CELL),
    dict(name='bots_diss_HIGH_MODERATE', display_name='BOTS diss (HIGH/MODERATE)',
         p2_regime='HIGH', restoration='MODERATE', bot_kind='diss', **BASE_CELL),
    dict(name='bots_diss_main', display_name='BOTS diss (main_confirmatory assignment)',
         assign_factors='participant', bot_kind='diss', **BASE_CELL),
    dict(name='bots_refresh', display_name='BOTS reload/duplicate robustness test',
         assign_factors='participant', bot_kind='diss', bot_refresh_test=True,
         **BASE_CELL),
]

# ---- diss_market: the yoked ten-repetition design as a basket economy with prediction
# markets (KGi-DISS-I042, I043). Every value marked DRAFT is an author decision. Slots of a
# schedule file are taken in order of arrival; give two sessions that share a file disjoint
# first_slot/last_slot. A seed wave needs a schedule drawn with --no-social.
MARKET_CELL = dict(
    app_sequence=['diss_market'],
    num_demo_participants=4,
    schedule_path=environ.get('MARKET_SCHEDULE', 'schedules/example_seed0_4pairs_v3.json'),
    board_source='schedule',       # 'schedule' (computer trader and forecaster; dev and bots only) | 'pool' | 'none'
    reveal_ms=9000,                # DRAFT: time over which a round's clearings appear
    probe_reveal_ms=6000,          # DRAFT: time over which ten trial closes appear
    source_reveal_ms=2500,         # DRAFT: time before a source's forecast can be answered
    recall_check=True,             # DRAFT: recall question after each market
    prize_points=20,               # DRAFT: forecast bonus
    points_to_currency=0.01,       # DRAFT: money per point
    completion_url='',             # e.g. the recruitment platform's completion link
    min_window_width=0,            # DRAFT: e.g. 900 keeps phones out; 0 lets every device in
    price_curves='both',           # 'both': the market screen draws both goods' clearing prices | 'own': only the ordered
                                   # good's (the display certified in I043). 'both' by the rule frozen in I047 and read on
                                   # records/live_cert_ad_I047.txt; a configuration without the key gets 'own'
)
SEED_SCHEDULE = environ.get('MARKET_SEED_SCHEDULE', 'schedules/example_seed0_4pairs_v3_nosocial.json')
SESSION_CONFIGS += [
    dict(name='market_dev', display_name='MARKET dev: computer-generated board (never shown to people in production)',
         **MARKET_CELL),
    dict(name='market_seed', display_name='MARKET seed wave: no board, record evidence only (feeds the pool)',
         **{**MARKET_CELL, 'board_source': 'none', 'schedule_path': SEED_SCHEDULE}),
    dict(name='market_pilot', display_name='MARKET pilot: board replays real earlier records (needs a pool file)',
         **{**MARKET_CELL, 'board_source': 'pool', 'pool_path': environ.get('MARKET_POOL', 'pools/pool.json')}),
    # pipeline-validation bot sessions (never human evidence)
    dict(name='market_bots_random', display_name='MARKET bots: random', bot_kind='random', **MARKET_CELL),
    dict(name='market_bots_model', display_name='MARKET bots: gate kernel', bot_kind='model', **MARKET_CELL),
    dict(name='market_bots_seed', display_name='MARKET bots: seed wave, no board', bot_kind='model',
         **{**MARKET_CELL, 'board_source': 'none', 'schedule_path': SEED_SCHEDULE}),
    dict(name='market_e2e', display_name='MARKET browser test: short reveals (never for people)', bot_kind='browser',
         **{**MARKET_CELL, 'reveal_ms': 1500, 'probe_reveal_ms': 1000, 'source_reveal_ms': 600,
            'num_demo_participants': 6}),
    dict(name='market_e2e_own', display_name="MARKET browser test: only the ordered good's prices drawn (never for people)",
         bot_kind='browser', **{**MARKET_CELL, 'reveal_ms': 1500, 'probe_reveal_ms': 1000, 'source_reveal_ms': 600,
                                'num_demo_participants': 6, 'price_curves': 'own'}),
    dict(name='market_e2e_both', display_name="MARKET browser test: both goods' prices drawn (never for people)",
         bot_kind='browser', **{**MARKET_CELL, 'reveal_ms': 1500, 'probe_reveal_ms': 1000, 'source_reveal_ms': 600,
                                'num_demo_participants': 6, 'price_curves': 'both'}),
    dict(name='market_e2e_seed', display_name='MARKET browser test: no board, short reveals (never for people)',
         bot_kind='browser', **{**MARKET_CELL, 'board_source': 'none', 'schedule_path': SEED_SCHEDULE, 'reveal_ms': 1500,
                                'probe_reveal_ms': 1000, 'source_reveal_ms': 600, 'num_demo_participants': 6}),
    # one round at the session's real speed, for the timing and frame measurements of tools/browser_run.py
    dict(name='market_real_own', display_name="MARKET timing test at real speed: only the ordered good's prices (never for people)",
         bot_kind='browser', **{**MARKET_CELL, 'price_curves': 'own'}),
    dict(name='market_real_both', display_name="MARKET timing test at real speed: both goods' prices (never for people)",
         bot_kind='browser', **{**MARKET_CELL, 'price_curves': 'both'}),
    dict(name='market_bots_pool', display_name='MARKET bots: board from a pool', bot_kind='model',
         **{**MARKET_CELL, 'board_source': 'pool', 'pool_path': environ.get('MARKET_POOL', 'pools/pool.json')}),
]

SESSION_CONFIG_DEFAULTS = dict(real_world_currency_per_point=1.00,
                               participation_fee=4.20, doc="")   # AUDIT: DESIGN §2

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'GBP'
USE_POINTS = False

ROOMS = []
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')
DEMO_PAGE_INTRO_HTML = """diss_market — yoked ten-repetition design as a basket economy with prediction markets (KGi-DISS-I042, I043); diss_bandit — task v3 (KGi-DISS-I032)"""
# AUDIT: secret from the environment; refuse the dev key in production mode.
SECRET_KEY = environ.get('OTREE_SECRET_KEY', 'dev-only-not-for-production')
if environ.get('OTREE_PRODUCTION') and SECRET_KEY == 'dev-only-not-for-production':
    raise RuntimeError('Set OTREE_SECRET_KEY in production.')
INSTALLED_APPS = ['otree']
