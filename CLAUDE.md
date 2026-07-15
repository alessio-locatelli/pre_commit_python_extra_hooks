# Different custom Python linters and hooks for pre-commit.

## Development Guidelines

- The repository contains multiple different linters.
- Each linter is independent and focuses on performing one task (e.g., only fixing function naming, or only fixing code comments).
- Linters must support being run via [prek](https://github.com/j178/prek) (a drop-in alternative to pre-commit).
- Performance is critical.

### Suggested Linter Architecture

Hybrid pipeline:

1. If possible, filter candidate files quickly using `ripgrep`, `ast-gre p`, or `git grep`.
2. Parse and process the files using a Python parser or faster alternatives (`tree-sitter`, `ast-grep`, native Rust).

## Commands

### Python package and project manager

Use [`uv`](https://docs.astral.sh/uv/).

## Development

Run before committing or after making code changes:

```bash
uv run ruff check --fix .
uv run ruff format .
uv run mypy src/ tests/
npx prettier . --write --cache
taplo fmt pyproject.toml
uv run coverage run -m pytest
uv run coverage report
uv run strict-no-cover
```
