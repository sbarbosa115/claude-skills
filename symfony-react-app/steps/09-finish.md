## 9. Finish

- **Docs:** a row in the README's API reference for every new endpoint (path, methods, filters, status and error
  codes). Add a "Data model decisions" bullet for a real decision (the *why*), and a "Known gaps" bullet for what
  was left out. If the project has user help articles, add or update the guide for the roles that use the feature.
- **Renamed a word the user sees?** Grep every place it lives (i18n, email translations, templates, tests, help)
  and change them together.
- **Stack changes** (new env var, cron line, queue message, feature flag) are documented where the deploy reads
  them and work on the production host.
- **CI runs the same gate.** If the project has no workflow, install `templates/ci.yml` as
  `.github/workflows/ci.yml` (it runs the style checks, the analysers, the test suites and the smoke suite in the
  project's Docker stack). A check that only runs locally will stop being run.
- **Then** the definition of done (§10), and only once it passes, the pull request and, after the merge, the
  teardown (§11).
