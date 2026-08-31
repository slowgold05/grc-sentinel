---
name: control-builder
description: Import, map, embed, or validate GRC controls and framework knowledge from authoritative machine-readable sources. Use for OSCAL, SCF, NIST, SOC 2, ISO identifiers, regulation-to-control mappings, and control knowledge-base changes; not for ordinary policy drafting or UI work.
---

# Control Builder

Build traceable control data; do not ask a model to recall compliance requirements.

## Source rules

- Prefer an official publisher's machine-readable source. Record its publisher, version, and URL.
- Ingest NIST controls from OSCAL and framework crosswalks from SCF using the existing `kb/`
  parsers. Extend those parsers instead of adding hand-maintained duplicates.
- Store ISO clause identifiers and licensed-source metadata only; never copy ISO control text.
- Model laws and mandatory regulations separately from voluntary assurance frameworks.
- Do not infer a crosswalk because two controls sound similar. Persist only sourced mappings;
  label any explicitly requested heuristic as inferred and keep it out of legal applicability.

## Workflow

1. Inspect the target framework, existing schema, parser, fixtures, and callers.
2. Define the expected framework version, stable identifiers, provenance, and one known mapping
   or control as the acceptance case.
3. Parse and schema-validate source data before persistence. Upserts must be idempotent.
4. Embed validated control text with the configured Ollama embedding model. Embeddings support
   retrieval; they never establish applicability or equivalence.
5. Run the relevant ingestion test, `python -m ruleset.kb.validate_kb`, backend tests, and Ruff.
6. Report imported counts, source version, integrity findings, and any licensing limitation.

Generated policy statements may cite only control IDs in their retrieval context. Keep citation
and evidence checks deterministic, and reject unsupported IDs rather than repairing them with AI.
