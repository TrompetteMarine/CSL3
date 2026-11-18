import {
  type Box, areaPath, centred, clamp, cumulative, dodge, linePath, linear, logScale, nearestIndex, price2, wholeTicks,
} from './chart';
import { glyphShape } from './glyphs';

/**
 * The charts of the market screens, drawn as SVG at the size of their host (no scaling, so
 * text keeps its size). Every chart draws only the data it was given; `show(n)` decides how
 * much of it is on screen.
 */

const NS = 'http://www.w3.org/2000/svg';
const STRIP_H = 10;
/** height of the band at the foot of the price chart's fill zone that no price reaches: the zone's caption stands in it */
const WORD_ROOM = 22;
/** a chart lower than this (a small phone) has no room for that band: it is drawn without the caption, and the prices get the room */
const CAPTION_MIN_H = 128;
/**
 * The price chart and the running-count chart of the clearing page share their time axis: both
 * keep the same room on the left (axis figures) and on the right (the cap, the line names), and
 * both put clearing j at x(j) on [0, k]. A fill is then a dot straight above its step.
 */
const ROOM_LEFT = 34;
/** room on the right of both clearing charts: less on a phone, where the line names carry no key */
function roomRight(w: number): number {
  return w < 480 ? 56 : 72;
}
type Attrs = Record<string, string | number>;
const r1 = (v: number): string => (Math.round(v * 10) / 10).toString();

function s<K extends keyof SVGElementTagNameMap>(name: K, attrs: Attrs, parent?: Element): SVGElementTagNameMap[K] {
  const el = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  if (parent) parent.appendChild(el);
  return el;
}

function label(parent: Element, x: number, y: number, text: string, cls = '', anchor = 'start'): SVGTextElement {
  const t = s('text', { x, y, class: cls, 'text-anchor': anchor }, parent);
  t.textContent = text;
  return t;
}

abstract class Chart {
  protected readonly svg: SVGSVGElement;
  protected w = 0;
  protected h = 0;

  constructor(protected readonly host: HTMLElement) {
    this.svg = s('svg', { class: 'dm-svg', 'aria-hidden': 'true', focusable: 'false' });
    host.appendChild(this.svg);
  }

  /** first drawing, and a new one whenever the host changes size */
  protected start(): void {
    this.layout();
    if (typeof ResizeObserver !== 'undefined') new ResizeObserver(() => this.layout()).observe(this.host);
    else window.addEventListener('resize', () => this.layout());
  }

  private layout(): void {
    const r = this.host.getBoundingClientRect();
    const w = Math.round(r.width);
    const h = Math.round(r.height);
    if (w === 0 || h === 0 || (w === this.w && h === this.h)) return;
    this.w = w;
    this.h = h;
    this.svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
    this.svg.replaceChildren();
    this.build();
  }

  protected abstract build(): void;

  /** pointer position -> index of the nearest visible point; null when the pointer leaves */
  protected hover(xs: () => readonly number[], visible: () => number, on: (i: number | null) => void): void {
    const at = (ev: PointerEvent): void => {
      const n = visible();
      if (n <= 0) return;
      const r = this.svg.getBoundingClientRect();
      on(nearestIndex(xs(), ev.clientX - r.left, n));
    };
    this.svg.addEventListener('pointermove', at);
    this.svg.addEventListener('pointerdown', at);
    this.svg.addEventListener('pointerleave', () => on(null));
    // a finger that lifts, or a gesture the browser takes for scrolling, ends the reading; a mouse button that lifts does not
    this.svg.addEventListener('pointerup', (ev) => { if (ev.pointerType !== 'mouse') on(null); });
    this.svg.addEventListener('pointercancel', () => on(null));
  }
}

// ------------------------------------------------------------------ clearing prices of the goods market

export interface PriceLine {
  ticket: string;
  prices: readonly number[];
}

export interface MarketData {
  /** clearings in a round */
  k: number;
  cap: number;
  lo: number;
  hi: number;
  zoneLabel: string;
  /** the ordered good's clearing prices; null on the frame shown before an order */
  own: PriceLine | null;
  /** the other good's clearing prices of the same round, when the session shows them */
  other: PriceLine | null;
  /** the ordered good's record: filled or not, clearing by clearing */
  bits: readonly boolean[];
}

