"""The app in a real browser (KGi-DISS-I042 gates G5, G6, G7; KGi-DISS-I043 gates H2, H3; KGi-DISS-I046 gates
G3 and G8 in part, G10, G11, G12): starts 'otree devserver' on a free port in a fresh copy of the project and plays
tools/browser_run.py against it, with the keyboard-only session, the extra window sizes and, where axe-core is
installed (experiment/frontend/node_modules), the accessibility audit. The I046 gates are binding (--strict).
Run from the repository root. Skipped where oTree, Playwright or its browser is missing. Takes about nine minutes
on two cores."""
import os
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


# both display modes of KGi-DISS-I047: the two goods' clearing prices drawn, or the ordered good's only
@pytest.mark.parametrize('config,curves', [('market_e2e_both', 'both'), ('market_e2e_own', 'own')])
@pytest.mark.skipif(OTREE is None or not _browser_ok(), reason='needs oTree and Playwright with Chromium')
def test_browser_run_passes(tmp_path, config, curves):
    proj = tmp_path / 'experiment'
    shutil.copytree(EXP, proj, ignore=shutil.ignore_patterns(
        'node_modules', 'db.sqlite3', '__pycache__', 'botdata', 'analysis', 'frontend', '_generated', '.env'))
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
    env = {k: v for k, v in os.environ.items() if not k.startswith('OTREE_')}
    # in a session of its own: 'otree devserver' runs the server in a child, which outlives a plain terminate()
    server = subprocess.Popen([OTREE, 'devserver', str(port)], cwd=proj, env=env, start_new_session=True,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        base = f'http://127.0.0.1:{port}'
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _ in range(60):
            try:
                opener.open(base + '/demo', timeout=2)
                break
            except Exception:
                time.sleep(0.5)
        else:
            pytest.fail('the development server did not start')
        cmd = [sys.executable, os.path.join(EXP, 'tools', 'browser_run.py'), '--base', base, '--strict', '--keyboard', '--sizes',
               '--config', config, '--curves', curves]
        axe = os.path.join(EXP, 'frontend', 'node_modules', 'axe-core', 'axe.min.js')
        if os.path.exists(axe):
            cmd += ['--axe', axe]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=2700)
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
