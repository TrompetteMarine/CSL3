"""Builds the pool of real earlier records that the trader board replays (KGi-DISS-I042).

Input: one or more custom exports of the diss_market app (a seed wave run with
board_source='none', or earlier waves). Every finished participant gives one record per
market round: the settlements of the ticket they held. The app then shows
  HIGH board   a rich-round record whose rate lies in the band (engine.HIGH_BAND)
  LOW board    a record of the same round whose count is nearest to the participant's own
(same payout rule as the participant's; node DISS-PEER-REPLAY).

Bot data are refused unless --allow-bots is given; the pool is then marked as a placeholder,
which the app never shows to people in production.

    python experiment/tools/make_board_pool.py seed_wave.csv --out experiment/pools/pool.json
"""
import argparse
import csv
import hashlib
import json
import os
import sys

HIGH_BAND = (0.65, 0.80)          # must equal engine.HIGH_BAND (checked by the tests)
N_MARKET = 6


def build(paths, allow_bots=False):
    streams, sources, bots = [], [], 0
    for path in paths:
        raw = open(path, 'rb').read()
        sources.append(dict(file=os.path.basename(path), sha256=hashlib.sha256(raw).hexdigest()))
        rows = list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
        finished = {r['participant'] for r in rows if r['row_type'] == 'participant' and r['finished'] == '1'}
        for r in rows:
            if r['row_type'] != 'repetition' or r['kind'] != 'market' or r['participant'] not in finished:
                continue
            if r['bot_kind'] != 'human':
                bots += 1
                if not allow_bots:
                    continue
            streams.append(dict(id=f"{r['session']}-{r['participant']}-r{r['repetition']}",
                                round=int(r['repetition']) - 1, bits=r['own_bits'],
                                chose_good=r['chose_good'] == '1', source=r['bot_kind']))
    if bots and not allow_bots:
        print(f'{bots} bot records left out (use --allow-bots for a development placeholder)', file=sys.stderr)
    ks = {len(s['bits']) for s in streams}
    if len(ks) > 1:
        raise SystemExit(f'records of different lengths {sorted(ks)}: one pool per design')
    return dict(version=1, placeholder=any(s['source'] != 'human' for s in streams),
                settlements_per_round=ks.pop() if ks else None, sources=sources, streams=streams)


def report(pool):
    """what the app can draw on: records per round, and how close a LOW match will be"""
    k = pool['settlements_per_round']
    out = dict(records=len(pool['streams']), placeholder=pool['placeholder'], by_round={})
    for r in range(N_MARKET):
        counts = sorted(s['bits'].count('1') for s in pool['streams'] if s['round'] == r)
        out['by_round'][r + 1] = dict(n=len(counts), counts_min_max=[counts[0], counts[-1]] if counts else None)
    rich = [s['bits'].count('1') / k for s in pool['streams'] if s['round'] == 0] if k else []
    out['high_band_records'] = sum(HIGH_BAND[0] <= x <= HIGH_BAND[1] for x in rich)
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('exports', nargs='+')
    ap.add_argument('--out', required=True)
    ap.add_argument('--allow-bots', action='store_true')
    a = ap.parse_args()
    pool = build(a.exports, a.allow_bots)
    if not pool['streams']:
        raise SystemExit('no usable record: nothing written')
    rep = report(pool)
    if rep['high_band_records'] == 0:
        raise SystemExit('no rich-round record in the HIGH band: the HIGH board cannot be filled')
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(pool, open(a.out, 'w'))
    print(json.dumps(rep, indent=1))
