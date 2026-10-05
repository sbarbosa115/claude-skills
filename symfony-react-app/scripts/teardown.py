#!/usr/bin/env python3
"""Tear down a feature once its pull request is merged (steps/11-pr-and-teardown.md).

Run from anywhere inside the project's git checkout:

    python3 ~/.claude/skills/symfony-react-app/scripts/teardown.py [feature/<name>]          # print what it would do
    python3 ~/.claude/skills/symfony-react-app/scripts/teardown.py [feature/<name>] --yes    # do it
    … --force    # the merge cannot be detected (a squash or rebase merge without gh): the user confirmed it

The branch defaults to the current one. It refuses while the branch is not merged into origin/main: its pull request
is MERGED (gh, when logged in), or its tip is in origin/main. Then, for the base branch and every item of its split
(the branches split.py recorded with splitBase = the base branch): `docker compose down --volumes --remove-orphans`
in each worktree, `git worktree remove` (refused for a worktree with uncommitted changes: it is reported and kept),
and the local branches deleted. The main checkout is never removed, and remote branches are left alone.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def sh(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, cwd=cwd)


def git(*args: str, cwd: Path | None = None) -> str:
    res = sh('git', *args, cwd=cwd)
    if res.returncode:
        raise SystemExit(f'teardown.py: git {" ".join(args)}: {res.stderr.strip()}')
    return res.stdout.strip()


def worktrees() -> list[tuple[Path, str]]:
    """(path, branch) of every worktree; the first one is the main checkout."""
    out, path = [], None
    for line in git('worktree', 'list', '--porcelain').splitlines():
        if line.startswith('worktree '):
            path = Path(line.split(' ', 1)[1])
        elif line.startswith('branch ') and path:
            out.append((path, line.split(' ', 1)[1].removeprefix('refs/heads/')))
        elif line == 'detached' and path:
            out.append((path, ''))
    return out


def merged(branch: str, base: str) -> tuple[bool, str]:
    if sh('gh', 'auth', 'status').returncode == 0:
        res = sh('gh', 'pr', 'view', branch, '--json', 'state,url', '-q', '.state + " " + .url')
        if res.returncode == 0 and res.stdout.strip():
            state, url = res.stdout.strip().split(' ', 1)
            return state == 'MERGED', f'pull request {state.lower()}: {url}'
    if sh('git', 'merge-base', '--is-ancestor', branch, f'origin/{base}').returncode == 0:
        return True, f'{branch} is in origin/{base}'
    return False, f'{branch} is not in origin/{base} (a squash merge is not detected without gh: --force once confirmed)'


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    do_it, force = '--yes' in sys.argv, '--force' in sys.argv
    trees = worktrees()
    main_checkout = trees[0][0]
    branch = args[0] if args else git('rev-parse', '--abbrev-ref', 'HEAD')
    try:
        base = git('symbolic-ref', '--short', 'refs/remotes/origin/HEAD').removeprefix('origin/')
    except SystemExit:
        base = 'main'
    if branch in (base, 'main', 'master', 'HEAD'):
        print(f'teardown.py: give the feature base branch (on {branch} now)', file=sys.stderr)
        return 2
    split_base = sh('git', 'config', f'branch.{branch}.splitBase').stdout.strip()
    if split_base:
        print(f'teardown.py: {branch} is an item of {split_base}: tear down the base branch, which takes its items too', file=sys.stderr)
        return 2

    sh('git', 'fetch', '--quiet', 'origin', cwd=main_checkout)
    ok, why = merged(branch, base)
    print(f'{"Merged" if ok else "Not merged"}: {why}')
    if not ok and not force:
        return 1

    items = [b for b in git('for-each-ref', '--format=%(refname:short)', 'refs/heads/').splitlines()
             if sh('git', 'config', f'branch.{b}.splitBase').stdout.strip() == branch]
    branches = [branch] + items
    targets = [(p, b) for p, b in trees if b in branches and p != main_checkout]

    print(f'\nStacks and worktrees ({len(targets)}):')
    for path, b in targets:
        has_compose = any((path / f).exists() for f in ('compose.yaml', 'compose.yml', 'docker-compose.yml', 'docker-compose.yaml'))
        print(f'  {path}  ({b}){"" if has_compose else "  no compose file"}')
    print(f'Local branches ({len(branches)}): {", ".join(branches)}')
    if any(b in branches for p, b in trees if p == main_checkout):
        print(f'  The main checkout ({main_checkout}) is on one of them: switch it to {base} first; it is kept.')
    if not do_it:
        print('\nNothing done. Run again with --yes to tear it down (the stacks\' volumes, the feature\'s data, go too).')
        return 0

    kept: list[str] = []
    for path, b in targets:
        if any((path / f).exists() for f in ('compose.yaml', 'compose.yml', 'docker-compose.yml', 'docker-compose.yaml')):
            res = sh('docker', 'compose', 'down', '--volumes', '--remove-orphans', cwd=path)
            print(f'{"down " if res.returncode == 0 else "FAIL "} docker compose in {path.name}' + ('' if res.returncode == 0 else f': {res.stderr.strip()[-200:]}'))
        res = sh('git', 'worktree', 'remove', str(path), cwd=main_checkout)
        if res.returncode:
            kept.append(f'{path}: {res.stderr.strip()}')
            print(f'KEPT  worktree {path.name}: {res.stderr.strip()}')
        else:
            print(f'gone  worktree {path.name}')
    sh('git', 'worktree', 'prune', cwd=main_checkout)

    still_out = {b for _, b in worktrees()}
    for b in branches:
        if b in still_out:
            print(f'KEPT  branch {b} (a worktree still has it)')
            continue
        res = sh('git', 'branch', '-D', b, cwd=main_checkout)
        print(f'{"gone " if res.returncode == 0 else "FAIL "} branch {b}' + ('' if res.returncode == 0 else f': {res.stderr.strip()}'))
    if kept:
        print('\nNot torn down (uncommitted changes: look at them, then remove by hand):\n  ' + '\n  '.join(kept))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
