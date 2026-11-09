#!/usr/bin/env python3
"""Build the yoked peer-stream pool from a pilot custom export (delta 7, I032).

Usage: python make_pool_from_pilot.py <pilot_custom_export.csv> <out_pool.json>

The pool is TRUTHFUL by construction: every stream is the per-trial settlement
record of a real pilot participant who consented to re-display (DESIGN.md §4);
provenance metadata is stored per stream and the instructions disclose exactly
this provenance. HIGH streams are usable only when their P2-window realized
rate lies in the session's high_band; selection at run time is stratified on
the within-block variance tercile so HIGH selection is on mean, not volatility.

The dev placeholder in diss_bandit._load_peer_pool is for bots only; the app
refuses a placeholder pool supplied via peer_pool_path.
"""
import csv
import json
import statistics as st
import sys


def main(export_csv, out_json):
    trials = {}
    with open(export_csv) as f:
        for row in csv.DictReader(f):
            if row['row_type'] != 'trial' or row.get('bot_kind', 'human') != 'human':
                continue
            pid = row['participant']
            trials.setdefault(pid, {})[int(row['t'])] = int(row['reward'])
    streams = []
    for pid, d in trials.items():
        if len(d) < 450:
            continue                       # completion screen
        earnings = [d[t] for t in range(1, 451)]
        p2 = earnings[150:300]
        rate_p2 = sum(p2) / len(p2)
        # within-block variance (blocks of 15) for the stratification terciles
        bvars = [st.pvariance(earnings[i:i + 15]) for i in range(0, 450, 15)]
        streams.append(dict(id=f'pilot-{pid}', rate=sum(earnings) / 450.0,
                            rate_p2=round(rate_p2, 4),
                            blockvar=round(st.mean(bvars), 5),
                            earnings=earnings,
                            provenance='pilot participant, consented re-display'))
    if not streams:
        sys.exit('no complete human streams in export')
    # variance terciles for stratified HIGH selection
    order = sorted(range(len(streams)), key=lambda i: streams[i]['blockvar'])
    for rank, i in enumerate(order):
        streams[i]['var_tercile'] = min(2, 3 * rank // len(order))
    pool = dict(placeholder=False, source=export_csv, n=len(streams),
                streams=streams)
    with open(out_json, 'w') as f:
        json.dump(pool, f)
    print(f'{len(streams)} streams -> {out_json}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
