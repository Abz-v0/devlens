import json
from pathlib import Path

import pytest

from devlens.project import (
    analyze_file,
    calculate_health_score,
    calculate_testing_deduction,
    check_project_structure,
    count_lines,
    create_project,
    detect_long_functions,
    detect_security_issues,
    detect_todos,
    get_index_path,
    get_snippet,
    get_vault_dir,
    load_index,
    main,
    parse_file,
    save_index,
    save_snippet,
    scan_project,
    search_snippets,
)


@pytest.fixture
def mock_home(monkeypatch, tmp_path):
    """Safely redirects Path.home() to a temporary test directory."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


def test_get_vault_dir_creates_folder_under_fake_home(mock_home):
    vault_dir = get_vault_dir()

    assert vault_dir.exists()
    assert vault_dir.relative_to(mock_home) == Path(".devlens/vault")


def test_save_and_load_index_round_trip(mock_home):
    test_data = {"snippet.py": {"original_path": "/fake/path", "saved_at": "now"}}

    save_index(test_data)
    loaded_data = load_index()

    assert loaded_data == test_data

def test_load_index_reports_corrupt_json_without_replacing_it(mock_home):
    index_path = get_index_path()
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        load_index()

    assert index_path.read_text(encoding="utf-8") == "{invalid json"

def test_save_snippet_copies_file_and_updates_index(mock_home, tmp_path):
    tmp_file = tmp_path / "my_script.py"
    tmp_file.write_text("print('hello')", encoding="utf-8")

    success = save_snippet(tmp_file)

    assert success is True

    expected_vault_file = mock_home / ".devlens" / "vault" / "my_script.py"
    assert expected_vault_file.exists()
    assert expected_vault_file.read_text() == "print('hello')"

    index = load_index()
    assert "my_script.py" in index
    assert index["my_script.py"]["original_path"] == str(tmp_file)

def test_save_snippet_returns_false_for_invalid_file(mock_home, tmp_path):
    fake_file = tmp_path / "ghost.py"

    result = save_snippet(fake_file)

    assert result is False

def test_save_snippet_does_not_overwrite_different_file_with_same_name(mock_home, tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    first_file = first_dir / "same.py"
    second_file = second_dir / "same.py"
    first_file.write_text("first", encoding="utf-8")
    second_file.write_text("second", encoding="utf-8")

    assert save_snippet(first_file) is True
    assert save_snippet(second_file) is False
    assert (get_vault_dir() / "same.py").read_text(encoding="utf-8") == "first"

def test_search_snippets_finds_matching_names(mock_home):
    test_dict = {
        "auth.py": {}, 
        "data.py": {}, 
        "bro.py": {}
    }

    save_index(test_dict)
    results = search_snippets("auth")

    assert results == ["auth.py"]

def test_get_snippet_returns_path_if_exists(mock_home, tmp_path):
    dummy_file = tmp_path / "validator.py"
    dummy_file.write_text("x = 1")
    save_snippet(dummy_file)

    path = get_snippet("validator.py")

    assert isinstance(path, Path)
    assert path.exists()


def test_get_snippet_returns_none_if_missing(mock_home):
    path = get_snippet("ghost_file.py")

    assert path is None

def test_get_snippet_rejects_path_outside_vault(mock_home):
    outside_file = mock_home / ".devlens" / "outside.py"
    outside_file.parent.mkdir(parents=True, exist_ok=True)
    outside_file.write_text("secret", encoding="utf-8")

    assert get_snippet("..\\outside.py") is None

def test_create_project_creates_project_if_folder_does_not_exist(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    result = create_project("myapp")
    assert result == True

    project_dir = tmp_path / "myapp"
    assert project_dir.exists()

    assert (project_dir / "tests").is_dir()
    assert (project_dir / "main.py").exists()

    expected_text_in_readme = (project_dir / "README.md").read_text()
    assert expected_text_in_readme == "# myapp"

    assert (project_dir / "requirements.txt").exists()
    assert (project_dir / "tests" / "test_main.py").exists()

def test_create_project_returns_false_if_folder_exists(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    tmp_dir = (tmp_path / "myapp")
    tmp_dir.mkdir()

    result = create_project(tmp_dir)

    assert result is False

def test_scan_project_returns_python_files(tmp_path: Path):
    (tmp_path / "main.py").touch()
    (tmp_path / "bro.py").touch()
    (tmp_path / "README.md").touch()

    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").touch()

    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "environment.py").touch()

    git = tmp_path / ".git"
    git.mkdir()
    (git / "internal.py").touch()

    pycache = tmp_path / "__pycache__"
    pycache.mkdir()
    (pycache / "cached.py").touch()

    found_files = scan_project(tmp_path)
    file_names = {file.name for file in found_files}

    assert file_names == {"main.py", "bro.py", "app.py"}

def test_scan_project_returns_empty_list_when_no_python_files(tmp_path: Path):
    found_files = scan_project(tmp_path)
    assert found_files == []

def test_count_lines_returns_number_of_lines_in_python_files(tmp_path):
    tmp_file = (tmp_path / "abz.py")

    tmp_file.write_text("one\ntwo\nthree", encoding="utf-8")
    line_count = count_lines(tmp_file.read_text(encoding="utf-8"))

    assert line_count == 3

def test_analyze_file_returns_line_function_and_class_details(tmp_path):
    tmp_file = (tmp_path / "func.py")

    tmp_file.write_text(
        "def greet():\n"
        "    pass\n"
        "\n"
        "class User:\n"
        "    pass\n"
    )
    code, tree = parse_file(tmp_file)
    analysis = analyze_file(code, tree)

    assert analysis["lines"] == 5
    assert analysis["functions"] == ["greet"]
    assert analysis["classes"] == ["User"]

def test_analyze_file_extracts_imports(tmp_path):
    tmp_file = tmp_path / "imports.py"
    tmp_file.write_text(
        "import json\n"
        "from pathlib import Path\n"
        "\n"
        "def my_func():\n"
        "    pass\n"
    )
    code, tree = parse_file(tmp_file)
    analysis = analyze_file(code, tree)

    assert "json" in analysis["imports"]
    assert "pathlib" in analysis["imports"]

def test_detect_todos_returns_real_todo_comment(tmp_path):
    todo_file = tmp_path / "todo.py"
    todo_file.write_text("# TODO validate entry")
    assert detect_todos(todo_file.read_text(encoding="utf-8")) == [(1, "# TODO validate entry")]

def test_detect_todos_ignores_todo_without_hash(tmp_path):
    print_file = tmp_path / "print.py"
    print_file.write_text("print('TODO hello world')")
    assert detect_todos(print_file.read_text(encoding="utf-8")) == []

def test_detect_todos_returns_empty_list_when_no_todos(tmp_path):
    no_todo_file = tmp_path / "no_todo.py"
    no_todo_file.write_text("if len(name) == 2:\n    pass")
    assert detect_todos(no_todo_file.read_text(encoding="utf-8")) == []

def test_detect_long_functions_flags_long_function(tmp_path):
    tmp_file = tmp_path / "long.py"

    body = "\n".join(
        f"    number_{i} = {i}"
        for i in range(1, 22)
    )

    tmp_file.write_text(
        "def long_function():\n"
        + body
    )

    _, tree = parse_file(tmp_file)
    assert detect_long_functions(tree) == [("long_function", 22)]

def test_detect_long_functions_returns_empty_list_if_short_function(tmp_path):
    tmp_file = (tmp_path / "son.py")
    
    tmp_file.write_text(
        "def greet():\n"
        "    greeting = 'hello world'\n"
        "    return greeting"
    )
    _, tree = parse_file(tmp_file)
    assert detect_long_functions(tree) == []

def test_detect_security_issues_flags_eval(tmp_path):
    tmp_file = tmp_path / "risky.py"
    tmp_file.write_text("x = eval('2 + 2')")
    code, tree = parse_file(tmp_file)
    result = detect_security_issues(code, tree)
    assert result == [(1, "eval() usage")]

def test_detect_security_issues_flags_hardcoded_secret(tmp_path):
    tmp_file = tmp_path / "config.py"
    tmp_file.write_text('password = "supersecret123"')
    code, tree = parse_file(tmp_file)
    result = detect_security_issues(code, tree)
    assert result == [(1, 'possible hardcoded secret: password = supersecret123')]

def test_detect_security_issues_returns_empty_list_for_clean_file(tmp_path):
    tmp_file = tmp_path / "clean.py"
    tmp_file.write_text("x = 5\nprint('hello')")
    code, tree = parse_file(tmp_file)
    assert detect_security_issues(code, tree) == []

def test_invalid_python_file_keeps_source_checks_and_skips_ast_checks(tmp_path):
    invalid_file = tmp_path / "invalid.py"
    invalid_file.write_text(
        "# TODO fix syntax\n"
        "password = 'example'\n"
        "def broken(:\n",
        encoding="utf-8",
    )

    code, tree = parse_file(invalid_file)

    assert tree == []
    assert detect_todos(code) == [(1, "# TODO fix syntax")]
    assert detect_long_functions(tree) == []
    assert detect_security_issues(code, tree) == [
        (2, "possible hardcoded secret: password = 'example'")
    ]

def test_explain_command_analyzes_file(monkeypatch, tmp_path, capsys):
    source_file = tmp_path / "example.py"
    source_file.write_text(
        "import json\n"
        "def greet():\n"
        "    return 'hello'\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.argv", ["devlens", "explain", str(source_file)])

    main()

    output = capsys.readouterr().out
    assert "Imports: " in output
    assert "json" in output
    assert "greet" in output

def test_scan_command_skips_ast_checks_for_invalid_file(monkeypatch, tmp_path, capsys):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    invalid_file = project_dir / "invalid.py"
    invalid_file.write_text(
        "# TODO fix syntax\n"
        "def broken(:\n",
        encoding="utf-8",
    )
    parse_calls = []
    original_parse_file = parse_file

    def track_parse_file(path):
        parse_calls.append(path)
        return original_parse_file(path)

    monkeypatch.setattr("devlens.project.parse_file", track_parse_file)
    monkeypatch.setattr("sys.argv", ["devlens", "scan", str(project_dir)])

    main()

    output = capsys.readouterr().out
    assert parse_calls == [invalid_file]
    assert "invalid.py" in output
    assert "TODOs" in output
    assert "# TODO fix syntax" in output

def test_check_project_structure_returns_empty_list_if_good(tmp_path):
    (tmp_path / "README.md").touch()
    (tmp_path / "requirements.txt").touch()

    tests = tmp_path / "tests"
    tests.mkdir()

    result = check_project_structure(tmp_path)

    assert result == []

def test_missing_readme(tmp_path):
    (tmp_path / "requirements.txt").touch()

    tests = tmp_path / "tests"
    tests.mkdir()

    result = check_project_structure(tmp_path)
    
    assert result == ["README.md"]

def test_missing_requirements(tmp_path):
    (tmp_path / "README.md").touch()

    tests = tmp_path / "tests"
    tests.mkdir()

    result = check_project_structure(tmp_path)
    
    assert result == ["requirements.txt or pyproject.toml"]

def test_missing_tests(tmp_path):
    (tmp_path / "README.md").touch()
    (tmp_path / "requirements.txt").touch()

    result = check_project_structure(tmp_path)
        
    assert result == ["tests"]

def test_everything_is_missing(tmp_path):
    assert check_project_structure(tmp_path) == ["README.md", "tests", "requirements.txt or pyproject.toml"]

def test_tests_exists_but_is_a_file(tmp_path):
    (tmp_path / "README.md").touch()
    (tmp_path / "requirements.txt").touch()
    (tmp_path / "tests").touch()

    result = check_project_structure(tmp_path)
            
    assert result == ["tests"]

def test_calculate_testing_deduction_returns_25_if_no_test_folder(tmp_path):

    assert calculate_testing_deduction(tmp_path) == 25

def test_calculate_testing_deduction_returns_12_if_no_test_file(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "__init__.py").touch()

    assert calculate_testing_deduction(tmp_path) == 12

def test_calculate_testing_deduction_returns_0_if_test_file(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_.py").touch()

    assert calculate_testing_deduction(tmp_path) == 0

def test_file_in_good_health(tmp_path):
    (tmp_path / "README.md").touch()
    (tmp_path / "requirements.txt").touch()

    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_.py").touch()

    tmp_file = tmp_path / "health.py"
    
    body = "\n".join(
        f"    number_{i} = {i}"
        for i in range(1, 22)
    )

    tmp_file.write_text(
        "def health_number():\n"
        + body
    )

    assert calculate_health_score(tmp_path, [parse_file(tmp_file)]) == 97

def test_file_in_bad_health(tmp_path):
    (tmp_path / "requirements.txt").touch()

    todo_file = tmp_path / "todo.py"
    todo_file.write_text(
        "def validate():\n"
        "pass\n"
        "# TODO change pass to actual logic"
        "# TODO add input counter"
    )

    assert calculate_health_score(tmp_path, [parse_file(todo_file)]) == 63