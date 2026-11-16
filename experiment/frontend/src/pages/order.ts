import { elapsedMs, field, form, nextButton, onSubmit } from '../env';

/** Two goods (radio inputs). The button unlocks once one is ordered. */
export function order(): void {
  const btn = nextButton();
  const radios = Array.from(form().querySelectorAll<HTMLInputElement>('input[name="ticket"]'));
  const sync = (): void => {
    const picked = radios.some((r) => r.checked);
    if (btn) btn.disabled = !picked;
    document.querySelector('.dm-goods')?.classList.toggle('has-pick', picked);
  };
  radios.forEach((r) => r.addEventListener('change', sync));
  sync();
  onSubmit(() => {
    if (!radios.some((r) => r.checked)) return false;
    field('rt_choose_ms').value = String(elapsedMs());
    return true;
  });
}
