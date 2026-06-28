#!/usr/bin/env python3
"""Unit tests for utils/shell.py module.

Tests shell detection (bash, zsh, fish, PowerShell, cmd, etc.).

Usage:
    python -m pytest tests/test_shell.py -v
"""

import sys
from pathlib import Path
from unittest import TestCase, main as unittest_main
from unittest.mock import patch

# Add project root to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))


# Test detect_shell() function on Unix-like systems
class TestDetectShell(TestCase):

    def setUp(self):
        from utils.platform import detect_platform
        from utils.shell import detect_shell
        detect_platform.cache_clear()
        detect_shell.cache_clear()

    # Test bash detection via SHELL env var
    @patch("utils.shell.detect_platform", return_value="linux")
    @patch.dict("os.environ", {"SHELL": "/bin/bash"}, clear=False)
    def test_bash_via_shell_env(self, mock_platform):
        from utils.shell import detect_shell
        result = detect_shell()
        self.assertEqual(result, "bash")

    # Test zsh detection via SHELL env var
    @patch("utils.shell.detect_platform", return_value="linux")
    @patch.dict("os.environ", {"SHELL": "/usr/bin/zsh"}, clear=False)
    def test_zsh_via_shell_env(self, mock_platform):
        from utils.shell import detect_shell
        result = detect_shell()
        self.assertEqual(result, "zsh")

    # Test fish detection via SHELL env var
    @patch("utils.shell.detect_platform", return_value="linux")
    @patch.dict("os.environ", {"SHELL": "/usr/bin/fish"}, clear=False)
    def test_fish_via_shell_env(self, mock_platform):
        from utils.shell import detect_shell
        result = detect_shell()
        self.assertEqual(result, "fish")

    # Test dash detection via SHELL env var
    @patch("utils.shell.detect_platform", return_value="linux")
    @patch.dict("os.environ", {"SHELL": "/usr/bin/dash"}, clear=False)
    def test_dash_via_shell_env(self, mock_platform):
        from utils.shell import detect_shell
        result = detect_shell()
        self.assertEqual(result, "dash")

    # Test fish detection via FISH_VERSION env var
    @patch("utils.shell.detect_platform", return_value="linux")
    @patch.dict("os.environ", {"FISH_VERSION": "3.6.0"}, clear=True)
    def test_fish_via_version_env(self, mock_platform):
        from utils.shell import detect_shell
        result = detect_shell()
        self.assertEqual(result, "fish")

    # Test zsh detection via ZSH_VERSION env var
    @patch("utils.shell.detect_platform", return_value="linux")
    @patch.dict("os.environ", {"ZSH_VERSION": "5.9"}, clear=True)
    def test_zsh_via_version_env(self, mock_platform):
        from utils.shell import detect_shell
        result = detect_shell()
        self.assertEqual(result, "zsh")

    # Test bash detection via BASH_VERSION env var
    @patch("utils.shell.detect_platform", return_value="linux")
    @patch.dict("os.environ", {"BASH_VERSION": "5.2.15"}, clear=True)
    def test_bash_via_version_env(self, mock_platform):
        from utils.shell import detect_shell
        result = detect_shell()
        self.assertEqual(result, "bash")

    # Test nushell detection via NU_VERSION env var
    @patch("utils.shell.detect_platform", return_value="linux")
    @patch.dict("os.environ", {"NU_VERSION": "0.80.0"}, clear=True)
    def test_nushell_via_version_env(self, mock_platform):
        from utils.shell import detect_shell
        result = detect_shell()
        self.assertEqual(result, "nushell")

    # Test unknown shell detection
    @patch("utils.shell.detect_platform", return_value="linux")
    @patch.dict("os.environ", {}, clear=True)
    @patch("utils.shell._detect_parent_process", return_value="unknown")
    def test_unknown_shell(self, mock_parent, mock_platform):
        from utils.shell import detect_shell
        result = detect_shell()
        self.assertEqual(result, "unknown")


# Test detect_shell() function on Windows
class TestDetectShellWindows(TestCase):

    def setUp(self):
        from utils.platform import detect_platform
        from utils.shell import detect_shell
        detect_platform.cache_clear()
        detect_shell.cache_clear()

    # Test PowerShell detection on Windows
    @patch("utils.shell.detect_platform", return_value="windows")
    @patch.dict("os.environ", {"PSModulePath": "C:\\Modules"}, clear=True)
    @patch("utils.shell.shutil.which", return_value=r"C:\Program Files\PowerShell\7\pwsh.exe")
    def test_powershell(self, mock_which, mock_platform):
        from utils.shell import detect_shell
        result = detect_shell()
        self.assertEqual(result, "pwsh")

    # Test legacy Windows PowerShell detection
    @patch("utils.shell.detect_platform", return_value="windows")
    @patch.dict("os.environ", {"PSModulePath": "C:\\Modules"}, clear=True)
    @patch("utils.shell.shutil.which", return_value=None)
    def test_powershell_legacy(self, mock_which, mock_platform):
        from utils.shell import detect_shell
        result = detect_shell()
        self.assertEqual(result, "powershell")

    # Test cmd detection on Windows
    @patch("utils.shell.detect_platform", return_value="windows")
    @patch.dict("os.environ", {"COMSPEC": "C:\\Windows\\system32\\cmd.exe"}, clear=True)
    def test_cmd(self, mock_platform):
        from utils.shell import detect_shell
        result = detect_shell()
        self.assertEqual(result, "cmd")


