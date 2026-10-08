## 1. Set up: scope, a safe stack, accounts, the run file

### 1.1 Scope

Take the scope from the request. If none was given, use this order:

1. **No `docs/qa/` yet:** the first run. Map the whole app (step 2), then audit every view.
2. **A view, an area or a flow named:** just that, plus anything it opens (a dialog, a detail page, an email).
3. **"Since the last run":** the views touched by `git log --since=<last run date> --name-only`, mapped to views
   through the router and the flow docs, plus every open issue (re-checked in step 5).
4. **"Everything" on a later run:** every view, the ones with the oldest "last checked" in the coverage table first.

A big app is done in passes. Say which areas this run covers and which it leaves, and write the same in the run
file. Never pretend a pass covered more than it did.

### 1.2 Read before using the app

- `README.md`, `CLAUDE.md`, the PRD or spec if there is one: what the app is for, who uses it (roles), the rules.
- The design sources: brand or design docs, the design tokens (CSS variables, theme file), the component library
  and its README. These are **the main design** that step 3 measures every screen against. Write their paths in
  `docs/qa/README.md` under "Design sources" on the first run.
- The router (frontend routes) and the API routes: the list of views and what each one calls.
- Existing test suites and regression docs: what is already covered, and the seed accounts and fixtures.
- `docs/qa/` from earlier runs: the flows, the open issues, the last run report.

### 1.3 A stack that is safe to break

- Use a local or disposable stack. Never production, never a shared stack another session is using (a test suite
  that resets the database will wipe what you are looking at, and your writes will spoil theirs).
- Know how to put it back: the seed or reset command. Note the commit you test (`git rev-parse --short HEAD`).
- Outside services (payments, LLMs, email): use the project's offline stand-ins or sandbox; read sent emails in the
  mail catcher.
- One account per role (owner, admin, member, visitor signed out, a second tenant for access checks).

### 1.4 The browser

Drive the app in a real browser (Claude in Chrome or the built-in browser; load its skill first). Check every screen
at a phone width (390px) and at a desktop width; if the window will not resize, use the device toolbar or say the
phone check was not done. Keep the console and network panels in view: an error there is a finding.

Browser tools are one shared window: do the browser work yourself, in sequence. Code reading (routes, handlers,
validation, voters) can be fanned out to subagents in parallel, one per area, each returning suspected issues with
file:line, which you then reproduce in the browser.

### 1.5 Start the files

```bash
python3 ~/.claude/skills/qa-expert/scripts/qa.py init                 # docs/qa/ skeleton, only what is missing
python3 ~/.claude/skills/qa-expert/scripts/qa.py run --scope=admin    # docs/qa/issues/runs/<date>-admin.md
```

Fill the run file's header (scope, commit, stack, accounts, widths) before starting.
