import {
  type Box, areaPath, centred, clamp, cumulative, dodge, linePath, linear, logScale, nearestIndex, price2, wholeTicks,
} from './chart';

/**
 * The charts of the market screens, drawn as SVG at the size of their host (no scaling, so
 * text keeps its size). Every chart draws only the data it was given; `show(n)` decides how
 * much of it is on screen.
 */

const NS = 'http://www.w3.org/2000/svg';
const STRIP_H = 9;
type Attrs = Record<string, string | number>;

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
  }
}

// ------------------------------------------------------------------ clearing prices

export interface PriceData {
  prices: readonly number[];
  bits: readonly boolean[];
  cap: number;
  lo: number;
  hi: number;
  zoneLabel: string;
}

/**
 * The clearing price of the ordered good against the cap. A filled order is marked twice: a
 * dot on the price line, and a coloured tick in the strip under the chart, where the share of
 * filled orders can be read at a glance however dense the round.
 */
export class PriceChart extends Chart {
  private xs: number[] = [];
  private ys: number[] = [];
  private line: SVGPathElement | null = null;
  private dots: SVGGElement | null = null;
  private strip: SVGGElement | null = null;
  private stripY = 0;
  private tickW = 1;
  private dotR = 3;
  private head: SVGGElement | null = null;
  private cross: SVGLineElement | null = null;
  private shown = 0;
  private drawn = 0;
  private resting = false;
  onHover: ((i: number | null) => void) | null = null;

  constructor(host: HTMLElement, private readonly data: PriceData) {
    super(host);
    this.start();
    this.hover(() => this.xs, () => (this.resting ? this.shown : 0), (i) => this.onHover?.(i));
  }

  protected build(): void {
    const { prices, cap, lo, hi, zoneLabel } = this.data;
    const k = prices.length;
    const box: Box = { x: 4, y: 10, w: this.w - 4 - 44, h: this.h - 10 - 22 - STRIP_H - 6 };
    const x = linear(0, k - 1, box.x + 5, box.x + box.w - 5);
    const y = logScale(lo, hi, box.y + box.h, box.y);
    const spacing = k > 1 ? (box.w - 10) / (k - 1) : box.w;
    this.tickW = clamp(spacing - 1, 1, 6);
    this.dotR = clamp(spacing * 0.62, 1.9, 3.25);
    this.stripY = box.y + box.h + 6;
    this.xs = prices.map((_, i) => x(i));
    this.ys = prices.map((p) => y(p));
    const capY = Math.round(y(cap)) + 0.5;
    const right = box.x + box.w;

    s('rect', { x: box.x, y: capY, width: box.w, height: box.y + box.h - capY, class: 'dm-zone', rx: 3 }, this.svg);
    let lastY = Infinity;                 // a price label needs room: from the one below it and from the cap tag
    for (const v of wholeTicks(lo, hi)) {
      const gy = Math.round(y(v)) + 0.5;
      if (v === cap) {
        lastY = capY;
        continue;
      }
      s('line', { x1: box.x, x2: right, y1: gy, y2: gy, class: 'dm-grid-line' }, this.svg);
      if (lastY - gy >= 15 && Math.abs(gy - capY) >= 16) {
        label(this.svg, right + 8, gy + 4, price2(v));
        lastY = gy;
      }
    }
    s('line', { x1: box.x, x2: right, y1: capY, y2: capY, class: 'dm-cap-line' }, this.svg);
    const tag = s('g', { class: 'dm-cap-tag' }, this.svg);
    s('rect', { x: right + 3, y: capY - 10, width: 40, height: 20, rx: 5 }, tag);
    label(tag, right + 23, capY + 4, price2(cap), '', 'middle');
    label(this.svg, box.x + 9, box.y + box.h - 9, zoneLabel, 'dm-zone-word');
    for (const v of [1, k / 4, k / 2, (3 * k) / 4, k]) {
      const i = Math.round(v);
      label(this.svg, x(i - 1), this.h - 5, String(i), '', i === 1 ? 'start' : i === k ? 'end' : 'middle');
    }
    this.strip = s('g', {}, this.svg);
    this.line = s('path', { class: 'dm-line is-price', d: '' }, this.svg);
    this.dots = s('g', {}, this.svg);
    this.cross = s('line', { class: 'dm-cross', y1: box.y, y2: box.y + box.h, x1: 0, x2: 0, visibility: 'hidden' }, this.svg);
    this.head = s('g', { class: 'dm-head-mark', visibility: 'hidden' }, this.svg);
    s('circle', { class: 'dm-head-halo', r: 9, cx: 0, cy: 0 }, this.head);
    s('circle', { class: 'dm-head', r: 4.5, cx: 0, cy: 0 }, this.head);
    this.drawn = 0;
    this.render();
  }

