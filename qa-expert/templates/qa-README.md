# QA

Written by the `qa-expert` skill. Each run uses the app view by view, looking for UI/UX inconsistencies and
functional issues, and files what it finds.

- `flows/`: how the app works, one doc per area: views, actions, rules, expected behaviour.
- `issues/README.md`: **the priority list** of every issue (generated; do not edit by hand).
- `issues/QA-nnnn-*.md`: one issue per file.
- `issues/runs/`: one report per run: what was covered, found, re-checked.

Priorities: **P0** data loss, security or privacy leak, money wrong, a core flow nobody can complete · **P1** a main
flow broken for some, wrong results, a crash, an unusable screen · **P2** a secondary flow broken, a clear departure
from the design · **P3** polish and rare edge cases.

## Design sources

The main design every screen is measured against:

- <!-- e.g. docs/brand.md, the tokens file, the component library README -->

Reference screens (the ones that follow it best):

- <!-- view: why -->

## Coverage

| View | Route | Role | Flow doc | Last checked | Open issues |
|---|---|---|---|---|---|
