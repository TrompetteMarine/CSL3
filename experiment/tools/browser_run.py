"""Browser run of the diss_market app against a running oTree server (KGi-DISS-I042, I043, I046, I047).

Plays whole sessions in Chromium the way a participant would (clicks, drags, waits for the
reveals) and checks what a bot cannot:
  - no console error, no failed request, no request to another host;
  - no page carries a later round, a market's evidence before its first forecast, a bet price
    before the second forecast, or how a market settles; the other good's prices reach the
    clearing page only in a session with price_curves = 'both', and then for the same round
    only, equal to the engine's price path for that good (gates G5 and H2; I047 G3, G6);
  - the two members of a yoked pair who make the same choices get the same pages except
    for the board's numbers (gate G7);
  - a reload during a reveal, and the back button, change nothing that is stored;
  - on a phone, the whole market screen is in view together.

Since KGi-DISS-I047 the phone is the reference device: the sessions are played at 390 x 844, at
375 x 667 and, with taps and touch drags on an emulated phone, at 360 x 640; one session is
played with the keyboard alone in a laptop window, which shows the same column. The touch
session also checks that a scroll gesture which starts on a slider stores nothing.

Since KGi-DISS-I046 it also records, for every page it stops on: the visible text outside the
charts, the number of chart marks, where the button and the charts sit in the window, the size of
every control on a phone, the colours in use on procurement pages, and (with --axe) what an
accessibility audit finds. It compares every stored rating and forecast with the value it dragged
to, lists every animation still running in the session played with reduced motion, plays one
session with the keyboard alone (--keyboard), plays more window sizes (--sizes) and measures frame
times during a reveal (--frames-config). --out writes all of it as JSON; --strict makes the I046
gates binding. tools/mark_contrast.py reads the screenshots written with --shots.

    otree devserver 8000        # in another shell, from experiment/
    python tools/browser_run.py --base http://localhost:8000 --shots /path/for/screenshots
"""
import argparse
import csv
import importlib.util
import io
import json
import math
import os
import re
import sys
import time
import urllib.request
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PHONE = dict(width=390, height=844)             # the reference phone
SMALL_PHONE = dict(width=375, height=667)
TOUCH_PHONE = dict(width=360, height=640)       # the small reference phone, played by touch
BETS = ('YES', 'NO', 'PASS', 'YES')
DESKTOP = dict(width=1280, height=860)          # a laptop window: the same column
SIZES = dict(pixel=dict(width=412, height=915), large=dict(width=430, height=932), se_bars=dict(width=375, height=553),
             phone_bars=dict(width=390, height=664), narrow=dict(width=320, height=568), tablet=dict(width=768, height=1024),
             laptop=dict(width=1280, height=860))
# the sizes at which the frozen fit gate binds (I047, G10); the two last ones are phones with the browser's bars showing
FIT_PHONES = {(360, 640), (375, 667), (390, 844), (412, 915), (430, 932), (375, 553), (390, 664)}
MOBILE_UA = ('Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36')
PROCUREMENT = ('order', 'clearing_done', 'rate')
# an error banner is drawn in its own note colours (I047, G12)
NOTE_COLOURS = {(0xfd, 0xf1, 0xe3), (0xef, 0xc6, 0x98), (0x5f, 0x2f, 0x08), (0x8a, 0x3f, 0x06)}
AXE_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']

# visible text outside the charts ('seen') and text for screen readers only ('spoken')
TEXT_JS = r"""() => {
  const root = document.querySelector('.dm');
  const seen = [], spoken = [];
  if (!root) return {seen, spoken};
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    const el = n.parentElement, s = n.nodeValue.replace(/\s+/g, ' ').trim();
    if (!el || !s || el.closest('svg, script, style, noscript, template')) continue;
    if (el.closest('.dm-sr')) { spoken.push(s); continue; }
    const vis = !el.checkVisibility || el.checkVisibility({checkOpacity: true, checkVisibilityCSS: true, opacityProperty: true, visibilityProperty: true});
    if (vis) seen.push(s);
  }
  return {seen, spoken};
}"""

# where things sit, in page coordinates (so a scrolled page reads the same)
FIT_JS = r"""() => {
  const root = document.querySelector('.dm');
  const y0 = window.scrollY;
  let maxRight = 0, worst = '';
  for (const el of root.querySelectorAll('*')) {
    if (el instanceof SVGElement && el.tagName.toLowerCase() !== 'svg') continue;
    if (el.checkVisibility && !el.checkVisibility()) continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (r.right > maxRight) { maxRight = r.right; worst = (el.getAttribute('class') || el.tagName).slice(0, 60); }
  }
  const box = (sel) => {
    const e = document.querySelector(sel);
    if (!e || (e.checkVisibility && !e.checkVisibility())) return null;
    const r = e.getBoundingClientRect();
    return [r.left, r.top + y0, r.right, r.bottom + y0].map((v) => Math.round(v * 10) / 10);
  };
  const btn = document.querySelector('#dm-next');
  return {vw: window.innerWidth, vh: window.innerHeight, maxRight: Math.round(maxRight * 10) / 10, worst,
          next: box('#dm-next'), nextOff: btn ? btn.disabled : null,
          nextShown: btn ? getComputedStyle(btn).visibility !== 'hidden' : null,
          price: box('[data-chart=price]'), fills: box('[data-chart=fills]'), counters: box('.dm-counters'),
          rows: box('.dm-rows'), ticket: box('.dm-ticket'), evi: box('.dm-evi'), bets: box('.dm-bets'),
          sheet: box('.dm'), scrollW: document.documentElement.scrollWidth,
          sliders: Array.from(document.querySelectorAll('.dm-sl')).map((e) => { const r = e.getBoundingClientRect(); return [Math.round(r.top + y0), Math.round(r.bottom + y0)]; })};
}"""

# controls smaller than 44 x 44 px
TARGET_JS = r"""() => {
  const out = [];
  const sel = ['button', 'a[href]', 'label.dm-good', 'label.dm-opt', 'label.dm-chip', 'label.dm-bet', 'label.dm-check', '.dm-sl',
               'textarea', 'input[type=text]', 'input[type=number]'].map((x) => '.dm ' + x).join(', ');
  for (const el of document.querySelectorAll(sel)) {
    if (el.checkVisibility && !el.checkVisibility()) continue;
    if (getComputedStyle(el).visibility === 'hidden') continue;
    const r = el.getBoundingClientRect();
    if (r.width < 43.5 || r.height < 43.5) out.push([(el.getAttribute('class') || el.tagName).slice(0, 40), Math.round(r.width), Math.round(r.height)]);
  }
  return out;
}"""

