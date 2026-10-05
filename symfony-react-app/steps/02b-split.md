## 2b. Split a big feature into parallel items

Most features are built straight through (§3 onwards). Split one only when the plan shows **more than one bounded
context or more than one new screen**, and the parts can be named so that no two of them change the same aggregate
or the same screen. A split costs a merge per item and a coordinator's time: for a feature one person would build in
a day or two, it is slower than building it in one go.

The flow of a split:

```
feature/<name> (the base branch, from fresh origin/main)
  ├─ item 0, the contract, built on it alone
  ├─ feature/<name>-<slug> per item, in parallel: test-first, its own tests, the gate
  │    └─ merged back into the base branch, cheap checks only (migrations, container, typecheck)
  └─ barrier: wait until every item is merged
       → main merged in once → gate → full PHPUnit + Vitest → security audit → verify
       → regression run → finish → definition of done → one PR (§11)
       → after the user merges it: every stack of the feature torn down (§11.2)
```

### 2b.1 Contract first: item 0

Parallel branches of this stack collide in a few places, always the same ones: the database schema, the API contract
(`openapi.json`, `api.d.ts`), and the shared files every screen touches. **Item 0 takes the collisions out before
anything runs in parallel.** It is built on the feature base branch itself (§3), alone, and holds:

- the new entities and value objects, their mapping and **the migration** (on the dev and test databases);
- the repository ports (and Doctrine adapters) the other items will call;
- the Output DTOs (and Input DTOs) of every new endpoint, with the controller routes returning a fixed example or
  `501`, and the regenerated `openapi.json` + `api.d.ts`, so the UI items build against real types;
- the i18n namespaces, CSS files and regression-suite sections the items will fill (empty, with a comment naming
  the item that owns each);
- **a no-op handler for every new domain event**, when the event bus refuses an event without one (Messenger's
  `NoHandlerForMessageException`): otherwise the item that publishes an event fails until the item that handles it
  merges. The handling item replaces the no-op.

Its tests cover the domain rules it adds and the shape of each response. When it is green and committed on the base
branch, the other items start from it.

### 2b.2 Cutting the rest

- **One item per bounded context on the backend, one per FSD slice (feature, widget or page) on the frontend.** An
  endpoint's use case and the screen that calls it may be one item or two; two is better when the screen is big.
- **Never two items on the same aggregate, the same screen or the same component.** If they must, they run one after
  the other (`Depends on`), not side by side.
- **Each item owns its files.** The plan names them, and an item that finds it must change another item's file stops
  and tells the coordinator: that is a missed dependency, and the plan changes, not the other branch.
- **Shared files are split up front:** each item gets its i18n key prefix, its CSS file or block, its README API rows,
  and **its range of regression case IDs** (`ORD-06 – 09`), so two branches never take the same number.
- **A migration after item 0** is allowed only for a table the item alone owns (named in the plan). A change to a
  shared table goes back to the coordinator as a new contract item (`0b`), merged before the items that need it.
- **Generated files are never merged by hand.** When `openapi.json`/`api.d.ts` conflict, take either side, then
  regenerate them on the merged code (§4.1).

### 2b.3 The split table

The table goes in the PRD (`docs/pdr/prd-<feature>.md`, from `templates/split-plan.md`), under `## Split`:

```markdown
| # | Slug | Item | Owns (context / slice, files) | Tests first | Browser cases | Depends on | Model |
|---|---|---|---|---|---|---|---|
| 0 | contract | Schema, ports, DTOs, types | Ordering/Domain, migration, Output DTOs, api.d.ts | OrderLineTest, response shapes | — | — | — |
| 1 | orders-api | Owner lists and marks orders | Ordering/Application + UI/Http | OrderListApiTest (owner, other tenant 404) | — | 0 | opus |
| 2 | orders-ui | Orders tab in the dashboard | widgets/order-list, features/mark-handled | OrderList.test.tsx | ORD-06 – 09 | 0 | sonnet |
| 3 | orders-email | Daily digest email | Ordering/Application/EventHandler, emails.* `digest.` | DigestTest | ORD-10 | 1 | sonnet |
```

