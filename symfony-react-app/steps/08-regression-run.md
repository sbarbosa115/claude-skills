## 8. Record a regression run after every feature: the smoke suite, then the browser

The regression suite in `docs/tests/ui-regression.md` proves the app still works as real users use it. It is run in
two parts, in this order, and **every feature ends with both recorded**:

1. **The smoke suite:** the simple cases, as Playwright tests against the worktree's Docker stack. Minutes.
2. **The manual run:** the cases that need a person, driven in a browser. It starts only when the smoke suite is
   green.

A failure in the smoke suite is cheaper to find and to fix than the same failure met by hand an hour into a manual
run, and a broken sign-in or a blank screen would spoil every manual case after it. So nothing is checked by hand
while a smoke test fails.

**A split feature (§2b)** records one run, on the base branch after every item is merged. Each item writes its
cases into the suite in the ID range the split table gave it, with its smoke tests passing on its own stack.

### 8.0 Which cases are smoke tests

Every case is written in the suite, in the format below. Then it is one of three things:

| Smoke: a script can judge all of it | Manual: it needs a person |
|---|---|
| A view opens and shows the right things, with no console error | Anything judged by eye: layout on a phone, themes, colours, motion |
| A straightforward create / edit / remove with a clear result | Timing and feel: a carousel, the scroll position, typing while something loads |
| Access rules: signed out, another tenant's record, a role or feature that is off | A real outside service (a payment provider, an LLM, OAuth, object storage) |
| A form's validation messages | Long stories with several actors and emails |
| A simple flow with the outside service replaced by the project's offline stand-in; an email read in the mail catcher | What only the database, a log or a console command can prove |

A case that mixes both is **part**: the action is a smoke test, and the rest stays in the manual run. When in doubt,
ask whether a failing assertion would reliably mean the app is broken; if a script cannot say, the case is manual.

The suite says which is which, on the line under the case's title:

```markdown
**ORD-01 · The "Create Order" pill starts the order with the catalog**
Smoke: `e2e/ordering.spec.ts`.
…the case's text, unchanged…

**ADM-06 · Products: add, change, remove**
Smoke (part): `e2e/admin.spec.ts` covers adding, changing and removing; by hand: the table at 390px.
…
```

No line: the case is manual. A case keeps its ID and its text whatever runs it, so a manual run can still be made
of any case, and a test is **named by its case ID** (`test('ORD-01 · the "Create Order" pill starts the order', …)`)
so a failure reads as a case of the suite.

### 8.1 The smoke suite

The suite lives in `<app>/e2e/` (`templates/e2e/` has the starting files when the project has none):

- `playwright.config.ts`: one worker, the viewport the app is used on, the `json` reporter writing
  `e2e/.results/report.json`.
- `e2e/prepare.sh`: puts the stack in a known state before a run: the dev database reset to the seed and the smoke
  fixtures, the accounts, the offline stand-ins for outside services, an empty mail catcher, no rate limit used.
- `e2e/smoke.sh`: `prepare.sh`, then Playwright in the stack's `e2e` container.
- `e2e/<area>.spec.ts`: one spec per area of the suite; `e2e/support/`: sign-in, the mail catcher, helpers.

Rules that keep it trustworthy:

- **Each spec works on its own data** (a fixture business, account or record of its own), so no test depends on
  another file's, and a test sets up what it needs through the UI or the API.
- **Find things as a person does** (role, label, text), never by CSS class, and never wait a fixed time: an
  assertion waits by itself.
- **No real outside service.** The suite needs no key and costs nothing.
- **A test is never weakened to pass.** If the app is wrong, the app is fixed.
- The specs pass ESLint, Prettier and `tsc` like the rest of the frontend, and CI runs the suite.

Running it, and the loop:

```bash
python3 ~/.claude/skills/symfony-react-app/scripts/new-run.py     # the run file: the smoke table and the manual cases
python3 ~/.claude/skills/symfony-react-app/scripts/smoke.py       # run the suite, record the attempt
```

1. **Run it.** `smoke.py` runs the whole suite and adds a row to the run file's "Smoke suite" table: when, the
   commit, how many passed, and the cases that failed.
2. **Not green: document it first.** Under "Smoke findings", for each failing test: its case ID, whether the app
   or the test was wrong, and the cause. Read the trace and the screenshot Playwright leaves
   (`e2e/.results/artifacts`) before deciding which.
3. **Fix it** on the feature branch: the app, with a PHPUnit or Vitest test where the logic lives, or the test when
   it was the one that was wrong. Add the fix's commit to the finding.
4. **Run it again**, the whole suite: another row. Repeat until the last row is green.

