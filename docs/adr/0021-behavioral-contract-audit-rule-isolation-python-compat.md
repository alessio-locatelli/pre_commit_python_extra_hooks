# Behavioral contract audit: rule isolation & Python-version compatibility (ch. 18, 19)

`docs/behavioral_contract.md` chapters 18 (Rule and Plugin Isolation) and 19 (Python Version and Language Compatibility) were audited against `ASTCheck`, `CheckOrchestrator`/`load_checks()`, `ALL_CHECKS`, and every check's own `fix()`. Full findings, with line citations for every already-satisfied item, are in `docs/audits/0011-behavioral-contract-audit-rule-isolation-python-compat.md`.

Both chapters presuppose a dynamic or third-party plugin system and a configurable analysis target version. This project has neither: `ALL_CHECKS` is a fixed, hand-authored list of in-repo classes with no plugin mechanism, and there is no target-version concept independent of the interpreter actually running the hook — every syntax-related requirement collapses to "whatever the running interpreter's own `ast`/`compile` accepts."

## Decision

No behavior in either chapter was found to be wrong: per-check failure isolation, fix validation via `atomic_write_text()`'s `compile()` gate, cache invalidation on rule or interpreter-version change, and deterministic rule selection were all already correct, verified against the code rather than assumed. The one gap was a documented-but-unenforced convention: `docs/adding-a-check.md` already states that a new check's `check_id`/`error_code` must be the next unused number, but nothing checked that a copy-pasted or mistyped value wouldn't silently collide with an existing check. `test_all_checks_have_unique_check_ids_and_error_codes` now locks in that invariant going forward.

## Consequences

- `tests/test_orchestrator.py` gains one preventive test asserting `ALL_CHECKS` never collides on `check_id` or `error_code`; no production code changed.