`scripts/split.py plan <prd>` checks the table (item 0 first, known dependencies, no cycles, no case ID range used
twice, a known model) and prints the **waves**: the items that can run at the same time, each with its model.
Items 1 and 2 above are wave 1; item 3 is wave 2, after item 1 merges.

**How many at once:** each item runs its own Docker stack (§7.1), a few GB of RAM each, so three or four at a time on
one machine. Browser checks share one browser: items verify their screens one at a time.

### 2b.4 Running the items

`scripts/split.py start <prd> [slug… | --wave=N]` creates, for each item, the branch `feature/<feature>-<slug>` from
the base branch, its worktree `../<repo>-<feature>-<slug>`, and a gitignored `.env` with free host ports; it records
the base branch in git config (read by `dod.py --item`) and prints the item's model. `split.py status <prd>` shows,
per item, its worktree, commits and whether it is merged.

**A model per item.** An agent launched without a model runs on the coordinator's, and a wave of them on the top
model spends the session's budget in minutes. The `Model` column says what each item runs on. The planner (§2, the
most advanced model) fills it for every item, by what the item builds, not by its size:

| Model | The item is | Examples |
|---|---|---|
| `haiku` | Mechanical: no rule to decide, the result is checked by the gate alone | Copy and i18n keys, README and help rows, a rename, CSS for a screen that exists |
| `sonnet` | Well specified, and the same shape as a feature that exists | A CRUD endpoint on an aggregate from item 0, a list or form screen built from the shared UI, an email, a command |
| `opus` | New rules or more than one moving part | New domain invariants, a voter or tenant boundary, money, a state machine, the queue and retries, an external API, a screen with real client state |
| `fable` | So hard a wrong turn costs more than the model | Rarely an item: if it needs this, ask whether it belongs in item 0 or to the coordinator |

Item 0 and the merges stay with the coordinator, on the session's model. When an item fits two rows, take the
cheaper one and write its risk in the PRD's "Decisions": an agent that fails the gate twice on the same problem, or
reports that it is stuck, is relaunched one model up on the same worktree (its commits stay). Do not start a whole
wave a model up "to be safe", and do not launch an agent on a model the table does not give it.

Two ways to run the items; pick one per feature:

| | Subagents (one coordinating session) | One session per item |
|---|---|---|
| How | The coordinator launches one agent per item with `split.py prompt <prd> <slug>` as its prompt and the item's model as the agent's `model`, all of a wave at once | Open a Claude session in each item's worktree on the item's model (`claude --model <model>`) and paste its brief |
| Good for | Items that are well specified and mostly backend or logic | Items with UI judgement, or that need the user's decisions while built |
| Watch | Agents do not share what they learn; the coordinator reads each report before merging. An agent's shell may start in the main checkout: every command `cd`s into the item's worktree | The user relays questions; the coordinator still does the merges |

**What the coordinator does for every item:** it reads the report and merges. Items cannot merge the base branch
into their own branch (the permission system refuses `git merge` to agents), so an item is checked against the base
commit it was cut from, and the coordinator resolves any overlap while merging, on the base branch.

**An item's "done" is short on purpose.** The whole suites, the browser and the regression run are what make an
item wait, and they prove little before the items meet, so they run **once, on the base branch, after every item is
merged** (§2b.6). Either way of running it, an item:

- builds test-first (§4) and runs **its own tests** (its test files: `bin/phpunit tests/Functional/Api/<X>Test.php`
  or `--filter`, `npx vitest run <its files>`), never the whole PHPUnit or Vitest suite, the smoke suite or `dod.py`;
