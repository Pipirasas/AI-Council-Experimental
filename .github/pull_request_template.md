## Change summary

Explain the narrow, verifiable behavior change.

## Evidence and tests

- [ ] New synthetic regression fails on the former behavior (when fixing a bug)
- [ ] Positive control preserves intended behavior
- [ ] `python -B -m unittest discover -s tests -v` succeeds
- [ ] `python -B scripts/check_public_tree.py` succeeds
- [ ] No model, network, private data or protected holdouts used

## Limitations and compatibility

State what this PR does **not** establish, including any untested behavior.

## Licensing

- [ ] I have the rights to contribute this material under Apache-2.0
- [ ] Third-party content/attribution is disclosed
