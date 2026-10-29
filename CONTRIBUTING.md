# Contributing to AI Council

[Project overview](README.md) · [Find a task](docs/GOOD_FIRST_ISSUES.md) · [Architecture](docs/ARCHITECTURE.md) · [Code of conduct](CODE_OF_CONDUCT.md)

Contribute a **small, reproducible improvement** to the experimental evidence-audit core. The goal is useful, supported conclusions—not the largest number of alleged bugs.

## Your first contribution

| Step | What to do |
| --- | --- |
| **1. Choose a bounded task** | Start with the [seven contribution proposals](docs/GOOD_FIRST_ISSUES.md). Open or comment on an Issue before substantial work. |
| **2. Establish the evidence** | Write a negative regression for the old behavior and a positive control that prevents an over-strict fix. |
| **3. Make the smallest useful change** | Preserve source identity, evidence provenance, completion accounting and fail-closed behavior. |
| **4. Explain the result** | Submit a PR with reproduction, tests, limitations and what remains unproven. |

You need Python 3.12+ and the source checkout for offline development. R0 tests and the demo use the standard library; no API key, paid AI plan or model download is required.

## Run the local checks

From the repository root:

```bash
python -B -m unittest discover -s tests -v
python -B -m examples.offline_demo
python -B scripts/check_public_tree.py
```

These Python commands also work in PowerShell. The path check is deliberately limited; it is not a complete secret scan or licensing audit.

## Non-negotiable boundaries

- Use synthetic or public fixtures. Never upload private projects, credentials, patient information, internal logs or protected evaluation cases.
- Separate a static hypothesis from an executed reproduction. Report what was actually tested, on which platform, and with what result.
- Do not replace authoritative evidence with model agreement or weaken checks to obtain a passing result.
- Model integrations and new proof/authority rules require a separate design review. They are not implicit in an R0 documentation or test task.

## What to put in a pull request

State the problem, why the selected source supports it, the narrow change and the test results. Include known limits and a clear condition under which work must stop rather than silently retry. Use the repository's [PR template](.github/pull_request_template.md).

## Review, rights and contact

Lead maintainer **[@Pipirasas](https://github.com/Pipirasas)** controls review, merges and release decisions. Passing CI is not automatic merge or publication approval. See [GOVERNANCE.md](GOVERNANCE.md).

Submit only contributions you have the necessary rights to provide under the repository's [Apache-2.0 license](LICENSE). Preserve third-party notices and identify generated or externally sourced material when it affects licensing or evidence quality.

For ordinary questions, use GitHub Issues; Discussions can be used after they are enabled. No personal email is published. Sensitive reports follow [SECURITY.md](SECURITY.md), not a public issue. See [CONTACT.md](CONTACT.md).
