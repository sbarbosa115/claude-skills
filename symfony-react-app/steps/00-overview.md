# Building a feature: stack, process and definition of done

How a new feature goes from an idea to a merged branch in a **Symfony + React** application that runs in
**Docker**. It holds the stack, the process and the quality bar, not any product's business rules. Those live in
the project's own `README.md`, `CLAUDE.md` and project skill (its `.claude/skills/`). When they disagree with this
guide, they win.

This guide is the process of the global `symfony-react-app` Claude Code skill (`~/.claude/skills/symfony-react-app/`,
file `steps/`). The skill's scripts run its checks: `gate.sh` (§5), `audit.py` (§6), `new-run.py` and `smoke.py` (§8) and `dod.py`
(definition of done). Its `templates/` hold the files a project gets when it has none: the security checklist, the
regression suite, the CI workflow, the FSD import rules and the format-on-edit hook.

The whole process, in order:

1. **Stack:** the tools every step below relies on.
2. **Plan:** write down what the feature does, which layers it touches and how it will be checked. When it is big,
   split it into items built in parallel after a contract item (§2b): each item is merged into the feature base
   branch as soon as it is built, the base branch waits until every item is merged, and only then do the full
   tests and steps 5–9 run, once. The plan is written by the most advanced model, which also sets the model each
   item's agent runs on.
3. **Branch:** create a feature base branch from a fresh `main` (or `master`) in its own worktree.
4. **Build test-first:** in the backend as a Senior PHP/Symfony developer, following DDD; in the frontend as a
   React UI/UX engineer, following Feature-Sliced Design.
5. **Static analysis and code style:** PHPStan and PHP-CS-Fixer (Symfony standard) for PHP; ESLint and Prettier
   (Google style) for JS/TS. Loop until every tool exits clean, and create the configs if the project has none.
6. **Security audit:** check the change against the common attacks, record every finding in `docs/security/`,
   fix it and move on.
7. **Verify on the local Docker stack:** automated suites and the browser.
8. **Record a regression run:** add the feature's cases to the regression suite, the simple ones as Playwright
   smoke tests. Run the smoke suite against the stack; record, fix and re-run until it is green; only then run the
   cases left for a person in the browser. Both parts are recorded in `docs/tests/runs/`. If there is no suite yet,
   the first feature sets up the baseline.
9. **Finish:** docs and CI.
10. **Definition of done:** the checklist, with `dod.py`.
11. **Pull request, then teardown:** open the pull request, or give the user the link to open it by hand, and
    write the feature's timeline into its PRD; once the user has merged it, tear down every Docker stack and
    worktree the feature used.

**Time every step as it starts.** The session cannot remember when a step began, so it records it then:

```bash
python3 ~/.claude/skills/symfony-react-app/scripts/timeline.py start <step>   # plan, split, branch, contract, build,
                                                                              # merge, barrier, gate, tests, audit,
                                                                              # verify, regression, finish, dod, pr
python3 ~/.claude/skills/symfony-react-app/scripts/timeline.py pause          # the user stops the work, or it waits on them
python3 ~/.claude/skills/symfony-react-app/scripts/timeline.py resume
```

Starting a step ends the one before; a step started again (the gate after a fix) adds to its time. The log lives in
the repository's git directory, so every worktree and a later session add to the same one. On `main`, before the
branch exists, add `--feature=<name>`. A step whose start was missed is recorded late with `--at="YYYY-MM-DD HH:MM"`
(from the commit or file times), never guessed: if nothing shows when it began, leave it out and say so.
