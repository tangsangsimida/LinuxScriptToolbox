"""Shell detection — identifies the current interactive shell.

Shell 检测 — 识别当前交互式 Shell。

Detects bash, zsh, fish, PowerShell, cmd, and other shells by examining
environment variables and the parent process.

通过检查环境变量和父进程来检测 bash、zsh、fish、PowerShell、cmd 等 Shell。
"""

import os
import shutil
import subprocess
from pathlib import Path

from utils.platform import detect_platform


# Detect the current interactive shell.
#
# 检测当前交互式 Shell。
#
# Delegates to platform-specific detection functions.
# 委托给平台特定的检测函数。
#
# Returns:
#     Shell name: "bash", "zsh", "fish", "powershell", "pwsh", "cmd",
#     "nushell", "elvish", "xonsh", or "unknown"
#
#     Shell 名称："bash"、"zsh"、"fish"、"powershell"、"pwsh"、"cmd"、
#     "nushell"、"elvish"、"xonsh" 或 "unknown"
def detect_shell() -> str:
    if detect_platform() == "windows":
        return _detect_windows_shell()

    return _detect_unix_shell()


# Detect shell on Unix-like systems (Linux, macOS).
#
# 在类 Unix 系统（Linux、macOS）上检测 Shell。
#
# Checks environment variables in order of reliability:
# SHELL → FISH_VERSION → ZSH_VERSION → BASH_VERSION → NU_VERSION → parent process.
#
# 按可靠性顺序检查环境变量：
# SHELL → FISH_VERSION → ZSH_VERSION → BASH_VERSION → NU_VERSION → 父进程。
def _detect_unix_shell() -> str:
    # Check SHELL environment variable first (most reliable)
    # 优先检查 SHELL 环境变量（最可靠）
    shell_env = os.environ.get("SHELL", "")
    if shell_env:
        shell_name = Path(shell_env).name
        if shell_name in ("bash", "zsh", "fish", "dash", "ash", "sh"):
            return shell_name

    # Check for fish-specific variables / 检查 fish 特有变量
    if os.environ.get("FISH_VERSION"):
        return "fish"

    # Check for zsh-specific variables / 检查 zsh 特有变量
    if os.environ.get("ZSH_VERSION") or os.environ.get("ZSH_NAME"):
        return "zsh"

    # Check for bash-specific variables / 检查 bash 特有变量
    if os.environ.get("BASH_VERSION") or os.environ.get("BASH"):
        return "bash"

    # Check for nushell / 检查 nushell
    if os.environ.get("NU_VERSION"):
        return "nushell"

    # Check parent process as fallback / 作为回退方案检查父进程
    return _detect_parent_process()


# Detect shell on Windows.
#
# 在 Windows 上检测 Shell。
#
# Checks for PowerShell (pwsh vs powershell), then falls back to cmd.
# 先检查 PowerShell（pwsh 与 powershell），然后回退到 cmd。
def _detect_windows_shell() -> str:
    # Check for PowerShell-specific variables / 检查 PowerShell 特有变量
    if os.environ.get("PSModulePath"):
        # Check for PowerShell 7+ (pwsh) vs Windows PowerShell
        # 区分 PowerShell 7+（pwsh）和 Windows PowerShell
        if shutil.which("pwsh"):
            return "pwsh"
        return "powershell"

    # Check for pwsh in PATH / 检查 PATH 中的 pwsh
    if os.environ.get("PWSH_VERSION"):
        return "pwsh"

    # Check COMSPEC for cmd / 通过 COMSPEC 检查 cmd
    comspec = os.environ.get("COMSPEC", "")
    if "cmd.exe" in comspec.lower():
        return "cmd"

    return "cmd"


