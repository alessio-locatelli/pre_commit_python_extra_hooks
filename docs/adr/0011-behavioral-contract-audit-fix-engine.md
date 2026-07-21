# Behavioral contract audit: fix-engine write & validation safety (ch. 1, 3, 4, 20)

`docs/behavioral_contract.md` chapters 1 (Correctness and Safety of Auto-Fixes), 3 (Source File Integrity), 4 (Parsing and Invalid Python), and 20 (Parsing, AST, CST, and Source Mapping) were audited against the fix-application and file-write path: `atomic_write_text()`/`FixValidationError` in `_base.py`, `CheckOrchestrator._apply_fixes()`/`_check_file()`, and every check's own `fix()`. Full findings are in `docs/audits/0002-behavioral-contract-audit-fix-engine.md`.

## Decision

A check's own write failure and a file the orchestrator couldn't read or parse must both be surfaced to the user and to the exit code, never silently dropped. Concretely: every check's `fix()` must catch its own `OSError` and return `False` rather than let it propagate (matching the `ASTCheck.fix()` protocol's documented contract), and `CheckOrchestrator` tracks files it could not process (`unprocessable_files`) separately from files it processed cleanly, so `main()` can report each one and force a non-zero exit code.

Two related gaps identified by the audit were judged acceptable, not fixed: concurrent external modification of a file mid-run (no compare-and-swap against the file's state at write time — the same limitation most `--fix`-capable linters accept, and disproportionate to close for a single-maintainer local hook with no parallel workers), and distinguishing "a violation was fixed" from "a violation disappeared as an undocumented side effect of a different check's fix" (would require snapshotting every check's original violations against a final full-file recheck).

## Consequences

- `CheckOrchestrator.unprocessable_files: list[str]` is populated whenever `_check_file()` can't read or parse a file, and `main()` reports each entry and sets `exit_code = 1` — a behavior change from the prior silent `exit_code = 0` for that case.
- Every check's `fix()` now uniformly catches its own `OSError` and returns `False`; none propagates it.
- No new defensive parsing was added — this project's precondition (every file already passed `check-ast`/ruff in the same pre-commit run) still holds, and invalid-syntax handling stays a catch-log-skip fallback rather than a recovery path.