# every colour in use on the page, with what it colours
COLOUR_JS = r"""() => {
  const seen = {};
  const add = (c, what) => {
    if (!c || c === 'none' || c === 'transparent' || c.startsWith('url(') || /rgba\(\d+, \d+, \d+, 0\)/.test(c)) return;
    (seen[c] = seen[c] || {})[what] = 1;
  };
  for (const el of document.querySelectorAll('.dm, .dm *')) {
    const tag = el.tagName.toLowerCase();
    const s = getComputedStyle(el);
    if (tag === 'stop') { add(s.stopColor, 'gradient'); continue; }
    if (el.checkVisibility && !el.checkVisibility()) continue;
    if (el instanceof SVGElement && tag !== 'svg') {
      add(s.fill, tag === 'text' ? 'text' : 'fill');
      if (parseFloat(s.strokeWidth) > 0) add(s.stroke, 'stroke');
    } else {
      add(s.color, 'text');
      add(s.backgroundColor, 'background');
      for (const side of ['Top', 'Right', 'Bottom', 'Left']) if (parseFloat(s['border' + side + 'Width']) > 0) add(s['border' + side + 'Color'], 'border');
      if (s.boxShadow && s.boxShadow !== 'none') (s.boxShadow.match(/rgba?\([^)]*\)/g) || []).forEach((c) => add(c, 'shadow'));
      if (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) add(s.outlineColor, 'outline');
      if (s.accentColor && s.accentColor !== 'auto') add(s.accentColor, 'accent');
    }
  }
  return Object.fromEntries(Object.entries(seen).map(([k, v]) => [k, Object.keys(v)]));
}"""

MARKS_JS = r"""() => {
  const verts = (sel) => { const e = document.querySelector(sel); const d = e ? (e.getAttribute('d') || '') : ''; return d ? d.split(/[ML]/).length - 1 : null; };
  // the caption of the fill zone and the marks of the price chart must not meet: how many dots and line vertices touch its box
  const word = document.querySelector('[data-chart=price] text.dm-zone-word');
  let met = null;
  if (word) {
    const b = word.getBBox(), pad = 2;
    const x0 = b.x - pad, x1 = b.x + b.width + pad, y0 = b.y - pad, y1 = b.y + b.height + pad;
    const near = (cx, cy, r) => { const nx = Math.max(x0, Math.min(cx, x1)), ny = Math.max(y0, Math.min(cy, y1)); return (cx - nx) ** 2 + (cy - ny) ** 2 < r * r; };
    met = 0;
    for (const c of document.querySelectorAll('[data-chart=price] circle.dm-dot')) met += near(+c.getAttribute('cx'), +c.getAttribute('cy'), +c.getAttribute('r') + 0.5);
    for (const line of document.querySelectorAll('[data-chart=price] path.dm-line.is-price, [data-chart=price] path.dm-line.is-price-other'))
      for (const p of (line.getAttribute('d') || '').split(/[ML]/).filter(Boolean)) { const [x, y] = p.trim().split(/[ ,]+/).map(Number); met += near(x, y, 1); }
  }
  // the ordered good's line lies on top of the other good's; its dots lie on top of both
  const kids = Array.from(document.querySelectorAll('[data-chart=price] svg > *'));
  const at = (sel) => kids.indexOf(document.querySelector('[data-chart=price] svg > ' + sel));
  const dotGroup = document.querySelector('[data-chart=price] circle.dm-dot');
  const heads = Array.from(document.querySelectorAll('[data-chart=price] g.dm-head-mark')).map((g) => [g.getAttribute('data-good'), g.getAttribute('visibility'), g.querySelectorAll('.dm-head-shape > *').length]);
  return {met,
          other: verts('[data-chart=price] path.dm-line.is-price-other'),
          otherGood: (document.querySelector('[data-chart=price] path.dm-line.is-price-other') || {getAttribute: () => null}).getAttribute('data-good'),
          ownGood: (document.querySelector('[data-chart=price] path.dm-line.is-price') || {getAttribute: () => null}).getAttribute('data-good'),
          ownOnTop: at('path.dm-line.is-price-other') < 0 || at('path.dm-line.is-price-other') < at('path.dm-line.is-price'),
          dotsOnTop: !dotGroup || kids.indexOf(dotGroup.parentNode) > at('path.dm-line.is-price'),
          heads, sent: window.js_vars.other_prices ? window.js_vars.other_prices.length : null,
          rowPrices: Array.from(document.querySelectorAll('.dm-rows.is-live [data-price]')).map((e) => [e.getAttribute('data-price'), e.textContent.trim()]),
          last: [window.js_vars.ticket, window.js_vars.prices[window.js_vars.prices.length - 1], window.js_vars.other_ticket,
                 window.js_vars.other_prices ? window.js_vars.other_prices[window.js_vars.other_prices.length - 1] : null],
          dots: document.querySelectorAll('[data-chart=price] circle.dm-dot').length,
          ticks: document.querySelectorAll('[data-chart=price] rect.dm-tickmark').length,
          price: verts('[data-chart=price] path.dm-line.is-price'),
          own: verts('[data-chart=fills] path.dm-line.is-own'),
          board: verts('[data-chart=fills] path.dm-line.is-board'),
          k: window.js_vars.own.length, wins: window.js_vars.own.split('1').length - 1};
}"""

# is the point of clearing i on the price line under the readout that describes it? (null: not found)
READOUT_OVER_JS = r"""(i) => {
  const svg = document.querySelector('[data-chart=price] svg'), line = svg && svg.querySelector('path.dm-line.is-price');
  const box = document.getElementById('dm-readout');
  const pts = ((line && line.getAttribute('d')) || '').split(/[ML]/).filter(Boolean).map((p) => p.trim().split(/[ ,]+/).map(Number));
  if (!box || !pts[i]) return null;
  const r = svg.getBoundingClientRect(), b = box.getBoundingClientRect();
  const x = r.left + pts[i][0], y = r.top + pts[i][1];
  return x >= b.left - 4 && x <= b.right + 4 && y >= b.top - 4 && y <= b.bottom + 4;
}"""

AXE_JS = r"""async (tags) => {
  const r = await axe.run({exclude: [['.debug-info'], ['#debug-info'], ['.otree-debug-info'], ['#_otree-debug']]},
                          {runOnly: {type: 'tag', values: tags}, resultTypes: ['violations']});
  return r.violations.map((v) => ({id: v.id, impact: v.impact, n: v.nodes.length, where: v.nodes.slice(0, 3).map((x) => x.target.join(' '))}));
}"""


def _oklch(rgb):
    """(r, g, b) in 0..255 -> (lightness, chroma, hue in degrees) in OKLCH"""
    lin = [c / 255 for c in rgb]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in lin]
    l_ = 0.4122214708 * lin[0] + 0.5363325363 * lin[1] + 0.0514459929 * lin[2]
    m_ = 0.2119034982 * lin[0] + 0.6806995451 * lin[1] + 0.1073969566 * lin[2]
    s_ = 0.0883024619 * lin[0] + 0.2817188376 * lin[1] + 0.6299787005 * lin[2]
    l_, m_, s_ = (x ** (1 / 3) for x in (l_, m_, s_))
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def _rgb(text):
    m = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', text)
    if m:
        return tuple(int(x) for x in m.groups())
    m = re.match(r'color\(srgb ([\d.]+) ([\d.]+) ([\d.]+)', text)
    return tuple(round(float(x) * 255) for x in m.groups()) if m else None


GOODS = dict(SQUARE=(0x2a, 0x78, 0xd6), TRIANGLE=(0xeb, 0x68, 0x34))


