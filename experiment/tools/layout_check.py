"""Text that is cut off, pieces of text that lie over each other, and text that leaves the window or its
sheet, on every page at several window sizes (KGi-DISS-I046).

A glance at a reduced screenshot misses these. The script plays one session per window size against a
running server, the way tools/browser_run.py does, and on every page the session stops on it looks at
every piece of text, in the page and in the charts:
  cut    the text does not fit the box that clips it;
  over   two pieces of text overlap by more than 1.5 px across and 3 px down;
  out    a piece of text reaches past the window, or past the sheet it belongs to.
It prints what it finds and exits with status 1 if it finds anything.

    otree devserver 8000        # in another shell, from experiment/
    python tools/layout_check.py --base http://localhost:8000
    python tools/layout_check.py --config market_seed --sizes 1280x860,390x844      # a session without a board
"""
import argparse
import collections
import json
import os
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import browser_run as br  # noqa: E402

SIZES = '1920x1080,1366x768,1366x650,1280x860,390x844,375x667,320x568'

LOOK_JS = r"""() => {
  const root = document.querySelector('.dm');
  const out = {cut: [], over: [], out: []};
  if (!root) return out;
  const vw = window.innerWidth;
  const shown = (el) => !el.checkVisibility || el.checkVisibility({checkOpacity: true, checkVisibilityCSS: true, opacityProperty: true, visibilityProperty: true});
  const name = (el) => (el.getAttribute('class') || el.tagName).toString().split(' ')[0];
  const spoken = (el) => { const r = el.closest('.dm-roundlabel'); return !!el.closest('.dm-sr') || (!!r && getComputedStyle(r).position === 'absolute'); };
  // text that does not fit the box that clips it
  for (const el of root.querySelectorAll('*')) {
    if (el instanceof SVGElement || !shown(el) || spoken(el)) continue;
    const cs = getComputedStyle(el);
    if (!el.textContent.trim() || cs.display === 'inline') continue;
    const clipsX = ['hidden', 'clip'].includes(cs.overflowX) || cs.textOverflow === 'ellipsis';
    const clipsY = ['hidden', 'clip'].includes(cs.overflowY);
    if ((clipsX && el.scrollWidth > el.clientWidth + 1) || (clipsY && el.scrollHeight > el.clientHeight + 1))
      out.cut.push([name(el), el.textContent.trim().slice(0, 40)]);
  }
  // every piece of text, line by line, in the page and in the charts
  const boxes = [];
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    const el = n.parentElement, s = n.nodeValue.replace(/\s+/g, ' ').trim();
    if (!el || !s || el.closest('script, style, noscript, template') || !shown(el) || spoken(el)) continue;
    const range = document.createRange();
    range.selectNodeContents(n);
    for (const r of range.getClientRects()) {
      if (r.width >= 1 && r.height >= 1) boxes.push({el, s, l: r.left, t: r.top, r: r.right, b: r.bottom});
    }
  }
  for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
    const a = boxes[i], b = boxes[j];
    if (a.el === b.el || a.el.contains(b.el) || b.el.contains(a.el)) continue;
    const ox = Math.min(a.r, b.r) - Math.max(a.l, b.l), oy = Math.min(a.b, b.b) - Math.max(a.t, b.t);
    if (ox > 1.5 && oy > 3) out.over.push([name(a.el), a.s.slice(0, 30), name(b.el), b.s.slice(0, 30)]);
  }
  const sheet = root.querySelector('.dm-main');
  const lim = sheet ? sheet.getBoundingClientRect() : null;
  for (const b of boxes) {
    if (b.r > vw + 0.5 || b.l < -0.5) out.out.push(['window', name(b.el), b.s.slice(0, 30)]);
    else if (lim && b.el.closest('.dm-main') && (b.r > lim.right + 0.5 || b.l < lim.left - 0.5)) out.out.push(['sheet', name(b.el), b.s.slice(0, 30)]);
  }
  return out;
}"""


def look_at_a_session(browser, link, base, width, height):
    """one whole session at this window size: {kind: {finding: pages}}, pages looked at, the run"""
    ctx = browser.new_context(viewport=dict(width=width, height=height), device_scale_factor=2 if width <= 400 else 1)
    page = ctx.new_page()
    run = br.Run(page, base)
    found = collections.defaultdict(lambda: collections.defaultdict(set))
    seen = [0]
    plain_shot = run.shot

    def shot(label):
        plain_shot(label)
        page.wait_for_timeout(350)                          # let the page transition and the fades end
        seen[0] += 1
        for kind, items in page.evaluate(LOOK_JS).items():
            for item in items:
                found[kind][json.dumps(item)].add(label)
    run.shot = shot
    run.html = page.goto(link).text()
    run.preamble()
    for r, pick in enumerate([0, 1, 0, 0, 1, 0]):
        run.market_round(pick, [20 + 10 * r, 55, 70 - 5 * r, 40], hover=(r == 4 and width > 760))
    for i, bet in enumerate(br.BETS):
        run.market(40 + 5 * i, 60 - 5 * i, bet)
    run.closing()
    ctx.close()
    return found, seen[0], run


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://localhost:8000')
    ap.add_argument('--config', default='market_e2e')
    ap.add_argument('--sizes', default=SIZES, help='window sizes, e.g. 1280x860,390x844')
    a = ap.parse_args()
    sizes = [tuple(int(v) for v in s.split('x')) for s in a.sizes.split(',')]
    bad = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        admin = browser.new_page()
        for width, height in sizes:
            link = br.start_links(admin, a.base, a.config)[0]
            found, pages, run = look_at_a_session(browser, link, a.base, width, height)
            n = sum(len(v) for v in found.values())
            bad += n + len(run.errors)
            print(f'{width} x {height}: {pages} pages; cut {len(found["cut"])}, over {len(found["over"])}, out {len(found["out"])}; '
                  f'console errors {len(run.errors)}', flush=True)
            for kind in ('cut', 'over', 'out'):
                for item, labels in sorted(found[kind].items()):
                    print(f'    {kind}: {item} on {", ".join(sorted(labels))}')
        browser.close()
    print('LAYOUT CHECK', 'FAIL' if bad else 'PASS')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
