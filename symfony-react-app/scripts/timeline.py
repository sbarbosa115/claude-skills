#!/usr/bin/env python3
"""Time each step of a feature, and write the table into its PRD (steps/00-overview.md, steps/11-pr-and-teardown.md).

Run from anywhere inside the project's git checkout (any worktree: the log is shared through the git directory):

    timeline.py start <step> [--feature=<name>] [--at="YYYY-MM-DD HH:MM"] [--note="…"]   # a step begins (ends the one open)
    timeline.py pause  [--feature=<name>] [--note="…"]      # the work stops (the user paused it, waiting on the user)
    timeline.py resume [--feature=<name>]
    timeline.py end    [--feature=<name>]                   # the last step ends
    timeline.py show   [--feature=<name>]                   # print the table
    timeline.py report <prd> [--feature=<name>]             # write it into the PRD under "## Timeline" (replaced if there)

The feature defaults to the current branch's (feature/<name>, or the base of a split item); on main, give --feature.
Steps: plan, split, branch, contract, build, merge, barrier, gate, tests, audit, verify, regression, finish, dod, pr
(another name is accepted). A step started again later (a gate re-run after a fix) adds to its time.

Each step shows its active time (pauses taken out) and its wall-clock time. For a split, each item gets a row too,
from git: the branch's creation to the commit that merged it into the base branch.
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

ORDER = ['plan', 'split', 'branch', 'contract', 'build', 'merge', 'barrier', 'gate', 'tests', 'audit', 'verify',
         'regression', 'finish', 'dod', 'pr']
LABELS = {'plan': 'Plan', 'split': 'Split table', 'branch': 'Branch and stack', 'contract': 'Item 0 (contract)',
          'build': 'Build test-first', 'merge': 'Merging the items', 'barrier': 'Barrier (waiting for the items)',
          'gate': 'Gate', 'tests': 'Full PHPUnit + Vitest', 'audit': 'Security audit', 'verify': 'Verify in the browser',
          'regression': 'Regression run (smoke, then manual)', 'finish': 'Finish (docs, CI)', 'dod': 'Definition of done',
          'pr': 'Pull request'}


def git(*args: str, check: bool = True) -> str:
    res = subprocess.run(['git', *args], capture_output=True, text=True)
    if check and res.returncode:
        raise SystemExit(f'timeline.py: git {" ".join(args)}: {res.stderr.strip()}')
    return res.stdout.strip()


def opt(name: str) -> str | None:
    return next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith(f'--{name}=')), None)


def feature() -> str:
    if f := opt('feature'):
        return f.removeprefix('feature/')
    branch = git('rev-parse', '--abbrev-ref', 'HEAD')
    branch = git('config', f'branch.{branch}.splitBase', check=False) or branch
    if not branch.startswith('feature/'):
        raise SystemExit(f'timeline.py: on {branch}: give --feature=<name>')
    return branch.removeprefix('feature/')


def log_file(name: str) -> Path:
    common = Path(git('rev-parse', '--path-format=absolute', '--git-common-dir'))
    path = common / 'feature-timeline' / f'{name}.tsv'
    path.parent.mkdir(exist_ok=True)
    return path


def read(path: Path) -> list[tuple[datetime, str, str]]:
    rows = []
    for line in path.read_text().splitlines() if path.exists() else []:
        when, event, step, *_ = line.split('\t') + ['', '']
        rows.append((datetime.fromisoformat(when), event, step))
    return sorted(rows, key=lambda r: r[0])


def fmt(d: timedelta) -> str:
    minutes = round(d.total_seconds() / 60)
    days, minutes = divmod(minutes, 1440)
    hours, minutes = divmod(minutes, 60)
    return ' '.join(p for p in (f'{days}d' if days else '', f'{hours}h' if hours else '', f'{minutes}m') if p) if (days or hours) else f'{minutes}m'


def table(name: str) -> str:
    rows = read(log_file(name))
    if not rows:
        raise SystemExit(f'timeline.py: nothing recorded for {name} (timeline.py start <step>)')
    active: dict[str, timedelta] = {}
    wall: dict[str, timedelta] = {}
    first: dict[str, datetime] = {}
    paused_total = timedelta()
    still_open = rows[-1][1] != 'end'
    events = rows + ([(datetime.now(), 'now', '')] if still_open else [])
    step, paused = None, False
    # Each interval between two marks belongs to the step open then; a paused interval counts for wall clock only.
    for (when, event, s), (after, _, _) in zip(events, events[1:] + [events[-1]]):
        if event == 'start':
            step, paused = s, False
            first.setdefault(s, when)
        elif event == 'pause':
            paused = True
        elif event == 'resume':
            paused = False
        elif event == 'end':
            step, paused = None, False
        d = after - when
        if paused:
            paused_total += d
        if step:
            wall[step] = wall.get(step, timedelta()) + d
            if not paused:
                active[step] = active.get(step, timedelta()) + d
    order = sorted(active, key=lambda s: (ORDER.index(s) if s in ORDER else len(ORDER), first[s]))
    out = [f'Recorded with `timeline.py`, from {rows[0][0]:%Y-%m-%d %H:%M} to '
           f'{"now (still open)" if still_open else f"{rows[-1][0]:%Y-%m-%d %H:%M}"}. Active time leaves out the pauses.',
           '', '| Step | Started | Active | Wall clock |', '|---|---|---|---|']
    for s in order:
        out.append(f'| {LABELS.get(s, s)} | {first[s]:%Y-%m-%d %H:%M} | {fmt(active.get(s, timedelta()))} | {fmt(wall.get(s, timedelta()))} |')
    total_wall = (datetime.now() if still_open else rows[-1][0]) - rows[0][0]
    out.append(f'| **Total** | | **{fmt(sum(active.values(), timedelta()))}** | **{fmt(total_wall)}** |')
    if paused_total:
        out.append(f'\nPaused for {fmt(paused_total)} in all.')
    items = item_rows(name)
    if items:
        out += ['', 'The items of the split (from git: branch created → merged into the base branch):', '',
                '| Item | Started | Merged | Took |', '|---|---|---|---|'] + items
    return '\n'.join(out)


def item_rows(name: str) -> list[str]:
    base = f'feature/{name}'
    if not git('rev-parse', '--verify', '--quiet', base, check=False):
        return []
    merges = [l.split() for l in git('log', '--first-parent', '--merges', '--format=%H %ct %P', base).splitlines()]
    out = []
    for b in git('for-each-ref', '--format=%(refname:short)', 'refs/heads/').splitlines():
        if git('config', f'branch.{b}.splitBase', check=False) != base:
            continue
        cut = git('config', f'branch.{b}.splitFrom', check=False) or base
        times = git('log', '--format=%ct', f'{cut}..{b}', check=False).split()
        if not times:
            continue
        # The branch's creation (its reflog's oldest entry) is when the item started; its first commit is the fallback.
        created = re.findall(r'@\{(\d+)\}', git('reflog', 'show', '--date=unix', '--format=%gd', b, check=False))
        start = datetime.fromtimestamp(int(created[-1] if created else times[-1]))
        tip = git('rev-parse', b)
        merged = next((datetime.fromtimestamp(int(m[1])) for m in reversed(merges) if len(m) > 3 and
                       subprocess.run(['git', 'merge-base', '--is-ancestor', tip, m[3]]).returncode == 0), None)
        slug = b.removeprefix(f'{base}-')
        out.append(f'| {slug} | {start:%Y-%m-%d %H:%M} | {f"{merged:%Y-%m-%d %H:%M}" if merged else "not merged"} | '
                   f'{fmt((merged or datetime.now()) - start)} |')
    return out


def write_report(prd: Path, text: str) -> None:
    content = prd.read_text()
    section = f'## Timeline\n\n{text}\n'
    if re.search(r'^## Timeline\s*$', content, re.M):
        content = re.sub(r'^## Timeline\s*$.*?(?=^## |\Z)', section + '\n', content, flags=re.M | re.S).rstrip() + '\n'
    else:
        content = content.rstrip() + '\n\n' + section
    prd.write_text(content)


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ('start', 'pause', 'resume', 'end', 'show', 'report'):
        print(__doc__.strip())
        return 2
    cmd, name = sys.argv[1], feature()
    path = log_file(name)
    if cmd in ('start', 'pause', 'resume', 'end'):
        step = ''
        if cmd == 'start':
            positional = [a for a in sys.argv[2:] if not a.startswith('--')]
            if not positional:
                raise SystemExit('timeline.py: start <step>')
            step = positional[0]
        at = opt('at')
        when = datetime.fromisoformat(at) if at else datetime.now()
        with path.open('a') as f:
            f.write(f'{when.isoformat(timespec="seconds")}\t{cmd}\t{step}\t{opt("note") or ""}\n')
        print(f'{when:%Y-%m-%d %H:%M} {cmd} {step} ({name})'.replace('  ', ' '))
        return 0
    text = table(name)
    if cmd == 'show':
        print(text)
        return 0
    positional = [a for a in sys.argv[2:] if not a.startswith('--')]
    if not positional or not Path(positional[0]).is_file():
        raise SystemExit('timeline.py: report <prd file>')
    write_report(Path(positional[0]), text)
    print(f'Timeline written into {positional[0]} under "## Timeline".')
    return 0


if __name__ == '__main__':
    sys.exit(main())
