# PCI DSS 4.0.1 source review

Status: **detailed assurance scope model — not a legal-applicability ruleset**

PCI DSS is a contractual industry standard. GRC Sentinel records a confirmed assurance objective
and scope facts; it does not create a legal determination merely because payment data exists.

## Source identity

| Field | Value |
| --- | --- |
| Standard | Payment Card Industry Data Security Standard |
| Version | 4.0.1 |
| Publisher | PCI Security Standards Council |
| Classification | Contractual industry standard |
| Official library | <https://www.pcisecuritystandards.org/document_library/?class=pcidss&doc=pci_dss> |
| Outsourced merchant scope FAQ | <https://www.pcisecuritystandards.org/faqs/does-pci-dss-apply-to-merchants-who-outsource-all-payment-processing-operations-and-never-store-process-or-transmit-cardholder-data/> |
| Service-provider impact FAQ | <https://www.pcisecuritystandards.org/faqs/1580/> |
| Repository review date | 2026-09-01 |

## Intake facts and meaning

| Fact | Meaning | Unknown behavior |
| --- | --- | --- |
| `pci_entity_role` | Merchant, service provider, both, or another role requiring review | Scope remains unconfirmed |
| `pci_stores_account_data` | Entity stores cardholder data and/or sensitive authentication data | Needs review |
| `pci_processes_account_data` | Entity processes payment account data | Needs review |
| `pci_transmits_account_data` | Entity transmits payment account data | Needs review |
| `pci_can_impact_cde` | Systems or services can affect cardholder-data-environment security | Needs review, including service providers without direct handling |
| `pci_fully_outsourced` | Payment processing is represented as fully outsourced | Does not remove oversight or validation responsibility |
| `pci_cde_scope_confirmed` | People, processes, technology, connected systems, and data flows have been scoped | Unconfirmed scope blocks readiness claims |
| `pci_validation_method` | Candidate SAQ or ROC path | Must be confirmed with the compliance-accepting entity |

`handles_cardholder_data` remains as a compatibility summary. New workflows must use the separate
storage, processing, transmission, and CDE-impact facts.

## Decision boundary

- Direct storage, processing, or transmission is a PCI scope signal.
- Ability to impact CDE security is independently relevant, especially for service providers.
- Full outsourcing may reduce directly applicable requirements but does not erase merchant
  responsibilities for third-party oversight, agreements, responsibility allocation, or validation.
- The applicable validation method is not inferred from one checkbox. The user records a candidate
  method and must confirm it with the acquirer, payment brand, customer, or other
  compliance-accepting entity.
- Selecting PCI DSS creates an assurance objective. It must never create a legal determination.

## Requirement integration still required

- Validate every installed PCI control identifier and SCF mapping against PCI DSS 4.0.1.
- Store publisher/version provenance and licensing metadata; do not commit unlicensed standard text.
- Add role and validation-method profiles for SAQ A, A-EP, B, B-IP, C, C-VT, SAQ D, and ROC paths.
- Model third-party responsibility allocation and evidence without treating outsourcing as transfer
  of accountability.
- Drive scoped controls through coverage, gaps, risks, policies, export, and Audit Hub.
- Add an authenticated Selenium case proving the UI labels PCI as contractual assurance.
