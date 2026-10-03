import fs from 'node:fs';
import path from 'node:path';
import {
  test as base,
  expect,
  type Browser,
  type BrowserContext,
  type Page,
} from '@playwright/test';
import {emailTo} from './mail';

export {expect};

/** The accounts of a smoke run (e2e/prepare.sh creates the super admin; the owners come from the fixtures). */
export const SUPER_ADMIN = 'ana@llyner.com';
export const SEED_OWNER = 'pedro@example.com';

const AUTH_DIR = path.join(process.cwd(), 'e2e', '.results', 'auth');
let addresses = 0;

/**
 * A visitor address of its own for every test: the app's rate limits count per IP (the stack trusts
 * X-Forwarded-For during a smoke run), so one test's requests never use up another's allowance.
 */
function nextAddress(): string {
  addresses += 1;
  return `10.77.${Math.floor(addresses / 250) % 250}.${(addresses % 250) + 1}`;
}

/** The pathname of an absolute link from an email, so it is opened on the stack under test. */
export function pathOf(link: string): string {
  const url = new URL(link);
  return url.pathname + url.search + url.hash;
}

/**
 * Signs an email in to the admin the way a person does: asks for the link, reads it in the mail catcher, opens it.
 * The session is kept for the whole run (one link per email: asking twice within two minutes sends nothing).
 */
async function sessionOf(
  browser: Browser,
  baseURL: string,
  email: string,
): Promise<string> {
  const file = path.join(
    AUTH_DIR,
    `${email.replace(/[^a-z0-9]+/gi, '_')}.json`,
  );
  if (fs.existsSync(file)) {
    return file;
  }
  const context = await browser.newContext({
    baseURL,
    extraHTTPHeaders: {'X-Forwarded-For': nextAddress()},
  });
  const since = new Date(Date.now() - 2_000);
  const asked = await context.request.post('/api/v1/admin/sign-in-link', {
    data: {email, language: 'en'},
    headers: {Origin: new URL(baseURL).origin},
  });
  expect(asked.status(), `asking for ${email}'s sign-in link`).toBe(202);
  const mail = await emailTo(context.request, email, {since});
  const link = mail.links.find((l) => l.includes('/admin/sign-in/'));
  expect(link, `the sign-in link in ${email}'s email`).toBeTruthy();
  const page = await context.newPage();
  await page.goto(pathOf(link as string));
  await page.waitForURL((url) => !url.pathname.includes('/sign-in'));
  fs.mkdirSync(AUTH_DIR, {recursive: true});
  await context.storageState({path: file});
  await context.close();
  return file;
}

interface Fixtures {
  /** A page signed in to the admin as this email (an owner of a fixture business, or the super admin). */
  signedInAs: (email: string) => Promise<Page>;
}

export const test = base.extend<Fixtures>({
  // Every test is its own visitor (see nextAddress).
  // (Playwright wants the first argument destructured, even when nothing of it is used.)
  extraHTTPHeaders: async ({locale: _locale}, provide) => {
    await provide({'X-Forwarded-For': nextAddress()});
  },
  signedInAs: async ({browser, baseURL, viewport, locale}, provide) => {
    const contexts: BrowserContext[] = [];
    await provide(async (email) => {
      const storageState = await sessionOf(browser, baseURL as string, email);
      const context = await browser.newContext({
        baseURL,
        viewport,
        locale,
        storageState,
        extraHTTPHeaders: {'X-Forwarded-For': nextAddress()},
      });
      contexts.push(context);
      return context.newPage();
    });
    await Promise.all(contexts.map((c) => c.close()));
  },
});

/** A page's console errors, collected from now on: `expect(errors).toEqual([])` at the end of a view's test. */
export function consoleErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') {
      errors.push(message.text());
    }
  });
  page.on('pageerror', (error) => errors.push(error.message));
  return errors;
}

/** Types a message in a business page's chat and sends it. */
export async function say(page: Page, text: string): Promise<void> {
  const box = page.getByRole('textbox').last();
  await box.fill(text);
  await box.press('Enter');
}
