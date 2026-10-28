# Proposed GitHub Issues for first contributors

Create these as individual GitHub Issues **after** the public repo is approved. They are planned tasks, not claims that the current R0 implementation has a newly confirmed bug.

## 1. [good first issue] Offline demo for `INCOMPLETE` requests

- **Scope:** `examples/` and tests only.
- **Acceptance:** Show synthetic missing evidence preserved as incomplete without a model call; print reason code and warning.
- **Do not:** Add live model APIs or disclose private cases.

## 2. [good first issue] Cross-platform path and Unicode fixtures

- **Scope:** `tests/` only.
- **Acceptance:** Deterministic Windows/Linux test matrix for path spelling, UTF-8 and failed reads with positive controls; existing tests remain green.

## 3. [help wanted] Explicit evidence-result API contract

- **Scope:** Design and tests first, then a narrow optional adapter.
- **Acceptance:** Document what `found`, `read_ok`, observed path identity and clipped text mean; no false-`COMPLETE` case passes.

## 4. [help wanted] Source snapshot consistency tests

- **Scope:** Synthetic concurrency/TOCTOU scenarios only.
- **Acceptance:** Report explicit STOP/INCOMPLETE on changed source bytes; no silent restoration, no automatic retries.

## 5. [help wanted] Bounded report rendering

- **Scope:** Deterministic pure presentation layer (no model).
- **Acceptance:** Display accepted/withheld findings, evidence and limitations without interpreting model-written claims as facts.

## 6. [research] Fair cost-matched single-agent baseline harness

- **Scope:** A design document and synthetic dry-run only.
- **Acceptance:** Freeze cost accounting, measurement protocol and abstention semantics without using protected holdouts or claiming superiority.

## 7. [documentation] Beginner contributor quickstart

- **Scope:** README and docs.
- **Acceptance:** Fresh Python 3.12 environment runs offline tests and demo on Windows and Linux, no API keys or installs required.
