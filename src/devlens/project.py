import argparse
import ast
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"

class FileAnalysis(TypedDict):
    lines: int
    functions: list[str]
    classes: list[str]
    imports: list[str]

def get_vault_dir():
    """Returns the path to the vault directory, creating it if it doesn't exist."""
    vault_dir = Path.home() / ".devlens" / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    return vault_dir

def get_index_path():
    """Returns the path to the index.json file."""
    return Path.home() / ".devlens" / "index.json"

def load_index():
    """Loads the JSON index, returning an empty dict if it doesn't exist yet."""
    index_path = get_index_path()
    if index_path.exists():
        try:
            return json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}

def save_index(data):
    """Saves the dictionary back to index.json."""
    index_path = get_index_path()
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(data, indent=4), encoding="utf-8")

def save_snippet(file_path):
    """Copies a file into the vault and updates the index."""
    if not file_path.exists() or not file_path.is_file():
        return False

    dest_path = get_vault_dir() / file_path.name
    shutil.copy2(file_path, dest_path)

    index = load_index()
    current_time = datetime.now(UTC).strftime("%Y-%m-%d--%H:%M:%S%z")

    index[file_path.name] = {
        "original_path": str(file_path),
        "saved_at": current_time
    }
    save_index(index)
    return True

def search_snippets(query):
    """Searches the index for snippet names matching the query."""
    index = load_index()
    matches = [name for name in index if query.lower() in name.lower()]

    return matches

def get_snippet(name):
    path = get_vault_dir() / name

    if path.exists() and path.is_file():
        return path
    else:
        return None

def create_project(name):
    project_dir = Path.cwd() / name

    if project_dir.exists():
        return False

    project_dir.mkdir()
    (project_dir / "tests").mkdir()
    (project_dir / "main.py").touch()
    (project_dir / "README.md").write_text(f"# {name}")
    (project_dir / "requirements.txt").touch()
    (project_dir / "tests" / "test_main.py").touch()

    return True

def get_score_bar(score):
    """Returns a visual progress bar for the health score."""
    bar_length = 20
    filled_length = (round(bar_length * score / 100))
    bar = "█" * filled_length + "░" * (bar_length - filled_length)
    
    if score >= 80:
        color = Color.GREEN
    elif score >= 50:
        color = Color.YELLOW
    else:
        color = Color.RED
        
    return f"{color}{bar}{Color.RESET}"

def scan_project(path):
    # Grab all Python files in the directory tree
    py_files = list(path.rglob("*.py"))
    valid_files = []
    for file in py_files:
        # Skip virtual environments and cache folders so we don't scan dependencies
        if any(ignored in file.parts for ignored in ("__pycache__", ".venv", ".git")): 
            continue
        valid_files.append(file)
    return valid_files

def count_lines(path):
    return len(path.read_text(encoding="utf-8").splitlines())

def analyze_file(path: Path) -> FileAnalysis:
    code = path.read_text(encoding="utf-8")

    # Use the ast module to safely parse the Python file's syntax tree
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Bail out early if the file has broken syntax
        return {
                "lines": count_lines(path),
                "functions": [],
                "classes": [],
                "imports": [],
                }

    functions = []
    classes = []
    imports = []

    # Walk through the syntax tree to pull out classes and functions
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        
    return {
            "lines": count_lines(path),
            "functions": functions,
            "classes": classes,
            "imports": imports,
        }

def detect_todos(path):
    lines = path.read_text(encoding="utf-8").splitlines()

    matches = []
    for line_number, line in enumerate(lines):
        # Split the line at the first '#' to separate code from comments
        parts = line.split("#", 1)
        # If there's a comment and it contains "TODO", log it
        if len(parts) == 2 and parts[1].strip().startswith("TODO"):
            matches.append((line_number + 1, line.strip()))
    return matches

def detect_long_functions(path):
    code = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    long_functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.end_lineno is None:
                continue

            # Calculate function length by subtracting line numbers
            function_len = node.end_lineno - node.lineno + 1

            # Flag functions that are over 20 lines long
            if function_len > 20:
                long_functions.append((node.name, function_len))
    return long_functions

