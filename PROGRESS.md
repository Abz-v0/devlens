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