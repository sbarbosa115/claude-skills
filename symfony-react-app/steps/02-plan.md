## 2. Plan the feature before writing code

A plan is short and written down. Put it in the PR description, or in `docs/pdr/prd-<feature>.md` when the feature
is big enough to need a product document.

**The plan is written by the most advanced model:** `fable`, or the most advanced one the Agent tool offers. A wrong
plan is paid for by every item built from it, so this is the one step that is never run a model down.

- **The session runs on that model:** it writes the plan itself.
- **The session runs on another model:** it launches one planning agent (agent type `Plan`, `model: "fable"`) and
  waits for it. The brief holds the user's request word for word, what the user already decided, and the files to
  read: the project's `README.md` and `CLAUDE.md`, this step and `steps/02b-split.md`. The agent returns the plan
  below and, when the feature is split, the whole PRD from `templates/split-plan.md`. It only reads: the session
  saves what it returns, runs `split.py plan` on it, and sends back to the same agent whatever the script refuses.

**The planner also decides the model of every agent that builds the plan** (§2b.4, "A model per item"): it fills
the split table's `Model` column, one model per item. Whoever launches the agents passes that model and does not
choose again. Only two things change it: the escalation in §2b.4, and the user.

The plan answers five questions:

1. **Who is it for and what do they do with it?** The role (and its URL space) and the job the feature does for
   them, in one or two sentences. Ask the user only what the code cannot answer.
2. **Where does it live?** On the backend, which bounded context owns the data it changes (§4.1). On the frontend,
   which FSD layer and slice (§4.2). A new screen is usually a tab or section of an existing page, not a new menu
   entry.
3. **Which layers does it touch?** Name them and skip the rest. Most features match one of these shapes:

   | Shape | Backend | Frontend |
   |---|---|---|
   | New thing a user manages | entity → migration → repository → command/handler → Input → Output → controller | entity slice → feature slice(s) → page/widget → route → menu → strings |
   | New field on an existing thing | entity + migration → Input → Output → controller (PATCH) | the form and the table that show it → strings |
   | New action on a row | command/handler → controller route → Output (if the response changes) | a feature slice with the button and its modal → strings |
   | New read-only view | query → Output → controller | widget/page → route → menu → strings |

4. **What is the nearest existing feature?** Open its files next to the ones you write and copy its *shape*: where
   it lives, how it is scoped, how it is tested. Do not copy its age. New code meets today's bar (§5, §6).
5. **How will it be verified?** List the tests you will write first (§4) and the cases you will add to the
   regression suite (§8), saying for each whether it is a smoke test (Playwright) or needs a person (§8.0).

Also list what you are deliberately leaving out. It goes in the README's "Known gaps" section at the end.

If the plan spans more than one bounded context or more than one new screen, consider splitting it into items that
can be built in parallel (§2b) before branching.