def foreign_colours(colours):
    """chromatic colours of a procurement page that are not one of the two goods' hues (rule I6)"""
    hues = [_oklch(v)[2] for v in GOODS.values()]
    out = []
    for text, uses in colours.items():
        rgb = _rgb(text)
        if rgb is None:
            out.append((text, uses, 'unreadable'))
            continue
        _, c, h = _oklch(rgb)
        if rgb in NOTE_COLOURS:
            continue
        if c > 0.03 and min(min(abs(h - g), 360 - abs(h - g)) for g in hues) > 10:
            out.append((text, uses, round(h)))
    return out


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
        self.obs = []                                       # one record per page the run stopped on (I046)
        self.axe = None                                     # path of axe.min.js when an audit is wanted
        self.expected = []                                  # (round, field, value) the run dragged or keyed to
        self.moving = []                                    # animations seen running in a reduced-motion session
        self.touch = False                                  # played with taps and touch drags (I047)
        self.cdp = None
        self.clearings = []                                 # per clearing page: the goods and price series it was sent
        self.gestures = []                                  # what a gesture that was not meant for a slider did to it

    def name(self):
        return self.page.evaluate('window.js_vars && window.js_vars.page')

    def observe(self, label):
        """what the page shows and where, for the before-and-after comparison (KGi-DISS-I046)"""
        if label.endswith('_mid'):
            return                                          # a moving page: nothing stable to record
        o = dict(label=label, n=len(self.obs), round=self.page.evaluate("document.querySelector('.dm-roundlabel b') ? document.querySelector('.dm-roundlabel b').textContent : ''"))
        o['fit'] = self.page.evaluate(FIT_JS)
        if label != 'clearing_hover':
            o.update(self.page.evaluate(TEXT_JS))
        if label == 'clearing_done':
            o['marks'] = self.page.evaluate(MARKS_JS)
        if self.page.viewport_size['width'] <= 480:
            o['small'] = self.page.evaluate(TARGET_JS)
        o['colours'] = self.page.evaluate(COLOUR_JS)        # on every page since I047: no colour stands for a side or an outcome
        if self.axe and label != 'clearing_hover':
            self.page.add_script_tag(path=self.axe)
            o['axe'] = self.page.evaluate(AXE_JS, AXE_TAGS)
        o['lang'] = self.page.evaluate('document.documentElement.lang')
        o['title'] = self.page.title()
        self.obs.append(o)

    def shot(self, label):
        self.n += 1
        self.observe(label)
        if self.shots:
            self.page.wait_for_timeout(450)                 # let the page transition finish
            self.page.add_style_tag(content='.debug-info, #debug-info, .otree-debug-info { display: none !important; }')
            self.page.screenshot(path=os.path.join(self.shots, f'{self.tag}{self.n:02d}_{label}.png'), full_page=True)

    def keep_source(self, label):
        self.sources.append((label, self.html))

    def press(self, target):
        """a click, or a tap in a touch session"""
        loc = self.page.locator(target) if isinstance(target, str) else target
        if self.touch:
            loc.tap()
        else:
            loc.click()

    def next(self):
        with self.page.expect_navigation() as nav:
            self.press('#dm-next')
        self.html = nav.value.text()
        self.page.wait_for_timeout(300)                     # the page transition swallows clicks while it runs

    def finger(self, points, pause=16):
        """one finger along the points [(x, y), ...]: down on the first, up after the last"""
        send = lambda kind, pts: self.cdp.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': pts})
        send('touchStart', [dict(x=points[0][0], y=points[0][1])])
        for x, y in points[1:]:
            send('touchMove', [dict(x=x, y=y)])
            self.page.wait_for_timeout(pause)
        send('touchEnd', [])

    def slide(self, index, value):
        """set the index-th slider to a value: a mouse drag, or with a finger a tap (even sliders) or a sideways drag (odd ones)"""
        track = self.page.locator('.dm-sl-track').nth(index)
        track.scroll_into_view_if_needed()
        box = track.bounding_box()
        y = box['y'] + box['height'] / 2
        at = lambda v: box['x'] + box['width'] * v / 100
        if self.touch and index % 2 == 0:
            self.page.touchscreen.tap(at(value), y)
        elif self.touch:
            start = 50 if abs(value - 50) >= 10 else (20 if value >= 50 else 80)
            self.finger([(at(start + (value - start) * i / 8), y + (i % 2)) for i in range(9)])
        else:
            self.page.mouse.move(at(50), y)
            self.page.mouse.down()
            self.page.mouse.move(at(value), y, steps=6)
            self.page.mouse.up()

    def stray_gestures(self):
        """two gestures that start on the last rating slider and are not meant for it: a swipe upwards, which scrolls
        the page, and a swipe downwards at the top of the page, which scrolls nothing. Neither may set the slider."""
        state = ("(i) => { const e = document.querySelectorAll('.dm-sl')[i]; return [e.classList.contains('is-untouched'), "
                 "document.querySelectorAll('[data-slider] input[type=hidden]')[i].value, window.scrollY, document.querySelector('#dm-next').disabled]; }")
        self.page.evaluate("window.__cancels = 0; document.addEventListener('pointercancel', () => { window.__cancels += 1; }, true);")
        i = self.page.locator('.dm-sl').count() - 1
        for kind, dy in (('swipe up', -1), ('swipe down at the top', 1)):
            self.page.evaluate('window.scrollTo(0, 0)')
            self.page.wait_for_timeout(120)
            track = self.page.locator('.dm-sl-track').nth(i)
            box = track.bounding_box()
            view = self.page.viewport_size
            if box['y'] + box['height'] > view['height'] - 4:           # the slider is below the fold: use the first one in view
                i = 0
                box = self.page.locator('.dm-sl-track').nth(i).bounding_box()
            x, y = box['x'] + box['width'] * 0.62, box['y'] + box['height'] / 2
            c0 = self.page.evaluate('window.__cancels')
            self.finger([(x + (k % 2), y + dy * 11 * k) for k in range(13)])
            self.page.wait_for_timeout(350)
            untouched, value, scroll, off = self.page.evaluate(state, i)
            self.gestures.append(dict(kind=kind, slider=i, untouched=untouched, stored=value, scrolled=round(scroll),
                                      cancelled=self.page.evaluate('window.__cancels') - c0, button_off=off))
            if not untouched or value != '' or not off:
                self.notes.append(f'a {kind} that started on slider {i} set it to {value!r}')
        # the browser's own scroll synthesiser: in this test browser it moves the finger without scrolling the page and
        # without cancelling the pointer, which is what a finger does on a page that has nowhere to scroll
        self.page.evaluate('window.scrollTo(0, 0)')
        self.page.wait_for_timeout(120)
        box = self.page.locator('.dm-sl-track').nth(i).bounding_box()
        c0 = self.page.evaluate('window.__cancels')
        self.cdp.send('Input.synthesizeScrollGesture', {'x': box['x'] + box['width'] * 0.62, 'y': box['y'] + box['height'] / 2,
                                                        'yDistance': -160, 'gestureSourceType': 'touch', 'speed': 600})
        self.page.wait_for_timeout(350)
        untouched, value, scroll, off = self.page.evaluate(state, i)
        self.gestures.append(dict(kind='synthesised swipe', slider=i, untouched=untouched, stored=value, scrolled=round(scroll),
                                  cancelled=self.page.evaluate('window.__cancels') - c0, button_off=off))
        if not untouched or value != '' or not off:
            self.notes.append(f'a synthesised swipe that started on slider {i} set it to {value!r}')
        self.page.evaluate('window.scrollTo(0, 0)')
        self.page.wait_for_timeout(120)

    # ---- pages
    def preamble(self):
        assert self.name() == 'consent', self.name()
        self.shot('consent')
        assert self.page.is_disabled('#dm-next')
        self.press('label.dm-check')
        assert self.page.is_checked('input[name=consent]')
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
            self.press(labels.nth(right[0] if i else 1 - right[0]))
        self.next()
        assert self.name() == 'quiz' and self.page.locator('.dm-error').count() == 1, self.name()
        self.shot('quiz_retry')
        for i in range(opts.count()):
            labels = opts.nth(i).locator('label.dm-opt')
            texts = [labels.nth(j).inner_text() for j in range(labels.count())]
            self.press(labels.nth([j for j, t in enumerate(texts) if RIGHT.search(t)][0]))
        self.next()

    def top_points(self):
        return int(self.page.locator('#dm-points').inner_text())

    def market_round(self, pick, ratings, reload_mid=False, back=False, repost=False, hover=False):
        """a procurement round: order, clearing, four ratings"""
        assert self.name() == 'order', self.name()
        self.keep_source('order')
        assert self.page.is_disabled('#dm-next')
        if self.page.evaluate("document.querySelectorAll('[data-chart=frame] path.dm-line, [data-chart=frame] circle.dm-dot, [data-chart=frame] rect.dm-tickmark').length"):
            self.notes.append('the chart of the order page shows a price or a fill')
        if self.page.locator('#dm-ticket-good').is_visible():
            self.notes.append('the ticket names a good before one is chosen')
        self.press(self.page.locator('label.dm-good').nth(pick))
        self.page.wait_for_timeout(250)                     # the row's button changes over 160 ms: read the page after it
        chosen = self.page.locator('input[name=ticket]').nth(pick).get_attribute('value')
        named = self.page.evaluate("Array.from(document.querySelectorAll('#dm-ticket-good [data-good]')).filter(e => !e.hidden).map(e => e.dataset.good)")
        if named != [chosen] or self.page.evaluate("document.querySelector('.dm-order').dataset.good") != chosen:
            self.notes.append(f'the ticket names {named} for an order of {chosen}')
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
            if (view['width'], view['height']) in FIT_PHONES and (box['y'] < 0 or box['y'] + box['height'] > view['height'] or box['width'] < 200):
                self.notes.append(f'{sel} is not fully in view on the clearing page ({view})')
        self.clearings.append(self.page.evaluate(
            "({round: Number(document.querySelector('.dm-roundlabel b').textContent), ticket: window.js_vars.ticket, "
            "prices: window.js_vars.prices, other_ticket: window.js_vars.other_ticket, other_prices: window.js_vars.other_prices})"))
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
        if hover:                                           # the readout names the clearing under the pointer or the finger
            box = self.page.locator('[data-chart=price]').bounding_box()
            mx, my = box['x'] + box['width'] * 0.5, box['y'] + box['height'] * 0.5
            if self.touch:                                  # a finger comes down on the chart and moves a little sideways
                self.cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [dict(x=mx - 6, y=my)]})
                for dx in (-3, 0):
                    self.cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [dict(x=mx + dx, y=my)]})
                    self.page.wait_for_timeout(30)
            else:
                self.page.mouse.move(mx, my)
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
                if self.page.evaluate(READOUT_OVER_JS, i) is not False:   # the readout never lies over its clearing (I046)
                    self.notes.append(f'the readout covers the point of clearing {i + 1}, which it describes')
                sent = self.page.evaluate(f'window.js_vars.other_prices ? [window.js_vars.other_ticket, window.js_vars.other_prices[{i}]] : null')
                if sent:                                    # with two lines the readout also gives the other good's price there
                    name = dict(SQUARE='Square', TRIANGLE='Triangle')[sent[0]]
                    if f'{name} {sent[1]:.2f}' not in text.replace('\n', ' '):
                        self.notes.append(f"the readout does not give the other good's price at clearing {i + 1}: {text!r}")
                elif re.search(r'Square|Triangle', text):
                    self.notes.append(f'the readout names a good whose prices were not sent: {text!r}')
            self.shot('clearing_hover')
            if self.touch:
                self.cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                self.page.wait_for_timeout(120)
                if self.page.locator('#dm-readout').inner_text().strip():
                    self.notes.append('the readout stays after the finger has lifted')
            else:
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
        if self.touch and not self.gestures:
            self.stray_gestures()
        names = self.page.evaluate("Array.from(document.querySelectorAll('[data-slider] input[type=hidden]')).map(e => e.name)")
        for i, v in enumerate(ratings[:-1]):
            self.slide(i, v)
        assert self.page.is_disabled('#dm-next'), 'every slider must be touched'
        self.slide(len(ratings) - 1, ratings[-1])
        rnd = self.page.evaluate("Number(document.querySelector('.dm-roundlabel b').textContent)")
        self.expected += [(rnd, nm, v) for nm, v in zip(names, ratings)]
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
        rnd = self.page.evaluate("Number(document.querySelector('.dm-roundlabel b').textContent)")
        self.expected += [(rnd, 'forecast_pre', pre), (rnd, 'forecast_post', post)]
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
        self.press(self.page.locator(f'label.dm-bet.is-{bet.lower()}'))
        self.shot('bet')
        self.next()
        if self.top_points() != self.points:
            self.notes.append('a bet moved the points total before the markets settled')
        if self.name() == 'recall':
            self.press(self.page.locator(f'label.dm-chip:has(input[name=recall][value="{seen}"])'))
            self.shot('recall')
            self.next()
        return kind, seen

    def closing(self):
        assert self.name() == 'closing', self.name()
        for n in ('rig_suspicion', 'betting_familiarity'):
            self.press(self.page.locator(f'label.dm-chip:has(input[name={n}])').nth(2))
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
    reduced = kw.pop('reduced', 'no-preference')
    touch = kw.pop('touch', False)
    phone = dict(has_touch=True, is_mobile=True, user_agent=MOBILE_UA) if touch else {}
    ctx = browser.new_context(viewport=viewport, device_scale_factor=kw.pop('dpr', 1), reduced_motion=reduced, **phone)
    moving = []
    if reduced == 'reduce':                                 # what still moves when motion is to be reduced (I046, G11)
        ctx.expose_function('__dmMoving', lambda key: moving.append(key))
        ctx.add_init_script(MOVING_JS)
    page = ctx.new_page()
    run = Run(page, base, shots, tag)
    run.moving = moving
    run.axe = kw.pop('axe', None)
    if touch:
        run.touch, run.cdp = True, ctx.new_cdp_session(page)
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


