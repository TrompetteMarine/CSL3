import { VisibleClock, countUp, elapsedMs, field, nextButton, num, onSubmit, reducedMotion, str, vars, wait } from '../env';
import { Tape } from '../tape';
import { dueCount, dueCountStepped, tween } from '../timeline';

const PAUSE_MS = 450;
const REGROUP_MS = 900;
const STEPS_REDUCED = 12;

/**
 * The round settles: own ticket and trader board are revealed in step, at a constant pace,
 * over reveal_ms; then both regroup into a proportion block. Identical in both arms.
 */
export function settle(): void {
  const btn = nextButton();
  const tapes: Tape[] = [];
  const own = document.querySelector<HTMLElement>('[data-tape="own"]');
  if (!own) throw new Error('no tape for the own ticket');
  // narrow screens: ten columns, so that own ticket and board fit side by side
  const k0 = str('own').length;
  const cols = window.matchMedia('(max-width: 720px)').matches && k0 % 10 === 0 ? 10 : undefined;
  tapes.push(new Tape(own, str('own'), cols));
  const boardEl = document.querySelector<HTMLElement>('[data-tape="board"]');
  if (boardEl && typeof vars.board === 'string') tapes.push(new Tape(boardEl, vars.board, cols));

  const total = num('reveal_ms');
  const k = tapes[0]!.length;
  const clock = new VisibleClock();
  const text = vars.text as { done: string; gain: string };

  let revealEnd = 0;
  const finish = async (): Promise<void> => {
    revealEnd = clock.elapsed();
    await wait(PAUSE_MS);
    await Promise.all(tapes.map((t) => t.regroup(REGROUP_MS, !reducedMotion)));
    document.querySelector('.dm-settle')?.classList.add('is-settled');
    const title = document.getElementById('dm-settle-title');
    if (title) title.textContent = text.done;
    const gain = document.getElementById('dm-gain');
    if (gain) {
      gain.textContent = text.gain;
      gain.hidden = false;
    }
    const pts = document.getElementById('dm-points');
    const before = num('points_before');
    if (pts) countUp(pts, before, before + tapes[0]!.bits.filter(Boolean).length, 700, tween);
    field('settle_done').value = '1';
    field('settle_meta').value = JSON.stringify({
      planned_ms: total,
      reveal_ms: Math.round(revealEnd),               // visible time until the last settlement appeared
      total_ms: Math.round(clock.elapsed()),          // … until the button was unlocked
      hidden_ms: Math.round(clock.hiddenMs),
      reduced_motion: reducedMotion,
    });
    if (btn) btn.disabled = false;
  };

  const frame = (): void => {
    const e = clock.elapsed();
    const n = reducedMotion ? dueCountStepped(e, total, k, STEPS_REDUCED) : dueCount(e, total, k);
    tapes.forEach((t) => t.show(n));
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
