import { field, form, nextButton, onSubmit, reducedMotion, vars } from '../env';

/**
 * Consent: the box must be ticked; the browser's display settings are recorded once.
 * If the session asks for a minimum window width, a narrower window cannot start.
 */
export function consent(): void {
  const box = form().querySelector<HTMLInputElement>('input[name="consent"]');
  const btn = nextButton();
  const minWidth = typeof vars.min_width === 'number' ? vars.min_width : 0;
  const notice = document.getElementById('dm-narrow-notice');
  const wideEnough = (): boolean => window.innerWidth >= minWidth;
  const sync = (): void => {
    if (notice) notice.hidden = wideEnough();
    if (btn && box) btn.disabled = !box.checked || !wideEnough();
  };
  window.addEventListener('resize', sync);
  box?.addEventListener('change', sync);
  sync();
  onSubmit(() => {
    field('client_info').value = JSON.stringify({
      w: window.innerWidth,
      h: window.innerHeight,
      dpr: window.devicePixelRatio,
      reduced_motion: reducedMotion,
      touch: navigator.maxTouchPoints > 0,
      ua: navigator.userAgent,
    });
    return !!box?.checked && wideEnough();
  });
}

/** Pages where every radio group must be answered before the button unlocks. */
export function radioGate(optional: readonly string[] = []): void {
  const btn = nextButton();
  const names = Array.from(new Set(
    Array.from(form().querySelectorAll<HTMLInputElement>('input[type="radio"]')).map((r) => r.name),
  )).filter((n) => !optional.includes(n));
  const answered = (): boolean =>
    names.every((n) => form().querySelector<HTMLInputElement>(`input[name="${n}"]:checked`) !== null);
  const sync = (): void => {
    if (btn) btn.disabled = !answered();
  };
  form().addEventListener('change', sync);
  sync();
  onSubmit(() => answered());
}

/** Pages with nothing to check. */
export function plain(): void {
  onSubmit(() => true);
}
