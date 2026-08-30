# Engineering Conventions

- Keep business logic pure and typed with Pydantic models at boundaries. Keep HTTP, database, and model-provider I/O at the edges.
- Routers validate, call one service, and return. Services do not import FastAPI.
- Load environment values only in `ruleset/config.py`; never log secrets or sensitive bodies.
- Use SQLAlchemy statements or static SQL with bound parameters. Never interpolate SQL.
- Set `app.org_id` inside every tenant transaction. RLS is mandatory on every tenant-owned table.
- Raise named domain errors. Never swallow broad exceptions.
- Log one structured event per stage with identifiers and counts, never customer content or prompts.
- Treat uploads, fetched pages, and model output as hostile. Validate size, type, schema, and allowed references.
- Public functions require docstrings. Non-trivial logic requires the smallest runnable test.
- Dependencies and actions are pinned. A high-severity audit finding blocks delivery.
- Applied migrations are immutable; corrections use a new migration.
- Rulesets and source catalogs are versioned data. Applicability and citation verification contain no randomness or LLM calls.
