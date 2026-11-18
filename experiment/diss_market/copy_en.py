"""Every sentence a participant reads (KGi-DISS-I042; the basket economy with prediction
markets, KGi-DISS-I043).

DRAFT. Nothing here is approved wording: consent, payment, the description of the trader
board and of the forecast sources, the three fairness items, the entitlement item and the
market questions are author decisions (freezes I042 and I043). Edit this file only;
templates and scripts take their text from it.
"""

STUDY = dict(
    brand='Basket market',
    consent_title='Before you start',
    consent_body=[
        '[DRAFT — replace with the approved study information and consent text.]',
        'In this study you take part in a simple market for ten rounds. It takes about ten '
        'minutes. You may stop at any time; payment requires completion.',
    ],
    consent_label='I have read the above and consent to take part.',
    consent_error='Consent is required to take part.',
    consent_next='Continue',
    narrow='This study needs a wider window. Please use a laptop or desktop computer, or widen this window.',
)

INSTRUCTIONS = dict(
    title='How the market works',
    market=[
        ('The economy',
         'This market trades two goods, <b>SQUARE</b> and <b>TRIANGLE</b>. You are a basket '
         'player: you buy goods to fill baskets. Every good you get is worth <b>1 point</b>; '
         '{basket} goods make a basket.'),
        ('Six procurement rounds',
         'In each of the first six rounds you order one good for the whole round. The goods '
         'market then clears <b>{k} times</b>. Each time, your order fills if the clearing price '
         'is at or below your cap of <b>{cap}</b>; otherwise it does not fill. You watch the '
         'prices come in; there is nothing to click. Orders are funded by the house: you never '
         'pay for a good and you cannot lose points.'),
        ('How prices are set',
         'Clearing prices follow a rule that was fixed before your session, using random draws '
         'made in advance. One good can be cheaper than the other, and prices <b>can change '
         'during the study without warning</b>.'),
    ],
    board=dict(
        pool=('The trader board',
              'Next to your own orders, a <b>trader board</b> shows the filled orders of a '
              '<b>previous participant</b> in this study, who traded under the same rule as you. '
              'Each round shows one previous participant; the record may come from a different '
              'point in their session than the round you are at. These are real records, not '
              'simulations.'),
        schedule=('The trader board (development build)',
                  'Next to your own orders, a <b>trader board</b> shows the filled orders of a '
                  '<b>computer-generated trader</b>. This build is for testing only and is never '
                  'shown to study participants.'),
        none=None,
    ),
    ratings=('Four quick questions',
             'After each procurement round we ask four quick questions about how you see the '
             'market. There are no right or wrong answers.'),
    probe=('Four prediction markets',
           'In the last four rounds you meet a market on an asset you have not seen: <i>will it '
           'close above a given price?</i> You give your forecast, then get some evidence, and '
           'forecast again. Then you can bet: buy a YES ticket, buy a NO ticket, or pass. A '
           'winning ticket pays <b>{pay} points</b>; the markets settle at the end. One of your '
           'eight forecasts is also picked at random and can win a bonus of <b>{prize} points</b>: '
           'the more accurate that forecast, the higher your chance of the bonus.'),
    payment='Your points are converted to money at the rate shown at the end.',
    legend_title='On the price chart',
    legend_cap='your cap',
    legend_paid='order filled',
    next='Continue',
)

QUIZ = dict(
    title='Quick check',
    intro='A few quick questions about how the task works. If an answer is not right you will see '
          'why and can try again. This check does not affect your payment.',
    items=dict(
        cq_cost=dict(
            label='Do you pay for the goods you order?',
            right='No — orders are funded by the house',
            wrong='Yes — each good costs a point',
            hint='Orders are funded by the house; you never pay for a good.'),
        cq_count=dict(
            label='In each of the first six rounds, how many times does the goods market clear?',
            right='{k} times',
            wrong='Once',
            hint='In each procurement round the market clears {k} times.'),
        cq_draws=dict(
            label='How are clearing prices set?',
            right='By a rule fixed before my session, using random draws made in advance',
            wrong='By other traders, live, as I play',
            hint='Prices follow a rule fixed in advance, with draws made in advance.'),
        cq_board=dict(
            label='Who is shown on the trader board?',
            right=dict(pool='A previous participant in this study, under the same rule as mine',
                       schedule='A computer-generated trader (development build)'),
            wrong=dict(pool='A computer simulation',
                       schedule='A previous participant in this study'),
            hint=dict(pool='The board shows real records of previous participants.',
                      schedule='In this development build the board trader is computer-generated.')),
    ),
    retry='Not quite — ',
    next='Open the market',
)