/**
 * The goods market: the clearing price of each good shown, against the cap. The head of a line
 * is the good's own shape, so a line is never told from the other by its colour alone. The
 * ordered good's line lies on top and carries what happened to the order: a dot on the line and
 * a coloured tick in the strip under the plot for every filled order. Without a line it is the
 * frame of the order page: the cap, the zone under it and the zone's caption.
 */
export class MarketChart extends Chart {
  private xs: number[] = [];
  private ys: number[] = [];
  private ysOther: number[] = [];
  private line: SVGPathElement | null = null;
  private lineOther: SVGPathElement | null = null;
  private dots: SVGGElement | null = null;
  private strip: SVGGElement | null = null;
  private stripY = 0;
  private tickW = 1;
  private dotR = 3;
  private head: SVGGElement | null = null;
  private headOther: SVGGElement | null = null;
  private pick: SVGCircleElement | null = null;
  private cross: SVGLineElement | null = null;
  private shown = 0;
  private drawn = 0;
  private resting = false;
  onHover: ((i: number | null) => void) | null = null;

  constructor(host: HTMLElement, private readonly data: MarketData) {
    super(host);
    this.start();
    this.hover(() => this.xs, () => (this.resting ? this.shown : 0), (i) => this.onHover?.(i));
  }

  protected build(): void {
    const { k, cap, lo, hi, zoneLabel, own, other } = this.data;
    const box: Box = { x: ROOM_LEFT, y: 10, w: this.w - ROOM_LEFT - roomRight(this.w), h: this.h - 10 - 22 - STRIP_H - 8 };
    const x = linear(0, k, box.x, box.x + box.w);
    // no price is below `lo`: the band under it, at the foot of the fill zone, is kept for the zone's caption
    const captioned = this.h >= CAPTION_MIN_H;
    const y = logScale(lo, hi, box.y + box.h - (captioned ? WORD_ROOM : 5), box.y);
    const spacing = box.w / Math.max(1, k);
    this.tickW = clamp(spacing - 1, 1, 6);
    this.dotR = clamp(spacing * 0.5, 1.7, 3.6);
    this.stripY = box.y + box.h + 7;
    this.xs = Array.from({ length: k }, (_, i) => x(i + 1));
    this.ys = own ? own.prices.map((p) => y(p)) : [];
    this.ysOther = other ? other.prices.map((p) => y(p)) : [];
    const capY = Math.round(y(cap)) + 0.5;
    const right = box.x + box.w;

    s('rect', { x: box.x, y: capY, width: box.w, height: box.y + box.h - capY, class: 'dm-zone', rx: 3 }, this.svg);
    for (const v of [k / 4, k / 2, (3 * k) / 4]) {
      const gx = Math.round(x(Math.round(v))) + 0.5;
      s('line', { x1: gx, x2: gx, y1: box.y, y2: box.y + box.h, class: 'dm-grid-line' }, this.svg);
    }
    let lastY = Infinity;                 // a price label needs room: from the one below it and from the cap tag
    for (const v of wholeTicks(lo, hi)) {
      const gy = Math.round(y(v)) + 0.5;
      if (v === cap) {
        lastY = capY;
        continue;
      }
      s('line', { x1: box.x, x2: right, y1: gy, y2: gy, class: 'dm-grid-line' }, this.svg);
      if (lastY - gy >= 15) {
        label(this.svg, box.x - 8, gy + 4, price2(v), '', 'end');
        lastY = gy;
      }
    }
    // the caption stands in its own band, under every mark: nothing that carries data is ever covered by it
    if (captioned) label(this.svg, box.x + 10, box.y + box.h - 7, zoneLabel, 'dm-zone-word');
    s('line', { x1: box.x, x2: right, y1: capY, y2: capY, class: 'dm-cap-line' }, this.svg);
    const tag = s('g', { class: 'dm-cap-tag' }, this.svg);
    s('rect', { x: right + 7, y: capY - 11, width: 44, height: 22, rx: 6 }, tag);
    label(tag, right + 29, capY + 4, price2(cap), '', 'middle');
    for (const v of [1, k / 4, k / 2, (3 * k) / 4, k]) {
      const i = Math.round(v);
      label(this.svg, x(i), this.h - 4, String(i), '', i === k ? 'end' : 'middle');
    }
    this.strip = s('g', {}, this.svg);
    // the other good's line lies under the ordered good's, thinner and without marks: its price is context
    this.lineOther = other ? s('path', { class: 'dm-line is-price-other', 'data-good': other.ticket, d: '' }, this.svg) : null;
    this.line = own ? s('path', { class: 'dm-line is-price', 'data-good': own.ticket, d: '' }, this.svg) : null;
    this.dots = s('g', own ? { 'data-good': own.ticket } : {}, this.svg);
    this.cross = s('line', { class: 'dm-cross', y1: box.y, y2: box.y + box.h, x1: 0, x2: 0, visibility: 'hidden' }, this.svg);
    this.headOther = other ? this.headOf(other.ticket, false) : null;
    this.head = own ? this.headOf(own.ticket, true) : null;
    this.pick = s('circle', { class: 'dm-pick', r: 5, visibility: 'hidden' }, this.svg);
    this.drawn = 0;
    this.render();
  }

