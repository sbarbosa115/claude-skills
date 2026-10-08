## 5. Record: one file per issue, deduplicated, then the priority list

Record as you go, view by view, not from memory at the end.

### 5.1 Before filing: is it already there?

```bash
python3 ~/.claude/skills/qa-expert/scripts/qa.py status            # open issues, by priority
grep -ril "<a key word>" docs/qa/issues/*.md                       # search by view, endpoint, symptom
```

- **Same issue, still open:** update its `last_seen` to today and add the run to its History. Nothing new.
- **Same issue, marked fixed, back again:** set `status: open` (a regression), keep the id, add a History line.
- **Related but different** (same view, another cause): a new issue, with `related: [QA-00nn]`.

### 5.2 Filing a new one

```bash
python3 ~/.claude/skills/qa-expert/scripts/qa.py new --category=functional --severity=P1 \
  --view="Orders list" --title="Deleting the last order on a page shows an empty page"
```

It writes `docs/qa/issues/QA-00nn-<slug>.md` from `templates/issue.md` and prints the path. Fill every section:

- **Summary:** one sentence: what is wrong, for whom.
- **Steps to reproduce:** numbered, from a known state (which account, which seed data), precise enough that
  someone else gets the same result first time.
- **Expected / Actual:** expected cites its source (the flow doc, the design doc, a reference screen, the spec).
- **Evidence:** console or network excerpts, the response body, the width and theme, file:line in the code.
- **Suspected cause:** when the code shows it (file:line); otherwise leave it out. No fix written as code.
- Frontmatter: `category` (ui | functional), `severity` (P0–P3, by step 3.3 or 4.4), `confidence` (reproduced |
  code-read), `area`, `view`, `route`.

A finding about a whole pattern (the same wrong button on eight screens) is one issue listing every place, not
eight.

### 5.3 Re-check the open issues in scope

For each open issue whose view this run covered: follow its steps. Not reproducible on this commit → `status:
fixed`, `fixed_seen` = today, a History line with the commit. Still there → `last_seen` = today. Not reached this
run → leave it.

### 5.4 Close the run

```bash
python3 ~/.claude/skills/qa-expert/scripts/qa.py index     # regenerate docs/qa/issues/README.md (the priority list)
```

1. **The run file:** what was covered (views, roles, widths), what was not and why, the new issues, the repeats,
   the ones found fixed, the regressions, the "Unclear:" questions for the user.
2. **The coverage table** in `docs/qa/README.md`: "Last checked" and "Open issues" for each view covered.
3. **Report to the user:** counts by priority, the P0s and P1s in one line each with their ids, what was not
   covered, the questions. Offer to commit `docs/qa/` on a branch; do not commit unasked.
