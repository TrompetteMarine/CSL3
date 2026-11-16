"""Browser run of the diss_market app against a running oTree server (KGi-DISS-I042, I043).

Plays whole sessions in Chromium the way a participant would (clicks, drags, waits for the
reveals) and checks what a bot cannot:
  - no console error, no failed request, no request to another host;
  - no page carries a later round, the other good's prices, a market's evidence before its
    first forecast, a bet price before the second forecast, or how a market settles
    (gates G5 and H2);
  - the two members of a yoked pair who make the same choices get the same pages except
    for the board's numbers (gate G7);
  - a reload during a reveal, and the back button, change nothing that is stored;
  - on a phone, the price chart and the filled-orders chart are in view together.

    otree devserver 8000        # in another shell, from experiment/
    python tools/browser_run.py --base http://localhost:8000 --shots /path/for/screenshots
"""
import argparse
import csv
import io
import json
import os
import re
import sys
import time
import urllib.request
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

PHONE = dict(width=390, height=844)
SMALL_PHONE = dict(width=375, height=667)
BETS = ('YES', 'NO', 'PASS', 'YES')
DESKTOP = dict(width=1280, height=860)


class Run:
    def __init__(self, page, base, shots=None, tag='', scale_shots=False):
        self.page, self.base, self.shots, self.tag = page, base, shots, tag
        self.errors, self.foreign, self.failed, self.sources = [], [], [], []
        host = urlparse(base).netloc
        page.on('console', lambda m: self.errors.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: self.errors.append(str(e)))
        page.on('requestfailed', lambda r: self.failed.append(r.url))
        page.on('request', lambda r: self.foreign.append(r.url)
                if urlparse(r.url).netloc not in (host, '') and not r.url.startswith('data:') else None)
        page.on('response', lambda r: self.failed.append(f'{r.status} {r.url}') if r.status >= 400 else None)
        self.n = 0
        self.points = 0                                     # the participant's total as it should stand on screen
        self.html = ''                                      # the server's HTML of the current page, as sent
        self.notes = []                                     # what a check found wrong

    def name(self):
        return self.page.evaluate('window.js_vars && window.js_vars.page')

    def shot(self, label):
        self.n += 1
        if self.shots:
            self.page.wait_for_timeout(450)                 # let the page transition finish
            self.page.add_style_tag(content='.debug-info, #debug-info, .otree-debug-info { display: none !important; }')
            self.page.screenshot(path=os.path.join(self.shots, f'{self.tag}{self.n:02d}_{label}.png'), full_page=True)

    def keep_source(self, label):
        self.sources.append((label, self.html))

    def next(self):
        with self.page.expect_navigation() as nav:
            self.page.click('#dm-next')
        self.html = nav.value.text()
        self.page.wait_for_timeout(300)                     # the page transition swallows clicks while it runs

    def slide(self, index, value):
        """drag the handle of the index-th slider to a value"""
        track = self.page.locator('.dm-sl-track').nth(index)
        track.scroll_into_view_if_needed()
        box = track.bounding_box()
        y = box['y'] + box['height'] / 2
        self.page.mouse.move(box['x'] + box['width'] * 0.5, y)
        self.page.mouse.down()
        self.page.mouse.move(box['x'] + box['width'] * value / 100, y, steps=6)
        self.page.mouse.up()

    # ---- pages
    def preamble(self):
        assert self.name() == 'consent', self.name()
        self.shot('consent')
        assert self.page.is_disabled('#dm-next')
        self.page.check('input[name=consent]')
        self.next()
        assert self.name() == 'instructions'
        self.shot('instructions')
        self.next()
        assert self.name() == 'quiz'
        opts = self.page.locator('fieldset.dm-q')
        for i in range(opts.count()):                      # first a wrong answer on the first item
            labels = opts.nth(i).locator('label.dm-opt')
            texts = [labels.nth(j).inner_text() for j in range(labels.count())]
            right = [j for j, t in enumerate(texts) if RIGHT.search(t)]
            assert len(right) == 1, texts
            labels.nth(right[0] if i else 1 - right[0]).click()
        self.next()
        assert self.name() == 'quiz' and self.page.locator('.dm-error').count() == 1, self.name()
        self.shot('quiz_retry')
        for i in range(opts.count()):
            labels = opts.nth(i).locator('label.dm-opt')
            texts = [labels.nth(j).inner_text() for j in range(labels.count())]
            labels.nth([j for j, t in enumerate(texts) if RIGHT.search(t)][0]).click()
        self.next()

    def top_points(self):
        return int(self.page.locator('#dm-points').inner_text())

    def market_round(self, pick, ratings, reload_mid=False, back=False, repost=False, hover=False):
        """a procurement round: order, clearing, four ratings"""
        assert self.name() == 'order', self.name()
        self.keep_source('order')
        assert self.page.is_disabled('#dm-next')
        self.page.locator('label.dm-good').nth(pick).click()
        self.shot('order')
        order_url = self.page.url
        other = self.page.locator('input[name=ticket]').nth(1 - pick).get_attribute('value')
        self.next()
        assert self.name() == 'clearing'
        if repost:                                          # a second, different submission of the order already sent
            self.page.request.post(order_url, form={'ticket': other, 'rt_choose_ms': '1'})
        self.keep_source('clearing')
        shown = re.search(r'id="dm-points">(\d+)<', self.html)
        assert shown and int(shown.group(1)) == self.points, 'the points total must not show the round before its reveal'
        view = self.page.viewport_size
        for sel in ('[data-chart=price]', '[data-chart=fills]'):
            box = self.page.locator(sel).bounding_box()
            if box['y'] < 0 or box['y'] + box['height'] > view['height'] or box['width'] < 200:
                self.notes.append(f'{sel} is not fully in view on the clearing page ({view})')
        if reload_mid:
            self.page.wait_for_timeout(400)
            self.shot('clearing_mid')
            self.page.reload()
            assert self.name() == 'clearing'
        elif self.shots:
            self.page.wait_for_timeout(500)
            self.shot('clearing_mid')
        self.page.wait_for_selector('.dm-clearing.is-cleared', timeout=60000)
        self.page.wait_for_timeout(800)
        own = int(self.page.locator('[data-count=own]').inner_text())
        self.points += own
        assert self.top_points() == self.points
        k = self.page.evaluate('window.js_vars.own.length')
        if int(self.page.locator('[data-seen]').first.inner_text()) != k:
            self.notes.append('the clearing counter did not reach the end of the round')
        if own != self.page.evaluate("window.js_vars.own.split('1').length - 1"):
            self.notes.append('the own count on screen is not the count of the record')
        dots = self.page.locator('[data-chart=price] circle.dm-dot').count()
        if dots != own:
            self.notes.append(f'{dots} fill marks on the price chart for {own} filled orders')
        board = self.page.locator('[data-count=board]')
        board = int(board.inner_text()) if board.count() else None
        if hover:                                           # the readout names the clearing under the pointer
            box = self.page.locator('[data-chart=price]').bounding_box()
            self.page.mouse.move(box['x'] + box['width'] * 0.5, box['y'] + box['height'] * 0.5)
            self.page.wait_for_timeout(120)
            text = self.page.locator('#dm-readout').inner_text()
            m = re.search(r'Clearing (\d+)\s+(\d+\.\d\d), (filled|not filled)', text)
            if not m:
                self.notes.append(f'no readout under the pointer: {text!r}')
            else:
                i = int(m.group(1)) - 1
                price, bit = self.page.evaluate(f'[window.js_vars.prices[{i}], window.js_vars.own[{i}]]')
                if f'{price:.2f}' != m.group(2) or (bit == '1') != (m.group(3) == 'filled'):
                    self.notes.append(f'the readout does not match clearing {i + 1}: {text!r}')
            self.shot('clearing_hover')
            self.page.mouse.move(2, 2)
        self.shot('clearing_done')
        if back:
            self.page.go_back()
            self.page.wait_for_load_state()
            assert self.name() == 'clearing', 'the back button must not return to the order'
            self.page.wait_for_selector('.dm-clearing.is-cleared', timeout=60000)
        self.next()
        assert self.name() == 'rate'
        assert self.page.is_disabled('#dm-next')
        for i, v in enumerate(ratings[:-1]):
            self.slide(i, v)
        assert self.page.is_disabled('#dm-next'), 'every slider must be touched'
        self.slide(len(ratings) - 1, ratings[-1])
        self.shot('rate')
        self.next()
        return own, board

    def market(self, pre, post, bet):
        """a prediction market: forecast, evidence, forecast again, bet, recall"""
        assert self.name() == 'market', self.name()
        self.keep_source('market')
        assert self.page.is_disabled('#dm-next')
        self.shot('market_unset')
        self.slide(0, pre)
        if self.page.locator('[data-forecast]').inner_text() != f'{pre}%':
            self.notes.append('the forecast figure does not show the slider value')
        self.shot('market')
        self.next()
        assert self.name() == 'evidence'
        self.keep_source('evidence')
        kind = self.page.evaluate('window.js_vars.evidence')
        if self.page.locator('#dm-ask').is_visible():
            self.notes.append('the second forecast could be given before the evidence was shown')
        self.page.wait_for_selector('#dm-ask:not([hidden])', timeout=60000)
        if kind == 'record':
            seen = int(self.page.locator('.dm-evi [data-count]').inner_text())
            marks = self.page.locator('[data-chart=strip] circle.is-above').count()
            if marks != seen or self.page.locator('[data-chart=strip] circle.dm-trial').count() != 10:
                self.notes.append('the record strip does not show the ten trial closes')
            self.points += seen
        else:
            seen = int(self.page.evaluate('window.js_vars.cue'))
            if self.page.locator('.dm-source-figure b').inner_text() != f'{seen}%':
                self.notes.append("the source card does not show the source's forecast")
        self.slide(0, post)
        self.page.wait_for_timeout(700)
        if self.top_points() != self.points:
            self.notes.append('the points total after the evidence is not the total so far')
        self.shot(f'evidence_{kind}')
        self.next()
        assert self.name() == 'bet', self.name()
        self.keep_source('bet')
        assert self.page.is_disabled('#dm-next')
        self.page.locator(f'label.dm-bet.is-{bet.lower()}').click()
        self.shot('bet')
        self.next()
        if self.top_points() != self.points:
            self.notes.append('a bet moved the points total before the markets settled')
        if self.name() == 'recall':
            self.page.locator(f'input[name=recall][value="{seen}"]').evaluate('e => e.parentElement.click()')
            self.shot('recall')
            self.next()
        return kind, seen

    def closing(self):
        assert self.name() == 'closing', self.name()
        for n in ('rig_suspicion', 'betting_familiarity'):
            self.page.locator(f'input[name={n}]').nth(2).evaluate('e => e.parentElement.click()')
        self.page.fill('textarea[name=purpose_guess]', 'browser run')
        self.shot('closing')
        self.next()
        assert self.name() == 'results'
        self.keep_source('results')
        self.final_points = self.top_points()
        self.shot('results')


