"""Shared subprocess helpers with timeout support."""

import subprocess

DEFAULT_TIMEOUT = 300  # seconds
TIMEOUT_EXIT_CODE = 124  # conventional exit code for timeout (same as coreutils timeout)


def run_cmd(cmd: list[str], timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str]:
    """Run a command and capture output.

    Returns:
        (returncode, stdout_stripped). Returns (TIMEOUT_EXIT_CODE, "")
        if the command exceeds the timeout.
    """
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return TIMEOUT_EXIT_CODE, ""


def run_verbose(cmd: list[str], timeout: int = DEFAULT_TIMEOUT) -> int:
    """Run a command with live output (inherits parent stdio).

    Returns:
        returncode. Returns TIMEOUT_EXIT_CODE if the command exceeds the timeout.
    """
    try:
        result = subprocess.run(cmd, timeout=timeout)
        return result.returncode
    except subprocess.TimeoutExpired:
        return TIMEOUT_EXIT_CODE
