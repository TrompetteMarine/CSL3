# diss-otree settings — task v3 market skin (I032; supersedes the I006 cells,
# which remain below for the pilot framing comparison and bot smoke runs).
from os import environ

BASE_CELL = dict(
    num_demo_participants=4,
    app_sequence=['diss_bandit'],
    points_to_currency=0.02,       # GBP per point; see DESIGN.md for payment
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
]

SESSION_CONFIG_DEFAULTS = dict(real_world_currency_per_point=1.00,
                               participation_fee=2.00, doc="")

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'GBP'
USE_POINTS = False

ROOMS = []
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')
DEMO_PAGE_INTRO_HTML = """diss_bandit — task v3 market skin (KGi-DISS-I032)"""
SECRET_KEY = 'dev-only-not-for-production'
INSTALLED_APPS = ['otree']
