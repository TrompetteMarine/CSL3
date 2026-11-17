import { elapsedMs, field, nextButton, onSubmit, t0 } from '../env';
import { mountSliders } from '../slider';

/** Four sliders; every one must be touched before the page can be left. */
export function rate(): void {
  const btn = nextButton();
  const sliders = mountSliders(document, t0);
  const items = Array.from(document.querySelectorAll<HTMLElement>('.dm-item'));
  const pips = Array.from(document.querySelectorAll<HTMLElement>('[data-left] i'));
  const sync = (): void => {
    const left = sliders.filter((s) => !s.touched()).length;
    if (btn) btn.disabled = left > 0;
    // which items are answered, and how many: marks without a word
    sliders.forEach((s, i) => items[i]?.classList.toggle('is-answered', s.touched()));
    pips.forEach((p, i) => p.classList.toggle('is-on', i < sliders.length - left));
  };
  sliders.forEach((s) => s.onChange(sync));
  sync();
  onSubmit(() => {
    if (sliders.some((s) => !s.touched())) return false;
    field('rate_meta').value = JSON.stringify({
      order: sliders.map((s) => s.name),
      touched: sliders.map((s) => s.touched()),
      moves: sliders.map((s) => s.moves()),
      first_ms: sliders.map((s) => s.firstTouchMs()),
      by: sliders.map((s) => s.placedBy()),
    });
    field('rt_rate_ms').value = String(elapsedMs());
    return true;
  });
}
