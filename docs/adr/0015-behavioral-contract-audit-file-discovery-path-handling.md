# Behavioral contract audit: file discovery, path handling & incremental scope (ch. 12, 13)

`docs/behavioral_contract.md` chapters 12 (Incremental Execution) and 13 (Filesystem and Path Handling) were audited against `_prefilter.py`'s `git grep`/`git ls-files` calls, `ast_checks/__init__.py`'s CLI argument handling, and `_cache.py`'s path-based cache keys. Full findings are in `docs/audits/0006-behavioral-contract-audit-file-discovery-path-handling.md`.

## Decision

`git grep`'s own result must never be trusted at face value when it can't distinguish "no match" from "couldn't check." A permission-denied tracked file, or a file that vanished between discovery and this call, both make `git grep` exit 0 or 1 with no distinguishing signal beyond stderr — the prefilter previously treated that as an authoritative non-match and silently dropped the file from every check's candidate list. `git_grep_filter()` now confirms each input path is readable up front (carrying an unreadable one through as a candidate regardless of what `git grep` reports), and only trusts `git grep`'s stdout when its stderr is also empty, falling back to the pre-existing Python scan otherwise. Either path defers the actual diagnosis to the orchestrator's existing unreadable-file reporting (ADR 0011) rather than teaching the prefilter to explain the failure itself.

A directory argument on the CLI (`ruff-extra-rules src/`, the exact form `AGENTS.md`'s own dev docs use) previously reached the orchestrator unexpanded and silently checked nothing — `git grep`'s directory-pathspec matches never resolved back to the literal directory path in the prefilter's own candidate map, so they were discarded by an existing "unresolvable git result" safety check. `expand_directories()` now expands a directory argument to its `.py` files (via `git ls-files` inside a repo, filtered to entries that still exist on disk since the index can list a file removed with a plain `rm`; a recursive glob otherwise) before `--exclude` filtering runs.

## Consequences

- `git_grep_filter()` now probes readability per input path before invoking `git grep`, and falls back to the Python scanner whenever `git grep` reports any stderr — a deliberate safety-over-speed tradeoff.
- `ast_checks/__init__.py` gains `expand_directories()` (public) and `_list_python_files_in_dir()` (private); `main()` expands directory arguments before `--exclude` filtering.
- File identity, path normalization, and the mtime-fast-path cache design were already correct and needed no change — verified with same-directory case-sensitivity checks, a path containing shell metacharacters, and a review of every `Path.resolve()` call site.
- Network-filesystem lock reliability and coarse-timestamp cache staleness are accepted, unfixed limitations: this project targets Linux/WSL only (`AGENTS.md`), and the worst case in either scenario is a stale cache entry a later run overwrites, never data loss.
