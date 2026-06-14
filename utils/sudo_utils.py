import os
import shutil
import subprocess
from pathlib import Path

SUDO_PASSWORD_ENV = "LST_SUDO_PASSWORD"


def need_sudo(path: str | Path) -> bool:
    path = Path(path)
    return not (path.exists() and os.access(path, os.W_OK))


def run(cmd: list[str], stdin_data: str | None = None) -> None:
    sudo_password = os.environ.get(SUDO_PASSWORD_ENV)
    if sudo_password:
        input_data = f"{sudo_password}\n"
        if stdin_data is not None:
            input_data += stdin_data
        proc = subprocess.run(
            ["sudo", "-S", "-p", ""] + cmd,
            input=input_data,
            capture_output=False,
            stdout=subprocess.DEVNULL if stdin_data is not None else None,
            text=True,
        )
        proc.check_returncode()
        return

    if stdin_data is not None:
        proc = subprocess.run(
            ["sudo"] + cmd,
            input=stdin_data,
            capture_output=False,
            stdout=subprocess.DEVNULL,
            text=True,
        )
        proc.check_returncode()
    else:
        subprocess.check_call(["sudo"] + cmd)


def write_file(path: str | Path, content: str) -> None:
    path = Path(path)
    if need_sudo(path):
        run(["tee", str(path)], stdin_data=content)
    else:
        path.write_text(content)


def copy_file(src: str | Path, dst: str | Path) -> None:
    src = Path(src)
    dst = Path(dst)
    if need_sudo(dst):
        run(["cp", str(src), str(dst)])
    else:
        shutil.copy2(src, dst)