MARKET = dict(
    choose_title='Which good do you order this round?',
    choose_sub='Your order stays in for all {k} clearings. It fills whenever the price is at or below your cap of {cap}.',
    ticket_names=dict(SQUARE='Square', TRIANGLE='Triangle'),
    recap_you='Last round you ordered {ticket}: {wins} of {k} filled',
    recap_board='Trader board: {wins} of {k} filled',
    choose_next='Send the order',
    order_btn='Order',                        # DRAFT (I047): the word on a good's button of the market screen
    held='ordered',
    settle_title='The market is clearing',
    settle_done='Round cleared',
    clearing='Clearing',
    price_label='Clearing price',
    cap_label='your cap',
    zone_label='your order fills at or below your cap',
    fills_of='filled of',
    filled='filled',
    not_filled='not filled',
    you='You',
    trader='Trader',
    trader_kind=dict(pool='a previous participant', schedule='computer-generated', none=''),
    of='of',
    baskets='baskets',
    fills_caption='Filled orders',            # DRAFT (I047): the caption of the lower chart of the market screen
    points_gain='+{wins} points',
    settle_next='Continue',
    rate_title='How do you see the market right now?',
    rate_sub='Move every slider, then continue.',
    fair_items=[
        'This market clears fairly.',
        'The prices here can be trusted.',
        'I am treated fairly in this market.',
    ],
    fair_anchors=('completely disagree', 'completely agree'),
    entitle_item='The share of my orders that I deserve to have filled.',
    entitle_anchors=('none', 'all of them'),
    rate_untouched='Please move every slider before continuing.',
    rate_next='Continue',
)

PROBE = dict(
    eyebrow='New market',
    question='Will {asset} close above {thr}?',
    last='last price',
    now='now',
    close='close',
    chance='chance',
    above='above {thr}',
    below='below {thr}',
    question_pre='How likely is {asset} to close above {thr}?',
    question_post='Now, how likely is {asset} to close above {thr}?',
    anchors=('certainly not', 'certainly'),
    place_hint='Click or drag on the line to set your forecast.',
    record_title='Ten trial closes',
    record_text='Held with <b>your own</b> YES tickets. Each close above {thr} adds a point to your total.',
    sum_paid='of {m} closed above',
    source_title="Another trader's forecast",
    source_kind=dict(pool='{label} is a previous participant who saw ten trial closes of this market.',
                     schedule='{label} is a computer-generated forecaster (development build).'),
    source_says='chance of closing above {thr}',
    source_track='On the right side in {k} of {n} other markets.',
    names=dict(CIRCLE='Circle', DIAMOND='Diamond', HEXAGON='Hexagon', STAR='Star', CROSS='Cross',
               PENTAGON='Pentagon'),
    unset='Please set your forecast before continuing.',
    next='Lock in forecast',
    bet_title='Place your bet',
    bet_text='You have a <b>{allow}-point</b> allowance for this market. A ticket pays <b>{pay} points</b> '
             'if it wins. If you pass you keep the allowance. The market settles at the end.',
    bet_yes='Buy YES',
    bet_no='Buy NO',
    bet_pass='Pass',
    bet_pass_sub='keep {allow} points',
    bet_cost='costs {cost} points',
    bet_error='Please choose YES, NO or pass.',
    bet_next='Place bet',
    recall_title='One quick question',
    recall_record='Without looking back: how many of the ten trial closes were above {thr}?',
    recall_source='Without looking back: what chance did the other trader give?',
    recall_next='Continue',
)

CLOSING = dict(
    title='A few final questions',
    intro='A few questions about your experience. There are no right or wrong answers.',
    peer_success='The trader shown on the board was successful at the task.',
    peer_success_anchors=('not at all', 'extremely'),
    peer_real='The trader shown on the board was a real previous participant.',
    peer_real_anchors=('certainly not', 'certainly'),
    rig_suspicion='The prices in my session were manipulated against me specifically.',
    rig_anchors=('certainly not', 'certainly'),
    betting_familiarity='How familiar are you with betting or prediction markets?',
    betting_anchors=('not at all', 'very'),
    purpose_guess='In your own words, what do you think this study was about?',
    age='Your age (optional)',
    gender='Your gender (optional)',
    next='Settle the markets',
)

RESULTS = dict(
    title='The markets have settled',
    closed_above='closed at {close}, above {thr}',
    closed_below='closed at {close}, below {thr}',
    resolved=dict(yes='YES', no='NO'),
    your_bet=dict(YES='You bought YES', NO='You bought NO', PASS='You passed'),
    bet_points='{pts} points',
    points='You earned <b>{points} points</b> from goods and trial closes.',
    bets='Your bets returned <b>{pts} points</b>.',
    bonus_won='The forecast picked at random won the bonus of <b>{prize} points</b>.',
    bonus_lost='The forecast picked at random did not win the bonus this time.',
    money='In total this converts to <b>{money}</b>.',
    thanks='Thank you for taking part.',
    complete='Complete your submission',
)

NO_SLOT = dict(
    title='This session is full',
    body='All places in this session have been taken. You have not started the task. Please '
         'return the study; thank you for your time.',
)

PROGRESS = dict(round='Round', of='of', points='Points')
