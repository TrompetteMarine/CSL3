# diss-otree settings — task v3 (I006). Cells = p2_regime (Factor A) x restoration (B).
from os import environ

BASE_CELL = dict(
    num_demo_participants=4,
    app_sequence=['diss_bandit'],
    points_to_currency=0.02,       # GBP per point; see design doc for payment rationale
    session_seed=20261104,
    peer_pool_path='',             # production: path to real yoked-stream pool (no deception)
)

SESSION_CONFIGS = [
    dict(name='cell_HIGH_FULL', display_name='Cell A=HIGH B=FULL',
         p2_regime='HIGH', restoration='FULL', **BASE_CELL),
    dict(name='cell_HIGH_MODERATE', display_name='Cell A=HIGH B=MODERATE',
         p2_regime='HIGH', restoration='MODERATE', **BASE_CELL),
    dict(name='cell_LOW_FULL', display_name='Cell A=LOW B=FULL',
         p2_regime='LOW', restoration='FULL', **BASE_CELL),
    dict(name='cell_LOW_MODERATE', display_name='Cell A=LOW B=MODERATE',
         p2_regime='LOW', restoration='MODERATE', **BASE_CELL),
    # pipeline-validation bot sessions (data labeled by bot_kind; never human evidence)
    dict(name='bots_random_HIGH_FULL', display_name='BOTS random (HIGH/FULL)',
         p2_regime='HIGH', restoration='FULL', bot_kind='random', **BASE_CELL),
    dict(name='bots_diss_HIGH_FULL', display_name='BOTS diss (HIGH/FULL)',
         p2_regime='HIGH', restoration='FULL', bot_kind='diss', **BASE_CELL),
    dict(name='bots_diss_LOW_FULL', display_name='BOTS diss (LOW/FULL)',
         p2_regime='LOW', restoration='FULL', bot_kind='diss', **BASE_CELL),
    dict(name='bots_diss_HIGH_MODERATE', display_name='BOTS diss (HIGH/MODERATE)',
         p2_regime='HIGH', restoration='MODERATE', bot_kind='diss', **BASE_CELL),
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
DEMO_PAGE_INTRO_HTML = """diss_bandit — task v3 (KGi-DISS-I006)"""
SECRET_KEY = 'dev-only-not-for-production'
INSTALLED_APPS = ['otree']