# Test get_shell_info() function
class TestGetShellInfo(TestCase):

    # Test getting bash shell info
    @patch("utils.shell.detect_shell", return_value="bash")
    @patch.dict("os.environ", {"SHELL": "/bin/bash"}, clear=False)
    def test_bash_info(self, mock_detect):
        from utils.shell import get_shell_info
        info = get_shell_info()
        self.assertEqual(info["name"], "bash")
        self.assertIn("version", info)
        self.assertIn("path", info)

    # Test getting fish shell info
    @patch("utils.shell.detect_shell", return_value="fish")
    @patch.dict("os.environ", {"SHELL": "/usr/bin/fish"}, clear=False)
    def test_fish_info(self, mock_detect):
        from utils.shell import get_shell_info
        info = get_shell_info()
        self.assertEqual(info["name"], "fish")
        self.assertIn("version", info)
        self.assertIn("path", info)

# Test the shell utility functions (rc file, detection helpers)
class TestShellUtilities(TestCase):

    def setUp(self):
        from utils.platform import detect_platform
        detect_platform.cache_clear()

    @patch("utils.shell.detect_shell", return_value="bash")
    def test_get_rc_file_bash(self, mock_shell):
        from utils.shell import get_rc_file
        rc = get_rc_file("bash")
        self.assertEqual(rc.name, ".bashrc")

    @patch("utils.shell.detect_shell", return_value="zsh")
    def test_get_rc_file_zsh(self, mock_shell):
        from utils.shell import get_rc_file
        rc = get_rc_file("zsh")
        self.assertEqual(rc.name, ".zshrc")

    @patch("utils.shell.detect_shell", return_value="fish")
    def test_get_rc_file_fish(self, mock_shell):
        from utils.shell import get_rc_file
        rc = get_rc_file("fish")
        self.assertIn("config.fish", str(rc))

    @patch("utils.shell.detect_shell", return_value="pwsh")
    def test_get_rc_file_pwsh(self, mock_shell):
        from utils.shell import get_rc_file
        rc = get_rc_file("pwsh")
        self.assertIn("Microsoft.PowerShell_profile.ps1", str(rc))

    @patch("utils.shell.detect_shell", return_value="cmd")
    def test_get_rc_file_cmd_returns_none(self, mock_shell):
        from utils.shell import get_rc_file
        rc = get_rc_file("cmd")
        self.assertIsNone(rc)

    def test_is_powershell_like(self):
        from utils.shell import is_powershell_like
        self.assertTrue(is_powershell_like("pwsh"))
        self.assertTrue(is_powershell_like("powershell"))
        self.assertFalse(is_powershell_like("bash"))
        self.assertFalse(is_powershell_like("cmd"))

    def test_is_windows_shell(self):
        from utils.shell import is_windows_shell
        self.assertTrue(is_windows_shell("cmd"))
        self.assertTrue(is_windows_shell("pwsh"))
        self.assertTrue(is_windows_shell("powershell"))
        self.assertFalse(is_windows_shell("bash"))
        self.assertFalse(is_windows_shell("zsh"))

    def test_get_windows_shell_cmd(self):
        from utils.shell import get_windows_shell_cmd
        self.assertEqual(get_windows_shell_cmd("pwsh"), "pwsh")
        self.assertEqual(get_windows_shell_cmd("powershell"), "powershell")
        self.assertEqual(get_windows_shell_cmd("cmd"), "cmd")
        self.assertEqual(get_windows_shell_cmd("bash"), "bash")

    def test_get_refresh_cmd(self):
        from utils.shell import get_refresh_cmd
        bash_cmd = get_refresh_cmd("bash")
        self.assertIn("source", bash_cmd)
        self.assertIn(".bashrc", bash_cmd)
        pwsh_cmd = get_refresh_cmd("pwsh")
        self.assertIn("Microsoft.PowerShell_profile.ps1", pwsh_cmd)



# Standalone test runner
def run_tests():
    print("Running shell detection unit tests...")
    print("=" * 60)
    unittest_main(module=__name__, exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
