#!/usr/bin/env python3
"""Open the feature's pull request, or print the link to open it by hand (steps/11-pr-and-teardown.md).

Run from anywhere inside the feature base branch's worktree, after the definition of done passed:

    python3 ~/.claude/skills/symfony-react-app/scripts/pr.py --title "…" --body-file <file>
    python3 ~/.claude/skills/symfony-react-app/scripts/pr.py --title "…" --body-file <file> --force   # skip the DoD check

It refuses an item of a split (only the base branch opens a pull request) and, unless --force, a branch whose
`dod.py --quick` fails. It pushes the branch, then opens the pull request with `gh` when gh is logged in (or prints the
one that is already open). Without gh it prints the GitHub link that opens the pull request form, and the body file to
paste into it.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def sh(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, cwd=cwd)


def git(*args: str) -> str:
    res = sh('git', *args)
    if res.returncode:
        raise SystemExit(f'pr.py: git {" ".join(args)}: {res.stderr.strip()}')
    return res.stdout.strip()


def arg(name: str) -> str | None:
    for i, a in enumerate(sys.argv[1:], 1):
        if a == name and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        if a.startswith(name + '='):
            return a.split('=', 1)[1]
    return None


def github_repo(url: str) -> str | None:
    m = re.match(r'^(?:git@github\.com:|https://github\.com/|ssh://git@github\.com/)([^/]+/[^/]+?)(?:\.git)?/?$', url)
    return m.group(1) if m else None


def main() -> int:
    root = Path(git('rev-parse', '--show-toplevel'))
    branch = git('rev-parse', '--abbrev-ref', 'HEAD')
    try:
        base = git('symbolic-ref', '--short', 'refs/remotes/origin/HEAD').removeprefix('origin/')
    except SystemExit:
        base = 'main'
    if branch in (base, 'main', 'master', 'HEAD'):
        print(f'pr.py: on {branch}: run it on the feature base branch', file=sys.stderr)
        return 1
    if sh('git', 'config', f'branch.{branch}.splitBase').stdout.strip():
        print(f'pr.py: {branch} is an item of a split: only its base branch opens a pull request', file=sys.stderr)
        return 1

    title = arg('--title')
    body_file = arg('--body-file')
    if not title or not body_file or not Path(body_file).is_file():
        print('pr.py: give --title "…" and --body-file <an existing file>', file=sys.stderr)
        return 2

    if '--force' not in sys.argv:
        dod = sh(sys.executable, str(SCRIPTS / 'dod.py'), '--quick', cwd=root)
        if dod.returncode:
            print(dod.stdout)
            print('pr.py: the definition of done is not met (dod.py --quick): fix it first, or --force', file=sys.stderr)
            return 1
    if sh('git', 'status', '--porcelain', '--untracked-files=no').stdout.strip():
        print('pr.py: uncommitted changes in tracked files: commit them first', file=sys.stderr)
        return 1

    push = sh('git', 'push', '-u', 'origin', branch)
    if push.returncode:
        print(f'pr.py: git push failed:\n{push.stderr.strip()}', file=sys.stderr)
        return 1
    print(f'Pushed {branch}.')

    if sh('gh', 'auth', 'status').returncode == 0:
        existing = sh('gh', 'pr', 'view', branch, '--json', 'url,state', '-q', 'select(.state == "OPEN") | .url')
        if existing.returncode == 0 and existing.stdout.strip():
            print(f'Pull request already open: {existing.stdout.strip()}')
            return 0
        res = sh('gh', 'pr', 'create', '--base', base, '--head', branch, '--title', title, '--body-file', body_file)
        if res.returncode == 0:
            print(f'Pull request opened: {res.stdout.strip().splitlines()[-1]}')
            return 0
        print(f'gh pr create failed ({res.stderr.strip()}); open it by hand:', file=sys.stderr)

    repo = github_repo(git('remote', 'get-url', 'origin'))
    if not repo:
        print('pr.py: origin is not a GitHub remote: open the pull request in its host by hand', file=sys.stderr)
        return 1
    from urllib.parse import quote
    print('\ngh is not available or not logged in. Open the pull request by hand:')
    print(f'  https://github.com/{repo}/compare/{base}...{quote(branch, safe="/")}?expand=1&title={quote(title)}')
    print(f'and paste the body from {Path(body_file).resolve()}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
