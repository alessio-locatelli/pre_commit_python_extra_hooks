# Feature Specification: Auto-Fixing Patterns for forbid-vars Hook

**Feature Branch**: `003-forbid-vars-autofixing`
**Created**: 2025-12-01
**Status**: Draft
**Input**: User description: "I want to brainstorm and add some auto-fixing patterns to the `forbid-vars` hook."

## Clarifications

### Session 2025-12-01

- Q: Should auto-fixes be automatically applied, or presented as suggestions for manual review? → A: Configurable via command-line flag (e.g., `--fix` to apply). Default behavior is suggest-only (report what should change), with optional `--fix` flag to auto-apply changes.
- Q: Should it use first match, most specific match, present all options, or flag as ambiguous when multiple patterns could apply? → A: Use most specific match (longest/most detailed pattern). Rank patterns by specificity to give the best suggestion.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Variable Renaming for Network/HTTP Code (Priority: P1)

Developers using the forbid-vars hook can automatically fix violations where forbidden variable names (like `data`, `result`) are assigned from HTTP library calls. Instead of manually reviewing error messages and renaming variables, the hook suggests correct names based on the library and method used (and optionally applies them with the `--fix` flag).

**Why this priority**: Network/HTTP code represents the most common and unambiguous use case. HTTP libraries have standardized return types (`Response` objects), making automatic renaming safe and predictable. This delivers immediate value by handling the highest-volume violation category.

**Independent Test**: Can be fully tested by running the hook on files containing `result = requests.get(url)` patterns and verifying it suggests/applies `response = requests.get(url)`. Delivers value by eliminating manual fixes for HTTP-related violations.

**Acceptance Scenarios**:

1. **Given** a Python file contains `result = requests.get(url)`, **When** the hook runs in default mode, **Then** it reports a suggestion to replace with `response = requests.get(url)` without modifying the file
2. **Given** a Python file contains `result = requests.get(url)`, **When** the hook runs with `--fix` flag, **Then** it automatically replaces the line with `response = requests.get(url)`
3. **Given** a Python file contains `data = response.json()`, **When** the hook runs, **Then** it suggests the replacement `payload = response.json()`
4. **Given** a Python file contains HTTP code with an inline ignore comment, **When** the hook runs, **Then** it respects the ignore directive and makes no suggestions or changes

---

### User Story 2 - Automatic Variable Renaming for File I/O Code (Priority: P2)

Developers working with file operations can automatically fix violations where forbidden names are used for file handles or file content. The hook distinguishes between file handles (`open()`) and file content (`.read()`), suggesting appropriate names for each.

**Why this priority**: File I/O is another frequent source of violations with clear semantic distinctions (handle vs content). While slightly more complex than HTTP (due to multiple file methods), it's still highly predictable and delivers significant value.

**Independent Test**: Can be fully tested by running the hook on files containing `data = open('file.txt')` and verifying it suggests `file_handle = open('file.txt')`. Independently valuable for file-heavy codebases.

**Acceptance Scenarios**:

1. **Given** a Python file contains `data = open('config.txt')`, **When** the auto-fix hook runs, **Then** it suggests `file_handle = open('config.txt')`
2. **Given** a Python file contains `result = file.read()`, **When** the auto-fix hook runs, **Then** it suggests `content = file.read()`
3. **Given** a Python file contains `data = Path('file.txt').read_text()`, **When** the auto-fix hook runs, **Then** it suggests `file_content = Path('file.txt').read_text()`
4. **Given** a Python file contains `result = json.load(f)`, **When** the auto-fix hook runs, **Then** it suggests `parsed_data = json.load(f)`

---

### User Story 3 - Automatic Variable Renaming for Database/ORM Code (Priority: P3)

Developers working with databases can automatically fix violations where forbidden names are used for database operations. The hook recognizes ORM patterns and database method calls, suggesting appropriate names based on the operation type (cursor, row, rows, queryset, etc.).

**Why this priority**: Database operations have clear semantic patterns but more variation than HTTP or file I/O (raw SQL vs ORM, different frameworks). Still delivers value but has higher complexity and lower universality.

