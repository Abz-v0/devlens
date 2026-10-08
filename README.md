# DevLens

**A simple Python CLI tool that helps developers understand and improve their projects.**

DevLens is a command-line tool for analyzing and improving Python projects. It scans projects for common issues, calculates a Health Score, saves and searches reusable code snippets, scaffolds new projects, and explains individual Python files.

DevLens was built as my final project for **CS50P: Introduction to Programming with Python**.

#### Video Demo: <https://youtu.be/EdKJAALavkw>

---

## Table of Contents

- [Description](#description)
- [Features](#features)
- [Installation](#installation)
- [Usage Examples](#usage-examples)
- [Running the Tests](#running-the-tests)
- [How the Health Score Works](#how-the-health-score-works)
- [Design Decisions](#design-decisions)
- [Project Structure](#project-structure)
- [Dependencies](#dependencies)
- [V2 Roadmap](#v2-roadmap)
- [Author](#author)
- [License](#license)

---

## Description

DevLens is a command-line tool written in Python that helps developers analyze and improve the quality of their Python projects.

It can scan an entire project for common issues, calculate a Health Score, save useful code snippets for later reuse, scaffold new projects, and explain the structure of individual Python files.

I created DevLens as my final project for CS50P. I wanted to build something that went beyond a single-purpose script and combined several Python concepts into one practical command-line application.

The project uses Python's standard library for its core functionality, including `argparse`, `ast`, `pathlib`, `json`, `shutil`, and `datetime`.

---

## Features

| Command | What it does |
| :--- | :--- |
| `uv run devlens scan <path>` | Analyzes a Python project, finds common issues, checks project structure, and calculates a Health Score. |
| `uv run devlens create <name>` | Scaffolds a new Python project with a basic structure. |
| `uv run devlens explain <file>` | Analyzes a Python file and displays its imports, classes, functions, and detected issues. |
| `uv run devlens save <file>` | Saves a useful code file or snippet to the DevLens Vault. |
| `uv run devlens search <query>` | Searches the Vault for saved snippets matching a query. |
| `uv run devlens get <name>` | Retrieves and displays a saved snippet from the Vault. |

---

## Installation

DevLens uses only the Python standard library for its runtime functionality.

Development dependencies such as `pytest`, Ruff, and Pyrefly are managed with `uv`.

Clone the repository:

```bash
git clone https://github.com/Abz-v0/devlens.git
cd devlens
````

Sync the project environment and dependencies:

```bash
uv sync
```

You can then run DevLens with:

```bash
uv run devlens scan .
```

### Requirements

* Python 3.14 or later
* Git, if cloning the repository
* `uv`

---

## Usage Examples

### Scanning a Project

Use the `scan` command to analyze a Python project:

```bash
uv run devlens scan .
```

DevLens examines the project's Python files and reports information such as:

* Number of Python files
* Classes and functions
* TODO comments
* Long functions
* Possible security issues
* Project structure
* Overall Health Score

Example output:

```text
──────────────────────────────────────────────────
DevLens Scan: .
──────────────────────────────────────────────────
2 Python files found.

project.py (550 lines)
··················································
  ├─ Classes (1): Color
  └─ Functions (22):
      • get_vault_dir
      • get_index_path
      • load_index
      • save_index
      • save_snippet
      • search_snippets
      • ...and 16 more

  ⚠ Long functions (3):
    • analyze_file (37 lines)
    • detect_security_issues (35 lines)
    • main (219 lines)

tests\test_project.py (352 lines)
··················································
  └─ Functions (34):
      • mock_home
      • test_get_vault_dir_creates_folder_under_fake_home
      • test_save_and_load_index_round_trip
      • test_save_snippet_copies_file_and_updates_index
      • test_save_snippet_returns_false_for_invalid_file
      • test_search_snippets_finds_matching_names
      • ...and 28 more

  ⚠ TODOs (4):
    • line 195: todo_file.write_text("# TODO validate entry")
    • line 196: assert detect_todos(todo_file) == [(1, "# TODO validate entry")]
    • line 348: "# TODO change pass to actual logic"
    • line 349: "# TODO add input counter"

  ⚠ Long functions (2):
    • test_scan_project_returns_python_files (25 lines)
    • test_file_in_good_health (21 lines)

  ⚠ Security issues (2):
    • line 241: possible hardcoded secret: tmp_file.write_text('password = "supersecret123"')
    • line 243: possible hardcoded secret: assert result == [(1, 'possible hardcoded secret: password = "supersecret123"')]

──────────────────────────────────────────────────
Project Structure
──────────────────────────────────────────────────
  ✓ Project structure looks good

══════════════════════════════════════════════════
Health Score: █████████████░░░░░░░ 67/100
══════════════════════════════════════════════════
```

The example above shows DevLens detecting issues in both the main application and its test suite. The detected TODOs, long functions, and possible hardcoded secrets demonstrate the types of problems DevLens is designed to identify.

### Creating a New Project

Use the `create` command to scaffold a new project:

```bash
uv run devlens create my-app
```

This creates a basic project structure containing:

```text
my-app/
├── main.py
├── README.md
├── requirements.txt
└── tests/
    └── test_main.py
```

### Explaining a File

Use the `explain` command to inspect an individual Python file:

```bash
uv run devlens explain main.py
```

DevLens reports the file's imports, classes, functions, and detected problems.

### Saving a Snippet

Save a useful file to the DevLens Vault:

```bash
uv run devlens save example.py
```

### Searching the Vault

Search previously saved snippets:

```bash
uv run devlens search sorting
```

### Retrieving a Snippet

Retrieve a saved snippet by name:

```bash
uv run devlens get example.py
```

---

## Running the Tests

The project includes an automated test suite covering the major parts of DevLens.

Run the tests with:

```bash
uv run pytest
```

The tests cover functionality including:

* Vault directory and index management
* Saving and searching snippets
* Project scanning
* TODO detection
* Security issue detection
* Health Score calculation
* Project creation
* File analysis

The test suite currently contains **33 tests**, all of which pass.

```text
33 passed
```

DevLens itself does not require `pytest` to run. `pytest` is used for development and testing.

---

## How the Health Score Works

DevLens starts each project with a score of **100**.

Points are then deducted based on four categories:

* **Structure — 20 points:** Checks whether `README.md` and `requirements.txt` exist.
* **Code Quality — 30 points:** Checks for TODO comments and functions longer than 20 lines.
* **Security — 25 points:** Looks for potentially dangerous uses of `eval()` and possible hardcoded secrets.
* **Testing — 25 points:** Checks whether a `tests/` folder exists and whether it contains test files.

Each category has a maximum deduction.

I deliberately added these caps so that a project with many issues in one category does not automatically receive an extremely low score. This keeps the different categories balanced.

The Health Score is intended as a simple indicator of project health rather than a replacement for a full static analysis or security tool.

---

## Design Decisions

While building DevLens, I made several deliberate design decisions.

### 1. Standard Library Only

I chose to use Python's standard library for the application itself. This keeps DevLens simple and allowed me to focus on Python's built-in tools and language features.

### 2. AST + Text Scanning

DevLens uses Python's `ast` module to analyze the structure of Python code.

This allows it to identify things such as:

* Functions
* Classes
* Imports
* `eval()` calls

For TODOs and possible hardcoded secrets, I use text-based scanning instead. This is useful because TODOs may appear in comments and simple text patterns can identify suspicious strings without requiring a full AST-based approach.

### 3. Capped Scoring System

The Health Score uses separate limits for each category.

Without caps, a project with a large number of TODOs or long functions could lose most of its score because of one type of issue. The caps keep the different categories balanced.

### 4. Simple Vault Design

The DevLens Vault stores saved snippets as normal files and maintains a small JSON index.

I chose this design instead of using a database because the Vault does not require the complexity of a database. The files and JSON index are easy to understand, inspect, and debug.

### 5. Readable Terminal Output

I designed the terminal output to make scan results easy to understand at a glance.

DevLens uses sections, ANSI colors, symbols, and a visual Health Score bar to separate different types of information.

---

## Project Structure

```text
devlens/
├── src/
│   └── devlens/
│       ├── __init__.py
│       └── project.py
├── tests/
│   └── test_project.py
├── .gitignore
├── .python-version
├── pyproject.toml
├── uv.lock
├── PROGRESS.md
└── README.md
```

### `src/devlens/project.py`

Contains the command-line interface, built with `argparse`, along with the core DevLens functionality:

* Project scanning
* Issue detection
* Health Score calculation
* Vault management
* Project creation
* File explanation

### `tests/test_project.py`

Contains the automated test suite for DevLens. The tests cover the major functions and features, including scanning, issue detection, Health Score calculation, Vault operations, and project creation.

### `pyproject.toml`

Contains the project's metadata, Python version requirement, CLI entry point, and development dependencies.

### `uv.lock`

Contains the locked dependency information used by `uv` to reproduce the project environment consistently.

### `README.md`

Contains documentation explaining the project, installation, usage, design decisions, and future plans.

---

## Dependencies

### Runtime Dependencies

DevLens itself uses only the Python standard library.

The main modules used include:

* `argparse`
* `ast`
* `json`
* `pathlib`
* `shutil`
* `datetime`

### Development Dependencies

Development and testing tools are managed through `uv`.

These currently include:

* `pytest`
* Ruff
* Pyrefly

Sync the project environment with:

```bash
uv sync
```

---

## V2 Roadmap

After submitting DevLens for CS50P, I plan to continue developing it.

Possible improvements include:

* Support for both `requirements.txt` and `pyproject.toml` project manifests
* Configuration file support, such as `.devlens.toml`
* JSON and Markdown report exports
* Dependency analysis
* Improving the Vault with tags and categories
* Adding more project templates, such as Flask applications and APIs
* Adding a plugin system for custom detection rules
* Extracting individual functions or classes from Vault snippets

These features are planned for future versions and are not part of the current CS50P submission.

---

## Author

Built by **Abraham Azeez** as a final project for **CS50P — Introduction to Programming with Python**.

GitHub: [https://github.com/Abz-v0/devlens](https://github.com/Abz-v0/devlens)

---

## License

MIT License

```
```