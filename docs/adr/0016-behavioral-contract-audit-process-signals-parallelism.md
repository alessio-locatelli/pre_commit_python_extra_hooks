# Behavioral contract audit: process, signals, cancellation & parallelism (ch. 15, 16)

`docs/behavioral_contract.md` chapters 15 (Process, Signals, and Cancellation) and 16 (Parallelism and Concurrency) were audited against `__main__.py`'s process entry point, `atomic_write_text()`, `_cache.py`'s locking, and every `subprocess.run()` call. Full findings are in `docs/audits/0007-behavioral-contract-audit-process-signals-parallelism.md`.

Chapter 16 is almost entirely moot by construction: this tool has no `threading`, `multiprocessing`, or `concurrent.futures` anywhere — confirmed by grep — so it runs single-process and serial within one invocation. The one real multi-_process_ scenario (separate hook invocations racing on the shared cache) was already hardened by ADR 0013's lock timeout.

## Decision

Cancellation must run this codebase's existing cleanup paths (`atomic_write_text()`'s and `_write_cache()`'s temp-file `finally` blocks, subprocess child-killing) regardless of which signal triggered it. Python only installs a default handler for SIGINT (translated to catchable `KeyboardInterrupt`); SIGTERM — the signal a hook timeout, CI cancellation, or plain `kill` sends — had none, so the process died immediately, skipping every `try`/`finally` this codebase relies on for safe atomic writes. `__main__.py` now installs a SIGTERM handler that raises `KeyboardInterrupt`, deliberately reusing Python's own SIGINT translation path rather than inventing a second cancellation mechanism, so the same cleanup that already worked for Ctrl-C now works for SIGTERM too. Handler registration itself can fail (wrong thread, restricted environment); that failure is caught and logged rather than propagated, since SIGINT's own handling doesn't depend on it.

A new `run()` wrapper in `__main__.py` catches `KeyboardInterrupt` from either signal, prints a single `Interrupted.` line, and returns `1` — the same exit code every other incomplete-run outcome already uses (ADR 0012), rather than a new signal-specific value. `main()` itself stays signal-agnostic and directly testable; only the process entry point changed.

SIGKILL is out of scope by construction — no userspace handler can intercept it — and the residual risk (a stray, harmless `.tmp` sibling file, never a corrupted target) is the same one every tool using this atomic-write pattern accepts.

## Consequences

- `ast_checks/__main__.py` gains `_install_sigterm_handler()` and `run()`; the entry point calls `sys.exit(run())` instead of `sys.exit(main())`. `main()` is unchanged.
- A SIGTERM now behaves the same as Ctrl-C: a clean message on stderr, exit code `1`, and every in-flight write left either fully committed or fully rolled back.
- No new exit code was introduced — an interrupted run reuses the existing `1`.
