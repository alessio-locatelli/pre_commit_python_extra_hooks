# Behavioral contract audit: caching & cache-affecting upgrades (ch. 11, 33)

`docs/behavioral_contract.md` chapter 11 (Caching) was audited against `CacheManager` and `CheckOrchestrator._generate_cache_key()`/`process_files()`; chapter 33 (Compatibility and Upgrade Behavior) only for its cache-invalidation-on-version-change portions (per issue #32's scope — the rest of ch. 33 is CLI/config UX and release process, not caching). Full findings are in `docs/audits/0005-behavioral-contract-audit-caching-and-version-invalidation.md`.

## Decision

An unavailable cache directory must degrade to uncached execution, never crash the whole run. `CacheManager.__init__` is constructed unconditionally by `CheckOrchestrator`, so a cache directory that can't be created (permission denied, read-only filesystem) previously crashed the entire hook with a raw traceback before a single file was checked. `_ensure_cache_dir()` now catches `OSError`, logs once, and sets `_cache_dir_unavailable` so every later cache read/write short-circuits to a no-op instead of repeating the same doomed filesystem call per file. Because `mkdir(exist_ok=True)` and the `CACHEDIR.TAG` write can both succeed trivially against an already-populated, since-read-only-mounted directory without ever attempting a write, availability is confirmed with an explicit `os.access(..., os.W_OK)` probe rather than inferred from whether a write happened to occur.

The cache key must also change whenever the running interpreter's own AST shape could differ for the same source — Python minor versions aren't guaranteed to produce an identical `ast.parse()` output. The cache key now includes `major.minor` of the running interpreter (not the full version — bugfix releases don't change the grammar, so including patch metadata would invalidate the cache on every patch upgrade for no behavioral reason, the same principle ADR 0005 already applied to the source-tree hash).

## Consequences

- `CacheManager._ensure_cache_dir()` can no longer raise; an unavailable cache directory logs one warning at construction and disables cache I/O for that `CacheManager`'s lifetime, rather than crashing or degrading per-call with repeated warnings.
- `_generate_cache_key()`'s output gains a fourth `|`-joined component (interpreter `major.minor`), invalidating every existing on-disk cache entry once — the same one-time cost every prior cache-key change (ADR 0005) already carried.
- No config-file parsing, environment-variable reads, or cache-pruning logic exist anywhere in this pipeline, so several chapter 11/33 items (config-file cache identity, env-dependent inputs, cache cleanup safety, migration paths for old config) don't apply — confirmed by grep, not assumed.