def tab_to(page, test, limit=80):
    """press Tab until the focused element passes the test (a JS function of the element)"""
    for _ in range(limit):
        page.keyboard.press('Tab')
        if page.evaluate(f'(() => {{ const e = document.activeElement; return !!e && ({test})(e); }})()'):
            return
    raise AssertionError(f'the keyboard does not reach: {test}')


def play_keyboard(browser, link, base, picks):
    """a whole session with the keyboard alone: Tab, Space, the arrow keys, Enter (KGi-DISS-I046, G11)"""
    ctx = browser.new_context(viewport=DESKTOP)
    page = ctx.new_page()
    run = Run(page, base, None, 'K_')
    run.html = page.goto(link).text()
    kb = page.keyboard

    def go():
        tab_to(page, "e => e.id === 'dm-next' && !e.disabled")
        with page.expect_navigation() as nav:
            kb.press('Enter')
        run.html = nav.value.text()
        page.wait_for_timeout(300)

    def radio(name, index):
        tab_to(page, f"e => e.type === 'radio' && e.name === '{name}'")
        group = f"Array.from(document.querySelectorAll('input[name={name}]'))"
        at = page.evaluate(f'{group}.indexOf(document.activeElement)')
        if at == index:
            kb.press('Space')
        for _ in range(abs(index - at)):
            kb.press('ArrowDown' if index > at else 'ArrowUp')
        assert page.evaluate(f'{group}.findIndex(e => e.checked)') == index, f'the keyboard did not pick option {index} of {name}'

    def slider(i, keys):
        tab_to(page, f"e => e.getAttribute('role') === 'slider' && Array.from(document.querySelectorAll('.dm-sl')).indexOf(e) === {i}")
        for key in keys:
            kb.press(key)
        return int(page.evaluate(f"document.querySelectorAll('[data-slider] input[type=hidden]')[{i}].value"))

    assert run.name() == 'consent', run.name()
    tab_to(page, "e => e.name === 'consent'")
    kb.press('Space')
    go()
    assert run.name() == 'instructions'
    go()
    assert run.name() == 'quiz'
    for name in page.evaluate("Array.from(new Set(Array.from(document.querySelectorAll('fieldset.dm-q input[type=radio]')).map(e => e.name)))"):
        texts = page.evaluate(f"Array.from(document.querySelectorAll('input[name={name}]')).map(e => e.value)")
        radio(name, [j for j, t in enumerate(texts) if RIGHT.search(t)][0])
    go()
    expected = []
    for r, pick in enumerate(picks):
        assert run.name() == 'order', run.name()
        radio('ticket', pick)
        go()
        assert run.name() == 'clearing'
        page.wait_for_selector('.dm-clearing.is-cleared', timeout=60000)
        go()
        assert run.name() == 'rate'
        names = page.evaluate("Array.from(document.querySelectorAll('[data-slider] input[type=hidden]')).map(e => e.name)")
        starts = page.evaluate("Array.from(document.querySelectorAll('[data-slider]')).map(e => Number(e.dataset.start))")
        for i, (nm, start) in enumerate(zip(names, starts)):
            if i == len(names) - 1:
                assert page.is_disabled('#dm-next'), 'every slider must be touched'
            up = i % 2 == 0
            got = slider(i, ['ArrowRight'] if up else ['ArrowLeft'])
            want = min(100, start + 5) if up else max(0, start - 5)
            if got != want:
                run.notes.append(f'round {r + 1}, {nm}: an arrow key from {start} gave {got}, not {want}')
            expected.append((r + 1, nm, got))
        go()
    for i in range(4):
        assert run.name() == 'market', run.name()
        rnd = len(picks) + i + 1
        pre = slider(0, ['ArrowRight', 'ArrowRight', 'ArrowRight'])           # the first key places the handle at 50
        go()
        assert run.name() == 'evidence'
        page.wait_for_selector('#dm-ask:not([hidden])', timeout=60000)
        post = slider(0, ['ArrowLeft', 'ArrowLeft', 'End', 'PageDown'])
        if (pre, post) != (60, 90):
            run.notes.append(f'market {i + 1}: the keys gave forecasts {pre} and {post}, not 60 and 90')
        expected += [(rnd, 'forecast_pre', pre), (rnd, 'forecast_post', post)]
        go()
        assert run.name() == 'bet', run.name()
        radio('bet', i % 3)
        go()
        if run.name() == 'recall':
            radio('recall', 1)
            go()
    assert run.name() == 'closing', run.name()
    tab_to(page, "e => e.tagName === 'TEXTAREA'")
    kb.type('keyboard run')
    go()
    assert run.name() == 'results'
    run.final_points = run.top_points()
    run.observe('results')
    ctx.close()
    return run, expected