  /** the mark at the end of a line: the good's shape, 12 px, ringed in white; the ordered good's has a halo while the round runs */
  private headOf(ticket: string, ordered: boolean): SVGGElement {
    const g = s('g', { class: `dm-head-mark${ordered ? ' is-ordered' : ''}`, 'data-good': ticket, visibility: 'hidden' }, this.svg);
    if (ordered) s('circle', { class: 'dm-head-halo', r: 10, cx: 0, cy: 0 }, g);
    const shape = s('g', { class: 'dm-head-shape', transform: 'translate(-6 -6) scale(0.5)' }, g);
    shape.innerHTML = glyphShape(ticket);
    return g;
  }

  show(n: number): void {
    const upto = Math.min(n, this.data.k);
    if (upto <= this.shown) return;
    this.shown = upto;
    this.render();
  }

  /** the round has cleared: the halo goes, the chart can be read clearing by clearing */
  rest(): void {
    this.resting = true;
    this.host.classList.add('is-resting');
  }

  /** where clearing i sits, in px from the left edge of the chart */
  xOf(i: number): number {
    return this.xs[i] ?? 0;
  }

  mark(i: number | null): void {
    if (!this.cross || !this.pick) return;
    if (i === null || i < 0 || i >= this.shown || !this.data.own) {
      this.cross.setAttribute('visibility', 'hidden');
      this.pick.setAttribute('visibility', 'hidden');
      return;
    }
    const cx = this.xs[i]!;
    this.cross.setAttribute('x1', String(cx));
    this.cross.setAttribute('x2', String(cx));
    this.cross.setAttribute('visibility', 'visible');
    this.pick.setAttribute('cx', String(cx));
    this.pick.setAttribute('cy', String(this.ys[i]!));
    this.pick.setAttribute('visibility', 'visible');
  }

  private render(): void {
    if (!this.line || !this.dots || !this.head || !this.strip) return;
    const n = this.shown;
    this.line.setAttribute('d', linePath(this.xs, this.ys, n));
    this.lineOther?.setAttribute('d', linePath(this.xs, this.ysOther, n));
    for (let i = this.drawn; i < n; i++) {
      const filled = this.data.bits[i]!;
      s('rect', {
        class: `dm-tickmark ${filled ? 'is-fill' : 'is-miss'}`, x: this.xs[i]! - this.tickW / 2, y: this.stripY,
        width: this.tickW, height: STRIP_H, rx: Math.min(1, this.tickW / 2),
      }, this.strip);
      if (filled) s('circle', { class: 'dm-dot', r: this.dotR, cx: this.xs[i]!, cy: this.ys[i]! }, this.dots);
    }
    this.drawn = n;
    if (n > 0) {
      this.head.setAttribute('transform', `translate(${r1(this.xs[n - 1]!)} ${r1(this.ys[n - 1]!)})`);
      this.head.setAttribute('visibility', 'visible');
      if (this.headOther) {
        this.headOther.setAttribute('transform', `translate(${r1(this.xs[n - 1]!)} ${r1(this.ysOther[n - 1]!)})`);
        this.headOther.setAttribute('visibility', 'visible');
      }
    }
  }
}

// ------------------------------------------------------------------ filled orders, you against the trader

export interface FillsData {
  own: readonly boolean[];
  board: readonly boolean[] | null;
  ownLabel: string;
  boardLabel: string;
}

