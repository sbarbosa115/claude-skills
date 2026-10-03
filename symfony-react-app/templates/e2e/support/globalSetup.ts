import {request} from '@playwright/test';

/**
 * Before any spec: the stack answers, and it was prepared for a smoke run (e2e/prepare.sh): the offline assistant,
 * so no spec ever calls OpenAI, and the seed.
 */
export default async function globalSetup(): Promise<void> {
  const baseURL = process.env.E2E_BASE_URL ?? 'http://localhost:8080';
  const api = await request.newContext({baseURL});
  const seed = await api.get('/api/v1/customer/llyner');
  if (!seed.ok()) {
    throw new Error(
      `The stack at ${baseURL} has no seed business (GET /api/v1/customer/llyner answered ${seed.status()}). Run e2e/smoke.sh, which prepares it.`,
    );
  }
  const reply = await api.post('/api/v1/customer/llyner/chat', {
    headers: {'X-Forwarded-For': '10.99.0.1'},
    data: {
      session: null,
      message: {id: 1, role: 'user', type: 'text', text: 'ping'},
    },
  });
  const text = reply.ok() ? JSON.stringify(await reply.json()) : '';
  if (!text.includes('(Offline assistant)')) {
    throw new Error(
      'The stack is not using the offline assistant (CHAT_ASSISTANT=offline). Run e2e/smoke.sh, which prepares it: the smoke suite never calls OpenAI.',
    );
  }
  await api.dispose();
}