RIGHT = re.compile(r'^(No — orders are funded|\d+ times|By a rule fixed|A computer-generated trader|A previous participant in this study, under)')


def start_links(pw_page, base, config):
    pw_page.goto(f'{base}/demo/{config}')
    pw_page.wait_for_url(re.compile(r'.*/SessionStartLinks/.*'), timeout=60000)   # the demo page creates the session, then redirects
    pw_page.wait_for_load_state()
    html = pw_page.content()
    links = re.findall(r'href="([^"]*InitializeParticipant/[^"]*)"', html)
    assert links, 'no participant links on the demo page'
    return [l if l.startswith('http') else base + l for l in dict.fromkeys(links)]


def play(browser, link, base, shots, tag, viewport, picks, **kw):
    ctx = browser.new_context(viewport=viewport, device_scale_factor=kw.pop('dpr', 1),
                              reduced_motion=kw.pop('reduced', 'no-preference'))
    page = ctx.new_page()
    run = Run(page, base, shots, tag)
    run.html = page.goto(link).text()
    run.preamble()
    counts = []
    for r, pick in enumerate(picks):
        counts.append(run.market_round(pick, [20 + 10 * r, 55, 70 - 5 * r, 40],
                                       reload_mid=kw.get('reload') and r == 1, back=kw.get('back') and r == 2,
                                       repost=kw.get('repost') and r == 3, hover=kw.get('hover') and r == 4))
    paid = [run.market(40 + 5 * i, 60 - 5 * i, bet) for i, bet in enumerate(kw.get('bets', BETS))]
    run.closing()
    ctx.close()
    return run, counts, paid


