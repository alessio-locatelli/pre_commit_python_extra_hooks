# pre_commit_extra_hooks Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-28

## Active Technologies
- Python 3.8+ (minimum version - pre-commit framework supports 3.8+) + Python standard library only (ast, tokenize, inspect, argparse, sys, pathlib) (002-style-maintainability-hooks)
- N/A (hooks process files in-place, no persistent storage needed) (002-style-maintainability-hooks)

- Python 3.8+ (minimum version compatible with most development environments; pre-commit supports Python 3.8+) + None (Python standard library only per FR-012 and Constitution I - KISS principle) (001-pre-commit-hooks)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.8+ (minimum version compatible with most development environments; pre-commit supports Python 3.8+): Follow standard conventions

## Recent Changes
- 002-style-maintainability-hooks: Added Python 3.8+ (minimum version - pre-commit framework supports 3.8+) + Python standard library only (ast, tokenize, inspect, argparse, sys, pathlib)

- 001-pre-commit-hooks: Added Python 3.8+ (minimum version compatible with most development environments; pre-commit supports Python 3.8+) + None (Python standard library only per FR-012 and Constitution I - KISS principle)

<!-- MANUAL ADDITIONS START -->

## Command Execution Guidelines

### Package Manager: Use `uv run`

**ALWAYS** use `uv run` to execute Python commands. **NEVER** directly call executables from `.venv/bin/`.

**Correct:**
```bash
uv run pytest
uv run pytest -v
uv run mypy src/
uv run ruff check .
```

**Incorrect:**
```bash
.venv/bin/pytest -v          # ❌ NEVER do this
pytest                        # ❌ May not work without uv run
python -m pytest             # ❌ Use uv run instead
```

### Code Quality: Always Format and Lint

**REQUIRED:** Before committing or after making code changes, **ALWAYS** run:

```bash
uv run ruff format .
uv run ruff check --fix .
```

These commands must be run in sequence:
1. `ruff format` - Formats all Python files according to project style
2. `ruff check --fix` - Runs linter and automatically fixes issues

**When to run:**
- After writing or modifying Python code
- Before creating commits
- After resolving merge conflicts
- When tests fail due to style issues

## Git Commit Guidelines

### Conventional Commits Standard

**ALWAYS** use the [Conventional Commits](https://www.conventionalcommits.org/) standard for commit messages.

**Format:**
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semicolons, etc)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to build process, dependencies, or auxiliary tools
- `perf`: Performance improvements
- `ci`: CI/CD configuration changes

**Examples:**
```bash
git commit -m "feat: add forbid-vars hook to detect meaningless variable names"
git commit -m "fix: handle syntax errors gracefully in AST parsing"
git commit -m "docs: update README with installation instructions"
git commit -m "refactor: migrate to src layout structure"
git commit -m "test: add edge cases for multiple inheritance"
git commit -m "chore: update dependencies to latest versions"
```

**Rules:**
- Use lowercase for type and description
- Keep description under 72 characters
- Use imperative mood ("add" not "added" or "adds")
- No period at the end of the description

<!-- MANUAL ADDITIONS END -->
