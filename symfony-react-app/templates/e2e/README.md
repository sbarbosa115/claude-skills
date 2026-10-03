# The smoke suite (Playwright)

The simple cases of [`docs/tests/ui-regression.md`](../../docs/tests/ui-regression.md), run by a script against this
checkout's Docker stack. It runs **before** anything is checked by hand in the browser: a failure here is recorded,
fixed and the suite run again until it is green; only then does the manual (Chrome) run of the complex cases start.

```bash
backend/e2e/smoke.sh                  # prepare the stack (reset to the seed) and run everything
backend/e2e/smoke.sh ordering         # one spec file
SMOKE_KEEP_DATA=1 backend/e2e/smoke.sh -g "ADM-06"     # one case, without resetting the stack
```

`prepare.sh` drops and recreates the dev database, imports the seed and `fixtures/customers/e2e/*.json`, makes
`ana@llyner.com` the super admin, switches the stack to the offline assistant and Maps import
(`backend/.env.dev.local`), empties the mail catcher and the rate limits. Reports: `e2e/.results/` (gitignored).

## What is a smoke case, and what stays manual

| Smoke (here)                                                                     | Manual (the Chrome run)                                                                |
| -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| A view opens and shows the right things, with no console error                   | Anything judged by eye: layout at 390px, themes, brand colours, motion                 |
| A straightforward create / edit / remove with a clear result                     | Timing and feel: the carousel, the scroll position, typing while the assistant answers |
| Access rules: signed out, another owner's business, a feature switched off       | A real outside service: OpenAI, Google, Apify, S3, DynamoDB                            |
| A form's validation messages                                                     | Long stories with several actors: an order through every status with its emails        |
| A simple chat flow with the offline assistant; an email read in the mail catcher | What only the database, a log or a console command can prove                           |

A case that mixes both is split: the action is tested here, and the case stays in the manual run for the rest.

## Conventions

- **One spec per area**, each test named by its case: `test('ORD-01 · the "Create Order" pill starts the order', …)`.
  A case that needs several tests shares the ID: `'ADM-06 · products: add'`, `'ADM-06 · products: remove'`.
- **In the suite**, a covered case gets a line right under its title: ``Smoke: `e2e/ordering.spec.ts`.`` when the
  script covers all of it, or ``Smoke (part): `e2e/…` covers …; by hand: ….`` when part stays manual. A case's ID
  and text are never removed.
- **Import from `./support/test`**, not from `@playwright/test`: every test is its own visitor for the rate limits,
  and `signedInAs(email)` gives a page signed in to the admin through the emailed link (one link per email per run).
- **Each spec works on its own business**, from `fixtures/customers/e2e/<area>.json` (the seed's shape, with
  `features` and an `owner.email` of its own): a spec that changes `llyner` breaks the specs after it. Read-only
  checks may use `llyner`. One worker, files in alphabetical order, and no test may depend on another file's.
- **A test sets up what it needs** through the UI or `page.request` (the session's cookies travel with it; a write
  under `/api/v1/admin` needs the `Origin` header of the site).
- **Find things as a person does**: `getByRole`, `getByLabel`, `getByText`. No CSS classes, no `waitForTimeout`:
  `expect(...)` waits by itself. Emails: `emailTo(page.request, address, {subject})` from `./support/mail`.
- **No OpenAI, Google, Apify, S3 or DynamoDB.** The offline assistant answers by what it was offered:
  `Conversation\Infrastructure\Offline\OfflineAssistant`.
- A spec passes `npm run lint`, `npm run typecheck` and Prettier, like the rest of the frontend.
