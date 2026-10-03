# <Feature name>

<!--
    A PRD for a feature built in parallel items (steps/02b-split.md). Save as docs/pdr/prd-<feature>.md; <feature>
    is the base branch's name without "feature/". `split.py plan` reads the table under "## Split".
-->

## What it is for

Who uses it (the role and its URL space) and the job it does for them, in two or three sentences.

## Plan

- **Owning contexts (backend):** …
- **FSD slices (frontend):** …
- **Nearest existing feature to copy the shape of:** …
- **Left out on purpose:** … (goes to the README's "Known gaps")

## Contract (item 0)

What item 0 fixes before the others start: entities and the migration, repository ports, the Output/Input DTOs of
every endpoint (and their JSON), the i18n prefixes, CSS files and regression-suite sections each item owns.

## Split

<!--
    One row per item. Slug: lowercase letters, digits and dashes; it names the branch (feature/<feature>-<slug>) and
    the worktree. "Depends on": the # of the items that must be merged first (comma-separated), or —. "Browser cases":
    the ID range the item adds to docs/tests/ui-regression.md (e.g. ORD-06 – 09), or —. "Model": the model the
    item's agent runs on (haiku, sonnet, opus or fable), set by the planner for every item by what the item builds
    (steps/02-plan.md, steps/02b-split.md §2b.4). Item 0 is built by the coordinator and has none.
-->

| # | Slug | Item | Owns (context / slice, files) | Tests first | Browser cases | Depends on | Model |
|---|---|---|---|---|---|---|---|
| 0 | contract | Schema, ports, DTOs, types | … | … | — | — | — |
| 1 | … | … | … | … | … | 0 | sonnet |

## Decisions

Anything the items must agree on that the code does not show yet (names, states, error codes, copy).
