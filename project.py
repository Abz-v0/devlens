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

                        print(f" \n{rel_path} — {analysis['lines']} lines")

                        details = []
                        if analysis["classes"]:
                            details.append(f"Classes ({len(analysis['classes'])}): {', '.join(analysis['classes'])}")
                        if analysis["functions"]:
                            details.append(f"Functions ({len(analysis['functions'])}): {', '.join(analysis['functions'])}")

                        for i, line in enumerate(details):
                            connector = "└─" if i == len(details) - 1 else "├─"
                            print(f"  {connector} {line}")
                else:
                    print(f"No Python (.py) files found in '{args.path}'.")
            else:
                print(f"'{args.path}'is not a project directory")
        else:
            print(f"Error '{args.path}' does not exist.")

if __name__ == "__main__":
    main()