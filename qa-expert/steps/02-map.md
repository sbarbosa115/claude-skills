## 2. Map the app into flows

The first run writes how the app works, before judging it: you cannot call behaviour wrong without writing down what
right is. Later runs keep the map current: a new or changed view updates its flow doc in the same run.

### 2.1 The inventory

From the router, the navigation and the API, list every view (a route, or a dialog or drawer big enough to be a
screen of its own) in `docs/qa/README.md`'s coverage table:

| View | Route | Role | Flow doc | Last checked | Open issues |
|---|---|---|---|---|---|

Group the views into areas (by the navigation, or by the domain: sign-in, catalog, orders, settings…). One flow doc
per area: `docs/qa/flows/<area>.md`, from `templates/flow.md`.

### 2.2 Each flow doc

Written from using the app and reading its code, in plain words a new tester could follow:

- **Purpose and who uses it**: the roles, and what each may and may not do here.
- **Views**: for each, what it shows, its states (empty, loading, populated, error, no permission), and every action
  on it with its result.
- **Flows**: the paths a user takes across views, step by step, with the expected result of each step (what is
  saved, what is shown, what is sent).
- **Rules**: validation (required fields, formats, limits), business rules (statuses and their transitions, prices,
  quotas, dates and time zones), access rules (who sees what; what another tenant gets).
- **Side effects**: emails, notifications, background jobs, outside calls.
- **Sources**: the route, the components, the API endpoints and handlers (file paths), so the next run starts fast.

Where the app's behaviour seems odd, write what it does, and file the oddity as an issue in step 5; do not write
the flow doc as if the bug were the design. Where the intended behaviour is unclear (the code and the spec disagree,
or neither says), write "Unclear:" with the question, and list it in the run report for the user.
