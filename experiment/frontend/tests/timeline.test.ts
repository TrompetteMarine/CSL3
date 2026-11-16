import { describe, expect, it } from 'vitest';
import {
  dueCount, dueCountStepped, fractionToValue, paidAmong, parseBits, snap, tween,
  valueToFraction,
} from '../src/timeline';

describe('settlement records', () => {
  it('parses bits and refuses anything else', () => {
    expect(parseBits('0110')).toEqual([false, true, true, false]);
    expect(() => parseBits('01x')).toThrow();
  });
  it('counts paid settlements among the first n', () => {
    const b = parseBits('1101001');
    expect([0, 1, 2, 3, 7, 99].map((n) => paidAmong(b, n))).toEqual([0, 1, 2, 2, 4, 4]);
  });
});

describe('reveal timing', () => {
  it('shows nothing at the start and everything at the end', () => {
    expect(dueCount(0, 9000, 120)).toBe(0);
    expect(dueCount(9000, 9000, 120)).toBe(120);
    expect(dueCount(20000, 9000, 120)).toBe(120);
    expect(dueCount(-5, 9000, 120)).toBe(0);
  });
  it('is monotone, never skips ahead of constant pace, and ends exactly once', () => {
    let last = 0;
    for (let t = 0; t <= 9000; t += 7) {
      const n = dueCount(t, 9000, 120);
      expect(n).toBeGreaterThanOrEqual(last);
      expect(n).toBeLessThanOrEqual(Math.floor((t / 9000) * 120) + 1);
      last = n;
    }
    expect(dueCount(4500, 9000, 120)).toBe(60);
    expect(dueCount(75, 9000, 120)).toBe(1);
  });
  it('the stepped reveal has the same duration and total', () => {
    expect(dueCountStepped(0, 9000, 120, 12)).toBe(0);
    expect(dueCountStepped(8999, 9000, 120, 12)).toBe(110);
    expect(dueCountStepped(9000, 9000, 120, 12)).toBe(120);
    const seen = new Set<number>();
    for (let t = 0; t <= 9000; t += 10) seen.add(dueCountStepped(t, 9000, 120, 12));
    expect(seen.size).toBe(13);
    expect(dueCountStepped(3000, 6000, 10, 12)).toBe(5);
  });
  it('degenerate inputs do not hang a page', () => {
    expect(dueCount(10, 0, 5)).toBe(5);
    expect(dueCount(10, 100, 0)).toBe(0);
  });
});

describe('sliders', () => {
  it('snaps to steps of five inside the scale', () => {
    expect(snap(52.4, 5)).toBe(50);
    expect(snap(52.6, 5)).toBe(55);
    expect(snap(-3, 5)).toBe(0);
    expect(snap(104, 5)).toBe(100);
  });
  it('maps positions to values and back', () => {
    expect(fractionToValue(0, 5)).toBe(0);
    expect(fractionToValue(1, 5)).toBe(100);
    expect(fractionToValue(0.333, 5)).toBe(35);
    expect(fractionToValue(2, 5)).toBe(100);
    for (let v = 0; v <= 100; v += 5) expect(fractionToValue(valueToFraction(v), 5)).toBe(v);
  });
  it('count-ups start and end on the exact numbers', () => {
    expect(tween(100, 131, 0)).toBe(100);
    expect(tween(100, 131, 1)).toBe(131);
    expect(tween(100, 131, 0.5)).toBeGreaterThan(100);
  });
});
