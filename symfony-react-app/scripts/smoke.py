#!/usr/bin/env python3
"""Run the smoke suite (steps/08-regression-run.md §8.1) and record the attempt in the feature's run file.

Run from anywhere inside the project's git checkout, with its Docker stack up:

    python3 ~/.claude/skills/symfony-react-app/scripts/smoke.py              # the whole suite, recorded
    python3 ~/.claude/skills/symfony-react-app/scripts/smoke.py ordering     # part of it (arguments go to Playwright): not recorded

The suite is the project's `<app>/e2e/smoke.sh` when it has one (it prepares the stack: seed data, offline stand-ins
for outside services), else `docker compose --profile e2e run --rm e2e`. The result is read from Playwright's JSON
report (`<app>/e2e/.results/report.json`: add the `json` reporter to the config) and added as a row to the "Smoke
suite" table of docs/tests/runs/<date>-<feature>.md (new-run.py creates the file if there is none). Every attempt
gets its row: the failing ones are the record of what was found and fixed before the browser run started.

Green means no test failed and none was skipped: a `test.fixme` is a known failure, not a pass. Exit 0 only then.
Settings: APP_DIR (backend).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
APP_DIR = os.environ.get('APP_DIR', 'backend')
MARKER = '<!-- smoke.py adds a row per run of the whole suite -->'


def git(*args: str) -> str:
    return subprocess.run(['git', *args], capture_output=True, text=True, check=True).stdout.strip()


def outcomes(report: dict) -> tuple[int, list[str], list[str]]:
    """How many tests passed, and the titles of those that failed and of those that were skipped."""
    passed, failed, skipped = 0, [], []

    def walk(suite: dict) -> None:
        nonlocal passed
        for spec in suite.get('specs', []):
            statuses = [t.get('status') for t in spec.get('tests', [])]
            if any(s == 'unexpected' for s in statuses):
                failed.append(spec['title'])
            elif any(s == 'flaky' for s in statuses):
                failed.append(spec['title'] + ' (flaky: passed on a retry)')
            elif statuses and all(s == 'skipped' for s in statuses):
                skipped.append(spec['title'])
            else:
                passed += 1
        for child in suite.get('suites', []):
            walk(child)

    for suite in report.get('suites', []):
        walk(suite)
    return passed, failed, skipped


def case_ids(titles: list[str]) -> str:
    """The case IDs the titles start with ("ORD-04 · …"), or the titles themselves."""
    names = []
    for title in titles:
        found = re.match(r'([A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)*-\d+)', title)
        name = found.group(1) + (' (flaky)' if 'flaky' in title else '') if found else title.replace('|', '/')
        if name not in names:
            names.append(name)
    return ', '.join(names)


def main() -> int:
    root = Path(git('rev-parse', '--show-toplevel'))
    os.chdir(root)
    args = sys.argv[1:]
    script = root / APP_DIR / 'e2e' / 'smoke.sh'
    report_file = root / APP_DIR / 'e2e' / '.results' / 'report.json'
    if report_file.exists():
        report_file.unlink()

    command = [str(script), *args] if script.exists() else ['docker', 'compose', '--profile', 'e2e', 'run', '--rm', 'e2e', 'npx', 'playwright', 'test', *args]
    started = dt.datetime.now()
    code = subprocess.run(command).returncode
    took = dt.datetime.now() - started

    if not report_file.exists():
        print(f'\nsmoke.py: no {report_file.relative_to(root)}: the suite did not run (or the config has no json reporter).', file=sys.stderr)
        return code or 1
    passed, failed, skipped = outcomes(json.loads(report_file.read_text()))
    green = code == 0 and not failed and not skipped
    result = f'{passed} passed, {len(failed)} failed' + (f', {len(skipped)} skipped' if skipped else '')
    print(f'\nSmoke suite: {result} in {int(took.total_seconds() // 60)} min {int(took.total_seconds() % 60)} s' + ('' if green else ': NOT GREEN'))

    if args:
        print('A partial run is not recorded: run the whole suite (no arguments) for the record.')
        return 0 if green else 1

    branch = git('rev-parse', '--abbrev-ref', 'HEAD')
    feature = branch.removeprefix('feature/').replace('/', '-')
    runs = sorted((root / 'docs' / 'tests' / 'runs').glob(f'*-{feature}.md'))
    if not runs:
        subprocess.run([sys.executable, str(SCRIPTS / 'new-run.py')], check=False)
        runs = sorted((root / 'docs' / 'tests' / 'runs').glob(f'*-{feature}.md'))
    if not runs or MARKER not in runs[-1].read_text():
        print('smoke.py: no run file with a "Smoke suite" table to record this in (new-run.py creates one).', file=sys.stderr)
        return 0 if green else 1
    run = runs[-1]
    text = run.read_text()
    attempt = len(re.findall(r'^\|\s*\d+\s*\|', text[text.index('## Smoke suite'):text.index(MARKER)], re.M)) + 1
    dirty = ' + uncommitted changes' if git('status', '--porcelain', '--', '.', ':!docs') else ''
    notes = '; '.join(filter(None, [case_ids(failed), f'skipped: {case_ids(skipped)}' if skipped else ''])) or '—'
    row = f'| {attempt} | {started:%Y-%m-%d %H:%M} | `{git("rev-parse", "--short", "HEAD")}`{dirty} | {"Green" if green else "Not green"}: {result} | {notes} |\n'
    run.write_text(text.replace(MARKER, row + MARKER))
    print(f'Recorded as attempt {attempt} in {run.relative_to(root)}.' + ('' if green else ' Write what failed and its fix under "Smoke findings", fix it, and run again.'))
    return 0 if green else 1


if __name__ == '__main__':
    sys.exit(main())
