## 3. UI/UX audit, view by view

Measure each screen against **the app's own design**, not your taste: the design sources from step 1.2, and the
screens that already follow them best (pick one or two reference screens per area and name them in the run file).
A finding says which rule or which reference screen the view departs from.

### 3.1 Uniformity with the rest of the app

- **Tokens:** colours, font sizes, weights, radii, shadows and spacing come from the design tokens. Look in the view
  for literal values (`#hex`, `rgb(`, `px` sizes off the scale) in its styles; a literal that duplicates or nearly
  duplicates a token is a finding.
- **Components:** buttons, inputs, tables, cards, dialogs, tabs, badges and toasts come from the component library.
  A hand-made look-alike, or the same thing styled two ways on two screens, is a finding.
- **Layout:** the same page frame as its siblings (header, title, width, gutters, where the main action sits). The
  same kind of screen (a list, a form, a detail) is laid out the same way everywhere.
- **Patterns:** the same action has the same name, icon, colour and place on every screen (Save, Delete, Cancel,
  Back); destructive actions are confirmed the same way; filters, search, pagination and sort behave alike.
- **Copy:** the same term for the same thing everywhere; one tone; no placeholder text, no raw keys, no untranslated
  strings, no developer messages shown to users.

### 3.2 Each view on its own

- **States:** empty (with a way forward), loading (no layout jump), error (says what happened and what to do), long
  content (long names, many rows, big numbers wrap or truncate cleanly), no permission.
- **Phone (390px) and desktop:** no horizontal scroll, nothing cut off or overlapping, touch targets ≥ 44px, tables
  become something usable, dialogs fit, the keyboard does not hide the field being typed in.
- **Hierarchy:** one obvious primary action; headings in order; related things grouped; alignment on a grid.
- **Feedback:** every action shows that it worked or failed; disabled controls say why when it is not obvious.
- **Accessibility basics:** labels on inputs, alt text, visible focus, keyboard reachable, readable contrast
  (text against its background ≥ 4.5:1), no meaning by colour alone.
- **Themes:** if the app has dark mode, every screen in it, nothing unreadable or still light.

### 3.3 Severity for UI findings

- **P1:** the screen cannot be used on a supported width or theme (hidden action, unreadable text, overlap that
  blocks a control), or an accessibility failure that blocks a task.
- **P2:** a clear departure from the design system a user will notice (wrong component, off-brand colour, a layout
  unlike its siblings, a missing empty or error state, an inconsistent action).
- **P3:** polish (spacing off the scale, a near-duplicate colour, alignment, copy wording).

A UI finding is never P0.
