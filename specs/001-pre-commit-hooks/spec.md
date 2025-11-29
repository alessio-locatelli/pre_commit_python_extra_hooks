# Feature Specification: Custom Pre-Commit Hooks Repository

**Feature Branch**: `001-pre-commit-hooks`
**Created**: 2025-11-28
**Status**: Draft
**Input**: User description: "In this repository I want you create and maintain my custom pre-commit hooks (very similar to https://github.com/pre-commit/pre-commit-hooks)."

## Clarifications

### Session 2025-11-28

- Q: What is the initial hook count for the MVP delivery? → A: Start with 1 hook (absolute minimum - proves concept but doesn't meet SC-005)
- Q: What is the repository distribution method? → A: Public GitHub repository
- Q: Where should documentation be located? → A: README.md in repository root
- Q: How should Python hook dependencies be managed? → A: No external dependencies (stdlib only)
- Q: What should the first hook's purpose be? → A: Forbid specific variable names

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Using Custom Hooks in a Project (Priority: P1)

A developer wants to integrate custom pre-commit hooks into their project to enforce code quality standards that aren't available in the standard pre-commit-hooks repository. They add this repository to their `.pre-commit-config.yaml` file, and the hooks automatically run before each commit to catch issues.

**MVP Scope**: Initial delivery includes 1 custom hook that forbids specific variable names in source code files. This hook demonstrates the full integration workflow including pattern matching, file processing, and actionable error reporting. Additional hooks will be added in subsequent phases to reach the 5+ hook target (SC-005).

**Why this priority**: This is the core value proposition - developers must be able to actually use the hooks in their projects. Without this working, the repository has no value.

**Independent Test**: Can be fully tested by adding the repository to a sample project's pre-commit configuration, making a commit that should trigger the hooks, and verifying the hooks execute correctly and catch the expected issues.

**Acceptance Scenarios**:

1. **Given** a project with pre-commit installed, **When** a developer adds this repository to `.pre-commit-config.yaml` and runs `pre-commit install`, **Then** the hooks are registered and ready to execute
2. **Given** configured hooks in a project, **When** a developer attempts to commit code that violates hook rules, **Then** the commit is blocked and clear error messages indicate what needs to be fixed
3. **Given** configured hooks in a project, **When** a developer commits code that passes all hook checks, **Then** the commit proceeds successfully without errors
4. **Given** a project using these hooks, **When** a developer runs `pre-commit run --all-files`, **Then** all hooks execute across the entire codebase and report any issues found

---

### User Story 2 - Adding New Custom Hooks (Priority: P2)

A developer identifies a recurring code quality issue in their team's workflow that isn't addressed by existing pre-commit hooks. They create a new custom hook by adding a script to this repository, configure the hook metadata, and test it locally before contributing it.

**Why this priority**: The repository needs to be maintainable and extensible. Once the initial hooks work (P1), the ability to add new hooks enables the repository to grow and serve more use cases.

**Independent Test**: Can be tested by creating a new hook script, adding its configuration, and verifying it can be used in a test project just like the existing hooks.

**Acceptance Scenarios**:

1. **Given** a need for a new validation check, **When** a developer creates a new hook script following the repository's structure, **Then** the script can be executed independently and returns appropriate exit codes (0 for success, non-zero for failure)
2. **Given** a new hook script, **When** a developer adds the hook configuration to the repository metadata, **Then** the hook becomes discoverable and usable in pre-commit configurations
3. **Given** a newly added hook, **When** a developer tests it against sample files (both passing and failing cases), **Then** the hook correctly identifies issues and provides helpful error messages
4. **Given** multiple hooks in the repository, **When** a developer views the repository documentation, **Then** each hook's purpose, usage, and configuration options are clearly described

---

### User Story 3 - Maintaining and Updating Hooks (Priority: P3)

As the repository evolves, existing hooks may need bug fixes, performance improvements, or feature enhancements. Developers can update hook implementations while maintaining backward compatibility with projects already using them.

**Why this priority**: This ensures long-term sustainability but is lower priority than getting hooks working (P1) and being able to add new ones (P2). Initial maintenance can be manual.

**Independent Test**: Can be tested by modifying an existing hook, verifying the change works correctly, and confirming existing projects using the hook still function as expected.

**Acceptance Scenarios**:

1. **Given** a bug report for an existing hook, **When** a developer fixes the issue and tests against the reported case, **Then** the hook no longer exhibits the buggy behavior
2. **Given** an updated hook version, **When** projects using the hook run `pre-commit autoupdate`, **Then** they receive the latest version without breaking their existing configuration
3. **Given** hooks that support various file types or languages, **When** a developer adds support for a new file type, **Then** the hook correctly processes both new and existing supported types
4. **Given** performance concerns with a hook, **When** a developer optimizes the implementation, **Then** hook execution time decreases measurably without changing the validation behavior

---

### Edge Cases

- What happens when a hook is run on file types it doesn't support (should skip gracefully)?
- How does the system handle hooks that encounter unexpected errors (should fail safely and report clearly)?
- What happens when hooks are run in environments with missing system tools (e.g., Bash hooks on systems without bash, should provide clear error messages)?
- How are hooks versioned when breaking changes are necessary (should use semantic versioning in repository tags)?
- What happens when multiple hooks conflict in their file modifications (should have clear execution order and conflict resolution)?
- How does the forbid-vars hook handle partial matches (e.g., should "myVar" be flagged if "Var" is forbidden, or only exact matches)? **RESOLVED**: The hook uses case-sensitive exact matching only. "Var" will not match "myVar" or "var". This ensures predictable behavior and avoids false positives.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Repository MUST be compatible with the pre-commit framework's hook repository format
- **FR-002**: Each hook MUST include metadata defining its entry point, supported file types, and execution requirements
- **FR-003**: Hooks MUST return exit code 0 for success and non-zero for failure to integrate correctly with pre-commit
- **FR-004**: Hooks MUST provide clear, actionable error messages when they fail, indicating what issue was found and where
- **FR-005**: Repository MUST include a README.md in the repository root documenting each hook's purpose, usage examples, and configuration options
- **FR-006**: Hooks MUST be testable independently without requiring git or pre-commit framework
- **FR-007**: Repository MUST include example configurations showing how to use hooks in `.pre-commit-config.yaml`
- **FR-008**: Each hook MUST specify its supported languages and file types in the hook metadata
- **FR-009**: Hooks MUST handle file path arguments passed by the pre-commit framework
- **FR-010**: Repository MUST follow a consistent structure for organizing hook scripts and supporting files
- **FR-011**: Repository MUST use git tags with semantic versioning for releases to enable `pre-commit autoupdate` functionality
- **FR-012**: Python-based hooks MUST use only Python standard library (no external dependencies) to maximize portability and minimize installation complexity
- **FR-013**: The initial "forbid-vars" hook MUST scan source files for forbidden variable names and reject commits containing them, with clear error messages indicating the forbidden name and its location

### Key Entities

- **Hook Script**: The executable code that performs the validation or transformation. Contains the core logic, accepts file paths as arguments, and returns appropriate exit codes.
- **Hook Metadata**: Configuration information defining how pre-commit should invoke the hook. Includes entry point, name, description, file type filters, and language requirements.
- **Repository Configuration**: Files that define the overall repository structure and make it discoverable by pre-commit. Includes `.pre-commit-hooks.yaml` and version management information.
- **Documentation**: User-facing descriptions of each hook's functionality in README.md. Includes usage examples, configuration options, and troubleshooting guidance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can add the repository to their pre-commit configuration and have hooks execute successfully on the first try
- **SC-002**: Each hook processes files and reports results in under 5 seconds when checking fewer than 1000 files passed by pre-commit. **Measurement**: This applies to files matching the hook's filter pattern (e.g., Python files for forbid-vars), not all repository files. Measured as wall-clock time from hook invocation to exit.
- **SC-003**: Hook error messages are clear enough that issues can be resolved without consulting external documentation. **Validation**: Error messages must include (1) what failed, (2) where it failed (file:line), and (3) how to fix it or link to guidance. Measured qualitatively through manual review during testing phases and user feedback in initial releases.
- **SC-004**: New hooks can be added to the repository and become functional in under 30 minutes of development time
- **SC-005**: The repository supports at least 5 different custom hooks addressing distinct code quality concerns. **MVP Exception**: Initial delivery (v1.0.0) includes 1 hook to prove the concept and framework compatibility. Subsequent releases (v1.1.0+) will add 4+ additional hooks to reach the 5-hook target. This criterion is satisfied when the repository demonstrates the *capability* to scale to multiple hooks through clear documentation and extensibility patterns (User Story 2).
- **SC-006**: Hooks work correctly across different operating systems (Linux, macOS, Windows) without modification

### Assumptions

- Developers using these hooks already have the pre-commit framework installed in their projects
- Users are familiar with basic pre-commit concepts and have used standard hooks before
- The repository will be publicly accessible on GitHub and referenced via GitHub URLs in `.pre-commit-config.yaml` files
- Hook scripts will primarily target common file types (text files, source code, configuration files)
- Standard development tools and interpreters (Python, Bash, etc.) are available in the environments where hooks run