def export_rows(base, rest_key=''):
    """the app's custom export, read from the server (open in dev mode, REST key in production)"""
    req = urllib.request.Request(f'{base}/api/export_app_custom?app=diss_market',
                                 headers={'otree-rest-key': rest_key} if rest_key else {})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return list(csv.DictReader(io.StringIO(opener.open(req).read().decode('utf-8-sig'))))


def stored(rows, session):
    """per slot: what the server holds after the run"""
    out = {}
    for r in rows:
        if r['session'] != session or r['row_type'] != 'repetition':
            continue
        d = out.setdefault(int(r['slot']), dict(market=0, probe=0, ratings=0, forecasts=0, bets=[], wins=[], views=[],
                                                meta=[], prices=[], bits=[]))
        if r['kind'] == 'market':
            d['market'] += 1
            d['ratings'] += all(r[k] != '' for k in ('fair1', 'fair2', 'fair3', 'entitle'))
            d['wins'].append(int(r['wins']))
            d['views'].append(int(r['settle_views']))
            d['meta'].append(json.loads(r['settle_meta'] or '{}'))
            d['prices'].append(r['prices'])
            d['bits'].append(r['own_bits'])
        else:
            d['probe'] += 1
            d['forecasts'] += (r['forecast_pre'] != '') + (r['forecast_post'] != '')
            d['bets'].append(r['bet'])
    return out


