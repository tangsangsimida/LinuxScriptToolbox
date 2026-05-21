import os
import subprocess
import sys
from pathlib import Path


def need_sudo(path: Path) -> bool:
    return not (path.exists() and os.access(path, os.W_OK))


def run(cmd: list[str], stdin_data: str | None = None) -> None:
    if stdin_data is not None:
        proc = subprocess.run(
            ["sudo"] + cmd, input=stdin_data, capture_output=False, text=True
        )
        proc.check_returncode()
    else:
        subprocess.check_call(["sudo"] + cmd)


def write_file(path: Path, content: str) -> None:
    if need_sudo(path):
        run(["tee", str(path)], stdin_data=content)
    else:
        path.write_text(content)


def copy_file(src: Path, dst: Path) -> None:
    if need_sudo(dst):
        run(["cp", str(src), str(dst)])
    else:
        import shutil
        shutil.copy2(src, dst)
