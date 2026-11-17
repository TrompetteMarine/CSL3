"""The interface's colours and what the polish of KGi-DISS-I046 may not touch, checked without a browser:
contrast of the palette (gate G11 in part), the colour rule's fixed values (invariant I6), the fonts shipped with
the app (I7), and that the page templates still carry the hooks the browser run relies on.
Run from the repository root."""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.abspath(os.path.join(HERE, '..', '..'))
CSS = open(os.path.join(EXP, 'frontend', 'src', 'styles', 'app.css'), encoding='utf-8').read()
TOKENS = dict(re.findall(r'--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6});', CSS.split('}')[0]))


def _lum(hexa):
    rgb = [int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    la, lb = sorted((_lum(TOKENS[a]), _lum(TOKENS[b])), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def test_body_text_has_seven_to_one():
    for text, ground in (('ink', 'surface'), ('ink', 'inset'), ('ink', 'page'), ('ink-2', 'surface'), ('ink-2', 'inset')):
        assert contrast(text, ground) >= 7, (text, ground, round(contrast(text, ground), 2))


def test_small_text_has_four_and_a_half_to_one():
    pairs = (('ink-3', 'surface'), ('ink-3', 'inset'), ('ink-3', 'page'), ('yes-ink', 'yes-wash'), ('no-ink', 'no-wash'),
             ('note-ink', 'surface'), ('surface', 'ink'), ('surface', 'yes-ink'), ('surface', 'no-ink'))
    for text, ground in pairs:
        assert contrast(text, ground) >= 4.5, (text, ground, round(contrast(text, ground), 2))


def test_marks_and_control_boundaries_have_three_to_one():
    pairs = (('control', 'surface'), ('control', 'inset'), ('control', 'page'), ('sq', 'surface'), ('tri', 'surface'),
             ('sq', 'sq-wash'), ('tri', 'tri-wash'), ('trader', 'surface'), ('yes', 'surface'), ('no', 'surface'),
             ('ink-3', 'surface'))
    for mark, ground in pairs:
        assert contrast(mark, ground) >= 3, (mark, ground, round(contrast(mark, ground), 2))


def _blocks(selector_pattern):
    """the declaration blocks of the style rules whose selector matches"""
    return [(sel.strip(), body) for sel, body in (b.split('{', 1) for b in re.findall(r'[^{}]*\{[^{}]*\}', CSS))
            if re.search(selector_pattern, sel)]


def test_a_goods_colour_stands_on_white_or_on_its_own_tint():
    """Triangle's orange has 3.2:1 on white: a grey panel under it (2.96:1) or a stronger tint already breaks 3:1.
    The tint is the good's colour at 5% on the sheet, and the fill zone of the price chart is drawn with the same 5%."""
    for good in ('sq', 'tri'):
        tone = [int(TOKENS[good][i:i + 2], 16) for i in (1, 3, 5)]
        wash = [int(TOKENS[good + '-wash'][i:i + 2], 16) for i in (1, 3, 5)]
        assert all(abs(w - (0.05 * t + 0.95 * 255)) <= 0.51 for t, w in zip(tone, wash)), (good, wash)
    assert [body for _, body in _blocks(r'\.dm-zone\b(?!-)')] == [' fill: var(--tone); opacity: .05; }']
    for selector in (r'\.dm-good-card\s*$', r'\.dm-legend\s*$'):                     # the order cards, the goods legend
        grounds = [g for _, body in _blocks(selector) for g in re.findall(r'background(?:-color)?:\s*([^;}]+)', body)]
        assert 'var(--surface)' in grounds and set(grounds) <= {'var(--surface)', 'var(--wash)'}, (selector, grounds)
    assert contrast('tri', 'inset') < 3 < contrast('tri', 'tri-wash')                    # why: the grey panel is too dark


def test_data_marks_are_drawn_at_full_strength():
    """a line, dot, tick or end mark that carries data is never made fainter than its colour (gate G11)"""
    marks = r'\.dm-(line|dot|tickmark\.is-fill|end|head|key|trial|cap-line|glyph)\b(?!-)'
    for sel, body in _blocks(marks):
        for value in re.findall(r'(?:stroke-|fill-)?opacity\s*:\s*([\d.]+)', body):
            assert float(value) == 1, (sel, value)


def test_the_zone_caption_has_its_own_band_and_lies_under_every_mark():
    """the caption of the fill zone can neither hide a filled order nor be cut by one: the price axis ends above a
    band kept for it, and it is drawn before the line and the dots"""
    src = open(os.path.join(EXP, 'frontend', 'src', 'svgchart.ts'), encoding='utf-8').read()
    build = src.split('export class PriceChart', 1)[1].split('show(n: number)', 1)[0]
    assert 'logScale(lo, hi, box.y + box.h - WORD_ROOM, box.y)' in build
    word, line, dots = (build.index(x) for x in ("'dm-zone-word'", "class: 'dm-line is-price'", "this.dots = s('g'"))
    assert word < line < dots
    assert re.search(r'const WORD_ROOM = (\d+);', src) and int(re.search(r'const WORD_ROOM = (\d+);', src).group(1)) >= 20


def test_page_transitions_only_without_reduced_motion():
    assert len(re.findall(r'@view-transition\b', CSS)) == 1
    assert re.search(r'@media \(prefers-reduced-motion: no-preference\) \{\s*@view-transition \{ navigation: auto; \}\s*\}', CSS)
    reduce = CSS.split('@media (prefers-reduced-motion: reduce) {', 1)[1]
    assert '::view-transition-group(*), ::view-transition-old(*), ::view-transition-new(*) { animation: none !important; }' in reduce
    assert '.dm-now-pulse { display: none; }' in reduce


def test_the_colour_rule_keeps_its_values():
    """goods, trader and bets: the values certified with the palette validator in I043 and again in I046"""
    assert (TOKENS['sq'], TOKENS['tri'], TOKENS['trader'], TOKENS['yes'], TOKENS['no']) == \
        ('#2a78d6', '#eb6834', '#3f4756', '#1f9d55', '#c93a9a')
    assert 'color-scheme: light' in CSS and 'prefers-color-scheme' not in CSS          # one light theme


def test_bet_colours_stay_off_the_procurement_styles():
    """the rules that style the order, clearing and rating pages name neither YES nor NO"""
    for block in re.findall(r'[^{}]*\{[^{}]*\}', CSS):
        sel, body = block.split('{', 1)
        if re.search(r'\.dm-(good|goods|recap|clear|inst|quote|asset|now|counter|baskets|pips|readout|gain|item|sl|anchors|left|zone|dot|tickmark|head|end|key)\b', sel):
            assert not re.search(r'var\(--(yes|no)(-ink|-wash)?\)', body), sel.strip()


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


def test_the_pages_keep_the_hooks_the_browser_run_uses():
    def page(name):
        return open(os.path.join(EXP, 'diss_market', name), encoding='utf-8').read()
    clearing = page('Clearing.html')
    for hook in ('data-chart="price"', 'data-chart="fills"', 'data-count="own"', 'data-count="board"', 'data-seen', 'data-price',
                 'data-pips', 'data-baskets', 'id="dm-readout"', 'id="dm-gain"', 'id="dm-next"', 'class="dm-counters"',
                 'name="settle_done"', 'name="settle_meta"', 'name="rt_settle_ms"'):
        assert hook in clearing, hook
    rate = page('Rate.html')
    assert 'data-slider data-start="{{ it.start }}" data-step="5"' in rate and 'name="rate_meta"' in rate
    assert 'data-show-value' not in rate                                                # a rating shows no number (I5)
    ask = page('_ask.html')
    assert 'data-slider data-step="5" data-unit="%"' in ask and 'data-start' not in ask  # a forecast has no handle until placed
    for name in ('Market.html', '_market.html', '_ask.html'):
        assert not re.search(r'dm-evi|dm-source|dm-bet|¢', page(name)), name             # no evidence or bet price before the first forecast
    assert not re.search(r'dm-bet|¢|price_yes', page('Evidence.html'))                    # no bet price before the second forecast