/** Running count of filled orders. One fixed axis (0 to the number of clearings) in every round. */
export class FillsChart extends Chart {
  private xs: number[] = [];
  private own: number[] = [];
  private board: number[] | null = null;
  private yOf: (v: number) => number = (v) => v;
  private box: Box = { x: 0, y: 0, w: 0, h: 0 };
  private parts: {
    own: SVGPathElement; halo: SVGPathElement; board: SVGPathElement | null;
    ownEnd: SVGCircleElement; boardEnd: SVGCircleElement | null;
    ownLabel: SVGTextElement; boardLabel: SVGTextElement | null; cross: SVGLineElement;
    ownKey: SVGLineElement | null; boardKey: SVGLineElement | null;
  } | null = null;
  private shown = 0;
  private resting = false;
  onHover: ((i: number | null) => void) | null = null;

  constructor(host: HTMLElement, private readonly data: FillsData) {
    super(host);
    this.own = cumulative(data.own);
    this.board = data.board ? cumulative(data.board) : null;
    this.start();
    // point j of a running count is the state after clearing j: the pointer reports clearing j - 1
    this.hover(() => this.xs, () => (this.resting ? this.shown + 1 : 0), (j) => this.onHover?.(j === null ? null : Math.max(0, j - 1)));
  }

  protected build(): void {
    const k = this.data.own.length;
    const box = (this.box = { x: ROOM_LEFT, y: 10, w: this.w - ROOM_LEFT - roomRight(this.w), h: this.h - 10 - 22 });
    const x = linear(0, k, box.x, box.x + box.w);
    const y = (this.yOf = linear(0, k, box.y + box.h, box.y));
    this.xs = Array.from({ length: k + 1 }, (_, i) => x(i));
    for (const v of [0, k / 4, k / 2, (3 * k) / 4, k]) {
      const gy = Math.round(y(v)) + 0.5;
      s('line', { x1: box.x, x2: box.x + box.w, y1: gy, y2: gy, class: v === 0 ? 'dm-base-line' : 'dm-grid-line' }, this.svg);
      label(this.svg, box.x - 8, gy + 4, String(Math.round(v)), '', 'end');
    }
    for (const v of [1, k / 4, k / 2, (3 * k) / 4, k]) {
      const i = Math.round(v);
      label(this.svg, x(i), this.h - 4, String(i), '', i === k ? 'end' : 'middle');
    }
    for (const v of [k / 4, k / 2, (3 * k) / 4]) {
      const gx = Math.round(x(Math.round(v))) + 0.5;
      s('line', { x1: gx, x2: gx, y1: box.y, y2: box.y + box.h, class: 'dm-grid-line' }, this.svg);
    }
    const cross = s('line', { class: 'dm-cross', y1: box.y, y2: box.y + box.h, x1: 0, x2: 0, visibility: 'hidden' }, this.svg);
    const board = this.board ? s('path', { class: 'dm-line is-board', d: '' }, this.svg) : null;
    const halo = s('path', { class: 'dm-line-halo', d: '' }, this.svg);
    const own = s('path', { class: 'dm-line is-own', d: '' }, this.svg);
    const boardEnd = this.board ? s('circle', { class: 'dm-end is-board', r: 4.5 }, this.svg) : null;
    const ownEnd = s('circle', { class: 'dm-end is-own', r: 4.5 }, this.svg);
    const boardLabel = this.board ? label(this.svg, 0, 0, this.data.boardLabel, 'dm-end-label') : null;
    const ownLabel = label(this.svg, 0, 0, this.data.ownLabel, 'dm-end-label');
    // a short stroke of the line's colour before each name, where there is room for it
    const keyed = this.w >= 480;
    const boardKey = this.board && keyed ? s('line', { class: 'dm-key is-board' }, this.svg) : null;
    const ownKey = keyed ? s('line', { class: 'dm-key is-own' }, this.svg) : null;
    this.parts = { own, halo, board, ownEnd, boardEnd, ownLabel, boardLabel, cross, ownKey, boardKey };
    this.render();
  }

  show(n: number): void {
    const upto = Math.min(n, this.data.own.length);
    if (upto <= this.shown) return;
    this.shown = upto;
    this.render();
  }

  rest(): void {
    this.resting = true;
  }

  mark(i: number | null): void {
    const cross = this.parts?.cross;
    if (!cross) return;
    if (i === null || i < 0 || i >= this.shown) {
      cross.setAttribute('visibility', 'hidden');
      return;
    }
    const cx = this.xs[i + 1]!;
    cross.setAttribute('x1', String(cx));
    cross.setAttribute('x2', String(cx));
    cross.setAttribute('visibility', 'visible');
  }

