# Behavioral contract audit: stdin/stdout/TTY, logging & debugging, installation and runtime environment (ch. 26, 27, 29)

`docs/behavioral_contract.md` chapters 26 (Standard Input, Output, and TTY Behavior), 27 (Logging and Debugging), and 29 (Installation and Runtime Environment) were audited against `_cli.py`, `__main__.py`, `_diagnostics.py`, every module's logging usage, and `pyproject.toml`'s dependency metadata. This tool has zero runtime dependencies beyond the standard library, never reads from or queries a terminal, and never logs source content or secrets — chapters 26 and the dependency-handling parts of 29 were already fully satisfied by construction. Full findings are in `docs/audits/0012-behavioral-contract-audit-stdio-tty-logging-runtime.md`.

## Decision

A user hitting a rule crash or an unreadable-file diagnostic had no supported way to see the underlying exception: ADR 0017 deliberately downgraded internal `logger.exception()` calls to `logger.debug(..., exc_info=True)` to stop duplicating the clean diagnostic line, but nothing in this codebase ever raised the log level, and no CLI flag existed to do so. `-v`/`--verbose` is added to `_cli.py` (mirroring `ruff`'s own flag, per ADR 0008's CLI-parity design); when set, `main()` calls `logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)` once before any file processing, surfacing the already-existing debug-level log lines. The flag only reconfigures logging — it cannot change which violations are reported or how `--fix` behaves, verified by diffing a `--verbose` and non-`--verbose` run byte-for-byte on exit code and violation output.

Runtime-version incompatibility is deliberately not checked in-code: this project's own entry point already uses Python 3.14-only syntax (PEP 758), so an incompatible interpreter fails to compile `__main__.py` before any version check written in this codebase could run. Adding a second, older-syntax shim module purely to gate on version would be exactly the compatibility branch `AGENTS.md` forbids; `pip`/`uv` already refuse installation on an incompatible interpreter via `requires-python`.

## Consequences

- `_cli.py` gains `-v`/`--verbose`; `main()` calls `logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)` once when set. No change to existing flags, check/fix behavior, or the exit-code contract (ADR 0012).
