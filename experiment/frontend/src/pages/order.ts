import { elapsedMs, field, form, nextButton, num, onSubmit, vars } from '../env';
import { MarketChart } from '../svgchart';

/**
 * The goods market, open for orders: the frame of the chart (the cap, the zone under it and what
 * the zone means; no price), a row per good with its button, and the ticket at the foot. A good
 * is chosen on its row; the ticket then names it and its button sends the order.
 */
export function order(): void {
  const btn = nextButton();
  const main = document.querySelector<HTMLElement>('.dm-order');
  const host = document.querySelector<HTMLElement>('[data-chart="frame"]');
  if (host) {
    const text = vars.text as { zone: string };
    new MarketChart(host, {
      k: num('k'), cap: num('cap'), lo: num('price_lo'), hi: num('price_hi'), zoneLabel: text.zone, own: null, other: null, bits: [],
    });
  }
  const radios = Array.from(form().querySelectorAll<HTMLInputElement>('input[name="ticket"]'));
  const named = document.getElementById('dm-ticket-good');
  const sync = (): void => {
    const picked = radios.find((r) => r.checked) ?? null;
    if (btn) btn.disabled = !picked;
    document.querySelector('.dm-goods')?.classList.toggle('has-pick', !!picked);
    // the zone under the cap and the ticket take the chosen good's colour and name
    if (main) {
      if (picked) main.dataset.good = picked.value;
      else delete main.dataset.good;
    }
    if (named) {
      named.hidden = !picked;
      named.querySelectorAll<HTMLElement>('[data-good]').forEach((el) => { el.hidden = !picked || el.dataset.good !== picked.value; });
    }
  };
  radios.forEach((r) => r.addEventListener('change', sync));
  sync();
  onSubmit(() => {
    if (!radios.some((r) => r.checked)) return false;
    field('rt_choose_ms').value = String(elapsedMs());
    return true;
  });
}