  private render(): void {
    const p = this.parts;
    if (!p) return;
    const n = this.shown;
    const ysOwn = this.own.map(this.yOf);
    const dOwn = linePath(this.xs, ysOwn, n + 1);
    p.own.setAttribute('d', dOwn);
    p.halo.setAttribute('d', dOwn);
    const ex = this.xs[n]!;
    const oy = ysOwn[n]!;
    p.ownEnd.setAttribute('cx', String(ex));
    p.ownEnd.setAttribute('cy', String(oy));
    let by: number | null = null;
    if (this.board && p.board && p.boardEnd) {
      const ysBoard = this.board.map(this.yOf);
      p.board.setAttribute('d', linePath(this.xs, ysBoard, n + 1));
      by = ysBoard[n]!;
      p.boardEnd.setAttribute('cx', String(ex));
      p.boardEnd.setAttribute('cy', String(by));
    }
    const lo = this.box.y + 4;
    const hi = this.box.y + this.box.h + 2;
    const [ly, lby] = by === null ? [Math.min(hi, Math.max(lo, oy)), 0] : dodge(oy, by, 15, lo, hi);
    const place = (name: SVGTextElement, key: SVGLineElement | null, at: number): void => {
      name.setAttribute('x', String(key ? ex + 24 : ex + 9));
      name.setAttribute('y', String(at + 4.5));
      if (!key) return;
      key.setAttribute('x1', String(ex + 11));
      key.setAttribute('x2', String(ex + 19));
      key.setAttribute('y1', String(at));
      key.setAttribute('y2', String(at));
    };
    place(p.ownLabel, p.ownKey, ly);
    if (p.boardLabel && by !== null) {
      place(p.boardLabel, p.boardKey, lby);
    }
  }
}

// ------------------------------------------------------------------ a prediction market's price history

export interface HistoryData {
  chart: readonly number[];
  threshold: number;
  nowLabel: string;
  closeLabel: string;
}

/**
 * Price history of a market's asset up to now, the line it has to close above, and the
 * stretch from now to the close left empty. The line sits in the middle of the axis, with
 * the same room above and below.
 */
export class HistoryChart extends Chart {
  private xs: number[] = [];
  private ys: number[] = [];
  private cross: SVGLineElement | null = null;
  private pick: SVGCircleElement | null = null;
  onHover: ((i: number | null) => void) | null = null;

  constructor(host: HTMLElement, private readonly data: HistoryData) {
    super(host);
    this.start();
    this.hover(() => this.xs, () => this.xs.length, (i) => {
      this.mark(i);
      this.onHover?.(i);
    });
  }

