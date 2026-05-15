import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_modular_monolith_boundaries() -> None:
    result = subprocess.run(
        ["lint-imports"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"import-linter detected boundary violations:\n--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
