#!/usr/bin/env python3
"""run.py — run the characterisation suite against a build of the engine.

    ./run.py --tap ../variants/bug03/chess.tap
    ./run.py --variant ../variants/bug03          # runs `make` first
    ./run.py --tap ... --only movegen,terminal    # groups or id substrings
    ./run.py --tap ... --tier 1                   # rules only, ~30 s
    ./run.py --tap ... -v                         # show every case

Exit codes
    0   everything matched
    1   a TIER 1 (RULE) case failed  -- the build breaks a rule of chess, of
        the documented interface, or of its own save/load round-trip
    2   only TIER 2 (GOLDEN) cases differ -- the build behaves differently
        from the recorded baseline.  That is information, not a verdict:
        after a deliberate change to search or evaluation it is expected.
    3   the suite could not run (harness missing, build missing, crash)

Recording a new baseline (only meaningful on a build you trust):

    ./run.py --tap <pristine>.tap --record

Every golden is captured twice and the two runs must agree, so a value that
is not reproducible never becomes an expectation.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import charlib                                                  # noqa: E402
import cases as cases_mod                                       # noqa: E402

GOLDEN_PATH = os.path.join(HERE, 'golden.json')

PASS, FAIL, DIFF, ERROR, SKIP = 'PASS', 'FAIL', 'DIFF', 'ERROR', 'SKIP'


# --------------------------------------------------------------------------

def run_case(emu, case, golden, record=False):
    """Execute one case.  Returns (status, detail, observed)."""
    kind = case.get('kind', 'state')
    try:
        if kind == 'screen':
            screen = emu.perft_selftest()
            missing = [s for s in case['contains'] if s not in screen]
            if missing:
                return (FAIL, 'self-test screen is missing: %s\n--- screen ---\n%s'
                        % (', '.join(repr(m) for m in missing), screen), None)
            return (PASS, '', {'contains': 'all'})

        if kind == 'saveload':
            saved = os.path.join(emu_tmpdir(), 'saved_%s.tap'
                                 % case['id'].replace('/', '_'))
            a = emu.run(save_tape=saved, **case['steps'][0])
            if not os.path.isfile(saved):
                return (FAIL, 'the engine wrote no tape when G was pressed '
                              '(save is broken, or the key was not accepted)', None)
            blocks = [open(saved, 'rb').read()]
            os.unlink(saved)
            b = emu.run(extra_blocks=blocks, load=True, **case['steps'][1])
            oa = charlib.observe(a, case['observe'])
            ob = charlib.observe(b, case['observe'])
            if oa != ob:
                return (FAIL, 'save/load is not the identity:\n  saved   %s\n'
                              '  reloaded %s' % (oa, ob), {'saved': oa, 'reloaded': ob})
            return (PASS, '', {'saved': oa, 'reloaded': ob})

        # kind == 'state'
        st = None
        for step in case['steps']:
            st = emu.run(**step)
        obs = charlib.observe(st, case['observe'])

    except charlib.EmuError as e:
        return (ERROR, str(e), None)

    if case['tier'] == 1 and 'expect' in case:
        bad = {k: (v, obs.get(k)) for k, v in case['expect'].items()
               if obs.get(k) != v}
        if bad:
            lines = ['  %-14s expected %r, got %r' % (k, v[0], v[1])
                     for k, v in sorted(bad.items())]
            return (FAIL, 'rule violated:\n' + '\n'.join(lines), obs)
        return (PASS, '', obs)

    # tier 2 -- compare with the recorded baseline
    if record:
        return (PASS, '', obs)
    want = golden.get(case['id'])
    if want is None:
        return (SKIP, 'no baseline recorded for this case', obs)
    bad = {k: (v, obs.get(k)) for k, v in want.items() if obs.get(k) != v}
    if bad:
        lines = ['  %-14s baseline %r, now %r' % (k, v[0], v[1])
                 for k, v in sorted(bad.items())]
        return (DIFF, 'behaviour changed:\n' + '\n'.join(lines), obs)
    return (PASS, '', obs)


_TMP = None


def emu_tmpdir():
    global _TMP
    if _TMP is None:
        import tempfile
        _TMP = tempfile.mkdtemp(prefix='charsuite.tapes.')
    return _TMP


# --------------------------------------------------------------------------

def select(all_cases, only, tier):
    out = []
    for c in all_cases:
        if tier and c['tier'] != tier:
            continue
        if only:
            keys = [c['id'], c['group']]
            if not any(any(o in k for k in keys) for o in only):
                continue
        out.append(c)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--tap', help='the chess.tap under test')
    g.add_argument('--variant', help='a variant directory; `make` is run in it '
                                     'and its chess.tap is used')
    ap.add_argument('--harness', help='directory holding build/hc91emu '
                                      '(default: found automatically)')
    ap.add_argument('--only', help='comma separated groups or id substrings')
    ap.add_argument('--tier', type=int, choices=(1, 2),
                    help='run only tier 1 (rules) or tier 2 (goldens)')
    ap.add_argument('--record', action='store_true',
                    help='rewrite golden.json from this build (twice, and the '
                         'two runs must agree)')
    ap.add_argument('--jobs', type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument('-v', '--verbose', action='store_true')
    ap.add_argument('--json', help='write a machine-readable result file here')
    a = ap.parse_args(argv)

    try:
        harness = charlib.find_harness(a.harness)
    except charlib.HarnessNotFound as e:
        sys.stderr.write('%s\n' % e)
        return 3

    tap = a.tap
    if a.variant:
        vd = os.path.abspath(a.variant)
        if not os.path.isdir(vd):
            sys.stderr.write('no such variant directory: %s\n' % vd)
            return 3
        try:
            r = subprocess.run(['make'], cwd=vd, capture_output=True, text=True)
        except OSError as e:
            sys.stderr.write('could not run make in %s: %s\n' % (vd, e))
            return 3
        if r.returncode != 0:
            sys.stderr.write('make failed in %s:\n%s\n%s\n' % (vd, r.stdout[-3000:],
                                                               r.stderr[-3000:]))
            return 3
        tap = os.path.join(vd, 'chess.tap')
    if not os.path.isfile(tap):
        sys.stderr.write('no such build: %s\n' % tap)
        return 3

    try:
        emu = charlib.Emu(harness, tap)
    except charlib.BuildNotFound as e:
        sys.stderr.write('%s\n' % e)
        return 3

    golden = {}
    if os.path.isfile(GOLDEN_PATH):
        with open(GOLDEN_PATH) as f:
            golden = json.load(f)['cases']

    only = [s.strip() for s in a.only.split(',')] if a.only else None
    todo = select(cases_mod.CASES, only, a.tier)
    if not todo:
        sys.stderr.write('no cases selected\n')
        return 3

    print('characterisation suite: %d cases against %s' % (len(todo), tap))
    print('harness: %s' % harness)
    if a.record:
        print('RECORDING a new baseline (each golden is run twice)')
    print('')

    t0 = time.time()
    results = {}

    def work(c):
        st, detail, obs = run_case(emu, c, golden, record=a.record)
        if a.record and c['tier'] == 2 and st == PASS:
            st2, detail2, obs2 = run_case(emu, c, golden, record=True)
            if st2 != PASS:
                st, detail, obs = st2, detail2, obs2
            elif obs != obs2:
                st = ERROR
                detail = ('not reproducible: two identical runs gave\n  %s\n  %s'
                          % (obs, obs2))
        return c, st, detail, obs

    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        for c, st, detail, obs in pool.map(work, todo):
            results[c['id']] = (c, st, detail, obs)

    # -- report ---------------------------------------------------------
    order = {PASS: 0, SKIP: 1, DIFF: 2, FAIL: 3, ERROR: 4}
    bad = [r for r in results.values() if r[1] in (FAIL, DIFF, ERROR)]

    for c in todo:
        cc, st, detail, obs = results[c['id']]
        if st == PASS and not a.verbose:
            continue
        print('%-6s %-34s %s' % (st, c['id'], c['title']))
        if st == FAIL and c.get('rule'):
            print('       rule: %s' % c['rule'])
        if detail:
            for line in detail.splitlines():
                print('       %s' % line)
        if st in (FAIL, DIFF, ERROR):
            print('')

    counts = {}
    for _, st, _, _ in results.values():
        counts[st] = counts.get(st, 0) + 1

    print('')
    print('--- summary (%.0fs) ---' % (time.time() - t0))
    for grp, cs in sorted(cases_mod.groups().items()):
        ids = [c['id'] for c in cs if c['id'] in results]
        if not ids:
            continue
        cnt = {}
        for i in ids:
            s = results[i][1]
            cnt[s] = cnt.get(s, 0) + 1
        print('  %-12s %s' % (grp, '  '.join('%s %d' % (k, v)
                                             for k, v in sorted(cnt.items(),
                                                                key=lambda kv: order[kv[0]]))))
    print('  %-12s %s' % ('TOTAL', '  '.join('%s %d' % (k, v) for k, v in
                                             sorted(counts.items(),
                                                    key=lambda kv: order[kv[0]]))))

    if a.record:
        payload = {
            # Deliberately not the path: a baseline is identified by what it
            # is, not by where the build that produced it happened to live.
            'recorded_from': os.path.basename(tap),
            'recorded_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'note': 'Values recorded from the pristine build. Tier-1 cases '
                    'carry their expectations in cases.py instead.',
            'cases': {c['id']: results[c['id']][3] for c in todo
                      if c['tier'] == 2 and results[c['id']][1] == PASS},
        }
        old = {}
        if os.path.isfile(GOLDEN_PATH):
            old = json.load(open(GOLDEN_PATH))['cases']
        old.update(payload['cases'])
        payload['cases'] = old
        with open(GOLDEN_PATH, 'w') as f:
            json.dump(payload, f, indent=1, sort_keys=True)
            f.write('\n')
        print('\nwrote %s (%d goldens)' % (GOLDEN_PATH, len(old)))
        errs = [c['id'] for c in todo if results[c['id']][1] == ERROR]
        if errs:
            print('NOT recorded (unreproducible or erroring): %s' % ', '.join(errs))
            return 3
        return 0

    if a.json:
        with open(a.json, 'w') as f:
            json.dump({cid: {'status': st, 'tier': c['tier'], 'group': c['group'],
                             'detail': detail, 'observed': obs}
                       for cid, (c, st, detail, obs) in results.items()},
                      f, indent=1, sort_keys=True)
            f.write('\n')

    if any(st in (FAIL, ERROR) for _, st, _, _ in results.values()):
        print('\nTIER 1 FAILURE: the build breaks a rule the suite asserts '
              'independently of the engine. See the rule text above.')
        return 1
    if any(st == DIFF for _, st, _, _ in results.values()):
        print('\nGOLDEN DIFFERENCES ONLY: no rule is broken, but the build no '
              'longer behaves as the recorded baseline did.\nThat is expected '
              'in the area you deliberately changed; anywhere else, it is worth '
              'understanding.')
        return 2
    print('\nall selected cases match.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
