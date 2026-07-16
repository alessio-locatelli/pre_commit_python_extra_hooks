# `requires_ast` capability flag, not a general AST-optional redesign

`CheckOrchestrator._check_file` gated every enabled check behind `ast.parse()` succeeding, even though `misplaced-comment` only tokenizes and never reads the `tree` argument in either `check()` or `fix()`. A tokenize-valid/ast-invalid file (e.g. a leftover Python 2 `print "x"` statement) silently skipped every check, including one that didn't need the tree at all — a regression from the pre-merge standalone `fix_misplaced_comments` hook, which ran on pure `tokenize` output with no `ast.parse()` dependency.

## Considered Options

- **Make `tree` optional (`ast.Module | None`) on the whole `ASTCheck` protocol**: rejected. Only `misplaced-comment` can ever receive `None`; the other 5 checks would gain `None`-handling noise (asserts or narrowing) for a case that can never actually happen to them, since the orchestrator only calls a `requires_ast=True` check when parsing succeeded. That trades a "never touch this" comment for real code churn spread across 5 files that don't need it.
- **A `requires_ast: bool` capability property, checked once by the orchestrator**: adopted. Every check still declares a real `ast.Module` parameter type — the contract ("if `requires_ast` is `False`, `tree` will not be a real parse of the file, and this check must not read it") is a documented invariant, not a type-level one, matching this codebase's existing style of trusting check implementations rather than encoding every constraint in the type system (e.g. `check_id` uniqueness isn't statically enforced either).

## Consequences

- `CheckOrchestrator` passes a shared `_EMPTY_TREE = ast.parse("")` sentinel to `requires_ast=False` checks when the real file doesn't parse, in both `_check_file` and `_apply_fixes`.
- No `CacheManager.CACHE_VERSION` bump: files that previously failed `ast.parse()` returned `None` from `_check_file` and were therefore never cached, so there's no previously-cached-now-wrong-answer scenario to invalidate.
- Adding a new AST-optional check in the future means implementing `requires_ast` truthfully and never touching `tree` when it returns `False` — there's no structural enforcement of that beyond the docstring on the protocol.
