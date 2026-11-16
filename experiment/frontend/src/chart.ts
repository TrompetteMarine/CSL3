/**
 * Chart arithmetic (no DOM): scales, paths, labels. The charts draw what the server sent;
 * nothing here decides an outcome.
 */

export interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

export type Scale = (v: number) => number;

/** linear map of [d0, d1] onto [r0, r1] */
export function linear(d0: number, d1: number, r0: number, r1: number): Scale {
  const span = d1 - d0;
  return (v) => (span === 0 ? r0 : r0 + ((v - d0) / span) * (r1 - r0));
}

/** logarithmic map of [d0, d1] onto [r0, r1]; prices move in ratios, so equal ratios get equal distances */
export function logScale(d0: number, d1: number, r0: number, r1: number): Scale {
  if (!(d0 > 0) || !(d1 > 0)) throw new Error('a log scale needs positive bounds');
  const a = Math.log(d0);
  const lin = linear(a, Math.log(d1), r0, r1);
  return (v) => lin(Math.log(Math.max(v, 1e-9)));
}

const r1 = (v: number): string => (Math.round(v * 10) / 10).toString();

/** 'M x y L x y …' through the first n points */
export function linePath(xs: readonly number[], ys: readonly number[], n = xs.length): string {
  const m = Math.min(n, xs.length, ys.length);
  let d = '';
  for (let i = 0; i < m; i++) d += `${i === 0 ? 'M' : 'L'}${r1(xs[i]!)} ${r1(ys[i]!)}`;
  return d;
}

/** the same line closed down to a base line, for a soft fill under a curve */
export function areaPath(xs: readonly number[], ys: readonly number[], base: number, n = xs.length): string {
  const m = Math.min(n, xs.length, ys.length);
  if (m < 2) return '';
  return `${linePath(xs, ys, m)}L${r1(xs[m - 1]!)} ${r1(base)}L${r1(xs[0]!)} ${r1(base)}Z`;
}

/** running count of filled orders: [0, c1, c2, …], one longer than the record */
export function cumulative(bits: readonly boolean[]): number[] {
  const out = [0];
  let s = 0;
  for (const b of bits) {
    if (b) s++;
    out.push(s);
  }
  return out;
}

/**
 * Two labels that must not overlap: if a and b are closer than `gap`, they are moved apart
 * around their midpoint (keeping their order) and kept inside [lo, hi].
 */
export function dodge(a: number, b: number, gap: number, lo: number, hi: number): [number, number] {
  if (Math.abs(a - b) >= gap) return [clamp(a, lo, hi), clamp(b, lo, hi)];
  const aFirst = a <= b;
  let top = (a + b) / 2 - gap / 2;
  top = clamp(top, lo, Math.max(lo, hi - gap));
  const pair: [number, number] = [top, top + gap];
  return aFirst ? pair : [pair[1], pair[0]];
}

export function clamp(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

/** index of the point nearest to x among the first n */
export function nearestIndex(xs: readonly number[], x: number, n = xs.length): number {
  const m = Math.min(n, xs.length);
  if (m <= 0) return -1;
  let best = 0;
  let dist = Infinity;
  for (let i = 0; i < m; i++) {
    const d = Math.abs(xs[i]! - x);
    if (d < dist) {
      dist = d;
      best = i;
    }
  }
  return best;
}

/** whole numbers from lo to hi (inclusive) that lie strictly inside the bounds */
export function wholeTicks(lo: number, hi: number): number[] {
  const out: number[] = [];
  for (let v = Math.ceil(lo + 1e-9); v <= hi - 1e-9; v++) out.push(v);
  return out;
}

/** a domain centred on `mid` that holds every value, with `pad` (a share) of room on each side */
export function centred(values: readonly number[], mid: number, pad = 0.25): [number, number] {
  let reach = 0;
  for (const v of values) reach = Math.max(reach, Math.abs(v - mid));
  if (reach === 0) reach = Math.abs(mid) * 0.01 || 1;
  const half = reach * (1 + pad);
  return [mid - half, mid + half];
}

/** completed baskets and goods in the open one */
export function basketsOf(goods: number, size: number): [number, number] {
  if (size <= 0) throw new Error('a basket holds at least one good');
  const g = Math.max(0, Math.floor(goods));
  return [Math.floor(g / size), g % size];
}

export function price2(v: number): string {
  return v.toFixed(2);
}
