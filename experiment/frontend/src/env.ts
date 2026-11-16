/** What every page shares: the values the server passed, the form, the page clock. */
export interface JsVars {
  page: string;
  [key: string]: unknown;
}

declare global {
  interface Window {
    js_vars?: JsVars;
  }
}

export const vars: JsVars = window.js_vars ?? { page: 'unknown' };
export const t0 = performance.now();
export const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

export function form(): HTMLFormElement {
  const f = document.getElementById('form');
  if (!(f instanceof HTMLFormElement)) throw new Error('the page has no form');
  return f;
}

export function field(name: string): HTMLInputElement {
  const el = form().elements.namedItem(name);
  if (!(el instanceof HTMLInputElement)) throw new Error(`no input named ${name}`);
  return el;
}

export function nextButton(): HTMLButtonElement | null {
  return document.querySelector<HTMLButtonElement>('#dm-next');
}

export function elapsedMs(): number {
  return Math.round(performance.now() - t0);
}

export function str(key: string): string {
  const v = vars[key];
  if (typeof v !== 'string') throw new Error(`the server did not send "${key}"`);
  return v;
}

export function num(key: string): number {
  const v = vars[key];
  if (typeof v !== 'number') throw new Error(`the server did not send "${key}"`);
  return v;
}

export function wait(ms: number): Promise<void> {
  return new Promise((res) => window.setTimeout(res, ms));
}

/**
 * Runs `before` when the form is submitted; a false return blocks the submission.
 * A second submission of the same page is ignored (double clicks).
 */
export function onSubmit(before: () => boolean | void): void {
  let sent = false;
  form().addEventListener('submit', (ev) => {
    if (sent) {
      ev.preventDefault();
      return;
    }
    if (before() === false) {
      ev.preventDefault();
      return;
    }
    sent = true;
    document.documentElement.classList.add('dm-leaving');
    const b = nextButton();
    if (b) b.setAttribute('aria-busy', 'true');
  });
}

/** a clock that stands still while the tab is hidden, so a reveal is always seen in full */
export class VisibleClock {
  private acc = 0;
  private since: number | null;
  private hiddenAt: number | null = null;
  hiddenMs = 0;

  constructor() {
    this.since = document.hidden ? null : performance.now();
    if (document.hidden) this.hiddenAt = performance.now();
    document.addEventListener('visibilitychange', () => {
      const now = performance.now();
      if (document.hidden) {
        if (this.since !== null) this.acc += now - this.since;
        this.since = null;
        this.hiddenAt = now;
      } else {
        if (this.hiddenAt !== null) this.hiddenMs += now - this.hiddenAt;
        this.hiddenAt = null;
        this.since = now;
      }
    });
  }

  elapsed(): number {
    return this.acc + (this.since === null ? 0 : performance.now() - this.since);
  }
}

/** count a number on screen from a to b */
export function countUp(el: HTMLElement, a: number, b: number, ms: number, tween: (a: number, b: number, p: number) => number): void {
  if (a === b || reducedMotion) {
    el.textContent = String(b);
    return;
  }
  const start = performance.now();
  const step = (): void => {
    const p = (performance.now() - start) / ms;
    el.textContent = String(tween(a, b, p));
    if (p < 1) window.requestAnimationFrame(step);
  };
  window.requestAnimationFrame(step);
}