# every CSS animation or transition seen running for longer than 1 ms, polled every 50 ms on every page and
# during the page transitions; the stepped reveal is drawn by script and is not one of them (KGi-DISS-I046, G11)
MOVING_JS = """
(() => {
  const seen = new Set();
  const look = () => {
    let list = [];
    try { list = document.getAnimations(); } catch (e) { return; }
    for (const a of list) {
      if (a.playState !== 'running') continue;
      let d = 0;
      try { d = Number(a.effect.getComputedTiming().duration) || 0; } catch (e) {}
      if (d <= 1) continue;
      const t = a.effect && a.effect.target;
      const who = t ? (t.className && t.className.baseVal !== undefined ? t.className.baseVal : t.className) || t.tagName : '?';
      const key = (a.animationName || a.transitionProperty || a.constructor.name) + ' on ' + String(who).split(' ')[0]
        + ((a.effect && a.effect.pseudoElement) || '') + ', ' + Math.round(d) + ' ms';
      if (!seen.has(key)) { seen.add(key); window.__dmMoving(key); }
    }
  };
  setInterval(look, 50);
  document.addEventListener('DOMContentLoaded', look);
})();
"""

FRAMES_INIT = """
window.__frames = []; window.__span = [null, null];
(function f() {
  const t = performance.now();
  window.__frames.push(t);
  const el = document.querySelector('[data-seen]');
  if (el && window.js_vars && window.js_vars.own) {
    const v = Number(el.textContent);
    if (v > 0 && window.__span[0] === null) window.__span[0] = t;
    if (v >= window.js_vars.own.length && window.__span[1] === null) window.__span[1] = t;
  }
  requestAnimationFrame(f);
})();
"""


def phone_context(browser, dpr=3):
    """the reference phone as the test browser emulates it: 390 x 844, touch, a mobile user agent"""
    return browser.new_context(viewport=PHONE, device_scale_factor=dpr, has_touch=True, is_mobile=True, user_agent=MOBILE_UA)


def frames_one_round(browser, link, base, slowdown=1, dpr=3):
    """frame times during one reveal at the session's real speed on the emulated phone, with the processor slowed if
    asked (G9, G14)"""
    ctx = phone_context(browser, dpr)
    page = ctx.new_page()
    page.add_init_script(FRAMES_INIT)
    run = Run(page, base)
    run.html = page.goto(link).text()
    run.preamble()
    page.locator('label.dm-good').nth(0).click()
    if slowdown > 1:
        ctx.new_cdp_session(page).send('Emulation.setCPUThrottlingRate', {'rate': slowdown})
    run.next()
    page.wait_for_selector('.dm-clearing.is-cleared', timeout=180000)
    meta = json.loads(page.input_value('input[name=settle_meta]'))
    frames, (t0, t1) = page.evaluate('[window.__frames, window.__span]')
    planned = page.evaluate('window.js_vars.reveal_ms')
    ctx.close()
    gaps = sorted(b - a for a, b in zip(frames, frames[1:]) if t0 <= a and b <= t1)
    q = lambda p: round(gaps[min(len(gaps) - 1, int(p * len(gaps)))], 1) if gaps else None
    return dict(slowdown=slowdown, dpr=dpr, planned_reveal_ms=planned, measured_reveal_ms=meta['reveal_ms'], frames=len(gaps),
                curves=meta.get('curves'), median_ms=q(0.5), p95_ms=q(0.95), max_ms=round(gaps[-1], 1) if gaps else None)


