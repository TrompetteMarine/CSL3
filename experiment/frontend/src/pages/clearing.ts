import { VisibleClock, countUp, elapsedMs, field, nextButton, num, onSubmit, reducedMotion, str, vars, wait } from '../env';
import { basketsOf, cumulative, price2 } from '../chart';
import { FillsChart, MarketChart } from '../svgchart';
import { dueCount, dueCountStepped, parseBits, tween } from '../timeline';

const PAUSE_MS = 500;
const STEPS_REDUCED = 12;

interface Text {
  done: string;
  gain: string;
  zone: string;
  you: string;
  trader: string;
  clearing: string;
  filled: string;
  not_filled: string;
  names: Record<string, string>;
}

function all(sel: string): HTMLElement[] {
  return Array.from(document.querySelectorAll<HTMLElement>(sel));
}

/**
 * The goods market runs: the clearing prices come in clearing by clearing, at a constant pace
 * over reveal_ms, and the running counts of filled orders (own and trader) grow with them. The
 * ordered good's prices are always drawn; the other good's are drawn when the server sent them.
 * Identical in both arms; the points total moves only once the round has cleared.
 */
export function clearing(): void {
  const btn = nextButton();
  const text = vars.text as Text;
  const ticket = str('ticket');
  const own = parseBits(str('own'));
  const board = typeof vars.board === 'string' ? parseBits(vars.board) : null;
  const prices = vars.prices as number[];
  const otherTicket = typeof vars.other_ticket === 'string' ? vars.other_ticket : null;
  const otherPrices = Array.isArray(vars.other_prices) ? (vars.other_prices as number[]) : null;
  const k = own.length;
  if (!Array.isArray(prices) || prices.length !== k || (board && board.length !== k)) throw new Error('the round is incomplete');
  if ((otherTicket === null) !== (otherPrices === null) || (otherPrices && otherPrices.length !== k)) throw new Error('the other good is incomplete');
  const priceHost = document.querySelector<HTMLElement>('[data-chart="price"]');
  const fillsHost = document.querySelector<HTMLElement>('[data-chart="fills"]');
  if (!priceHost || !fillsHost) throw new Error('the clearing page has no charts');

  const price = new MarketChart(priceHost, {
    k, cap: num('cap'), lo: num('price_lo'), hi: num('price_hi'), zoneLabel: text.zone, bits: own,
    own: { ticket, prices }, other: otherTicket && otherPrices ? { ticket: otherTicket, prices: otherPrices } : null,
  });
  const fills = new FillsChart(fillsHost, { own, board, ownLabel: text.you, boardLabel: text.trader });
  const ownCum = cumulative(own);
  const boardCum = board ? cumulative(board) : null;

  const seen = all('[data-seen]');
  const priceNow = document.querySelector<HTMLElement>(`[data-price="${ticket}"]`);
  const priceOther = otherTicket ? document.querySelector<HTMLElement>(`[data-price="${otherTicket}"]`) : null;
  const ownCount = document.querySelector<HTMLElement>('[data-count="own"]');
  const boardCount = document.querySelector<HTMLElement>('[data-count="board"]');
  const basketCount = document.querySelector<HTMLElement>('[data-baskets]');
  const pips = all('[data-pips] i');
  const goodsBefore = num('goods_before');
  const size = num('basket_size');

  let shown = -1;
  const paint = (n: number): void => {
    if (n === shown) return;
    shown = n;
    price.show(n);
    fills.show(n);
    seen.forEach((el) => { el.textContent = String(n); });
    if (priceNow && n > 0) priceNow.textContent = price2(prices[n - 1]!);
    if (priceOther && otherPrices && n > 0) priceOther.textContent = price2(otherPrices[n - 1]!);
    if (ownCount) ownCount.textContent = String(ownCum[n]!);
    if (boardCount && boardCum) boardCount.textContent = String(boardCum[n]!);
    const [full, part] = basketsOf(goodsBefore + ownCum[n]!, size);
    if (basketCount) basketCount.textContent = String(full);
    pips.forEach((p, i) => p.classList.toggle('is-on', i < part));
  };
  paint(0);

  // the clearing under the pointer or the finger, once the round has cleared: named in the line above the chart
  const readout = document.getElementById('dm-readout');
  const point = (i: number | null): void => {
    price.mark(i);
    fills.mark(i);
    if (!readout) return;
    readout.parentElement?.classList.toggle('is-reading', i !== null);       // the heading gives its place to the reading
    if (i === null) {
      readout.replaceChildren();
      return;
    }
    // with two price lines each price is named by its good; with one, the price stands alone as before
    const mine = `${price2(prices[i]!)}, ${own[i] ? text.filled : text.not_filled}`;
    const bits = [`${text.clearing} ${i + 1}`, otherTicket ? `${text.names[ticket] ?? ticket} ${mine}` : mine];
    if (otherTicket && otherPrices) bits.push(`${text.names[otherTicket] ?? otherTicket} ${price2(otherPrices[i]!)}`);
    bits.push(`${text.you} ${ownCum[i + 1]!}`);
    if (boardCum) bits.push(`${text.trader} ${boardCum[i + 1]!}`);
    readout.replaceChildren(...bits.map((b) => {
      const part = document.createElement('span');
      part.textContent = b;
      return part;
    }));
  };
  price.onHover = point;
  fills.onHover = point;

  const total = num('reveal_ms');
  const clock = new VisibleClock();
  let revealEnd = 0;
  let scrolled = 0;
  const finish = async (): Promise<void> => {
    revealEnd = clock.elapsed();
    await wait(PAUSE_MS);
    price.rest();
    fills.rest();
    document.querySelector('.dm-clearing')?.classList.add('is-cleared');
    const title = document.getElementById('dm-clear-title');
    if (title) title.textContent = text.done;
    const gain = document.getElementById('dm-gain');
    if (gain) {
      gain.textContent = text.gain;
      gain.hidden = false;
    }
    const pts = document.getElementById('dm-points');
    const before = num('points_before');
    if (pts) countUp(pts, before, before + ownCum[k]!, 700, tween);
    const shell = document.querySelector<HTMLElement>('.dm');
    field('settle_done').value = '1';
    field('settle_meta').value = JSON.stringify({
      planned_ms: total,
      reveal_ms: Math.round(revealEnd),               // visible time until the last clearing appeared
      total_ms: Math.round(clock.elapsed()),          // … until the button was unlocked
      hidden_ms: Math.round(clock.hiddenMs),
      reduced_motion: reducedMotion,
      curves: otherPrices ? 2 : 1,                    // price lines drawn
      vw: window.innerWidth,                          // the window while the round ran
      vh: window.innerHeight,
      fit: shell ? shell.getBoundingClientRect().bottom + window.scrollY <= window.innerHeight + 1 : null,   // the whole screen was in view without scrolling
      scrolled: Math.round(scrolled),                 // how far the page was scrolled at most during the reveal
    });
    if (btn) btn.disabled = false;
  };

  const frame = (): void => {
    const e = clock.elapsed();
    const n = reducedMotion ? dueCountStepped(e, total, k, STEPS_REDUCED) : dueCount(e, total, k);
    if (window.scrollY > scrolled) scrolled = window.scrollY;
    paint(n);
    if (n < k) window.requestAnimationFrame(frame);
    else void finish();
  };
  window.requestAnimationFrame(frame);

  onSubmit(() => {
    if (field('settle_done').value !== '1') return false;
    field('rt_settle_ms').value = String(elapsedMs());
    return true;
  });
}
