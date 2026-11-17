import { VisibleClock, countUp, elapsedMs, field, nextButton, num, onSubmit, reducedMotion, str, vars, wait } from '../env';
import { basketsOf, cumulative, price2 } from '../chart';
import { FillsChart, PriceChart } from '../svgchart';
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
}

function all(sel: string): HTMLElement[] {
  return Array.from(document.querySelectorAll<HTMLElement>(sel));
}

/**
 * The goods market clears: the price of the ordered good comes in clearing by clearing, at a
 * constant pace over reveal_ms, and the running counts of filled orders (own and trader) grow
 * with it. Identical in both arms; the points total moves only once the round has cleared.
 */
export function clearing(): void {
  const btn = nextButton();
  const text = vars.text as Text;
  const own = parseBits(str('own'));
  const board = typeof vars.board === 'string' ? parseBits(vars.board) : null;
  const prices = vars.prices as number[];
  const k = own.length;
  if (!Array.isArray(prices) || prices.length !== k || (board && board.length !== k)) throw new Error('the round is incomplete');
  const priceHost = document.querySelector<HTMLElement>('[data-chart="price"]');
  const fillsHost = document.querySelector<HTMLElement>('[data-chart="fills"]');
  if (!priceHost || !fillsHost) throw new Error('the clearing page has no charts');

  const price = new PriceChart(priceHost, {
    prices, bits: own, cap: num('cap'), lo: num('price_lo'), hi: num('price_hi'), zoneLabel: text.zone,
  });
  const fills = new FillsChart(fillsHost, { own, board, ownLabel: text.you, boardLabel: text.trader });
  const ownCum = cumulative(own);
  const boardCum = board ? cumulative(board) : null;

  const seen = all('[data-seen]');
  const priceNow = document.querySelector<HTMLElement>('[data-price]');
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
    if (ownCount) ownCount.textContent = String(ownCum[n]!);
    if (boardCount && boardCum) boardCount.textContent = String(boardCum[n]!);
    const [full, part] = basketsOf(goodsBefore + ownCum[n]!, size);
    if (basketCount) basketCount.textContent = String(full);
    pips.forEach((p, i) => p.classList.toggle('is-on', i < part));
  };
  paint(0);

  const readout = document.getElementById('dm-readout');
  const point = (i: number | null): void => {
    price.mark(i);
    fills.mark(i);
    if (!readout) return;
    if (i === null) {
      readout.replaceChildren();
      return;
    }
    const bits = [`${text.clearing} ${i + 1}`, `${price2(prices[i]!)}, ${own[i] ? text.filled : text.not_filled}`,
      `${text.you} ${ownCum[i + 1]!}`];
    if (boardCum) bits.push(`${text.trader} ${boardCum[i + 1]!}`);
    readout.replaceChildren(...bits.map((b) => {
      const row = document.createElement('span');
      row.textContent = b;
      return row;
    }));
    // beside the clearing it describes and never over it: to its right, or to its left where the right has no room
    const frame = readout.offsetParent instanceof HTMLElement ? readout.offsetParent.clientWidth : window.innerWidth;
    const width = readout.offsetWidth;
    const at = priceHost.offsetLeft + price.xOf(i);
    const gap = 14;
    const left = at + gap + width <= frame ? at + gap : at - gap - width;
    readout.style.left = `${Math.max(0, left)}px`;
    readout.style.top = `${priceHost.offsetTop + 2}px`;
  };
  price.onHover = point;
  fills.onHover = point;

  const total = num('reveal_ms');
  const clock = new VisibleClock();
  let revealEnd = 0;
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
    field('settle_done').value = '1';
    field('settle_meta').value = JSON.stringify({
      planned_ms: total,
      reveal_ms: Math.round(revealEnd),               // visible time until the last clearing appeared
      total_ms: Math.round(clock.elapsed()),          // … until the button was unlocked
      hidden_ms: Math.round(clock.hiddenMs),
      reduced_motion: reducedMotion,
    });
    if (btn) btn.disabled = false;
  };

  const frame = (): void => {
    const e = clock.elapsed();
    const n = reducedMotion ? dueCountStepped(e, total, k, STEPS_REDUCED) : dueCount(e, total, k);
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
