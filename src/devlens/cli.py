import argparse
from pathlib import Path

from devlens.colors import Color
from devlens.scanner import (
    analyze_file,
    calculate_health_score,
    check_project_structure,
    detect_long_functions,
    detect_security_issues,
    detect_todos,
    get_score_bar,
    parse_file,
    scan_project,
)
from devlens.vault import create_project, get_snippet, save_snippet, search_snippets


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

                    parsed_files = [parse_file(file) for file in py_files]

                    for file, (code, tree) in zip(py_files, parsed_files):
                        rel_path = file.relative_to(args.path) 
                        analysis = analyze_file(code, tree)
                        todo_matches = detect_todos(code)
                        long_functions = detect_long_functions(tree)
                        security_issues = detect_security_issues(code, tree)

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
                        if details and (todo_matches or long_functions or security_issues):
                            print()

                        # Report any TODOs found
                        if todo_matches:
                            print(f"  {Color.YELLOW}⚠ TODOs{Color.RESET} ({len(todo_matches)}):")
                            first_ten = todo_matches[:10]
                            remaining = len(todo_matches) - 10
                            for (number, text) in first_ten:
                                print(f"    {Color.GRAY}• line {number}:{Color.RESET} {text}")
                            if remaining > 0:
                                print(f"    {Color.GRAY}• ...and {remaining} more{Color.RESET}")

                        # Report long functions
                        if long_functions:
                            print(f"  {Color.YELLOW}⚠ Long functions{Color.RESET} ({len(long_functions)}):")
                            for (name, length) in long_functions:
                                print(f"    {Color.GRAY}• {Color.RED}{name}{Color.RESET} ({length} lines)")

                        # Report security issues
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
                    health_score = calculate_health_score(args.path, parsed_files)
                    
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
            print(
                f"{Color.RED}Error: Could not save '{args.file.name}'. "
                "Check that the file is valid and the snippet name is not already in use."
                f"{Color.RESET}"
            )
    
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
            code, tree = parse_file(args.file)
            analysis = analyze_file(code, tree)

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
            
            long_funcs = detect_long_functions(tree)
            if long_funcs:
                has_issues = True
                print(f"  {Color.YELLOW}⚠ Contains {len(long_funcs)} long function(s).{Color.RESET}")
                
            todos = detect_todos(code)
            if todos:
                has_issues = True
                print(f"  {Color.YELLOW}⚠ Contains {len(todos)} TODOs.{Color.RESET}")
                
            security = detect_security_issues(code, tree)
            if security:
                has_issues = True
                print(f"  {Color.RED}⚠ Contains {len(security)} security issue(s).{Color.RESET}")
                
            if not has_issues:
                print(f"  {Color.GREEN}✓ No major issues detected in this file.{Color.RESET}")
            print()




if __name__ == "__main__":
    main()