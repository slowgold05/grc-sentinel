# DORA source review

Status: intake and candidate-evaluation foundation implemented; activation remains protected
pending legal review.

## Authority and version

- Publisher: European Parliament and Council of the European Union
- Instrument: Regulation (EU) 2022/2554 (DORA), CELEX `32022R2554`
- Official text: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R2554
- Application date: 17 January 2025 (Article 64; also confirmed by the EBA)

## Reviewed scope boundaries

- Article 2(1) enumerates the covered financial-entity categories. The intake preserves the
  category instead of relying on one generic EU-financial-entity checkbox.
- Article 2(3) excludes specified small or exempt entities; Article 2(4) also permits a Member
  State exclusion for specified credit institutions. The intake records the claimed exclusion
  without treating it as approved legal advice.
- ICT third-party service providers are not automatically financial entities. Provider status is
  therefore separate from Article 2 entity scope.
- Critical ICT third-party-provider designation is a separate Article 31 oversight status made by
  the ESAs. Group context is retained because Article 31 applies designation criteria to services
  provided by the group as a whole.

## Activation gate

Before adding a protected executable ruleset, a reviewer must approve the category and exclusion
interpretation, non-EU nexus treatment, citations, effective dates, and positive/negative/unknown
golden profiles. Requirement text must be imported from an official machine-readable EUR-Lex
artifact with article identifiers and provenance; mappings must be publisher- or SCF-sourced.
Ollama must not decide scope, exclusions, designation, or control equivalence.
