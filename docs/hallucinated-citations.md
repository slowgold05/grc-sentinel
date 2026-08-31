# Designing an LLM system where hallucinated citations are structurally impossible

Large language models are useful policy writers and unreliable compliance authorities. GRC Sentinel
uses a local Qwen model through Ollama, but the model never decides which law applies and never
gets permission to cite from memory. The surrounding architecture constrains what it can do.

## Applicability is deterministic

Company facts enter a versioned rules engine. A rule—not a prompt—decides whether a regulation
applies and stores the rule version and facts snapshot. Voluntary frameworks such as SOC 2,
ISO 27001, and NIST SP 800-53 are recorded separately as assurance objectives so they are not
misrepresented as laws.

## Retrieval creates a citation allowlist

Each policy section starts from a database template containing required control UUIDs. GRC Sentinel
retrieves the current control records and sends their stable codes and text to the model as
`ALLOWED_CONTROLS`. Company facts are explicitly delimited as untrusted data.

The model must return strict JSON. Pydantic rejects extra fields, empty statements, oversized
text, and malformed output. Schema validation limits the output's shape, but it does not establish
that a citation is real. That requires a plain set comparison:

```python
invalid = sorted(set(cited_control_ids) - set(retrieved_control_ids))
accepted = not invalid
```

If Qwen emits `FAKE-1`, the identifier is absent from the retrieval set and the whole output is
rejected before storage. A larger model cannot bypass this check, and a weaker model cannot make
it less correct.

## Evidence claims require literal evidence

Gap analysis uses embeddings to find the best uploaded-policy section for each required control.
Similarity produces only a candidate. The model classifies it as covered, partial, or missing and
must return an exact evidence quote.

GRC Sentinel then checks that the non-empty quote is a literal substring of the retrieved section.
The trusted control and chunk identifiers are assigned by application code rather than accepted
from model output. An uploaded document can contain prompt-injection instructions, but it cannot
make an invented quote pass the substring check.

## The remaining judgment is visible

A second structured model pass checks whether each generated statement faithfully implements its
supplied controls. This is intentionally advisory model judgment, not the citation security
boundary. Outputs remain draft compliance material requiring professional review.

The resulting trust chain is simple:

```text
versioned rules -> sourced controls -> bounded retrieval -> structured generation
                -> deterministic citation/evidence checks -> human review
```

GRC Sentinel currently indexes 4,233 controls and 4,354 sourced crosswalks, with every control embedded
locally. Its 30-profile HIPAA applicability evaluation scores 1.00 precision and 1.00 recall, and
the repository keeps the deterministic checks under automated tests. The important result is not
that the model hallucinates less. It is that unsupported citations cannot cross the storage
boundary.
