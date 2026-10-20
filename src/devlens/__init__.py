from devlens.cli import main
from devlens.colors import Color
from devlens.scanner import (
    analyze_file,
    calculate_code_quality_deduction,
    calculate_health_score,
    calculate_security_deduction,
    calculate_structure_deduction,
    calculate_testing_deduction,
    check_project_structure,
    count_lines,
    detect_long_functions,
    detect_security_issues,
    detect_todos,
    get_score_bar,
    parse_file,
    scan_project,
)
from devlens.types import FileAnalysis
from devlens.vault import (
    create_project,
    get_index_path,
    get_snippet,
    get_vault_dir,
    load_index,
    save_index,
    save_snippet,
    search_snippets,
)