**Green** means no test failed and none was skipped. A `test.fixme` is a known failure, not a pass: it is fixed, or
the case goes back to the manual run with its reason. A test that passes only sometimes is a failing test: fix its
waiting or the race it found. A run of part of the suite (`smoke.py ordering`) is for working on a fix and is not
recorded. `dod.py` fails while the last recorded attempt is not green, or when the code changed after it.

### 8.2 The manual run

Only after §8.1 is green, and on the same stack:

1. **Reset to the seed data** (the suite's "Before you start"), so the run does not depend on what the smoke suite
   left.
2. **Run the cases listed in the run file's "Manual run" table, in order,** through the real UI (clicks, typing,
   file inputs), reading emails in the mail catcher, and checking the database or logs only where a screen cannot
   prove the result. A case marked "part" is run for what its line says is left "by hand".
3. **Record each result** in the table.
4. **Fix what failed** on the feature branch with a test where the backend was involved. A fix changes the code, so
   the smoke suite is run again (a new green row) before the failed cases are re-run and marked "Pass after fix"
   with the commit.

A manual case that turns out to be simple (it was run by hand and a script could have judged it) becomes a smoke
test in the same feature.

### 8.3 No suite yet: establish the baseline

If this is the project's first feature, or nobody has written the suite yet, this feature creates it:

1. Write `docs/tests/ui-regression.md` with:
   - **Before you start:** the commands that reset the stack to known data, the services that must be up, the
     test accounts per role (dev-only passwords), and the files to have ready (a PDF, an image…).
   - **Checks on every screen:** no console errors, no blank page, no raw translation keys, tables in the house
     style, a message after every save.
   - **One section per area of the app** (public site, each role's space, emails), with cases for what already
     exists: sign-in and sign-out for every role, each list (search, filter, empty state), each create/edit/delete,
     each email, and access control (a role cannot reach another's URLs, another tenant's data is invisible).
     Order the cases so later ones use the data earlier ones create.
   - The new feature's own cases.
2. Set up `<app>/e2e/` from `templates/e2e/` and write the smoke tests for the simple cases (§8.0), marking them in
   the suite.
3. Run both parts (§8.1, §8.2) and record them as `docs/tests/runs/<YYYY-MM-DD>-baseline.md`. That run is the
   baseline every later run is compared against.
4. Failures found by the baseline that are **not** caused by the feature go in the run file's findings and the
   README's "Known gaps". Fix them only if the user agrees. The baseline records the truth; it does not have to be
   all green.

### Case format

```markdown
**AREA-NN · What the user does, as a sentence**
Smoke: `e2e/<area>.spec.ts`.          (or "Smoke (part): … covers …; by hand: …", or no such line: manual)
Where to go › what to click, with the exact data to type (`Example value`) › the button.
**Expected:** the message that appears, what the row/table shows now, and the email that arrives (subject, recipient).
```

IDs are stable: a case keeps its ID forever. New cases take the next number in their section, and a removed case
leaves a gap.

### Run file format

`new-run.py` writes it; `smoke.py` fills the smoke table.

```markdown
# UI regression run — <date> (<feature or "baseline">)

- **Suite:** [`../ui-regression.md`](../ui-regression.md), at `<commit>`.
- **Branch:** `feature/<name>` at `<commit>`, on the worktree's stack (app :<port>).
- **Data:** reset to the seed before each part / not reset (say why).
- **How:** the smoke suite first, until green; then the cases left for a person, in a browser.

## Summary
| | Cases |
|---|---|
| Cases in the suite | N |
| Run by the smoke suite | N |
| Left for the manual run | N |
| Manual: pass | N (M after a fix made during the run) |
| Manual: fail | N — IDs |

## Smoke suite
| # | When | Commit | Result | Failed |
|---|---|---|---|---|
| 1 | 2026-01-10 10:02 | `abc1234` | Not green: 96 passed, 2 failed | ORD-04, ADM-06 |
| 2 | 2026-01-10 10:31 | `def5678` | Green: 98 passed, 0 failed | — |

### Smoke findings
1. ORD-04: the app was wrong. The summary added the delivery fee twice. Fixed in `def5678`, with `OrderTotalTest`.
2. ADM-06: the test was wrong. It looked for "Saved" before the modal closed. Fixed in `def5678`.

## Manual run
| ID | Result | Notes |
|---|---|---|
| PUB-03 | Pass | |
| ADM-06 | Pass after fix | by hand: the table at 390px. What failed, fixed in `<commit>` |

## Findings
Numbered: what happened, which case, the cause, and the fix or why it was left.

## Conditions
Anything about the environment that could have affected the result (a crashed worker, a shared database, a step
that could not be driven in the browser and how it was checked instead).
```
