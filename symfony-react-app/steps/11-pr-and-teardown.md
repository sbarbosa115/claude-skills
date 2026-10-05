## 11. Pull request, then teardown after the merge

### 11.1 The pull request, once the definition of done passes

Only after `dod.py` passes (§10), and only from the feature base branch (an item of a split never opens one).
Mark it: `timeline.py start pr`.

1. **Write the body** to a file in the scratchpad: link the plan (or the PRD), summarise what changed per layer, link
   the regression run file (the smoke suite's attempts and the manual run) and the security audit file, paste
   `dod.py`'s output, and list what was not done.
2. **Open it:**
   ```bash
   python3 ~/.claude/skills/symfony-react-app/scripts/pr.py --title "<what the feature does>" --body-file <file>
   ```
   It checks `dod.py --quick` again, refuses uncommitted changes, pushes the branch, and opens the pull request against
   `main`/`master` with `gh` (or prints the one already open). **Without `gh`** (not installed or not logged in), it
   prints the GitHub link that opens the pull request form with the title filled in, and the body file to paste.
3. **Write the timeline into the PRD** once the link is ready: end the timeline and write its table into the
   feature's PRD (`docs/pdr/prd-<feature>.md`), commit it on the branch and push it, so the pull request carries it:
   ```bash
   python3 ~/.claude/skills/symfony-react-app/scripts/timeline.py end
   python3 ~/.claude/skills/symfony-react-app/scripts/timeline.py report docs/pdr/prd-<feature>.md
   git add docs/pdr/prd-<feature>.md && git commit -m "Timeline: how long each step took" && git push
   ```
   The `## Timeline` section holds one row per step (when it started, its active time without the pauses, its wall
   clock), the total, and for a split one row per item. Run again, it replaces the section. A feature without a PRD
   puts `timeline.py show`'s table in the pull request's body instead.
4. **Report the link** to the user: the pull request's URL, or the link to open it by hand, with the timeline's
   total. The feature is not finished until the user has one of the two.

Merging is the user's decision: never merge the pull request yourself.

### 11.2 Teardown, once the pull request is merged

The merge happens outside the session, so the teardown starts from a check, when the user says it is merged (or
asks to clean up):

```bash
python3 ~/.claude/skills/symfony-react-app/scripts/teardown.py feature/<name>          # what it would do
python3 ~/.claude/skills/symfony-react-app/scripts/teardown.py feature/<name> --yes    # do it
```

- It **refuses while the branch is not merged** into `origin/main`: the pull request is `MERGED` (with `gh`), or the
  branch's tip is in `origin/main`. A squash or rebase merge cannot be seen without `gh`: confirm it with the user,
  then add `--force`.
- It takes down **every Docker stack of the feature**, the base branch's and every item's of a split
  (`docker compose down --volumes --remove-orphans`: the feature's data goes too), removes their worktrees, and deletes
  the local base and item branches. Item branches are deleted only now, after the base branch is merged.
- A worktree with uncommitted changes is **kept and reported**, never forced: look at what is there and ask.
- The main checkout and remote branches are left alone (GitHub can delete the remote branch on merge).

Run it without `--yes` first and read the list: it is what will be deleted.