def totals(rows, session):
    return {int(r['slot']): int(r['points_total']) for r in rows
            if r['session'] == session and r['row_type'] == 'participant' and r['points_total'] != ''}


def time_one_round(browser, link, base):
    """one procurement round at the session's real reveal speed: seconds from the page to 'cleared'"""
    ctx = browser.new_context(viewport=DESKTOP)
    page = ctx.new_page()
    run = Run(page, base)
    run.html = page.goto(link).text()
    run.preamble()
    page.locator('label.dm-good').nth(0).click()
    run.next()
    t0 = time.time()
    # the tab is hidden for three seconds in the middle: the reveal must stand still meanwhile
    hide = "v => { Object.defineProperty(document, 'hidden', {configurable: true, get: () => v}); document.dispatchEvent(new Event('visibilitychange')); }"
    page.wait_for_timeout(1500)
    seen_before = int(page.locator('[data-seen]').first.inner_text())
    page.evaluate(hide, True)
    page.wait_for_timeout(3000)
    seen_hidden = int(page.locator('[data-seen]').first.inner_text())
    page.evaluate(hide, False)
    page.wait_for_selector('.dm-clearing.is-cleared', timeout=120000)
    dt = time.time() - t0 + 0.3                              # next() already waited 0.3 s on the page
    planned = page.evaluate('window.js_vars.reveal_ms')
    meta = json.loads(page.input_value('input[name=settle_meta]'))
    ctx.close()
    return dict(planned_reveal_ms=planned, measured_reveal_ms=meta['reveal_ms'], total_ms=meta['total_ms'], hidden_ms=meta['hidden_ms'],
                page_to_settled_s=round(dt, 2), settlements_shown_while_hidden=seen_hidden - seen_before)