def detect_security_issues(path):
    code = path.read_text(encoding="utf-8")

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    report = []
    for node in ast.walk(tree):
        # Look for eval() calls, which are a major security risk
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "eval"
        ):
            report.append((node.lineno, "eval() usage"))

    # Heuristic to detect hardcoded secrets: look for suspicious words, an equals sign, and quotes
    suspicious_words = ("password", "passwd", "secret", "api_key", "apikey", "token", "access_key", "private_key", "credential")
    lines = code.splitlines()

    for line_number, line in enumerate(lines):
        # Skip the line where we define the words so we don't flag ourselves!
        if "suspicious_words =" in line:
            continue
        has_word = any(word in line.lower() for word in suspicious_words)
        has_equals = "=" in line
        has_quotes = '"' in line or "'" in line

        # If it looks like a variable assignment with a string value, flag it
        if has_word and has_equals and has_quotes:
            report.append((line_number + 1, f"possible hardcoded secret: {line.strip()}"))

    return report

def check_project_structure(path):
    missing = []

    # Define what a standard, healthy project structure looks like
    expected = [
        ("README.md", "file"),
        ("requirements.txt", "file"),
        ("tests", "dir"),
    ]

    for name, item_type in expected:
        item_path = path / name

        if item_type == "file" and (not item_path.exists() or not item_path.is_file()):
            missing.append(name)

        if item_type == "dir" and (not item_path.exists() or not item_path.is_dir()):
            missing.append(name)

    return missing

def calculate_structure_deduction(path):
    deduction = 0
    missing = check_project_structure(path)
    
    # Penalize heavily for missing core project files
    if "README.md" in missing:
        deduction += 10
    if "requirements.txt" in missing:
        deduction += 10

    return deduction

def calculate_code_quality_deduction(py_files):
    total_todos = 0
    total_long_functions = 0

    # Aggregate all code quality issues across the project
    for file in py_files:
        total_todos += len(detect_todos(file))
        total_long_functions += len(detect_long_functions(file))

    # Deduct points, but cap the penalties so they don't spiral out of control
    deduction = 0
    deduction += min(total_todos * 2, 15)
    deduction += min(total_long_functions * 3, 15)

    return deduction

def calculate_security_deduction(py_files):
    total_eval = 0
    total_secrets = 0

    for file in py_files:
        issues = detect_security_issues(file)
        for _, issue in issues:
            if issue == "eval() usage":
                total_eval += 1
            elif issue.startswith("possible hardcoded secret"):
                total_secrets += 1

    # eval() is penalized more heavily than potential secrets
    deduction = 0
    deduction += total_eval * 10
    deduction += total_secrets * 5

    # Cap the maximum security deduction
    return min(deduction, 25)

def calculate_testing_deduction(path):
    deduction = 0
    tests_dir = path / "tests"
    
    # Big penalty if the tests folder doesn't even exist
    if not tests_dir.is_dir():
        deduction += 25
    else:
        # Look for common test file naming conventions inside the tests dir
        test_files = list(tests_dir.glob("test_*.py")) + list(tests_dir.glob("*_test.py"))
        
        # Smaller penalty if the folder exists but is empty
        if not test_files:
            deduction += 12
            
    return deduction

def calculate_health_score(path, py_files):
    # Start with a perfect score and subtract penalties for each issue category
    score = 100
    score -= calculate_structure_deduction(path)
    score -= calculate_code_quality_deduction(py_files)
    score -= calculate_security_deduction(py_files)
    score -= calculate_testing_deduction(path)

    # Never let the score drop below zero
    return max(score, 0)

