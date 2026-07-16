# PEP 263 encoding + exact newline fidelity, restored via a shared raw-bytes read

The merge of `fix_misplaced_comments` into `ast_checks` (ADR 0001) replaced the standalone hook's `tokenize.open()` read (which honors a PEP 263 encoding declaration and preserves exact line endings via `newline=""`) with `CheckOrchestrator` reading every file as UTF-8 text. A file with a non-UTF-8 declared encoding, or CRLF line endings, could be misread or have its line endings silently normalized on write — a regression across all 6 checks, not just misplaced-comment.

## Considered Options

- **Restore this only for misplaced-comment**: rejected — the read path is shared by every check through `CheckOrchestrator`, so a per-check fix would either duplicate the read (reintroducing exactly the duplicated-pipeline problem ADR 0001 removed) or leave the other 5 checks silently misreading non-UTF-8 declared files.
- **Read raw bytes and decode manually via `tokenize.detect_encoding`, add an `encoding: str = "utf-8"` parameter to `ASTCheck.fix()`**: adopted. Decoding bytes directly (rather than opening in text mode) never touches line endings — a CRLF file's `source` string keeps literal `\r\n`, which `ast.parse`/`tokenize` both already tolerate. The `fix()` parameter defaults to `"utf-8"` so none of the ~30 existing direct `check.fix(...)` calls in tests needed updating; only `CheckOrchestrator` (which always knows the real detected encoding) passes it explicitly.

## Consequences

- `read_source_with_encoding()` (`_base.py`) is the single shared primitive; `CheckOrchestrator._read_source` wraps it with the orchestrator's existing log-and-return-None error handling.
- `validate_function_name` doesn't consume `CheckOrchestrator`'s `source`/`tree` at all — it independently re-reads via its own `analysis.read_source()`/`autofix.apply_fix()` (a pre-existing inconsistency, not introduced by this change). Both were pointed at the same shared `read_source_with_encoding()` primitive so this check's encoding handling isn't silently left behind; the redundant-read architecture itself is unchanged and out of scope here.
- Every check's fix() write call now passes `encoding=` through to `write_text()`, with `newline=""` to stop Python from re-translating line endings on write. A fix still constructs any brand-new line content with a literal `"\n"` (matching the pre-merge implementation exactly — it never attempted per-edit newline-style matching, only preserving encoding/newlines for lines a fix didn't touch).
- `redundant_assignment/autofix.py`'s write call was previously missing an `encoding=` argument entirely (locale-default encoding) — folded into this same pass since every write call site was already being touched.
- No `CacheManager.CACHE_VERSION` bump: a file that previously failed to decode as UTF-8 returned `None` from `_check_file` and was therefore never cached, so there's no previously-cached-now-wrong-answer scenario.
