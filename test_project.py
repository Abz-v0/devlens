from pathlib import Path

from project import analyze_file, count_lines, scan_project


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

    tmp_file.write_text("one\ntwo\nthree")
    line_count = count_lines(tmp_file)

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
    analysis = analyze_file(tmp_file)

    assert analysis["lines"] == 5
    assert analysis["functions"] == ["greet"]
    assert analysis["classes"] == ["User"]