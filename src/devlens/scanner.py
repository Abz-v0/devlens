import ast
import io
import os
import tokenize
from pathlib import Path

from devlens.colors import Color
from devlens.types import FileAnalysis


def parse_file(path: Path) -> tuple[str, list[ast.AST]]:
    code = path.read_text(encoding="utf-8")

    try:
        tree = ast.parse(code)
        return code, list(ast.walk(tree))
    except SyntaxError:
        return code, []

def scan_project(path):
    valid_files = []
    for root, dirs, files in os.walk(path):
        root_path = Path(root)
        # Skip virtual environments and cache folders so we don't scan dependencies
        if (root_path / "pyvenv.cfg").is_file():
            dirs.clear()
            continue
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", ".venv", "venv", "env")]
        for file in files:
            if file.endswith(".py"):
                valid_files.append(root_path / file)
    return valid_files

def count_lines(code: str):
    return len(code.splitlines())

def analyze_file(code: str, nodes: list[ast.AST]) -> FileAnalysis:
    functions = []
    classes = []
    imports = []

    # Walk through the syntax tree to pull out classes and functions
    for node in nodes:
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
            "lines": count_lines(code),
            "functions": functions,
            "classes": classes,
            "imports": imports,
        }

def detect_todos(code: str):
    tokens = tokenize.generate_tokens(io.StringIO(code).readline)
    matches = []
    try:
        for token in tokens:
            # If there's a comment and it contains "TODO", log it
            if token.type == tokenize.COMMENT and token.string.strip().startswith("# TODO"):
                    matches.append((token.start[0], token.line.strip()))
    except tokenize.TokenError:
        pass
    return matches

def detect_long_functions(nodes: list[ast.AST]):
    long_functions = []

    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.end_lineno is None:
                continue

            # Calculate function length by subtracting line numbers
            function_len = node.end_lineno - node.lineno + 1

            # Flag functions that are over 20 lines long
            if function_len > 20:
                long_functions.append((node.name, function_len))
    return long_functions

def detect_security_issues(code: str, nodes: list[ast.AST]):
    suspicious_words = ("password", "passwd", "secret", "api_key", "apikey", "token", "access_key", "private_key", "credential")
    report = []
    for node in nodes:
        # Look for eval() calls, which are a major security risk
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "eval"
        ):
            report.append((node.lineno, "eval() usage"))
        if (
            isinstance(node, ast.Assign) 
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id.lower() in suspicious_words
            and isinstance(node.value, ast.Constant) 
            and isinstance(node.value.value, str)
        ):
            report.append((node.lineno, f"possible hardcoded secret: {node.targets[0].id} = {node.value.value}"))
        
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "os"
            and node.func.attr == "system"
        ):
            report.append((node.lineno, "os.system() usage"))

        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "subprocess"
            and node.func.attr in ("run", "Popen", "call", "check_output")
            and any(
                kw.arg == "shell"
                and isinstance(kw.value,ast.Constant)
                and kw.value.value is True
                for kw in node.keywords
            )
        ):
            report.append((node.lineno, "subprocess.run(shell=True) usage"))

    if not nodes:
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
        ("tests", "dir"),
    ]

    for name, item_type in expected:
        item_path = path / name

        if item_type == "file" and (not item_path.exists() or not item_path.is_file()):
            missing.append(name)

        if item_type == "dir" and (not item_path.exists() or not item_path.is_dir()):
            missing.append(name)
    if (path / "requirements.txt").is_file() is False and (path / "pyproject.toml").is_file() is False:
        missing.append("requirements.txt or pyproject.toml")

    return missing

def calculate_structure_deduction(path):
    deduction = 0
    missing = check_project_structure(path)
    
    # Penalize heavily for missing core project files
    if "README.md" in missing:
        deduction += 10
    if "requirements.txt or pyproject.toml" in missing:
        deduction += 10

    return deduction

def calculate_code_quality_deduction(parsed_files: list[tuple[str, list[ast.AST]]]):
    total_todos = 0
    total_long_functions = 0

    # Aggregate all code quality issues across the project
    for code, tree in parsed_files:
        total_todos += len(detect_todos(code))
        total_long_functions += len(detect_long_functions(tree))

    # Deduct points, but cap the penalties so they don't spiral out of control
    deduction = 0
    deduction += min(total_todos * 2, 15)
    deduction += min(total_long_functions * 3, 15)

    return deduction

def calculate_security_deduction(parsed_files: list[tuple[str, list[ast.AST]]]):
    total_eval = 0
    total_secrets = 0

    for code, tree in parsed_files:
        issues = detect_security_issues(code, tree)
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

def calculate_health_score(path, parsed_files: list[tuple[str, list[ast.AST]]]):
    # Start with a perfect score and subtract penalties for each issue category
    score = 100
    score -= calculate_structure_deduction(path)
    score -= calculate_code_quality_deduction(parsed_files)
    score -= calculate_security_deduction(parsed_files)
    score -= calculate_testing_deduction(path)

    # Never let the score drop below zero
    return max(score, 0)

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