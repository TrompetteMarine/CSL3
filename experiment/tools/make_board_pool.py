"""Builds the pool of real earlier records that the app replays (KGi-DISS-I042, I043): the
trader board of the procurement rounds and the forecast sources of the prediction markets.

Input: one or more custom exports of the diss_market app (a seed wave run with
board_source='none' on a --no-social schedule, or earlier waves).

Board. Every finished participant gives one record per procurement round: the fills of the
good they ordered. The app then shows
  HIGH board   a rich-round record whose rate lies in the band (engine.HIGH_BAND)
  LOW board    a record of the same round whose count is nearest to the participant's own
(same price rule as the participant's; node DISS-PEER-REPLAY).

Sources. Every forecast a finished participant gave after seeing ten trial closes of a market
is a candidate source for that market (identified by its uid: the pilot's schedule must reuse
the seed wave's markets, yoked_schedules.py --markets-from). A source's track record is the
number of the forecaster's OTHER markets in which the second forecast lay on the side the
market closed (above 50 and closed above, or below 50 and closed below). The market the
forecast is shown for is never counted: a record that included it would tell the reader how
that market settles. The app shows a forecast inside the band (engine.SOURCE_BANDS), as near
90 / 10 as the pool allows.

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
SOURCE_BANDS = {True: (80, 100), False: (0, 20)}     # must equal engine.SOURCE_BANDS (checked by the tests)
N_MARKET = 6


def right_side(forecast, above):
    """a forecast on the side the market closed (50 is on neither side)"""
    return (forecast > 50 and above) or (forecast < 50 and not above)


def build(paths, allow_bots=False):
    streams, sources, files, bots = [], [], [], 0
    for path in paths:
        raw = open(path, 'rb').read()
        files.append(dict(file=os.path.basename(path), sha256=hashlib.sha256(raw).hexdigest()))
        rows = list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
        finished = {r['participant'] for r in rows if r['row_type'] == 'participant' and r['finished'] == '1'}
        track = {}
        for r in rows:
            if r['row_type'] == 'repetition' and r['kind'] == 'probe' and r['participant'] in finished:
                track.setdefault(r['participant'], {})[r['market']] = right_side(int(r['forecast_post']), r['market_above'] == '1')
        for r in rows:
            if r['row_type'] != 'repetition' or r['participant'] not in finished:
                continue
            if r['bot_kind'] != 'human':
                bots += 1
                if not allow_bots:
                    continue
            if r['kind'] == 'market':
                streams.append(dict(id=f"{r['session']}-{r['participant']}-r{r['repetition']}",
                                    round=int(r['repetition']) - 1, bits=r['own_bits'],
                                    chose_good=r['chose_good'] == '1', source=r['bot_kind']))
            elif r['kind'] == 'probe' and r['evidence'] == 'record':
                # only a forecast given after the ten trial closes: the description shown with it says so
                others = [v for k, v in track[r['participant']].items() if k != r['market']]
                sources.append(dict(id=f"{r['session']}-{r['participant']}-{r['market']}", market_uid=r['market_uid'],
                                    market=r['market'], favourable=r['probe_favourable'] == '1',
                                    forecast=int(r['forecast_post']), right_others=sum(others), others=len(others),
                                    source=r['bot_kind']))
    if bots and not allow_bots:
        print(f'{bots} bot records left out (use --allow-bots for a development placeholder)', file=sys.stderr)
    ks = {len(s['bits']) for s in streams}
    if len(ks) > 1:
        raise SystemExit(f'records of different lengths {sorted(ks)}: one pool per design')
    return dict(version=2, placeholder=any(s['source'] != 'human' for s in streams + sources),
                settlements_per_round=ks.pop() if ks else None, files=files, streams=streams, sources=sources)


def report(pool):
    """what the app can draw on: records per round, and how close a LOW match will be"""
    k = pool['settlements_per_round']
    out = dict(records=len(pool['streams']), placeholder=pool['placeholder'], by_round={})
    for r in range(N_MARKET):
        counts = sorted(s['bits'].count('1') for s in pool['streams'] if s['round'] == r)
        out['by_round'][r + 1] = dict(n=len(counts), counts_min_max=[counts[0], counts[-1]] if counts else None)
    rich = [s['bits'].count('1') / k for s in pool['streams'] if s['round'] == 0] if k else []
    out['high_band_records'] = sum(HIGH_BAND[0] <= x <= HIGH_BAND[1] for x in rich)
    out['sources'] = {}
    for uid in sorted({x['market_uid'] for x in pool['sources']}):
        xs = [x for x in pool['sources'] if x['market_uid'] == uid]
        lo, hi = SOURCE_BANDS[xs[0]['favourable']]
        band = [x for x in xs if lo <= x['forecast'] <= hi]
        out['sources'][uid] = dict(market=xs[0]['market'], favourable=xs[0]['favourable'], forecasts=len(xs),
                                   in_band=len(band), best_track_in_band=max((x['right_others'] for x in band), default=None))
    out['markets_without_a_usable_source'] = [v['market'] for v in out['sources'].values() if v['in_band'] == 0]
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
    if not rep['sources'] or rep['markets_without_a_usable_source']:
        print('this pool cannot fill a forecast source for every market: it serves a session whose schedule '
              'was drawn with --no-social only', file=sys.stderr)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(pool, open(a.out, 'w'))
    print(json.dumps(rep, indent=1))
