# Research evaluation plan (not completed)

## Question

Does an evidence-grounded, multi-reviewer AI Council yield **fewer unsupported claims and better detection** than a strong single model under an equal or reasonably cost-matched **total** budget?

## Required fair comparison

1. Choose a **strong** single-model baseline, not a weak or deliberately underprompted comparator.
2. Freeze task inputs, prompts, versions and scoring rules **before** blind evaluation.
3. Match or report end-to-end costs: total tokens, calls, retries, wall time, compute budget and failure handling (not just the last model call).
4. Use held-out, independently judged cases. Keep any private holdouts separate from this public repository.
5. Measure precision/recall of **supported findings**, false-support rate, unsupported severity claims, abstention/completeness behavior and statistical uncertainty.
6. Include control cases where code is correct, where tests are wrong, where the specification is absent and where evidence is missing.
7. Publish reproducible **aggregate results** and limitation statements without disclosing sealed inputs before protocol authorization.

## Status

**No qualifying result is supplied in R0.** The existing offline tests check the validator, not the comparative performance of live Council versus one model. A project contributor must not describe Council superiority as an established result.
