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
DEMO_PAGE_INTRO_HTML = """diss_bandit — task v3 market skin (KGi-DISS-I032)"""
# AUDIT: secret from the environment; refuse the dev key in production mode.
SECRET_KEY = environ.get('OTREE_SECRET_KEY', 'dev-only-not-for-production')
if environ.get('OTREE_PRODUCTION') and SECRET_KEY == 'dev-only-not-for-production':
    raise RuntimeError('Set OTREE_SECRET_KEY in production.')
INSTALLED_APPS = ['otree']
