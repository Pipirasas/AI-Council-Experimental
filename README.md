# AI Council — experimental evidence-audit core (R0)

**Experimental research / contributor preview. Not a production code auditor.**

The long-term goal of AI Council is to test whether an evidence-grounded group of model reviewers can outperform a **strong single-model baseline at a comparable total budget**. That superiority **has not been demonstrated**.

## What this repository actually contains

This is the first intentionally limited, offline and dependency-free **audit evidence core**, not the complete multi-agent Council application:

- Exact-byte source/evidence binding and narrowly scoped deterministic source claims.
- A read-only, bounded evidence broker with explicit source-read outcomes.
- Audit-session conflict and certificate-preservation helpers.
- Minimal report provenance checks and a deterministic demo.
- Synthetic regression tests. No real user projects, protected evaluation cases, or model outputs are bundled.

**Not included:** live agents, an LLM runner, multi-agent orchestration, UI, benchmark oracles, private datasets/holdouts, production integrations, and the private project's history. Some upstream integration code remains under development and is not part of R0.

## Run it offline

Requires Python **3.12+**. No `pip install`, Ollama, API keys, network, GitHub account or database needed.

```bash
python -B -m examples.offline_demo
python -B -m unittest discover -s tests -v
python -B scripts/check_public_tree.py
```

The demo constructs a disposable two-line Python program and an explicit synthetic requirement; **it never runs/imports the target program**. The result is a bounded proof demonstration, not a claim of a comprehensive code review.

## Structure

| Path | Purpose |
| --- | --- |
| `ai_council/audit_provenance.py` | Citation checks, narrow certificates, final report reconstruction |
| `ai_council/evidence.py` | Read-only evidence collection with explicit read status |
| `ai_council/audit_session.py` | Evidence reconciliation and certificate retention |
| `ai_council/project_files.py` | Project-file inventory helpers |
| `ai_council/schema_validation.py`, `schemas.py` | Deterministic structured-output constraints |
| `tests/` | Synthetic-only regression suite |
| `examples/` | Offline walkthrough |
| `docs/` | Architecture, evaluation protocol, limitations, contribution backlog |

## Evidence ≠ correctness

An existing path or matching excerpt alone never proves that a model's explanation is true. Claims only become *verified* for explicitly supported deterministic patterns. Other claims remain unverified. A report with zero verified bugs is **not evidence of bug-free software**. An audit with unresolved evidence should be marked incomplete, not silently complete.

## Contributions welcome

Start with the [good first issues](docs/GOOD_FIRST_ISSUES.md) and [contribution guide](CONTRIBUTING.md). Run offline tests, explain the failing case and ensure new claims are evidence-backed. The project maintainer reviews and controls merges; contributions are not automatically accepted.

For ordinary discussion use **GitHub Issues**, and **GitHub Discussions** once enabled. No personal contact email is published; see [CONTACT.md](CONTACT.md). Never paste credentials or private code into a public issue.

## Licensing

An **Apache-2.0 `LICENSE`** is included in this candidate. The maintainer must confirm source-code ownership and third-party attribution before authorizing publication. See the separate private release-review checklist. No public repository or release has been published by this preparation.

## Status

**R0 = bounded development preview**, not a release of the full AI Council or a qualified safety/correctness assessment. Do not use as the sole basis for critical decisions. See [Limitations](docs/LIMITATIONS.md) and [Evaluation](docs/EVALUATION_PROTOCOL.md).
