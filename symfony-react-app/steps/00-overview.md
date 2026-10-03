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
   split it into items built in parallel after a contract item (§2b). The plan is written by the most advanced
   model, which also sets the model each item's agent runs on.
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
9. **Finish:** docs, the definition-of-done checklist and the pull request.
