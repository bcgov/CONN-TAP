from pathlib import Path

# a dummy test
def test_readme_exists() -> None:
    assert Path("README.md").exists()

def test_base_placeholder() -> None:
    assert 1 == 1
