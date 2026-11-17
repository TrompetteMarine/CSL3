import { VisibleClock, countUp, elapsedMs, field, form, nextButton, num, onSubmit, reducedMotion, str, t0, vars, wait } from '../env';
import { price2 } from '../chart';
import { mountSliders, type SliderHandle } from '../slider';
import { HistoryChart, TrialStrip } from '../svgchart';
import { dueCount, paidAmong, parseBits, tween } from '../timeline';

/** the market card: price history against the line, with the price under the pointer */
function history(): void {
  const host = document.querySelector<HTMLElement>('[data-chart="history"]');
  if (!host) return;
  const chart = vars.chart as number[];
  const last = document.querySelector<HTMLElement>('[data-last]');
  const rest = last?.textContent ?? '';
  const h = new HistoryChart(host, {
    chart, threshold: num('threshold'), nowLabel: host.dataset.now ?? '', closeLabel: host.dataset.close ?? '',
  });
  h.onHover = (i) => {
    if (last) last.textContent = i === null ? rest : price2(chart[i]!);
  };
}

/** one forecast slider; its value is echoed as a large figure */
function forecast(): SliderHandle {
  const [slider] = mountSliders(document, t0);
  if (!slider) throw new Error('no forecast slider');
  const out = document.querySelector<HTMLElement>('[data-forecast]');
  slider.onChange(() => {
    const v = slider.value();
    if (out && v !== null) {
      out.textContent = `${v}%`;
      out.parentElement?.classList.add('is-set');
    }
  });
  return slider;
}

/** A new market and the first forecast. Neither evidence nor a bet price is on this page. */
export function market(): void {
  const btn = nextButton();
  history();
  const slider = forecast();
  const sync = (): void => {
    if (btn) btn.disabled = !slider.touched();
  };
  slider.onChange(sync);
  sync();
  onSubmit(() => {
    if (!slider.touched()) return false;
    field('rt_pre_ms').value = String(elapsedMs());
    return true;
  });
}

/**
 * The evidence, then the second forecast. A record of trial closes appears close by close; a
 * source's forecast stays on screen for a fixed time. Only then can the forecast be given.
 */
export function evidence(): void {
  const btn = nextButton();
  history();
  const slider = forecast();
  const ask = document.getElementById('dm-ask');
  const total = num('reveal_ms');
  const clock = new VisibleClock();
  const sync = (): void => {
    if (btn) btn.disabled = !(slider.touched() && field('record_done').value === '1');
  };
  slider.onChange(sync);

  const open = async (): Promise<void> => {
    await wait(reducedMotion ? 0 : 400);
    if (ask) {
      ask.hidden = false;
      // on a short screen the question opens below the fold: bring it and the button into view
      const foot = document.querySelector<HTMLElement>('.dm-actions') ?? ask;
      if (foot.getBoundingClientRect().bottom > window.innerHeight) foot.scrollIntoView({ block: 'end', behavior: reducedMotion ? 'auto' : 'smooth' });
    }
    field('record_done').value = '1';
    sync();
  };

  if (str('evidence') === 'record') {
    const host = document.querySelector<HTMLElement>('[data-chart="strip"]');
    if (!host) throw new Error('no record');
    const bits = parseBits(str('shown'));
    const strip = new TrialStrip(host, bits, { above: host.dataset.above ?? '', below: host.dataset.below ?? '' });
    const count = document.querySelector<HTMLElement>('[data-count]');
    const frame = (): void => {
      const n = dueCount(clock.elapsed(), total, strip.length);
      strip.show(n);
      if (count) count.textContent = String(paidAmong(bits, n));
      if (n < strip.length) {
        window.requestAnimationFrame(frame);
        return;
      }
      document.querySelector('.dm-evi')?.classList.add('is-complete');
      const gain = num('gain');
      const pts = document.getElementById('dm-points');
      if (pts && gain > 0) {
        const before = Number(pts.textContent ?? '0');
        countUp(pts, before, before + gain, 600, tween);
      }
      void open();
    };
    window.requestAnimationFrame(frame);
  } else {
    document.querySelector('.dm-evi')?.classList.add('is-in');
    const frame = (): void => {
      if (clock.elapsed() < total) window.requestAnimationFrame(frame);
      else void open();
    };
    window.requestAnimationFrame(frame);
  }
  sync();

  onSubmit(() => {
    if (!slider.touched() || field('record_done').value !== '1') return false;
    field('rt_post_ms').value = String(elapsedMs());
    return true;
  });
}

/** YES, NO or pass. The posted price is on this page for the first time. */
export function bet(): void {
  const btn = nextButton();
  history();
  const radios = Array.from(form().querySelectorAll<HTMLInputElement>('input[name="bet"]'));
  const sync = (): void => {
    const picked = radios.some((r) => r.checked);
    if (btn) btn.disabled = !picked;
    document.querySelector('.dm-bets')?.classList.toggle('has-pick', picked);
  };
  radios.forEach((r) => r.addEventListener('change', sync));
  sync();
  onSubmit(() => {
    if (!radios.some((r) => r.checked)) return false;
    field('rt_bet_ms').value = String(elapsedMs());
    return true;
  });
}
