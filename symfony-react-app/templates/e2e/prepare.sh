#!/usr/bin/env bash
# Prepares this checkout's Docker stack for a smoke run (e2e/smoke.sh calls it): the database reset to the seed and
# the smoke fixtures, the super admin, the offline assistant and Maps import, an empty mail catcher, no rate limit
# already used. Run from anywhere inside the repository.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

console() { docker compose exec -T php php bin/console "$@"; }

# What a smoke run needs from the app, in a file of its own (gitignored): the offline assistant and Maps import (no
# key, no cost), and X-Forwarded-For trusted so every test is its own visitor for the rate limits. Development only.
ENV_FILE=backend/.env.dev.local
MARK='# Written by e2e/prepare.sh for smoke runs.'
if [ -f "$ENV_FILE" ] && ! grep -qF "$MARK" "$ENV_FILE"; then
    echo "$ENV_FILE exists and was not written by this script: move its settings to backend/.env.local first." >&2
    exit 1
fi
printf '%s\nCHAT_ASSISTANT=offline\nMAPS_IMPORT=offline\nTRUSTED_PROXIES=REMOTE_ADDR\n' "$MARK" > "$ENV_FILE"

echo "· database: drop, create, migrate"
console doctrine:database:drop --force --if-exists -q
console doctrine:database:create -q
console doctrine:migrations:migrate -n -q

echo "· seed and smoke fixtures"
console app:customer:import fixtures/customers/llyner.json --silent
if compgen -G "backend/fixtures/customers/e2e/*.json" > /dev/null; then
    for file in backend/fixtures/customers/e2e/*.json; do
        console app:customer:import "fixtures/customers/e2e/$(basename "$file")" --silent
    done
fi
console app:account:super-admin ana@llyner.com -q

echo "· cache, rate limits, worker, mail catcher, uploaded files, saved sessions"
console cache:clear -q
console cache:pool:clear cache.rate_limiter -q
# The worker keeps the old code and settings until it restarts.
docker compose up -d worker > /dev/null 2>&1
docker compose restart worker > /dev/null 2>&1
docker compose exec -T php sh -c 'wget -q -O /dev/null --method=DELETE http://mailpit:8025/api/v1/messages 2>/dev/null || curl -s -X DELETE http://mailpit:8025/api/v1/messages > /dev/null'
rm -rf backend/e2e/.results/auth
echo "· ready"
