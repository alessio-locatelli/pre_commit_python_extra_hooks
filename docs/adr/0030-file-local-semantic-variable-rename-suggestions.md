# File-local semantic variable rename suggestions

## Context

TRI001 must keep reporting forbidden names wherever they are bound, while useful rename suggestions require more information than a right-hand-side spelling pattern can provide. A misleading automatic rename is worse than no rename, and a hook must remain fast, deterministic, offline, and independent of repository-wide analysis.

## Decision

TRI001 keeps detection and scope-aware rewriting in `forbid_vars.py`. A dedicated private module builds a file-local model from the parsed AST and returns structured rename proposals for eligible simple local assignments.

The model separates expression, type annotation, consumer, control-flow, import-resolved API, and lexical-safety evidence from name generation. It recognizes a small fixed vocabulary of standard APIs and derives ordinary producer, collection, predicate, and annotation names without network access or project configuration.

Only a locally unambiguous proposal with strong compatible evidence is fixable. A useful but weaker proposal is reported without a fix. Missing, conflicting, dynamic, rebinding, collision, reflection, or externally visible context produces no automatic rename. The analysis never follows context outside the current file.

## Consequences

- New naming patterns can be added without changing TRI001 detection or its rewrite engine.
- Suggestions are reproducible and have bounded per-file analysis cost.
- Many generic bindings intentionally receive no proposal; precision takes priority over coverage.
- The API vocabulary is deliberately limited and must be expanded with explicit semantics and tests rather than inferred from arbitrary call names.
