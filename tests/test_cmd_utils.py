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


# Test run_cmd() function
class TestRunCmd(TestCase):

    # Test successful command execution
    @patch("utils.cmd_utils.subprocess.run")
    def test_successful_command(self, mock_run):
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

    # Test failed command execution
    @patch("utils.cmd_utils.subprocess.run")
    def test_failed_command(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        from utils.cmd_utils import run_cmd
        code, output = run_cmd(["false"])

        self.assertEqual(code, 1)
        self.assertEqual(output, "")

    # Test command timeout handling
    @patch("utils.cmd_utils.subprocess.run")
    def test_command_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="sleep 100", timeout=10)

        from utils.cmd_utils import run_cmd, TIMEOUT_EXIT_CODE
        code, output = run_cmd(["sleep", "100"], timeout=10)

        self.assertEqual(code, TIMEOUT_EXIT_CODE)
        self.assertEqual(output, "")

    # Test custom timeout parameter
    @patch("utils.cmd_utils.subprocess.run")
    def test_custom_timeout(self, mock_run):
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

    # Test that stdout is stripped of whitespace
    @patch("utils.cmd_utils.subprocess.run")
    def test_stdout_stripped(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "  hello  \n"
        mock_run.return_value = mock_result

        from utils.cmd_utils import run_cmd
        _, output = run_cmd(["echo", "hello"])

        self.assertEqual(output, "hello")

    # Test non-interactive sudo password injection for captured commands
    @patch.dict("os.environ", {"LST_SUDO_PASSWORD": "secret"})
    @patch("utils.cmd_utils.subprocess.run")
    def test_sudo_command_uses_password_from_env(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_run.return_value = mock_result

        from utils.cmd_utils import run_cmd
        code, output = run_cmd(["sudo", "cat", "/etc/shadow"])

        self.assertEqual(code, 0)
        self.assertEqual(output, "ok")
        mock_run.assert_called_once_with(
            ["sudo", "-S", "-p", "", "cat", "/etc/shadow"],
            input="secret\n",
            capture_output=True,
            text=True,
            timeout=300,
        )


# Test run_verbose() function
class TestRunVerbose(TestCase):

    # Test successful command execution
    @patch("utils.cmd_utils.subprocess.run")
    def test_successful_command(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        from utils.cmd_utils import run_verbose
        code = run_verbose(["echo", "hello"])

        self.assertEqual(code, 0)
        mock_run.assert_called_once_with(["echo", "hello"], timeout=300)

    # Test failed command execution
    @patch("utils.cmd_utils.subprocess.run")
    def test_failed_command(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        from utils.cmd_utils import run_verbose
        code = run_verbose(["false"])

        self.assertEqual(code, 1)

    # Test command timeout handling
    @patch("utils.cmd_utils.subprocess.run")
    def test_command_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="sleep 100", timeout=10)

        from utils.cmd_utils import run_verbose, TIMEOUT_EXIT_CODE
        code = run_verbose(["sleep", "100"], timeout=10)

        self.assertEqual(code, TIMEOUT_EXIT_CODE)

    # Test custom timeout parameter
    @patch("utils.cmd_utils.subprocess.run")
    def test_custom_timeout(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        from utils.cmd_utils import run_verbose
        run_verbose(["echo", "ok"], timeout=60)

        mock_run.assert_called_once_with(["echo", "ok"], timeout=60)

    # Test non-interactive sudo password injection for verbose commands
    @patch.dict("os.environ", {"LST_SUDO_PASSWORD": "secret"})
    @patch("utils.cmd_utils.subprocess.run")
    def test_sudo_verbose_uses_password_from_env(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        from utils.cmd_utils import run_verbose
        code = run_verbose(["sudo", "pacman", "-Sy"])

        self.assertEqual(code, 0)
        mock_run.assert_called_once_with(
            ["sudo", "-S", "-p", "", "pacman", "-Sy"],
            input="secret\n",
            text=True,
            timeout=300,
        )


# Test module constants
class TestConstants(TestCase):

    # Test default timeout value
    def test_default_timeout(self):
        from utils.cmd_utils import DEFAULT_TIMEOUT
        self.assertEqual(DEFAULT_TIMEOUT, 300)

    # Test timeout exit code value
    def test_timeout_exit_code(self):
        from utils.cmd_utils import TIMEOUT_EXIT_CODE
        self.assertEqual(TIMEOUT_EXIT_CODE, 124)


# Standalone test runner
def run_tests():
    print("Running cmd_utils unit tests...")
    print("=" * 60)
    unittest_main(module=__name__, exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
