import argparse
import ast
from pathlib import Path


def scan_project(path):
    py_files = list(path.rglob("*.py"))
    valid_files = []
    for file in py_files:
        if any(ignored in file.parts for ignored in ("__pycache__", ".venv", ".git")): 
            continue
        valid_files.append(file)
    return valid_files

def count_lines(path):
    return len(path.read_text().splitlines())

def analyze_file(path):
    code = path.read_text()
    tree = ast.parse(code)

    functions = []
    classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
    return {
            "lines": count_lines(path),
            "functions": functions,
            "classes": classes,
        }

def detect_todos(path):
    lines = path.read_text().splitlines()

    matches = []
    for line_number, line in enumerate(lines):
        parts = line.split("#", 1)
        if len(parts) == 2 and "TODO" in parts[1]:
            matches.append((line_number + 1, line.strip()))
    return matches

def detect_long_functions(path):
    code = path.read_text()
    tree = ast.parse(code)

    long_functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.end_lineno is None:
                continue

            function_len = node.end_lineno - node.lineno + 1

            if function_len > 20:
                long_functions.append((node.name, function_len))
    return long_functions

def main():
    parser = argparse.ArgumentParser(
        prog= "devlens",
        description="Analyze a Python project for common issues."
    )

    subparsers = parser.add_subparsers(dest="command")

    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a python project."
    )
    scan_parser.add_argument(
        "path",
        type=Path,
        help="Path to the project to scan."
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()

    elif args.command == "scan":
        if args.path.exists():
            if args.path.is_dir():
                py_files = scan_project(args.path)
                if py_files:
                    print(f"Scanning: {args.path}\n")
                    print(f"{len(py_files)} Python files found:")
                    for file in py_files:
                        rel_path = file.relative_to(args.path) 
                        analysis = analyze_file(file)

                        print(f"\n{rel_path} — {analysis['lines']} lines")

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
                                print(f"  {connector} {label} ({len(names)}): {(', ').join(names)}")
                            else:
                                print(f"  {connector} {label} ({len(names)}):")
                                for name in first_six:
                                    print(f"      • {name}")
                                if remaining > 0:
                                    print(f"      ...and {remaining} more")

                        todo_matches = detect_todos(file)
                        if todo_matches:
                            print(f"  ⚠ TODOs ({len(todo_matches)}):")
                            first_ten = todo_matches[:10]
                            remaining = len(todo_matches) - 10
                            for (number, text) in first_ten:
                                print(f"    line {number}: {text}")
                            if remaining > 0:
                                print(f"    ...and {remaining} more")

                        long_functions = detect_long_functions(file)
                        if long_functions:
                            print(f"  ⚠ Long functions ({len(long_functions)}):")

                            for (name, length) in long_functions:
                                print(f"    {name} ({length} lines)")
                else:
                    print(f"No Python (.py) files found in '{args.path}'.")
            else:
                print(f"'{args.path}'is not a project directory")
        else:
            print(f"Error '{args.path}' does not exist.")

if __name__ == "__main__":
    main()