**Independent Test**: Can be fully tested by running the hook on files containing `result = cursor.execute(query)` and `data = cursor.fetchall()`, verifying correct suggestions for each. Valuable for database-heavy applications.

**Acceptance Scenarios**:

1. **Given** a Python file contains `result = cursor.execute(query)`, **When** the auto-fix hook runs, **Then** it suggests `cursor = cursor.execute(query)` (note: some DB libraries return cursor)
2. **Given** a Python file contains `data = cursor.fetchall()`, **When** the auto-fix hook runs, **Then** it suggests `rows = cursor.fetchall()`
3. **Given** a Python file contains `result = Model.objects.filter(name='foo')`, **When** the auto-fix hook runs, **Then** it suggests `queryset = Model.objects.filter(name='foo')`
4. **Given** a Python file contains `data = Model.objects.get(id=1)`, **When** the auto-fix hook runs, **Then** it suggests `instance = Model.objects.get(id=1)`

---

### User Story 4 - Automatic Variable Renaming for Data Science Code (Priority: P4)

Developers using data science libraries can automatically fix violations where forbidden names are used for DataFrames, arrays, or regex matches. The hook recognizes pandas, numpy, and regex patterns, applying community-standard naming conventions.

**Why this priority**: Data science code has strong conventions (`df` for DataFrames, `arr` for arrays, `match` for regex) but is less universal than the previous categories. Valuable for data-focused projects but not all codebases use these libraries.

**Independent Test**: Can be fully tested by running the hook on files containing `data = pd.read_csv('file.csv')` and verifying it suggests `df = pd.read_csv('file.csv')`. Delivers value specifically for data science workflows.

**Acceptance Scenarios**:

1. **Given** a Python file contains `data = pd.read_csv('sales.csv')`, **When** the auto-fix hook runs, **Then** it suggests `df = pd.read_csv('sales.csv')`
2. **Given** a Python file contains `data = np.array([1, 2, 3])`, **When** the auto-fix hook runs, **Then** it suggests `arr = np.array([1, 2, 3])`
3. **Given** a Python file contains `result = re.search(r'\d+', text)`, **When** the auto-fix hook runs, **Then** it suggests `match = re.search(r'\d+', text)`
4. **Given** a Python file contains `result = re.findall(r'\w+', text)`, **When** the auto-fix hook runs, **Then** it suggests `matches = re.findall(r'\w+', text)`

---

### User Story 5 - Semantic Function Name Pattern Matching (Priority: P5)

Developers using functions with semantic names (like `get_user()`, `find_order()`, `create_session()`) can automatically fix violations by extracting the meaningful noun from the function name and using it as the variable name.

**Why this priority**: This is the most advanced pattern with highest risk of false positives. While valuable when it works correctly, it requires careful analysis of function naming patterns and may not be universally applicable. Provides polish but not critical functionality.

**Independent Test**: Can be fully tested by running the hook on files containing `result = api.get_user_id()` and verifying it suggests `user_id = api.get_user_id()`. Delivers incremental value for codebases with consistent naming conventions.

**Acceptance Scenarios**:

1. **Given** a Python file contains `result = api.get_user()`, **When** the auto-fix hook runs, **Then** it suggests `user = api.get_user()`
2. **Given** a Python file contains `data = service.find_orders()`, **When** the auto-fix hook runs, **Then** it suggests `found_orders = service.find_orders()` or `orders = service.find_orders()`
3. **Given** a Python file contains `result = factory.create_session()`, **When** the auto-fix hook runs, **Then** it suggests `new_session = factory.create_session()` or `session = factory.create_session()`
4. **Given** a Python file contains `data = utils.is_valid(x)`, **When** the auto-fix hook runs, **Then** it suggests `is_valid = utils.is_valid(x)`

---

### Edge Cases

