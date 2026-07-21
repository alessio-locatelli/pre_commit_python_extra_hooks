# Behavioral contract audit: determinism & idempotence (ch. 9, 10)

`docs/behavioral_contract.md` chapters 9 (Determinism) and 10 (Idempotence) were audited against `_prefilter.py`, `_orchestrator.py`, `_discovery.py`, `_cache.py`, and `_diagnostics.py`, sequenced after `0011`'s fix-engine audit (issue #30) so this was tested against a settled engine. Full findings are in `docs/audits/0014-behavioral-contract-audit-determinism-idempotence.md`.

## Decision

`git_grep_filter()`'s successful-match branch built its result by iterating `git_matches`, a plain `set` of path strings — Python's own per-process `PYTHONHASHSEED` randomization made its iteration order, and so this function's own return order, vary run-to-run for identical input. This was invisible in the orchestrator's real call path (`batch_filter_files()`, its only in-repo caller, already re-sorts its result), but `git_grep_filter()` is itself an exported, independently documented function, so the nondeterminism was real for any caller that trusts its order directly. Fixed by building the result from `input_map.items()` (a `dict`, insertion-ordered by `filepaths` itself) instead of the hash-ordered set.

Fix idempotence (ch. 10: "MUST ensure that applying the same fix repeatedly converges to a stable result"; "MUST test fix idempotence explicitly") had only ever been verified once, ad hoc, as a manual spot-check recorded in `docs/audits/0002`'s prose — never as a committed test that would catch a future regression. `test_fix_converges_after_one_pass_across_all_checks` now runs the full check suite's `--fix` twice over all 33 existing `tests/fixtures/**/bad/*.py` fixtures and asserts the second pass changes nothing, reproducing `0002`'s finding as a permanent regression test.

Cache-hit/cache-miss equivalence (ch. 9) was also only weakly covered — the existing test compared just one field (`error_code`). `test_cache_hit_and_cache_miss_report_equivalent_violations` now compares every field a printed diagnostic depends on between a genuine cache-miss and a genuine cache-hit.

Everything else audited against ch. 9/10 (fix-application ordering, diagnostic ordering, absence of in-process parallelism, sorted filesystem traversal, cache-bypass in fix mode, formatter/fixer interaction) was already satisfied — either previously verified by `0002`/`0003`/`0007`/`0009`/`0011` or newly confirmed by this audit; see the audit report for citations and for the two items judged not applicable (no opposite-direction rule pair exists among this project's 6 checks; cross-rule cycle detection is verified empirically via the new idempotence test rather than built as a dedicated mechanism this project's fixed, pluginless check set doesn't need).

## Consequences

- `git_grep_filter()`'s match order no longer depends on `PYTHONHASHSEED`; no observable behavior change to the real pipeline, since `batch_filter_files()`'s own `sorted()` already erased the difference for every existing caller.
- `tests/test_prefilter.py` gains `test_git_grep_filter_match_order_is_independent_of_hash_seed`; `tests/test_orchestrator.py` gains `test_fix_converges_after_one_pass_across_all_checks` and `test_cache_hit_and_cache_miss_report_equivalent_violations`.
