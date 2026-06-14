"""Project virtual environment bootstrap helpers."""

import os
import subprocess
import sys
from pathlib import Path


def ensure_venv(project_dir: Path) -> None:
    """Run the current script under the project's virtual environment."""
    if sys.prefix != sys.base_prefix:
        return

    venv_dir = project_dir / ".venv"
    venv_python = venv_dir / "bin" / "python"
    if venv_python.exists():
        os.execvp(str(venv_python), [str(venv_python)] + sys.argv)

    _setup_venv(project_dir, venv_dir, project_dir / "requirements.txt")


def _setup_venv(project_dir: Path, venv_dir: Path, requirements: Path) -> None:
    """Create .venv, install dependencies, and re-exec under venv Python."""
    print("Creating virtual environment...")
    if subprocess.run([sys.executable, "-m", "venv", str(venv_dir)]).returncode != 0:
        print("Error: Failed to create virtual environment.")
        raise SystemExit(1)

    venv_pip = venv_dir / "bin" / "pip"
    if requirements.exists():
        print("Installing dependencies...")
        if subprocess.run([str(venv_pip), "install", "-r", str(requirements)]).returncode != 0:
            print("Error: Failed to install dependencies.")
            raise SystemExit(1)

    venv_python = venv_dir / "bin" / "python"
    os.execvp(str(venv_python), [str(venv_python)] + sys.argv)
