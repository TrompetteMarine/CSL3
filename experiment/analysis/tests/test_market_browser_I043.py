"""The app in a real browser (KGi-DISS-I042 gates G5, G6, G7; KGi-DISS-I043 gates H2, H3; KGi-DISS-I046 gates
G3 and G8 in part, G10, G11, G12; KGi-DISS-I047 gates G3, G5 to G12, G15, G16): starts 'otree devserver' on a free
port in a fresh copy of the project and plays tools/browser_run.py against it, once for each display mode (both
goods' clearing prices drawn, or the ordered good's only), with the session by touch, the keyboard-only session,
the extra window sizes and, where axe-core is installed (experiment/frontend/node_modules), the accessibility
audit. The gates are binding (--strict). Run from the repository root. Skipped where oTree, Playwright or its
browser is missing. Takes about a quarter of an hour per run on two cores.

A third run plays the default display against 'otree prodserver' in production mode, which is what a participant
gets: no debug panel under the page, so the run can measure that a screen which fits is not higher than the window
(KGi-DISS-I047: the framework's empty line after the form made every page a line too high, and a development
server hides that under its debug panel). The three secrets the production settings ask for are random strings made
for the run and are written nowhere.

With MARKET_BROWSER_OUT set to a directory the runs also time and measure one round at the session's real speed
(gates G9 and G14) and leave there, per run, the report (both.json, own.json, production.json), the runner's
output and the screenshots."""
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.abspath(os.path.join(HERE, '..', '..'))
OTREE = shutil.which('otree')


def _browser_ok():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            pw.chromium.launch().close()
        return True
    except Exception:
        return False


# both display modes of KGi-DISS-I047 on a development server (the two goods' clearing prices drawn, or the ordered
# good's only), and the default display on a production server
@pytest.mark.parametrize('config,curves,server_mode', [('market_e2e_both', 'both', 'development'),
                                                      ('market_e2e_own', 'own', 'development'),
                                                      ('market_e2e_both', 'both', 'production')])
@pytest.mark.skipif(OTREE is None or not _browser_ok(), reason='needs oTree and Playwright with Chromium')
def test_browser_run_passes(tmp_path, config, curves, server_mode):
    proj = tmp_path / 'experiment'
    shutil.copytree(EXP, proj, ignore=shutil.ignore_patterns(
        'node_modules', 'db.sqlite3', '__pycache__', 'botdata', 'analysis', 'frontend', '_generated', '.env'))
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
    env = {k: v for k, v in os.environ.items() if not k.startswith('OTREE_')}
    production = server_mode == 'production'
    rest_key = secrets.token_hex(16)
    if production:
        env.update(OTREE_PRODUCTION='1', OTREE_ADMIN_PASSWORD=secrets.token_hex(16), OTREE_SECRET_KEY=secrets.token_hex(32),
                   OTREE_REST_KEY=rest_key)
    # in a session of its own: 'otree devserver' runs the server in a child, which outlives a plain terminate()
    server = subprocess.Popen([OTREE, 'prodserver' if production else 'devserver', str(port)], cwd=proj, env=env,
                              start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    name = 'production' if production else curves
    try:
        base = f'http://127.0.0.1:{port}'
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _ in range(120):
            try:
                opener.open(base + '/demo', timeout=2)
                break
            except Exception:
                time.sleep(0.5)
        else:
            pytest.fail(f'the {server_mode} server did not start')
        cmd = [sys.executable, os.path.join(EXP, 'tools', 'browser_run.py'), '--base', base, '--strict', '--keyboard', '--sizes',
               '--config', config, '--curves', curves]
        axe = os.path.join(EXP, 'frontend', 'node_modules', 'axe-core', 'axe.min.js')
        if os.path.exists(axe):
            cmd += ['--axe', axe]
        keep = os.environ.get('MARKET_BROWSER_OUT')
        if keep:
            os.makedirs(keep, exist_ok=True)
            cmd += ['--out', os.path.join(keep, f'{name}.json'), '--shots', os.path.join(keep, name),
                    '--frames-config', f'market_real_{curves}', '--timing-config', f'market_real_{curves}']
        # the export's key goes to the runner through its environment, not its command line
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3300,
                           env=dict(os.environ, OTREE_REST_KEY=rest_key) if production else None)
        if keep:
            with open(os.path.join(keep, f'{name}.txt'), 'w') as f:
                f.write(r.stdout + '\n--- stderr ---\n' + r.stderr)
        assert r.returncode == 0 and 'BROWSER RUN PASS' in r.stdout, r.stdout[-6000:] + r.stderr[-3000:]
    finally:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(server.pid, sig)
                server.wait(timeout=10)
                break
            except ProcessLookupError:
                break
            except subprocess.TimeoutExpired:
                continue
