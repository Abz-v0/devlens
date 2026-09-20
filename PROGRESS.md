## Day 63 - Sept 20, 2026
- Created dedicated devlens repo, separate from python-practice
- Added .gitignore (excludes __pycache__, .pytest_cache, .venv, app.py, practice_todo.py)
- Pushed project.py and test_project.py as the initial commit
- Set up pytest-watch (using `python -m pytest_watch` since `ptw` isn't on PATH)
- Added detect_todos(): finds real `# TODO` comments in a file
- Fixed a false-positive bug: "TODO" appearing inside strings/print statements (no `#` before it) was wrongly flagged as a real TODO — fixed using str.split("#", 1) to only search the part after the comment marker
- Added 3 tests for detect_todos (real TODO, false positive without hash, no TODOs)
- Next: width-based inline packing for short function/class names (e.g. f2, f3) instead of always one-per-line