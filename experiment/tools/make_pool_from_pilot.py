#!/usr/bin/env python3
"""Build the yoked peer-stream pool from pilot / pool-source custom exports
(delta 7; rewritten in the I032 audit).

Usage: python make_pool_from_pilot.py <out_pool.json> <export.csv> [<export.csv> ...]

The pool is TRUTHFUL by construction: every stream is the per-trial settlement
record of a real participant who consented to re-display, with provenance.

AUDIT changes (records/98_audit_I032.md):
 - per-stream `schedule` ('standard-MODERATE', 'standard-FULL', 'rich') read from
   the export's schedule/restoration columns;
 - per-stream `block_rates` [P1, P2, P3]: the app selects HIGH peers on the rate
   in the CURRENT block window (what is displayed), and LOW peers on the PREVIOUS
   block's rate among same-schedule streams. The old tool exposed only the
   450-trial rate, on which no standard-schedule participant can reach the HIGH
   band (overall ~.44-.50), and the app silently fell back to a deprivation peer;
 - feasibility report: how many streams can serve HIGH in each block, and how
   many LOW candidates each schedule offers. A HIGH P2 board needs rich-schedule
   sources (config 'pool_rich'), because standard-schedule P2 rates are ~.28.
"""
import csv
import json
import statistics as st
import sys

HIGH_BAND = (0.60, 0.70)


def read(export_csv):
    trials, meta = {}, {}
    with open(export_csv) as f:
        for row in csv.DictReader(f):
            if row['row_type'] != 'trial' or row.get('bot_kind', 'human') != 'human':
                continue
            pid = row['participant']
            trials.setdefault(pid, {})[int(row['t'])] = int(row['reward'])
            sched = row.get('schedule') or 'standard'
            meta[pid] = 'rich' if sched == 'rich' else f"standard-{row['restoration']}"
    return trials, meta


def main(out_json, exports):
    streams = []
    for ex in exports:
        trials, meta = read(ex)
        for pid, d in trials.items():
            if len(d) < 450:
                continue                       # completion screen
            earn = [d[t] for t in range(1, 451)]
            rates = [round(sum(earn[b * 150:(b + 1) * 150]) / 150, 4) for b in range(3)]
            bvars = [st.pvariance(earn[i:i + 15]) for i in range(0, 450, 15)]
            streams.append(dict(id=f'pilot-{pid}', schedule=meta[pid], block_rates=rates,
                                blockvar=round(st.mean(bvars), 5), earnings=earn,
                                source=ex, provenance='consented re-display'))
    if not streams:
        sys.exit('no complete human streams')
    order = sorted(range(len(streams)), key=lambda i: streams[i]['blockvar'])
    for rank, i in enumerate(order):
        streams[i]['var_tercile'] = min(2, 3 * rank // len(order))
    with open(out_json, 'w') as f:
        json.dump(dict(placeholder=False, n=len(streams), streams=streams), f)
    print(f'{len(streams)} streams -> {out_json}')
    for b in range(3):
        n_hi = sum(HIGH_BAND[0] <= s['block_rates'][b] <= HIGH_BAND[1] for s in streams)
        print(f'  block {b + 1}: streams usable as HIGH (rate in {HIGH_BAND}): {n_hi}')
    for sch in sorted({s['schedule'] for s in streams}):
        print(f'  schedule {sch}: {sum(s["schedule"] == sch for s in streams)} streams (LOW pool)')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
