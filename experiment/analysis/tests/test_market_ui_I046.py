"""The interface's colours and what a change of the interface may not touch, checked without a browser:
contrast of the palette, the colour rule, the fonts shipped with the app, the hooks the browser run relies on
(KGi-DISS-I046), and the phone-first rules of KGi-DISS-I047.

Amended in I047 where the author's answers amended an invariant of I046 (freezes/00_freeze_I047.yaml):
  - YES and NO have no colour of their own any more (I6): their tokens and contrast pairs are gone, and one test
    now checks that no colour in the stylesheet stands for a side or an outcome;
  - the order cards became rows and the price chart the market chart (D2, D3): the tests of the goods' grounds, of
    the marks' strength and of the zone caption name the new rules and class;
  - the bet template shows one figure, the cost in points (R2): no cent sign, no price variable.
Run from the repository root."""
import difflib
import math
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.abspath(os.path.join(HERE, '..', '..'))
CSS = open(os.path.join(EXP, 'frontend', 'src', 'styles', 'app.css'), encoding='utf-8').read()
TOKENS = dict(re.findall(r'--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6});', CSS.split('}')[0]))
NOTE = {'#fdf1e3', '#efc698', '#5f2f08', '#8a3f06'}          # an error banner or a notice, in its own colours


def _rgb(hexa):
    h = hexa.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def _lum(hexa):
    lin = [c / 255 / 12.92 if c / 255 <= 0.04045 else ((c / 255 + 0.055) / 1.055) ** 2.4 for c in _rgb(hexa)]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _oklch(hexa):
    lin = [c / 255 / 12.92 if c / 255 <= 0.04045 else ((c / 255 + 0.055) / 1.055) ** 2.4 for c in _rgb(hexa)]
    l_ = 0.4122214708 * lin[0] + 0.5363325363 * lin[1] + 0.0514459929 * lin[2]
    m_ = 0.2119034982 * lin[0] + 0.6806995451 * lin[1] + 0.1073969566 * lin[2]
    s_ = 0.0883024619 * lin[0] + 0.2817188376 * lin[1] + 0.6299787005 * lin[2]
    l_, m_, s_ = (x ** (1 / 3) for x in (l_, m_, s_))
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def contrast(a, b):
    la, lb = sorted((_lum(TOKENS[a]), _lum(TOKENS[b])), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _blocks(selector_pattern):
    """the declaration blocks of the style rules whose selector matches"""
    return [(sel.strip(), body) for sel, body in (b.split('{', 1) for b in re.findall(r'[^{}]*\{[^{}]*\}', CSS))
            if re.search(selector_pattern, sel)]


def _px(selector_pattern, prop):
    """every value in px a property takes in the rules whose selector matches"""
    return [float(v) for _, body in _blocks(selector_pattern) for v in re.findall(rf'(?<![a-z-]){prop}:\s*([\d.]+)px', body)]


# ------------------------------------------------------------------ contrast

def test_body_text_has_seven_to_one():
    for text, ground in (('ink', 'surface'), ('ink', 'inset'), ('ink', 'page'), ('ink-2', 'surface'), ('ink-2', 'inset'),
                         ('ink', 'sq-wash'), ('ink', 'tri-wash'), ('ink-2', 'sq-wash'), ('ink-2', 'tri-wash')):
        assert contrast(text, ground) >= 7, (text, ground, round(contrast(text, ground), 2))


def test_small_text_has_four_and_a_half_to_one():
    pairs = (('ink-3', 'surface'), ('ink-3', 'inset'), ('ink-3', 'page'), ('note-ink', 'surface'), ('surface', 'ink'))
    for text, ground in pairs:
        assert contrast(text, ground) >= 4.5, (text, ground, round(contrast(text, ground), 2))


def test_marks_and_control_boundaries_have_three_to_one():
    pairs = (('control', 'surface'), ('control', 'inset'), ('control', 'page'), ('sq', 'surface'), ('tri', 'surface'),
             ('sq', 'sq-wash'), ('tri', 'tri-wash'), ('trader', 'surface'), ('ink-3', 'surface'))
    for mark, ground in pairs:
        assert contrast(mark, ground) >= 3, (mark, ground, round(contrast(mark, ground), 2))


def test_a_goods_colour_stands_on_white_or_on_its_own_tint():
    """Triangle's orange has 3.2:1 on white: a grey panel under it (2.96:1) or a stronger tint already breaks 3:1.
    The tint is the good's colour at 5% on the sheet, and the fill zone of the price chart is drawn with the same 5%."""
    for good in ('sq', 'tri'):
        tone, wash = _rgb(TOKENS[good]), _rgb(TOKENS[good + '-wash'])
        assert all(abs(w - (0.05 * t + 0.95 * 255)) <= 0.51 for t, w in zip(tone, wash)), (good, wash)
    assert [body for _, body in _blocks(r'\.dm-zone\b(?!-)')] == [' fill: var(--tone); opacity: .05; }']
    # the rows of the two goods (open for orders, and running), the ticket, the goods legend
    for selector in (r'\.dm-row-body\s*$', r'\.dm-ticket[\w-]*\s*$', r'\.dm-legend\s*$', r'\.dm-rows[\w.-]*\s*$'):
        grounds = [g.strip() for _, body in _blocks(selector) for g in re.findall(r'background(?:-color)?:\s*([^;}]+)', body)]
        assert set(grounds) <= {'var(--surface)', 'var(--wash)'}, (selector, grounds)
    assert contrast('tri', 'inset') < 3 < contrast('tri', 'tri-wash')                    # why: the grey panel is too dark


def test_data_marks_are_drawn_at_full_strength():
    """a line, dot, tick or end mark that carries data is never made fainter than its colour (gate G11): the other
    good's price line is thinner than the ordered good's, never fainter"""
    marks = r'\.dm-(line|dot|tickmark\.is-fill|end|head|head-shape|pick|key|trial|cap-line|glyph)\b(?!-)'
    seen = [sel for sel, _ in _blocks(marks)]
    assert any('is-price-other' in sel for sel in seen) and any('dm-head-shape' in sel for sel in seen)
    for sel, body in _blocks(marks):
        for value in re.findall(r'(?:stroke-|fill-)?opacity\s*:\s*([\d.]+)', body):
            assert float(value) == 1, (sel, value)
    width = lambda sel: [float(v) for _, body in _blocks(sel) for v in re.findall(r'stroke-width:\s*([\d.]+)', body)]
    assert width(r'\.dm-line\.is-price-other\s*$') == [1.0] and width(r'\.dm-line\.is-price\s*$') == [1.5]


def test_the_zone_caption_has_its_own_band_and_lies_under_every_mark():
    """the caption of the fill zone can neither hide a filled order nor be cut by one: the price axis ends above a
    band kept for it, and it is drawn before the lines and the dots. A chart too low for the band has no caption."""
    src = open(os.path.join(EXP, 'frontend', 'src', 'svgchart.ts'), encoding='utf-8').read()
    build = src.split('export class MarketChart', 1)[1].split('show(n: number)', 1)[0]
    assert 'const captioned = this.h >= CAPTION_MIN_H;' in build
    assert 'logScale(lo, hi, box.y + box.h - (captioned ? WORD_ROOM : 5), box.y)' in build
    assert "if (captioned) label(this.svg, box.x + 10, box.y + box.h - 7, zoneLabel, 'dm-zone-word');" in build
    word, other, line, dots = (build.index(x) for x in ("'dm-zone-word'", "class: 'dm-line is-price-other'", "class: 'dm-line is-price'",
                                                        "this.dots = s('g'"))
    assert word < other < line < dots                    # caption, then the other good's line, then the ordered good's, then its dots
    assert int(re.search(r'const WORD_ROOM = (\d+);', src).group(1)) >= 20


def test_page_transitions_only_without_reduced_motion():
    assert len(re.findall(r'@view-transition\b', CSS)) == 1
    assert re.search(r'@media \(prefers-reduced-motion: no-preference\) \{\s*@view-transition \{ navigation: auto; \}\s*\}', CSS)
    reduce = CSS.split('@media (prefers-reduced-motion: reduce) {', 1)[1]
    assert '::view-transition-group(*), ::view-transition-old(*), ::view-transition-new(*) { animation: none !important; }' in reduce
    assert '.dm-now-pulse { display: none; }' in reduce


# ------------------------------------------------------------------ the colour rule (I6, as amended in I047)

def test_the_colour_rule_keeps_its_values():
    """goods and trader: the values certified with the palette validator in I043 and again in I046"""
    assert (TOKENS['sq'], TOKENS['tri'], TOKENS['trader']) == ('#2a78d6', '#eb6834', '#3f4756')
    assert 'color-scheme: light' in CSS and 'prefers-color-scheme' not in CSS          # one light theme


def test_no_colour_stands_for_a_side_or_an_outcome():
    """every colour written in the stylesheet is a neutral, one of the two goods' hues, or a note colour; YES and NO
    have no token; the rules of the bets and of the settled markets name no good's colour"""
    assert not re.search(r'--(yes|no)\b', CSS) and not re.search(r'\bis-(yes|no)\b', CSS)
    hues = [_oklch(TOKENS[g])[2] for g in ('sq', 'tri')]
    rules = re.sub(r'/\*.*?\*/', '', CSS, flags=re.S)
    for hexa in set(re.findall(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b', rules)):
        if hexa.lower() in NOTE:
            continue
        _, chroma, hue = _oklch(hexa)
        near = min(min(abs(hue - h), 360 - abs(hue - h)) for h in hues)
        assert chroma <= 0.03 or near <= 10, (hexa, round(chroma, 3), round(hue))
    for sel, body in _blocks(r'\.dm-(bet|bets|betting|tag|settled)[\w-]*'):
        assert not re.search(r'var\(--(tone|wash|sq|tri)[\w-]*\)', body), sel


# ------------------------------------------------------------------ shipped files and page hooks

def test_fonts_ship_with_the_app_and_nothing_is_fetched_from_elsewhere():
    static = os.path.join(EXP, '_static', 'diss_market')
    fonts = sorted(os.listdir(os.path.join(static, 'fonts')))
    assert fonts == ['ibm-plex-sans-condensed-latin-500-normal.woff2', 'ibm-plex-sans-condensed-latin-600-normal.woff2',
                     'ibm-plex-sans-latin-400-normal.woff2', 'ibm-plex-sans-latin-500-normal.woff2',
                     'ibm-plex-sans-latin-600-normal.woff2']
    built = open(os.path.join(static, 'app.css'), encoding='utf-8').read() + open(os.path.join(static, 'app.js'), encoding='utf-8').read()
    assert not re.search(r'https?://(?!www\.w3\.org/)', built), 'the bundle names another host'
    weight = sum(os.path.getsize(os.path.join(static, d, f)) for d in ('', 'fonts') for f in os.listdir(os.path.join(static, d))
                 if f.endswith(('.css', '.js', '.woff2')))
    assert weight <= 250_000, weight                                                    # gate G13
    for name in os.listdir(os.path.join(EXP, 'diss_market')):
        if name.endswith('.html'):
            page = open(os.path.join(EXP, 'diss_market', name), encoding='utf-8').read()
            assert not re.search(r'(src|href)="https?://', page), name


def _page(name):
    return open(os.path.join(EXP, 'diss_market', name), encoding='utf-8').read()


def test_the_pages_keep_the_hooks_the_browser_run_uses():
    clearing = _page('Clearing.html')
    for hook in ('data-chart="price"', 'data-chart="fills"', 'data-count="own"', 'data-count="board"', 'data-seen', 'data-price',
                 'data-pips', 'data-baskets', 'id="dm-readout"', 'id="dm-gain"', 'id="dm-next"', 'class="dm-counters"',
                 'name="settle_done"', 'name="settle_meta"', 'name="rt_settle_ms"', 'class="dm-rows is-live"',
                 '{{ t.fills_caption }}', '{{ t.held }}', '{{ t.price_label }}'):
        assert hook in clearing, hook
    order = _page('Order.html')
    for hook in ('data-chart="frame"', 'name="ticket"', 'name="rt_choose_ms"', 'id="dm-ticket-good"', 'id="dm-next"',
                 'class="dm-row dm-good"', 'role="radiogroup"', '{{ t.order_btn }}', '{{ t.choose_next }}', '{{ t.cap_label }}'):
        assert hook in order, hook
    rate = _page('Rate.html')
    assert 'data-slider data-start="{{ it.start }}" data-step="5"' in rate and 'name="rate_meta"' in rate
    assert 'data-show-value' not in rate                                                # a rating shows no number (I5)
    ask = _page('_ask.html')
    assert 'data-slider data-step="5" data-unit="%"' in ask and 'data-start' not in ask  # a forecast has no handle until placed
    for name in ('Market.html', '_market.html', '_ask.html'):
        assert not re.search(r'dm-evi|dm-source|dm-bet|¢', _page(name)), name            # no evidence or bet price before the first forecast
    assert not re.search(r'dm-bet|¢|price_yes', _page('Evidence.html'))                   # no bet price before the second forecast


# ------------------------------------------------------------------ KGi-DISS-I047: one unit, one column, a finger

def test_a_bet_shows_one_figure_in_points():
    """the ticket's cost in points, inside the existing sentence; no cent sign and no price figure beside it (R2)"""
    bet = _page('Bet.html')
    assert '¢' not in bet and 'price_yes' not in bet and 'price_no' not in bet
    assert bet.count('{{ cost_yes|safe }}') == 1 and bet.count('{{ cost_no|safe }}') == 1
    for name in os.listdir(os.path.join(EXP, 'diss_market')):
        if name.endswith('.html'):
            assert '¢' not in _page(name), name
    src = open(os.path.join(EXP, 'diss_market', '__init__.py'), encoding='utf-8').read()
    assert "t['bet_cost'].format(cost=f'<b>{int(round(pay * p / 100))}</b>')" in src


def test_one_column_at_every_width():
    """the layout does not change with the width of the window: one column of at most 480 px; the only rule for a
    wider window draws the column's edge"""
    assert re.search(r'\.dm \{ width: min\(480px, 100%\);', CSS)
    wide = re.findall(r'@media \(min-width:[^)]*\)\s*\{((?:[^{}]*\{[^{}]*\})*)\s*\}', CSS)
    assert len(wide) == 1 and re.fullmatch(r'\s*\.dm \{ border-left: [^;]+; border-right: [^;]+; \}\s*', wide[0]), wide
    assert 'min-height: 100dvh' in CSS                                                  # the visible height, without the browser's bars


def test_controls_are_large_enough_for_a_finger():
    """every control is at least 44 px high in every rule that sets its height, and the page's button at least 48 (D9)"""
    assert min(_px(r'\.dm-btn\s*$', 'height')) >= 48
    assert min(_px(r'\.dm-sl\s*$', 'height')) >= 44
    assert min(_px(r'\.dm-chip span\s*$', 'height')) >= 44 and min(_px(r'\.dm-chip span\s*$', 'width')) >= 44
    assert min(_px(r'\.dm-opt span\s*$', 'min-height')) >= 44
    assert min(_px(r'\.dm-good \.dm-row-body\s*$', 'min-height')) >= 44
    assert min(_px(r'\.dm-bet(\.is-pass)? \.dm-bet-card\s*$', 'min-height')) >= 44
    assert min(_px(r'\.dm-field input\[type="text"\]', 'min-height')) >= 44


def test_a_finger_on_a_slider_scrolls_the_page_or_sets_the_slider_never_both():
    """the slider lets the browser scroll up and down; a cancelled touch stores nothing, a tap counts only where the
    finger lifted close to where it came down (I5 as amended). What the browser really does is checked in the browser run."""
    assert all('touch-action: pan-y' in body for _, body in _blocks(r'\.dm-sl\s*$') if 'touch-action' in body)
    assert any('touch-action: pan-y' in body for _, body in _blocks(r'\.dm-sl\s*$'))
    src = open(os.path.join(EXP, 'frontend', 'src', 'slider.ts'), encoding='utf-8').read()
    cancel = src.split("root.addEventListener('pointercancel'", 1)[1].split('});', 1)[0]
    assert 'pending = null' in cancel and 'commit(' not in cancel
    up = src.split("root.addEventListener('pointerup'", 1)[1].split('});', 1)[0]
    assert 'const still = Math.hypot(ev.clientX - pending.x, ev.clientY - pending.y) <= TAP_SLOP;' in up
    assert 'if (still) commit(fromPointer(ev)' in up
    down = src.split("root.addEventListener('pointerdown'", 1)[1].split('});', 1)[0]
    assert down.index("ev.pointerType === 'touch'") < down.index('commit(')            # a finger coming down sets nothing yet


def test_wording_two_draft_strings_added_and_none_changed():
    """gate G4: against the copy of 569c3f8 no line is changed or removed, and the added strings are marked DRAFT"""
    try:
        before = subprocess.run(['git', 'show', '569c3f8:experiment/diss_market/copy_en.py'], cwd=EXP, capture_output=True,
                                text=True, check=True).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError):
        import pytest
        pytest.skip('the repository history is not at hand')
    after = open(os.path.join(EXP, 'diss_market', 'copy_en.py'), encoding='utf-8').read().splitlines()
    diff = [d for d in difflib.ndiff(before, after) if d[:1] in '+-']
    assert not [d for d in diff if d.startswith('-')], diff
    added = [d[2:].strip() for d in diff]
    assert len(added) == 2 and all('# DRAFT (I047)' in a for a in added), added
    assert any(a.startswith("order_btn='Order',") for a in added) and any(a.startswith("fills_caption='Filled orders',") for a in added)


def test_which_prices_are_drawn_is_a_session_key_with_a_conservative_fallback():
    """D4: the configurations of the study draw both goods' prices (the rule frozen in I047, read on
    records/live_cert_ad_I047.txt); a configuration without the key draws the ordered good's only"""
    src = open(os.path.join(EXP, 'diss_market', '__init__.py'), encoding='utf-8').read()
    assert "return session.config.get('price_curves', 'own')" in src
    assert "other_prices=en.price_path(s, d, r, not player.chose_good) if both else None," in src
    settings = open(os.path.join(EXP, 'settings.py'), encoding='utf-8').read()
    cell = settings.split('MARKET_CELL = dict(', 1)[1].split('\n)\n', 1)[0]
    assert "price_curves='both'," in cell