- How does the system handle situations where the suggested name already exists in the same scope?
- What happens when the right-hand side expression is complex (multiple chained method calls)?
- How does the system handle cases where the auto-fix suggestion itself would be a forbidden name?
- What happens when a file contains syntax errors that prevent AST parsing?
- How does the system handle multi-line assignments or assignments within comprehensions?
- How does the system handle false positives where `data` or `result` is actually the correct semantic name?
- What happens when the auto-fix pattern matches but the context suggests the generic name is actually appropriate?
- How should pattern specificity be calculated when ranking multiple matches (by regex length, by category priority, or by exact vs partial match)?
- What happens when `--fix` flag is used but the suggested fix would break the code (e.g., name collision)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST analyze the right-hand side (RHS) of assignment expressions to determine if an auto-fix pattern applies
- **FR-002**: System MUST support pattern matching for HTTP/network libraries (requests, httpx, aiohttp, urllib)
- **FR-003**: System MUST support pattern matching for file I/O operations (open(), Path.read_text(), json.load())
- **FR-004**: System MUST support pattern matching for database operations (cursor.execute(), .fetchall(), ORM methods)
- **FR-005**: System MUST support pattern matching for data science libraries (pandas, numpy, regex)
- **FR-006**: System MUST support semantic pattern extraction from function names (get_X, find_X, create_X patterns)
- **FR-007**: System MUST respect existing inline ignore comments and not suggest fixes for suppressed violations
- **FR-008**: System MUST support configurable fix application mode: default behavior reports suggested changes without modifying files, with optional command-line flag (e.g., `--fix`) to enable automatic application of fixes
- **FR-009**: System MUST handle cases where multiple patterns could apply by selecting the most specific match (longest or most detailed pattern), ranking patterns by their specificity level
- **FR-010**: System MUST validate that suggested replacements do not create new violations or conflicts
- **FR-011**: System MUST provide clear feedback to users about what was changed (if auto-applying) or what should change (if suggesting)
- **FR-012**: System MUST gracefully handle files with syntax errors by skipping auto-fix analysis (consistent with current hook behavior)
- **FR-013**: System MUST preserve code formatting and indentation when applying fixes
- **FR-014**: System MUST only analyze assignment contexts where forbidden names are found (do not scan files without violations)
- **FR-015**: Users MUST be able to configure which auto-fix patterns are enabled
- **FR-016**: Users MUST be able to add custom auto-fix patterns without modifying core hook code

### Key Entities

- **Auto-Fix Pattern**: Represents a rule that maps a code pattern (RHS expression) to a suggested variable name, including: trigger regex (what to match on RHS), suggested replacement name, confidence level, and category (HTTP, File I/O, Database, etc.)
- **Violation**: A detected use of a forbidden variable name, including: variable name, line number, file path, and (new) applicable auto-fix pattern if one matches
- **Fix Suggestion**: A proposed change to resolve a violation, including: original name, suggested name, line number, rationale (which pattern matched), and confidence level

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can resolve at least 70% of HTTP-related forbid-vars violations without manual variable renaming
- **SC-002**: The hook correctly identifies auto-fix opportunities for the five major categories (HTTP, File I/O, Database, Data Science, Semantic) with 90%+ accuracy (no incorrect suggestions)
- **SC-003**: Developers can enable or disable specific auto-fix pattern categories through configuration
- **SC-004**: Processing time for files with violations increases by less than 50% when auto-fix analysis is enabled
- **SC-005**: Zero false positive auto-fix suggestions are applied (suggested name is always semantically appropriate for the context)
- **SC-006**: Developers can add custom auto-fix patterns without requiring code changes to the hook (configuration-based extensibility)

## Assumptions

- Auto-fix patterns are based on common Python library conventions (requests, pandas, Django ORM, etc.) that are widely recognized in the community
- Developers using this hook are writing Python code that follows conventional naming patterns for library usage
- The existing AST-based violation detection mechanism can be extended to analyze RHS expressions
- Auto-fix suggestions will not attempt to analyze complex semantic context beyond pattern matching (e.g., won't understand business logic to suggest domain-specific names)
- Initial implementation will focus on the patterns documented in feature.md, with extensibility for future additions
- The hook will maintain backward compatibility with existing configurations and ignore comments

## Dependencies

- Existing forbid-vars hook must be functional and capable of detecting forbidden variable names
- Hook must support analyzing both variable names and their assigned values to enable pattern matching
