# Roadmap

[Overview](../README.md) · [Contribution proposals](GOOD_FIRST_ISSUES.md) · [Evaluation protocol](EVALUATION_PROTOCOL.md)

**Destination:** a reproducible answer to whether an evidence-grounded Council outperforms a strong single-model baseline under a comparable total budget.

**Starting point:** a deliberately limited, offline evidence-audit core. The stages below are a development proposal, not a delivery schedule or authorization for live inference.

| Stage | Status | Focus | Evidence needed to advance |
| --- | --- | --- | --- |
| **R0 — Contributor preview** | Current experimental source snapshot | Offline core, synthetic fixtures, demo, licensing and contributor workflow. | Local/CI checks, selected-file privacy and ownership review, explicit publication decision. |
| **R1 — Evidence interfaces** | Proposed | Clear acquisition/completeness contracts, portability, source-consistency tests and bounded report presentation. | Reproducible negative regressions with positive controls; no weakening of provenance rules. |
| **R2 — Controlled model adapter** | Proposed; not included in R0 | Explicit inputs, bounded resources, auditable outputs and defined failure handling. | Adapter design review and cost accounting before model-backed experiments. |
| **R3 — Fair comparison** | Research plan; not completed | Preregistered, cost-matched Council versus strong single-model evaluation. | Frozen protocol, independent adjudication, held-out cases and reported uncertainty. |
| **Later** | Exploratory | GUI, additional backends, performance and maintainability. | Demonstrated need without compromising evidence or evaluation integrity. |

## Start without waiting for model infrastructure

The [contribution guide and task index](GOOD_FIRST_ISSUES.md) cover work possible now: an incomplete-evidence demo, cross-platform tests, an evidence-result contract, source consistency, a report renderer, evaluation design and newcomer documentation. Six directions have open GitHub Issues; the evidence-result contract remains a design proposal.

## What is not a release milestone

More agents, a larger test count or an attractive demo do not establish comparative reliability. Claims of Council superiority require the [evaluation protocol](EVALUATION_PROTOCOL.md), including total resource use and failed runs.

Private holdouts remain separate from contributor development. A public release must use selected, reviewed source and a clean history; publishing private development history is not part of this roadmap.
