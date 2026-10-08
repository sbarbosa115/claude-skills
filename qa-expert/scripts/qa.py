#!/usr/bin/env python3
"""The QA docs' bookkeeping (steps/01-setup.md, steps/05-record.md). Run from anywhere inside the project checkout.

    qa.py init                         docs/qa/ skeleton (README, flows/, issues/, issues/runs/); only what is missing
    qa.py run --scope=<scope>          docs/qa/issues/runs/<date>-<scope>.md from templates/run.md; never overwrites
    qa.py new --category=ui|functional --severity=P0..P3 --title="…" [--view=… --area=… --route=… --run=…]
                                       docs/qa/issues/QA-nnnn-<slug>.md from templates/issue.md; prints the path
    qa.py index                        regenerate docs/qa/issues/README.md, the priority list
    qa.py status                       the open issues, by priority, on the terminal

An issue's state lives in its frontmatter (`key: value` lines between `---`); the index is built from it alone.
"""

from __future__ import annotations

import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
CATEGORIES = ('ui', 'functional')
SEVERITIES = ('P0', 'P1', 'P2', 'P3')
STATUSES = ('open', 'fixed', 'wontfix', 'duplicate')
ISSUE_FILE = re.compile(r'^QA-(\d{4,})-.*\.md$')


def git(*args: str) -> str:
    return subprocess.run(['git', *args], capture_output=True, text=True, check=True).stdout.strip()


def root() -> Path:
    return Path(git('rev-parse', '--show-toplevel'))


def today() -> str:
    return dt.date.today().isoformat()


def slug(text: str, limit: int = 60) -> str:
    s = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return s[:limit].rstrip('-') or 'issue'


def options(argv: list[str]) -> dict[str, str]:
    opts = {}
    for a in argv:
        if not a.startswith('--') or '=' not in a:
            sys.exit(f'qa.py: expected --key=value, got {a!r}')
        k, v = a[2:].split('=', 1)
        opts[k] = v
    return opts


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding='utf-8')
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    if not m:
        return {}
    data = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            data[k.strip()] = v.strip()
    return data


def issues(qa: Path) -> list[tuple[Path, dict[str, str]]]:
    folder = qa / 'issues'
    if not folder.is_dir():
        return []
    return [(p, frontmatter(p)) for p in sorted(folder.iterdir()) if ISSUE_FILE.match(p.name)]


def fill(template: str, values: dict[str, str]) -> str:
    return re.sub(r'\{(\w+)\}', lambda m: values.get(m.group(1), m.group(0)), template)


def cmd_init(qa: Path) -> None:
    for d in (qa / 'flows', qa / 'issues' / 'runs'):
        d.mkdir(parents=True, exist_ok=True)
    readme = qa / 'README.md'
    if not readme.exists():
        readme.write_text((SKILL / 'templates' / 'qa-README.md').read_text(encoding='utf-8'), encoding='utf-8')
        print(f'wrote {readme}')
    cmd_index(qa)


def cmd_run(qa: Path, opts: dict[str, str]) -> None:
    scope = opts.get('scope', 'all')
    (qa / 'issues' / 'runs').mkdir(parents=True, exist_ok=True)
    path = qa / 'issues' / 'runs' / f'{today()}-{slug(scope, 40)}.md'
    n = 2
    while path.exists():
        path = path.with_name(f'{today()}-{slug(scope, 40)}-{n}.md')
        n += 1
    values = {'date': today(), 'scope': scope, 'commit': git('rev-parse', '--short', 'HEAD'),
              'branch': git('rev-parse', '--abbrev-ref', 'HEAD')}
    path.write_text(fill((SKILL / 'templates' / 'run.md').read_text(encoding='utf-8'), values), encoding='utf-8')
    print(path)


def cmd_new(qa: Path, opts: dict[str, str]) -> None:
    category, severity, title = opts.get('category'), opts.get('severity', '').upper(), opts.get('title', '').strip()
    if category not in CATEGORIES:
        sys.exit(f'qa.py new: --category must be one of {", ".join(CATEGORIES)}')
    if severity not in SEVERITIES:
        sys.exit(f'qa.py new: --severity must be one of {", ".join(SEVERITIES)}')
    if severity == 'P0' and category == 'ui':
        sys.exit('qa.py new: a UI finding is never P0 (steps/03-design-audit.md §3.3)')
    if not title:
        sys.exit('qa.py new: --title is required')
    (qa / 'issues').mkdir(parents=True, exist_ok=True)
    numbers = [int(ISSUE_FILE.match(p.name).group(1)) for p, _ in issues(qa)]
    issue_id = f'QA-{(max(numbers) + 1 if numbers else 1):04d}'
    runs = sorted((qa / 'issues' / 'runs').glob(f'{today()}-*.md')) if (qa / 'issues' / 'runs').is_dir() else []
    values = {'id': issue_id, 'title': title.replace('\n', ' '), 'category': category, 'severity': severity,
              'area': opts.get('area', ''), 'view': opts.get('view', ''), 'route': opts.get('route', ''),
              'date': today(), 'commit': git('rev-parse', '--short', 'HEAD'),
              'run': opts.get('run', runs[-1].stem if runs else today())}
    path = qa / 'issues' / f'{issue_id}-{slug(title)}.md'
    path.write_text(fill((SKILL / 'templates' / 'issue.md').read_text(encoding='utf-8'), values), encoding='utf-8')
    print(path)


