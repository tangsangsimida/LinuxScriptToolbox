#!/usr/bin/env python3
"""Unit tests for utils/cmd_utils.py module.

Tests subprocess helpers with mocked subprocess.run.

Usage:
    python -m pytest tests/test_cmd_utils.py -v
"""

import sys
import subprocess
from pathlib import Path
from unittest import TestCase, main as unittest_main
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))


class TestRunCmd(TestCase):
    """Test run_cmd() function."""

    @patch("utils.cmd_utils.subprocess.run")
    def test_successful_command(self, mock_run):
        """Test successful command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello world\n"
        mock_run.return_value = mock_result

        from utils.cmd_utils import run_cmd
        code, output = run_cmd(["echo", "hello world"])

        self.assertEqual(code, 0)
        self.assertEqual(output, "hello world")
        mock_run.assert_called_once_with(
            ["echo", "hello world"],
            capture_output=True,
            text=True,
            timeout=300
        )

    @patch("utils.cmd_utils.subprocess.run")
    def test_failed_command(self, mock_run):
        """Test failed command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        from utils.cmd_utils import run_cmd
        code, output = run_cmd(["false"])

        self.assertEqual(code, 1)
        self.assertEqual(output, "")

    @patch("utils.cmd_utils.subprocess.run")
    def test_command_timeout(self, mock_run):
        """Test command timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="sleep 100", timeout=10)

        from utils.cmd_utils import run_cmd, TIMEOUT_EXIT_CODE
        code, output = run_cmd(["sleep", "100"], timeout=10)

        self.assertEqual(code, TIMEOUT_EXIT_CODE)
        self.assertEqual(output, "")

    @patch("utils.cmd_utils.subprocess.run")
    def test_custom_timeout(self, mock_run):
        """Test custom timeout parameter."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_run.return_value = mock_result

        from utils.cmd_utils import run_cmd
        run_cmd(["echo", "ok"], timeout=60)

        mock_run.assert_called_once_with(
            ["echo", "ok"],
            capture_output=True,
            text=True,
            timeout=60
        )

    @patch("utils.cmd_utils.subprocess.run")
    def test_stdout_stripped(self, mock_run):
        """Test that stdout is stripped of whitespace."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "  hello  \n"
        mock_run.return_value = mock_result

        from utils.cmd_utils import run_cmd
        _, output = run_cmd(["echo", "hello"])

        self.assertEqual(output, "hello")


class TestRunVerbose(TestCase):
    """Test run_verbose() function."""

    @patch("utils.cmd_utils.subprocess.run")
    def test_successful_command(self, mock_run):
        """Test successful command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        from utils.cmd_utils import run_verbose
        code = run_verbose(["echo", "hello"])

        self.assertEqual(code, 0)
        mock_run.assert_called_once_with(["echo", "hello"], timeout=300)

    @patch("utils.cmd_utils.subprocess.run")
    def test_failed_command(self, mock_run):
        """Test failed command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        from utils.cmd_utils import run_verbose
        code = run_verbose(["false"])

        self.assertEqual(code, 1)

    @patch("utils.cmd_utils.subprocess.run")
    def test_command_timeout(self, mock_run):
        """Test command timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="sleep 100", timeout=10)

        from utils.cmd_utils import run_verbose, TIMEOUT_EXIT_CODE
        code = run_verbose(["sleep", "100"], timeout=10)

        self.assertEqual(code, TIMEOUT_EXIT_CODE)

    @patch("utils.cmd_utils.subprocess.run")
    def test_custom_timeout(self, mock_run):
        """Test custom timeout parameter."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        from utils.cmd_utils import run_verbose
        run_verbose(["echo", "ok"], timeout=60)

        mock_run.assert_called_once_with(["echo", "ok"], timeout=60)


class TestConstants(TestCase):
    """Test module constants."""

    def test_default_timeout(self):
        """Test default timeout value."""
        from utils.cmd_utils import DEFAULT_TIMEOUT
        self.assertEqual(DEFAULT_TIMEOUT, 300)

    def test_timeout_exit_code(self):
        """Test timeout exit code value."""
        from utils.cmd_utils import TIMEOUT_EXIT_CODE
        self.assertEqual(TIMEOUT_EXIT_CODE, 124)


def run_tests():
    """Standalone test runner."""
    print("Running cmd_utils unit tests...")
    print("=" * 60)
    unittest_main(module=__name__, exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
