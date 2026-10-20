import json
import shutil
from datetime import UTC, datetime
from pathlib import Path


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
        return json.loads(index_path.read_text(encoding="utf-8"))
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

    index = load_index()
    dest_path = get_vault_dir() / file_path.name
    existing_entry = index.get(file_path.name)
    if dest_path.exists() and (
        existing_entry is None
        or Path(existing_entry["original_path"]).resolve() != file_path.resolve()
    ):
        return False

    shutil.copy2(file_path, dest_path)

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
    vault_dir = get_vault_dir().resolve()
    path = (vault_dir / name).resolve()

    if path.is_relative_to(vault_dir) and path.is_file():
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