def main():
    # Set up the CLI argument parser
    parser = argparse.ArgumentParser(
        prog="devlens",
        description="A developer toolkit to scan Python projects and manage a local code snippet vault."
    )

    subparsers = parser.add_subparsers(dest="command")

    scan_parser = subparsers.add_parser("scan", help="Scan a python project.")
    scan_parser.add_argument("path", type=Path, help="Path to the project to scan.")

    save_parser = subparsers.add_parser("save", help="Save a file to the vault.")
    save_parser.add_argument("file", type=Path, help="Path to the file to save.")

    search_parser = subparsers.add_parser("search", help="Search the vault.")
    search_parser.add_argument("query", type=str, help="Search query.")

    get_parser = subparsers.add_parser("get", help="Print a snippet from the vault.")
    get_parser.add_argument("name", type=str, help="Name of the snippet to retrieve.")

    create_parser = subparsers.add_parser("create", help="Create a project in current directory")
    create_parser.add_argument("name", type=str, help="Name of the new project.")

    explain_parser = subparsers.add_parser("explain", help="Explain a project")
    explain_parser.add_argument("file", type=Path, help="Name of project to explain")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()

    elif args.command == "scan":
        if args.path.exists():
            if args.path.is_dir():
                py_files = scan_project(args.path)
                if py_files:
                    # --- TOP HEADER ---
                    print(f"\n{Color.CYAN}{'─' * 50}{Color.RESET}")
                    print(f"{Color.BOLD}DevLens Scan:{Color.RESET} {args.path}")
                    print(f"{Color.CYAN}{'─' * 50}{Color.RESET}")
                    print(f"{len(py_files)} Python files found.\n")

                    for file in py_files:
                        rel_path = file.relative_to(args.path) 
                        analysis = analyze_file(file)

                        # File name and subtle dotted separator
                        print(f"{Color.CYAN}{rel_path}{Color.RESET} {Color.GRAY}({analysis['lines']} lines){Color.RESET}")
                        print(f"{Color.GRAY}{'·' * 50}{Color.RESET}")

                        # Group the classes and functions together for the tree output
                        details = []
                        if analysis["classes"]:
                            details.append(("Classes",analysis["classes"]))
                        if analysis["functions"]:
                            details.append(("Functions", analysis["functions"]))

                        for i, (label, names) in enumerate(details):
                            total_length = sum(len(name) for name in names)
                            first_six = names[:6]
                            remaining = len(names) - 6
                            connector = "└─" if i == len(details) - 1 else "├─"

                            if total_length < 50:
                                print(f"  {connector} {Color.GRAY}{label}{Color.RESET} ({len(names)}): {(', ').join(names)}")
                            else:
                                print(f"  {connector} {Color.GRAY}{label}{Color.RESET} ({len(names)}):")
                                for name in first_six:
                                    print(f"      • {name}")
                                if remaining > 0:
                                    print(f"      {Color.GRAY}• ...and {remaining} more{Color.RESET}")

                        # Blank line between structure and warnings
                        if details and (detect_todos(file) or detect_long_functions(file) or detect_security_issues(file)):
                            print()

                        # Report any TODOs found
                        todo_matches = detect_todos(file)
                        if todo_matches:
                            print(f"  {Color.YELLOW}⚠ TODOs{Color.RESET} ({len(todo_matches)}):")
                            first_ten = todo_matches[:10]
                            remaining = len(todo_matches) - 10
                            for (number, text) in first_ten:
                                print(f"    {Color.GRAY}• line {number}:{Color.RESET} {text}")
                            if remaining > 0:
                                print(f"    {Color.GRAY}• ...and {remaining} more{Color.RESET}")

                        # Report long functions
                        long_functions = detect_long_functions(file)
                        if long_functions:
                            print(f"  {Color.YELLOW}⚠ Long functions{Color.RESET} ({len(long_functions)}):")
                            for (name, length) in long_functions:
                                print(f"    {Color.GRAY}• {Color.RED}{name}{Color.RESET} ({length} lines)")

                        # Report security issues
                        security_issues = detect_security_issues(file)
                        if security_issues:
                            print(f"  {Color.RED}⚠ Security issues{Color.RESET} ({len(security_issues)}):")
                            for (line_number, issue) in security_issues:
                                print(f"    {Color.GRAY}• line {line_number}:{Color.RESET} {Color.RED}{issue}{Color.RESET}")
                        
                        print() # Blank line after each file

                    # --- BOTTOM STRUCTURE SUMMARY ---
                    missing = check_project_structure(args.path)
                    
                    print(f"{Color.CYAN}{'─' * 50}{Color.RESET}")
                    print(f"{Color.BOLD}Project Structure{Color.RESET}")
                    print(f"{Color.CYAN}{'─' * 50}{Color.RESET}")
                    
                    if missing:
                        for item in missing:
                            print(f"  {Color.RED}✗ {item} is missing{Color.RESET}")
                    else:
                        print(f"  {Color.GREEN}✓ Project structure looks good{Color.RESET}")

                    # --- FINAL HEALTH SCORE ---
                    health_score = calculate_health_score(args.path, py_files)
                    
                    print(f"\n{'═' * 50}")
                    print(f"Health Score: {get_score_bar(health_score)} {Color.BOLD}{health_score}/100{Color.RESET}")
                    print(f"{'═' * 50}\n")
                else:
                    print(f"{Color.YELLOW}No Python (.py) files found in '{args.path}'.{Color.RESET}")
            else:
                print(f"{Color.RED}Error: '{args.path}' is not a project directory{Color.RESET}")
        else:
            print(f"{Color.RED}Error: '{args.path}' does not exist.{Color.RESET}")

    elif args.command == "save":
        success = save_snippet(args.file)

        if success:
            print(f"{Color.GREEN}✓ Saved '{args.file.name}' to the vault.{Color.RESET}")
        else:
            print(f"{Color.RED}Error: '{args.file.name}' is not a valid file.{Color.RESET}")
    
    elif args.command == "search":
        matches = search_snippets(args.query)
        if matches:
            print(f"{Color.GREEN}Found {len(matches)} snippets:{Color.RESET}")
            for name in matches:
                print(f"  • {name}")
        else:
            print(f"{Color.YELLOW}No snippets found matching '{args.query}'.{Color.RESET}")

    elif args.command == "get":
        path = get_snippet(args.name)
        if path:
            print(path.read_text(encoding="utf-8"))
        else:
            print(f"{Color.RED}Error: Snippet '{args.name}' not found in vault.{Color.RESET}")

    elif args.command == "create":
        success = create_project(args.name)

        if success:
            print(f"{Color.GREEN}✓ Project '{args.name}' created successfully!{Color.RESET}")
        else:
            print(f"{Color.RED}Error: Directory '{args.name}' already exists.{Color.RESET}")

    elif args.command == "explain":
        if not args.file.exists() or not args.file.is_file():
            print(f"{Color.RED}Error: '{args.file}' is not a valid file.{Color.RESET}")
        else:
            analysis = analyze_file(args.file)

            # --- HEADER ---
            print(f"\n{Color.CYAN}{'─' * 50}{Color.RESET}")
            print(f"\n{Color.BOLD}DevLens Explain:{Color.RESET} '{args.file.name}'")
            print(f"\n{Color.CYAN}{'─' * 50}{Color.RESET}")

            # --- Overview ---
            print(f"{Color.BOLD}Overview:{Color.RESET}")
            print(f"  • Lines: {Color.GREEN}{analysis['lines']}{Color.RESET}")
            print(f"  • Imports: {Color.GREEN}{len(analysis['imports'])}{Color.RESET}")
            print(f"  • Classes: {Color.GREEN}{len(analysis['classes'])}{Color.RESET}")
            print(f"  • Functions: {Color.GREEN}{len(analysis['functions'])}{Color.RESET}")
            print()

            # --- DEPENDENCIES ---
            if analysis['imports']:
                print(f"{Color.BOLD}Dependencies{Color.RESET}")
                for imp in analysis['imports']:
                    print(f"  • {Color.GRAY}{imp}{Color.RESET}")
                print()
                
            # --- DEFINITIONS ---
            if analysis['classes'] or analysis['functions']:
                print(f"{Color.BOLD}Definitions{Color.RESET}")
                for cls in analysis['classes']:
                    print(f"  • Class: {Color.CYAN}{cls}{Color.RESET}")
                for func in analysis['functions']:
                    print(f"  • Function: {Color.CYAN}{func}{Color.RESET}")
                print()
                
            # --- OBSERVATIONS ---
            print(f"{Color.BOLD}Observations{Color.RESET}")
            has_issues = False
            
            long_funcs = detect_long_functions(args.file)
            if long_funcs:
                has_issues = True
                print(f"  {Color.YELLOW}⚠ Contains {len(long_funcs)} long function(s).{Color.RESET}")
                
            todos = detect_todos(args.file)
            if todos:
                has_issues = True
                print(f"  {Color.YELLOW}⚠ Contains {len(todos)} TODOs.{Color.RESET}")
                
            security = detect_security_issues(args.file)
            if security:
                has_issues = True
                print(f"  {Color.RED}⚠ Contains {len(security)} security issue(s).{Color.RESET}")
                
            if not has_issues:
                print(f"  {Color.GREEN}✓ No major issues detected in this file.{Color.RESET}")
            print()




if __name__ == "__main__":
    main()