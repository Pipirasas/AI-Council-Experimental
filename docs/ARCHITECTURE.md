# Architecture and trust boundaries

AI Council's **research hypothesis** is that specialist model reviews might be more reliable when checked by a shared, deterministic evidence process. This repository exports only the **offline evidence/validation layer**.

```text
[Original task + explicit source requirement]
                   |
                   v
       [read-only project inventory]
                   |
                   v
      [bounded evidence broker]
                   |
                   v
        [source/ID validation]
                   |
                   v
   [narrow deterministic certificates]
                   |
                   v
 [certificate retention + conflict checks]
                   |
                   v
  [bounded report / incomplete accounting]
```

**Model calls, model-selection policies, orchestration runtime, GUI and benchmark harness are NOT supplied in R0.** The diagram describes the interface intent; it is not proof of a deployed full Council pipeline.

## Core boundaries

- **Source identity:** When code is cited, byte hashes, paths, and numbered lines must agree. A citation is not a semantic proof.
- **Contract authority:** A directly parsed, explicitly user-authorized requirement can support a **small arithmetic subset**; tests or model comments cannot invent an independent specification.
- **Evidence broker:** Path identity and successful content reads matter; search alternatives, truncated queries and read failures are not fulfilled requests.
- **Semantic certification:** A conservative static proof certifies only supported patterns. Arbitrary program behavior is not certified.
- **Audit completeness:** Missing evidence must be visible. `INCOMPLETE` differs from `COMPLETE` and from a claim of a bug-free program.
- **Report:** Never promote raw model prose into authoritative findings or guarantees.

See [Limitations](LIMITATIONS.md) and [Evaluation Protocol](EVALUATION_PROTOCOL.md).