- passes `gate.sh` (§5): lint and type errors are cheap to fix in the item and costly to untangle after many merges;
- writes its regression cases into the suite (in its ID range), the simple ones as smoke tests in a spec file of its
  own, which it does not run;
- passes `dod.py --item`: the branch, the gate, its migration and the regenerated types (it leaves the suites to the
  base branch);
- does not open its screens in the browser, record a run or run the security audit.

It reports back, and is ready to merge.

### 2b.5 Merging

The coordinator merges each finished item into the base branch (never into `main`), in dependency order, and after
each merge runs only the **cheap checks** that say the merge itself is sound, so a broken merge is caught while it is
still clear which item broke it:

```bash
cd ../<repo>-<feature>                           # the base branch's worktree
git merge --no-ff feature/<feature>-<slug>
# conflicts in openapi.json / api.d.ts: regenerate, never edit
docker compose exec php php bin/console doctrine:migrations:migrate -n          # and --env=test
docker compose exec php php bin/console cache:warmup                            # the container still builds
docker compose exec node npm run -s typecheck                                   # the merged UI still type-checks
```

No gate, no PHPUnit, no Vitest between merges: they run once, at the barrier. A merge whose cheap checks fail is fixed
on the base branch right away, before the next merge. When a wave is merged, the next wave starts from the updated
base branch (`split.py start --wave=N`).

**Stop each merged item's stack** (`docker compose stop` in its worktree) as soon as it is merged; **keep its
worktree and branch** until the base branch is merged into `main`: `split.py status` knows an item is merged by its
branch, and `teardown.py` removes them all then (§11.2).

**The base branch stays frozen while items are built:** do not merge `main` into it between merges, so every item of a
wave is cut from, and merged into, the same code. `main` comes in once, at the barrier. If an item truly needs
something that just landed on `main`, merge it between waves, never in the middle of one.

Clearing the Symfony cache while the stack's worker runs kills the worker the next time it loads a service (a queued
email is then stuck until Messenger's redelivery timeout): restart the worker after `cache:clear`.

### 2b.6 The barrier, then the base branch as one feature

The coordinator's timeline marks the split's phases (`timeline.py start contract`, `build` when the first wave
starts, `merge`, `barrier` while it waits on items, then the steps below); each item's own time comes from git in
the report (its branch's creation to its merge), so item agents record nothing.

The base branch waits here until **every** item of the split is merged: `split.py status <prd> --check` exits 0
(it prints the items still open otherwise, and `dod.py` fails while one is). Nothing below starts before that.

Then, on the base branch's worktree and its own stack, in this order:

1. **Bring `main` in once:** `git fetch origin && git merge origin/main`, then migrations on dev and test.
2. **Gate** (§5): `gate.sh`. It comes before the suites because its `--fix` (PHP-CS-Fixer's risky rules, Prettier,
   ESLint) changes code the suites must then test.
3. **The full local tests:** the whole PHPUnit suite and the whole Vitest suite, green.
4. **Security audit** (§6) of the whole feature (`audit.py` against `main`). If its fixes change code, run step 3
   again.
5. **Verify** (§7): every item's screens opened in the browser on this stack.
6. **Regression run** (§8): the whole smoke suite until green, then the manual run.
7. **Finish** (§9): docs and CI.
8. **Definition of done:** `dod.py` (without `--item`).
9. **One pull request** from the base branch (§11.1): `pr.py` opens it, or prints the link to open it by hand.
10. **After the user merges it:** `teardown.py` takes down the base branch's and every item's stack and worktree
    (§11.2).

**Fixes go on the base branch.** Item worktrees are stale by now and are not reopened: the coordinator fixes what the
suites, the audit or the runs find on the base branch, or launches an agent in the base branch's worktree.

**Which item broke it?** When a failure in step 3 is not obvious, bisect over the merges only:
`git bisect start --first-parent <base-branch> <commit-before-the-first-item-merge>`, with the failing test as the
check at each step. The commit it names is the merge of the item that brought the failure.
