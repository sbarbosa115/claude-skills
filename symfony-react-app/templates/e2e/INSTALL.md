# Starter files for the smoke suite (steps/08-regression-run.md §8.1)

Copied from a working project (Tacoma: Symfony + React, Mailpit, an offline stand-in for the LLM). Adapt the lines
marked by the project's names before the first run.

| File | Goes to | Adapt |
|---|---|---|
| `playwright.config.ts` | `<app>/playwright.config.ts` | the viewport the app is used on |
| `support/test.ts`, `support/mail.ts` | `<app>/e2e/support/` | the accounts (`SUPER_ADMIN`, `SEED_OWNER`) and how a user signs in (`sessionOf`: here an emailed link) |
| `support/globalSetup.ts` | `<app>/e2e/support/` | the seed record it checks, and the check that outside services are stood in for |
| `prepare.sh` | `<app>/e2e/prepare.sh` | the seed command, the fixture folder, the accounts, the env settings that switch on the stand-ins |
| `smoke.sh`, `README.md` | `<app>/e2e/` | paths, and the README's table if the project needs another split |

Also: an `e2e` service in `docker-compose.yml` (image `mcr.microsoft.com/playwright:v<the @playwright/test version>`,
the app folder mounted, `E2E_BASE_URL` and `MAILPIT_URL` pointing at the stack's services, behind a profile),
`@playwright/test` and `@types/node` as dev dependencies, `e2e/**/*` and the config in `tsconfig.json`, and
`/e2e/.results/` in `.gitignore`. Rate limits counted per IP need the stack to trust `X-Forwarded-For` during a
smoke run (`prepare.sh` sets it for development only).