# Detect shell by examining the parent process name.
#
# 通过检查父进程名称来检测 Shell。
#
# On Linux, reads /proc/<ppid>/cmdline.
# On macOS, uses ps command.
#
# 在 Linux 上读取 /proc/<ppid>/cmdline；
# 在 macOS 上使用 ps 命令。
def _detect_parent_process() -> str:
    try:
        system = detect_platform()
        if system == "linux":
            ppid = os.getppid()
            cmdline = Path(f"/proc/{ppid}/cmdline").read_text().split("\0")
            if cmdline:
                proc_name = Path(cmdline[0]).name
                if proc_name in ("bash", "zsh", "fish", "dash", "ash", "sh"):
                    return proc_name
        elif system == "macos":
            result = subprocess.run(
                ["ps", "-p", str(os.getppid()), "-o", "comm="],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                proc_name = Path(result.stdout.strip()).name
                if proc_name in ("bash", "zsh", "fish"):
                    return proc_name
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass

    return "unknown"


# Get comprehensive shell information.
#
# 获取全面的 Shell 信息。
#
# Returns:
#     Dict with 'name', 'version', 'path' keys.
#     包含 'name'、'version'、'path' 键的字典。
def get_shell_info() -> dict[str, str]:
    shell_name = detect_shell()
    info = {"name": shell_name, "version": "", "path": ""}

    # Get version / 获取版本
    try:
        if shell_name in ("bash", "zsh", "fish"):
            result = subprocess.run(
                [shell_name, "--version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                info["version"] = result.stdout.strip().split("\n")[0]
        elif shell_name in ("powershell", "pwsh"):
            result = subprocess.run(
                [shell_name, "-Command", "$PSVersionTable.PSVersion.ToString()"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                info["version"] = result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Get path / 获取路径
    shell_env = os.environ.get("SHELL", "")
    if shell_env:
        info["path"] = shell_env
    elif shell_name in ("powershell", "pwsh", "cmd"):
        info["path"] = os.environ.get("COMSPEC", "")

    return info



# Get the shell configuration file path.
#
# 获取 Shell 配置文件路径。
#
# Returns the rc/profile file where persistent environment modifications
# (PATH, aliases, exports) should be written. Returns None for shells
# that have no such concept (cmd).
#
# 返回应写入持久化环境变量（PATH、别名、导出）的 rc/profile 文件路径。
# 对于没有此概念的 Shell（cmd），返回 None。
#
# Args:
#     shell_name: Shell name, or None to auto-detect. / Shell 名称，None 表示自动检测。
#
# Returns:
#     Path to the rc file, or None. / rc 文件路径，或 None。
def get_rc_file(shell_name: str | None = None) -> "Path | None":
    if shell_name is None:
        shell_name = detect_shell()

    rc_map = {
        "bash": Path.home() / ".bashrc",
        "zsh": Path.home() / ".zshrc",
        "dash": Path.home() / ".profile",
        "ash": Path.home() / ".profile",
        "sh": Path.home() / ".profile",
        "fish": Path.home() / ".config" / "fish" / "config.fish",
        "nushell": Path.home() / ".config" / "nushell" / "config.nu",
        "powershell": Path.home() / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1",
        "pwsh": Path.home() / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1",
        "cmd": None,
    }
    return rc_map.get(shell_name)


# Get the command to reload/apply shell configuration changes.
#
# 获取重新加载/应用 Shell 配置更改的命令。
#
# Returns a command string the user can run to apply changes made to
# their shell rc file without restarting the shell.
#
# 返回用户可运行的命令字符串，用于在不重启 Shell 的情况下应用对
# Shell rc 文件所做的更改。
#
# Args:
#     shell_name: Shell name, or None to auto-detect. / Shell 名称，None 表示自动检测。
#
# Returns:
#     Reload command string, or None if not applicable. / 重新加载命令字符串，或不适用时返回 None。
def get_refresh_cmd(shell_name: str | None = None) -> str | None:
    if shell_name is None:
        shell_name = detect_shell()

    rc = get_rc_file(shell_name)
    if rc is None:
        return None

    if shell_name in ("bash", "zsh", "dash", "ash", "sh"):
        return f"source {rc}"
    elif shell_name == "fish":
        return f"source {rc}"
    elif shell_name == "nushell":
        return f"source {rc}"
    elif shell_name in ("powershell", "pwsh"):
        return f". {rc}"
    return None


# Get a human-readable hint for applying shell config changes.
#
# 获取应用 Shell 配置更改的人类可读提示。
#
# Returns a message telling the user what command to run to reload
# their shell configuration.
#
# 返回一条消息，告诉用户运行什么命令来重新加载 Shell 配置。
#
# Args:
#     shell_name: Shell name, or None to auto-detect. / Shell 名称，None 表示自动检测。
#
# Returns:
#     Hint string, or None if not applicable. / 提示字符串，或不适用时返回 None。
def get_rc_update_hint(shell_name: str | None = None) -> str | None:
    if shell_name is None:
        shell_name = detect_shell()

    rc = get_rc_file(shell_name)
    refresh = get_refresh_cmd(shell_name)

    if shell_name == "cmd":
        return "Restart the command prompt to apply changes."
    if rc and refresh:
        return f"Run '{refresh}' or restart your shell to apply changes."
    return "Restart your shell to apply changes."


# Check if the current (or specified) shell is a Windows-native shell.
#
# 检查当前（或指定）Shell 是否为 Windows 原生 Shell。
#
# Returns True for cmd, powershell, and pwsh.
#
# 对于 cmd、powershell 和 pwsh 返回 True。
#
# Args:
#     shell_name: Shell name, or None to auto-detect. / Shell 名称，None 表示自动检测。
#
# Returns:
#     True if the shell is Windows-native. / 如果 Shell 是 Windows 原生的则返回 True。
def is_windows_shell(shell_name: str | None = None) -> bool:
    if shell_name is None:
        shell_name = detect_shell()
    return shell_name in ("cmd", "powershell", "pwsh")


# Check if the current (or specified) shell is PowerShell (any version).
#
# 检查当前（或指定）Shell 是否为 PowerShell（任何版本）。
#
# Returns True for both Windows PowerShell 5.1 (powershell) and
# PowerShell 7+ (pwsh).
#
# 对于 Windows PowerShell 5.1（powershell）和 PowerShell 7+（pwsh）均返回 True。
#
# Args:
#     shell_name: Shell name, or None to auto-detect. / Shell 名称，None 表示自动检测。
#
# Returns:
#     True if the shell is PowerShell. / 如果 Shell 是 PowerShell 则返回 True。
def is_powershell_like(shell_name: str | None = None) -> bool:
    if shell_name is None:
        shell_name = detect_shell()
    return shell_name in ("powershell", "pwsh")


# Get the executable name for the current Windows shell.
#
# 获取当前 Windows Shell 的可执行文件名。
#
# Used by tools that need to invoke shell commands via subprocess on Windows.
# Returns "pwsh" for PowerShell 7+, "powershell" for Windows PowerShell,
# and "cmd" for Command Prompt.
#
# 工具在 Windows 上需要通过 subprocess 调用 Shell 命令时使用。
# 对于 PowerShell 7+ 返回 "pwsh"，对于 Windows PowerShell 返回 "powershell"，
# 对于命令提示符返回 "cmd"。
#
# Args:
#     shell_name: Shell name, or None to auto-detect. / Shell 名称，None 表示自动检测。
#
# Returns:
#     Shell executable name. / Shell 可执行文件名。
def get_windows_shell_cmd(shell_name: str | None = None) -> str:
    if shell_name is None:
        shell_name = detect_shell()
    if is_powershell_like(shell_name):
        return shell_name  # "pwsh" or "powershell"
    if shell_name == "cmd":
        return "cmd"
    return shell_name  # fallback for unexpected values