def strip_board(html):
    """what may differ between the two members of a pair: the board's record and counts, the
    participant's own code in URLs, and the arm-independent debug table of the dev server"""
    html = re.sub(r'"board":\s*"[01]*"', '"board":"#"', html)
    html = re.sub(r'/p/[a-z0-9]+/', '/p/#/', html)
    html = re.sub(r'Trader board: \d+ of', 'Trader board: # of', html)
    html = re.sub(r'<div[^>]*class="[^"]*debug-info.*', '', html, flags=re.S)
    html = re.sub(r'data-socket-url="[^"]*"', '', html)
    html = re.sub(r'<title>.*?</title>', '', html, flags=re.S)
    html = re.sub(r'<meta name="tab-title-debug-info"[^>]*>', '', html)
    return html


SECRET = re.compile(r'score_u|prize_u|"chance"|"close"\s*:|"favourable"|closed at')


def leaks_of(run):
    """what a page's source must not carry (gates G5 and H2)"""
    out = []
    for label, html in run.sources:
        body = strip_board(html)
        if label != 'results' and SECRET.search(body):
            out.append(f'{label}: how a market settles')
        if label in ('order', 'market') and re.search(r'[01]{10,}', body):
            out.append(f'{label}: a record')
        if label == 'order' and re.search(r'"prices"', body):
            out.append('order: clearing prices before the order')
        if label == 'clearing':
            if len(re.findall(r'"own":\s*"[01]+"', html)) != 1:
                out.append('clearing carries more than this round')
            series = re.findall(r'"prices":\s*\[([^\]]*)\]', html)
            k = len(re.search(r'"own":\s*"([01]+)"', html).group(1))
            if len(series) != 1 or len(series[0].split(',')) != k or len(re.findall(r'\d\.\d+(?:,\s*\d\.\d+){20,}', body)) != 1:
                out.append("clearing carries prices beyond the ordered good's own path")
        if label == 'market' and re.search(r'"shown"|"cue"|"evidence"|dm-evi|dm-source|dm-bet|¢', body):
            out.append('market: evidence or a bet price before the first forecast')
        if label == 'evidence' and re.search(r'dm-bet|¢|price_yes', body):
            out.append('evidence: a bet price before the second forecast')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://localhost:8000')
    ap.add_argument('--config', default='market_e2e')
    ap.add_argument('--shots', default='')
    ap.add_argument('--timing-config', default='', help='also time one round of this session config at its real speed')
    ap.add_argument('--rest-key', default=os.environ.get('OTREE_REST_KEY', ''))
    a = ap.parse_args()
    if a.shots:
        os.makedirs(a.shots, exist_ok=True)
    report = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        admin = browser.new_page()
        links = start_links(admin, a.base, a.config)
        picks = [0, 1, 0, 0, 1, 0]
        # slots 0 and 1 are the two members of one pair: same choices, desktop
        a_run, a_counts, a_paid = play(browser, links[0], a.base, a.shots, 'A_', DESKTOP, picks, reload=True, back=True,
                                       repost=True, hover=True)
        b_run, b_counts, b_paid = play(browser, links[1], a.base, a.shots, 'B_', DESKTOP, picks)
        # third participant on a phone, fourth with reduced motion, fifth on a small phone
        c_run, _, _ = play(browser, links[2], a.base, a.shots, 'C_', PHONE, picks, dpr=2)
        d_run, _, _ = play(browser, links[3], a.base, a.shots, 'D_', DESKTOP, picks, reduced='reduce')
        e_run, _, _ = play(browser, links[4], a.base, a.shots, 'E_', SMALL_PHONE, picks, dpr=2)
        session = re.search(r'/SessionStartLinks/(\w+)', admin.url).group(1)
        if a.timing_config:
            report['timing'] = time_one_round(browser, start_links(admin, a.base, a.timing_config)[0], a.base)
        browser.close()
    # what the server stored: one row per repetition, nothing doubled by the reload or the back button
    rows = export_rows(a.base, a.rest_key)
    st = stored(rows, session)
    report['stored'] = {k: {x: v[x] for x in ('market', 'probe', 'ratings', 'forecasts', 'bets')} for k, v in st.items()}
    complete = all(v['market'] == 6 and v['probe'] == 4 and v['ratings'] == 6 and v['forecasts'] == 8
                   and v['bets'] == list(BETS) for v in st.values()) and len(st) == 5
    # every stored price is at or below the cap exactly when the order filled
    cap = 4.0
    report['stored_prices_match_fills'] = all(
        [float(x) <= cap for x in p.split(',')] == [c == '1' for c in b]
        for v in st.values() for p, b in zip(v['prices'], v['bits']))
    tot = totals(rows, session)
    runs_by_slot = dict(enumerate((a_run, b_run, c_run, d_run, e_run)))
    report['final_points_on_screen_match_stored'] = all(tot.get(i) == r.final_points for i, r in runs_by_slot.items())
    report['stored_complete'] = complete
    report['stored_own_counts_match_screen'] = st[0]['wins'] == [x[0] for x in a_counts] and st[1]['wins'] == [x[0] for x in b_counts]
    report['settle_views_A'] = st[0]['views']
    report['reduced_motion_recorded'] = [m.get('reduced_motion') for m in st[3]['meta']]
    runs = dict(A=a_run, B=b_run, C=c_run, D=d_run, E=e_run)
    report['notes'] = {k: r.notes for k, r in runs.items() if r.notes}
    report['console_errors'] = {k: r.errors for k, r in runs.items() if r.errors}
    report['failed_requests'] = {k: r.failed for k, r in runs.items() if r.failed}
    report['foreign_requests'] = {k: r.foreign for k, r in runs.items() if r.foreign}
    # G7: the two members of the pair, same choices
    diffs = []
    for (la, ha), (lb, hb) in zip(a_run.sources, b_run.sources):
        assert la == lb
        if strip_board(ha) != strip_board(hb):
            diffs.append(la)
    report['pair_same_own_counts'] = [x[0] for x in a_counts] == [x[0] for x in b_counts]
    report['pair_board_counts'] = dict(A=[x[1] for x in a_counts], B=[x[1] for x in b_counts])
    report['pair_page_differences_beyond_the_board'] = diffs
    # G5, H2: what a page's source must not carry
    leaks = [x for run in runs.values() for x in leaks_of(run)]
    report['leaks'] = leaks
    report['pages_checked_for_leaks'] = sum(len(r.sources) for r in runs.values())
    report['evidence_seen'] = dict(A=a_paid, B=b_paid)
    print(json.dumps(report, indent=1))
    ok = not (report['console_errors'] or report['failed_requests'] or report['foreign_requests'] or diffs or leaks
              or report['notes']) \
        and report['pair_same_own_counts'] and complete and report['stored_own_counts_match_screen'] \
        and all(report['reduced_motion_recorded']) and report['stored_prices_match_fills'] \
        and report['final_points_on_screen_match_stored'] and a_paid == b_paid
    if 'timing' in report:
        t = report['timing']
        ok = ok and abs(t['measured_reveal_ms'] - t['planned_reveal_ms']) <= 150 and abs(t['hidden_ms'] - 3000) <= 250 \
            and t['settlements_shown_while_hidden'] <= 1
    print('BROWSER RUN', 'PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
