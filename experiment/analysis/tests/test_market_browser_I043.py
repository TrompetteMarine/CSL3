"""The app in a real browser (KGi-DISS-I042 gates G5, G6, G7; KGi-DISS-I043 gates H2, H3): starts 'otree devserver' on a
free port in a fresh copy of the project and plays tools/browser_run.py against it.
Run from the repository root. Skipped where oTree, Playwright or its browser is missing."""
import os
import shutil
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


@pytest.mark.skipif(OTREE is None or not _browser_ok(), reason='needs oTree and Playwright with Chromium')
def test_browser_run_passes(tmp_path):
    proj = tmp_path / 'experiment'
    shutil.copytree(EXP, proj, ignore=shutil.ignore_patterns(
        'node_modules', 'db.sqlite3', '__pycache__', 'botdata', 'analysis', 'frontend', '_generated', '.env'))
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
    env = {k: v for k, v in os.environ.items() if not k.startswith('OTREE_')}
    server = subprocess.Popen([OTREE, 'devserver', str(port)], cwd=proj, env=env,
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
        r = subprocess.run([sys.executable, os.path.join(EXP, 'tools', 'browser_run.py'), '--base', base],
                           capture_output=True, text=True, timeout=900)
        assert r.returncode == 0 and 'BROWSER RUN PASS' in r.stdout, r.stdout[-3000:] + r.stderr[-2000:]
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
