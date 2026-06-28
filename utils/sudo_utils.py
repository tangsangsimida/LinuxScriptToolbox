"""Privileged file I/O wrappers — platform-aware elevation.

特权文件 I/O 封装 — 平台感知的权限提升。

On Linux/macOS: uses sudo with optional password via LST_SUDO_PASSWORD env var.
On Windows: uses PowerShell Start-Process -Verb RunAs for admin elevation.

在 Linux/macOS 上：通过 LST_SUDO_PASSWORD 环境变量使用 sudo 可选密码认证。
在 Windows 上：使用 PowerShell Start-Process -Verb RunAs 进行管理员权限提升。
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from utils.platform import IS_WINDOWS
from utils.shell import get_windows_shell_cmd

# Environment variable name for sudo password injection (non-interactive remote tests).
# 用于 sudo 密码注入的环境变量名称（非交互式远程测试）。
SUDO_PASSWORD_ENV = "LST_SUDO_PASSWORD"


def _nearest_existing_parent(path: Path) -> Path:
    """Return the closest existing parent for permission checks.

    返回最近的已存在父目录，用于权限检查。

    Walks up the directory tree until an existing directory is found.
    This is needed when the target file doesn't exist yet but we need
    to check write permissions on its parent directory.

    沿目录树向上遍历直到找到存在的目录。
    当目标文件尚不存在但需要检查父目录写权限时使用。

    Args:
        path: Target path to check / 要检查的目标路径

    Returns:
        Nearest existing parent directory / 最近的已存在父目录
    """
    parent = path.parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    return parent


def need_sudo(path: str | Path) -> bool:
    """Check if elevated privileges are needed to write to path.

    检查写入路径是否需要提升权限。

    If the file exists, checks write permission directly.
    If not, checks the nearest existing parent directory.

    如果文件存在，直接检查写权限；
    如果不存在，检查最近的已存在父目录。

    Args:
        path: File or directory path to check / 要检查的文件或目录路径

    Returns:
        True if elevated privileges are needed / 需要提升权限时返回 True
    """
    path = Path(path)
    try:
        target = path if path.exists() else _nearest_existing_parent(path)
        return not os.access(target, os.W_OK)
    except OSError:
        return True


def _needs_sudo_to_read(path: Path) -> bool:
    """Check if elevated privileges are needed to read a file.

    检查读取文件是否需要提升权限。

    Args:
        path: File path to check / 要检查的文件路径

    Returns:
        True if elevated privileges are needed / 需要提升权限时返回 True
    """
    return not (path.exists() and os.access(path, os.R_OK))


def _read_file_with_sudo(path: Path) -> bytes:
    """Read a file using elevated privileges.

    使用提升权限读取文件。

    On Windows, tries direct read first, then falls back to PowerShell elevation.
    On Linux/macOS, uses sudo cat with optional password from SUDO_PASSWORD_ENV.

    在 Windows 上先尝试直接读取，失败后回退到 PowerShell 权限提升。
    在 Linux/macOS 上使用 sudo cat，可选通过 SUDO_PASSWORD_ENV 提供密码。

    Args:
        path: File path to read / 要读取的文件路径

    Returns:
        File content as bytes / 文件内容（字节）

    Raises:
        subprocess.CalledProcessError: If the command fails / 命令执行失败时
    """
    if IS_WINDOWS:
        # On Windows, try reading directly; if access denied, use PowerShell elevation
        # 在 Windows 上先尝试直接读取，权限不足时使用 PowerShell 提升
        win_shell = get_windows_shell_cmd()
        try:
            return path.read_bytes()
        except PermissionError:
            result = subprocess.run(
                [win_shell, "-Command", f"Get-Content -Path '{path}' -Raw"],
                capture_output=True,
            )
            result.check_returncode()
            return result.stdout

    sudo_password = os.environ.get(SUDO_PASSWORD_ENV)
    cmd = ["sudo", "cat", str(path)]
    kwargs = {"capture_output": True}
    if sudo_password:
        # -S: read password from stdin; -p "": no prompt
        # -S: 从 stdin 读取密码；-p "": 不显示提示符
        cmd = ["sudo", "-S", "-p", "", "cat", str(path)]
        kwargs["input"] = f"{sudo_password}\n".encode()

    proc = subprocess.run(cmd, **kwargs)
    proc.check_returncode()
    return proc.stdout


def _ps_quote_arg(arg: str) -> str:
    """Quote a single argument for PowerShell Start-Process -ArgumentList.

    为 PowerShell Start-Process -ArgumentList 引用单个参数。

    PowerShell uses double quotes for quoting; embedded double quotes and
    dollar signs must be escaped with backticks.

    PowerShell 使用双引号进行引用；嵌入的双引号和美元符号需要用反引号转义。

    Args:
        arg: Argument to quote / 要引用的参数

    Returns:
        Quoted argument string / 引用后的参数字符串
    """
    return '"' + arg.replace('"', '`"').replace("$", "`$") + '"'


def _run_elevated_win(cmd: list[str], stdin_data: str | None = None) -> None:
    """Run a command with admin privileges on Windows via PowerShell.

    在 Windows 上通过 PowerShell 以管理员权限运行命令。

    Note: stdin_data is not supported on Windows elevation because
    Start-Process -Verb RunAs launches a new process that cannot
    inherit stdin from the parent. A RuntimeError is raised if
    stdin_data is provided.

    注意：Windows 权限提升不支持 stdin_data，因为 Start-Process -Verb RunAs
    启动的新进程无法继承父进程的 stdin。如果提供了 stdin_data 将抛出 RuntimeError。

    Args:
        cmd: Command and arguments / 命令及参数
        stdin_data: Optional stdin input (unsupported on Windows) / 可选的 stdin 输入（Windows 不支持）

    Raises:
        RuntimeError: If stdin_data is provided on Windows / 在 Windows 上提供 stdin_data 时
        subprocess.CalledProcessError: If the command fails / 命令执行失败时
    """
    if stdin_data is not None:
        raise RuntimeError(
            "stdin_data is not supported for elevated Windows commands "
            "because Start-Process -Verb RunAs cannot inherit stdin"
        )
    win_shell = get_windows_shell_cmd()
    ps_args = ", ".join(_ps_quote_arg(a) for a in cmd[1:]) if len(cmd) > 1 else "''"
    ps_cmd = f"Start-Process -FilePath '{cmd[0]}' -ArgumentList {ps_args} -Verb RunAs -Wait"
    result = subprocess.run(
        [win_shell, "-Command", ps_cmd],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)


def run(cmd: list[str], stdin_data: str | None = None) -> None:
    """Run a command with elevated privileges if needed.

    以提升权限运行命令（如需要）。

    On Windows, delegates to _run_elevated_win.
    On Linux/macOS, uses sudo with optional password injection via SUDO_PASSWORD_ENV.

    在 Windows 上委托给 _run_elevated_win。
    在 Linux/macOS 上使用 sudo，可通过 SUDO_PASSWORD_ENV 注入密码。

    Args:
        cmd: Command and arguments / 命令及参数
        stdin_data: Optional stdin input / 可选的 stdin 输入

    Raises:
        subprocess.CalledProcessError: If the command fails / 命令执行失败时
    """
    if IS_WINDOWS:
        _run_elevated_win(cmd, stdin_data)
        return

    sudo_password = os.environ.get(SUDO_PASSWORD_ENV)
    if sudo_password:
        # Build input: password first, then any additional stdin data
        # 构造输入：先密码，再附加的 stdin 数据
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
    """Write content to a file, using elevated privileges if needed.

    将内容写入文件，需要时使用提升权限。

    Checks write permission first. If insufficient, uses sudo tee (Linux/macOS)
    or PowerShell Set-Content (Windows).

    先检查写权限。权限不足时使用 sudo tee（Linux/macOS）
    或 PowerShell Set-Content（Windows）。

    Args:
        path: Target file path / 目标文件路径
        content: Text content to write / 要写入的文本内容
    """
    path = Path(path)
    if need_sudo(path):
        if IS_WINDOWS:
            # Write to a temp file first, then use elevated PowerShell to copy to destination.
            # This avoids embedding content in the command string (unsafe for large/special content).
            # 先写入临时文件，再用提升权限的 PowerShell 复制到目标。
            # 避免将内容嵌入命令字符串（对大文件/特殊字符不安全）。
            with tempfile.NamedTemporaryFile(mode="w", suffix=".tmp", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            try:
                win_shell = get_windows_shell_cmd()
                inner_cmd = f"Copy-Item -Path {_ps_quote_arg(tmp_path)} -Destination {_ps_quote_arg(str(path))} -Force"
                ps_cmd = (
                    f"Start-Process -FilePath {_ps_quote_arg(win_shell)} "
                    f"-ArgumentList {_ps_quote_arg('-Command')}, {_ps_quote_arg(inner_cmd)} "
                    f"-Verb RunAs -Wait"
                )
                subprocess.run(
                    [win_shell, "-Command", ps_cmd],
                    check=True,
                    capture_output=True,
                )
            finally:
                Path(tmp_path).unlink(missing_ok=True)
        else:
            # Use sudo tee to write with elevated privileges
            # 使用 sudo tee 以提升权限写入
            run(["tee", str(path)], stdin_data=content)
    else:
        path.write_text(content)


def copy_file(src: str | Path, dst: str | Path) -> None:
    """Copy a file, using elevated privileges if needed.

    复制文件，需要时使用提升权限。

    Handles three scenarios:
    1. Destination needs sudo → use sudo cp (Linux) or PowerShell Copy-Item (Windows)
    2. Source needs sudo to read → read with sudo, write normally
    3. Both accessible → use shutil.copy2

    处理三种情况：
    1. 目标需要 sudo → 使用 sudo cp（Linux）或 PowerShell Copy-Item（Windows）
    2. 源文件需要 sudo 读取 → 用 sudo 读取，正常写入
    3. 两者均可访问 → 使用 shutil.copy2

    Args:
        src: Source file path / 源文件路径
        dst: Destination file path / 目标文件路径
    """
    src = Path(src)
    dst = Path(dst)
    if need_sudo(dst):
        if IS_WINDOWS:
            win_shell = get_windows_shell_cmd()
            inner_cmd = f"Copy-Item -Path {_ps_quote_arg(str(src))} -Destination {_ps_quote_arg(str(dst))} -Force"
            ps_cmd = (
                f"Start-Process -FilePath {_ps_quote_arg(win_shell)} "
                f"-ArgumentList {_ps_quote_arg('-Command')}, {_ps_quote_arg(inner_cmd)} "
                f"-Verb RunAs -Wait"
            )
            subprocess.run(
                [win_shell, "-Command", ps_cmd],
                check=True,
                capture_output=True,
            )
        else:
            run(["cp", str(src), str(dst)])
    elif _needs_sudo_to_read(src):
        dst.write_bytes(_read_file_with_sudo(src))
    else:
        shutil.copy2(src, dst)
