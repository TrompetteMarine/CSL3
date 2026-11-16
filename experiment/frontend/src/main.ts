import './styles/fonts.css';
import './styles/app.css';
import { vars } from './env';
import { mountGlyphs } from './glyphs';
import { choose } from './pages/choose';
import { consent, plain, radioGate } from './pages/misc';
import { probePost, probePre } from './pages/probe';
import { rate } from './pages/rate';
import { settle } from './pages/settle';

/**
 * Entry point of the diss_market front end. Each oTree page names itself in js_vars.page;
 * the browser displays what the server sent and never computes an outcome.
 */
const PAGES: Record<string, () => void> = {
  consent,
  instructions: plain,
  quiz: () => radioGate(),
  noslot: () => undefined,
  choose,
  settle,
  rate,
  probe_pre: probePre,
  probe_post: probePost,
  probe_recall: () => radioGate(),
  closing: () => radioGate(['peer_success', 'peer_real', 'rig_suspicion', 'betting_familiarity']),
  results: () => undefined,
};

function start(): void {
  document.documentElement.classList.add('dm-js');
  mountGlyphs();
  const run = PAGES[vars.page];
  if (!run) throw new Error(`unknown page: ${vars.page}`);
  run();
  document.documentElement.classList.add('dm-ready');
}

start();
