"""Browser run of the diss_market app against a running oTree server (KGi-DISS-I042).

Plays whole sessions in Chromium the way a participant would (clicks, drags, waits for the
reveals) and checks what a bot cannot:
  - no console error, no failed request, no request to another host;
  - no page carries a later outcome or a probe record before its first forecast (gate G5);
  - the two members of a yoked pair who make the same choices get the same pages except
    for the board's numbers (gate G7);
  - a reload during a reveal, and the back button, change nothing that is stored.

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
        self.html = ''                                      # the server's HTML of the current page, as sent

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

    def market_round(self, pick, ratings, reload_mid=False, back=False):
        assert self.name() == 'choose', self.name()
        self.keep_source('choose')
        assert self.page.is_disabled('#dm-next')
        self.page.locator('label.dm-ticket').nth(pick).click()
        self.shot('choose')
        self.next()
        assert self.name() == 'settle'
        self.keep_source('settle')
        if reload_mid:
            self.page.wait_for_timeout(400)
            self.shot('settle_mid')
            self.page.reload()
            assert self.name() == 'settle'
        self.page.wait_for_selector('.dm-settle.is-settled', timeout=60000)
        self.page.wait_for_timeout(800)
        own = int(self.page.locator('[data-tape=own] [data-count]').inner_text())
        board = self.page.locator('[data-tape=board] [data-count]')
        board = int(board.inner_text()) if board.count() else None
        self.shot('settle_done')
        if back:
            self.page.go_back()
            self.page.wait_for_load_state()
            assert self.name() == 'settle', 'the back button must not return to the choice'
            self.page.wait_for_selector('.dm-settle.is-settled', timeout=60000)
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

    def probe(self, pre, post):
        assert self.name() == 'probe_pre', self.name()
        self.keep_source('probe_pre')
        assert self.page.is_disabled('#dm-next')
        self.shot('probe_pre_unset')
        self.slide(0, pre)
        self.shot('probe_pre')
        self.next()
        assert self.name() == 'probe_post'
        self.page.wait_for_selector('#dm-ask:not([hidden])', timeout=60000)
        paid = int(self.page.locator('[data-tape=record] [data-count]').inner_text())
        self.slide(0, post)
        self.page.wait_for_timeout(300)
        self.shot('probe_post')
        self.next()
        if self.name() == 'probe_recall':
            self.page.locator('label.dm-chip').nth(paid).click()
            self.shot('probe_recall')
            self.next()
        return paid

    def closing(self):
        assert self.name() == 'closing', self.name()
        for n in ('rig_suspicion', 'betting_familiarity'):
            self.page.locator(f'input[name={n}]').nth(2).evaluate('e => e.parentElement.click()')
        self.page.fill('textarea[name=purpose_guess]', 'browser run')
        self.shot('closing')
        self.next()
        assert self.name() == 'results'
        self.shot('results')


RIGHT = re.compile(r'^(No — tickets are free|\d+ times|By a rule fixed|A computer-generated trader|A previous participant in this study, under)')


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
                                       reload_mid=kw.get('reload') and r == 1, back=kw.get('back') and r == 2))
    paid = [run.probe(40 + 5 * i, 60 - 5 * i) for i in range(4)]
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
        d = out.setdefault(int(r['slot']), dict(market=0, probe=0, ratings=0, forecasts=0, wins=[], views=[], meta=[]))
        if r['kind'] == 'market':
            d['market'] += 1
            d['ratings'] += all(r[k] != '' for k in ('fair1', 'fair2', 'fair3', 'entitle'))
            d['wins'].append(int(r['wins']))
            d['views'].append(int(r['settle_views']))
            d['meta'].append(json.loads(r['settle_meta'] or '{}'))
        else:
            d['probe'] += 1
            d['forecasts'] += (r['forecast_pre'] != '') + (r['forecast_post'] != '')
    return out


def time_one_round(browser, link, base):
    """one market round at the session's real reveal speed: seconds from the page to 'settled'"""
    ctx = browser.new_context(viewport=DESKTOP)
    page = ctx.new_page()
    run = Run(page, base)
    run.html = page.goto(link).text()
    run.preamble()
    page.locator('label.dm-ticket').nth(0).click()
    run.next()
    t0 = time.time()
    page.wait_for_selector('.dm-settle.is-settled', timeout=120000)
    dt = time.time() - t0 + 0.3                              # next() already waited 0.3 s on the page
    planned = page.evaluate('window.js_vars.reveal_ms')
    meta = json.loads(page.input_value('input[name=settle_meta]'))
    ctx.close()
    return dict(planned_reveal_ms=planned, measured_reveal_ms=meta['reveal_ms'], total_ms=meta['total_ms'], hidden_ms=meta['hidden_ms'],
                page_to_settled_s=round(dt, 2))


