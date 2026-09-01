# MAS Technology Risk Management Notice source review

Status: intake and candidate-evaluation foundation implemented; activation remains protected
pending Singapore regulatory review.

## Authority and current notice set

- Publisher: Monetary Authority of Singapore (MAS)
- Authority reviewed: MAS *Frequently Asked Questions: Notice on Technology Risk Management*
- Official source: https://www.mas.gov.sg/-/media/mas-media-library/regulation/faqs/trpd/faqs---notice-on-technology-risk-management/faqs---notice-on-trm/faq---notice-on-technology-risk-management.pdf
- Current notice mapping recorded from FAQ Q1:

| Institution category | Notice |
| --- | --- |
| Licensed insurer or insurance agent | FSM-N03 |
| Bank | FSM-N05 |
| Credit or charge card issuer | FSM-N07 |
| Finance company | FSM-N09 |
| Merchant bank | FSM-N11 |
| Designated-payment-system, payment-service, or DPT entity in the stated scope | FSM-N13 |
| Money broker | FSM-N15 |
| Licensed credit bureau | FSM-N17 |
| Registered insurance broker | FSM-N19 |
| Capital-markets financial institution | FSM-N21 |
| Licensed financial adviser | FSM-N23 |
| Licensed trust company | FSM-N25 |

## Reviewed scope boundaries

- Institution category, licence or approval, and exact notice number are separate facts. The
  platform does not infer licence status from a company description.
- FAQ Q3-Q4 says institutions establish and document a framework for identifying critical
  systems and may conclude that none of their systems are critical. Those two facts remain
  separate in intake.
- The transition field exists to prevent a cancelled legacy notice from being treated as current.
  A reviewer must verify the applicable FSM notice and effective version before activation.

## Activation gate

Create one versioned source record per notice, using the current published notice rather than a
comparison or cancelled copy. A Singapore reviewer must approve institution coverage, exceptions,
transition dates, citations, and positive/negative/unknown golden profiles. Import only official
requirement text and identifiers with provenance; load only publisher- or SCF-sourced mappings.
Ollama must not select the notice or infer control equivalence.
