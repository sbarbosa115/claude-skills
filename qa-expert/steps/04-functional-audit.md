## 4. Functional audit, view by view

Use each view as each role would, following its flow doc, then try to break it. Read its handler code alongside: the
browser shows symptoms, the code shows causes and the cases the screen hides.

### 4.1 Use it as intended

Every flow in the flow doc, end to end, with each step's expected result checked: what the screen says, what is
saved (reload and look again), what another view shows of it (a list's count, a dashboard's total, the public page),
what is sent (the email in the mail catcher). A step whose result differs from the flow doc is a finding, or the
flow doc was wrong: decide which, and fix the doc if so.

### 4.2 Try to break it

- **Input:** empty, spaces only, too long, the maximum and one past it, zero and negatives, decimals, other
  formats (dates, phones, emails, URLs), unicode and emoji, HTML and script text (shown as text, never run),
  pasted text with line breaks. Server-side validation agrees with the form's.
- **Actions:** double-click submit (one record, not two), submit while loading, back and forward, refresh mid-flow,
  a deep link straight into step 3, two tabs editing the same record, a session that expired.
- **Access:** signed out, a role without the right, another tenant's record by changing the id in the address or
  in an API call (expect 404 or 403, and no data in the body), hidden buttons whose endpoints still work.
- **State and logic:** status transitions that should not be allowed, totals and counts that disagree, dates around
  midnight and time zones, pagination edges (last page, one item, deleting the last item of a page), sort and
  filter combined, undo or cancel leaving things half-done.
- **Failure:** an outside service down or slow (the stand-in's failure mode, or the network panel's offline), a
  server error: the user sees a useful message and nothing is lost or half-saved.
- **Console and network:** any JS error, failed request, 500, or slow call (> 2s) during normal use is a finding.

### 4.3 Read the code for what the screen hides

For the view's endpoints: missing authorization checks, validation only on the client, a query not scoped to the
tenant, data in a response the UI does not show (contact details, internal fields), unhandled exceptions, off-by-one
and rounding, race conditions, a job or email that fails silently. Reproduce what you can; what you cannot is filed
with `confidence: code-read`.

### 4.4 Severity for functional findings

- **P0:** data loss or corruption, a security or privacy leak (another tenant's data, a role bypass, stored XSS),
  money wrong, or a core flow that cannot be completed by anyone.
- **P1:** a main flow broken for some users or inputs, wrong results a user would rely on, a crash or 500 on a
  normal path, an error with no way out.
- **P2:** a secondary flow broken, missing validation with a workaround, a confusing or misleading result, a console
  error with no visible effect yet.
- **P3:** minor: an edge case few will meet, a message worded wrong, a small inefficiency.
