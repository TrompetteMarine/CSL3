"""The words a participant sees, before and after a change of the interface (KGi-DISS-I046, gate G3).

Reads two reports written by `browser_run.py --out` and compares, page by page, the visible text
outside the charts as a bag of words and numbers. Both runs must play the same schedule slots with
the same choices, which browser_run.py does.

    # the tree before the change, served on port 8001; the tree after it on port 8000
    python tools/browser_run.py --base http://localhost:8001 --out before.json
    python tools/browser_run.py --base http://localhost:8000 --out after.json
    python tools/text_before_after.py before.json after.json            # participant A
    python tools/text_before_after.py before.json after.json C          # the phone

The runner of the tree after the change can play the tree before it, as long as the page hooks
are the same. Text that is clipped for screen readers and not shown (the round label on phones)
is counted as seen unless it carries the class dm-sr. The text drawn inside the charts is not in
the reports.
"""
import collections
import json
import sys


def bag(o):
    return collections.Counter(w for s in o.get('seen', []) for w in s.split())


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    before, after = (json.load(open(p))['obs'] for p in sys.argv[1:3])
    tag = sys.argv[3] if len(sys.argv) > 3 else 'A'
    b = [o for o in before[tag] if 'seen' in o]
    a = [o for o in after[tag] if 'seen' in o]
    if [o['label'] for o in b] != [o['label'] for o in a]:
        sys.exit(f'participant {tag}: the two runs did not stop on the same pages')
    same, added, removed = 0, collections.Counter(), collections.Counter()
    where = collections.defaultdict(set)
    for ob, oa in zip(b, a):
        x, y = bag(ob), bag(oa)
        same += x == y
        for w, n in (y - x).items():
            added[w] += n
            where['+' + w].add(oa['label'])
        for w, n in (x - y).items():
            removed[w] += n
            where['-' + w].add(ob['label'])
    print(f'participant {tag}: {len(b)} pages; the same words on {same}')
    for name, words, sign in (('added', added, '+'), ('removed', removed, '-')):
        for w, n in sorted(words.items()):
            print(f'  {name}: {w!r} x{n} on {", ".join(sorted(where[sign + w]))}')
    print(f'  words on all pages: {sum(sum(bag(o).values()) for o in b)} before, {sum(sum(bag(o).values()) for o in a)} after')
    sys.exit(0 if same == len(b) else 1)


if __name__ == '__main__':
    main()
