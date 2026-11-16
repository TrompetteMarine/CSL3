/** Ticket symbols. One 24 x 24 box each, drawn in the current text colour. */
const SHAPES: Record<string, string> = {
  SQUARE: '<rect x="4" y="4" width="16" height="16" rx="1.5"/>',
  TRIANGLE: '<path d="M12 3.6 21 19.6H3z"/>',
  CIRCLE: '<circle cx="12" cy="12" r="8.6"/>',
  DIAMOND: '<path d="M12 2.6 21.4 12 12 21.4 2.6 12z"/>',
  HEXAGON: '<path d="M12 2.8 20.2 7.4v9.2L12 21.2 3.8 16.6V7.4z"/>',
  STAR: '<path d="m12 2.6 2.75 6.1 6.65.7-4.97 4.47 1.4 6.53L12 17.06 6.17 20.4l1.4-6.53L2.6 9.4l6.65-.7z"/>',
  CROSS: '<path d="M9 3.4h6V9h5.6v6H15v5.6H9V15H3.4V9H9z"/>',
  PENTAGON: '<path d="M12 2.8 21.2 9.5l-3.5 10.9H6.3L2.8 9.5z"/>',
};

export function glyphSvg(name: string): string {
  const shape = SHAPES[name];
  if (!shape) throw new Error(`unknown ticket symbol: ${name}`);
  return (
    '<svg class="dm-glyph-svg" viewBox="0 0 24 24" aria-hidden="true" focusable="false" ' +
    `fill="currentColor" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round">${shape}</svg>`
  );
}

/** fills every element carrying data-glyph="NAME" */
export function mountGlyphs(root: ParentNode = document): void {
  root.querySelectorAll<HTMLElement>('[data-glyph]').forEach((el) => {
    const name = el.dataset.glyph;
    if (name && !el.firstChild) el.innerHTML = glyphSvg(name);
  });
}