  show(n: number): void {
    const upto = Math.min(n, this.data.prices.length);
    if (upto <= this.shown) return;
    this.shown = upto;
    this.render();
  }

  /** the reveal is over: the moving head goes, the chart can be read point by point */
  rest(): void {
    this.resting = true;
    this.head?.setAttribute('visibility', 'hidden');
  }

  mark(i: number | null): void {
    if (!this.cross || !this.head) return;
    if (i === null || i < 0 || i >= this.shown) {
      this.cross.setAttribute('visibility', 'hidden');
      if (this.resting) this.head.setAttribute('visibility', 'hidden');
      return;
    }
    const cx = this.xs[i]!;
    this.cross.setAttribute('x1', String(cx));
    this.cross.setAttribute('x2', String(cx));
    this.cross.setAttribute('visibility', 'visible');
    this.head.setAttribute('transform', `translate(${cx} ${this.ys[i]!})`);
    this.head.setAttribute('visibility', 'visible');
  }

  private render(): void {
    if (!this.line || !this.dots || !this.head || !this.strip) return;
    const n = this.shown;
    this.line.setAttribute('d', linePath(this.xs, this.ys, n));
    for (let i = this.drawn; i < n; i++) {
      const filled = this.data.bits[i]!;
      s('rect', {
        class: `dm-tickmark ${filled ? 'is-fill' : 'is-miss'}`, x: this.xs[i]! - this.tickW / 2, y: this.stripY,
        width: this.tickW, height: STRIP_H, rx: Math.min(1, this.tickW / 2),
      }, this.strip);
      if (filled) s('circle', { class: 'dm-dot', r: this.dotR, cx: this.xs[i]!, cy: this.ys[i]! }, this.dots);
    }
    this.drawn = n;
    if (n > 0 && !this.resting) {
      this.head.setAttribute('transform', `translate(${this.xs[n - 1]!} ${this.ys[n - 1]!})`);
      this.head.setAttribute('visibility', 'visible');
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
    const box = (this.box = { x: 30, y: 10, w: this.w - 30 - 56, h: this.h - 10 - 22 });
    const x = linear(0, k, box.x, box.x + box.w);
    const y = (this.yOf = linear(0, k, box.y + box.h, box.y));
    this.xs = Array.from({ length: k + 1 }, (_, i) => x(i));
    for (const v of [0, k / 4, k / 2, (3 * k) / 4, k]) {
      const gy = Math.round(y(v)) + 0.5;
      s('line', { x1: box.x, x2: box.x + box.w, y1: gy, y2: gy, class: v === 0 ? 'dm-base-line' : 'dm-grid-line' }, this.svg);
      label(this.svg, box.x - 7, gy + 4, String(Math.round(v)), '', 'end');
    }
    for (const v of [k / 4, k / 2, (3 * k) / 4, k]) {
      label(this.svg, x(v), this.h - 5, String(Math.round(v)), '', v === k ? 'end' : 'middle');
    }
    const cross = s('line', { class: 'dm-cross', y1: box.y, y2: box.y + box.h, x1: 0, x2: 0, visibility: 'hidden' }, this.svg);
    const board = this.board ? s('path', { class: 'dm-line is-board', d: '' }, this.svg) : null;
    const halo = s('path', { class: 'dm-line-halo', d: '' }, this.svg);
    const own = s('path', { class: 'dm-line is-own', d: '' }, this.svg);
    const boardEnd = this.board ? s('circle', { class: 'dm-end is-board', r: 4.5 }, this.svg) : null;
    const ownEnd = s('circle', { class: 'dm-end is-own', r: 4.5 }, this.svg);
    const boardLabel = this.board ? label(this.svg, 0, 0, this.data.boardLabel, 'dm-end-label') : null;
    const ownLabel = label(this.svg, 0, 0, this.data.ownLabel, 'dm-end-label');
    this.parts = { own, halo, board, ownEnd, boardEnd, ownLabel, boardLabel, cross };
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
    p.ownLabel.setAttribute('x', String(ex + 9));
    p.ownLabel.setAttribute('y', String(ly + 4));
    if (p.boardLabel && by !== null) {
      p.boardLabel.setAttribute('x', String(ex + 9));
      p.boardLabel.setAttribute('y', String(lby + 4));
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
    const box: Box = { x: 4, y: 12, w: this.w - 4 - 50, h: this.h - 12 - 24 };
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
    s('rect', { x: right + 3, y: thrY - 10, width: 46, height: 20, rx: 5 }, tag);
    label(tag, right + 26, thrY + 4, price2(threshold), '', 'middle');
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
