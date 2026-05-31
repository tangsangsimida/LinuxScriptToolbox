"""Shared subprocess helpers with timeout support."""

import subprocess

DEFAULT_TIMEOUT = 300  # seconds


def run_cmd(cmd: list[str], timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str]:
    """Run a command and capture output.

    Returns:
        (returncode, stdout_stripped)
    """
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.returncode, result.stdout.strip()


def run_verbose(cmd: list[str], timeout: int = DEFAULT_TIMEOUT) -> int:
    """Run a command with live output (inherits parent stdio).

    Returns:
        returncode
    """
    result = subprocess.run(cmd, timeout=timeout)
    return result.returncode
