import { describe, expect, it } from 'vitest';
import {
  areaPath, basketsOf, centred, clamp, cumulative, dodge, linePath, linear, logScale, nearestIndex, price2, wholeTicks,
} from '../src/chart';
import { parseBits } from '../src/timeline';

describe('scales', () => {
  it('maps the ends of a domain onto the ends of the range', () => {
    const y = linear(0, 120, 200, 10);
    expect(y(0)).toBe(200);
    expect(y(120)).toBe(10);
    expect(y(60)).toBe(105);
    expect(linear(5, 5, 3, 9)(5)).toBe(3);
  });
  it('a log scale gives equal ratios equal distances', () => {
    const y = logScale(2, 8, 0, 100);
    expect(y(2)).toBeCloseTo(0);
    expect(y(8)).toBeCloseTo(100);
    expect(y(4)).toBeCloseTo(50);
    expect(() => logScale(0, 8, 0, 1)).toThrow();
  });
  it('a price above the cap is drawn above the cap line, one at or below it is not', () => {
    const y = logScale(2.1, 7.9, 220, 10);        // screen y grows downwards
    const cap = 4;
    for (const p of [4.01, 4.4, 7.9]) expect(y(p)).toBeLessThan(y(cap));
    for (const p of [3.99, 3.2, 2.1]) expect(y(p)).toBeGreaterThan(y(cap));
    expect(y(4)).toBe(y(cap));
  });
});

describe('paths', () => {
  it('draws only the points that are visible', () => {
    const xs = [0, 10, 20, 30];
    const ys = [5, 6, 7, 8];
    expect(linePath(xs, ys, 0)).toBe('');
    expect(linePath(xs, ys, 2)).toBe('M0 5L10 6');
    expect(linePath(xs, ys)).toBe('M0 5L10 6L20 7L30 8');
    expect(linePath(xs, ys, 99)).toBe(linePath(xs, ys));
  });
  it('closes an area down to its base', () => {
    expect(areaPath([0, 10], [5, 6], 20)).toBe('M0 5L10 6L10 20L0 20Z');
    expect(areaPath([0], [5], 20)).toBe('');
  });
});

describe('filled orders', () => {
  it('counts them clearing by clearing and ends on the total', () => {
    const b = parseBits('0110100111');
    const c = cumulative(b);
    expect(c).toEqual([0, 0, 1, 2, 2, 3, 3, 3, 4, 5, 6]);
    expect(c[c.length - 1]).toBe(b.filter(Boolean).length);
    for (let i = 1; i < c.length; i++) expect(c[i]! - c[i - 1]!).toBe(b[i - 1] ? 1 : 0);
  });
  it('turns goods into baskets without a remainder being lost', () => {
    expect(basketsOf(0, 6)).toEqual([0, 0]);
    expect(basketsOf(5, 6)).toEqual([0, 5]);
    expect(basketsOf(6, 6)).toEqual([1, 0]);
    expect(basketsOf(31, 6)).toEqual([5, 1]);
    for (let g = 0; g < 200; g++) {
      const [full, part] = basketsOf(g, 6);
      expect(full * 6 + part).toBe(g);
    }
    expect(() => basketsOf(3, 0)).toThrow();
  });
});

describe('labels', () => {
  it('leaves labels alone when they are far apart', () => {
    expect(dodge(20, 80, 15, 0, 100)).toEqual([20, 80]);
  });
  it('moves close labels apart, keeps their order and stays inside the plot', () => {
    for (const [a, b] of [[50, 52], [52, 50], [50, 50], [2, 3], [99, 98], [0, 100]] as const) {
      const [x, y] = dodge(a, b, 15, 0, 100);
      expect(Math.abs(x - y)).toBeGreaterThanOrEqual(15 - 1e-9);
      expect(Math.min(x, y)).toBeGreaterThanOrEqual(0);
      expect(Math.max(x, y)).toBeLessThanOrEqual(100);
      if (a < b) expect(x).toBeLessThan(y);
      if (a > b) expect(x).toBeGreaterThan(y);
    }
  });
  it('finds the point under the pointer among the visible ones only', () => {
    const xs = [0, 10, 20, 30, 40];
    expect(nearestIndex(xs, 14)).toBe(1);
    expect(nearestIndex(xs, 16)).toBe(2);
    expect(nearestIndex(xs, 400)).toBe(4);
    expect(nearestIndex(xs, 400, 3)).toBe(2);
    expect(nearestIndex(xs, 5, 0)).toBe(-1);
  });
});

describe('axes', () => {
  it('lists whole prices strictly inside the range', () => {
    expect(wholeTicks(2.1, 7.9)).toEqual([3, 4, 5, 6, 7]);
    expect(wholeTicks(2, 5)).toEqual([3, 4]);
  });
  it('centres a market chart on its line, with the same room above and below', () => {
    const [lo, hi] = centred([4.7, 5.05, 5.0], 5.0, 0.35);
    expect((lo + hi) / 2).toBeCloseTo(5.0);
    expect(lo).toBeLessThan(4.7);
    expect(hi).toBeGreaterThan(5.05);
    expect(hi - 5.0).toBeCloseTo(5.0 - lo);
    const [a, b] = centred([8, 8, 8], 8);
    expect(a).toBeLessThan(8);
    expect(b).toBeGreaterThan(8);
  });
  it('formats prices with two decimals and clamps', () => {
    expect(price2(4)).toBe('4.00');
    expect(price2(3.456)).toBe('3.46');
    expect(clamp(5, 0, 3)).toBe(3);
  });
});