def fit_findings(runs):
    """G10 of I047: nothing reaches past the window's right edge at any size; what must be in view without scrolling
    at the phone sizes of FIT_PHONES. Also returns, per window size, how far the rating page's button lies below the
    window (0: in view)."""
    out, rate_need = [], {}
    for tag, run in runs.items():
        for o in run.obs:
            f, lab = o['fit'], o['label']
            size, name = (f['vw'], f['vh']), f"{f['vw']}x{f['vh']}"
            if f['maxRight'] > f['vw'] + 1:
                out.append(f"{tag} {lab} {name}: content reaches {f['maxRight']} px ({f['worst']})")
            inside = lambda b: b is not None and b[1] >= 0 and b[3] <= f['vh'] + 0.5
            need = ()
            if size in FIT_PHONES:
                if lab == 'clearing_done':
                    need = ('price', 'rows', 'counters', 'fills', 'next')
                elif lab == 'order':
                    need = ('rows', 'next')
                elif lab == 'bet' and f['vh'] >= 667:
                    need = ('bets', 'next')
                elif lab in ('market', 'recall') and f['vh'] >= 667:
                    need = ('next',)
                elif lab == 'rate' and f['vh'] >= 844:
                    need = ('sliders', 'next')
                elif lab.startswith('evidence') and f['vh'] >= 844:
                    need = ('evi', 'sliders')
            for part in need:
                boxes = [[0, a, 0, b] for a, b in f['sliders']] if part == 'sliders' else [f[part]]
                if not boxes or not all(inside(b) for b in boxes):
                    out.append(f'{tag} {lab} {name}: {part} is not in view without scrolling {boxes}')
            if lab == 'rate' and f['next']:
                rate_need[name] = max(rate_need.get(name, 0), round(f['next'][3] - f['vh']))
    return out, rate_need


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
                                                meta=[], prices=[], bits=[], values={}, rate_meta=[], inits=[],
                                                sched=int(r['schedule']), chose=[]))
        for name in ('fair1', 'fair2', 'fair3', 'entitle', 'forecast_pre', 'forecast_post'):
            if r.get(name, '') != '':
                d['values'][(int(r['repetition']), name)] = int(float(r[name]))
        if r['kind'] == 'market':
            d['rate_meta'].append(json.loads(r['rate_meta'] or '{}'))
            d['inits'].append(r['rate_inits'])
        if r['kind'] == 'market':
            d['market'] += 1
            d['ratings'] += all(r[k] != '' for k in ('fair1', 'fair2', 'fair3', 'entitle'))
            d['wins'].append(int(r['wins']))
            d['views'].append(int(r['settle_views']))
            d['meta'].append(json.loads(r['settle_meta'] or '{}'))
            d['prices'].append(r['prices'])
            d['bits'].append(r['own_bits'])
            d['chose'].append(int(r['chose_good']))
        else:
            d['probe'] += 1
            d['forecasts'] += (r['forecast_pre'] != '') + (r['forecast_post'] != '')
            d['bets'].append(r['bet'])
    return out


def totals(rows, session):
    return {int(r['slot']): int(r['points_total']) for r in rows
            if r['session'] == session and r['row_type'] == 'participant' and r['points_total'] != ''}


def time_one_round(browser, link, base):
    """one procurement round at the session's real reveal speed on the emulated phone: seconds from the page to 'cleared'"""
    ctx = phone_context(browser)
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


def leaks_of(run, both):
    """what a page's source must not carry (gates G5 and H2; I047 G6). both: the session draws both goods' prices"""
    out = []
    for label, html in run.sources:
        body = strip_board(html)
        if label != 'results' and SECRET.search(body):
            out.append(f'{label}: how a market settles')
        if label in ('order', 'market') and re.search(r'[01]{10,}', body):
            out.append(f'{label}: a record')
        if label == 'order' and (re.search(r'prices"', body) or re.search(r'\d\.\d+(?:,\s*\d\.\d+){5,}', body)):
            out.append('order: clearing prices before the order')
        if label == 'clearing':
            if len(re.findall(r'"own":\s*"[01]+"', html)) != 1:
                out.append('clearing carries more than this round')
            series = re.findall(r'"prices":\s*\[([^\]]*)\]', html)
            others = re.findall(r'"other_prices":\s*(null|\[[^\]]*\])', html)
            k = len(re.search(r'"own":\s*"([01]+)"', html).group(1))
            runs_of_prices = len(re.findall(r'\d\.\d+(?:,\s*\d\.\d+){20,}', body))
            if len(series) != 1 or len(series[0].split(',')) != k:
                out.append("clearing does not carry the ordered good's prices as one series of the round's length")
            if both:
                if len(others) != 1 or others[0] == 'null' or len(others[0].strip('[]').split(',')) != k or runs_of_prices != 2:
                    out.append("clearing does not carry exactly the two goods' prices of this round")
            elif others != ['null'] or runs_of_prices != 1:
                out.append("clearing carries prices beyond the ordered good's own path")
        if label == 'market' and re.search(r'"shown"|"cue"|"evidence"|dm-evi|dm-source|dm-bet|¢', body):
            out.append('market: evidence or a bet price before the first forecast')
        if label == 'evidence' and re.search(r'dm-bet|¢|price_yes', body):
            out.append('evidence: a bet price before the second forecast')
    return out


