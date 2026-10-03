#!/usr/bin/env python3
"""Create the file for a regression run (steps/08-regression-run.md), and the suite itself when there is none.

Run from anywhere inside the project's git checkout:

    python3 ~/.claude/skills/symfony-react-app/scripts/new-run.py            # docs/tests/runs/<date>-<feature>.md
    python3 ~/.claude/skills/symfony-react-app/scripts/new-run.py --name=release-2.3

It reads every case from docs/tests/ui-regression.md (lines like `**AREA-01 · What the user does**`). A case whose
next line starts with "Smoke:" is run by the smoke suite (smoke.py) and is not listed; one marked "Smoke (part):"
is listed with what is left to do by hand; every other case is listed as "Not run". The file has two parts, in the
order they are done: the smoke suite's attempts (smoke.py adds a row per run), then the manual run in the browser.
With no suite yet it writes the skeleton from templates/ui-regression.md and names the run "baseline": write the
cases for what exists first, then run it. An existing run file is never overwritten.
"""

from __future__ import annotations

import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
CASE = re.compile(r'^\*\*([A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)*-\d+)\s*·\s*(.+?)\*\*[^\n]*\n(?:(Smoke(?: \(part\))?):\s*([^\n]*(?:\n(?![\n*#])[^\n]*)*))?', re.M)


def git(*args: str) -> str:
    return subprocess.run(['git', *args], capture_output=True, text=True, check=True).stdout.strip()


def main() -> int:
    root = Path(git('rev-parse', '--show-toplevel'))
    tests = root / 'docs' / 'tests'
    suite = tests / 'ui-regression.md'
    branch = git('rev-parse', '--abbrev-ref', 'HEAD')
    commit = git('rev-parse', '--short', 'HEAD')
    name = next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('--name=')), None)

    baseline = not suite.exists()
    if baseline:
        tests.mkdir(parents=True, exist_ok=True)
        suite.write_text((SKILL / 'templates' / 'ui-regression.md').read_text())
        print(f'No suite yet: wrote the skeleton {suite.relative_to(root)}. Add a case for everything that exists, then run it.')
        name = name or 'baseline'
    name = name or branch.removeprefix('feature/').replace('/', '-')

    found = CASE.findall(suite.read_text())
    automated = [cid for cid, _, smoke, _ in found if smoke == 'Smoke']
    cases = []
    for cid, title, smoke, note in found:
        if smoke == 'Smoke':
            continue
        if smoke:
            # The marker ends at its first full stop at the end of a line (the case's own text follows it). What
            # is left for a person is what it says after "by hand:".
            note = re.split(r'\.[ \t]*(?:\n|$)', note, maxsplit=1)[0]
            by_hand = re.search(r'by hand:\s*(.+)', ' '.join(note.split()), re.I)
            title += ' — by hand: ' + (by_hand.group(1).rstrip('.') if by_hand else 'see the case')
        cases.append((cid, title.replace('|', '/')))
    run = tests / 'runs' / f'{dt.date.today():%Y-%m-%d}-{name}.md'
    if run.exists():
        print(f'{run.relative_to(root)} exists: not overwritten.')
        return 1
    run.parent.mkdir(parents=True, exist_ok=True)
    rows = '\n'.join(f'| {cid} | Not run | {title} |' for cid, title in cases)
    run.write_text(f'''# UI regression run — {dt.date.today():%Y-%m-%d} ({name})

- **Suite:** [`../ui-regression.md`](../ui-regression.md), at `{commit}`{", first version (the baseline)" if baseline else ""}.
- **Branch:** `{branch}` at `{commit}`, on this checkout's stack (app <!-- URL -->).
- **Data:** <!-- reset to the seed before the run / not reset (why) -->
- **How:** the smoke suite first (Playwright against this stack), until it is green; then the cases left for a person, in a browser driven through the real UI; emails read in the mail catcher; database/logs where a screen could not prove it.

## Summary

| | Cases |
|---|---|
| Cases in the suite | {len(found)} |
| Run by the smoke suite | {len(automated)} |
| Left for the manual run | {len(cases)} |
| Manual: pass | <!-- N (M after a fix made during the run) --> |
| Manual: fail | <!-- N: IDs --> |

## Smoke suite

`python3 ~/.claude/skills/symfony-react-app/scripts/smoke.py` runs it and adds a row here. A run that is not green
is recorded too: write what failed under "Smoke findings", fix it, and run again. The manual run starts only when
the last row is green.

| # | When | Commit | Result | Failed |
|---|---|---|---|---|
<!-- smoke.py adds a row per run of the whole suite -->

### Smoke findings

<!-- Numbered: the failing test (its case ID), whether the app or the test was wrong, the cause, and the fix (commit). -->

## Manual run

Replace "Not run" with Pass, Fail, "Pass after fix" (with the commit) or Blocked (with why). Group consecutive
passes into ranges (`AREA-01 – 05`) once done.

| ID | Result | Case / notes |
|---|---|---|
{rows}

## Findings

<!-- Numbered: what happened, which case, the cause, and the fix (commit) or why it was left. -->

## Conditions

<!-- Anything about the environment that could have affected the result. -->
''')
    print(f'Created {run.relative_to(root)}: {len(automated)} cases run by the smoke suite, {len(cases)} to run by hand.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
