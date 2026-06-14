"""Shared subprocess helpers with timeout support."""

import os
import subprocess

DEFAULT_TIMEOUT = 300  # seconds
TIMEOUT_EXIT_CODE = 124  # conventional exit code for timeout (same as coreutils timeout)
SUDO_PASSWORD_ENV = "LST_SUDO_PASSWORD"


def _prepare_cmd(cmd: list[str], input_data: str | None = None) -> tuple[list[str], str | None]:
    """Inject sudo password input for non-interactive remote tests when requested."""
    sudo_password = os.environ.get(SUDO_PASSWORD_ENV)
    if not sudo_password or not cmd or cmd[0] != "sudo":
        return cmd, input_data

    sudo_cmd = ["sudo", "-S", "-p", ""] + cmd[1:]
    sudo_input = f"{sudo_password}\n"
    if input_data is not None:
        sudo_input += input_data
    return sudo_cmd, sudo_input


def run_cmd(cmd: list[str], timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str]:
    """Run a command and capture output.

    Returns:
        (returncode, stdout_stripped). Returns (TIMEOUT_EXIT_CODE, "")
        if the command exceeds the timeout.
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


def run_cmd_with_stdin(cmd: list[str], input_data: str, timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str]:
    """Run a command with stdin input and capture output.

    Args:
        cmd: Command to run as a list of strings.
        input_data: Data to send to stdin.
        timeout: Timeout in seconds.

    Returns:
        (returncode, stdout_stripped). Returns (TIMEOUT_EXIT_CODE, "")
        if the command exceeds the timeout.
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


def run_verbose(cmd: list[str], timeout: int = DEFAULT_TIMEOUT) -> int:
    """Run a command with live output (inherits parent stdio).

    Returns:
        returncode. Returns TIMEOUT_EXIT_CODE if the command exceeds the timeout.
    """
    try:
        cmd, input_data = _prepare_cmd(cmd)
        if input_data is None:
            result = subprocess.run(cmd, timeout=timeout)
        else:
            result = subprocess.run(cmd, input=input_data, text=True, timeout=timeout)
        return result.returncode
    except subprocess.TimeoutExpired:
        return TIMEOUT_EXIT_CODE


def run_verbose_with_stdin(cmd: list[str], input_data: str, timeout: int = DEFAULT_TIMEOUT) -> int:
    """Run a command with stdin input and live output (inherits parent stdio).

    Args:
        cmd: Command to run as a list of strings.
        input_data: Data to send to stdin.
        timeout: Timeout in seconds.

    Returns:
        returncode. Returns TIMEOUT_EXIT_CODE if the command exceeds the timeout.
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
