# Contributing to AI Council

The maintainer welcomes **small, reviewable, evidence-backed** contributions to this experimental audit core. This is not a competition to produce the greatest number of alleged bugs.

## Working agreement

1. Open or comment on an Issue to establish a bounded problem and expected behavior.
2. Work only with synthetic/public fixtures. **Never upload private projects, credentials, patient information, internal logs or protected holdouts**.
3. First write a negative regression demonstrating the old behavior and a positive control preventing an over-strict fix.
4. Change the minimum code necessary; do not weaken source identity, evidence provenance or fail-closed rules.
5. Run `python -B -m unittest discover -s tests -v` and `python -B scripts/check_public_tree.py`.
6. Describe what was proven and what was only hypothesized. A static observation is not a runtime test.
7. Open a PR with test output, limitations, affected modules and a clear STOP condition.

## Scope of initial contributions

See [good first issues](docs/GOOD_FIRST_ISSUES.md). Focus on source evidence identity, completion accounting, offline portability, reproducible evaluation infrastructure and documentation. Model integrations and new authority rules require separate design review.

## Maintainer decisions

The project maintainer **@Pipirasas** is responsible for review, release scope, merge decisions and license approval. A successful CI run is not authorization to merge or to publish private evaluation material.

By submitting a contribution for inclusion, you confirm that you have the necessary rights to submit it under the repository's Apache-2.0 license. Preserve third-party notices and identify generated or externally sourced material when it affects licensing or evidence quality.

## Contact

Use GitHub Issues, then Discussions when enabled. Do not post personal emails or security-sensitive reports in issues; see [CONTACT.md](CONTACT.md) and [SECURITY.md](SECURITY.md).
