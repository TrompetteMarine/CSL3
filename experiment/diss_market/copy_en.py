"""Every sentence a participant reads (KGi-DISS-I042).

DRAFT. Nothing here is approved wording: consent, payment, the description of the trader
board, the three fairness items, the entitlement item and the probe questions are author
decisions (freeze I042, draft_and_author_gated). Edit this file only; templates and scripts
take their text from it.
"""

STUDY = dict(
    brand='Ticket market',
    consent_title='Before you start',
    consent_body=[
        '[DRAFT — replace with the approved study information and consent text.]',
        'In this study you take part in a simple ticket market for ten rounds. It takes about '
        'ten minutes. You may stop at any time; payment requires completion.',
    ],
    consent_label='I have read the above and consent to take part.',
    consent_error='Consent is required to take part.',
    narrow='This study needs a wider window. Please use a laptop or desktop computer, or widen this window.',
)

INSTRUCTIONS = dict(
    title='How the market works',
    market=[
        ('Six market rounds',
         'In each of the first six rounds you pick one of two tickets, <b>SQUARE</b> or '
         '<b>TRIANGLE</b>, and hold it for the round. The market then settles your ticket '
         '<b>{k} times</b>. Each settlement either pays <b>1 point</b> or pays nothing. You watch '
         'the settlements come in; there is nothing to click.'),
        ('How settlements are decided',
         'Settlements follow a payout rule that was fixed before your session, using random '
         'draws made in advance. One ticket can pay more often than the other, and how often a '
         'ticket pays <b>can change during the study without warning</b>. Tickets are free: you '
         'never pay for one and you cannot lose points.'),
    ],
    board=dict(
        pool=('The trader board',
              'Next to your own settlements, a <b>trader board</b> shows the settlements of a '
              '<b>previous participant</b> in this study, who played under the same payout rule '
              'as you. Each round shows one previous participant; the record may come from a '
              'different point in their session than the round you are at. These are real '
              'records, not simulations.'),
        schedule=('The trader board (development build)',
                  'Next to your own settlements, a <b>trader board</b> shows the settlements of '
                  'a <b>computer-generated trader</b>. This build is for testing only and is '
                  'never shown to study participants.'),
        none=None,
    ),
    ratings=('Four quick questions',
             'After each market round we ask four quick questions about how you see the market. '
             'There are no right or wrong answers.'),
    probe=('Four new tickets',
           'In the last four rounds you meet a ticket you have not seen before. You say how '
           'likely it is to pay, then see ten of its settlements, then say again how likely it '
           'is to pay. One of your eight forecasts is picked at random and can win a bonus of '
           '<b>{prize} points</b>: the more accurate that forecast, the higher your chance of the '
           'bonus.'),
    payment='Your points are converted to money at the rate shown at the end.',
    legend_paid='paid',
    legend_unpaid='did not pay',
    next='Continue',
)

QUIZ = dict(
    title='Quick check',
    intro='Four quick questions about how the task works. If an answer is not right you will see '
          'why and can try again. This check does not affect your payment.',
    items=dict(
        cq_cost=dict(
            label='Do you pay for the tickets you choose?',
            right='No — tickets are free',
            wrong='Yes — each ticket costs a point',
            hint='Tickets are free; you never pay for one.'),
        cq_count=dict(
            label='In each of the first six rounds, how many times is your ticket settled?',
            right='{k} times',
            wrong='Once',
            hint='Each market round settles your ticket {k} times.'),
        cq_draws=dict(
            label='How is each settlement decided?',
            right='By a rule fixed before my session, using random draws made in advance',
            wrong='By the experimenter, live, as I play',
            hint='Settlements follow a rule fixed in advance, with draws made in advance.'),
        cq_board=dict(
            label='Who is shown on the trader board?',
            right=dict(pool='A previous participant in this study, under the same payout rule as mine',
                       schedule='A computer-generated trader (development build)'),
            wrong=dict(pool='A computer simulation',
                       schedule='A previous participant in this study'),
            hint=dict(pool='The board shows real records of previous participants.',
                      schedule='In this development build the board trader is computer-generated.')),
    ),
    retry='Not quite — ',
    next='Start the market',
)

MARKET = dict(
    choose_title='Choose your ticket for this round',
    choose_sub='You hold it for all {k} settlements of the round.',
    ticket_names=dict(SQUARE='Square', TRIANGLE='Triangle'),
    recap_you='Last round you held {ticket}: paid {wins} of {k}',
    recap_board='Trader board: paid {wins} of {k}',
    choose_next='Hold this ticket',
    settle_title='The market is settling',
    settle_done='Round settled',
    own_label='Your ticket',
    board_kicker='Trader board',
    board_label=dict(pool='a previous participant',
                     schedule='computer-generated trader',
                     none=''),
    paid_of='paid',
    of='of',
    points_gain='+{wins} points',
    settle_next='Continue',
    rate_title='How do you see the market right now?',
    rate_sub='Move every slider, then continue.',
    fair_items=[
        'The market settles fairly.',
        'The payout rule can be trusted.',
        'I am treated fairly in this market.',
    ],
    fair_anchors=('completely disagree', 'completely agree'),
    entitle_item='What I deserve to win in a round.',
    entitle_anchors=('nothing', 'every settlement'),
    rate_untouched='Please move every slider before continuing.',
    rate_next='Continue',
)

PROBE = dict(
    pre_title='A new ticket',
    pre_body='You have not seen this ticket before.',
    question_pre='How likely is this ticket to pay at a settlement?',
    question_post='Now, how likely is this ticket to pay at its next settlement?',
    anchors=('never pays', 'always pays'),
    place_hint='Click or drag on the line to set your forecast.',
    record_own='The market now settles this ticket ten times <b>for you</b>. Each settlement that '
               'pays adds a point to your total.',
    record_other='Here are ten settlements of this ticket. They are <b>not yours</b> and pay '
                 'nothing to you.',
    names=dict(CIRCLE='Circle', DIAMOND='Diamond', HEXAGON='Hexagon', STAR='Star', CROSS='Cross',
               PENTAGON='Pentagon'),
    unset='Please set your forecast before continuing.',
    sum_paid='paid of',
    next='Lock in forecast',
    recall_title='One quick question',
    recall_q='Without looking back: how many of the ten settlements you just saw paid?',
    recall_next='Continue',
)

CLOSING = dict(
    title='A few final questions',
    intro='A few questions about your experience. There are no right or wrong answers.',
    peer_success='The trader shown on the board was successful at the task.',
    peer_success_anchors=('not at all', 'extremely'),
    peer_real='The trader shown on the board was a real previous participant.',
    peer_real_anchors=('certainly not', 'certainly'),
    rig_suspicion='The settlements in my session were manipulated against me specifically.',
    rig_anchors=('certainly not', 'certainly'),
    betting_familiarity='How familiar are you with betting or prediction markets?',
    betting_anchors=('not at all', 'very'),
    purpose_guess='In your own words, what do you think this study was about?',
    age='Your age (optional)',
    gender='Your gender (optional)',
    next='See my results',
)

RESULTS = dict(
    title='Finished',
    points='You earned <b>{points} points</b> in the market.',
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
