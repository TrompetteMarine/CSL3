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

  let dragging = false;
  root.addEventListener('pointerdown', (ev) => {
    if (ev.button !== 0 && ev.pointerType === 'mouse') return;
    dragging = true;
    root.setPointerCapture(ev.pointerId);
    root.classList.add('is-dragging');
    commit(fromPointer(ev), 'pointer');
  });
  root.addEventListener('pointermove', (ev) => {
    if (dragging) commit(fromPointer(ev), 'pointer');
  });
  const end = (ev: PointerEvent): void => {
    if (!dragging) return;
    dragging = false;
    root.classList.remove('is-dragging');
    if (root.hasPointerCapture(ev.pointerId)) root.releasePointerCapture(ev.pointerId);
  };
  root.addEventListener('pointerup', end);
  root.addEventListener('pointercancel', end);

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
