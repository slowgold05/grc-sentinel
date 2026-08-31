# GRC Sentinel agent instructions

Read `PROJECT.md`, `CONVENTIONS.md`, and the relevant roadmap section before changing code.
The repository and tests are the source of truth: a status claim in `PROJECT.md` does not prove
that a feature exists.

For each task:

1. State the roadmap part, outcome, allowed files, and runnable definition of done.
2. Trace the existing flow and reuse its patterns before writing code.
3. Keep one active task; bundle only adjacent steps that share the same verification path.
4. Do not expand scope when a prerequisite is missing. Record the blocker and finish other
   safe work inside the task.
5. Run the smallest relevant test first, then the repository lint/type/build checks before
   committing.

Security rules in `PROJECT.md` section 6b are binding. Never invent compliance requirements,
control mappings, citations, or evidence. Use the `control-builder` skill for control knowledge
base work. Ollama is an untrusted processor, never an authority.

Do not edit applied migrations, imported source artifacts, or generated shared types. Add a new
migration or rerun the generator instead. Preserve unrelated user changes in the worktree.
