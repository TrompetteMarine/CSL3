import { VisibleClock, countUp, elapsedMs, field, nextButton, num, onSubmit, reducedMotion, str, t0, wait } from '../env';
import { mountSliders } from '../slider';
import { Tape } from '../tape';
import { dueCount, tween } from '../timeline';

/** First forecast for a ticket never seen before. The record is not on this page. */
export function probePre(): void {
  const btn = nextButton();
  const [slider] = mountSliders(document, t0);
  if (!slider) throw new Error('no forecast slider');
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

/** The record appears settlement by settlement; only then can the second forecast be given. */
export function probePost(): void {
  const btn = nextButton();
  const host = document.querySelector<HTMLElement>('[data-tape="record"]');
  if (!host) throw new Error('no record');
  const shown = str('shown');
  const tape = new Tape(host, shown, shown.length);
  const total = num('reveal_ms');
  const clock = new VisibleClock();
  const ask = document.getElementById('dm-ask');
  const [slider] = mountSliders(document, t0);
  if (!slider) throw new Error('no forecast slider');
  const sync = (): void => {
    if (btn) btn.disabled = !(slider.touched() && field('record_done').value === '1');
  };
  slider.onChange(sync);

  const finish = async (): Promise<void> => {
    await wait(350);
    tape.rest();
    host.classList.add('is-complete');
    const gain = num('gain');
    const pts = document.getElementById('dm-points');
    if (pts && gain > 0) {
      const before = Number(pts.textContent ?? '0');
      countUp(pts, before, before + gain, 600, tween);
    }
    await wait(reducedMotion ? 0 : 450);
    if (ask) ask.hidden = false;
    field('record_done').value = '1';
    sync();
  };

  const frame = (): void => {
    const n = dueCount(clock.elapsed(), total, tape.length);
    tape.show(n);
    if (n < tape.length) window.requestAnimationFrame(frame);
    else void finish();
  };
  window.requestAnimationFrame(frame);
  sync();

  onSubmit(() => {
    if (!slider.touched() || field('record_done').value !== '1') return false;
    field('rt_post_ms').value = String(elapsedMs());
    return true;
  });
}
