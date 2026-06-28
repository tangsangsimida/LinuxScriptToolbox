"""Shared subprocess helpers with timeout support.

提供带超时支持的通用子进程辅助函数。
"""

import os
import subprocess

DEFAULT_TIMEOUT = 300  # Default timeout in seconds / 默认超时时间（秒）
TIMEOUT_EXIT_CODE = 124  # Conventional exit code for timeout (same as coreutils timeout) / 超时的约定退出码（与 coreutils timeout 一致）
SUDO_PASSWORD_ENV = "LST_SUDO_PASSWORD"  # Environment variable name for sudo password / sudo 密码的环境变量名


def _prepare_cmd(cmd: list[str], input_data: str | None = None) -> tuple[list[str], str | None]:
    """Inject sudo password input for non-interactive remote tests when requested.

    在非交互式远程测试中，当需要时自动注入 sudo 密码输入。

    Args:
        cmd: Command to run as a list of strings. / 要执行的命令列表。
        input_data: Optional data to send to stdin. / 可选的 stdin 输入数据。

    Returns:
        A tuple of (prepared_command, prepared_input_data). / 返回 (处理后的命令, 处理后的输入数据) 元组。
    """
    sudo_password = os.environ.get(SUDO_PASSWORD_ENV)
    # Skip injection if no sudo password is set, command is empty, or command is not sudo / 如果未设置 sudo 密码、命令为空或命令不是 sudo，则跳过注入
    if not sudo_password or not cmd or cmd[0] != "sudo":
        return cmd, input_data

    # Use -S to read password from stdin, -p "" to suppress the prompt / 使用 -S 从 stdin 读取密码，-p "" 抑制提示信息
    sudo_cmd = ["sudo", "-S", "-p", ""] + cmd[1:]
    sudo_input = f"{sudo_password}\n"
    if input_data is not None:
        sudo_input += input_data
    return sudo_cmd, sudo_input


_CMD_NOT_FOUND_EXIT_CODE = 127  # standard "command not found" exit code


def run_cmd(cmd: list[str], timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str]:
    """Run a command and capture output.

    执行命令并捕获输出。

    Args:
        cmd: Command to run as a list of strings. / 要执行的命令列表。
        timeout: Timeout in seconds. Defaults to DEFAULT_TIMEOUT. / 超时时间（秒），默认为 DEFAULT_TIMEOUT。

    Returns:
        (returncode, stdout_stripped). Returns (TIMEOUT_EXIT_CODE, "")
        if the command exceeds the timeout, or (_CMD_NOT_FOUND_EXIT_CODE, "")
        if the command does not exist.
        / 返回 (返回码, 去除空白的 stdout)。如果命令超时则返回 (TIMEOUT_EXIT_CODE, "")，
        如果命令不存在则返回 (_CMD_NOT_FOUND_EXIT_CODE, "")。
    """
    try:
        cmd, input_data = _prepare_cmd(cmd)
        if input_data is None:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        else:
            result = subprocess.run(
                cmd,
                input=input_data,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        return result.returncode, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return TIMEOUT_EXIT_CODE, ""
    except FileNotFoundError:
        return _CMD_NOT_FOUND_EXIT_CODE, ""


def run_cmd_with_stdin(cmd: list[str], input_data: str, timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str]:
    """Run a command with stdin input and capture output.

    执行命令并通过 stdin 传入数据，同时捕获输出。

    Args:
        cmd: Command to run as a list of strings. / 要执行的命令列表。
        input_data: Data to send to stdin. / 要发送到 stdin 的数据。
        timeout: Timeout in seconds. / 超时时间（秒）。

    Returns:
        (returncode, stdout_stripped). Returns (TIMEOUT_EXIT_CODE, "")
        if the command exceeds the timeout, or (_CMD_NOT_FOUND_EXIT_CODE, "")
        if the command does not exist.
        / 返回 (返回码, 去除空白的 stdout)。如果命令超时则返回 (TIMEOUT_EXIT_CODE, "")，
        如果命令不存在则返回 (_CMD_NOT_FOUND_EXIT_CODE, "")。
    """
    try:
        cmd, input_data = _prepare_cmd(cmd, input_data)
        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return TIMEOUT_EXIT_CODE, ""
    except FileNotFoundError:
        return _CMD_NOT_FOUND_EXIT_CODE, ""


def run_verbose(cmd: list[str], timeout: int = DEFAULT_TIMEOUT) -> int:
    """Run a command with live output (inherits parent stdio).

    执行命令并实时输出（继承父进程的 stdio）。

    Args:
        cmd: Command to run as a list of strings. / 要执行的命令列表。
        timeout: Timeout in seconds. Defaults to DEFAULT_TIMEOUT. / 超时时间（秒），默认为 DEFAULT_TIMEOUT。

    Returns:
        returncode. Returns TIMEOUT_EXIT_CODE if the command exceeds the timeout,
        or _CMD_NOT_FOUND_EXIT_CODE if the command does not exist.
        / 返回退出码。如果命令超时则返回 TIMEOUT_EXIT_CODE，
        如果命令不存在则返回 _CMD_NOT_FOUND_EXIT_CODE。
    """
    try:
        cmd, input_data = _prepare_cmd(cmd)
        if input_data is None:
            result = subprocess.run(cmd, timeout=timeout)
        else:
            # stdin data present (e.g. sudo password), so we need text mode / 存在 stdin 数据（如 sudo 密码），因此需要文本模式
            result = subprocess.run(cmd, input=input_data, text=True, timeout=timeout)
        return result.returncode
    except subprocess.TimeoutExpired:
        return TIMEOUT_EXIT_CODE
    except FileNotFoundError:
        return _CMD_NOT_FOUND_EXIT_CODE


def run_verbose_with_stdin(cmd: list[str], input_data: str, timeout: int = DEFAULT_TIMEOUT) -> int:
    """Run a command with stdin input and live output (inherits parent stdio).

    执行命令并通过 stdin 传入数据，同时实时输出（继承父进程的 stdio）。

    Args:
        cmd: Command to run as a list of strings. / 要执行的命令列表。
        input_data: Data to send to stdin. / 要发送到 stdin 的数据。
        timeout: Timeout in seconds. / 超时时间（秒）。

    Returns:
        returncode. Returns TIMEOUT_EXIT_CODE if the command exceeds the timeout,
        or _CMD_NOT_FOUND_EXIT_CODE if the command does not exist.
        / 返回退出码。如果命令超时则返回 TIMEOUT_EXIT_CODE，
        如果命令不存在则返回 _CMD_NOT_FOUND_EXIT_CODE。
    """
    try:
        cmd, input_data = _prepare_cmd(cmd, input_data)
        result = subprocess.run(
            cmd,
            input=input_data,
            text=True,
            timeout=timeout,
        )
        return result.returncode
    except subprocess.TimeoutExpired:
        return TIMEOUT_EXIT_CODE
    except FileNotFoundError:
        return _CMD_NOT_FOUND_EXIT_CODE
