from src.core.app import main

def test_app_runs() -> None:
    assert main() == "it works"

def test_scaffold_exists() -> None:
    import importlib
    importlib.import_module("src")
