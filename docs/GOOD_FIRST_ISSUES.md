# Find your first contribution

[Overview](../README.md) · [Contribution guide](../CONTRIBUTING.md) · [Roadmap](ROADMAP.md)

**Seven scoped directions for the R0 core.** Six are tracked in the GitHub Issues below. The evidence-result API contract remains a design proposal, not an open Issue. These tasks are planned improvements, not newly confirmed defects.

All work uses synthetic or public fixtures. No model service, protected holdout or private source project is needed. Comment on an existing Issue before starting to avoid duplicate work.

| # | Direction | GitHub task | Suggested entry point |
| --- | --- | --- | --- |
| 1 | [Incomplete-evidence demo](#1-offline-incomplete-demo) | [Issue #2](https://github.com/Pipirasas/AI-Council-Experimental/issues/2) | First contribution: examples and tests |
| 2 | [Path and Unicode fixtures](#2-cross-platform-path-and-unicode-fixtures) | [Issue #3](https://github.com/Pipirasas/AI-Council-Experimental/issues/3) | First contribution: Python testing |
| 3 | [Evidence-result contract](#3-evidence-result-api-contract) | Design proposal; no Issue yet | API design and test contracts |
| 4 | [Source consistency](#4-source-snapshot-consistency-tests) | [Issue #4](https://github.com/Pipirasas/AI-Council-Experimental/issues/4) | Reproducibility and concurrency testing |
| 5 | [Bounded report renderer](#5-bounded-report-rendering) | [Issue #5](https://github.com/Pipirasas/AI-Council-Experimental/issues/5) | Deterministic presentation |
| 6 | [Cost-matched baseline design](#6-cost-matched-baseline-design) | [Issue #6](https://github.com/Pipirasas/AI-Council-Experimental/issues/6) | Evaluation research |
| 7 | [Newcomer quickstart validation](#7-newcomer-quickstart-validation) | [Issue #7](https://github.com/Pipirasas/AI-Council-Experimental/issues/7) | First contribution: documentation |

## 1. Offline INCOMPLETE demo

**Scope:** `examples/` and synthetic tests only. Add a companion to the current [arithmetic demo](../examples/offline_demo.py).

**Acceptance:** missing evidence remains `INCOMPLETE`; the output includes a reason code and warning. Include a fulfilled-evidence positive control. No model call or target-code execution.

**Not in scope:** a model adapter, broader proof rules or private cases.

## 2. Cross-platform path and Unicode fixtures

**Scope:** `tests/` only.

**Acceptance:** deterministic Windows/Linux cases for path spelling, UTF-8 and read failures, paired with successful-read controls. State platform assumptions instead of silently treating different filesystem semantics as identical. Existing tests remain green.

**Not in scope:** changing source-identity rules simply to make a test pass.

## 3. Evidence-result API contract

**Scope:** design and tests first; a narrow optional adapter only after agreement.

**Acceptance:** define `found`, `read_ok`, observed path identity, clipped text and unresolved requests. Demonstrate that unusable or unrelated evidence does not silently become `COMPLETE`.

**Not in scope:** expanding into a general-purpose retrieval service.

## 4. Source snapshot consistency tests

**Scope:** synthetic source-change and time-of-check/time-of-use scenarios.

**Acceptance:** changed source bytes cause an explicit STOP or `INCOMPLETE` where required; stable-source positive controls still work. Preserve conflict records and distinguish tested guarantees from untested durability assumptions.

**Not in scope:** silent restoration, automatic retries or claims of atomic isolation without evidence.

## 5. Bounded report rendering

**Scope:** a deterministic presentation layer; no model.

**Acceptance:** show accepted and withheld claims, evidence, limitations and completion status without upgrading model-written prose to fact. Keep output bounded and omission accounting visible.

**Not in scope:** changing scoring, certification or completion semantics.

## 6. Cost-matched baseline design

**Scope:** a design document and synthetic dry-run specification only.

**Acceptance:** define a strong single-model baseline; account for all calls, tokens, retries, wall time and failures; freeze abstention and adjudication rules before comparison. Align with the [evaluation protocol](EVALUATION_PROTOCOL.md).

**Not in scope:** protected holdouts, live qualification or a claim that Council already wins.

## 7. Newcomer quickstart validation

**Scope:** README and contributor documentation, tested from a fresh local copy.

**Acceptance:** a new contributor can run the demo and tests with Python 3.12+ on Windows and Linux, without package installation or API keys. Document working-directory assumptions and the meaning of expected output. Verify rather than merely repeat existing instructions.

**Not in scope:** introducing a package manager or build system without a separately agreed need.

## Before you start

Open or comment on a GitHub Issue to agree a bounded task. Include the proposed acceptance criteria, a negative case and a positive control. Follow [CONTRIBUTING.md](../CONTRIBUTING.md); a passing test suite does not itself authorize a merge.
