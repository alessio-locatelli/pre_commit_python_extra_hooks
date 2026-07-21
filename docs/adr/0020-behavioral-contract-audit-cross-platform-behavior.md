# Behavioral contract audit: cross-platform behavior (ch. 14)

`docs/behavioral_contract.md` chapter 14 (Cross-Platform Behavior) was audited against every module in `src/pre_commit_hooks/`. Every path already goes through `pathlib.Path`, every write is already POSIX-atomic via `tempfile.mkstemp()`/`Path.replace()`, and every text I/O call already passes explicit `encoding=`/`newline=""` — so nearly the whole chapter was already satisfied. Full findings are in `docs/audits/0010-behavioral-contract-audit-cross-platform-behavior.md`.

## Decision

An optional platform feature's absence must degrade with a warning, never hard-crash the whole package at import time. `_cache.py`'s unconditional `import fcntl` (used only by `CacheManager._locked()`'s advisory cross-process lock) made the entire package fail to import on any platform without `fcntl` — Windows has none — before any of this hook's own error handling could run. This project targets Linux/WSL only (`AGENTS.md`), which is why the gap shipped unnoticed: nothing exercised the without-`fcntl` path, since the project's prior stated design ruled out testing it at all.

The import is now wrapped in `try/except ImportError`, and `CacheManager` computes `_locking_unavailable` once at construction (mirroring the existing `_cache_dir_unavailable` pattern). When locking is unavailable, the cache is disabled entirely, not just unlocked — an earlier draft that kept the cache enabled but skipped the lock would reintroduce the exact unsynchronized read-modify-write race the lock exists to prevent, just on a platform where it happens to be unavailable rather than absent by oversight. `AGENTS.md`'s cross-platform policy now states this "degrade with a clear warning" requirement explicitly, alongside its pre-existing "don't add Windows/macOS-specific code paths" instruction.

## Consequences

- `_cache.py`'s `fcntl` import is conditional; `CacheManager` gains `_locking_unavailable`, checked alongside `_cache_dir_unavailable` in both `get_cached_result()`/`set_cached_result()` — either one disables the cache for the run.
- No behavior change on the one supported platform: `fcntl` always imports successfully there, so `_locking_unavailable` is always `False`.
- This changes an unsupported platform's failure mode from "crashes on import" to "runs uncached with a warning" — it does not add or claim Windows/macOS support.