def sort_key(item: tuple[Path, dict[str, str]]) -> tuple:
    _, fm = item
    sev = fm.get('severity', 'P3')
    return (SEVERITIES.index(sev) if sev in SEVERITIES else 9,
            0 if fm.get('confidence', 'reproduced') == 'reproduced' else 1,
            0 if fm.get('category') == 'functional' else 1,
            fm.get('found', ''), fm.get('id', ''))


def row(path: Path, fm: dict[str, str]) -> str:
    title = fm.get('title', path.stem).replace('|', '\\|')
    conf = '' if fm.get('confidence', 'reproduced') == 'reproduced' else ' (code-read)'
    return (f"| [{fm.get('id', path.stem)}]({path.name}) | {fm.get('severity', '?')} | {fm.get('category', '?')} | "
            f"{fm.get('area', '')} | {fm.get('view', '')} | {title}{conf} | {fm.get('last_seen', '')} |")


def cmd_index(qa: Path) -> None:
    items = issues(qa)
    open_items = sorted([i for i in items if i[1].get('status', 'open') == 'open'], key=sort_key)
    closed = sorted([i for i in items if i[1].get('status', 'open') != 'open'], key=lambda i: i[1].get('id', ''))
    counts = {s: sum(1 for _, fm in open_items if fm.get('severity') == s) for s in SEVERITIES}
    head = '| Id | Priority | Category | Area | View | Title | Last seen |\n|---|---|---|---|---|---|---|'
    lines = [
        '# QA issues: the priority list',
        '',
        f'Generated by `qa.py index` on {today()} from the issues\' frontmatter; do not edit by hand.',
        '',
        f"**Open: {len(open_items)}** · " + ' · '.join(f'{s}: {counts[s]}' for s in SEVERITIES)
        + f' · closed: {len(closed)}',
        '',
        'Fix from the top: priority first, reproduced before code-read, functional before UI, oldest first.',
        '',
    ]
    for sev in SEVERITIES:
        group = [i for i in open_items if i[1].get('severity') == sev]
        if group:
            lines += [f'## {sev}', '', head, *(row(p, fm) for p, fm in group), '']
    other = [i for i in open_items if i[1].get('severity') not in SEVERITIES]
    if other:
        lines += ['## No valid priority', '', head, *(row(p, fm) for p, fm in other), '']
    if not open_items:
        lines += ['No open issues.', '']
    if closed:
        lines += ['## Closed', '', '| Id | Status | Title | Since |\n|---|---|---|---|']
        lines += [f"| [{fm.get('id', p.stem)}]({p.name}) | {fm.get('status')} | "
                  f"{fm.get('title', '').replace('|', chr(92) + '|')} | {fm.get('fixed_seen', '')} |"
                  for p, fm in closed]
        lines.append('')
    runs = sorted((qa / 'issues' / 'runs').glob('*.md'), reverse=True) if (qa / 'issues' / 'runs').is_dir() else []
    if runs:
        lines += ['## Runs', '', *(f'- [{r.stem}](runs/{r.name})' for r in runs), '']
    out = qa / 'issues' / 'README.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines), encoding='utf-8')
    bad = [p.name for p, fm in items if fm.get('status', 'open') not in STATUSES or fm.get('category') not in CATEGORIES]
    print(f'wrote {out}: {len(open_items)} open, {len(closed)} closed')
    if bad:
        print('check the frontmatter of: ' + ', '.join(bad))


def cmd_status(qa: Path) -> None:
    open_items = sorted([i for i in issues(qa) if i[1].get('status', 'open') == 'open'], key=sort_key)
    if not open_items:
        print('No open issues.')
    for p, fm in open_items:
        conf = '' if fm.get('confidence', 'reproduced') == 'reproduced' else ' (code-read)'
        print(f"{fm.get('severity', '?')}  {fm.get('id', p.stem)}  {fm.get('category', '?'):<10}  "
              f"{fm.get('view', '')}: {fm.get('title', '')}{conf}")


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        return 0
    qa = root() / 'docs' / 'qa'
    command, opts = sys.argv[1], options(sys.argv[2:])
    if command == 'init':
        cmd_init(qa)
    elif command == 'run':
        cmd_run(qa, opts)
    elif command == 'new':
        cmd_new(qa, opts)
    elif command == 'index':
        cmd_index(qa)
    elif command == 'status':
        cmd_status(qa)
    else:
        sys.exit(f'qa.py: unknown command {command!r}; see --help')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
