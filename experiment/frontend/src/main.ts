import './styles/fonts.css';
import './styles/app.css';
import { vars } from './env';
import { mountGlyphs } from './glyphs';
import { clearing } from './pages/clearing';
import { bet, evidence, market } from './pages/market';
import { consent, plain, radioGate } from './pages/misc';
import { order } from './pages/order';
import { rate } from './pages/rate';

/**
 * Entry point of the diss_market front end. Each oTree page names itself in js_vars.page;
 * the browser displays what the server sent and never computes an outcome.
 */
const PAGES: Record<string, () => void> = {
  consent,
  instructions: plain,
  quiz: () => radioGate(),
  noslot: () => undefined,
  order,
  clearing,
  rate,
  market,
  evidence,
  bet,
  recall: () => radioGate(),
  closing: () => radioGate(['peer_success', 'peer_real', 'rig_suspicion', 'betting_familiarity']),
  results: () => undefined,
};

function start(): void {
  document.documentElement.classList.add('dm-js');
  // the framework's page declares neither a language nor a title
  if (!document.documentElement.lang) document.documentElement.lang = 'en';
  const brand = document.querySelector('.dm-brand')?.textContent?.trim();
  if (brand && !document.title.trim()) document.title = brand;
  mountGlyphs();
  const run = PAGES[vars.page];
  if (!run) throw new Error(`unknown page: ${vars.page}`);
  run();
  document.documentElement.classList.add('dm-ready');
}

start();
