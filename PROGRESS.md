## Day 63 - Sept 20, 2026
- Created dedicated devlens repo, separate from python-practice
- Added .gitignore (excludes __pycache__, .pytest_cache, .venv, app.py, practice_todo.py)
- Pushed project.py and test_project.py as the initial commit
- Set up pytest-watch (using `python -m pytest_watch` since `ptw` isn't on PATH)
- Added detect_todos(): finds real `# TODO` comments in a file
- Fixed a false-positive bug: "TODO" appearing inside strings/print statements (no `#` before it) was wrongly flagged as a real TODO — fixed using str.split("#", 1) to only search the part after the comment marker
- Added 3 tests for detect_todos (real TODO, false positive without hash, no TODOs)
- Next: width-based inline packing for short function/class names (e.g. f2, f3) instead of always one-per-line

## Day 64 - Sept 21, 2026
- Redesigned Classes/Functions display: short lists now print inline on one line (e.g. "Functions (10): main, f1, f2..."), long lists stay bulleted one-per-line — decided using total combined character length (sum of name lengths), not item count or per-name length
- Fixed indentation consistency across inline, bulleted, and overflow lines
- Learned ast.parse() strips comments entirely — TODOs can only be found via text scanning (current approach) or Python's tokenize module (not used yet); known limitation: detect_todos can false-positive on "# TODO" appearing inside strings/text, not just real comments
- Added detect_long_functions(): flags functions over 20 lines using node.lineno/end_lineno, handling the rare case where end_lineno is None
- Wired long-function detection into scan's report output
- Added 2 tests for detect_long_functions (flags a 22-line function, ignores a short one)
- Committed and pushed
- Fixed a crash: analyze_file and detect_long_functions now catch SyntaxError so scanning one invalid/broken Python file doesn't crash the entire scan — found via an automated code review, evaluated its other suggestions (async def support, exit codes, sort order) and logged them as known items rather than fixing everything at once

## Day 65 - Sept 22, 2026

- Implemented `check_project_structure(path)`
  - Checks for the presence of `README.md`, `requirements.txt`, and a real `tests/` directory
  - Returns a simple list of whichever items are missing
  - Uses an `expected` list of `(name, type)` pairs so it’s easy to extend later
- Wired the structure check into the `scan` command (runs once on the project root, after the file loop)
- Added full unit tests for the new function:
  - Perfect structure → empty list
  - Missing only README
  - Missing only requirements.txt
  - Missing only tests folder
  - Everything missing
  - `tests` exists but is a file instead of a directory
- Fixed several bugs along the way (hard-coded names in the missing list, calling the check on individual files instead of the project root, wrong pathlib methods)
- Next: health score calculation

## Day 66 - Sept 23, 2026
- Added check_project_structure(): verifies README.md and requirements.txt exist
- Added calculate_health_score(): combines structure, code quality, security, and testing into a 0-100 score (structure 20pts, code quality 30pts, security 25pts, testing 25pts, each independently capped)
- Added calculate_testing_deduction(): checks for a tests/ folder and real test files inside it (test_*.py or *_test.py patterns), not just folder existence
- Fixed the security false-positive from last session: detect_security_issues now skips its own suspicious_words definition line
- Added ast.AsyncFunctionDef support to analyze_file and detect_long_functions (closes a gap from the earlier code review)
- Wrote 12 new tests covering structure checks, testing deduction, and full health-score scenarios (verified deduction math by hand before asserting)
- scan is now feature-complete against the original V1 checklist
- Next: vault command (save/search/get with local JSON storage)

## Day 67 - Sept 24, 2026
- Polished scan output: Added raw ANSI colors (warnings in yellow/red, success in green, file headers in cyan) using a custom Color class
- Added a visual progress bar for the Health Score (dynamically colors green/yellow/red based on score)
- Restructured main() print statements for cleaner spacing, dotted file separators, and better visual hierarchy
- Design choice: Chose raw ANSI escape codes over third-party libraries (like colorist) to keep DevLens completely dependency-free
- Fixed a UnicodeDecodeError on Windows by enforcing encoding="utf-8" across all path.read_text() calls
- Fixed detect_todos to use startswith("TODO") to prevent flagging comments that merely mention the word
- Did a deep-dive code review to understand AST vs text processing, capped deductions, and Python file encodings
- Next: Start building the vault command from scratch (local JSON storage for snippets)

## Day 68 - Sept 25, 2026
- Started Phase 3: Building the vault command (local code snippet library)
- Planned hybrid architecture: store actual .py files in ~/.devlens/vault/ and track metadata in index.json
- Implemented get_vault_dir(): uses Path.home() to dynamically create the hidden .devlens/vault/ directory cross-platform
- Next: Implement load_index() and save_index() using Python's json module

## Day 68 - Sept 25, 2026
- Started vault command: Designed hybrid storage architecture (raw files for code, JSON index for metadata)
- Implemented backend logic functions: get_vault_dir(), load_index(), save_index()
- Implemented save_snippet() (copies file to vault, updates JSON index with UTC timestamp)
- Realized shutil.copy2 can natively preserve file metadata, will swap out manual datetime logic tomorrow for cleaner code
- Implemented search_snippets() (uses list comprehension over JSON index keys)
- Implemented get_snippet() (returns Path or None)
- Separated concerns: logic functions return data/booleans, CLI handles the printing/colors
- Wired up save, search, and get subparsers in main()
- Next: Swap to shutil.copy2, complete the main() CLI logic for vault commands, and test the workflow