def engine_check(runs_by_slot, st, schedule_path):
    """every price series a clearing page was sent, against the engine's own price paths for that schedule, round and
    order (I047, G3): the ordered good's, and under 'both' the other good's. Returns (pages checked, pages with a
    second series, what was wrong)."""
    spec = importlib.util.spec_from_file_location('dm_engine', os.path.join(EXP, 'diss_market', 'engine.py'))
    en = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(en)
    obj = en.load_schedules(schedule_path if os.path.isabs(schedule_path) else os.path.join(EXP, schedule_path))
    d = obj['design']
    pages, seconds, bad = 0, 0, []
    for slot, run in runs_by_slot.items():
        if slot not in st:
            continue
        sched = en.schedule_by_id(obj, st[slot]['sched'])
        for c in run.clearings:
            r = c['round'] - 1
            good = bool(st[slot]['chose'][r])
            pages += 1
            if c['prices'] != en.price_path(sched, d, r, good):
                bad.append(f"slot {slot}, round {r + 1}: the ordered good's prices are not the engine's")
            if c['other_prices'] is None:
                if c['other_ticket'] is not None:
                    bad.append(f'slot {slot}, round {r + 1}: a second good is named without prices')
                continue
            seconds += 1
            if c['other_ticket'] == c['ticket'] or c['other_ticket'] not in ('SQUARE', 'TRIANGLE'):
                bad.append(f"slot {slot}, round {r + 1}: the second series is named {c['other_ticket']}")
            if c['other_prices'] != en.price_path(sched, d, r, not good):
                bad.append(f"slot {slot}, round {r + 1}: the other good's prices are not the engine's for that good")
    return pages, seconds, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://localhost:8000')
    ap.add_argument('--config', default='market_e2e')
    ap.add_argument('--curves', default='', choices=('', 'own', 'both'), help='the display mode the session must have (price_curves)')
    ap.add_argument('--schedule', default='schedules/example_seed0_4pairs_v3.json',
                    help="the session's schedule file: the prices sent to the browser are checked against the engine's")
    ap.add_argument('--shots', default='')
    ap.add_argument('--timing-config', default='', help='also time one round of this session config at its real speed')
    ap.add_argument('--rest-key', default=os.environ.get('OTREE_REST_KEY', ''))
    ap.add_argument('--axe', default='', help='path of axe.min.js: audit the phone session and the touch session with it')
    ap.add_argument('--keyboard', action='store_true', help='also play one session with the keyboard alone')
    ap.add_argument('--sizes', action='store_true',
                    help='also play 412 x 915, 430 x 932, 375 x 553, 390 x 664, 320 x 568, 768 x 1024 and 1280 x 860')
    ap.add_argument('--frames-config', default='', help='also measure frame times during a reveal of this session config')
    ap.add_argument('--out', default='', help='write everything recorded to this JSON file')
    ap.add_argument('--strict', action='store_true',
                    help='the gates of I046 and I047 (fit, access, colours, marks, stored values, touch, the prices sent, nothing '
                         'moving under reduced motion) are binding')
    a = ap.parse_args()
    if a.shots:
        os.makedirs(a.shots, exist_ok=True)
    report = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        admin = browser.new_page()
        links = start_links(admin, a.base, a.config)
        picks = [0, 1, 0, 0, 1, 0]
        # slots 0 and 1 are the two members of one pair: same choices, the reference phone
        a_run, a_counts, a_paid = play(browser, links[0], a.base, a.shots, 'A_', PHONE, picks, dpr=2, reload=True, back=True,
                                       repost=True, hover=True, axe=a.axe or None)
        b_run, b_counts, b_paid = play(browser, links[1], a.base, a.shots, 'B_', PHONE, picks, dpr=2)
        # third participant by touch on the small phone, fourth with reduced motion, fifth at 375 x 667
        c_run, _, _ = play(browser, links[2], a.base, a.shots, 'C_', TOUCH_PHONE, picks, dpr=3, touch=True, hover=True,
                           axe=a.axe or None)
        d_run, _, _ = play(browser, links[3], a.base, a.shots, 'D_', PHONE, picks, dpr=2, reduced='reduce')
        e_run, _, _ = play(browser, links[4], a.base, a.shots, 'E_', SMALL_PHONE, picks, dpr=2)
        session = re.search(r'/SessionStartLinks/(\w+)', admin.url).group(1)
        k_run, k_expected, size_runs = None, [], {}
        if a.keyboard:
            k_run, k_expected = play_keyboard(browser, links[5], a.base, picks)
        if a.sizes:
            size_links = start_links(admin, a.base, a.config) + start_links(admin, a.base, a.config)
            for (name, viewport), link in zip(SIZES.items(), size_links):
                size_runs[name], _, _ = play(browser, link, a.base, a.shots, f'{name}_', viewport, picks,
                                             dpr=2 if viewport['width'] <= 480 else 1)
        if a.frames_config:
            fl = start_links(admin, a.base, a.frames_config)
            report['frames'] = [frames_one_round(browser, fl[0], a.base, 1), frames_one_round(browser, fl[1], a.base, 4),
                                frames_one_round(browser, fl[2], a.base, 1, dpr=1)]
        if a.timing_config:
            report['timing'] = time_one_round(browser, start_links(admin, a.base, a.timing_config)[0], a.base)
        browser.close()
    # what the server stored: one row per repetition, nothing doubled by the reload or the back button
    rows = export_rows(a.base, a.rest_key)
    st = stored(rows, session)
    report['stored'] = {k: {x: v[x] for x in ('market', 'probe', 'ratings', 'forecasts', 'bets')} for k, v in st.items()}
    complete = all(v['market'] == 6 and v['probe'] == 4 and v['ratings'] == 6 and v['forecasts'] == 8
                   and v['bets'] == list(BETS) for v in st.values()) and len(st) == 5 + bool(a.keyboard)
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
    watched = dict(runs, **size_runs)                       # the sessions at the extra window sizes are watched for errors and requests too
    report['notes'].update({k: r.notes for k, r in size_runs.items() if r.notes})
    report['console_errors'] = {k: r.errors for k, r in watched.items() if r.errors}
    report['failed_requests'] = {k: r.failed for k, r in watched.items() if r.failed}
    report['foreign_requests'] = {k: r.foreign for k, r in watched.items() if r.foreign}
    # G7: the two members of the pair, same choices
    diffs = []
    for (la, ha), (lb, hb) in zip(a_run.sources, b_run.sources):
        assert la == lb
        if strip_board(ha) != strip_board(hb):
            diffs.append(la)
    report['pair_same_own_counts'] = [x[0] for x in a_counts] == [x[0] for x in b_counts]
    report['pair_board_counts'] = dict(A=[x[1] for x in a_counts], B=[x[1] for x in b_counts])
    report['pair_page_differences_beyond_the_board'] = diffs
    # ---- KGi-DISS-I047: which prices the clearing page was sent, and whether they are the engine's
    modes = {('both' if c['other_prices'] is not None else 'own') for r in watched.values() for c in r.clearings}
    both = modes == {'both'}
    report['price_curves'] = sorted(modes)
    pages, seconds, wrong = engine_check(runs_by_slot, st, a.schedule)
    report['clearing_pages_checked_against_the_engine'] = pages
    report['clearing_pages_with_a_second_series'] = seconds
    report['prices_sent_differ_from_the_engine'] = wrong
    report['curves_recorded'] = sorted({m.get('curves') for v in st.values() for m in v['meta']})
    report['fit_recorded'] = {slot: [m.get('fit') for m in v['meta']] for slot, v in st.items()}
    report['windows_recorded'] = {slot: sorted({(m.get('vw'), m.get('vh')) for m in v['meta']}) for slot, v in st.items()}
    # G5, H2: what a page's source must not carry
    leaks = [x for run in runs.values() for x in leaks_of(run, both)]
    report['leaks'] = leaks
    report['pages_checked_for_leaks'] = sum(len(r.sources) for r in runs.values())
    report['evidence_seen'] = dict(A=a_paid, B=b_paid)
    # ---- KGi-DISS-I046: stored values, chart marks, fit, sizes of controls, colours, audit
    everyone = dict(runs, **({'K': k_run} if k_run else {}), **size_runs)
    exp = {i: r.expected for i, r in runs_by_slot.items()}
    if k_run:
        exp[5] = k_expected
        report['keyboard'] = dict(notes=k_run.notes, errors=k_run.errors,
                                  complete=5 in st and st[5]['market'] == 6 and st[5]['probe'] == 4 and st[5]['ratings'] == 6
                                  and st[5]['forecasts'] == 8)
    report['values_checked'] = sum(len(v) for v in exp.values())
    report['values_checked_by'] = dict(mouse=sum(len(exp[i]) for i in (0, 1, 3, 4)), touch=len(exp[2]), keyboard=len(k_expected))
    report['stored_values_differ_from_those_set'] = [
        [slot, rnd, name, want, st.get(slot, {}).get('values', {}).get((rnd, name))]
        for slot, items in exp.items() for rnd, name, want in items
        if st.get(slot, {}).get('values', {}).get((rnd, name)) != want]
    report['rate_meta_incomplete'] = [slot for slot, v in st.items() for m, init in zip(v['rate_meta'], v['inits'])
                                      if not (len(m.get('touched', [])) == 4 and all(m['touched']) and init)]
    report['touch'] = dict(gestures=c_run.gestures, complete=2 in st and st[2]['market'] == 6 and st[2]['probe'] == 4
                           and st[2]['ratings'] == 6 and st[2]['forecasts'] == 8,
                           sliders_set_by=sorted({b for m in st.get(2, {}).get('rate_meta', []) for b in m.get('by', [])}))
    marks = [o['marks'] for r in everyone.values() for o in r.obs if 'marks' in o]
    report['marks_checked'] = len(marks)

    def marks_ok(m):
        price = lambda v: f'{v:.2f}'
        heads = {h[0]: h for h in m['heads']}
        rows = dict(m['rowPrices'])
        ok = (m['dots'] == m['wins'] and m['ticks'] == m['k'] and m['price'] == m['k'] and not m.get('met')
              and m['own'] == m['k'] + 1 and m['board'] in (None, m['k'] + 1)
              and m['ownGood'] == m['last'][0] and m['ownOnTop'] and m['dotsOnTop']
              and heads.get(m['last'][0], [None, None, 0])[1:] == ['visible', 1] and rows.get(m['last'][0]) == price(m['last'][1]))
        if both:
            return (ok and m['other'] == m['k'] and m['sent'] == m['k'] and m['otherGood'] == m['last'][2] and len(heads) == 2
                    and heads.get(m['last'][2], [None, None, 0])[1:] == ['visible', 1] and rows.get(m['last'][2]) == price(m['last'][3]))
        return ok and m['other'] is None and m['sent'] is None and len(heads) == 1 and len(rows) == 2 \
            and [v for g, v in rows.items() if g != m['last'][0]] == ['–']

    report['marks_wrong'] = [m for m in marks if not marks_ok(m)]
    report['caption_meets_marks'] = sum(m.get('met') or 0 for m in marks)      # dots and line vertices touching the zone's caption
    report['fit'], report['rating_page_button_below_the_window_px'] = fit_findings(everyone)
    report['small_controls'] = sorted({(tag, o['label'], *x) for tag, r in everyone.items() for o in r.obs
                                       for x in o.get('small', []) if o['fit']['vw'] >= 360})
    report['small_controls_at_320'] = sorted({(o['label'], *x) for r in everyone.values() for o in r.obs
                                              for x in o.get('small', []) if o['fit']['vw'] == 320})
    report['foreign_colours'] = sorted({(o['label'], c, ','.join(u), str(h)) for r in everyone.values() for o in r.obs
                                        for c, u, h in foreign_colours(o.get('colours', {}))})
    report['pages_scanned_for_colour'] = sum('colours' in o for r in everyone.values() for o in r.obs)
    audit = {}
    for tag, r in everyone.items():
        for o in r.obs:
            for v in o.get('axe', []):
                audit.setdefault((v['impact'], v['id']), set()).add(o['label'])
    report['audit'] = [dict(impact=k[0], rule=k[1], pages=sorted(v)) for k, v in sorted(audit.items(), key=lambda x: str(x[0]))]
    report['audit_pages'] = sum('axe' in o for r in everyone.values() for o in r.obs)
    report['no_language'] = sorted({o['label'] for r in everyone.values() for o in r.obs if not o['lang']})
    report['no_title'] = sorted({o['label'] for r in everyone.values() for o in r.obs if not o['title'].strip()})
    report['moving_with_reduced_motion'] = sorted(set(d_run.moving))
    if k_run:
        report['notes'].update({'K': k_run.notes} if k_run.notes else {})
        report['console_errors'].update({'K': k_run.errors} if k_run.errors else {})
        report['failed_requests'].update({'K': k_run.failed} if k_run.failed else {})
        report['foreign_requests'].update({'K': k_run.foreign} if k_run.foreign else {})
    if a.out:
        json.dump(dict(report=report, obs={tag: r.obs for tag, r in everyone.items()}), open(a.out, 'w'), indent=1, default=list)
    print(json.dumps(report, indent=1, default=list))
    ok = not (report['console_errors'] or report['failed_requests'] or report['foreign_requests'] or diffs or leaks
              or report['notes']) \
        and report['pair_same_own_counts'] and complete and report['stored_own_counts_match_screen'] \
        and all(report['reduced_motion_recorded']) and report['stored_prices_match_fills'] \
        and report['final_points_on_screen_match_stored'] and a_paid == b_paid
    if 'timing' in report:
        t = report['timing']
        ok = ok and abs(t['measured_reveal_ms'] - t['planned_reveal_ms']) <= 150 and abs(t['hidden_ms'] - 3000) <= 250 \
            and t['settlements_shown_while_hidden'] <= 1
    serious = [x for x in report['audit'] if x['impact'] in ('serious', 'critical')]
    g = c_run.gestures
    gates = dict(values=not report['stored_values_differ_from_those_set'] and not report['rate_meta_incomplete'],
                 marks=not report['marks_wrong'], fit=not report['fit'], controls=not report['small_controls'],
                 colours=not report['foreign_colours'], audit=not serious, language=not report['no_language'],
                 title=not report['no_title'], keyboard=report.get('keyboard', {}).get('complete', True),
                 motion=not report['moving_with_reduced_motion'],
                 # a session by touch is complete; neither stray gesture set a slider; the upward one did scroll the page
                 touch=report['touch']['complete'] and len(g) == 3 and all(x['untouched'] and x['stored'] == '' for x in g)
                 and g[0]['scrolled'] > 0,
                 # one display mode, the one asked for; what was sent is the engine's; the browser recorded what it drew
                 curves=len(modes) == 1 and (not a.curves or modes == {a.curves}) and not wrong and pages > 0
                 and seconds == (pages if both else 0) and report['curves_recorded'] == [2 if both else 1])
    if 'frames' in report:
        plain, slowed, plain1 = report['frames']
        gates['smooth'] = plain['median_ms'] <= 20 and plain['max_ms'] <= 100 and slowed['median_ms'] <= 34
        gates['timing_slowed'] = abs(slowed['measured_reveal_ms'] - slowed['planned_reveal_ms']) <= 250
    print('I047 GATES', json.dumps(gates))
    if a.strict:
        ok = ok and all(gates.values())
    print('BROWSER RUN', 'PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