def strip_board(html):
    """what may differ between the two members of a pair: the board's record and counts, the
    participant's own code in URLs, and the arm-independent debug table of the dev server"""
    html = re.sub(r'"board":\s*"[01]*"', '"board":"#"', html)
    html = re.sub(r'/p/[a-z0-9]+/', '/p/#/', html)
    html = re.sub(r'Trader board: paid \d+ of', 'Trader board: paid # of', html)
    html = re.sub(r'<div[^>]*class="[^"]*debug-info.*', '', html, flags=re.S)
    html = re.sub(r'data-socket-url="[^"]*"', '', html)
    html = re.sub(r'<title>.*?</title>', '', html, flags=re.S)
    html = re.sub(r'<meta name="tab-title-debug-info"[^>]*>', '', html)
    return html


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
        a_run, a_counts, a_paid = play(browser, links[0], a.base, a.shots, 'A_', DESKTOP, picks, reload=True, back=True)
        b_run, b_counts, b_paid = play(browser, links[1], a.base, a.shots, 'B_', DESKTOP, picks)
        # third participant on a phone, fourth with reduced motion
        c_run, _, _ = play(browser, links[2], a.base, a.shots, 'C_', PHONE, picks, dpr=2)
        d_run, _, _ = play(browser, links[3], a.base, a.shots, 'D_', DESKTOP, picks, reduced='reduce')
        session = re.search(r'/SessionStartLinks/(\w+)', admin.url).group(1)
        if a.timing_config:
            report['timing'] = time_one_round(browser, start_links(admin, a.base, a.timing_config)[0], a.base)
        browser.close()
    # what the server stored: one row per repetition, nothing doubled by the reload or the back button
    st = stored(export_rows(a.base, a.rest_key), session)
    report['stored'] = {k: {x: v[x] for x in ('market', 'probe', 'ratings', 'forecasts')} for k, v in st.items()}
    complete = all(v['market'] == 6 and v['probe'] == 4 and v['ratings'] == 6 and v['forecasts'] == 8 for v in st.values()) and len(st) == 4
    report['stored_complete'] = complete
    report['stored_own_counts_match_screen'] = st[0]['wins'] == [x[0] for x in a_counts] and st[1]['wins'] == [x[0] for x in b_counts]
    report['settle_views_A'] = st[0]['views']
    report['reduced_motion_recorded'] = [m.get('reduced_motion') for m in st[3]['meta']]
    runs = dict(A=a_run, B=b_run, C=c_run, D=d_run)
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
    # G5: nothing of a later round on a choice page; no record on the first-forecast page
    leaks = []
    for run in runs.values():
        for label, html in run.sources:
            if label in ('choose', 'probe_pre') and re.search(r'[01]{10,}', strip_board(html)):
                leaks.append(label)
            if label == 'settle' and len(re.findall(r'"own":\s*"[01]+"', html)) != 1:
                leaks.append('settle carries more than this round')
    report['leaks'] = leaks
    report['probe_paid'] = dict(A=a_paid, B=b_paid)
    print(json.dumps(report, indent=1))
    ok = not (report['console_errors'] or report['failed_requests'] or report['foreign_requests'] or diffs or leaks) \
        and report['pair_same_own_counts'] and complete and report['stored_own_counts_match_screen'] \
        and all(report['reduced_motion_recorded'])
    print('BROWSER RUN', 'PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
