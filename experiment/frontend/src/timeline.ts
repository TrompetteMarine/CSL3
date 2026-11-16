/**
 * Pure display logic (no DOM): what is on screen at a given moment.
 * The browser never computes an outcome; it only decides when to show what the server sent.
 */

/** '0110…' -> [false, true, true, false, …] */
export function parseBits(bits: string): boolean[] {
  const out: boolean[] = [];
  for (const c of bits) {
    if (c !== '0' && c !== '1') throw new Error(`not a settlement record: ${c}`);
    out.push(c === '1');
  }
  return out;
}

/** number of settlements among the first n that paid */
export function paidAmong(bits: readonly boolean[], n: number): number {
  let s = 0;
  for (let i = 0; i < Math.min(n, bits.length); i++) if (bits[i]) s++;
  return s;
}

/** columns of the settlement grid: the widest of 15, 12, 10, 8, 5 that divides k (else 10) */
export function gridCols(k: number): number {
  for (const c of [15, 12, 10, 8, 5]) if (k % c === 0 && k / c >= 1) return c;
  return 10;
}

/**
 * How many of n settlements are visible after `elapsed` ms of a reveal lasting `total` ms.
 * Constant pace; the last one appears exactly at `total`.
 */
export function dueCount(elapsed: number, total: number, n: number): number {
  if (n <= 0) return 0;
  if (total <= 0 || elapsed >= total) return n;
  if (elapsed <= 0) return 0;
  return Math.min(n, Math.floor((elapsed / total) * n + 1e-9));
}

/** the same reveal in `chunks` equal steps (reduced motion): same duration, fewer changes */
export function dueCountStepped(elapsed: number, total: number, n: number, chunks: number): number {
  if (n <= 0) return 0;
  if (total <= 0 || elapsed >= total) return n;
  if (elapsed <= 0) return 0;
  const c = Math.max(1, Math.min(chunks, n));
  const done = Math.floor((elapsed / total) * c + 1e-9);
  return Math.min(n, Math.round((done / c) * n));
}

/**
 * Regrouping after the reveal: paid settlements first, each group in its original order.
 * Returns, for each new position, the original index of the cell that moves there.
 */
export function regroupOrder(bits: readonly boolean[]): number[] {
  const paid: number[] = [];
  const unpaid: number[] = [];
  bits.forEach((b, i) => (b ? paid : unpaid).push(i));
  return paid.concat(unpaid);
}

/** nearest multiple of `step` inside [min, max] */
export function snap(value: number, step: number, min = 0, max = 100): number {
  const v = Math.round((value - min) / step) * step + min;
  return Math.min(max, Math.max(min, v));
}

/** slider position (0..1 along the track) -> value */
export function fractionToValue(f: number, step: number, min = 0, max = 100): number {
  const x = Math.min(1, Math.max(0, f));
  return snap(min + x * (max - min), step, min, max);
}

/** value -> slider position (0..1) */
export function valueToFraction(v: number, min = 0, max = 100): number {
  return max === min ? 0 : (Math.min(max, Math.max(min, v)) - min) / (max - min);
}

/** integer count-up shown while a number changes from a to b; p in [0, 1] */
export function tween(a: number, b: number, p: number): number {
  const x = Math.min(1, Math.max(0, p));
  const eased = 1 - Math.pow(1 - x, 3);
  return Math.round(a + (b - a) * eased);
}
