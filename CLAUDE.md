# pre_commit_extra_hooks Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-01

## Active Technologies

- Python 3.13+ + Python stdlib only (ast, re, tokenize) (005-fix-forbid-vars-linter-bugs)
- N/A (operates on source files) (005-fix-forbid-vars-linter-bugs)

## Project Structure

```text
src/
tests/
```

## Recent Changes

- 005-fix-forbid-vars-linter-bugs: Added Python 3.13+ + Python stdlib only (ast, re, tokenize)

- 004-fix-reported-bugs: Added Python 3.13+ + pytest, ruff, mypy (all dev dependencies, no runtime dependencies)

## Commands

### Python package and project manager

Use [`uv`](https://docs.astral.sh/uv/).

### Test

```bash
uv run pytest
```

## Code Style

### Code Quality: Always Format and Lint

**REQUIRED:** Before committing or after making code changes, **ALWAYS** run:

```bash
uv run ruff check --fix .
uv run ruff format .
uv run mypy src/
npx prettier . --write --cache
taplo fmt pyproject.toml
```

## Git

Commit your changes after completing the task.

### Git Commit Guidelines

**ALWAYS** use the [Conventional Commits](https://www.conventionalcommits.org/) standard for commit messages.

## Development Environment Troubleshooting

```mermaid
flowchart TD
  Start[Encountered a critical dev-environment problem: version mismatch, missing dependencies, missing environment variables, or 'command not found' for documented tools] --> B{Were you invoked solely to implement a feature, refactor, or bugfix?}

  B -->|Yes| C{Do the project or user instructions explicitly authorize modifying the development environment or resolving issues autonomously?}
  B -->|No| D[Use your best judgment. If a change to the environment is required, ask the user first. Otherwise, report the blocking problem with details.]

  C -->|Yes| E[Attempt safe, minimal fixes automatically. If these attempts fail, report the errors and what you tried.]
  C -->|No| F[Do not modify the environment. Report the issue with specific errors and suggest how to fix it.]

  E --> G(End)
  F --> G
  D --> G
```

## **MUST NOT** Rules

- Do not implement before clarifying the missing information and understanding existing patterns.
- Never use `git commit --amend`, `git commit --no-verify`, `git add --all`, `git add .`, or `git add -A`.
- Never modify test expectations to bypass failures.
- Do not sacrifice using the latest Python features in favor of backward compatibility and supporting older versions.
- Do not suppress linter warnings (e.g., by adding `# noqa` or `# type: ignore` code comments) before trying to understand and fix the root cause.
