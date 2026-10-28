# Known limitations of R0

- **Not the full Council application.** This package has no LLM execution, multi-agent workflow, GUI or production data adapter.
- Static semantic proofs are intentionally narrow: selected direct arithmetic-contract mismatches, unconditional constant division-by-zero, and structural documentation observations. They do **not** establish general Python correctness.
- Unsupported positive `KEEP_AS_IS` claims are withheld, not endorsed. Zero verified bugs does not mean there are no bugs.
- Source files can change between operations; some consistency checks fail closed, but atomic whole-project snapshots, concurrent updates and power-loss durability are not proven.
- Synthetic test success is not evidence of live system reliability, security review, good model behavior or superiority over a single strong model.
- No sealed holdouts, patient data, internal audit logs or private benchmarks are included in the public snapshot.
- Published R0 interfaces should be treated as unstable; backwards compatibility is not promised.