  protected build(): void {
    const { chart, threshold, nowLabel, closeLabel } = this.data;
    const n = chart.length;
    const box: Box = { x: 2, y: 12, w: this.w - 2 - 56, h: this.h - 12 - 24 };
    const right = box.x + box.w;
    const nowX = box.x + box.w * 0.8;
    const x = linear(0, n - 1, box.x + 4, nowX);
    const [d0, d1] = centred(chart, threshold, 0.35);
    const y = linear(d0, d1, box.y + box.h, box.y);
    this.xs = chart.map((_, i) => x(i));
    this.ys = chart.map((v) => y(v));
    const thrY = Math.round(y(threshold)) + 0.5;

    const defs = s('defs', {}, this.svg);
    const grad = s('linearGradient', { id: 'dm-hist-fill', x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
    s('stop', { offset: '0', 'stop-color': 'currentColor', 'stop-opacity': 0.13 }, grad);
    s('stop', { offset: '1', 'stop-color': 'currentColor', 'stop-opacity': 0 }, grad);
    const hatch = s('pattern', { id: 'dm-hist-hatch', width: 7, height: 7, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)' }, defs);
    s('line', { x1: 0, y1: 0, x2: 0, y2: 7, class: 'dm-hatch-line' }, hatch);

    s('rect', { x: nowX, y: box.y, width: right - nowX, height: box.h, fill: 'url(#dm-hist-hatch)', class: 'dm-future' }, this.svg);
    const reach = (d1 - d0) / 2 / 1.35;
    for (const v of [threshold + reach, threshold - reach]) {
      const gy = Math.round(y(v)) + 0.5;
      s('line', { x1: box.x, x2: right, y1: gy, y2: gy, class: 'dm-grid-line' }, this.svg);
      label(this.svg, right + 8, gy + 4, price2(v));
    }
    s('path', { class: 'dm-area', d: areaPath(this.xs, this.ys, box.y + box.h), fill: 'url(#dm-hist-fill)' }, this.svg);
    s('line', { x1: box.x, x2: right, y1: thrY, y2: thrY, class: 'dm-cap-line' }, this.svg);
    const tag = s('g', { class: 'dm-cap-tag' }, this.svg);
    s('rect', { x: right + 6, y: thrY - 11, width: 50, height: 22, rx: 6 }, tag);
    label(tag, right + 31, thrY + 4, price2(threshold), '', 'middle');
    s('line', { x1: right, x2: right, y1: box.y, y2: box.y + box.h, class: 'dm-close-line' }, this.svg);
    s('path', { class: 'dm-line is-history', d: linePath(this.xs, this.ys) }, this.svg);
    this.cross = s('line', { class: 'dm-cross', y1: box.y, y2: box.y + box.h, x1: 0, x2: 0, visibility: 'hidden' }, this.svg);
    this.pick = s('circle', { class: 'dm-head is-history', r: 4.5, visibility: 'hidden' }, this.svg);
    const lx = this.xs[n - 1]!;
    const ly = this.ys[n - 1]!;
    s('circle', { class: 'dm-now-pulse', r: 5, cx: lx, cy: ly }, this.svg);
    s('circle', { class: 'dm-head is-history', r: 5, cx: lx, cy: ly }, this.svg);
    label(this.svg, lx, this.h - 6, nowLabel, 'dm-axis-word', 'middle');
    label(this.svg, right, this.h - 6, closeLabel, 'dm-axis-word', 'end');
  }

  private mark(i: number | null): void {
    if (!this.cross || !this.pick) return;
    if (i === null || i < 0) {
      this.cross.setAttribute('visibility', 'hidden');
      this.pick.setAttribute('visibility', 'hidden');
      return;
    }
    const cx = this.xs[i]!;
    this.cross.setAttribute('x1', String(cx));
    this.cross.setAttribute('x2', String(cx));
    this.cross.setAttribute('visibility', 'visible');
    this.pick.setAttribute('cx', String(cx));
    this.pick.setAttribute('cy', String(this.ys[i]!));
    this.pick.setAttribute('visibility', 'visible');
  }
}

// ------------------------------------------------------------------ ten trial closes

/**
 * Trial closes of a market, one after the other: a filled dot above the line when the trial
 * closed above it, a ring below the line when it did not. Position and shape say the same
 * thing; no price level is drawn, because none was recorded.
 */
export class TrialStrip extends Chart {
  private marks: SVGGElement | null = null;
  private slots: number[] = [];
  private mid = 0;
  private shown = 0;
  private drawn = 0;

  constructor(host: HTMLElement, private readonly bits: readonly boolean[], private readonly words: { above: string; below: string }) {
    super(host);
    this.start();
  }

  get length(): number {
    return this.bits.length;
  }

  protected build(): void {
    const n = this.bits.length;
    const gutter = Math.min(104, Math.max(72, this.w * 0.2));
    const mid = (this.mid = Math.round(this.h / 2) + 0.5);
    const span = this.w - gutter - 6;
    this.slots = this.bits.map((_, i) => gutter + ((i + 0.5) * span) / n);
    s('line', { x1: 0, x2: this.w, y1: mid, y2: mid, class: 'dm-cap-line' }, this.svg);
    label(this.svg, 0, mid - 13, this.words.above, 'dm-lane-word');
    label(this.svg, 0, mid + 22, this.words.below, 'dm-lane-word');
    for (const cx of this.slots) s('line', { x1: cx, x2: cx, y1: mid - 3, y2: mid + 3, class: 'dm-slot' }, this.svg);
    this.marks = s('g', {}, this.svg);
    this.drawn = 0;
    this.render();
  }

  show(n: number): void {
    const upto = Math.min(n, this.bits.length);
    if (upto <= this.shown) return;
    this.shown = upto;
    this.render();
  }

  private render(): void {
    if (!this.marks) return;
    const r = Math.min(9, Math.max(6, (this.slots[1]! - this.slots[0]!) * 0.3));
    for (let i = this.drawn; i < this.shown; i++) {
      const up = this.bits[i]!;
      s('circle', {
        class: `dm-trial ${up ? 'is-above' : 'is-below'}`, r, cx: this.slots[i]!, cy: this.mid + (up ? -1 : 1) * (r + 9),
      }, this.marks);
    }
    this.drawn = this.shown;
  }
}
