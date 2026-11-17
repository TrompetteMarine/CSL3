import { fractionToValue, valueToFraction } from './timeline';

/**
 * A slider drawn by the app, so it looks the same in every browser.
 * - ratings: the handle sits at a pre-drawn start position and is hollow until it is touched;
 * - forecasts: there is no handle at all until the participant places one.
 * The value is written to a hidden input only once the slider has been touched.
 */
export interface SliderHandle {
  readonly name: string;
  value(): number | null;
  touched(): boolean;
  moves(): number;
  firstTouchMs(): number | null;
  placedBy(): 'pointer' | 'key' | null;
  onChange(cb: () => void): void;
}

export function mountSlider(host: HTMLElement, t0: number): SliderHandle {
  const input = host.querySelector<HTMLInputElement>('input[type="hidden"]');
  if (!input) throw new Error('slider without its hidden input');
  const step = Number(host.dataset.step ?? '5');
  const min = 0;
  const max = 100;
  const start = host.dataset.start === undefined || host.dataset.start === '' ? null : Number(host.dataset.start);
  const showValue = host.dataset.showValue === '1';
  const unit = host.dataset.unit ?? '';

  const root = document.createElement('div');
  root.className = 'dm-sl';
  root.tabIndex = 0;
  root.setAttribute('role', 'slider');
  root.setAttribute('aria-valuemin', String(min));
  root.setAttribute('aria-valuemax', String(max));
  root.setAttribute('aria-label', host.dataset.label ?? '');
  root.innerHTML =
    '<div class="dm-sl-track"><div class="dm-sl-fill"></div>' +
    '<div class="dm-sl-ticks"><i></i><i></i><i></i><i></i><i></i></div></div>' +
    '<div class="dm-sl-thumb"><span class="dm-sl-bubble"></span></div>';
  host.appendChild(root);
  const track = root.querySelector<HTMLElement>('.dm-sl-track')!;
  const thumb = root.querySelector<HTMLElement>('.dm-sl-thumb')!;
  const fill = root.querySelector<HTMLElement>('.dm-sl-fill')!;
  const bubble = root.querySelector<HTMLElement>('.dm-sl-bubble')!;

  let current: number | null = start;
  let isTouched = false;
  let nMoves = 0;
  let first: number | null = null;
  let how: 'pointer' | 'key' | null = null;
  const listeners: Array<() => void> = [];

  function render(): void {
    root.classList.toggle('is-unset', current === null);
    root.classList.toggle('is-untouched', current !== null && !isTouched);
    root.classList.toggle('is-set', isTouched);
    if (current === null) {
      root.removeAttribute('aria-valuenow');
      root.setAttribute('aria-valuetext', 'not set');
      return;
    }
    const pct = valueToFraction(current, min, max) * 100;
    thumb.style.left = `${pct}%`;
    fill.style.width = `${pct}%`;
    root.setAttribute('aria-valuenow', String(current));
    root.setAttribute('aria-valuetext', isTouched ? `${current}${unit}` : 'not answered yet');
    bubble.textContent = showValue ? `${current}${unit}` : '';
  }

  function commit(v: number, by: 'pointer' | 'key'): void {
    if (!isTouched) {
      isTouched = true;
      first = Math.round(performance.now() - t0);
      how = by;
    }
    if (v !== current || input!.value === '') nMoves += 1;
    current = v;
    input!.value = String(v);
    render();
    listeners.forEach((cb) => cb());
  }

  function fromPointer(ev: PointerEvent): number {
    const r = track.getBoundingClientRect();
    return fractionToValue((ev.clientX - r.left) / r.width, step, min, max);
  }

  /**
   * Pointer. A mouse or a pen sets the value at once and while it drags. A finger is different,
   * because the same finger scrolls the page (the slider lets the browser scroll up and down):
   * a tap sets the value when the finger lifts where it came down, a sideways drag sets it from
   * its first sideways step on, and every other gesture leaves the slider exactly as it was: one
   * the browser takes for scrolling (pointercancel), and one that moved up or down without
   * scrolling anything (the page was at its end). Nothing is stored for a touch that was not
   * meant for the slider.
   */
  const SLOP = 6;
  const TAP_SLOP = 10;
  let dragging = false;
  let pending: { id: number; x: number; y: number } | null = null;
  const release = (ev: PointerEvent): void => {
    root.classList.remove('is-dragging');
    if (root.hasPointerCapture(ev.pointerId)) root.releasePointerCapture(ev.pointerId);
  };
  root.addEventListener('pointerdown', (ev) => {
    if (ev.button !== 0 && ev.pointerType === 'mouse') return;
    if (ev.pointerType === 'touch') {
      pending = { id: ev.pointerId, x: ev.clientX, y: ev.clientY };
      return;
    }
    dragging = true;
    root.setPointerCapture(ev.pointerId);
    root.classList.add('is-dragging');
    commit(fromPointer(ev), 'pointer');
  });
  root.addEventListener('pointermove', (ev) => {
    if (pending && ev.pointerId === pending.id) {
      const dx = Math.abs(ev.clientX - pending.x);
      if (dx < SLOP || dx < Math.abs(ev.clientY - pending.y)) return;      // not yet a sideways drag
      pending = null;
      dragging = true;
      root.setPointerCapture(ev.pointerId);
      root.classList.add('is-dragging');
    }
    if (dragging) commit(fromPointer(ev), 'pointer');
  });
  root.addEventListener('pointerup', (ev) => {
    if (pending && ev.pointerId === pending.id) {
      const still = Math.hypot(ev.clientX - pending.x, ev.clientY - pending.y) <= TAP_SLOP;
      pending = null;
      if (still) commit(fromPointer(ev), 'pointer');                        // a tap; a finger that wandered sets nothing
      return;
    }
    if (!dragging) return;
    dragging = false;
    release(ev);
  });
  root.addEventListener('pointercancel', (ev) => {
    pending = null;                                                          // the browser scrolled: no value
    if (!dragging) return;
    dragging = false;
    release(ev);
  });

  root.addEventListener('keydown', (ev) => {
    const base = current ?? (min + max) / 2;
    let v: number | null = null;
    switch (ev.key) {
      case 'ArrowLeft': case 'ArrowDown': v = base - step; break;
      case 'ArrowRight': case 'ArrowUp': v = base + step; break;
      case 'PageDown': v = base - 2 * step; break;
      case 'PageUp': v = base + 2 * step; break;
      case 'Home': v = min; break;
      case 'End': v = max; break;
      case ' ': case 'Enter': v = base; break;
      default: return;
    }
    if (current === null && ev.key.startsWith('Arrow')) v = base;   // the first key press places the handle
    ev.preventDefault();
    commit(Math.min(max, Math.max(min, v)), 'key');
  });

  render();
  return {
    name: input.name,
    value: () => (isTouched ? current : null),
    touched: () => isTouched,
    moves: () => nMoves,
    firstTouchMs: () => first,
    placedBy: () => how,
    onChange: (cb) => { listeners.push(cb); },
  };
}

export function mountSliders(root: ParentNode, t0: number): SliderHandle[] {
  return Array.from(root.querySelectorAll<HTMLElement>('[data-slider]')).map((el) => mountSlider(el, t0));
}
