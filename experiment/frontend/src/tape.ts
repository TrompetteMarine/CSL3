import { gridCols, paidAmong, parseBits, regroupOrder } from './timeline';

/**
 * A settlement tape: one cell per settlement, revealed in order, then regrouped (paid first)
 * so the block reads as a proportion. Paid and not paid differ by shape: a filled disc
 * against a hollow ring.
 */
export class Tape {
  readonly bits: boolean[];
  private readonly cells: HTMLElement[] = [];
  private readonly grid: HTMLElement;
  private readonly count: HTMLElement | null;
  private readonly seen: HTMLElement | null;
  private shown = 0;

  constructor(private readonly host: HTMLElement, bits: string, cols?: number) {
    this.bits = parseBits(bits);
    const grid = host.querySelector<HTMLElement>('[data-grid]');
    if (!grid) throw new Error('tape without a grid');
    this.grid = grid;
    this.count = host.querySelector<HTMLElement>('[data-count]');
    this.seen = host.querySelector<HTMLElement>('[data-seen]');
    this.grid.style.setProperty('--dm-cols', String(cols ?? gridCols(this.bits.length)));
    const frag = document.createDocumentFragment();
    this.bits.forEach((paid) => {
      const c = document.createElement('i');
      c.className = `dm-cell ${paid ? 'is-paid' : 'is-unpaid'}`;
      this.cells.push(c);
      frag.appendChild(c);
    });
    this.grid.appendChild(frag);
    this.writeCounts();
  }

  get length(): number {
    return this.bits.length;
  }

  /** make the first n settlements visible (never hides one again) */
  show(n: number): void {
    const upto = Math.min(n, this.cells.length);
    if (upto <= this.shown) return;
    for (let i = this.shown; i < upto; i++) this.cells[i]!.classList.add('is-on');
    this.cells[upto - 1]!.classList.add('is-head');
    if (this.shown > 0) this.cells[this.shown - 1]!.classList.remove('is-head');
    this.shown = upto;
    this.writeCounts();
  }

  /** the reveal is over: no cell is the newest one any more */
  rest(): void {
    this.cells.forEach((c) => c.classList.remove('is-head'));
  }

  private writeCounts(): void {
    if (this.count) this.count.textContent = String(paidAmong(this.bits, this.shown));
    if (this.seen) this.seen.textContent = String(this.shown);
  }

  /** paid cells move to the front; resolves when the move is over */
  regroup(ms: number, animate: boolean): Promise<void> {
    this.cells[this.shown - 1]?.classList.remove('is-head');
    const order = regroupOrder(this.bits);
    const before = this.cells.map((c) => c.getBoundingClientRect());
    order.forEach((from) => this.grid.appendChild(this.cells[from]!));
    this.host.classList.add('is-grouped');
    if (!animate) return new Promise((res) => window.setTimeout(res, ms));
    const moves: Animation[] = [];
    order.forEach((from, to) => {
      const cell = this.cells[from]!;
      const a = before[from]!;
      const b = cell.getBoundingClientRect();
      const dx = a.left - b.left;
      const dy = a.top - b.top;
      if (dx === 0 && dy === 0) return;
      moves.push(cell.animate(
        [{ transform: `translate(${dx}px, ${dy}px)` }, { transform: 'translate(0, 0)' }],
        { duration: ms * 0.75, delay: (to / order.length) * ms * 0.25, easing: 'cubic-bezier(.5,0,.2,1)', fill: 'backwards' },
      ));
    });
    return Promise.all(moves.map((m) => m.finished.catch(() => undefined))).then(() => undefined);
  }
}
